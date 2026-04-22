#!/usr/bin/env python3
"""快速测试改进后的 GP"""
import sys
sys.path.insert(0, '/home/admin/.openclaw/workspace')

from agi.genetic_programmer import GeneticProgrammer
import numpy as np
import random

# 设置种子
random.seed(42)
np.random.seed(42)

# 创建有模式的数据（确保 GP 能学到东西）
n = 100
behavior_labels = []
env_states = []

for i in range(n):
    # 创建人工模式：当 entropy_variance > 0.5 且 resource_level < 0.3 时，label=1
    ev = np.random.random()
    rl = np.random.random()
    
    if ev > 0.5 and rl < 0.3:
        label = 1
    else:
        label = 0
    
    behavior_labels.append(label)
    env_states.append({
        'entropy_variance': ev,
        'resource_level': rl,
        'environment_entropy': np.random.random(),
        'file_count_norm': np.random.random(),
    })

print("Testing Improved GP v8.2.1")
print(f"Data: {n} samples, {sum(behavior_labels)} positive")
print()

gp = GeneticProgrammer({
    'population_size': 150,
    'generations': 50,
    'acceptance_threshold': 0.25,
})

result = gp.evolve(behavior_labels, env_states)

if result:
    print(f"✅ SUCCESS!")
    print(f"   Expression: {result.expr_string}")
    print(f"   Fitness: {result.fitness:.3f}")
    print(f"   Correlation: {result.correlation:.3f}")
    print(f"   Behavioral Gain: {result.behavioral_gain:.3f}")
    print(f"   Node Count: {result.node_count}")
    print(f"   Features: {result.source_features}")
    
    # 验证不是单终端
    if result.node_count > 1:
        print(f"   ✅ Composite function (not single terminal)")
    else:
        print(f"   ⚠️ Single terminal function")
else:
    print("❌ No valid function found")
