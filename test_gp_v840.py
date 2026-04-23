#!/usr/bin/env python3
"""测试 GP v8.4.0 优化效果"""
import sys
sys.path.insert(0, '/home/admin/.openclaw/workspace')

from agi.genetic_programmer import GeneticProgrammer
import numpy as np
import random

print("=" * 70)
print("GP v8.4.0 性能测试")
print("=" * 70)

# 创建有模式的数据
def create_patterned_data(n=100, seed=42):
    random.seed(seed)
    np.random.seed(seed)
    
    behavior_labels = []
    env_states = []
    
    for i in range(n):
        ev = np.random.random()
        rl = np.random.random()
        
        if ev > 0.6 and rl < 0.4:
            label = 1
        else:
            label = 0
        
        behavior_labels.append(label)
        env_states.append({
            'entropy_variance': ev,
            'resource_level': rl,
            'environment_entropy': np.random.random(),
            'file_count_norm': np.random.random(),
            'visited_ratio': np.random.random(),
        })
    
    return behavior_labels, env_states

# 测试 20 个种子
seeds = [42, 123, 456, 789, 2024, 31415, 271828, 161803, 999999, 111111,
         555555, 777777, 888888, 666666, 333333, 121212, 131313, 141414, 151515, 161616]

print(f"\n测试 {len(seeds)} 个随机种子 (v8.4.0 参数)...\n")
print(f"配置: pop=300, gens=100, crossover=0.6, mutation=0.5")
print()

results = []
for seed in seeds:
    print(f"Seed {seed}: ", end="", flush=True)
    
    behavior_labels, env_states = create_patterned_data(seed=seed)
    
    # 使用 v8.4.0 默认参数
    gp = GeneticProgrammer({})
    
    result = gp.evolve(behavior_labels, env_states)
    
    if result:
        print(f"✅ gain={result.behavioral_gain:.3f}, nodes={result.node_count}")
        results.append({
            'seed': seed,
            'success': True,
            'gain': result.behavioral_gain,
            'nodes': result.node_count,
        })
    else:
        print("❌ No valid function")
        results.append({'seed': seed, 'success': False})

# 统计
print("\n" + "=" * 70)
print("统计结果")
print("=" * 70)

success_count = sum(1 for r in results if r['success'])
success_rate = success_count / len(results)

print(f"\n成功率: {success_count}/{len(results)} ({success_rate*100:.1f}%)")

if success_count > 0:
    gains = [r['gain'] for r in results if r['success']]
    nodes = [r['nodes'] for r in results if r['success']]
    
    print(f"平均 Behavioral Gain: {np.mean(gains):.3f} (±{np.std(gains):.3f})")
    print(f"平均节点数: {np.mean(nodes):.1f} (±{np.std(nodes):.1f})")
    print(f"最小 Gain: {min(gains):.3f}")
    print(f"最大 Gain: {max(gains):.3f}")

print("\n" + "=" * 70)
if success_rate >= 0.8:
    print(f"✅ 目标达成! ({success_rate*100:.0f}% >= 80%)")
elif success_rate >= 0.7:
    print(f"⚠️ 接近目标 ({success_rate*100:.0f}% >= 70%)")
else:
    print(f"❌ 未达目标 ({success_rate*100:.0f}% < 70%)")
print("=" * 70)
