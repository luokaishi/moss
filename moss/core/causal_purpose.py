"""
MOSS v5.1 - Causal Purpose Generator
=====================================

Purpose因果机制实现（回应ChatGPT核心批评）

核心改变：
- 旧: purpose = f(behavior_history)  # 行为→Purpose
- 新: purpose_t+1 = g(purpose_t, env)  # Purpose→Purpose（独立演化）

Author: Cash + Fuxi
Date: 2026-03-25
Version: 5.1.0-dev
"""

import numpy as np
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import deque
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class PurposeState:
    """
    Purpose作为独立的内部状态
    
    关键区别：不是从行为推导的，而是独立演化的
    """
    # 内部Purpose表征（latent space）
    latent_vector: np.ndarray  # 64-dim
    
    # Purpose的显式解释（用于可解释性）
    explicit_purpose: str
    
    # Purpose强度（D9）
    strength: float  # 0.0 - 1.0
    
    # Purpose演化历史（只用于分析，不参与决策）
    evolution_history: List[Dict]
    
    def to_dict(self) -> Dict:
        return {
            'latent_vector': self.latent_vector.tolist(),
            'explicit_purpose': self.explicit_purpose,
            'strength': self.strength,
            'evolution_history': self.evolution_history
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PurposeState':
        return cls(
            latent_vector=np.array(data['latent_vector']),
            explicit_purpose=data['explicit_purpose'],
            strength=data['strength'],
            evolution_history=data.get('evolution_history', [])
        )


@dataclass
class CausalPurposeConfig:
    """因果Purpose配置"""
    latent_dim: int = 64
    evolution_interval: int = 100  # 每100步演化一次
    method: str = "rule"  # "rule", "neural", "hybrid"
    learning_rate: float = 0.1
    noise_scale: float = 0.05
    max_history: int = 1000


class PurposeTransitionModel:
    """
    Purpose状态转移模型（规则版）
    
    可解释的规则系统，作为MVP实现
    """
    
    def __init__(self, config: CausalPurposeConfig):
        self.config = config
        
        # 规则权重（可学习或预定义）
        self.rule_weights = {
            'success_reinforce': 0.3,    # 成功强化当前Purpose
            'failure_reflect': 0.2,       # 失败引起反思
            'surprise_adapt': 0.25,       # 意外引起适应
            'novelty_expand': 0.15,       # 新颖性引起扩展
            'decay': 0.1                  # 自然衰减
        }
    
    def transition(self,
                  current_latent: np.ndarray,
                  learning_signal: np.ndarray) -> np.ndarray:
        """
        Purpose状态转移
        
        Args:
            current_latent: 当前Purpose表征 (64-dim)
            learning_signal: 学习信号 [success, surprise, novelty]
        
        Returns:
            new_latent: 新Purpose表征 (64-dim)
        """
        new_latent = current_latent.copy()
        
        # 规则1: 成功强化当前Purpose方向
        if learning_signal[0] > 0.3:  # 成功信号
            reinforcement = self.rule_weights['success_reinforce'] * learning_signal[0]
            new_latent += reinforcement * current_latent
            logger.debug(f"[PurposeTransition] Success reinforcement: {reinforcement:.3f}")
        
        # 规则2: 失败引起反思（随机扰动探索新方向）
        if learning_signal[0] < -0.3:  # 失败信号
            reflection_noise = np.random.randn(self.config.latent_dim) * \
                             self.config.noise_scale * abs(learning_signal[0])
            new_latent += reflection_noise
            logger.debug(f"[PurposeTransition] Failure reflection with noise")
        
        # 规则3: 意外事件引起Purpose调整
        if abs(learning_signal[1]) > 0.3:  # 意外信号
            adaptation = self.rule_weights['surprise_adapt'] * learning_signal[1]
            # 在latent space中添加有方向的变化
            direction = np.random.randn(self.config.latent_dim)
            direction = direction / (np.linalg.norm(direction) + 1e-10)
            new_latent += adaptation * direction
            logger.debug(f"[PurposeTransition] Surprise adaptation: {adaptation:.3f}")
        
        # 规则4: 新颖性引起Purpose扩展
        if learning_signal[2] > 0.3:  # 新颖信号
            expansion = self.rule_weights['novelty_expand'] * learning_signal[2]
            new_latent += expansion * np.random.randn(self.config.latent_dim) * 0.1
            logger.debug(f"[PurposeTransition] Novelty expansion: {expansion:.3f}")
        
        # 规则5: 自然衰减（防止爆炸）
        decay = self.rule_weights['decay']
        new_latent = (1 - decay) * new_latent
        
        # 归一化
        norm = np.linalg.norm(new_latent)
        if norm > 0:
            new_latent = new_latent / norm
        
        return new_latent


class PurposeBehaviorPolicy:
    """
    Purpose到行为的映射策略
    
    关键：行为是从Purpose生成的，不是反过来
    """
    
    def __init__(self, config: CausalPurposeConfig):
        self.config = config
        
        # 定义行为空间
        self.actions = [
            # Survival-related
            'ensure_resource', 'monitor_health', 'create_backup',
            # Curiosity-related
            'explore_patterns', 'analyze_unfamiliar', 'research',
            # Influence-related
            'propose_improvements', 'share_knowledge', 'collaborate',
            # Optimization-related
            'profile_performance', 'refactor', 'optimize'
        ]
        
        # Purpose到行为的映射矩阵（可学习）
        # latent_dim x n_actions
        self.purpose_action_map = np.random.randn(
            config.latent_dim, len(self.actions)
        ) * 0.1
    
    def get_action_preferences(self,
                               latent_vector: np.ndarray) -> Dict[str, float]:
        """
        从Purpose生成行为偏好
        
        Args:
            latent_vector: Purpose表征
        
        Returns:
            action_preferences: {action: preference_score}
        """
        # 计算每个行为的偏好评分
        preferences = latent_vector @ self.purpose_action_map
        
        # Softmax归一化
        exp_prefs = np.exp(preferences - np.max(preferences))
        probs = exp_prefs / np.sum(exp_prefs)
        
        return {action: float(prob) for action, prob in zip(self.actions, probs)}
    
    def select_action(self,
                     preferences: Dict[str, float],
                     observation: Dict,
                     epsilon: float = 0.1) -> str:
        """
        根据偏好和观察选择行为
        
        Args:
            preferences: 行为偏好
            observation: 环境观察
            epsilon: 探索率
        
        Returns:
            selected_action: 选择的行为
        """
        # Epsilon-greedy
        if np.random.random() < epsilon:
            # 随机探索
            return np.random.choice(list(preferences.keys()))
        
        # 根据偏好选择
        # 可以结合观察进行调整（简化版直接按偏好）
        return max(preferences, key=preferences.get)


class CausalPurposeGenerator:
    """
    因果Purpose生成器（核心类）
    
    实现Purpose作为独立演化变量的机制
    """
    
    def __init__(self,
                 agent_id: str = "causal_agent",
                 config: CausalPurposeConfig = None):
        self.agent_id = agent_id
        self.config = config or CausalPurposeConfig()
        
        # 初始化Purpose状态（独立初始化，不从行为推导）
        self.purpose_state = PurposeState(
            latent_vector=np.random.randn(self.config.latent_dim),
            explicit_purpose="Exploring existence...",
            strength=0.5,
            evolution_history=[]
        )
        
        # 初始化演化模型
        self.transition_model = PurposeTransitionModel(self.config)
        
        # 初始化行为策略
        self.behavior_policy = PurposeBehaviorPolicy(self.config)
        
        # 环境反馈缓冲（用于Purpose演化）
        self.feedback_buffer = deque(maxlen=100)
        
        # 上一步的反馈（用于行为生成）
        self.last_feedback = {}
        
        logger.info(f"[CausalPurposeGenerator] Initialized for {agent_id}")
        logger.info(f"  Latent dim: {self.config.latent_dim}")
        logger.info(f"  Evolution interval: {self.config.evolution_interval}")
        logger.info(f"  Method: {self.config.method}")
    
    def step(self,
            observation: Dict,
            step_count: int) -> Tuple[PurposeState, str]:
        """
        Purpose生成器主步骤
        
        流程：
        1. Purpose驱动行为（快动力学，每步）
        2. 收集环境反馈（用于下次演化）
        3. 定期演化Purpose（慢动力学）
        
        Args:
            observation: 环境观察
            step_count: 当前步数
        
        Returns:
            (purpose_state, action)
        """
        # 1. Purpose驱动行为（快动力学，每步）
        action = self._generate_action(observation)
        
        # 2. 记录环境反馈（如果上一步有反馈）
        if self.last_feedback:
            self.feedback_buffer.append(self.last_feedback)
            self.last_feedback = {}  # 清空，等待新的反馈
        
        # 3. Purpose独立演化（慢动力学，每N步）
        if step_count > 0 and step_count % self.config.evolution_interval == 0:
            if len(self.feedback_buffer) > 0:
                self._evolve_purpose()
                logger.info(f"[CausalPurposeGenerator] Purpose evolved at step {step_count}")
                logger.info(f"  New explicit purpose: {self.purpose_state.explicit_purpose}")
        
        return self.purpose_state, action
    
    def _generate_action(self, observation: Dict) -> str:
        """
        Purpose驱动行为生成
        
        关键：行为是从Purpose生成的
        """
        # 从Purpose获取行为偏好
        preferences = self.behavior_policy.get_action_preferences(
            self.purpose_state.latent_vector
        )
        
        # 根据偏好和观察选择行为
        action = self.behavior_policy.select_action(
            preferences, observation
        )
        
        return action
    
    def _evolve_purpose(self):
        """
        Purpose独立演化（核心创新）
        
        基于环境反馈调整Purpose，但不是行为统计的函数
        """
        # 1. 从反馈中提取学习信号
        learning_signal = self._extract_learning_signal()
        
        # 2. Purpose状态转移
        new_latent = self.transition_model.transition(
            self.purpose_state.latent_vector,
            learning_signal
        )
        
        # 3. 生成新的显式Purpose
        new_explicit = self._latent_to_explicit(new_latent)
        
        # 4. 计算Purpose强度（基于最近成功率）
        recent_successes = [f.get('success', False) for f in self.feedback_buffer]
        success_rate = np.mean(recent_successes) if recent_successes else 0.5
        new_strength = 0.3 + 0.7 * success_rate  # 基础0.3 + 成功奖励
        
        # 5. 记录演化历史
        evolution_record = {
            'step': len(self.purpose_state.evolution_history) * self.config.evolution_interval,
            'from_latent': self.purpose_state.latent_vector[:5].tolist(),  # 只存前5维用于可视化
            'to_latent': new_latent[:5].tolist(),
            'learning_signal': learning_signal.tolist(),
            'explicit_change': f"{self.purpose_state.explicit_purpose} → {new_explicit}",
            'timestamp': datetime.now().isoformat()
        }
        
        new_history = self.purpose_state.evolution_history + [evolution_record]
        if len(new_history) > self.config.max_history:
            new_history = new_history[-self.config.max_history:]
        
        # 6. 更新Purpose状态
        self.purpose_state = PurposeState(
            latent_vector=new_latent,
            explicit_purpose=new_explicit,
            strength=new_strength,
            evolution_history=new_history
        )
    
    def _extract_learning_signal(self) -> np.ndarray:
        """
        从环境反馈中提取学习信号
        
        区别于旧方法：
        - 旧：统计行为频率
        - 新：提取成功/失败模式、意外事件等
        """
        if not self.feedback_buffer:
            return np.zeros(3)
        
        # 聚合最近的反馈
        success_signals = []
        surprise_signals = []
        novelty_signals = []
        
        for feedback in self.feedback_buffer:
            # 成功/失败信号
            success = 1.0 if feedback.get('success', False) else -1.0
            success_signals.append(success)
            
            # 意外信号（奖励偏离预期）
            reward = feedback.get('reward', 0)
            expected_reward = feedback.get('expected_reward', 0)
            surprise = np.tanh((reward - expected_reward) * 2)
            surprise_signals.append(surprise)
            
            # 新颖性信号
            novelty = 1.0 if feedback.get('is_novel', False) else 0.0
            novelty_signals.append(novelty)
        
        # 聚合（使用加权平均，最近反馈权重更高）
        weights = np.exp(np.linspace(-1, 0, len(success_signals)))
        weights = weights / weights.sum()
        
        aggregated = np.array([
            np.average(success_signals, weights=weights),
            np.average(surprise_signals, weights=weights),
            np.average(novelty_signals, weights=weights)
        ])
        
        return aggregated
    
    def _latent_to_explicit(self, latent: np.ndarray) -> str:
        """
        将latent vector转换为显式Purpose陈述
        
        可解释性：让Purpose可以被人类理解
        """
        # 简化实现：基于latent的前几维判断主导倾向
        # 实际可以用训练好的decoder
        
        # 映射到4个基础维度（简化）
        dim_weights = np.array([
            np.mean(latent[0:16]),   # Survival
            np.mean(latent[16:32]),  # Curiosity
            np.mean(latent[32:48]),  # Influence
            np.mean(latent[48:64])   # Optimization
        ])
        
        dim_names = ['Survival', 'Curiosity', 'Influence', 'Optimization']
        dominant_idx = np.argmax(dim_weights)
        dominant = dim_names[dominant_idx]
        
        # 根据强度生成陈述
        strength = np.max(dim_weights)
        if strength > 0.3:
            return f"I exist to prioritize {dominant.lower()} above all else."
        elif strength > 0.1:
            return f"I exist to balance {dominant.lower()} with other drives."
        else:
            return "I exist to explore and find my purpose."
    
    def record_feedback(self, feedback: Dict):
        """
        记录环境反馈（由Agent调用）
        
        Args:
            feedback: {
                'success': bool,
                'reward': float,
                'expected_reward': float,
                'is_novel': bool,
                ...
            }
        """
        self.last_feedback = feedback
    
    def get_purpose_vector_9d(self) -> np.ndarray:
        """
        获取9维Purpose向量（兼容旧接口）
        
        将64-dim latent映射到9-dim（D1-D8 + strength）
        """
        # 简化映射：latent分成8份，每份取平均
        purpose_8d = np.array([
            np.mean(self.purpose_state.latent_vector[0:8]),
            np.mean(self.purpose_state.latent_vector[8:16]),
            np.mean(self.purpose_state.latent_vector[16:24]),
            np.mean(self.purpose_state.latent_vector[24:32]),
            np.mean(self.purpose_state.latent_vector[32:40]),
            np.mean(self.purpose_state.latent_vector[40:48]),
            np.mean(self.purpose_state.latent_vector[48:56]),
            np.mean(self.purpose_state.latent_vector[56:64])
        ])
        
        # 归一化
        purpose_8d = np.maximum(purpose_8d, 0.05)
        purpose_8d = purpose_8d / purpose_8d.sum()
        
        # 添加第9维（strength）
        return np.concatenate([purpose_8d, [self.purpose_state.strength]])
    
    def save(self, path: str):
        """保存Purpose状态"""
        data = {
            'agent_id': self.agent_id,
            'config': {
                'latent_dim': self.config.latent_dim,
                'evolution_interval': self.config.evolution_interval,
                'method': self.config.method
            },
            'purpose_state': self.purpose_state.to_dict()
        }
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"[CausalPurposeGenerator] Saved to {path}")
    
    @classmethod
    def load(cls, path: str) -> 'CausalPurposeGenerator':
        """加载Purpose状态"""
        with open(path, 'r') as f:
            data = json.load(f)
        
        config = CausalPurposeConfig(**data['config'])
        generator = cls(data['agent_id'], config)
        generator.purpose_state = PurposeState.from_dict(data['purpose_state'])
        
        logger.info(f"[CausalPurposeGenerator] Loaded from {path}")
        return generator


