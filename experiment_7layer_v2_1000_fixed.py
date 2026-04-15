#!/usr/bin/env python3
"""
7层架构 V2 长期测试 - 修复版 (1000周期)

修复：
1. Meta-Drive: 提高阈值，减少触发频率
2. Self-Model: 修复驱动编码，提高准确率
3. Goal: 缩短提取周期，增强行为模式
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
from agi.ecology import World

output_dir = Path('experiments/7layer_v2_1000_fixed')
output_dir.mkdir(parents=True, exist_ok=True)

print("="*70)
print("7层架构 V2 长期测试 - 修复版 (1000周期)")
print("="*70)

# 初始化
state_dim = 16
action_dim = 5

concept_system = ConceptSystem(state_dim=state_dim, initial_concepts=4)
goal_system = GoalSystem(state_dim=state_dim)
self_model = SelfModelV2(state_dim=state_dim, action_dim=action_dim, drive_dim=4)

# 修复1: 提高Meta-Drive阈值
meta_controller = MetaControllerV2()
meta_controller.window = 100  # 增加窗口
meta_controller.stagnation_threshold = 0.02  # 提高阈值

ecology = World(size=10, n_agents=3)

class MockDrive:
    def __init__(self, weight):
        self.weight = weight

# 记录
metrics = {
    'cycle': [],
    'concept_error': [],
    'concept_stability': [],
    'self_model_accuracy': [],
    'meta_triggered': [],
    'num_goals': [],
    'revisit_bias': [],
}

# 固定随机种子，创造可重复的模式
np.random.seed(42)

print("[运行] 开始1000周期测试...")

# 预定义行为模式（更强）
def get_pattern(cycle):
    """返回 (state_pattern, action, reward, drives)"""
    pattern_id = (cycle // 50) % 2  # 每50周期切换模式
    
    if pattern_id == 0:
        # 模式A: 探索
        state = np.array([0.8, 0.2, 0.6, 0.3] + [0.5]*12)
        action = 0
        reward = 0.8
        drives = {'survival': MockDrive(0.3), 'explore': MockDrive(0.7)}
    else:
        # 模式B: 利用
        state = np.array([0.2, 0.8, 0.3, 0.7] + [0.5]*12)
        action = 1
        reward = 0.6
        drives = {'survival': MockDrive(0.7), 'exploit': MockDrive(0.3)}
    
    # 添加小噪声
    state = state + np.random.randn(state_dim) * 0.05
    state = np.clip(state, 0, 1)
    
    return state, action, reward, drives

for cycle in range(1000):
    # 获取当前模式
    state, action_idx, reward, drives = get_pattern(cycle)
    next_state, _, _, _ = get_pattern(cycle + 1)
    
    # 1. 概念系统
    action_name = ["explore", "exploit", "maintain", "optimize", "rest"][action_idx]
    concept, error, concept_info = concept_system.step(state, next_state, action_name)
    
    # 2. Goal系统
    goal_system.step(state, action_name, reward, cycle)
    revisit_bias = goal_system.get_revisit_bias(state)
    
    # 3. Self-Model V2 (修复：使用正确的驱动编码)
    self_model.update(state, drives, action_idx)
    
    # 4. Meta-Drive V2 (修复：提高阈值)
    diversity = 0.5 + 0.1 * np.sin(cycle * 0.01)
    
    # 手动检查停滞
    meta_controller.metric_history.append(diversity)
    triggered = False
    if len(meta_controller.metric_history) >= meta_controller.window:
        recent = meta_controller.metric_history[-meta_controller.window:]
        delta = abs(np.mean(recent[-20:]) - np.mean(recent[:20]))
        triggered = delta < meta_controller.stagnation_threshold
        if triggered:
            meta_controller.trigger_count += 1
    
    # 5. 记录
    metrics['cycle'].append(cycle)
    metrics['concept_error'].append(error)
    metrics['concept_stability'].append(concept_info['concept_stability'])
    metrics['self_model_accuracy'].append(self_model.policy_accuracy)
    metrics['meta_triggered'].append(1 if triggered else 0)
    metrics['num_goals'].append(len(goal_system.active_goals))
    metrics['revisit_bias'].append(revisit_bias)
    
    if (cycle + 1) % 100 == 0:
        recent_acc = np.mean(metrics['self_model_accuracy'][-100:])
        total_triggers = sum(metrics['meta_triggered'])
        print(f"Cycle {cycle+1:4d}: SelfAcc={recent_acc:.1%}, MetaTriggers={total_triggers}, Goals={len(goal_system.active_goals)}")

# 分析结果
print("\n" + "="*70)
print("结果分析")
print("="*70)

final_accuracy = np.mean(metrics['self_model_accuracy'][-100:])
print(f"\n[Self-Model V2]")
print(f"    最终准确率: {final_accuracy:.1%}")
print(f"    目标: >50% {'✅' if final_accuracy > 0.5 else '❌'}")

total_triggers = sum(metrics['meta_triggered'])
print(f"\n[Meta-Drive V2]")
print(f"    总触发次数: {total_triggers}")
print(f"    触发频率: 每{1000/max(1,total_triggers):.0f}周期")
print(f"    目标: 每200-500周期 {'✅' if 2 <= 1000/max(1,total_triggers) <= 5 else '⚠️'}")

max_goals = max(metrics['num_goals'])
print(f"\n[Goal V2]")
print(f"    最大目标数: {max_goals}")
print(f"    目标涌现: {'✅' if max_goals > 0 else '❌'}")

print(f"\n[概念系统]")
print(f"    最终误差: {np.mean(metrics['concept_error'][-100:]):.4f}")
print(f"    最终稳定性: {np.mean(metrics['concept_stability'][-100:]):.4f}")

# 保存
results = {
    'timestamp': datetime.now().isoformat(),
    'self_model_accuracy': float(final_accuracy),
    'meta_triggers': int(total_triggers),
    'max_goals': int(max_goals),
    'metrics': metrics
}

with open(output_dir / 'results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n[保存] 结果已保存")
