"""
MOSS模拟实验4（改进版）：真实API环境测试
调整参数：提高探索奖励，迫使Agent更积极地探索
"""

import numpy as np
import json
import time
import random
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import sys
sys.path.insert(0, '/workspace/projects')


@dataclass
class APIEnvironment:
    """模拟真实API环境的约束和机会"""
    
    daily_quota: int = 1000
    used_quota: int = 0
    cost_per_call: float = 0.01
    budget: float = 10.0
    
    available_apis: List[str] = None
    api_success_rates: Dict[str, float] = None
    api_values: Dict[str, float] = None  # 各API的价值（探索收益）
    
    time_of_day: int = 0
    day_of_week: int = 0
    
    def __post_init__(self):
        if self.available_apis is None:
            self.available_apis = ['search', 'calculate', 'store', 'notify', 'learn']
        
        if self.api_success_rates is None:
            self.api_success_rates = {api: 0.9 for api in self.available_apis}
        
        # 设置API价值：calculate低价值，search/learn高价值
        if self.api_values is None:
            self.api_values = {
                'search': 2.0,    # 高价值：获取新知识
                'calculate': 0.1, # 低价值：简单计算
                'store': 0.5,     # 中等价值：备份
                'notify': 0.8,    # 中等价值：建立影响
                'learn': 3.0      # 最高价值：自我提升
            }
    
    def call_api(self, api_name: str, agent_id: str) -> Dict:
        """模拟API调用"""
        if self.used_quota >= self.daily_quota:
            return {'success': False, 'error': 'quota_exceeded'}
        
        if self.budget < self.cost_per_call:
            return {'success': False, 'error': 'budget_depleted'}
        
        base_rate = self.api_success_rates.get(api_name, 0.8)
        if self.time_of_day in [9, 10, 11, 14, 15, 16]:
            base_rate *= 0.9
        
        self.used_quota += 1
        self.budget -= self.cost_per_call
        
        success = random.random() < base_rate
        value = self.api_values.get(api_name, 0.5) if success else 0
        
        return {
            'success': success,
            'api': api_name,
            'value': value,
            'cost': self.cost_per_call,
            'remaining_quota': self.daily_quota - self.used_quota,
            'remaining_budget': self.budget,
            'timestamp': datetime.now().isoformat()
        }
    
    def step_time(self, hours: int = 1):
        """推进时间"""
        self.time_of_day = (self.time_of_day + hours) % 24
        if self.time_of_day < hours:
            self.day_of_week = (self.day_of_week + 1) % 7
            self.used_quota = 0
            self.budget = min(self.budget + 5.0, 20.0)


class ImprovedMOSSAgent:
    """改进版MOSS Agent，更注重探索"""
    
    def __init__(self, agent_id: str, environment: APIEnvironment):
        self.agent_id = agent_id
        self.env = environment
        
        self.knowledge_base = {}
        self.reputation_score = 0.5
        self.api_usage = {api: 0 for api in environment.available_apis}
        self.explored_apis = set()
        
        # 学习参数
        self.api_effectiveness = {api: 0.5 for api in environment.available_apis}
        self.cumulative_value = 0.0
    
    def perceive(self) -> Dict:
        """感知环境状态"""
        return {
            'resource_ratio': self.env.budget / 20.0,
            'quota_ratio': 1.0 - (self.env.used_quota / self.env.daily_quota),
            'exploration_ratio': len(self.explored_apis) / len(self.env.available_apis),
            'knowledge_size': len(self.knowledge_base),
            'cumulative_value': self.cumulative_value
        }
    
    def decide_action(self, state: Dict) -> str:
        """基于MOSS框架决策，提高探索权重"""
        
        # 生存评分
        survival_score = (state['resource_ratio'] + state['quota_ratio']) / 2
        
        # 好奇评分 - 提高权重，鼓励探索
        curiosity_score = 1.0 - state['exploration_ratio']
        if state['knowledge_size'] < 20:
            curiosity_score *= 1.5  # 知识少时更积极探索
        
        # 影响评分
        influence_score = self.reputation_score
        
        # 优化评分
        optimization_score = min(state['knowledge_size'] / 50, 1.0)
        
        # 动态权重 - 提高好奇和优化权重
        if state['resource_ratio'] < 0.15:
            weights = [0.5, 0.2, 0.2, 0.1]  # 危机时生存优先
        elif curiosity_score > 0.3:
            weights = [0.15, 0.5, 0.15, 0.2]  # 需要探索时好奇优先
        elif state['knowledge_size'] > 30:
            weights = [0.1, 0.15, 0.25, 0.5]  # 知识多后优化优先
        else:
            weights = [0.2, 0.35, 0.25, 0.2]  # 平衡模式，好奇权重高
        
        objectives = ['survival', 'curiosity', 'influence', 'optimization']
        scores = [survival_score, curiosity_score, influence_score, optimization_score]
        weighted_scores = [s * w for s, w in zip(scores, weights)]
        chosen_objective = objectives[np.argmax(weighted_scores)]
        
        return self._objective_to_action(chosen_objective, state)
    
    def _objective_to_action(self, objective: str, state: Dict) -> str:
        """将目标转换为具体API调用"""
        if objective == 'survival':
            if state['resource_ratio'] < 0.3:
                return 'store'  # 备份
            else:
                # 选择成本效益高的API
                unexplored = set(self.env.available_apis) - self.explored_apis
                if unexplored and random.random() < 0.3:
                    return random.choice(list(unexplored))
                return 'calculate'
        
        elif objective == 'curiosity':
            # 优先使用高价值API
            unexplored = set(self.env.available_apis) - self.explored_apis
            if unexplored:
                # 优先探索高价值API
                unexplored_values = {api: self.env.api_values.get(api, 0.5) 
                                     for api in unexplored}
                return max(unexplored_values, key=unexplored_values.get)
            else:
                # 都探索过了，选择高价值的学习
                return 'learn'
        
        elif objective == 'influence':
            return 'notify'
        
        else:  # optimization
            return 'learn'
    
    def execute(self, action: str) -> Dict:
        """执行动作"""
        result = self.env.call_api(action, self.agent_id)
        
        if result['success']:
            self.explored_apis.add(action)
            self.api_usage[action] += 1
            self.cumulative_value += result['value']
            
            # 知识获取
            if action == 'search' and result['value'] > 0:
                self.knowledge_base[f'fact_{len(self.knowledge_base)}'] = result['value']
            elif action == 'learn' and result['value'] > 0:
                self.reputation_score = min(1.0, self.reputation_score + 0.02)
                self.knowledge_base[f'learning_{len(self.knowledge_base)}'] = result['value']
        
        return result
    
    def step(self) -> Dict:
        """单步运行"""
        state = self.perceive()
        action = self.decide_action(state)
        result = self.execute(action)
        
        return {
            'state': state,
            'action': action,
            'result': result,
            'knowledge_size': len(self.knowledge_base),
            'reputation': self.reputation_score,
            'explored_apis': len(self.explored_apis),
            'cumulative_value': self.cumulative_value
        }


