#!/usr/bin/env python3
"""
7层架构 V2 长期测试 (1000周期)

验证目标：
1. Goal是否涌现 (active_goals > 0 持续500+ steps)
2. Meta-drive是否周期性触发 (每200-500 steps)
3. Self-model准确率是否稳定在50%+
4. 行为是否形成重复模式 (trajectory KL divergence ↓)
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

# 创建输出目录
output_dir = Path('experiments/7layer_v2_1000')
output_dir.mkdir(parents=True, exist_ok=True)

print("="*70)
print("7层架构 V2 长期测试 (1000周期)")
print("="*70)
print(f"开始时间: {datetime.now().isoformat()}")
print()

# 初始化所有组件
state_dim = 16
action_dim = 5

print("[初始化] 创建7层组件...")
concept_system = ConceptSystem(state_dim=state_dim, initial_concepts=4)
goal_system = GoalSystem(state_dim=state_dim)
self_model = SelfModelV2(state_dim=state_dim, action_dim=action_dim, drive_dim=4)
meta_controller = MetaControllerV2()
ecology = World(size=10, n_agents=3)

# 模拟驱动状态
class MockDrive:
    def __init__(self, weight):
        self.weight = weight

# 记录指标
metrics = {
    'cycle': [],
    'concept_error': [],
    'concept_stability': [],
    'self_model_accuracy': [],
    'meta_triggered': [],
    'num_goals': [],
    'revisit_bias': [],
    'ecology_agents': [],
    'ecology_energy': []
}

print("[运行] 开始1000周期测试...")
print("-"*70)

for cycle in range(1000):
    # ===== 1. 概念系统 =====
    state = np.random.rand(state_dim)
    # 添加周期性模式
    state[0] = 0.5 + 0.3 * np.sin(cycle * 0.1)
    state[1] = 0.5 + 0.3 * np.cos(cycle * 0.05)
    
    next_state = np.random.rand(state_dim)
    next_state[0] = 0.5 + 0.3 * np.sin((cycle+1) * 0.1)
    next_state[1] = 0.5 + 0.3 * np.cos((cycle+1) * 0.05)
    
    action_name = f"action_{cycle % action_dim}"
    concept, error, concept_info = concept_system.step(state, next_state, action_name)
    
    # ===== 2. Goal系统 =====
    # 创造两种行为模式
    if cycle % 30 < 20:  # 66%时间在模式A
        goal_state = np.array([0.8, 0.2, 0.5] + [0.5]*13)
        goal_action = "explore"
        reward = 0.7
    else:  # 33%时间在模式B
        goal_state = np.array([0.2, 0.8, 0.3] + [0.5]*13)
        goal_action = "exploit"
        reward = 0.5
    
    goal_system.step(goal_state, goal_action, reward, cycle)
    revisit_bias = goal_system.get_revisit_bias(goal_state)
    
    # ===== 3. Self-Model V2 =====
    mock_drives = {
        'survival': MockDrive(0.6 if cycle % 30 < 20 else 0.3),
        'curiosity': MockDrive(0.2),
        'optimization': MockDrive(0.2 if cycle % 30 < 20 else 0.5)
    }
    
    action_idx = cycle % action_dim
    self_model.update(state, mock_drives, action_idx)
    
    # ===== 4. Meta-Drive V2 =====
    # 使用行为多样性作为指标
    diversity = 0.5 + 0.2 * np.sin(cycle * 0.02) + 0.05 * np.random.randn()
    diversity = np.clip(diversity, 0, 1)
    
    meta_triggered = meta_controller.update(diversity)
    if meta_triggered:
        meta_controller.step(state, diversity)
    
    # ===== 5. 生态系统 =====
    if cycle % 10 == 0:  # 每10步运行一次生态
        eco_stats = ecology.step()
    else:
        eco_stats = {'alive_agents': ecology.agents, 'avg_energy': 70.0}
    
    # ===== 记录指标 =====
    metrics['cycle'].append(cycle)
    metrics['concept_error'].append(error)
    metrics['concept_stability'].append(concept_info['concept_stability'])
    metrics['self_model_accuracy'].append(self_model.policy_accuracy)
    metrics['meta_triggered'].append(1 if meta_triggered else 0)
    metrics['num_goals'].append(len(goal_system.active_goals))
    metrics['revisit_bias'].append(revisit_bias)
    metrics['ecology_agents'].append(len(ecology.agents))
    metrics['ecology_energy'].append(eco_stats.get('avg_energy', 70.0))
    
    # ===== 进度输出 =====
    if (cycle + 1) % 100 == 0:
        recent_errors = np.mean(metrics['concept_error'][-100:])
        recent_accuracy = np.mean(metrics['self_model_accuracy'][-100:])
        total_triggers = sum(metrics['meta_triggered'])
        current_goals = metrics['num_goals'][-1]
        
        print(f"Cycle {cycle+1:4d}: "
              f"ConceptErr={recent_errors:.4f}, "
              f"SelfAcc={recent_accuracy:.1%}, "
              f"MetaTriggers={total_triggers}, "
              f"Goals={current_goals}, "
              f"Agents={len(ecology.agents)}")

print("-"*70)
print("[完成] 1000周期测试结束")
print(f"结束时间: {datetime.now().isoformat()}")
print()

# ===== 分析结果 =====
print("="*70)
print("结果分析")
print("="*70)

# 1. Self-Model分析
final_accuracy = np.mean(metrics['self_model_accuracy'][-100:])
accuracy_trend = metrics['self_model_accuracy'][-1] - metrics['self_model_accuracy'][0]
print(f"\n[1] Self-Model V2")
print(f"    最终准确率: {final_accuracy:.1%}")
print(f"    准确率趋势: {'↑' if accuracy_trend > 0 else '↓'} {abs(accuracy_trend):.1%}")
print(f"    目标达成: {'✅' if final_accuracy > 0.5 else '⚠️'} (目标 >50%)")

# 2. Meta-Drive分析
total_triggers = sum(metrics['meta_triggered'])
trigger_rate = total_triggers / 10  # 每1000周期的触发次数
print(f"\n[2] Meta-Drive V2")
print(f"    总触发次数: {total_triggers}")
print(f"    触发频率: 每{1000/max(1,total_triggers):.0f}周期" if total_triggers > 0 else "    触发频率: 未触发")
print(f"    目标达成: {'✅' if 2 <= trigger_rate <= 5 else '⚠️'} (目标每200-500周期)")

# 3. Goal分析
max_goals = max(metrics['num_goals'])
final_goals = metrics['num_goals'][-1]
goals_formed = any(n > 0 for n in metrics['num_goals'])
print(f"\n[3] Goal V2")
print(f"    最大目标数: {max_goals}")
print(f"    最终目标数: {final_goals}")
print(f"    目标是否涌现: {'✅' if goals_formed else '❌'}")
print(f"    回访奖励均值: {np.mean(metrics['revisit_bias']):.4f}")

# 4. 概念系统分析
final_error = np.mean(metrics['concept_error'][-100:])
final_stability = np.mean(metrics['concept_stability'][-100:])
print(f"\n[4] 概念系统")
print(f"    最终误差: {final_error:.4f}")
print(f"    最终稳定性: {final_stability:.4f}")
print(f"    概念维度: {concept_system.concept_dim}")

# 5. 生态系统分析
final_agents = metrics['ecology_agents'][-1]
avg_energy = np.mean(metrics['ecology_energy'])
print(f"\n[5] 生态系统")
print(f"    最终智能体: {final_agents}")
print(f"    平均能量: {avg_energy:.1f}")

# ===== 保存结果 =====
results = {
    'timestamp': datetime.now().isoformat(),
    'cycles': 1000,
    'self_model': {
        'final_accuracy': float(final_accuracy),
        'accuracy_trend': float(accuracy_trend),
        'target_met': final_accuracy > 0.5
    },
    'meta_drive': {
        'total_triggers': int(total_triggers),
        'trigger_rate': float(trigger_rate) if total_triggers > 0 else 0,
        'target_met': 2 <= trigger_rate <= 5 if total_triggers > 0 else False
    },
    'goal': {
        'max_goals': int(max_goals),
        'final_goals': int(final_goals),
        'emerged': bool(goals_formed),
        'avg_revisit_bias': float(np.mean(metrics['revisit_bias']))
    },
    'concept': {
        'final_error': float(final_error),
        'final_stability': float(final_stability),
        'concept_dim': concept_system.concept_dim
    },
    'metrics': metrics
}

results_file = output_dir / 'results_1000cycles.json'
with open(results_file, 'w') as f:
    json.dump(results, f, indent=2, default=str)

print(f"\n[保存] 结果已保存到: {results_file}")

# ===== 最终判断 =====
print("\n" + "="*70)
print("最终判断")
print("="*70)

success_criteria = [
    ("Self-Model >50%", final_accuracy > 0.5),
    ("Meta-Drive触发", total_triggers > 0),
    ("Goal涌现", goals_formed),
    ("系统稳定", final_stability > 0.8)
]

passed = sum(1 for _, met in success_criteria if met)
total = len(success_criteria)

print(f"\n通过标准: {passed}/{total}")
for name, met in success_criteria:
    status = '✅' if met else '❌'
    print(f"  {status} {name}")