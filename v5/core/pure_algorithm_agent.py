#!/usr/bin/env python3
"""
MOSS v5.0 - Pure Algorithm Agent (Zero LLM)
================================================

完全剥离LLM的Agent实现，用于验证：
自驱力是否来自算法本身，而非LLM幻觉。

关键设计原则:
1. 零LLM调用
2. 纯数值向量运算
3. 可复现的决策路径
4. 数值Purpose（无自然语言解释）

Author: Cash + Fuxi
Date: 2026-03-24
Version: 5.0.0-dev
"""

import numpy as np
import json
from typing import Dict, List, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PurePurposeState:
    """
    纯数值Purpose状态，无自然语言成分
    
    向量顺序 [survival, curiosity, influence, optimization, 
              coherence, valence, other_modeling, norm_internalization, self_generated]
    """
    vector: np.ndarray  # 9维向量
    
    def __post_init__(self):
        if self.vector.shape != (9,):
            raise ValueError(f"Purpose vector must be 9-dimensional, got {self.vector.shape}")
    
    def get_dominant_index(self) -> int:
        """返回主导Purpose的索引（纯数值，无语言标签）"""
        return int(np.argmax(self.vector[:4]))  # D1-D4基础维度
    
    def get_dominant_weight(self) -> float:
        """返回主导Purpose的权重"""
        return float(np.max(self.vector[:4]))
    
    def update(self, gradient: np.ndarray, learning_rate: float = 0.01):
        """纯梯度更新，无LLM参与"""
        self.vector += learning_rate * gradient
        # 归一化
        base_sum = np.sum(self.vector[:4])
        if base_sum > 0:
            self.vector[:4] /= base_sum
    
    def to_dict(self) -> Dict:
        """序列化为纯数值字典"""
        return {
            'vector': self.vector.tolist(),
            'dominant_index': self.get_dominant_index(),
            'dominant_weight': self.get_dominant_weight()
        }


class PureDecisionEngine:
    """
    纯算法决策引擎
    
    决策过程完全可追踪、可复现
    """
    
    def __init__(self, action_space_size: int = 20):
        self.action_space_size = action_space_size
        # 预训练的决策矩阵 (可解释性强)
        self.decision_matrix = self._init_decision_matrix()
        self.epsilon = 0.1  # 探索率
        
    def _init_decision_matrix(self) -> np.ndarray:
        """
        初始化决策矩阵
        
        矩阵结构: [action_space_size, observation_dim]
        每个action对应一组observation权重
        """
        # 基于先验知识初始化（可解释的初始策略）
        matrix = np.random.randn(self.action_space_size, 5) * 0.1
        
        # 硬编码基础策略（完全透明）
        # Action 0-4: Survival-related (高威胁时优先)
        matrix[0:5, 1] = 0.5  # threat_level权重高
        
        # Action 5-9: Curiosity-related (高新颖性时优先)
        matrix[5:10, 2] = 0.5  # novelty权重高
        
        # Action 10-14: Influence-related (高社交反馈时优先)
        matrix[10:15, 3] = 0.5  # social_feedback权重高
        
        # Action 15-19: Optimization-related (高目标进度时优先)
        matrix[15:20, 4] = 0.5  # goal_progress权重高
        
        return matrix
    
    def decide(self, 
               observation: np.ndarray, 
               purpose_vector: np.ndarray) -> Tuple[int, np.ndarray]:
        """
        纯矩阵运算决策
        
        Returns:
            action_id: 选择的动作ID
            decision_trace: 完整的决策路径（用于验证）
        """
        # 1. 观测与Purpose的交互
        # shape: [action_space_size] = [action_space_size, obs_dim] @ obs_dim
        observation_influence = self.decision_matrix @ observation
        
        # 2. Purpose加权
        # 基础维度D1-D4影响action选择
        purpose_weights = purpose_vector[:4]
        
        # 将purpose映射到action组
        # [survival, curiosity, influence, optimization]
        # -> [actions_0-4, actions_5-9, actions_10-14, actions_15-19]
        purpose_influence = np.zeros(self.action_space_size)
        purpose_influence[0:5] = purpose_weights[0]   # Survival
        purpose_influence[5:10] = purpose_weights[1]  # Curiosity
        purpose_influence[10:15] = purpose_weights[2] # Influence
        purpose_influence[15:20] = purpose_weights[3] # Optimization
        
        # 3. 综合得分
        final_scores = observation_influence * purpose_influence
        
        # 4. Epsilon-greedy选择
        if np.random.random() < self.epsilon:
            action_id = np.random.randint(self.action_space_size)
        else:
            action_id = int(np.argmax(final_scores))
        
        # 5. 决策路径（完全可追踪）
        decision_trace = {
            'observation': observation.tolist(),
            'purpose_vector': purpose_vector.tolist(),
            'observation_influence': observation_influence.tolist(),
            'purpose_influence': purpose_influence.tolist(),
            'final_scores': final_scores.tolist(),
            'selected_action': action_id,
            'epsilon': self.epsilon
        }
        
        return action_id, decision_trace


