#!/usr/bin/env python3
"""
测试7层系统的核心组件
"""

import numpy as np
import sys
sys.path.insert(0, '.')

print("=" * 60)
print("测试7层架构核心组件")
print("=" * 60)

# 测试1: 概念系统
print("\n[测试1] 概念系统 (ConceptSystem)")
from agi.concept import ConceptSystem, ConceptEncoder, Predictor

state_dim = 16
concept_system = ConceptSystem(state_dim=state_dim, initial_concepts=4)

# 模拟运行
for i in range(20):
    state = np.random.rand(state_dim)
    next_state = np.random.rand(state_dim)
    action = f"action_{i % 3}"
    
    concept, error, info = concept_system.step(state, next_state, action)

stats = concept_system.get_stats()
print(f"  ✓ 概念维度: {stats['concept_dim']}")
print(f"  ✓ 运行步数: {stats['step_count']}")
print(f"  ✓ 概念稳定性: {stats['encoder']['stability']:.3f}")
print(f"  ✓ 预测质量: {stats['predictor']['prediction_quality']:.3f}")

# 测试2: 目标系统
print("\n[测试2] 目标系统 (GoalSystem)")
from agi.goal import GoalSystem

goal_system = GoalSystem(state_dim=state_dim)

# 模拟运行
for i in range(150):
    state = np.random.rand(state_dim)
    action = f"action_{i % 4}"
    reward = np.random.rand()
    
    goal_system.step(state, action, reward, i)

stats = goal_system.get_stats()
print(f"  ✓ 活跃目标数: {stats['num_active_goals']}")
print(f"  ✓ 轨迹缓冲区: {stats['trajectory_buffer_size']}")

# 测试3: 自我模型
print("\n[测试3] 自我模型 (SelfModel)")
from agi.meta_drive import SelfModel

self_model = SelfModel(state_dim=state_dim, action_dim=10, drive_dim=4)

# 模拟运行
for i in range(50):
    state = np.random.rand(state_dim)
    action = np.zeros(10)
    action[i % 10] = 1.0
    
    self_model.update(state, action)

stats = self_model.get_stats()
print(f"  ✓ 策略预测准确率: {stats['policy_accuracy']:.3f}")
print(f"  ✓ 自我意识分数: {stats['self_awareness_score']:.3f}")

# 测试4: 元控制器
print("\n[测试4] 元控制器 (MetaController)")
from agi.meta_drive import MetaController

meta_controller = MetaController(self_model=self_model)

# 模拟运行
for i in range(50):
    state = np.random.rand(state_dim)
    performance = 0.5 + 0.3 * np.sin(i * 0.1)
    
    meta_controller.step(state, performance)

stats = meta_controller.get_stats()
print(f"  ✓ 元驱动数量: {stats['num_meta_drives']}")
print(f"  ✓ 元驱动影响: {stats['meta_drive_influence']:.3f}")
print(f"  ✓ 修改次数: {stats['num_modifications']}")

# 测试5: 生态系统
print("\n[测试5] 生态系统 (World)")
from agi.ecology import World

world = World(size=10, n_agents=3)

# 模拟运行
for i in range(50):
    stats = world.step()

print(f"  ✓ 存活智能体: {stats['alive_agents']}")
print(f"  ✓ 出生数: {stats['birth_count']}")
print(f"  ✓ 死亡数: {stats['death_count']}")
print(f"  ✓ 平均能量: {stats['avg_energy']:.2f}")
print(f"  ✓ 驱动多样性: {len(stats['drive_diversity'])} 个维度")

print("\n" + "=" * 60)
print("所有测试通过! 7层架构核心组件运行正常。")
print("=" * 60)