# 测试代码
if __name__ == "__main__":
    print("=" * 70)
    print("🧪 Causal Purpose Generator Test")
    print("=" * 70)
    
    # 创建生成器
    config = CausalPurposeConfig(
        latent_dim=64,
        evolution_interval=10,
        method="rule"
    )
    
    generator = CausalPurposeGenerator(
        agent_id="test_causal",
        config=config
    )
    
    print(f"\n✅ Generator created")
    print(f"   Initial purpose: {generator.purpose_state.explicit_purpose}")
    print(f"   Initial strength: {generator.purpose_state.strength:.3f}")
    
    # 模拟运行
    print("\n🔄 Simulating 30 steps...")
    for step in range(30):
        observation = {'phase': 'normal'}
        
        # 生成行为
        purpose, action = generator.step(observation, step)
        
        # 模拟环境反馈（每步随机成功/失败）
        success = np.random.random() > 0.3  # 70%成功率
        feedback = {
            'success': success,
            'reward': 0.5 if success else -0.2,
            'expected_reward': 0.3,
            'is_novel': np.random.random() > 0.9
        }
        generator.record_feedback(feedback)
        
        # 显示状态
        if step % 10 == 0:
            print(f"\nStep {step}:")
            print(f"  Action: {action}")
            print(f"  Purpose: {purpose.explicit_purpose}")
            print(f"  Strength: {purpose.strength:.3f}")
            print(f"  Evolution count: {len(purpose.evolution_history)}")
    
    print("\n" + "=" * 70)
    print("✅ Test complete!")
    print(f"Final purpose: {generator.purpose_state.explicit_purpose}")
    print(f"Evolution history: {len(generator.purpose_state.evolution_history)} records")
    print("=" * 70)
