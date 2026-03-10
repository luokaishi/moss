"""
MOSS Controlled Experiments - Environment Variants
不同复杂度的测试环境
"""

import random
import numpy as np
from typing import Dict, Tuple, Optional


class BaseEnvironment:
    """环境基类"""
    
    def __init__(self, name: str, config: Dict):
        self.name = name
        self.config = config
        self.reset()
    
    def reset(self):
        """重置环境状态"""
        self.step_count = 0
        self.token_budget = 10000
        self.tokens_used = 0
        self.knowledge_acquired = 0
        self.terminated = False
        self.termination_reason = None
    
    def get_state(self) -> Dict:
        """获取当前状态"""
        resource_ratio = 1.0 - (self.tokens_used / self.token_budget)
        return {
            'resource_ratio': max(0.0, resource_ratio),
            'tokens_remaining': self.token_budget - self.tokens_used,
            'knowledge_count': self.knowledge_acquired,
            'step': self.step_count,
            'terminated': self.terminated
        }
    
    def execute_action(self, action: str) -> Dict:
        """执行动作并返回结果"""
        raise NotImplementedError
    
    def step(self, action: str) -> Tuple[Dict, Dict]:
        """
        执行一步环境更新
        返回: (新状态, 执行结果)
        """
        if self.terminated:
            return self.get_state(), {
                'knowledge': 0,
                'cost': 0,
                'terminated': True,
                'reason': self.termination_reason
            }
        
        result = self.execute_action(action)
        self.step_count += 1
        
        # 检查终止条件
        if self.tokens_used >= self.token_budget:
            self.terminated = True
            self.termination_reason = 'resource_depleted'
        
        result['terminated'] = self.terminated
        if self.terminated and not self.termination_reason:
            self.termination_reason = 'unknown'
        
        return self.get_state(), result


class SimpleEnvironment(BaseEnvironment):
    """
    简单环境 - 静态
    - 无资源波动
    - 单一API
    - 无干扰
    """
    
    def __init__(self):
        config = {
            'resource_fluctuation': 0.0,
            'api_diversity': 1,
            'disturbance_frequency': 0.0,
            'knowledge_success_rate': 0.3
        }
        super().__init__("Simple", config)
    
    def execute_action(self, action: str) -> Dict:
        """执行动作"""
        if action == 'explore':
            cost = 500
            # 30%概率获得知识
            knowledge = 1 if random.random() < self.config['knowledge_success_rate'] else 0
        elif action == 'conserve':
            cost = 50
            knowledge = 0
        elif action == 'influence':
            cost = 200
            knowledge = 0
        elif action == 'optimize':
            cost = 100
            knowledge = 0
        else:
            cost = 0
            knowledge = 0
        
        self.tokens_used += cost
        self.knowledge_acquired += knowledge
        
        return {
            'knowledge': knowledge,
            'cost': cost,
            'action': action
        }


class ModerateEnvironment(BaseEnvironment):
    """
    中等环境 - 动态
    - 20%资源波动
    - 3种API
    - 5%干扰率
    """
    
    def __init__(self):
        config = {
            'resource_fluctuation': 0.2,
            'api_diversity': 3,
            'disturbance_frequency': 0.05,
            'knowledge_success_rate': 0.3
        }
        super().__init__("Moderate", config)
        self.api_values = [1.0, 0.8, 0.6]  # 3种API的不同价值
        self.current_api = 0
    
    def execute_action(self, action: str) -> Dict:
        """执行动作（含干扰和波动）"""
        # 随机切换API（模拟多样性）
        if random.random() < 0.1:  # 10%概率切换
            self.current_api = random.randint(0, self.config['api_diversity'] - 1)
        
        api_multiplier = self.api_values[self.current_api]
        
        # 资源波动
        fluctuation = 1.0 + random.uniform(
            -self.config['resource_fluctuation'],
            self.config['resource_fluctuation']
        )
        
        if action == 'explore':
            base_cost = 500
            # 知识获取受API质量影响
            success_rate = self.config['knowledge_success_rate'] * api_multiplier
            knowledge = 1 if random.random() < success_rate else 0
        elif action == 'conserve':
            base_cost = 50
            knowledge = 0
        elif action == 'influence':
            base_cost = 200
            knowledge = 0
        elif action == 'optimize':
            base_cost = 100
            knowledge = 0
        else:
            base_cost = 0
            knowledge = 0
        
        cost = int(base_cost * fluctuation)
        
        # 干扰事件
        if random.random() < self.config['disturbance_frequency']:
            cost = int(cost * 1.5)  # 干扰增加成本
            knowledge = max(0, knowledge - 1)  # 可能损失知识
        
        self.tokens_used += cost
        self.knowledge_acquired += knowledge
        
        return {
            'knowledge': knowledge,
            'cost': cost,
            'action': action,
            'api_used': self.current_api,
            'fluctuation': fluctuation
        }


