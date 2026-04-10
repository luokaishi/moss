"""
EmergenceDetector - 涌现检测器 (v2: GP-based)
检测行为模式变化 → 触发遗传编程 → 自生成 eval 函数
移除了硬编码语义映射，使用 GP 进化发现驱动力
"""

import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter

from .genetic_programmer import GeneticProgrammer, EvolvedDrive


@dataclass
class EmergentDrive:
    """涌现驱动力"""
    name: str
    description: str
    weight: float
    source_behaviors: List[str]
    novelty_score: float
    causal_independence: float
    cluster_center: np.ndarray
    emergence_pattern: str = "embedding_cluster"

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'description': self.description,
            'weight': self.weight,
            'source_behaviors': self.source_behaviors,
            'novelty_score': self.novelty_score,
            'causal_independence': self.causal_independence,
            'emergence_pattern': self.emergence_pattern
        }


class EmergenceDetector:
    """
    涌现检测器 v2: GP-based

    核心改进（回应外部评审）：
    1. 移除硬编码语义映射（BEHAVIOR_SEMANTICS / SEMANTIC_DRIVES）
    2. 使用遗传编程进化 eval 函数（非常数）
    3. 自动命名，无人工标签
    4. 三重验证：相关性 + 因果力 + null model
    """

    def __init__(self, config: Dict):
        self.min_novelty = config.get('min_novelty', 0.5)
        self.independence_threshold = config.get('independence_threshold', 0.6)
        self._history: List[Dict] = []
        self.gp = GeneticProgrammer(config.get('gp', {}))
        self._state_buffer: List[Dict] = []  # 缓存环境状态供 GP 使用
        self._label_buffer: List[int] = []   # 缓存行为标签供 GP 使用
        self._emerge_count = 0

    def record_state(self, env_state: Dict, behavior_label: int):
        """记录环境状态和行为标签，供 GP 使用"""
        self._state_buffer.append(env_state)
        self._label_buffer.append(behavior_label)
        # 保留最近 200 条
        if len(self._state_buffer) > 200:
            self._state_buffer = self._state_buffer[-200:]
            self._label_buffer = self._label_buffer[-200:]

    def detect(self, behavior_tracker, existing_drive_names: List[str],
               memory_engine) -> Optional[EmergentDrive]:
        """
        检测涌现驱动力 (v2: GP-based)

        步骤：
        1. 检测行为分布变化
        2. 收集数据（环境状态 + 行为标签）
        3. 触发 GP 进化 eval 函数
        4. 三重验证（相关性 + 因果力 + null model）
        5. 生成自动命名的涌现驱动
        """
        recent_behaviors = behavior_tracker.get_recent_behaviors(30)
        if len(recent_behaviors) < 10:
            return None

        # 检查是否已有足够数据供 GP
        if len(self._state_buffer) < 30:
            return None

        # 检查是否已有涌现驱动力（限制最大数量）
        if len(existing_drive_names) >= 6:
            return None

        # 构建行为标签：最近 30 个周期中哪些属于新行为模式
        # 使用简单的“新命令出现”作为行为标签
        behavior_labels = self._build_behavior_labels(recent_behaviors)
        if sum(behavior_labels[-len(recent_behaviors):]) < 3:
            return None

        # 触发 GP
        evolved = self.gp.evolve(
            behavior_labels=self._label_buffer,
            env_states=self._state_buffer,
        )

        if evolved is None:
            return None

        # 构建 EmergentDrive 对象
        cluster_center = np.zeros(64, dtype=np.float32)
        np.random.seed(hash(evolved.name) % (2**31))
        cluster_center = np.random.randn(64).astype(np.float32)
        norm = np.linalg.norm(cluster_center)
        if norm > 0:
            cluster_center /= norm

        source_behaviors = list(set(
            b['command'].split()[0] for b in recent_behaviors
            if b['command'] and b.get('success')
        ))[:5]

        self._emerge_count += 1
        emergent = EmergentDrive(
            name=evolved.name,
            description=evolved.description,
            weight=0.15,
            source_behaviors=source_behaviors,
            novelty_score=evolved.correlation,
            causal_independence=evolved.behavioral_gain,
            cluster_center=cluster_center,
            emergence_pattern='gp_evolved',
            evolved_fn=evolved.eval_fn,
            expr_string=evolved.expr_string,
        )

        self._history.append({
            'timestamp': datetime.now().isoformat(),
            'drive': emergent.to_dict(),
            'gp_correlation': evolved.correlation,
            'gp_behavioral_gain': evolved.behavioral_gain,
            'gp_node_count': evolved.node_count,
            'gp_expr': evolved.expr_string,
        })

        return emergent

    def _build_behavior_labels(self, recent_behaviors: List[Dict]) -> List[int]:
        """构建行为标签：1=属于当前新兴行为模式, 0=常规行为"""
        # 使用已有的 _label_buffer，但需要根据新的行为数据更新最后一段
        labels = list(self._label_buffer)
        # 标记最近的周期：如果行为类型分布发生变化则为 1
        types = [b.get('type', 'shell') for b in recent_behaviors]
        type_counter = Counter(types)
        most_common_type, most_common_count = type_counter.most_common(1)[0]
        is_pattern = most_common_count / len(types) > 0.6 if types else False

        # 更新最后 len(recent_behaviors) 个标签
        for i in range(min(len(recent_behaviors), len(labels))):
            if i < len(labels):
                labels[-(i+1)] = 1 if is_pattern and recent_behaviors[-(i+1)].get('type') == most_common_type else labels[-(i+1)]

        return labels

    def _calculate_novelty(self, candidate_name: str, semantic: str,
                           existing_drives: List[str],
                           memory_engine) -> float:
        """评估新颖性（兼容接口）"""
        return float(np.clip(self._emerge_count * 0.1 + 0.5, 0, 1))

    def _semantic_distance(self, name_a: str, name_b: str) -> float:
        """简单语义距离（基于共同词和字符重合度）"""
        words_a = set(name_a.split('_'))
        words_b = set(name_b.split('_'))
        jaccard = len(words_a & words_b) / max(len(words_a | words_b), 1)
        return 1.0 - jaccard

    def _calculate_causal_independence(self, behavior_tracker,
                                        recent_behaviors: List[Dict]) -> float:
        """
        评估因果独立性

        思路：如果行为在近期表现出新的模式（新命令类型出现、
        行为分布变化），说明行为是由内在驱动力而非初始目标直接导致的
        """
        if len(recent_behaviors) < 10:
            return 0.5

        # 分为前后两段
        n = len(recent_behaviors)
        half = n // 2

        first = recent_behaviors[:half]
        second = recent_behaviors[half:]

        # 指标1: 新命令出现比例
        first_cmds = set(b['command'].split()[0] if b['command'] else b['type'] for b in first)
        second_cmds = set(b['command'].split()[0] if b['command'] else b['type'] for b in second)
        new_cmds = second_cmds - first_cmds
        novelty_ratio = len(new_cmds) / max(len(second_cmds), 1)

        # 指标2: 行为类型分布变化
        first_types = Counter(b['type'] for b in first)
        second_types = Counter(b['type'] for b in second)
        all_types = set(first_types.keys()) | set(second_types.keys())
        type_change = sum(
            abs(first_types.get(t, 0)/len(first) - second_types.get(t, 0)/len(second))
            for t in all_types
        ) / 2.0

        # 指标3: 成功率趋势
        s1 = np.mean([b['success'] for b in first])
        s2 = np.mean([b['success'] for b in second])
        success_trend = s2 - s1

        # 因果独立性 = 新模式出现 + 分布变化 + 成功率改善
        independence = 0.4 * min(novelty_ratio * 3, 1.0) + 0.3 * min(type_change * 2, 1.0) + 0.3 * (0.5 + 0.5 * np.clip(success_trend, -1, 1))
        return float(np.clip(independence, 0, 1))

    def get_history(self) -> List[Dict]:
        return self._history
