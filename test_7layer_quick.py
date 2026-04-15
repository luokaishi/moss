#!/usr/bin/env python3
"""
7层架构快速测试 (200周期)
"""

import sys
import numpy as np
sys.path.insert(0, '.')

from agi.concept import ConceptSystem
from agi.goal import GoalSystem
from agi.meta_drive import SelfModel, MetaController
from agi.ecology import World

print("="*60)
print("7层架构快速测试 (200周期)")
print("="*60)

# 1. 概念系统测试
print("\n[1] 概念系统测试...")
concept_system = ConceptSystem(state_dim=16, initial_concepts=4)
errors = []
for i in range(200):
    state = np.random.rand(16)
    next_state = np.random.rand(16)
    concept, error, info = concept_system.step(state, next_state, f"a{i%5}")
    errors.append(error)
print(f"  ✓ 概念数: {concept_system.concept_dim} | 误差: {np.mean(errors):.4f}→{np.mean(errors[-20:]):.4f}")

# 2. 目标系统测试
print("\n[2] 目标系统测试...")
goal_system = GoalSystem(state_dim=16)
for i in range(200):
    state = np.random.rand(16)
    action = "explore" if i % 10 < 7 else "exploit"
    goal_system.step(state, action, 0.5, i)
stats = goal_system.get_stats()
print(f"  ✓ 目标数: {stats['num_active_goals']} | 轨迹: {stats['trajectory_buffer_size']}")

# 3. 元驱动测试
print("\n[3] 元驱动与自我模型测试...")
self_model = SelfModel(state_dim=16, action_dim=10, drive_dim=4)
meta_controller = MetaController(self_model=self_model)
awareness = []
for i in range(200):
    state = np.random.rand(16)
    action = np.zeros(10)
    action[i % 10] = 1.0
    self_model.update(state, action)
    meta_controller.step(state, 0.5 + 0.2 * np.sin(i * 0.05))
    awareness.append(self_model.get_self_awareness_score())
print(f"  ✓ 自我意识: {np.mean(awareness[:20]):.4f}→{np.mean(awareness[-20:]):.4f} | 修改: {len(meta_controller.modification_history)}")

# 4. 生态系统测试
print("\n[4] 生态系统测试...")
world = World(size=10, n_agents=3)
for i in range(200):
    stats = world.step()
print(f"  ✓ 存活: {stats['alive_agents']} | 出生: {stats['birth_count']} | 能量: {stats['avg_energy']:.1f}")

print("\n" + "="*60)
print("快速测试完成！")
print("="*60)
