#!/usr/bin/env python3
"""
7层架构长期测试 - 第3阶段: 生态系统 (500周期)
"""

import sys
import numpy as np
sys.path.insert(0, '.')
from agi.ecology import World

print("="*60)
print("7层架构测试 - 阶段3: 生态系统 (500周期)")
print("="*60)

world = World(size=10, n_agents=3)

agent_counts = []
energy_history = []

for i in range(500):
    stats = world.step()
    agent_counts.append(stats['alive_agents'])
    energy_history.append(stats['avg_energy'])
    
    if (i+1) % 100 == 0:
        print(f"Cycle {i+1:3d}: Agents={stats['alive_agents']}, Energy={stats['avg_energy']:.1f}, Births={stats['birth_count']}, Deaths={stats['death_count']}")

print("\n" + "="*60)
print("生态系统测试结果:")
print(f"  最终存活: {stats['alive_agents']} 智能体")
print(f"  总出生: {stats['birth_count']}")
print(f"  总死亡: {stats['death_count']}")
print(f"  平均能量: {np.mean(energy_history):.1f}")
print(f"  能量稳定性: {1.0 - np.std(energy_history)/np.mean(energy_history):.3f}")
print(f"  驱动多样性维度: {len(stats['drive_diversity'])}")
for key, div in list(stats['drive_diversity'].items())[:2]:
    print(f"    - {key}: mean={div['mean']:.3f}, std={div['std']:.3f}")
print("="*60)
