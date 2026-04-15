#!/usr/bin/env python3
"""
7层架构长期测试 - 第1阶段: 概念系统 (500周期)
"""

import sys
import numpy as np
sys.path.insert(0, '.')
from agi.concept import ConceptSystem

print("="*60)
print("7层架构测试 - 阶段1: 概念系统 (500周期)")
print("="*60)

concept_system = ConceptSystem(state_dim=16, initial_concepts=4)
errors = []
stabilities = []

for i in range(500):
    state = np.random.rand(16)
    state[0] = 0.5 + 0.3 * np.sin(i * 0.1)
    state[1] = 0.5 + 0.3 * np.cos(i * 0.05)
    
    next_state = np.random.rand(16)
    next_state[0] = 0.5 + 0.3 * np.sin((i+1) * 0.1)
    next_state[1] = 0.5 + 0.3 * np.cos((i+1) * 0.05)
    
    concept, error, info = concept_system.step(state, next_state, f"a{i%5}")
    errors.append(error)
    stabilities.append(info['concept_stability'])
    
    if (i+1) % 100 == 0:
        print(f"Cycle {i+1:3d}: Error={np.mean(errors[-100:]):.4f}, Stability={np.mean(stabilities[-100:]):.4f}, Concepts={concept_system.concept_dim}")

print("\n" + "="*60)
print("概念系统测试结果:")
print(f"  初始概念数: 4")
print(f"  最终概念数: {concept_system.concept_dim}")
print(f"  概念分裂: {concept_system.split_count}")
print(f"  误差改进: {np.mean(errors[:50]):.4f} → {np.mean(errors[-50:]):.4f}")
print(f"  平均稳定性: {np.mean(stabilities):.4f}")
print("="*60)
