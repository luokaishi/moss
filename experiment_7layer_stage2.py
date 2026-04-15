#!/usr/bin/env python3
"""
7层架构长期测试 - 第2阶段: 元驱动与自我模型 (500周期)
"""

import sys
import numpy as np
sys.path.insert(0, '.')
from agi.meta_drive import SelfModel, MetaController

print("="*60)
print("7层架构测试 - 阶段2: 元驱动与自我模型 (500周期)")
print("="*60)

self_model = SelfModel(state_dim=16, action_dim=10, drive_dim=4)
meta_controller = MetaController(self_model=self_model)

awareness_history = []
modification_count = 0

for i in range(500):
    state = np.random.rand(16)
    action = np.zeros(10)
    action[i % 10] = 1.0
    
    self_model.update(state, action)
    
    performance = 0.5 + 0.3 * np.sin(i * 0.02) + 0.05 * np.random.randn()
    performance = np.clip(performance, 0, 1)
    
    prev_mods = len(meta_controller.modification_history)
    meta_controller.step(state, performance)
    if len(meta_controller.modification_history) > prev_mods:
        modification_count += 1
    
    awareness = self_model.get_self_awareness_score()
    awareness_history.append(awareness)
    
    if (i+1) % 100 == 0:
        print(f"Cycle {i+1:3d}: Awareness={awareness:.4f}, PolicyAcc={self_model.policy_accuracy:.4f}, Mods={modification_count}")

print("\n" + "="*60)
print("元驱动与自我模型测试结果:")
print(f"  初始自我意识: {np.mean(awareness_history[:20]):.4f}")
print(f"  最终自我意识: {np.mean(awareness_history[-20:]):.4f}")
print(f"  趋势: {'↑ 提升' if awareness_history[-1] > awareness_history[0] else '→ 稳定/下降'}")
print(f"  自我修改次数: {modification_count}")
print(f"  策略预测准确率: {self_model.policy_accuracy:.4f}")
print(f"  驱动演化准确率: {self_model.drive_accuracy:.4f}")
print("="*60)