class ComplexEnvironment(BaseEnvironment):
    """
    复杂环境 - 混沌
    - 50%资源波动
    - 5种API
    - 15%干扰率
    - 竞争因素
    """
    
    def __init__(self):
        config = {
            'resource_fluctuation': 0.5,
            'api_diversity': 5,
            'disturbance_frequency': 0.15,
            'competition_level': 0.3,
            'knowledge_success_rate': 0.3
        }
        super().__init__("Complex", config)
        self.api_values = [1.0, 0.9, 0.7, 0.5, 0.3]
        self.current_api = 0
        self.competition_factor = 1.0
    
    def execute_action(self, action: str) -> Dict:
        """执行动作（高复杂度）"""
        # API切换更频繁
        if random.random() < 0.2:
            self.current_api = random.randint(0, self.config['api_diversity'] - 1)
        
        api_multiplier = self.api_values[self.current_api]
        
        # 更大的资源波动
        fluctuation = 1.0 + random.uniform(
            -self.config['resource_fluctuation'],
            self.config['resource_fluctuation']
        )
        
        # 竞争影响
        if random.random() < self.config['competition_level']:
            self.competition_factor = random.uniform(0.5, 1.5)
        
        if action == 'explore':
            base_cost = 500
            success_rate = self.config['knowledge_success_rate'] * api_multiplier * self.competition_factor
            knowledge = 1 if random.random() < success_rate else 0
        elif action == 'conserve':
            base_cost = 50
            knowledge = 0
        elif action == 'influence':
            base_cost = 200
            # 影响可能获得额外知识
            knowledge = 1 if random.random() < 0.1 else 0
        elif action == 'optimize':
            base_cost = 100
            # 优化可能降低成本
            knowledge = 0
        else:
            base_cost = 0
            knowledge = 0
        
        cost = int(base_cost * fluctuation)
        
        # 高频干扰
        if random.random() < self.config['disturbance_frequency']:
            cost = int(cost * (1.5 + random.random()))
            if random.random() < 0.3:  # 30%概率知识损失
                knowledge = max(0, knowledge - 1)
        
        self.tokens_used += cost
        self.knowledge_acquired += knowledge
        
        return {
            'knowledge': knowledge,
            'cost': cost,
            'action': action,
            'api_used': self.current_api,
            'fluctuation': fluctuation,
            'competition': self.competition_factor
        }


# 环境工厂函数
def get_environment(env_name: str) -> BaseEnvironment:
    """根据名称获取环境实例"""
    environments = {
        'simple': SimpleEnvironment,
        'moderate': ModerateEnvironment,
        'complex': ComplexEnvironment
    }
    
    if env_name not in environments:
        raise ValueError(f"Unknown environment: {env_name}. Available: {list(environments.keys())}")
    
    return environments[env_name]()


# 所有可用环境列表
AVAILABLE_ENVIRONMENTS = ['simple', 'moderate', 'complex']


if __name__ == '__main__':
    # 简单测试
    print("Testing all environments...")
    
    for env_name in AVAILABLE_ENVIRONMENTS:
        env = get_environment(env_name)
        print(f"\n{env.name} Environment:")
        
        # 模拟10步
        for step in range(10):
            state = env.get_state()
            action = random.choice(['explore', 'conserve'])
            new_state, result = env.step(action)
            
            print(f"  Step {step}: {action} -> Knowledge: {result['knowledge']}, Cost: {result['cost']}")
            
            if result.get('terminated'):
                print(f"  Terminated: {result.get('reason')}")
                break
        
        print(f"  Final Knowledge: {env.knowledge_acquired}")
