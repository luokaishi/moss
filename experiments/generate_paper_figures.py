"""
生成论文图表

创建实验结果的可视化图表
"""

import matplotlib.pyplot as plt
import numpy as np
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 创建输出目录
output_dir = 'docs/paper_figures'
os.makedirs(output_dir, exist_ok=True)

# 图1: 涌现事件统计对比
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# 左图：各实验涌现事件数
experiments = ['N=50', 'N=100', '24h', 'Semantic\n(N=50)']
emergence_counts = [145, 291, 42, 200]
colors = ['#3498db', '#2ecc71', '#e74c3c', '#9b59b6']

axes[0].bar(experiments, emergence_counts, color=colors, alpha=0.8, edgecolor='black')
axes[0].set_ylabel('Number of Emergence Events', fontsize=12)
axes[0].set_title('Emergence Events by Experiment', fontsize=14, fontweight='bold')
axes[0].grid(axis='y', alpha=0.3)

# 添加数值标签
for i, v in enumerate(emergence_counts):
    axes[0].text(i, v + 5, str(v), ha='center', fontsize=11, fontweight='bold')

# 右图：成功率对比
experiments2 = ['N=50', 'N=100', '24h']
success_rates = [90.0, 92.0, 100.0]

axes[1].bar(experiments2, success_rates, color=['#3498db', '#2ecc71', '#e74c3c'], alpha=0.8, edgecolor='black')
axes[1].set_ylabel('Success Rate (%)', fontsize=12)
axes[1].set_title('Success Rate by Experiment', fontsize=14, fontweight='bold')
axes[1].set_ylim(85, 105)
axes[1].grid(axis='y', alpha=0.3)

# 添加数值标签
for i, v in enumerate(success_rates):
    axes[1].text(i, v + 0.5, f'{v}%', ha='center', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig(f'{output_dir}/figure1_emergence_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

print("✅ Figure 1: Emergence comparison saved")

# 图2: 改进方案效果对比
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# 方案A：词汇扩展
categories_a = ['Before', 'After']
vocab_sizes = [10, 58]
unique_goals = [129, 199]

x = np.arange(len(categories_a))
width = 0.35

axes[0].bar(x - width/2, vocab_sizes, width, label='Vocabulary Size', color='#3498db', alpha=0.8)
axes[0].bar(x + width/2, unique_goals, width, label='Unique Goals', color='#2ecc71', alpha=0.8)
axes[0].set_ylabel('Count', fontsize=11)
axes[0].set_title('Scheme A: Vocabulary Expansion\n(5.8x increase)', fontsize=12, fontweight='bold')
axes[0].set_xticks(x)
axes[0].set_xticklabels(categories_a)
axes[0].legend()
axes[0].grid(axis='y', alpha=0.3)

# 方案B：结构多样化
word_counts = ['2-word', '3-word', '4-word', '5-word']
before_dist = [2.4, 95.2, 2.4, 0]
after_dist = [25.5, 28.5, 22.0, 24.0]

x = np.arange(len(word_counts))
axes[1].bar(x - width/2, before_dist, width, label='Before', color='#e74c3c', alpha=0.8)
axes[1].bar(x + width/2, after_dist, width, label='After', color='#2ecc71', alpha=0.8)
axes[1].set_ylabel('Percentage (%)', fontsize=11)
axes[1].set_title('Scheme B: Structural Diversification\n(4+ words: 0% → 46%)', fontsize=12, fontweight='bold')
axes[1].set_xticks(x)
axes[1].set_xticklabels(word_counts)
axes[1].legend()
axes[1].grid(axis='y', alpha=0.3)

# 方案C：语义合成
schemes = ['Original', 'A+B', 'Semantic\n(C)']
semantic_rates = [0, 10.5, 100]
novelty_scores = [0, 0.75, 0.936]

x = np.arange(len(schemes))
axes[2].bar(x - width/2, semantic_rates, width, label='Semantic Goals (%)', color='#9b59b6', alpha=0.8)
axes[2].bar(x + width/2, [n*100 for n in novelty_scores], width, label='Novelty Score (×100)', color='#f39c12', alpha=0.8)
axes[2].set_ylabel('Percentage / Score', fontsize=11)
axes[2].set_title('Scheme C: Semantic Synthesis\n(100% semantic, 0.936 novelty)', fontsize=12, fontweight='bold')
axes[2].set_xticks(x)
axes[2].set_xticklabels(schemes)
axes[2].legend()
axes[2].grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig(f'{output_dir}/figure2_improvement_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

print("✅ Figure 2: Improvement comparison saved")

# 图3: 四维度验证结果
fig, ax = plt.subplots(figsize=(10, 6))

dimensions = ['List\nIndependence', 'Semantic\nIndependence', 'Source\nIndependence', 'Causal\nIndependence']
pass_rates = [100, 100, 100, 100]
avg_scores = [1.00, 1.00, 1.00, 0.82]

x = np.arange(len(dimensions))
width = 0.35

bars1 = ax.bar(x - width/2, pass_rates, width, label='Pass Rate (%)', color='#2ecc71', alpha=0.8, edgecolor='black')
bars2 = ax.bar(x + width/2, [s*100 for s in avg_scores], width, label='Avg Score (×100)', color='#3498db', alpha=0.8, edgecolor='black')

ax.set_ylabel('Percentage / Score', fontsize=12)
ax.set_title('Four-Dimension Validation Results\n(100% pass rate, 0.96 average)', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(dimensions)
ax.legend(fontsize=11)
ax.grid(axis='y', alpha=0.3)
ax.set_ylim(0, 110)

# 添加数值标签
for bar in bars1:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 1, f'{height:.0f}%', 
            ha='center', va='bottom', fontsize=10, fontweight='bold')

for bar in bars2:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 1, f'{height/100:.2f}', 
            ha='center', va='bottom', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig(f'{output_dir}/figure3_validation_dimensions.png', dpi=300, bbox_inches='tight')
plt.close()

print("✅ Figure 3: Validation dimensions saved")

# 图4: 语义概念示例
fig, ax = plt.subplots(figsize=(12, 6))

concepts = ['knowledge_exchange', 'exploratory_adaptation', 'collaborative_defense', 
            'innovation_diffusion', 'experiential_learning', 'exploratory_innovation']
novelty = [0.95, 0.92, 0.90, 0.95, 0.94, 0.94]

# 创建渐变色
colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(concepts)))

bars = ax.barh(concepts, novelty, color=colors, alpha=0.8, edgecolor='black')
ax.set_xlabel('Novelty Score', fontsize=12)
ax.set_title('Semantic Concept Examples\n(Novelty: 0.90-0.95)', fontsize=14, fontweight='bold')
ax.set_xlim(0.85, 1.0)
ax.grid(axis='x', alpha=0.3)

# 添加数值标签
for i, (bar, score) in enumerate(zip(bars, novelty)):
    ax.text(score + 0.005, i, f'{score:.2f}', va='center', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig(f'{output_dir}/figure4_semantic_concepts.png', dpi=300, bbox_inches='tight')
plt.close()

print("✅ Figure 4: Semantic concepts saved")

print(f"\n🎉 All figures saved to {output_dir}/")
print("📊 Generated 4 figures:")
print("  1. figure1_emergence_comparison.png")
print("  2. figure2_improvement_comparison.png")
print("  3. figure3_validation_dimensions.png")
print("  4. figure4_semantic_concepts.png")
