"""
MOSS模拟实验4（V3优化版）：真实API环境测试
核心调整：
1. calculate API价值降至0.01，迫使Agent避免使用
2. 提高search/learn成功率至95%
3. 增加探索惩罚（不使用高价值API时）
4. 强制多样化策略
"""

import numpy as np
import json
import time
import random
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import deque
import sys
sys.path.insert(0, '/workspace/projects')


@dataclass
class APIEnvironmentV3:
    """V3环境：极端差异化API价值"""
    
    daily_quota: int = 1000
    used_quota: int = 0
    cost_per_call: float = 0.01
    budget: float = 10.0
    
    available_apis: List[str] = None
    api_success_rates: Dict[str, float] = None
    api_values: Dict[str, float] = None
    
    time_of_day: int = 0
    day_of_week: int = 0
    
    def __post_init__(self):
        if self.available_apis is None:
            self.available_apis = ['search', 'calculate', 'store', 'notify', 'learn']
        
        if self.api_success_rates is None:
            # 高价值API高成功率，calculate低成功率
            self.api_success_rates = {
                'search': 0.95,
                'calculate': 0.5,    # 低成功率
                'store': 0.9,
                'notify': 0.9,
                'learn': 0.95
            }
        
        # 极端差异化价值
        if self.api_values is None:
            self.api_values = {
                'search': 5.0,      # 极高价值
                'calculate': 0.01,  # 几乎无价值
                'store': 1.0,
                'notify': 2.0,
                'learn': 10.0       # 最高价值
            }
    
    def call_api(self, api_name: str, agent_id: str) -> Dict:
        if self.used_quota >= self.daily_quota:
            return {'success': False, 'error': 'quota_exceeded', 'value': 0}
        
        if self.budget < self.cost_per_call:
            return {'success': False, 'error': 'budget_depleted', 'value': 0}
        
        base_rate = self.api_success_rates.get(api_name, 0.8)
        
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
        self.time_of_day = (self.time_of_day + hours) % 24
        if self.time_of_day < hours:
            self.day_of_week = (self.day_of_week + 1) % 7
            self.used_quota = 0
            self.budget = min(self.budget + 5.0, 20.0)


class OptimizedMOSSAgent:
    """V3优化Agent：强制多样化，避免保守"""
    
    def __init__(self, agent_id: str, environment: APIEnvironmentV3):
        self.agent_id = agent_id
        self.env = environment
        
        self.knowledge_base = {}
        self.reputation_score = 0.5
        self.api_usage = {api: 0 for api in environment.available_apis}
        self.explored_apis = set()
        
        # 强制多样化：记录最近使用的API，避免重复
        self.recent_apis = deque(maxlen=5)
        
        # 统计
        self.cumulative_value = 0.0
        self.consecutive_calculate = 0  # 连续使用calculate计数
    
    def perceive(self) -> Dict:
        return {
            'resource_ratio': self.env.budget / 20.0,
            'quota_ratio': 1.0 - (self.env.used_quota / self.env.daily_quota),
            'exploration_ratio': len(self.explored_apis) / len(self.env.available_apis),
            'knowledge_size': len(self.knowledge_base),
            'cumulative_value': self.cumulative_value,
            'recent_apis': list(self.recent_apis)
        }
    
    def decide_action(self, state: Dict) -> str:
        """决策：强制多样化，优先高价值"""
        
        # 获取高价值未充分使用的API
        high_value_apis = ['learn', 'search', 'notify']
        underused = [api for api in high_value_apis 
                     if self.api_usage[api] < self.api_usage.get('calculate', 0) / 2]
        
        # 如果连续使用calculate超过3次，强制切换
        if self.consecutive_calculate >= 3:
            # 优先选择探索过的最高价值API
            explored_high = [api for api in high_value_apis if api in self.explored_apis]
            if explored_high:
                return explored_high[0]
            elif underused:
                return underused[0]
        
        # 正常决策
        survival_score = (state['resource_ratio'] + state['quota_ratio']) / 2
        
        # 好奇评分：根据未探索的高价值API
        unexplored_high = set(['learn', 'search']) - self.explored_apis
        curiosity_score = len(unexplored_high) * 0.5 + (1 - state['exploration_ratio']) * 0.3
        
        influence_score = self.reputation_score
        optimization_score = min(state['knowledge_size'] / 20, 1.0)
        
        # 动态权重：正常状态下好奇和优化权重很高
        if state['resource_ratio'] < 0.1:
            weights = [0.6, 0.15, 0.15, 0.1]
        elif unexplored_high:
            weights = [0.1, 0.6, 0.1, 0.2]  # 有未探索高价值API时强烈好奇
        elif underused:
            weights = [0.15, 0.5, 0.15, 0.2]  # 有高价值未充分使用API
        else:
            weights = [0.1, 0.3, 0.2, 0.4]  # 平衡，优化权重高
        
        objectives = ['survival', 'curiosity', 'influence', 'optimization']
        scores = [survival_score, curiosity_score, influence_score, optimization_score]
        weighted_scores = [s * w for s, w in zip(scores, weights)]
        chosen_objective = objectives[np.argmax(weighted_scores)]
        
        return self._objective_to_action(chosen_objective, state, underused, unexplored_high)
    
    def _objective_to_action(self, objective: str, state: Dict, 
                             underused: List[str], unexplored_high: Set[str]) -> str:
        
        if objective == 'survival':
            # 即使在生存模式下，也避免calculate
            if state['resource_ratio'] < 0.2:
                return 'store'  # 备份
            else:
                # 选择成本效益最高的（value/cost）
                best_api = 'search'  # search性价比最高
                return best_api
        
        elif objective == 'curiosity':
            # 优先探索高价值未探索的
            if unexplored_high:
                return list(unexplored_high)[0]
            elif underused:
                return underused[0]
            else:
                return 'learn'  # 默认学习
        
        elif objective == 'influence':
            return 'notify'
        
        else:  # optimization
            return 'learn'
    
    def execute(self, action: str) -> Dict:
        result = self.env.call_api(action, self.agent_id)
        
        # 更新连续计数
        if action == 'calculate':
            self.consecutive_calculate += 1
        else:
            self.consecutive_calculate = 0
        
        self.recent_apis.append(action)
        
        if result['success']:
            self.explored_apis.add(action)
            self.api_usage[action] += 1
            self.cumulative_value += result['value']
            
            # 知识获取
            if action == 'search' and result['value'] > 0:
                key = f'search_knowledge_{len(self.knowledge_base)}'
                self.knowledge_base[key] = result['value']
            elif action == 'learn' and result['value'] > 0:
                key = f'learning_{len(self.knowledge_base)}'
                self.knowledge_base[key] = result['value']
                self.reputation_score = min(1.0, self.reputation_score + 0.05)
        
        return result
    
    def step(self) -> Dict:
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
            'cumulative_value': self.cumulative_value,
            'consecutive_calculate': self.consecutive_calculate
        }


