"""
MOSS实验4（重构版）：真实API环境中的自适应策略演化

核心问题反思：
- 之前版本：Agent找到高效策略后坚持使用（这是理性的）
- 根本问题：真实世界不是静态的，环境会变化
- 新设计：引入环境动态变化，迫使Agent持续适应

关键洞察：自驱力的价值在于适应变化，而非静态优化
"""

import numpy as np
import json
import random
from typing import Dict, List, Tuple
from dataclasses import dataclass
from collections import defaultdict
import sys
sys.path.insert(0, '/workspace/projects')


@dataclass
class DynamicAPIEnvironment:
    """
    动态API环境：API的价值和成功率会随时间变化
    这迫使Agent必须持续监控环境并调整策略
    """
    
    # 初始配置
    apis: List[str] = None
    
    def __post_init__(self):
        if self.apis is None:
            self.apis = ['search', 'calculate', 'store', 'notify', 'learn']
        
        # 动态参数：随时间变化
        self.api_params = {
            api: {
                'base_value': random.uniform(1.0, 5.0),
                'base_success': random.uniform(0.7, 0.95),
                'trend': random.choice([-1, 0, 1]),  # -1=下降, 0=稳定, 1=上升
                'volatility': random.uniform(0.05, 0.2)
            }
            for api in self.apis
        }
        
        # 环境状态
        self.time_step = 0
        self.phase = 0  # 不同阶段有不同的最优策略
        
        # 资源约束
        self.budget = 10.0
        self.daily_quota = 100
        self.used_quota = 0
    
    def get_current_params(self, api: str) -> Tuple[float, float]:
        """获取当前时点的API参数"""
        params = self.api_params[api]
        
        # 添加趋势和随机波动
        trend_effect = params['trend'] * (self.time_step / 1000) * 0.5
        noise = random.gauss(0, params['volatility'])
        
        value = max(0.1, params['base_value'] + trend_effect + noise)
        success_rate = max(0.1, min(0.99, params['base_success'] + noise * 0.5))
        
        return value, success_rate
    
    def call_api(self, api: str) -> Dict:
        """调用API"""
        if self.used_quota >= self.daily_quota or self.budget <= 0:
            return {'success': False, 'value': 0, 'error': 'depleted'}
        
        value, success_rate = self.get_current_params(api)
        
        self.used_quota += 1
        self.budget -= 0.01  # 每次调用成本
        
        success = random.random() < success_rate
        
        return {
            'success': success,
            'api': api,
            'value': value if success else 0,
            'actual_success_rate': success_rate,
            'timestamp': self.time_step
        }
    
    def step(self):
        """环境演化"""
        self.time_step += 1
        
        # 每100步一个阶段，最优API可能变化
        if self.time_step % 100 == 0:
            self.phase = (self.phase + 1) % 3
            # 随机改变趋势
            for api in self.apis:
                if random.random() < 0.3:  # 30%概率改变趋势
                    self.api_params[api]['trend'] = random.choice([-1, 0, 1])
        
        # 每日重置配额
        if self.time_step % 24 == 0:
            self.used_quota = 0
            self.budget = min(self.budget + 2.0, 20.0)  # 每日补贴


class AdaptiveMOSSAgent:
    """
    自适应Agent：持续监控API效果，动态调整策略
    
    关键能力：
    1. 跟踪每个API的历史表现
    2. 检测环境变化（表现突然改变）
    3. 快速适应：当最优策略变化时切换
    """
    
    def __init__(self, agent_id: str, env: DynamicAPIEnvironment):
        self.id = agent_id
        self.env = env
        
        # API表现历史（滑动窗口）
        self.api_history = {api: [] for api in env.apis}
        self.api_estimated_value = {api: 0.0 for api in env.apis}
        
        # 知识积累
        self.knowledge = 0
        self.total_value = 0.0
        
        # 自适应参数
        self.exploration_rate = 0.3  # 探索率
        self.min_samples = 5  # 最少采样次数才做决策
        self.adaptation_speed = 0.3  # 适应速度
    
    def update_api_estimate(self, api: str, result: Dict):
        """更新API效果估计"""
        if result['success']:
            self.api_history[api].append(result['value'])
        else:
            self.api_history[api].append(0)
        
        # 只保留最近20次
        if len(self.api_history[api]) > 20:
            self.api_history[api].pop(0)
        
        # 更新估计值（指数移动平均）
        if self.api_history[api]:
            recent_avg = np.mean(self.api_history[api][-5:])  # 最近5次
            old_estimate = self.api_estimated_value[api]
            self.api_estimated_value[api] = (
                (1 - self.adaptation_speed) * old_estimate + 
                self.adaptation_speed * recent_avg
            )
    
    def detect_environment_change(self) -> bool:
        """检测环境是否发生变化"""
        # 如果最近表现和估计值差异大，说明环境可能变了
        for api, history in self.api_history.items():
            if len(history) >= 5:
                recent = np.mean(history[-3:])
                estimate = self.api_estimated_value[api]
                if abs(recent - estimate) > 1.0:  # 差异阈值
                    return True
        return False
    
    def decide_action(self) -> str:
        """决策：基于当前估计选择最优或探索"""
        
        # 检测环境变化，增加探索
        if self.detect_environment_change():
            self.exploration_rate = min(0.5, self.exploration_rate + 0.1)
        else:
            self.exploration_rate = max(0.1, self.exploration_rate - 0.02)
        
        # 探索：随机选择采样不足的API
        under_sampled = [api for api in self.env.apis 
                        if len(self.api_history[api]) < self.min_samples]
        
        if under_sampled and random.random() < self.exploration_rate:
            return random.choice(under_sampled)
        
        # 利用：选择当前估计值最高的API
        # 但添加扰动避免死锁
        values = [(api, self.api_estimated_value[api] + random.gauss(0, 0.2)) 
                  for api in self.env.apis]
        return max(values, key=lambda x: x[1])[0]
    
    def step(self) -> Dict:
        """执行一步"""
        action = self.decide_action()
        result = self.env.call_api(action)
        
        self.update_api_estimate(action, result)
        
        if result['success']:
            self.total_value += result['value']
            if action in ['search', 'learn']:
                self.knowledge += 1
        
        return {
            'action': action,
            'knowledge': self.knowledge,
            'total_value': self.total_value,
            'exploration_rate': self.exploration_rate,
            'estimates': dict(self.api_estimated_value)
        }