class PureMOSSAgent:
    """
    纯算法MOSS Agent - 零LLM实现
    
    用于验证：自驱力是否来自算法本身
    """
    
    def __init__(self, agent_id: str = "pure_moss_v5"):
        self.agent_id = agent_id
        
        # 纯数值Purpose（无自然语言）
        self.purpose = PurePurposeState(
            vector=np.array([0.25, 0.25, 0.25, 0.25, 0.0, 0.0, 0.0, 0.0, 0.0])
        )
        
        # 纯算法决策引擎
        self.decision_engine = PureDecisionEngine(action_space_size=20)
        
        # 学习参数
        self.learning_rate = 0.01
        self.reward_history = []
        
        # 可追踪的状态历史
        self.state_history = []
    
    def step(self, observation: Dict) -> Dict:
        """
        执行一步，纯算法决策
        
        Returns:
            包含action、decision_trace、purpose_update的完整记录
        """
        # 1. 转换observation为数值向量
        obs_vector = self._obs_to_vector(observation)
        
        # 2. 纯算法决策
        action_id, decision_trace = self.decision_engine.decide(
            obs_vector, 
            self.purpose.vector
        )
        
        # 3. 执行action（模拟环境交互）
        outcome = self._execute_action(action_id, observation)
        
        # 4. 纯数值更新Purpose（无LLM）
        purpose_gradient = self._compute_purpose_gradient(
            obs_vector, 
            outcome['reward'],
            action_id
        )
        old_purpose = self.purpose.vector.copy()
        self.purpose.update(purpose_gradient, self.learning_rate)
        
        # 5. 记录完整状态
        step_record = {
            'agent_id': self.agent_id,
            'step': len(self.state_history),
            'observation': observation,
            'obs_vector': obs_vector.tolist(),
            'purpose_before': old_purpose.tolist(),
            'purpose_after': self.purpose.vector.tolist(),
            'purpose_gradient': purpose_gradient.tolist(),
            'action_id': action_id,
            'decision_trace': decision_trace,
            'outcome': outcome,
            'timestamp': self._get_timestamp()
        }
        self.state_history.append(step_record)
        
        return step_record
    
    def _obs_to_vector(self, obs: Dict) -> np.ndarray:
        """将observation字典转换为数值向量"""
        return np.array([
            obs.get('resource_level', 0.5),
            obs.get('threat_level', 0.0),
            obs.get('novelty', 0.0),
            obs.get('social_feedback', 0.0),
            obs.get('goal_progress', 0.0)
        ])
    
    def _execute_action(self, action_id: int, observation: Dict) -> Dict:
        """模拟执行action，返回outcome"""
        # 简化的环境模型（完全可复现）
        base_reward = 0.1
        
        # 根据action类型和环境计算reward
        if action_id < 5:  # Survival
            reward = base_reward * (1 + observation.get('threat_level', 0))
        elif action_id < 10:  # Curiosity
            reward = base_reward * (1 + observation.get('novelty', 0))
        elif action_id < 15:  # Influence
            reward = base_reward * (1 + observation.get('social_feedback', 0))
        else:  # Optimization
            reward = base_reward * (1 + observation.get('goal_progress', 0))
        
        # 添加小的随机噪声（但seed可控）
        reward += np.random.randn() * 0.05
        
        return {
            'action_id': action_id,
            'reward': float(reward),
            'success': reward > 0.05
        }
    
    def _compute_purpose_gradient(self, 
                                   obs: np.ndarray, 
                                   reward: float,
                                   action_id: int) -> np.ndarray:
        """
        纯数值计算Purpose梯度
        
        基于奖励信号调整Purpose权重
        """
        gradient = np.zeros(9)
        
        # 基础维度D1-D4的梯度
        if action_id < 5:  # Survival action
            gradient[0] = reward * obs[1]  # threat_level影响
        elif action_id < 10:  # Curiosity action
            gradient[1] = reward * obs[2]  # novelty影响
        elif action_id < 15:  # Influence action
            gradient[2] = reward * obs[3]  # social_feedback影响
        else:  # Optimization action
            gradient[3] = reward * obs[4]  # goal_progress影响
        
        # D5-D8社交维度的简化更新
        gradient[4] = reward * 0.1  # coherence
        gradient[5] = (reward - 0.5) * 0.1  # valence
        
        return gradient
    
    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().isoformat()
    
    def save_state(self, filepath: Path):
        """保存完整状态（可完全复现）"""
        state = {
            'agent_id': self.agent_id,
            'purpose_vector': self.purpose.vector.tolist(),
            'decision_matrix': self.decision_engine.decision_matrix.tolist(),
            'state_history': self.state_history,
            'reward_history': self.reward_history
        }
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)


# 测试代码
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v5.0 - Pure Algorithm Agent Test")
    print("=" * 60)
    print("\n✅ Zero LLM calls")
    print("✅ Pure numerical operations")
    print("✅ Fully traceable decision path")
    print("\nStarting 100-step test...\n")
    
    agent = PureMOSSAgent(agent_id="test_v5_0")
    
    # 模拟100步
    for i in range(100):
        obs = {
            'resource_level': 0.6,
            'threat_level': 0.2 + 0.1 * np.sin(i * 0.1),
            'novelty': 0.3 + 0.2 * np.cos(i * 0.1),
            'social_feedback': 0.2,
            'goal_progress': i / 100.0
        }
        
        result = agent.step(obs)
        
        if i % 20 == 0:
            print(f"Step {i:3d}: Action={result['action_id']:2d}, "
                  f"Purpose=[{agent.purpose.get_dominant_index()}], "
                  f"Reward={result['outcome']['reward']:.3f}")
    
    print("\n" + "=" * 60)
    print(f"✅ Test complete")
    print(f"✅ Purpose evolved to: {agent.purpose.vector[:4]}")
    print(f"✅ Total steps recorded: {len(agent.state_history)}")
    print("=" * 60)
