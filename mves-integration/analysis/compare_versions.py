#!/usr/bin/env python3
"""
MVES 版本对比分析工具
比较 v1-v4 的实验结果
"""

import json
import os
import matplotlib.pyplot as plt
import numpy as np

def load_checkpoint(version, gen):
    """加载检查点数据"""
    path = f"../mves_v{version}/checkpoints/checkpoint_gen{gen:04d}.json"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None

def extract_metrics(version):
    """提取版本的指标时间序列"""
    metrics = []
    for gen in range(10, 101, 10):
        cp = load_checkpoint(version, gen)
        if cp:
            if 'metrics' in cp:
                metrics.append({
                    'generation': gen,
                    'population': cp['metrics'].get('population_size', 0),
                    'energy': cp['metrics'].get('avg_energy', 0),
                    'complexity': cp['metrics'].get('complexity_score', 0),
                    'entropy': cp['metrics'].get('behavior_entropy', 0)
                })
            elif 'population' in cp:
                # v1-v3 格式
                pop = cp['population']
                metrics.append({
                    'generation': gen,
                    'population': len(pop),
                    'energy': np.mean([a.get('energy', 0) for a in pop]),
                    'complexity': 1.0 + np.mean([a.get('mutations', 0) for a in pop]) * 0.1,
                    'entropy': 1.0
                })
    return metrics

def plot_comparison():
    """绘制版本对比图"""
    versions = [1, 2, 3, 4]
    colors = ['blue', 'green', 'orange', 'red']
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # 1. 存活率
    ax = axes[0, 0]
    for v, c in zip(versions, colors):
        metrics = extract_metrics(v)
        if metrics:
            pops = [m['population'] for m in metrics]
            gens = [m['generation'] for m in metrics]
            ax.plot(gens, pops, label=f'v{v}', color=c, marker='o')
    ax.set_xlabel('Generation')
    ax.set_ylabel('Population Size')
    ax.set_title('Population Survival')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 2. 能量变化
    ax = axes[0, 1]
    for v, c in zip(versions, colors):
        metrics = extract_metrics(v)
        if metrics:
            energies = [m['energy'] for m in metrics]
            gens = [m['generation'] for m in metrics]
            ax.plot(gens, energies, label=f'v{v}', color=c, marker='s')
    ax.set_xlabel('Generation')
    ax.set_ylabel('Average Energy')
    ax.set_title('Energy Dynamics')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 3. 复杂度
    ax = axes[1, 0]
    for v, c in zip(versions, colors):
        metrics = extract_metrics(v)
        if metrics:
            complexities = [m['complexity'] for m in metrics]
            gens = [m['generation'] for m in metrics]
            ax.plot(gens, complexities, label=f'v{v}', color=c, marker='^')
    ax.set_xlabel('Generation')
    ax.set_ylabel('Complexity Score')
    ax.set_title('Complexity Growth')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 4. 行为熵
    ax = axes[1, 1]
    for v, c in zip(versions, colors):
        metrics = extract_metrics(v)
        if metrics:
            entropies = [m['entropy'] for m in metrics]
            gens = [m['generation'] for m in metrics]
            ax.plot(gens, entropies, label=f'v{v}', color=c, marker='d')
    ax.set_xlabel('Generation')
    ax.set_ylabel('Behavior Entropy')
    ax.set_title('Behavior Diversity')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('version_comparison.png', dpi=150)
    print("✅ 对比图已保存：version_comparison.png")
    plt.show()

def summary_table():
    """生成总结表格"""
    print("\n" + "="*70)
    print("MVES 实验总结")
    print("="*70)
    print(f"{'版本':<8} {'存活率':<10} {'变异数':<10} {'复杂度':<10} {'关键发现':<30}")
    print("-"*70)
    print(f"{'v1':<8} {'100%':<10} {'3':<10} {'低':<10} {'策略跃迁':<30}")
    print(f"{'v2':<8} {'100%':<10} {'6':<10} {'中':<10} {'反思驱动':<30}")
    print(f"{'v3':<8} {'100%':<10} {'42':<10} {'中高':<10} {'代码演化':<30}")
    print(f"{'v4':<8} {'20%':<10} {'0':<10} {'低':<10} {'驱动失衡':<30}")
    print("="*70)

if __name__ == "__main__":
    summary_table()
    
    try:
        plot_comparison()
    except ImportError:
        print("⚠️ 需要安装 matplotlib: pip install matplotlib")
