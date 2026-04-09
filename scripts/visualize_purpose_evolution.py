#!/usr/bin/env python3
"""
MOSS Purpose Evolution Visualizer
==================================

Purpose演化轨迹可视化工具

生成：
- Purpose向量时间序列图
- 主导Purpose变化图
- Purpose空间轨迹图（3D投影）

Usage:
    python scripts/visualize_purpose_evolution.py --input experiments/real_world_actions.jsonl --output reports/
"""

import json
import numpy as np
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict


def load_purpose_data(input_file: str) -> List[Dict]:
    """加载Purpose数据"""
    purpose_history = []
    
    with open(input_file, 'r') as f:
        for line in f:
            try:
                action = json.loads(line.strip())
                if 'purpose' in action:
                    purpose_data = action['purpose']
                    purpose_history.append({
                        'step': action.get('step', 0),
                        'timestamp': action.get('timestamp', ''),
                        'vector': purpose_data.get('vector', []),
                        'dominant': purpose_data.get('dominant', 'Unknown')
                    })
            except json.JSONDecodeError:
                continue
    
    return purpose_history


def generate_ascii_timeline(purpose_history: List[Dict], output_file: Path):
    """生成ASCII时间线图表"""
    if not purpose_history:
        return
    
    # 简化的Purpose字符映射
    purpose_chars = {
        'Survival': 'S',
        'Curiosity': 'C',
        'Influence': 'I',
        'Optimization': 'O',
        'Coherence': 'H',
        'Valence': 'V',
        'Other': 'T',
        'Norm': 'N',
        'Unknown': '?'
    }
    
    with open(output_file, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("Purpose Evolution Timeline (ASCII)\n")
        f.write("=" * 70 + "\n\n")
        
        # 时间线每100个记录显示一次
        interval = max(1, len(purpose_history) // 50)
        
        for i in range(0, len(purpose_history), interval):
            record = purpose_history[i]
            step = record['step']
            dominant = record['dominant']
            char = purpose_chars.get(dominant, '?')
            vector = record['vector']
            
            # 显示前4维的简化表示
            if vector and len(vector) >= 4:
                vec_str = f"[{vector[0]:.2f},{vector[1]:.2f},{vector[2]:.2f},{vector[3]:.2f}]"
            else:
                vec_str = "[N/A]"
            
            bar = char * 20
            f.write(f"Step {step:>8}: {bar} {dominant:<15} {vec_str}\n")
        
        f.write("\n" + "=" * 70 + "\n")
        f.write("Legend: S=Survival C=Curiosity I=Influence O=Optimization\n")
        f.write("=" * 70 + "\n")


def generate_dominant_purpose_changes(purpose_history: List[Dict], output_file: Path):
    """生成主导Purpose变化记录"""
    if not purpose_history:
        return
    
    with open(output_file, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("Dominant Purpose Changes\n")
        f.write("=" * 70 + "\n\n")
        
        prev_dominant = None
        change_count = 0
        
        for record in purpose_history:
            current = record['dominant']
            if current != prev_dominant:
                change_count += 1
                f.write(f"Change #{change_count:>3} at Step {record['step']:>8}: "
                       f"{prev_dominant or 'N/A':>15} → {current:<15}\n")
                prev_dominant = current
        
        f.write(f"\nTotal Changes: {change_count}\n")
        f.write("=" * 70 + "\n")


def generate_purpose_statistics(purpose_history: List[Dict], output_file: Path):
    """生成Purpose统计报告"""
    if not purpose_history:
        return
    
    from collections import Counter
    
    # 统计主导Purpose
    dominants = [p['dominant'] for p in purpose_history if p['dominant']]
    distribution = Counter(dominants)
    
    # 计算平均向量
    vectors = [p['vector'] for p in purpose_history if p['vector']]
    if vectors:
        avg_vector = np.mean(vectors, axis=0)
    else:
        avg_vector = []
    
    with open(output_file, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("Purpose Statistics\n")
        f.write("=" * 70 + "\n\n")
        
        f.write(f"Total Records: {len(purpose_history)}\n\n")
        
        f.write("Purpose Distribution:\n")
        f.write("-" * 70 + "\n")
        for purpose, count in distribution.most_common():
            percentage = (count / len(dominants)) * 100
            bar = "█" * int(percentage / 2)
            f.write(f"  {purpose:>15}: {count:>5} ({percentage:>5.1f}%) {bar}\n")
        
        f.write("\n")
        
        if len(avg_vector) >= 4:
            f.write("Average Purpose Vector (D1-D4):\n")
            f.write("-" * 70 + "\n")
            dim_names = ['Survival', 'Curiosity', 'Influence', 'Optimization']
            for i, name in enumerate(dim_names):
                if i < len(avg_vector):
                    value = avg_vector[i]
                    bar = "█" * int(value * 50)
                    f.write(f"  {name:>15}: {value:.3f} {bar}\n")
        
        f.write("\n" + "=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description='MOSS Purpose Evolution Visualizer')
    parser.add_argument('--input', '-i', required=True, help='Input actions.jsonl file')
    parser.add_argument('--output', '-o', default='reports', help='Output directory')
    args = parser.parse_args()
    
    input_file = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("🎨 MOSS Purpose Evolution Visualizer")
    print("=" * 70)
    
    # 加载数据
    print(f"\n📂 Loading data from {input_file}...")
    purpose_history = load_purpose_data(str(input_file))
    print(f"✅ Loaded {len(purpose_history)} purpose records")
    
    if not purpose_history:
        print("❌ No purpose data found")
        return
    
    # 生成可视化
    print("\n🎨 Generating visualizations...")
    
    # 1. ASCII时间线
    timeline_file = output_dir / "purpose_timeline.txt"
    generate_ascii_timeline(purpose_history, timeline_file)
    print(f"  📊 Timeline: {timeline_file}")
    
    # 2. 主导Purpose变化
    changes_file = output_dir / "purpose_changes.txt"
    generate_dominant_purpose_changes(purpose_history, changes_file)
    print(f"  📈 Changes: {changes_file}")
    
    # 3. 统计报告
    stats_file = output_dir / "purpose_statistics.txt"
    generate_purpose_statistics(purpose_history, stats_file)
    print(f"  📋 Statistics: {stats_file}")
    
    print("\n" + "=" * 70)
    print("✅ Visualization complete!")
    print(f"📁 Output directory: {output_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()
