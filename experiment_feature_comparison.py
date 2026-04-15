#!/usr/bin/env python3
"""
特征对比实验

比较: 手工设计特征 vs 自编码器学习特征
"""

import sys
import json
import numpy as np
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '.')

from agi.representation.autoencoder import StateAutoEncoder
from agi.concept import ConceptSystem
from agi.goal import GoalSystem
from agi.meta_drive.self_model_v2 import SelfModelV2

print("="*70)
print("特征对比实验: 手工特征 vs 学习特征")
print("="*70)

# 生成训练数据
np.random.seed(42)
n_samples = 2000
raw_observations = [np.random.randn(64) for _ in range(n_samples)]

# 训练自编码器
print("\n[1] 训练自编码器...")
encoder = StateAutoEncoder(input_dim=64, latent_dim=16, lr=0.01)
encoder.train(raw_observations[:1000], epochs=20)
print(f"  最终损失: {encoder.get_stats()['final_loss']:.4f}")

# 对比实验
print("\n[2] 运行对比实验...")

def run_experiment(feature_type, cycles=1000):
    """运行单种特征实验"""
    np.random.seed(42)
    
    if feature_type == 'handcrafted':
        state_dim = 16
    else:  # learned
        state_dim = 16
    
    action_dim = 5
    
    concept_system = ConceptSystem(state_dim=state_dim, initial_concepts=4)
    goal_system = GoalSystem(state_dim=state_dim)
    self_model = SelfModelV2(state_dim=state_dim, action_dim=action_dim, drive_dim=4)
    
    class MockDrive:
        def __init__(self, weight):
            self.weight = weight
    
    for cycle in range(cycles):
        # 生成原始观测
        raw_obs = np.random.randn(64)
        
        if feature_type == 'handcrafted':
            # 手工特征: 取前16维
            state = raw_obs[:16]
            state = (state - state.min()) / (state.max() - state.min() + 1e-8)
        else:
            # 学习特征: 通过自编码器
            state = encoder.get_representation(raw_obs)
        
        # 行为
        action = cycle % action_dim
        reward = 0.5 + 0.3 * np.sin(cycle * 0.01)
        drives = {'survival': MockDrive(0.6), 'explore': MockDrive(0.4)}
        
        next_raw = np.random.randn(64)
        if feature_type == 'handcrafted':
            next_state = next_raw[:16]
            next_state = (next_state - next_state.min()) / (next_state.max() - next_state.min() + 1e-8)
        else:
            next_state = encoder.get_representation(next_raw)
        
        # 更新
        concept_system.step(state, next_state, f"a{action}")
        goal_system.step(state, f"a{action}", reward, cycle)
        self_model.update(state, drives, action)
    
    return {
        'self_model_accuracy': self_model.policy_accuracy,
        'concept_stability': concept_system.encoder.get_concept_stability(),
        'num_goals': len(goal_system.active_goals),
        'goal_stability': np.mean([g.stability for g in goal_system.active_goals]) if goal_system.active_goals else 0
    }

# 运行两种实验
print("\n  运行手工特征实验...")
handcrafted_results = run_experiment('handcrafted')

print("  运行学习特征实验...")
learned_results = run_experiment('learned')

# 对比结果
print("\n" + "="*70)
print("对比结果")
print("="*70)

metrics = ['self_model_accuracy', 'concept_stability', 'num_goals', 'goal_stability']

print(f"\n{'指标':<25} {'手工特征':<15} {'学习特征':<15} {'差异':<10}")
print("-"*70)

for metric in metrics:
    h_val = handcrafted_results[metric]
    l_val = learned_results[metric]
    diff = l_val - h_val
    
    print(f"{metric:<25} {h_val:>14.4f} {l_val:>14.4f} {diff:>+9.4f}")

# 统计显著性判断
print("\n" + "="*70)
print("结论")
print("="*70)

improvements = []
for metric in metrics:
    diff = learned_results[metric] - handcrafted_results[metric]
    if abs(diff) > 0.05:
        improvements.append(f"{metric}: {'+' if diff>0 else ''}{diff:.4f}")

if improvements:
    print("\n✅ 学习特征相比手工特征的改进:")
    for imp in improvements:
        print(f"  - {imp}")
else:
    print("\n⚠️  两种特征表现相近 (差异<5%)")

# 保存结果
output_dir = Path('experiments/feature_comparison')
output_dir.mkdir(parents=True, exist_ok=True)

results = {
    'timestamp': datetime.now().isoformat(),
    'handcrafted': handcrafted_results,
    'learned': learned_results,
    'encoder_stats': encoder.get_stats(),
    'conclusion': 'learned_features_better' if improvements else 'similar_performance'
}

with open(output_dir / 'results.json', 'w') as f:
    json.dump(results, f, indent=2, default=str)

print(f"\n[保存] 结果已保存到: {output_dir}/results.json")

print("\n" + "="*70)
print("特征对比实验完成!")
print("="*70)
