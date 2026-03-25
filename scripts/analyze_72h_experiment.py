#!/usr/bin/env python3
"""
MOSS 72小时实验数据分析工具
生成 Purpose 演化可视化图表

使用: python3 scripts/analyze_72h_experiment.py
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from collections import Counter

def load_experiment_data():
    """加载实验数据"""
    data = {}
    
    # Purpose 历史
    purpose_file = Path('experiments/purpose_real_world_agent.json')
    if purpose_file.exists():
        with open(purpose_file) as f:
            data['purpose'] = json.load(f)
    
    # 行为日志
    actions_file = Path('experiments/real_world_actions.jsonl')
    if actions_file.exists():
        actions = []
        with open(actions_file) as f:
            for line in f:
                actions.append(json.loads(line))
        data['actions'] = actions
    
    return data

def plot_purpose_evolution(data, output_path='experiments/purpose_evolution.png'):
    """绘制Purpose演化图"""
    if 'purpose' not in data:
        print("No purpose data found")
        return
    
    history = data['purpose']['purpose_history']
    steps = [h['step'] for h in history]
    
    # 提取各维度
    dims = ['Survival', 'Curiosity', 'Influence', 'Optimization']
    colors = ['#e74c3c', '#3498db', '#9b59b6', '#2ecc71']
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('MOSS 72h Experiment: Purpose Evolution', fontsize=16)
    
    # 1. D1-D4 演化轨迹
    ax = axes[0, 0]
    for i, (dim, color) in enumerate(zip(dims, colors)):
        values = [h['purpose_vector'][i] for h in history]
        ax.plot(steps, values, label=dim, color=color, linewidth=2)
    ax.set_xlabel('Step')
    ax.set_ylabel('Purpose Weight')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_title('D1-D4 Purpose Evolution')
    
    # 2. D9 (Purpose Strength)
    ax = axes[0, 1]
    d9_values = [h['purpose_vector'][8] for h in history]
    ax.plot(steps, d9_values, color='#e67e22', linewidth=2)
    ax.axhline(y=0, color='r', linestyle='--', alpha=0.5, label='Zero line')
    ax.set_xlabel('Step')
    ax.set_ylabel('D9 Strength')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_title('D9 Purpose Strength (Note: Bug in early data)')
    
    # 3. 主导维度分布
    ax = axes[1, 0]
    dominant_dims = []
    for h in history:
        max_idx = np.argmax(h['purpose_vector'][:4])
        dominant_dims.append(dims[max_idx])
    
    counts = Counter(dominant_dims)
    ax.bar(counts.keys(), counts.values(), color=colors)
    ax.set_ylabel('Count')
    ax.set_title('Dominant Purpose Distribution')
    
    # 4. Purpose变化幅度
    ax = axes[1, 1]
    changes = []
    change_steps = []
    for i in range(1, len(history)):
        prev = np.array(history[i-1]['purpose_vector'][:4])
        curr = np.array(history[i]['purpose_vector'][:4])
        change = np.linalg.norm(curr - prev)
        changes.append(change)
        change_steps.append(history[i]['step'])
    
    ax.plot(change_steps, changes, color='#34495e', linewidth=2)
    ax.set_xlabel('Step')
    ax.set_ylabel('Change Magnitude')
    ax.grid(True, alpha=0.3)
    ax.set_title('Purpose Change Magnitude')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {output_path}")

def plot_tool_usage(data, output_path='experiments/tool_usage.png'):
    """绘制工具使用分布"""
    if 'actions' not in data:
        print("No action data found")
        return
    
    actions = data['actions']
    
    # 统计工具使用
    tools = Counter(a['action']['tool'] for a in actions)
    purposes = Counter(a['purpose']['dominant'] for a in actions)
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('MOSS 72h Experiment: Tool Usage & Purpose Distribution', fontsize=14)
    
    # 工具使用
    ax = axes[0]
    colors = ['#3498db', '#2ecc71', '#e74c3c']
    ax.pie(tools.values(), labels=tools.keys(), autopct='%1.1f%%', colors=colors)
    ax.set_title('Tool Usage Distribution')
    
    # Purpose分布
    ax = axes[1]
    colors2 = ['#e74c3c', '#3498db', '#9b59b6', '#2ecc71']
    ax.bar(purposes.keys(), purposes.values(), color=colors2)
    ax.set_ylabel('Count')
    ax.set_title('Action Purpose Distribution')
    ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {output_path}")

def generate_summary_report(data):
    """生成文字摘要报告"""
    print("\n" + "="*60)
    print("MOSS 72小时实验 - 数据分析报告")
    print("="*60)
    
    if 'purpose' in data:
        history = data['purpose']['purpose_history']
        print(f"\n📊 Purpose统计:")
        print(f"  总生成次数: {len(history)}")
        
        dims = ['Survival', 'Curiosity', 'Influence', 'Optimization']
        dominant_counts = Counter(dims[np.argmax(h['purpose_vector'][:4])] for h in history)
        print(f"  主导分布:")
        for dim, count in dominant_counts.most_common():
            print(f"    {dim}: {count}次 ({count/len(history)*100:.1f}%)")
    
    if 'actions' in data:
        actions = data['actions']
        print(f"\n🛠️  操作统计:")
        print(f"  总操作数: {len(actions)}")
        
        tools = Counter(a['action']['tool'] for a in actions)
        print(f"  工具分布:")
        for tool, count in tools.most_common():
            print(f"    {tool}: {count}次 ({count/len(actions)*100:.1f}%)")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    print("Loading experiment data...")
    data = load_experiment_data()
    
    if not data:
        print("No data found. Make sure experiment is running.")
    else:
        print(f"Loaded:")
        if 'purpose' in data:
            print(f"  - Purpose history: {len(data['purpose']['purpose_history'])} entries")
        if 'actions' in data:
            print(f"  - Actions: {len(data['actions'])} entries")
        
        # 生成图表
        try:
            plot_purpose_evolution(data)
            plot_tool_usage(data)
            generate_summary_report(data)
            print("\n✅ Analysis complete!")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
