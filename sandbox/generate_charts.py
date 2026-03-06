#!/usr/bin/env python3
"""
MOSS实验数据可视化生成器
生成论文所需图表
"""

import json
import os

def generate_ascii_charts():
    """生成ASCII图表（无需matplotlib）"""
    
    # 读取数据
    with open('/workspace/projects/moss/logs/results_20260306_155322.json', 'r') as f:
        data = json.load(f)
    
    history = data['history']
    
    print("="*70)
    print("MOSS 500-Generation Evolution Charts")
    print("="*70)
    
    # 1. 知识增长曲线
    print("\n📈 Chart 1: Knowledge Growth Over 500 Generations")
    print("-"*70)
    
    milestones = [0, 100, 200, 300, 400, 499]
    max_knowledge = history[-1]['total_knowledge']
    
    for gen in milestones:
        if gen < len(history):
            h = history[gen]
            knowledge = h['total_knowledge']
            bar_len = int((knowledge / max_knowledge) * 50)
            bar = "█" * bar_len
            print(f"Gen {gen:3d}: {bar:50s} {knowledge:>8,}")
    
    # 2. 种群增长曲线
    print("\n📊 Chart 2: Population Growth")
    print("-"*70)
    
    max_pop = 100
    for gen in [0, 1, 2, 3, 10, 50, 100, 200, 499]:
        if gen < len(history):
            h = history[gen]
            pop = h['alive']
            bar_len = int((pop / max_pop) * 40)
            bar = "█" * bar_len
            print(f"Gen {gen:3d}: {bar:40s} {pop:>3d} agents")
    
    # 3. 能量增长
    print("\n⚡ Chart 3: Average Energy Growth")
    print("-"*70)
    
    max_energy = history[-1]['avg_energy']
    for gen in milestones:
        if gen < len(history):
            h = history[gen]
            energy = h['avg_energy']
            bar_len = int((energy / max_energy) * 40)
            bar = "█" * bar_len
            print(f"Gen {gen:3d}: {bar:40s} {energy:>8.1f}")
    
    # 4. 关键统计数据
    print("\n📊 Key Statistics Summary")
    print("-"*70)
    initial = history[0]
    final = history[-1]
    
    print(f"\nPopulation:")
    print(f"  Initial: {initial['alive']} → Final: {final['alive']} ({final['alive']/initial['alive']:.1f}x)")
    
    print(f"\nKnowledge:")
    print(f"  Initial: {initial['total_knowledge']:,} → Final: {final['total_knowledge']:,}")
    print(f"  Growth: {final['total_knowledge']/initial['total_knowledge']:.0f}x")
    print(f"  Per Generation: +{(final['total_knowledge']-initial['total_knowledge'])/len(history):.0f}")
    
    print(f"\nEnergy:")
    print(f"  Initial: {initial['avg_energy']:.1f} → Final: {final['avg_energy']:.1f}")
    print(f"  Growth: {final['avg_energy']/initial['avg_energy']:.1f}x")
    
    print(f"\nExploration Stability:")
    explore_values = [h['avg_explore'] for h in history]
    avg_explore = sum(explore_values) / len(explore_values)
    min_explore = min(explore_values)
    max_explore = max(explore_values)
    print(f"  Average: {avg_explore:.4f}")
    print(f"  Range: {min_explore:.4f} - {max_explore:.4f}")
    print(f"  Stability: ±{(max_explore-min_explore)/2:.4f}")
    
    print("\n" + "="*70)
    print("✅ Charts generated successfully!")
    print("="*70)

if __name__ == "__main__":
    generate_ascii_charts()
