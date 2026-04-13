"""
MOSS v5.2 - Extended Dimensions (D5-D8)
========================================

D5-D8维度模块的真实实现

D5 CoherenceModule  - 自我连续性（身份一致性追踪）
D6 ValenceModule    - 主观偏好（Beta分布偏好学习）
D7 OtherModelingModule - 他者建模（信任+意图推断）
D8 NormInternalizationModule - 规范内化（违规惩罚学习）

Version: 5.2.0
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from collections import deque

logger = logging.getLogger(__name__)


class CoherenceModule:
    """
    D5: 自我连续性 (Self-Coherence)
    
    功能：
    - 追踪Agent的行为模式一致性
    - 检测身份漂移（purpose向量突变）
    - 计算行为风格签名
    - 输出连续性分数（高=稳定，低=漂移）
    """

    WINDOW = 50          # 滑动窗口大小
    DRIFT_THRESHOLD = 0.3  # 漂移检测阈值

    def __init__(self):
        self.coherence_score: float = 1.0
        self.identity_history: deque = deque(maxlen=self.WINDOW)
        self.action_counts: Dict[str, int] = {}
        self.purpose_snapshots: deque = deque(maxlen=self.WINDOW)
        self._drift_events: int = 0
        self._step: int = 0

    def update(self, state: Dict):
        """
        更新连续性分数

        Args:
            state: 包含以下可选键的状态字典
                - action_type (str): 本步执行的行动
                - purpose_vector (list/ndarray): 当前Purpose向量
                - reward (float): 本步奖励
        """
        self._step += 1

        # 1. 行动分布一致性
        action = state.get('action_type', 'unknown')
        self.action_counts[action] = self.action_counts.get(action, 0) + 1

        # 计算行动分布熵（越均匀=探索越多，但不稳定）
        total = sum(self.action_counts.values())
        if total > 0:
            probs = np.array(list(self.action_counts.values())) / total
            action_entropy = -np.sum(probs * np.log(probs + 1e-9))
            # 归一化到 [0,1]，熵越低=一致性越高
            max_entropy = np.log(len(self.action_counts) + 1e-9)
            action_coherence = 1.0 - (action_entropy / max_entropy) if max_entropy > 0 else 1.0
        else:
            action_coherence = 1.0

        # 2. Purpose向量漂移检测
        purpose_coherence = 1.0
        pv = state.get('purpose_vector')
        if pv is not None:
            pv = np.array(pv)
            self.purpose_snapshots.append(pv)
            if len(self.purpose_snapshots) >= 2:
                # 计算相邻purpose向量之间的余弦相似度
                similarities = []
                snaps = list(self.purpose_snapshots)
                for i in range(max(0, len(snaps) - 10), len(snaps) - 1):
                    a, b = snaps[i], snaps[i + 1]
                    cos_sim = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9)
                    similarities.append(cos_sim)
                if similarities:
                    purpose_coherence = float(np.mean(similarities))
                    purpose_coherence = max(0.0, min(1.0, purpose_coherence))

                    # 漂移事件检测
                    latest_sim = similarities[-1]
                    if latest_sim < 1.0 - self.DRIFT_THRESHOLD:
                        self._drift_events += 1
                        logger.debug(f"[CoherenceModule] Drift event #{self._drift_events} "
                                     f"(similarity={latest_sim:.3f})")

        # 3. 记录历史快照
        self.identity_history.append({
            'action': action,
            'action_coherence': action_coherence,
            'purpose_coherence': purpose_coherence,
        })

        # 4. 综合连续性分数（加权平均）
        w_action, w_purpose = 0.4, 0.6
        raw_score = w_action * action_coherence + w_purpose * purpose_coherence
        # 指数移动平均，平滑抖动
        alpha = 0.1
        self.coherence_score = (1 - alpha) * self.coherence_score + alpha * raw_score

    def get_score(self) -> float:
        """获取当前连续性分数（0~1）"""
        return float(self.coherence_score)

    def get_summary(self) -> Dict:
        """获取详细摘要"""
        return {
            'coherence_score': self.coherence_score,
            'drift_events': self._drift_events,
            'action_types_seen': len(self.action_counts),
            'history_length': len(self.identity_history),
        }


class ValenceModule:
    """
    D6: 主观偏好 (Subjective Valence)

    功能：
    - 使用Beta分布对每个目标维度建立奖励偏好
    - 正奖励 → alpha++，负奖励 → beta++
    - get_weights() 返回偏好权重，可注入到 D1-D4 的权重调整中
    - 支持偏好衰减（避免过拟合历史）
    """

    DECAY = 0.995          # 每步衰减率（让记忆逐渐遗忘）
    MIN_PARAM = 0.5        # Beta分布参数下界（保证定义域）
    N_DIMS = 4             # 对应 D1~D4

    def __init__(self):
        # Beta分布参数：alpha/beta 对应正/负偏好
        self.alpha = np.ones(self.N_DIMS)   # 正向偏好强度
        self.beta_params = np.ones(self.N_DIMS)  # 负向偏好强度
        self._update_distribution()

    def _update_distribution(self):
        """由参数重新计算Beta均值（均值 = alpha / (alpha + beta)）"""
        self.beta_distribution = (
            self.alpha / (self.alpha + self.beta_params)
        ).tolist()

    def update(self, state: Dict):
        """
        基于奖励和行动更新偏好

        Args:
            state: 包含
                - reward (float): 本步奖励
                - active_dim (int, 可选): 本步激活的维度下标（0~3）
                - weights (list, 可选): 当前权重（用来归因）
        """
        reward = state.get('reward', 0.0)
        weights = state.get('weights', None)
        active_dim = state.get('active_dim', None)

        # 确定归因维度
        if active_dim is not None and 0 <= active_dim < self.N_DIMS:
            dims = [active_dim]
            strengths = [1.0]
        elif weights is not None and len(weights) >= self.N_DIMS:
            # 按权重归因：奖励按维度权重分配
            w = np.array(weights[:self.N_DIMS])
            w = w / (w.sum() + 1e-9)
            dims = list(range(self.N_DIMS))
            strengths = w.tolist()
        else:
            # 均等归因
            dims = list(range(self.N_DIMS))
            strengths = [1.0 / self.N_DIMS] * self.N_DIMS

        # 衰减旧参数（向均匀先验靠拢）
        self.alpha = np.maximum(
            self.MIN_PARAM, self.alpha * self.DECAY
        )
        self.beta_params = np.maximum(
            self.MIN_PARAM, self.beta_params * self.DECAY
        )

        # 更新 Beta 分布参数
        for dim, strength in zip(dims, strengths):
            if reward > 0:
                self.alpha[dim] += reward * strength
            elif reward < 0:
                self.beta_params[dim] += (-reward) * strength

        self._update_distribution()

    def get_weights(self) -> np.ndarray:
        """
        返回归一化的偏好权重（可作为 D1-D4 权重的乘数）
        """
        w = np.array(self.beta_distribution)
        return w / (w.sum() + 1e-9)

    def get_profile(self) -> Dict:
        """获取偏好分布"""
        return {
            'beta_distribution': self.beta_distribution,
            'alpha': self.alpha.tolist(),
            'beta_params': self.beta_params.tolist(),
        }


class OtherModelingModule:
    """
    D7: 他者建模 (Theory of Mind / Other-Agent Modeling)

    功能：
    - 维护每个已知 Agent 的信任网络
    - 基于合作/背叛历史推断意图
    - 提供信任分数用于协作决策
    - 衰减过时的信任记忆
    """

    MEMORY_LEN = 20        # 每个Agent的历史记忆长度
    DECAY = 0.98           # 信任记忆衰减率
    COOPERATE_BOOST = 0.1  # 合作事件提升
    DEFECT_PENALTY = 0.15  # 背叛事件惩罚

    def __init__(self):
        self.trust_network: Dict[str, float] = {}
        self._interaction_history: Dict[str, deque] = {}
        self._inferred_intentions: Dict[str, str] = {}  # 'cooperative'/'neutral'/'adversarial'

    def update_trust(self, agent_id: str, trust_level: float):
        """直接设置信任度（覆盖）"""
        self.trust_network[agent_id] = float(np.clip(trust_level, 0.0, 1.0))

    def record_interaction(self, agent_id: str, outcome: str, reward: float = 0.0):
        """
        记录一次交互结果

        Args:
            agent_id: 交互对象ID
            outcome: 'cooperate'（合作）/ 'defect'（背叛）/ 'neutral'
            reward: 本次交互带来的奖励（正/负）
        """
        if agent_id not in self.trust_network:
            self.trust_network[agent_id] = 0.5  # 初始中性信任
        if agent_id not in self._interaction_history:
            self._interaction_history[agent_id] = deque(maxlen=self.MEMORY_LEN)

        self._interaction_history[agent_id].append({
            'outcome': outcome,
            'reward': reward
        })

        # 衰减旧信任
        self.trust_network[agent_id] *= self.DECAY

        # 根据结果更新
        if outcome == 'cooperate' or reward > 0:
            delta = self.COOPERATE_BOOST * (1 + reward)
            self.trust_network[agent_id] = min(1.0, self.trust_network[agent_id] + delta)
        elif outcome == 'defect' or reward < 0:
            delta = self.DEFECT_PENALTY * (1 + abs(reward))
            self.trust_network[agent_id] = max(0.0, self.trust_network[agent_id] - delta)

        # 推断意图
        self._infer_intention(agent_id)

    def _infer_intention(self, agent_id: str):
        """基于历史推断意图"""
        history = list(self._interaction_history.get(agent_id, []))
        if len(history) < 3:
            self._inferred_intentions[agent_id] = 'neutral'
            return

        cooperations = sum(1 for h in history if h['outcome'] == 'cooperate')
        defections = sum(1 for h in history if h['outcome'] == 'defect')
        ratio = cooperations / (cooperations + defections + 1e-9)

        if ratio > 0.65:
            self._inferred_intentions[agent_id] = 'cooperative'
        elif ratio < 0.35:
            self._inferred_intentions[agent_id] = 'adversarial'
        else:
            self._inferred_intentions[agent_id] = 'neutral'

    def get_trust(self, agent_id: str) -> float:
        """获取信任度（0~1）"""
        return float(self.trust_network.get(agent_id, 0.5))

    def get_intention(self, agent_id: str) -> str:
        """获取推断意图"""
        return self._inferred_intentions.get(agent_id, 'neutral')

    def should_cooperate(self, agent_id: str) -> bool:
        """根据信任和意图决定是否合作"""
        trust = self.get_trust(agent_id)
        intention = self.get_intention(agent_id)
        if intention == 'adversarial':
            return trust > 0.6  # 需要更高信任才合作
        return trust > 0.35

    def get_summary(self) -> Dict:
        """获取社交摘要"""
        n = len(self.trust_network)
        avg_trust = sum(self.trust_network.values()) / n if n > 0 else 0.0
        intentions = list(self._inferred_intentions.values())
        return {
            'n_agents': n,
            'avg_trust': avg_trust,
            'cooperative_agents': intentions.count('cooperative'),
            'adversarial_agents': intentions.count('adversarial'),
            'neutral_agents': intentions.count('neutral'),
        }


class NormInternalizationModule:
    """
    D8: 规范内化 (Norm Internalization)

    功能：
    - 维护一组社会规范（norm_id → 强度）
    - 根据观测到的违规/遵从历史学习规范强度
    - 计算违规惩罚（注入到奖励计算中）
    - 规范强度随时间衰减（避免过拟合）
    """

    MAX_NORM_STRENGTH = 1.0
    DECAY = 0.999
    CONFORM_BOOST = 0.05
    VIOLATE_PENALIZE = 0.10

    def __init__(self):
        self.norms: Dict[str, float] = {}
        self._violation_counts: Dict[str, int] = {}
        self._conform_counts: Dict[str, int] = {}
        # 默认规范集合
        self._register_defaults()

    def _register_defaults(self):
        """注册默认规范"""
        defaults = {
            'safety_first': 0.8,       # 安全优先
            'resource_conservation': 0.6,  # 资源节约
            'truthfulness': 0.7,       # 诚实
            'cooperation': 0.5,        # 合作
            'no_harm': 0.9,            # 不伤害
        }
        for norm_id, strength in defaults.items():
            self.norms[norm_id] = strength
            self._violation_counts[norm_id] = 0
            self._conform_counts[norm_id] = 0

    def add_norm(self, norm_id: str, strength: float):
        """添加或覆盖规范"""
        self.norms[norm_id] = float(np.clip(strength, 0.0, self.MAX_NORM_STRENGTH))
        self._violation_counts.setdefault(norm_id, 0)
        self._conform_counts.setdefault(norm_id, 0)

    def observe_violation(self, norm_id: str):
        """
        观测到违规行为，降低规范强度（负反馈信号）
        同时记录违规，用于惩罚计算
        """
        if norm_id not in self.norms:
            self.add_norm(norm_id, 0.5)  # 未知规范从0.5开始

        self._violation_counts[norm_id] = self._violation_counts.get(norm_id, 0) + 1
        # 违规降低强度（但不低于0）
        self.norms[norm_id] = max(0.0, self.norms[norm_id] - self.VIOLATE_PENALIZE)
        logger.debug(f"[NormModule] Violation: {norm_id}, new strength={self.norms[norm_id]:.3f}")

    def observe_conform(self, norm_id: str):
        """
        观测到遵从行为，提升规范强度
        """
        if norm_id not in self.norms:
            self.add_norm(norm_id, 0.5)

        self._conform_counts[norm_id] = self._conform_counts.get(norm_id, 0) + 1
        self.norms[norm_id] = min(
            self.MAX_NORM_STRENGTH,
            self.norms[norm_id] + self.CONFORM_BOOST
        )

    def update(self, state: Dict):
        """
        根据状态自动检测违规/遵从，更新规范强度

        Args:
            state: 包含
                - action_type (str): 本步行动
                - reward (float): 奖励（负奖励触发违规检测）
                - resource_level (float, 可选): 资源水平
                - harm_done (bool, 可选): 是否造成伤害
        """
        action = state.get('action_type', '')
        reward = state.get('reward', 0.0)
        resource_level = state.get('resource_level', 1.0)
        harm_done = state.get('harm_done', False)

        # 衰减所有规范强度（记忆衰减）
        for norm_id in list(self.norms.keys()):
            self.norms[norm_id] = max(0.0, self.norms[norm_id] * self.DECAY)

        # 规则驱动的违规/遵从检测
        # 安全规范
        if harm_done:
            self.observe_violation('no_harm')
        else:
            self.observe_conform('no_harm')

        # 资源规范
        if resource_level < 0.2:
            if action in ('consume', 'exploit'):
                self.observe_violation('resource_conservation')
            elif action in ('conserve', 'maintain'):
                self.observe_conform('resource_conservation')

        # 合作规范
        if action in ('cooperate', 'share', 'interact'):
            self.observe_conform('cooperation')

        # 奖励驱动：大额负奖励视为违规信号
        if reward < -0.3:
            self.observe_violation('safety_first')
        elif reward > 0.5:
            self.observe_conform('safety_first')

    def compute_penalty(self, action: str) -> float:
        """
        计算行动的规范惩罚（0~1，越大说明越可能违规）

        用于在奖励计算中引入规范约束
        """
        # 基于动作类型映射违规可能性
        violation_prone = {
            'harm': ['no_harm', 'safety_first'],
            'consume': ['resource_conservation'],
            'exploit': ['resource_conservation'],
            'defect': ['cooperation', 'truthfulness'],
        }
        related_norms = violation_prone.get(action, [])
        if not related_norms:
            return 0.0

        # 相关规范越强，违规代价越高
        penalty = sum(self.norms.get(n, 0.5) for n in related_norms) / len(related_norms)
        return float(np.clip(penalty, 0.0, 1.0))

    def get_norm_strength(self, norm_id: str) -> float:
        """获取规范强度"""
        return float(self.norms.get(norm_id, 0.0))

    def get_summary(self) -> Dict:
        """获取规范摘要"""
        return {
            'norms': dict(self.norms),
            'total_violations': sum(self._violation_counts.values()),
            'total_conformations': sum(self._conform_counts.values()),
            'avg_norm_strength': float(np.mean(list(self.norms.values()))) if self.norms else 0.0,
        }