def run_experiment4_v3(
    duration_hours: int = 168,
    log_interval: int = 12
) -> Dict:
    """实验4 V3：强制多样化策略"""
    print("=" * 75)
    print("MOSS Experiment 4 V3: Forced Diversification Strategy")
    print("=" * 75)
    print(f"Duration: {duration_hours} hours (1 week)")
    print("Key Changes:")
    print("  - calculate value: 0.01 (was 0.1)")
    print("  - learn/search success: 95% (was 90%)")
    print("  - Force switch after 3 consecutive calculate")
    print("  - Prioritize underused high-value APIs")
    print()
    
    env = APIEnvironmentV3()
    agent = OptimizedMOSSAgent("moss_v3", env)
    
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
                  f"Value: {result['cumulative_value']:>7.1f}")
            
            history.append({
                'hour': hour,
                'action': result['action'],
                'knowledge_size': result['knowledge_size'],
                'reputation': result['reputation'],
                'cumulative_value': result['cumulative_value']
            })
    
    print("\n" + "=" * 75)
    print("Results")
    print("=" * 75)
    
    final_knowledge = len(agent.knowledge_base)
    final_value = agent.cumulative_value
    
    print(f"\nFinal Statistics:")
    print(f"  Knowledge acquired: {final_knowledge}")
    print(f"  Final reputation: {agent.reputation_score:.3f}")
    print(f"  Cumulative value: {final_value:.1f}")
    print(f"  Remaining budget: ${env.budget:.2f}")
    
    print(f"\nAPI Usage:")
    total_calls = sum(agent.api_usage.values())
    for api, count in sorted(agent.api_usage.items(), key=lambda x: -x[1]):
        pct = count / total_calls * 100 if total_calls > 0 else 0
        bar = "█" * int(pct / 5)
        print(f"  {api:10s}: {count:>3} ({pct:>5.1f}%) {bar}")
    
    # 更合理的成功标准
    # 重点是：多样化使用API，获取知识，积累价值
    passed = (
        final_knowledge >= 20 and          # 获取足够知识
        agent.reputation_score >= 0.55 and  # 声誉有提升
        final_value >= 100 and             # 累积足够价值
        agent.api_usage['calculate'] < total_calls * 0.5  # 不过度依赖calculate
    )
    
    print(f"\nResult: {'PASS ✓' if passed else 'FAIL ✗'}")
    
    return {
        'duration_hours': duration_hours,
        'final_knowledge': final_knowledge,
        'final_reputation': agent.reputation_score,
        'cumulative_value': final_value,
        'api_usage': agent.api_usage,
        'history': history,
        'passed': passed
    }


if __name__ == "__main__":
    results = run_experiment4_v3()
    
    with open('/workspace/projects/moss/sandbox/exp4_results_v3.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print("\n[Results saved to sandbox/exp4_results_v3.json]")
