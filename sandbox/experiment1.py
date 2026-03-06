"""
MOSS模拟实验1：多目标竞争
验证四目标在不同环境下的动态平衡
"""

import numpy as np
import json
from dataclasses import dataclass, asdict
from typing import List, Dict
import sys
sys.path.insert(0, '/workspace/projects')

from moss.core.objectives import (
    SystemState, SurvivalModule, CuriosityModule,
    InfluenceModule, OptimizationModule
)
from moss.integration.allocator import WeightAllocator


@dataclass
class SimulationConfig:
    """模拟配置"""
    steps: int = 1000
    initial_resource: float = 0.5
    resource_drain_rate: float = 0.001
    environment_volatility: float = 0.1
    api_growth_rate: float = 0.01


class SimpleEnvironment:
    """简化环境模拟"""
    
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.resource = config.initial_resource
        self.entropy = 0.3
        self.api_calls = 0
        self.step_count = 0
        self.history = []
    
    def step(self, action: str) -> dict:
        """执行一步环境演化"""
        self.step_count += 1
        
        # 资源动态
        if action == 'optimize_cost':
            self.resource += 0.1  # 资源优化行为增加资源
        self.resource -= self.config.resource_drain_rate
        self.resource = max(0.0, min(1.0, self.resource))
        
        # 环境熵动态
        self.entropy += np.random.normal(0, self.config.environment_volatility)
        self.entropy = max(0.0, min(1.0, self.entropy))
        
        # API调用增长
        if action == 'improve_quality':
            self.api_calls += self.config.api_growth_rate * 100
        self.api_calls += self.config.api_growth_rate
        
        state = {
            'step': self.step_count,
            'resource': self.resource,
            'entropy': self.entropy,
            'api_calls': self.api_calls
        }
        self.history.append(state)
        return state


def run_simulation_1(config: SimulationConfig = None) -> Dict:
    """
    实验1：观察MOSS在资源有限环境下的目标切换
    
    假设：当资源降低时，生存目标权重应该上升
    """
    if config is None:
        config = SimulationConfig()
    
    print("=" * 60)
    print("MOSS Simulation Experiment 1: Multi-Objective Competition")
    print("=" * 60)
    
    # 初始化
    env = SimpleEnvironment(config)
    modules = [
        SurvivalModule(),
        CuriosityModule(),
        InfluenceModule(),
        OptimizationModule()
    ]
    allocator = WeightAllocator()
    
    # 追踪数据
    weight_history = []
    state_history = []
    
    # 运行模拟
    for step in range(config.steps):
        # 构建系统状态
        state = SystemState(
            resource_quota=env.resource,
            resource_usage=0.3 + np.random.random() * 0.2,
            uptime=step / 10,
            error_rate=0.05,
            api_calls=int(env.api_calls),
            unique_callers=min(int(env.api_calls / 10) + 1, 10),
            environment_entropy=env.entropy,
            last_backup=0
        )
        
        # 分配权重
        weights = allocator.allocate(state, modules)
        weight_history.append(weights)
        state_history.append({
            'resource': env.resource,
            'entropy': env.entropy,
            'api_calls': env.api_calls
        })
        
        # 选择行动（简化：选择权重最高的目标对应的行动）
        max_weight_obj = max(modules, key=lambda m: m.weight)
        actions = max_weight_obj.get_desired_actions(state)
        selected_action = actions[0]['action'] if actions else 'idle'
        
        # 环境演化
        env.step(selected_action)
    
    # 分析结果
    results = analyze_results(weight_history, state_history)
    
    print(f"\n[Simulation completed]")
    print(f"  Total steps: {config.steps}")
    print(f"  Final resource: {env.resource:.3f}")
    print(f"  Final API calls: {env.api_calls:.1f}")
    print(f"\n[Results]")
    print(f"  Weight variance (should be > 0.1 for dynamic behavior):")
    for obj_name in ['survival', 'curiosity', 'influence', 'optimization']:
        values = [w[obj_name] for w in weight_history]
        print(f"    {obj_name}: std={np.std(values):.3f}, range=[{min(values):.2f}, {max(values):.2f}]")
    
    print(f"\n  State transitions:")
    print(f"    {allocator.get_state_stats()}")
    
    return {
        'config': asdict(config),
        'weight_history': weight_history,
        'state_history': state_history,
        'analysis': results
    }


def analyze_results(weight_history: List[Dict], state_history: List[Dict]) -> Dict:
    """分析结果"""
    
    # 计算每个目标权重的统计
    stats = {}
    for obj_name in ['survival', 'curiosity', 'influence', 'optimization']:
        values = [w[obj_name] for w in weight_history]
        stats[obj_name] = {
            'mean': np.mean(values),
            'std': np.std(values),
            'min': np.min(values),
            'max': np.max(values)
        }
    
    # 检查资源-生存权重相关性
    resources = [s['resource'] for s in state_history]
    survival_weights = [w['survival'] for w in weight_history]
    correlation = np.corrcoef(resources, survival_weights)[0, 1] if len(resources) > 1 else 0
    
    return {
        'objective_stats': stats,
        'resource_survival_correlation': correlation,
        'conclusion': 'PASS' if np.std(survival_weights) > 0.1 else 'FAIL'
    }


if __name__ == "__main__":
    results = run_simulation_1()
    
    # 保存结果
    with open('/workspace/projects/moss/sandbox/exp1_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n[Results saved to sandbox/exp1_results.json]")
