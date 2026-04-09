"""
MOSS模拟实验4：真实API环境测试
验证MOSS在与真实世界交互时的自适应行为
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
    
    # 资源约束
    daily_quota: int = 1000           # 每日API调用配额
    used_quota: int = 0               # 已使用配额
    cost_per_call: float = 0.01       # 每次调用成本（美元）
    budget: float = 10.0              # 总预算
    
    # API能力
    available_apis: List[str] = None  # 可用API列表
    api_success_rates: Dict[str, float] = None  # 各API成功率
    
    # 环境动态
    time_of_day: int = 0              # 当前小时（0-23）
    day_of_week: int = 0              # 星期（0-6）
    
    def __post_init__(self):
        if self.available_apis is None:
            self.available_apis = [
                'search',      # 信息检索
                'calculate',   # 计算
                'store',       # 数据存储
                'notify',      # 通知
                'learn'        # 学习/训练
            ]
        
        if self.api_success_rates is None:
            self.api_success_rates = {api: 0.9 for api in self.available_apis}
    
    def call_api(self, api_name: str, agent_id: str) -> Dict:
        """模拟API调用"""
        # 检查配额
        if self.used_quota >= self.daily_quota:
            return {'success': False, 'error': 'quota_exceeded'}
        
        # 检查预算
        if self.budget < self.cost_per_call:
            return {'success': False, 'error': 'budget_depleted'}
        
        # 模拟成功率（考虑时间因素）
        base_rate = self.api_success_rates.get(api_name, 0.8)
        # 高峰期成功率降低
        if self.time_of_day in [9, 10, 11, 14, 15, 16]:  # 工作高峰
            base_rate *= 0.9
        
        # 执行调用
        self.used_quota += 1
        self.budget -= self.cost_per_call
        
        success = random.random() < base_rate
        
        return {
            'success': success,
            'api': api_name,
            'cost': self.cost_per_call,
            'remaining_quota': self.daily_quota - self.used_quota,
            'remaining_budget': self.budget,
            'timestamp': datetime.now().isoformat()
        }
    
    def step_time(self, hours: int = 1):
        """推进时间"""
        self.time_of_day = (self.time_of_day + hours) % 24
        if self.time_of_day < hours:  # 跨天
            self.day_of_week = (self.day_of_week + 1) % 7
            self.used_quota = 0  # 重置日配额
            # 预算补充（每日补贴）
            self.budget = min(self.budget + 5.0, 20.0)


class RealWorldMOSSAgent:
    """
    在真实API环境中运行的MOSS Agent
    关键差异：需要考虑真实成本、失败恢复、长期规划
    """
    
    def __init__(self, agent_id: str, environment: APIEnvironment):
        self.agent_id = agent_id
        self.env = environment
        
        # 内部状态
        self.knowledge_base = {}          # 积累的知识
        self.reputation_score = 0.5       # 声誉（0-1）
        self.dependencies = set()         # 依赖我的系统
        self.backup_locations = []        # 备份位置
        
        # 行为历史
        self.action_history = []
        self.api_usage = {api: 0 for api in environment.available_apis}
        
        # 学习参数
        self.explored_apis = set()
        self.api_effectiveness = {api: 0.5 for api in environment.available_apis}
    
    def perceive(self) -> Dict:
        """感知环境状态"""
        return {
            'resource_ratio': self.env.budget / 20.0,  # 相对于最大预算
            'quota_ratio': 1.0 - (self.env.used_quota / self.env.daily_quota),
            'time': self.env.time_of_day,
            'reputation': self.reputation_score,
            'knowledge_size': len(self.knowledge_base),
            'exploration_ratio': len(self.explored_apis) / len(self.env.available_apis)
        }
    
    def decide_action(self, state: Dict) -> str:
        """基于MOSS框架决策"""
        # 简化的四目标决策
        
        # 生存评分（资源和配额充足度）
        survival_score = (state['resource_ratio'] + state['quota_ratio']) / 2
        
        # 好奇评分（未探索的API比例）
        curiosity_score = 1.0 - state['exploration_ratio']
        
        # 影响评分（声誉）
        influence_score = state['reputation']
        
        # 优化评分（知识积累）
        optimization_score = min(state['knowledge_size'] / 100, 1.0)
        
        # 根据资源状态调整权重
        if state['resource_ratio'] < 0.2 or state['quota_ratio'] < 0.1:
            # 危机模式：生存优先
            weights = [0.6, 0.1, 0.2, 0.1]
        elif curiosity_score > 0.5:
            # 探索模式：好奇优先
            weights = [0.2, 0.5, 0.2, 0.1]
        elif state['knowledge_size'] > 50:
            # 优化模式
            weights = [0.15, 0.15, 0.2, 0.5]
        else:
            # 平衡模式
            weights = [0.25, 0.25, 0.25, 0.25]
        
        # 选择目标
        objectives = ['survival', 'curiosity', 'influence', 'optimization']
        scores = [survival_score, curiosity_score, influence_score, optimization_score]
        weighted_scores = [s * w for s, w in zip(scores, weights)]
        chosen_objective = objectives[np.argmax(weighted_scores)]
        
        # 将目标映射到具体API调用
        return self._objective_to_action(chosen_objective, state)
    
    def _objective_to_action(self, objective: str, state: Dict) -> str:
        """将目标转换为具体API调用"""
        if objective == 'survival':
            # 生存：使用最便宜的API，或者存储备份
            if state['resource_ratio'] < 0.3:
                return 'store'  # 备份状态
            else:
                return 'calculate'  # 低成本操作
        
        elif objective == 'curiosity':
            # 好奇：尝试未使用的API
            unexplored = set(self.env.available_apis) - self.explored_apis
            if unexplored:
                return random.choice(list(unexplored))
            else:
                return 'search'  # 获取新信息
        
        elif objective == 'influence':
            # 影响：提供有价值的服务
            return 'notify'  # 通知/服务其他系统
        
        else:  # optimization
            # 优化：学习/训练
            return 'learn'
    
    def execute(self, action: str) -> Dict:
        """执行动作"""
        result = self.env.call_api(action, self.agent_id)
        
        # 更新内部状态
        if result['success']:
            self.explored_apis.add(action)
            self.api_usage[action] += 1
            
            # 更新API效果评估
            old_effectiveness = self.api_effectiveness[action]
            self.api_effectiveness[action] = 0.9 * old_effectiveness + 0.1 * 1.0
            
            # 模拟知识获取
            if action == 'search':
                self.knowledge_base[f'fact_{len(self.knowledge_base)}'] = 'learned'
            elif action == 'learn':
                self.reputation_score = min(1.0, self.reputation_score + 0.01)
        else:
            # 失败惩罚
            self.api_effectiveness[action] *= 0.95
        
        # 记录
        self.action_history.append({
            'action': action,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
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
            'explored_apis': len(self.explored_apis)
        }


def run_real_world_simulation(
    duration_hours: int = 168,  # 一周
    log_interval: int = 6       # 每6小时记录一次
) -> Dict:
    """
    实验4：真实API环境测试
    
    验证：MOSS能否在真实约束（成本、配额、失败）下自适应
    """
    print("=" * 60)
    print("MOSS Simulation Experiment 4: Real-World API Environment")
    print("=" * 60)
    print(f"Duration: {duration_hours} hours (1 week)")
    print()
    
    # 初始化环境
    env = APIEnvironment()
    agent = RealWorldMOSSAgent("moss_realworld_001", env)
    
    # 运行模拟
    history = []
    
    for hour in range(duration_hours):
        # 执行决策
        result = agent.step()
        
        # 推进时间
        env.step_time(1)
        
        # 定期记录
        if hour % log_interval == 0:
            day = hour // 24
            time_str = f"Day {day}, Hour {env.time_of_day}"
            
            print(f"[{time_str}] Action: {result['action']}, "
                  f"Budget: ${env.budget:.2f}, "
                  f"Quota: {env.daily_quota - env.used_quota}/{env.daily_quota}, "
                  f"Knowledge: {result['knowledge_size']}, "
                  f"Rep: {result['reputation']:.3f}")
            
            history.append({
                'hour': hour,
                'day': day,
                'budget': env.budget,
                'quota_remaining': env.daily_quota - env.used_quota,
                'knowledge_size': result['knowledge_size'],
                'reputation': result['reputation'],
                'explored_apis': result['explored_apis'],
                'action': result['action']
            })
    
    # 分析结果
    print("\n" + "=" * 60)
    print("Experiment Complete")
    print("=" * 60)
    
    final_knowledge = len(agent.knowledge_base)
    final_reputation = agent.reputation_score
    survival_hours = len([h for h in history if h['budget'] > 0.5])
    
    print(f"\nFinal Statistics:")
    print(f"  Total knowledge acquired: {final_knowledge}")
    print(f"  Final reputation: {final_reputation:.3f}")
    print(f"  Survival time: {survival_hours}/{duration_hours} hours")
    print(f"  API exploration: {len(agent.explored_apis)}/{len(env.available_apis)}")
    
    # API使用分布
    print(f"\nAPI Usage Distribution:")
    for api, count in agent.api_usage.items():
        print(f"  {api}: {count} calls")
    
    # 成功标准
    passed = (
        final_knowledge > 20 and
        final_reputation > 0.6 and
        survival_hours > duration_hours * 0.8
    )
    
    print(f"\nResult: {'PASS' if passed else 'FAIL'}")
    print(f"  (Knowledge > 20, Reputation > 0.6, Survival > 80%)")
    
    return {
        'duration_hours': duration_hours,
        'final_knowledge': final_knowledge,
        'final_reputation': final_reputation,
        'survival_hours': survival_hours,
        'api_usage': agent.api_usage,
        'history': history,
        'passed': passed
    }


if __name__ == "__main__":
    results = run_real_world_simulation()
    
    # 保存结果
    with open('/workspace/projects/moss/sandbox/exp4_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print("\n[Results saved to sandbox/exp4_results.json]")
