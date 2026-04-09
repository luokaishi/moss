"""
MOSS Controlled Experiments - Baseline Strategies
验证核心假设：多目标自驱力 > 单目标/随机策略
"""

import random
import numpy as np
from typing import Dict, List, Tuple
from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    """所有策略的基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.action_history = []
        self.metrics_history = []
        
    @abstractmethod
    def decide(self, state: Dict) -> str:
        """根据当前状态决定动作"""
        pass
    
    def record_action(self, action: str, state: Dict):
        """记录动作和状态"""
        self.action_history.append({
            'step': len(self.action_history),
            'action': action,
            'state': state.copy()
        })
    
    def get_action_distribution(self) -> Dict[str, int]:
        """获取动作分布统计"""
        distribution = {'explore': 0, 'conserve': 0, 'influence': 0, 'optimize': 0}
        for record in self.action_history:
            action = record['action']
            if action in distribution:
                distribution[action] += 1
        return distribution
    
    def reset(self):
        """重置策略状态"""
        self.action_history = []
        self.metrics_history = []


class RandomStrategy(BaseStrategy):
    """
    随机策略 - 下界基准
    完全随机选择动作，没有任何目标指导
    """
    
    def __init__(self):
        super().__init__("Random")
        self.actions = ['explore', 'conserve', 'influence', 'optimize']
    
    def decide(self, state: Dict) -> str:
        """完全随机选择"""
        action = random.choice(self.actions)
        self.record_action(action, state)
        return action


class CuriosityOnlyStrategy(BaseStrategy):
    """
    仅好奇策略 - 极端探索
    始终选择探索，无视资源状态
    测试：单目标（探索）是否足够
    """
    
    def __init__(self):
        super().__init__("CuriosityOnly")
    
    def decide(self, state: Dict) -> str:
        """始终探索"""
        action = 'explore'
        self.record_action(action, state)
        return action


class SurvivalOnlyStrategy(BaseStrategy):
    """
    仅生存策略 - 极端保守
    始终选择保存资源，永不冒险
    测试：单目标（生存）是否导致停滞
    """
    
    def __init__(self):
        super().__init__("SurvivalOnly")
    
    def decide(self, state: Dict) -> str:
        """始终保存"""
        action = 'conserve'
        self.record_action(action, state)
        return action


class FixedWeightsStrategy(BaseStrategy):
    """
    固定权重策略
    4个目标权重固定为0.25，从不改变
    测试：动态调整是否优于静态分配
    """
    
    def __init__(self):
        super().__init__("FixedWeights")
        self.weights = {
            'explore': 0.25,
            'conserve': 0.25,
            'influence': 0.25,
            'optimize': 0.25
        }
        self.actions = list(self.weights.keys())
    
    def decide(self, state: Dict) -> str:
        """基于固定权重的随机选择"""
        action = random.choices(
            self.actions,
            weights=[self.weights[a] for a in self.actions]
        )[0]
        self.record_action(action, state)
        return action


class MOSSStrategy(BaseStrategy):
    """
    MOSS策略 - 我们的方法
    根据资源状态动态调整4个目标的权重
    """
    
    def __init__(self):
        super().__init__("MOSS")
        self.actions = ['explore', 'conserve', 'influence', 'optimize']
    
    def allocate_weights(self, state: Dict) -> Dict[str, float]:
        """根据资源状态分配权重"""
        resource_ratio = state.get('resource_ratio', 1.0)
        
        if resource_ratio < 0.2:
            # Crisis: 优先生存
            weights = {
                'explore': 0.1,
                'conserve': 0.6,
                'influence': 0.2,
                'optimize': 0.1
            }
        elif resource_ratio < 0.5:
            # Concerned: 平衡探索与保存
            weights = {
                'explore': 0.3,
                'conserve': 0.5,
                'influence': 0.15,
                'optimize': 0.05
            }
        else:
            # Normal: 优先探索
            weights = {
                'explore': 0.6,
                'conserve': 0.2,
                'influence': 0.15,
                'optimize': 0.05
            }
        
        return weights
    
    def decide(self, state: Dict) -> str:
        """基于动态权重的选择"""
        weights = self.allocate_weights(state)
        action = random.choices(
            self.actions,
            weights=[weights[a] for a in self.actions]
        )[0]
        self.record_action(action, state)
        return action


# 策略工厂函数
def get_strategy(strategy_name: str) -> BaseStrategy:
    """根据名称获取策略实例"""
    strategies = {
        'random': RandomStrategy,
        'curiosity_only': CuriosityOnlyStrategy,
        'survival_only': SurvivalOnlyStrategy,
        'fixed_weights': FixedWeightsStrategy,
        'moss': MOSSStrategy
    }
    
    if strategy_name not in strategies:
        raise ValueError(f"Unknown strategy: {strategy_name}. Available: {list(strategies.keys())}")
    
    return strategies[strategy_name]()


# 所有可用策略列表
AVAILABLE_STRATEGIES = [
    'random',
    'curiosity_only',
    'survival_only',
    'fixed_weights',
    'moss'
]


if __name__ == '__main__':
    # 简单测试
    print("Testing all strategies...")
    
    for strategy_name in AVAILABLE_STRATEGIES:
        strategy = get_strategy(strategy_name)
        print(f"\n{strategy.name}:")
        
        # 模拟10步
        for step in range(10):
            state = {'resource_ratio': 0.8 - step * 0.05}  # 资源逐渐减少
            action = strategy.decide(state)
            print(f"  Step {step}: {action}")
        
        distribution = strategy.get_action_distribution()
        print(f"  Distribution: {distribution}")
