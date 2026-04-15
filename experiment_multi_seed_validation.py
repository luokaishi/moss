#!/usr/bin/env python3
"""
多种子验证实验

验证关键发现是否跨随机种子稳定
"""

import sys
import json
import numpy as np
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '.')

from agi.concept import ConceptSystem
from agi.goal import GoalSystem
from agi.meta_drive.self_model_v2 import SelfModelV2
from agi.meta_drive.meta_controller_v2 import MetaControllerV2

print("="*70)
print("多种子验证实验")
print("="*70)

# 测试种子列表
seeds = [42, 43, 44, 45, 46, 47, 48, 49, 50, 51]
results_by_seed = {}

class MockDrive:
    def __init__(self, weight):
        self.weight = weight

def run_experiment(seed, cycles=2000):
    """运行单种子实验"""
    np.random.seed(seed)
    
    state_dim = 16
    action_dim = 5
    
    concept_system = ConceptSystem(state_dim=state_dim, initial_concepts=4)
    goal_system = GoalSystem(state_dim=state_dim)
    self_model = SelfModelV2(state_dim=state_dim, action_dim=action_dim, drive_dim=4)
    meta_controller = MetaControllerV2()
    meta_controller.window = 200
    meta_controller.stagnation_threshold = 0.05
    
    # 运行
    for cycle in range(cycles):
        # 行为模式
        pattern_id = (cycle // 100) % 2
        if pattern_id == 0:
            state = np.array([0.8, 0.2, 0.6, 0.3] + [0.5]*12)
            state = state + np.random.randn(state_dim) * 0.03
            state = np.clip(state, 0, 1)
            action = 0
            reward = 0.8
            drives = {'survival': MockDrive(0.3), 'explore': MockDrive(0.7)}
        else:
            state = np.array([0.2, 0.8, 0.3, 0.7] + [0.5]*12)
            state = state + np.random.randn(state_dim) * 0.03
            state = np.clip(state, 0, 1)
            action = 1
            reward = 0.6
            drives = {'survival': MockDrive(0.7), 'exploit': MockDrive(0.3)}
        
        next_state = state + np.random.randn(state_dim) * 0.02
        next_state = np.clip(next_state, 0, 1)
        
        # 更新系统
        concept_system.step(state, next_state, f"a{action}")
        goal_system.step(state, f"a{action}", reward, cycle)
        self_model.update(state, drives, action)
        
        diversity = 0.5 + 0.08 * np.sin(cycle * 0.005)
        meta_controller.metric_history.append(diversity)
    
    # 返回结果
    return {
        'self_model_accuracy': self_model.policy_accuracy,
        'concept_stability': concept_system.encoder.get_concept_stability(),
        'num_goals': len(goal_system.active_goals),
        'goal_stability': np.mean([g.stability for g in goal_system.active_goals]) if goal_system.active_goals else 0,
        'meta_triggers': meta_controller.trigger_count
    }

# 运行所有种子
print(f"运行 {len(seeds)} 个随机种子...")
print("-"*70)

for seed in seeds:
    print(f"Seed {seed}: ", end='', flush=True)
    result = run_experiment(seed)
    results_by_seed[seed] = result
    print(f"SelfAcc={result['self_model_accuracy']:.1%}, "
          f"Goals={result['num_goals']}, "
          f"Triggers={result['meta_triggers']}")

# 分析跨种子稳定性
print("\n" + "="*70)
print("跨种子稳定性分析")
print("="*70)

metrics = ['self_model_accuracy', 'concept_stability', 'num_goals', 'goal_stability']

for metric in metrics:
    values = [results_by_seed[s][metric] for s in seeds]
    mean = np.mean(values)
    std = np.std(values)
    cv = std / mean if mean > 0 else 0  # 变异系数
    
    print(f"\n{metric}:")
    print(f"  均值: {mean:.4f}")
    print(f"  标准差: {std:.4f}")
    print(f"  变异系数: {cv:.2%}")
    print(f"  范围: [{min(values):.4f}, {max(values):.4f}]")
    
    # 稳定性判断
    if cv < 0.1:
        stability = "高度稳定 ✅"
    elif cv < 0.2:
        stability = "中等稳定 ⚠️"
    else:
        stability = "不稳定 ❌"
    print(f"  稳定性: {stability}")

# 关键发现验证
print("\n" + "="*70)
print("关键发现验证")
print("="*70)

# Self-Model > 50%
accs = [results_by_seed[s]['self_model_accuracy'] for s in seeds]
pass_count = sum(1 for a in accs if a > 0.5)
print(f"\nSelf-Model > 50%: {pass_count}/{len(seeds)} 种子通过")

# Goal涌现
goals = [results_by_seed[s]['num_goals'] for s in seeds]
emerge_count = sum(1 for g in goals if g > 0)
print(f"Goal涌现: {emerge_count}/{len(seeds)} 种子出现")

# 概念稳定性 > 0.95
stabs = [results_by_seed[s]['concept_stability'] for s in seeds]
stable_count = sum(1 for s in stabs if s > 0.95)
print(f"概念稳定性 > 0.95: {stable_count}/{len(seeds)} 种子通过")

# 保存结果
output_dir = Path('experiments/multi_seed_validation')
output_dir.mkdir(parents=True, exist_ok=True)

results = {
    'timestamp': datetime.now().isoformat(),
    'seeds': seeds,
    'results_by_seed': results_by_seed,
    'summary': {
        'self_model_pass_rate': pass_count / len(seeds),
        'goal_emerge_rate': emerge_count / len(seeds),
        'concept_stable_rate': stable_count / len(seeds)
    }
}

with open(output_dir / 'results.json', 'w') as f:
    json.dump(results, f, indent=2, default=str)

print(f"\n[保存] 结果已保存到: {output_dir}/results.json")

print("\n" + "="*70)
print("多种子验证完成!")
print("="*70)
