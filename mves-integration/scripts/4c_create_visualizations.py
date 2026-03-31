#!/usr/bin/env python3
"""
Phase 4c - 可视化生成

生成论文级别的专业图表
"""

import json
import csv
import os
from pathlib import Path
from datetime import datetime

# 设置 matplotlib 使用非交互式后端
import os
os.environ['MPLBACKEND'] = 'Agg'

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')
    HAS_MATPLOTLIB = True
    print("✓ matplotlib 已安装，版本:", matplotlib.__version__)
except ImportError:
    HAS_MATPLOTLIB = False
    print("⚠️  matplotlib 未安装，使用文本模式生成图表")


def load_data():
    """加载数据"""
    data = []
    with open('analysis/dataset_clean.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            for key in row:
                try:
                    row[key] = float(row[key])
                except (ValueError, TypeError):
                    pass
            data.append(row)
    return data


def create_fitness_evolution_plot(data, output_file='plots/fitness_evolution.png'):
    """创建适应度演化曲线图"""
    if not HAS_MATPLOTLIB:
        print_text_fitness_plot(data)
        return
    
    generations = [d['generation'] for d in data]
    fitness = [d['avg_fitness'] for d in data]
    
    plt.figure(figsize=(12, 8))
    
    # 主图
    plt.subplot(2, 1, 1)
    plt.plot(generations, fitness, 'b-o', linewidth=2.5, markersize=6, label='Average Fitness')
    
    # 指数拟合曲线
    import math
    a, b = 2.18, 0.011
    fitted = [a * math.exp(b * x) for x in generations]
    plt.plot(generations, fitted, 'r--', linewidth=2, label=f'Exponential Fit (y={a:.2f}·e^({b:.4f}·x))')
    
    plt.xlabel('Generation', fontsize=12)
    plt.ylabel('Fitness Score', fontsize=12)
    plt.title('MVES v5: Fitness Evolution Over Generations', fontsize=14, fontweight='bold')
    plt.legend(loc='upper left')
    plt.grid(True, alpha=0.3)
    
    # 标注关键点
    max_idx = fitness.index(max(fitness))
    plt.annotate(f'Max: {max(fitness):.2f}\n@ Gen {generations[max_idx]}',
                xy=(generations[max_idx], fitness[max_idx]),
                xytext=(generations[max_idx]+10, fitness[max_idx]-1),
                arrowprops=dict(arrowstyle='->', color='red', lw=2),
                fontsize=10, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # 增长率子图
    plt.subplot(2, 1, 2)
    growth_rates = []
    for i in range(1, len(fitness)):
        if fitness[i-1] > 0:
            rate = (fitness[i] - fitness[i-1]) / fitness[i-1] * 100
            growth_rates.append(rate)
    
    gen_rates = generations[1:]
    plt.bar(gen_rates, growth_rates, color='steelblue', alpha=0.7, width=3)
    plt.axhline(y=0, color='red', linestyle='-', linewidth=1)
    plt.axhline(y=53.76, color='green', linestyle='--', linewidth=2, label=f'Avg: 53.76%')
    
    plt.xlabel('Generation', fontsize=12)
    plt.ylabel('Growth Rate (%)', fontsize=12)
    plt.title('Generation-over-Generation Growth Rate', fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ 适应度演化图已保存：{output_file}")


def print_text_fitness_plot(data):
    """文本模式适应度图"""
    print("\n" + "="*70)
    print("适应度演化曲线 (文本模式)")
    print("="*70)
    
    generations = [d['generation'] for d in data]
    fitness = [d['avg_fitness'] for d in data]
    
    max_fit = max(fitness)
    min_fit = min(fitness)
    range_fit = max_fit - min_fit if max_fit != min_fit else 1
    
    for gen, fit in zip(generations, fitness):
        bar_len = int((fit - min_fit) / range_fit * 50)
        bar = "█" * bar_len
        marker = "← MAX" if fit == max_fit else ""
        print(f"Gen {gen:3.0f}: {bar} {fit:6.3f} {marker}")
    
    print("="*70)


def create_diversity_analysis_plot(data, output_file='plots/diversity_analysis.png'):
    """创建多样性分析图"""
    if not HAS_MATPLOTLIB:
        print("跳过多样性图 (需要 matplotlib)")
        return
    
    generations = [d['generation'] for d in data]
    diversity = [d.get('diversity', 0) for d in data]
    complexity = [d.get('complexity', 0) for d in data]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # 多样性变化
    ax1.plot(generations, diversity, 'g-o', linewidth=2, markersize=6)
    ax1.set_xlabel('Generation', fontsize=12)
    ax1.set_ylabel('Diversity Index', fontsize=12)
    ax1.set_title('Population Diversity Over Time', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=0.3, color='orange', linestyle='--', label='Min Threshold (0.3)')
    ax1.legend()
    
    # 复杂度变化
    ax2.plot(generations, complexity, 'purple', linewidth=2, markersize=6)
    ax2.set_xlabel('Generation', fontsize=12)
    ax2.set_ylabel('Complexity Score', fontsize=12)
    ax2.set_title('System Complexity Over Time', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ 多样性分析图已保存：{output_file}")


def create_milestone_plot(data, output_file='plots/milestones.png'):
    """创建里程碑图"""
    if not HAS_MATPLOTLIB:
        print("跳过里程碑图 (需要 matplotlib)")
        return
    
    generations = [d['generation'] for d in data]
    fitness = [d['avg_fitness'] for d in data]
    
    plt.figure(figsize=(14, 8))
    plt.plot(generations, fitness, 'b-o', linewidth=2.5, markersize=6, alpha=0.6)
    
    # 标注里程碑
    milestones = [
        (1, 'Start', 'green'),
        (50, 'Fitness≥5', 'orange'),
        (100, '100 Gen', 'blue'),
        (140, 'Max: 10.26', 'red')
    ]
    
    for target_gen, label, color in milestones:
        closest_idx = min(range(len(generations)), key=lambda i: abs(generations[i] - target_gen))
        plt.scatter([generations[closest_idx]], [fitness[closest_idx]], 
                   c=color, s=200, zorder=5, label=label, edgecolors='black', linewidth=2)
    
    plt.xlabel('Generation', fontsize=12)
    plt.ylabel('Fitness Score', fontsize=12)
    plt.title('MVES v5: Key Milestones', fontsize=14, fontweight='bold')
    plt.legend(loc='upper left', fontsize=10)
    plt.grid(True, alpha=0.3)
    
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ 里程碑图已保存：{output_file}")


def create_summary_report():
    """生成可视化总结报告"""
    report = []
    report.append("# MVES v5 可视化报告")
    report.append(f"\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"\n## 已生成图表\n")
    
    plots_dir = Path('plots')
    if plots_dir.exists():
        plots = list(plots_dir.glob('*.png'))
        for plot in plots:
            size_kb = plot.stat().st_size / 1024
            report.append(f"- ✅ `{plot.name}` ({size_kb:.1f} KB)")
    
    report.append(f"\n## 图表说明\n")
    report.append("1. **fitness_evolution.png** - 适应度演化曲线 + 增长率")
    report.append("2. **diversity_analysis.png** - 多样性与复杂度分析")
    report.append("3. **milestones.png** - 关键里程碑标注")
    
    report_path = 'plots/VISUALIZATION_SUMMARY.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"✓ 可视化总结已保存：{report_path}")


def main():
    """主函数"""
    print("📊 Phase 4c - 可视化生成")
    print("="*60)
    
    # 创建目录
    Path('plots').mkdir(exist_ok=True)
    
    # 加载数据
    print("\n加载数据...")
    data = load_data()
    print(f"✓ 加载 {len(data)} 条记录")
    
    if not data:
        print("❌ 数据为空，跳过可视化")
        return
    
    # 生成图表
    print("\n生成图表...")
    
    print("1. 生成适应度演化图...")
    create_fitness_evolution_plot(data)
    
    print("2. 生成多样性分析图...")
    create_diversity_analysis_plot(data)
    
    print("3. 生成里程碑图...")
    create_milestone_plot(data)
    
    # 生成总结
    print("\n生成总结报告...")
    create_summary_report()
    
    print("\n✅ Phase 4c 完成！")
    print("下一步：Phase 4d - 能力涌现分析")


if __name__ == "__main__":
    main()
