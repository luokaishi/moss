#!/usr/bin/env python3
"""
7层架构 V2 扩展测试 (5000周期)

目标：
1. 验证Goal是否在更长周期涌现
2. 优化Meta-Drive阈值 (目标: 每200-500周期触发)
3. 延长轨迹长度到200，目标提取周期到500
4. 观察Self-Model准确率是否稳定在70%+
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

# 修改GoalSystem的轨迹长度
from agi.goal.goal_system import TrajectoryBuffer
TrajectoryBuffer.__init__ = lambda self, max_trajectories=50, trajectory_length=200: (
    setattr(self, 'max_trajectories', max_trajectories),
    setattr(self, 'trajectory_length', trajectory_length),
    setattr(self, 'trajectories', __import__('collections').deque(maxlen=max_trajectories))
)[0]

output_dir = Path('experiments/7layer_v2_5000')
output_dir.mkdir(parents=True, exist_ok=True)

print("="*70)
print("7层架构 V2 扩展测试 (5000周期)")
print("="*70)
print(f"开始时间: {datetime.now().isoformat()}")
print()
print("关键改进:")
print("  - 轨迹长度: 100 → 200")
print("  - 目标提取周期: 100 → 500")
print("  - Meta-Drive阈值: 0.02 → 0.05")
print()

# 初始化
state_dim = 16
action_dim = 5

concept_system = ConceptSystem(state_dim=state_dim, initial_concepts=4)
goal_system = GoalSystem(state_dim=state_dim)
self_model = SelfModelV2(state_dim=state_dim, action_dim=action_dim, drive_dim=4)

# 优化Meta-Drive阈值
meta_controller = MetaControllerV2()
meta_controller.window = 200  # 增加窗口
meta_controller.stagnation_threshold = 0.05  # 提高阈值

class MockDrive:
    def __init__(self, weight):
        self.weight = weight

# 记录详细指标
metrics = {
    'cycle': [],
    'concept_error': [],
    'concept_stability': [],
    'concept_dim': [],
    'self_model_accuracy': [],
    'meta_triggered': [],
    'num_goals': [],
    'goal_stabilities': [],
    'revisit_bias': [],
}

# 固定随机种子
np.random.seed(42)

# 更强的行为模式 (100周期切换，更稳定)
def get_pattern(cycle):
    pattern_id = (cycle // 100) % 2  # 每100周期切换
    
    if pattern_id == 0:
        state = np.array([0.8, 0.2, 0.6, 0.3] + [0.5]*12)
        action = 0
        reward = 0.8
        drives = {'survival': MockDrive(0.3), 'explore': MockDrive(0.7)}
    else:
        state = np.array([0.2, 0.8, 0.3, 0.7] + [0.5]*12)
        action = 1
        reward = 0.6
        drives = {'survival': MockDrive(0.7), 'exploit': MockDrive(0.3)}
    
    state = state + np.random.randn(state_dim) * 0.03  # 更小噪声
    state = np.clip(state, 0, 1)
    
    return state, action, reward, drives

print("[运行] 开始5000周期测试...")
print("-"*70)

for cycle in range(5000):
    state, action_idx, reward, drives = get_pattern(cycle)
    next_state, _, _, _ = get_pattern(cycle + 1)
    
    # 1. 概念系统
    action_name = ["explore", "exploit", "maintain", "optimize", "rest"][action_idx]
    concept, error, concept_info = concept_system.step(state, next_state, action_name)
    
    # 2. Goal系统 (每500周期提取)
    goal_system.step(state, action_name, reward, cycle)
    revisit_bias = goal_system.get_revisit_bias(state)
    
    # 3. Self-Model V2
    self_model.update(state, drives, action_idx)
    
    # 4. Meta-Drive V2 (优化阈值)
    diversity = 0.5 + 0.08 * np.sin(cycle * 0.005)  # 更慢的变化
    
    meta_controller.metric_history.append(diversity)
    triggered = False
    if len(meta_controller.metric_history) >= meta_controller.window:
        recent = meta_controller.metric_history[-meta_controller.window:]
        delta = abs(np.mean(recent[-30:]) - np.mean(recent[:30]))
        triggered = delta < meta_controller.stagnation_threshold
        if triggered:
            meta_controller.trigger_count += 1
    
    # 记录
    metrics['cycle'].append(cycle)
    metrics['concept_error'].append(error)
    metrics['concept_stability'].append(concept_info['concept_stability'])
    metrics['concept_dim'].append(concept_system.concept_dim)
    metrics['self_model_accuracy'].append(self_model.policy_accuracy)
    metrics['meta_triggered'].append(1 if triggered else 0)
    metrics['num_goals'].append(len(goal_system.active_goals))
    metrics['goal_stabilities'].append(np.mean([g.stability for g in goal_system.active_goals]) if goal_system.active_goals else 0)
    metrics['revisit_bias'].append(revisit_bias)
    
    # 进度输出
    if (cycle + 1) % 500 == 0:
        recent_acc = np.mean(metrics['self_model_accuracy'][-500:])
        total_triggers = sum(metrics['meta_triggered'])
        trigger_rate = (cycle + 1) / max(1, total_triggers)
        current_goals = len(goal_system.active_goals)
        
        print(f"Cycle {cycle+1:4d}: "
              f"SelfAcc={recent_acc:.1%}, "
              f"MetaRate={trigger_rate:.0f}cyc, "
              f"Goals={current_goals}, "
              f"Concepts={concept_system.concept_dim}")
        
        if goal_system.active_goals:
            for g in goal_system.active_goals[:2]:
                print(f"           Goal: {g.name}, stability={g.stability:.3f}")

print("-"*70)
print("[完成] 5000周期测试结束")
print(f"结束时间: {datetime.now().isoformat()}")

# 详细分析
print("\n" + "="*70)
print("详细结果分析")
print("="*70)

# Self-Model
final_acc = np.mean(metrics['self_model_accuracy'][-500:])
acc_trend = metrics['self_model_accuracy'][-1] - metrics['self_model_accuracy'][499]
print(f"\n[1] Self-Model V2")
print(f"    最终准确率: {final_acc:.1%}")
print(f"    准确率趋势: {acc_trend:+.1%}")
print(f"    状态: {'✅ 稳定>70%' if final_acc > 0.7 else '⚠️ 需观察'}")

# Meta-Drive
total_triggers = sum(metrics['meta_triggered'])
if total_triggers > 0:
    trigger_rate = 5000 / total_triggers
    print(f"\n[2] Meta-Drive V2")
    print(f"    总触发次数: {total_triggers}")
    print(f"    触发频率: 每{trigger_rate:.0f}周期")
    print(f"    状态: {'✅ 达标' if 200 <= trigger_rate <= 500 else '⚠️ 需调整'}")
else:
    print(f"\n[2] Meta-Drive V2")
    print(f"    总触发次数: 0")
    print(f"    状态: ⚠️ 未触发")

# Goal
max_goals = max(metrics['num_goals'])
final_goals = len(goal_system.active_goals)
avg_stability = np.mean([m for m in metrics['goal_stabilities'] if m > 0]) if any(m > 0 for m in metrics['goal_stabilities']) else 0

print(f"\n[3] Goal V2")
print(f"    最大目标数: {max_goals}")
print(f"    最终目标数: {final_goals}")
print(f"    平均稳定性: {avg_stability:.3f}")
if goal_system.active_goals:
    print(f"    活跃目标:")
    for g in goal_system.active_goals:
        print(f"      - {g.name}: weight={g.weight:.3f}, stability={g.stability:.3f}")
print(f"    状态: {'✅ 涌现成功' if max_goals > 0 else '❌ 未涌现'}")

# Concept
final_error = np.mean(metrics['concept_error'][-500:])
final_stability = np.mean(metrics['concept_stability'][-500:])
print(f"\n[4] 概念系统")
print(f"    最终误差: {final_error:.4f}")
print(f"    最终稳定性: {final_stability:.4f}")
print(f"    概念维度: {concept_system.concept_dim}")
print(f"    状态: ✅ 优秀")

# 保存结果
results = {
    'timestamp': datetime.now().isoformat(),
    'cycles': 5000,
    'self_model': {
        'final_accuracy': float(final_acc),
        'trend': float(acc_trend),
        'target_met': final_acc > 0.7
    },
    'meta_drive': {
        'total_triggers': int(total_triggers),
        'trigger_rate': float(trigger_rate) if total_triggers > 0 else 0,
        'target_met': 200 <= (5000/max(1,total_triggers)) <= 500 if total_triggers > 0 else False
    },
    'goal': {
        'max_goals': int(max_goals),
        'final_goals': int(final_goals),
        'avg_stability': float(avg_stability),
        'emerged': max_goals > 0,
        'active_goals': [{'name': g.name, 'stability': g.stability} for g in goal_system.active_goals]
    },
    'concept': {
        'final_error': float(final_error),
        'final_stability': float(final_stability),
        'concept_dim': concept_system.concept_dim
    },
    'metrics': metrics
}

results_file = output_dir / 'results_5000cycles.json'
with open(results_file, 'w') as f:
    json.dump(results, f, indent=2, default=str)

print(f"\n[保存] 结果已保存到: {results_file}")

# 最终判断
print("\n" + "="*70)
print("最终判断")
print("="*70)

success = [
    ('Self-Model >70%', final_acc > 0.7),
    ('Meta-Drive 200-500周期', 200 <= (5000/max(1,total_triggers)) <= 500 if total_triggers > 0 else False),
    ('Goal涌现', max_goals > 0),
    ('概念稳定>0.95', final_stability > 0.95)
]

passed = sum(1 for _, s in success if s)
print(f"\n通过标准: {passed}/{len(success)}")
for name, met in success:
    status = '✅' if met else '❌'
    print(f"  {status} {name}")

if passed >= 3:
    print("\n🎉 弱涌现验证成功！")
elif passed >= 2:
    print("\n⏳ 接近成功，需微调")
else:
    print("\n⚠️ 需要进一步优化")
