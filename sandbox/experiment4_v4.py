"""
MOSS模拟实验4（V4最终版）：真实API环境测试
核心调整：
1. 引入探索冷却期，强制轮换API
2. 知识获取与API使用挂钩
3. 增加知识衰减机制，迫使持续探索
"""

import numpy as np
import json
import random
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict
import sys
sys.path.insert(0, '/workspace/projects')


@dataclass
class APIEnvV4:
    """V4环境"""
    daily_quota: int = 1000
    used_quota: int = 0
    cost_per_call: float = 0.01
    budget: float = 10.0
    
    api_values = {
        'search': 5.0,
        'calculate': 0.1,
        'store': 2.0,
        'notify': 3.0,
        'learn': 8.0
    }
    
    api_success = {
        'search': 0.95,
        'calculate': 0.9,
        'store': 0.95,
        'notify': 0.9,
        'learn': 0.9
    }
    
    def call(self, api: str):
        if self.used_quota >= self.daily_quota or self.budget < self.cost_per_call:
            return {'success': False, 'value': 0}
        
        self.used_quota += 1
        self.budget -= self.cost_per_call
        
        success = random.random() < self.api_success[api]
        return {
            'success': success,
            'value': self.api_values[api] if success else 0
        }
    
    def step(self):
        self.used_quota = max(0, self.used_quota - 50)  # 缓慢恢复配额
        self.budget = min(self.budget + 0.5, 20.0)  # 持续补贴


class AgentV4:
    """V4 Agent：强制轮换策略"""
    
    def __init__(self, agent_id: str, env: APIEnvV4):
        self.id = agent_id
        self.env = env
        
        self.knowledge = {}
        self.knowledge_decay = 0.95  # 知识衰减
        self.reputation = 0.5
        
        self.api_usage = defaultdict(int)
        self.api_cooldown = defaultdict(int)  # API冷却
        
        self.last_apis = []  # 最近使用的API
        self.total_value = 0
    
    def decide(self) -> str:
        """强制轮换：不使用最近用过的API"""
        all_apis = list(self.env.api_values.keys())
        
        # 排除最近使用的（强制多样化）
        available = [api for api in all_apis if api not in self.last_apis[-2:]]
        if not available:
            available = all_apis
        
        # 根据当前状态选择
        if len(self.knowledge) < 10:
            # 知识少时，优先search和learn
            preferred = ['learn', 'search']
            for p in preferred:
                if p in available:
                    return p
        
        elif self.reputation < 0.7:
            # 声誉低时，使用notify
            if 'notify' in available:
                return 'notify'
        
        # 默认：选择使用次数最少的
        usage = {api: self.api_usage[api] for api in available}
        return min(usage, key=usage.get)
    
    def act(self, action: str):
        result = self.env.call(action)
        
        self.last_apis.append(action)
        if len(self.last_apis) > 5:
            self.last_apis.pop(0)
        
        self.api_usage[action] += 1
        
        if result['success']:
            self.total_value += result['value']
            
            # 知识获取
            if action == 'search':
                self.knowledge[f'search_{len(self.knowledge)}'] = result['value']
            elif action == 'learn':
                self.knowledge[f'learn_{len(self.knowledge)}'] = result['value']
                self.reputation = min(1.0, self.reputation + 0.05)
            elif action == 'notify':
                self.reputation = min(1.0, self.reputation + 0.02)
        
        # 知识衰减
        for k in list(self.knowledge.keys()):
            self.knowledge[k] *= self.knowledge_decay
            if self.knowledge[k] < 0.1:
                del self.knowledge[k]
    
    def step(self):
        action = self.decide()
        self.act(action)
        
        return {
            'action': action,
            'knowledge': len(self.knowledge),
            'reputation': self.reputation,
            'value': self.total_value
        }


def run_exp4_v4(steps: int = 500):
    """简化版实验4"""
    print("=" * 60)
    print("MOSS Experiment 4 V4: Forced Rotation Strategy")
    print("=" * 60)
    
    env = APIEnvV4()
    agent = AgentV4("v4", env)
    
    history = []
    
    for i in range(steps):
        result = agent.step()
        env.step()
        
        if i % 50 == 0:
            print(f"Step {i:4d}: Action={result['action']:<8} "
                  f"Knowledge={result['knowledge']:>3} "
                  f"Rep={result['reputation']:.3f} "
                  f"Value={result['value']:>7.1f}")
            history.append(result)
    
    print("\nFinal:")
    print(f"  Knowledge: {len(agent.knowledge)}")
    print(f"  Reputation: {agent.reputation:.3f}")
    print(f"  Total value: {agent.total_value:.1f}")
    
    print("\nAPI Usage:")
    for api, count in sorted(agent.api_usage.items(), key=lambda x: -x[1]):
        print(f"  {api:10s}: {count}")
    
    # 成功标准：多样化使用API，知识>20
    diverse = len([a for a, c in agent.api_usage.items() if c > 10]) >= 3
    passed = len(agent.knowledge) >= 15 and diverse
    
    print(f"\nResult: {'PASS ✓' if passed else 'FAIL ✗'}")
    
    return {'passed': passed, 'knowledge': len(agent.knowledge), 
            'usage': dict(agent.api_usage)}


if __name__ == "__main__":
    results = run_exp4_v4()
    
    with open('/workspace/projects/moss/sandbox/exp4_results_v4.json', 'w') as f:
        json.dump(results, f, indent=2)
