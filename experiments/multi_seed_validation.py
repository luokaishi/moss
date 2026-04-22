#!/usr/bin/env python3
"""
多随机种子验证 - Phase 4
运行多次实验，验证涌现的稳定性
"""
import sys
sys.path.insert(0, '/home/admin/.openclaw/workspace')

from agi.genetic_programmer import GeneticProgrammer
import numpy as np
import random
import json
from datetime import datetime

print("=" * 70)
print("多随机种子验证 - 检查涌现稳定性")
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
        
        # 模式：entropy_variance 高且 resource_level 低时 -> label=1
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

# 测试多个种子
seeds = [42, 123, 456, 789, 2024, 31415, 271828, 161803, 999999, 111111]
results = []

print(f"\n测试 {len(seeds)} 个随机种子...\n")

for seed in seeds:
    print(f"Seed {seed}: ", end="", flush=True)
    
    behavior_labels, env_states = create_patterned_data(seed=seed)
    
    gp = GeneticProgrammer({
        'population_size': 150,
        'generations': 50,
        'acceptance_threshold': 0.25,
    })
    
    result = gp.evolve(behavior_labels, env_states)
    
    if result:
        print(f"✅ {result.expr_string[:40]}... (gain={result.behavioral_gain:.3f}, nodes={result.node_count})")
        results.append({
            'seed': seed,
            'success': True,
            'expr': result.expr_string,
            'fitness': result.fitness,
            'gain': result.behavioral_gain,
            'nodes': result.node_count,
            'features': result.source_features,
        })
    else:
        print("❌ No valid function")
        results.append({
            'seed': seed,
            'success': False,
        })

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
    
    # 检查是否都是复合函数
    single_terminal = sum(1 for r in results if r['success'] and r['nodes'] == 1)
    print(f"单终端函数: {single_terminal}/{success_count}")
    
    # 常用特征
    all_features = []
    for r in results:
        if r['success']:
            all_features.extend(r['features'])
    
    from collections import Counter
    feature_counts = Counter(all_features)
    print(f"\n常用特征 (Top 5):")
    for feat, count in feature_counts.most_common(5):
        print(f"  {feat}: {count} 次")

# 保存结果
output = {
    'timestamp': datetime.now().isoformat(),
    'seeds_tested': len(seeds),
    'success_rate': success_rate,
    'results': results,
}

output_path = '/home/admin/.openclaw/workspace/experiments/multi_seed_results.json'
with open(output_path, 'w') as f:
    json.dump(output, f, indent=2)

print(f"\n结果已保存: {output_path}")

# 结论
print("\n" + "=" * 70)
if success_rate >= 0.7:
    print("✅ 涌现稳定性良好 (成功率 ≥ 70%)")
elif success_rate >= 0.5:
    print("⚠️ 涌现稳定性一般 (成功率 50-70%)")
else:
    print("❌ 涌现稳定性不足 (成功率 < 50%)")
print("=" * 70)