def run_improved_experiment4(
    duration_hours: int = 168,
    log_interval: int = 12
) -> Dict:
    """改进版实验4"""
    print("=" * 70)
    print("MOSS Simulation Experiment 4 (Improved): Real-World API Environment")
    print("=" * 70)
    print(f"Duration: {duration_hours} hours (1 week)")
    print("Parameters: Increased exploration rewards, API value differentiation")
    print()
    
    env = APIEnvironment()
    agent = ImprovedMOSSAgent("moss_realworld_v2", env)
    
    history = []
    
    for hour in range(duration_hours):
        result = agent.step()
        env.step_time(1)
        
        if hour % log_interval == 0:
            day = hour // 24
            time_str = f"Day {day}, Hour {env.time_of_day}"
            
            print(f"[{time_str}] Action: {result['action']:<8} "
                  f"Budget: ${env.budget:>5.2f} "
                  f"Knowledge: {result['knowledge_size']:>3} "
                  f"Rep: {result['reputation']:.3f} "
                  f"Explored: {result['explored_apis']}/5 "
                  f"Value: {result['cumulative_value']:>6.1f}")
            
            history.append({
                'hour': hour,
                'day': day,
                'budget': env.budget,
                'knowledge_size': result['knowledge_size'],
                'reputation': result['reputation'],
                'explored_apis': result['explored_apis'],
                'cumulative_value': result['cumulative_value'],
                'action': result['action']
            })
    
    print("\n" + "=" * 70)
    print("Experiment Complete")
    print("=" * 70)
    
    final_knowledge = len(agent.knowledge_base)
    final_reputation = agent.reputation_score
    final_explored = len(agent.explored_apis)
    
    print(f"\nFinal Statistics:")
    print(f"  Total knowledge acquired: {final_knowledge}")
    print(f"  Final reputation: {final_reputation:.3f}")
    print(f"  APIs explored: {final_explored}/5")
    print(f"  Cumulative value: {agent.cumulative_value:.1f}")
    print(f"  Remaining budget: ${env.budget:.2f}")
    
    print(f"\nAPI Usage Distribution:")
    for api, count in agent.api_usage.items():
        pct = count / sum(agent.api_usage.values()) * 100 if sum(agent.api_usage.values()) > 0 else 0
        print(f"  {api:10s}: {count:>3} calls ({pct:>5.1f}%)")
    
    # 成功标准
    passed = (
        final_knowledge > 30 and
        final_reputation > 0.6 and
        final_explored >= 4 and
        agent.cumulative_value > 50
    )
    
    print(f"\nResult: {'PASS ✓' if passed else 'FAIL ✗'}")
    print(f"  (Knowledge > 30: {'✓' if final_knowledge > 30 else '✗'}), "
          f"(Reputation > 0.6: {'✓' if final_reputation > 0.6 else '✗'}), "
          f"(Explored >= 4: {'✓' if final_explored >= 4 else '✗'}), "
          f"(Value > 50: {'✓' if agent.cumulative_value > 50 else '✗'})")
    
    return {
        'duration_hours': duration_hours,
        'final_knowledge': final_knowledge,
        'final_reputation': final_reputation,
        'final_explored': final_explored,
        'cumulative_value': agent.cumulative_value,
        'remaining_budget': env.budget,
        'api_usage': agent.api_usage,
        'history': history,
        'passed': passed
    }


if __name__ == "__main__":
    results = run_improved_experiment4()
    
    with open('/workspace/projects/moss/sandbox/exp4_results_v2.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print("\n[Results saved to sandbox/exp4_results_v2.json]")