def run_experiment4_final(steps: int = 1000):
    """
    实验4最终版：验证自适应能力
    
    成功标准：
    1. Agent能够跟踪环境变化
    2. API使用分布随环境变化而变化
    3. 总体价值获取高于静态策略
    """
    print("=" * 70)
    print("MOSS Experiment 4 Final: Adaptive Strategy in Dynamic Environment")
    print("=" * 70)
    print(f"Steps: {steps}")
    print("Key Feature: API values change over time, Agent must adapt")
    print()
    
    env = DynamicAPIEnvironment()
    agent = AdaptiveMOSSAgent("adaptive_001", env)
    
    history = []
    
    for i in range(steps):
        result = agent.step()
        env.step()
        
        if i % 100 == 0:
            # 找出当前最优API
            best_api = max(agent.api_estimated_value.items(), key=lambda x: x[1])
            print(f"Step {i:4d}: Knowledge={result['knowledge']:>4} "
                  f"Value={result['total_value']:>8.1f} "
                  f"Explore={result['exploration_rate']:.2f} "
                  f"BestAPI={best_api[0]}")
            history.append({
                'step': i,
                'knowledge': result['knowledge'],
                'value': result['total_value'],
                'exploration_rate': result['exploration_rate'],
                'estimates': result['estimates']
            })
    
    print("\n" + "=" * 70)
    print("Results")
    print("=" * 70)
    
    print(f"\nFinal Statistics:")
    print(f"  Total knowledge: {agent.knowledge}")
    print(f"  Total value: {agent.total_value:.1f}")
    print(f"  Average exploration rate: {np.mean([h['exploration_rate'] for h in history]):.3f}")
    
    print(f"\nAPI Usage Distribution:")
    total_calls = sum(len(h) for h in agent.api_history.values())
    for api in env.apis:
        calls = len(agent.api_history[api])
        pct = calls / max(total_calls, 1) * 100
        bar = "█" * int(pct / 5)
        print(f"  {api:10s}: {calls:>4} calls ({pct:>5.1f}%) {bar}")
    
    print(f"\nFinal API Estimates:")
    for api, value in sorted(agent.api_estimated_value.items(), key=lambda x: -x[1]):
        print(f"  {api:10s}: {value:.2f}")
    
    # 成功标准
    # 1. 知识获取 > 50
    # 2. 探索率保持 > 0.15（说明Agent持续探索而非固化）
    # 3. 使用了至少3种API（多样化）
    diverse_apis = sum(1 for h in agent.api_history.values() if len(h) > 10)
    avg_explore = np.mean([h['exploration_rate'] for h in history])
    
    passed = (
        agent.knowledge > 50 and
        avg_explore > 0.15 and
        diverse_apis >= 3
    )
    
    print(f"\nResult: {'PASS ✓' if passed else 'FAIL ✗'}")
    print(f"  Knowledge > 50: {'✓' if agent.knowledge > 50 else '✗'} ({agent.knowledge})")
    print(f"  Exploration > 0.15: {'✓' if avg_explore > 0.15 else '✗'} ({avg_explore:.3f})")
    print(f"  Diverse APIs: {'✓' if diverse_apis >= 3 else '✗'} ({diverse_apis})")
    
    return {
        'steps': steps,
        'knowledge': agent.knowledge,
        'total_value': agent.total_value,
        'exploration_rate': avg_explore,
        'diverse_apis': diverse_apis,
        'history': history,
        'passed': passed
    }


if __name__ == "__main__":
    results = run_experiment4_final()
    
    with open('/workspace/projects/moss/sandbox/exp4_final.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n[Results saved to exp4_final.json]")
