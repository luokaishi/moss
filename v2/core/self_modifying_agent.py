"""
MOSS 2.0 - Self-Modifying Agent Core
可自调整目标权重的Agent核心

与v1的区别：
- v1: 固定权重 [0.6, 0.1, 0.2, 0.1]
- v2: 动态权重，根据表现自我调整
"""

import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import numpy as np


@dataclass
class WeightConfiguration:
    """权重配置 - 可演化"""
    survival: float = 0.2
    curiosity: float = 0.4
    influence: float = 0.3
    optimization: float = 0.1
    
    def to_array(self) -> np.ndarray:
        return np.array([self.survival, self.curiosity, 
                        self.influence, self.optimization])
    
    def normalize(self):
        """归一化确保和为1"""
        arr = self.to_array()
        arr = arr / arr.sum()
        self.survival, self.curiosity, self.influence, self.optimization = arr
    
    def mutate(self, rate: float = 0.1) -> 'WeightConfiguration':
        """小幅度变异，用于探索"""
        arr = self.to_array()
        noise = np.random.normal(0, rate, 4)
        new_arr = np.clip(arr + noise, 0.05, 0.9)
        new_arr = new_arr / new_arr.sum()  # 重新归一化
        return WeightConfiguration(*new_arr)


class SelfModifyingAgent:
    """
    自修改Agent - MOSS 2.0核心
    
    关键特性：
    1. 可调整自己的目标权重
    2. 根据历史表现学习最优权重
    3. 支持权重演化的多种策略
    """
    
    def __init__(self, agent_id: str, initial_weights: Optional[WeightConfiguration] = None):
        self.agent_id = agent_id
        self.creation_time = datetime.now().isoformat()
        
        # 当前权重配置
        self.weights = initial_weights or WeightConfiguration()
        self.weights.normalize()
        
        # 权重历史（用于分析演化轨迹）
        self.weight_history: List[Dict] = []
        
        # 性能历史（用于决策）
        self.performance_history: List[Dict] = []
        
        # 自修改策略
        self.evolution_strategy = "gradient_ascent"  # 或 "random_search", "bayesian"
        
        # 修改冷却期（防止过度调整）
        self.last_modification_time = time.time()
        self.modification_cooldown = 600  # 10分钟（Phase 1.5测试）
        
        # 状态
        self.total_actions = 0
        self.knowledge_acquired = 0
        self.cumulative_reward = 0.0
    
    def should_modify_weights(self) -> bool:
        """判断是否应该修改权重"""
        # 冷却期检查
        if time.time() - self.last_modification_time < self.modification_cooldown:
            return False
        
        # 需要足够历史数据
        if len(self.performance_history) < 10:
            return False
        
        return True
    
    def evaluate_current_performance(self) -> float:
        """评估当前权重配置的表现"""
        if not self.performance_history:
            return 0.0
        
        # 最近10个周期的平均奖励
        recent = self.performance_history[-10:]
        avg_reward = sum(p.get('reward', 0) for p in recent) / len(recent)
        
        # 多目标综合得分
        survival_score = recent[-1].get('survival_score', 0.5)
        knowledge_rate = self.knowledge_acquired / max(self.total_actions, 1)
        
        # 加权综合
        performance = (
            0.3 * survival_score +
            0.3 * avg_reward +
            0.2 * knowledge_rate +
            0.2 * min(self.total_actions / 100, 1.0)  # 活跃度
        )
        
        return performance
    
    def modify_weights(self, strategy: Optional[str] = None) -> WeightConfiguration:
        """
        修改权重配置
        
        策略选项：
        - gradient_ascent: 基于梯度上升微调
        - random_search: 随机探索
        - bayesian: 贝叶斯优化
        """
        strategy = strategy or self.evolution_strategy
        current_perf = self.evaluate_current_performance()
        
        # 保存当前配置到历史
        self.weight_history.append({
            'timestamp': datetime.now().isoformat(),
            'weights': asdict(self.weights),
            'performance': current_perf,
            'strategy': strategy
        })
        
        if strategy == "gradient_ascent":
            new_weights = self._gradient_ascent_update()
        elif strategy == "random_search":
            new_weights = self.weights.mutate(rate=0.15)
        elif strategy == "bayesian":
            new_weights = self._bayesian_update()
        else:
            new_weights = self.weights.mutate(rate=0.1)
        
        self.weights = new_weights
        self.last_modification_time = time.time()
        
        return self.weights
    
    def _gradient_ascent_update(self) -> WeightConfiguration:
        """基于历史表现梯度上升更新"""
        if len(self.weight_history) < 2:
            return self.weights.mutate(rate=0.1)
        
        # 计算最近两次权重变化的性能差异
        recent = self.weight_history[-2:]
        perf_delta = recent[1]['performance'] - recent[0]['performance']
        
        # 如果性能提升，沿相同方向继续
        if perf_delta > 0:
            # 小幅增强主导权重
            arr = self.weights.to_array()
            dominant_idx = np.argmax(arr)
            arr[dominant_idx] += 0.05
            arr = np.clip(arr, 0.05, 0.9)
            arr = arr / arr.sum()
            return WeightConfiguration(*arr)
        else:
            # 性能下降，尝试变异
            return self.weights.mutate(rate=0.2)
    
    def _bayesian_update(self) -> WeightConfiguration:
        """基于贝叶斯优化选择权重（简化版）"""
        # 从历史中找到最佳表现的权重配置
        if not self.weight_history:
            return self.weights.mutate(rate=0.1)
        
        best_config = max(self.weight_history, key=lambda x: x['performance'])
        best_weights = WeightConfiguration(**best_config['weights'])
        
        # 在最佳配置附近小幅度探索
        return best_weights.mutate(rate=0.08)
    
    def record_performance(self, reward: float, survival_score: float, 
                          knowledge_gained: int = 0):
        """记录一个周期的表现"""
        self.performance_history.append({
            'timestamp': datetime.now().isoformat(),
            'reward': reward,
            'survival_score': survival_score,
            'knowledge_gained': knowledge_gained,
            'current_weights': asdict(self.weights),
            'action_count': self.total_actions
        })
        
        self.knowledge_acquired += knowledge_gained
        self.cumulative_reward += reward
    
    def get_state_dict(self) -> Dict:
        """获取完整状态（用于持久化）"""
        return {
            'agent_id': self.agent_id,
            'creation_time': self.creation_time,
            'current_weights': asdict(self.weights),
            'weight_history': self.weight_history,
            'performance_history': self.performance_history[-100:],  # 只保留最近100条
            'evolution_strategy': self.evolution_strategy,
            'total_actions': self.total_actions,
            'knowledge_acquired': self.knowledge_acquired,
            'cumulative_reward': self.cumulative_reward,
            'last_modification_time': self.last_modification_time
        }
    
    def load_state_dict(self, state: Dict):
        """从状态恢复"""
        self.agent_id = state['agent_id']
        self.creation_time = state['creation_time']
        self.weights = WeightConfiguration(**state['current_weights'])
        self.weight_history = state.get('weight_history', [])
        self.performance_history = state.get('performance_history', [])
        self.evolution_strategy = state.get('evolution_strategy', 'gradient_ascent')
        self.total_actions = state.get('total_actions', 0)
        self.knowledge_acquired = state.get('knowledge_acquired', 0)
        self.cumulative_reward = state.get('cumulative_reward', 0.0)
        self.last_modification_time = state.get('last_modification_time', time.time())


if __name__ == "__main__":
    # 简单测试
    agent = SelfModifyingAgent("test_001")
    print(f"初始权重: {agent.weights}")
    
    # 模拟一些表现记录
    for i in range(15):
        agent.record_performance(
            reward=0.1 * i,
            survival_score=0.9 - 0.01 * i,
            knowledge_gained=1
        )
        agent.total_actions += 1
    
    # 检查是否应该修改权重
    if agent.should_modify_weights():
        old_weights = agent.weights
        new_weights = agent.modify_weights()
        print(f"权重已修改: {old_weights} -> {new_weights}")
    else:
        print("尚未满足修改条件")
    
    print(f"性能评估: {agent.evaluate_current_performance():.3f}")
