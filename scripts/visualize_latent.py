"""
Visualization Tool - 可视化工具

生成权重时序图、涌现检测图、聚类散点图等可视化。

使用:
    python scripts/visualize_latent.py --experiment-dir logs/experiment_v6_full_*
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
import numpy as np
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from agi.analysis.latent_export import LatentExporter
from agi.analysis.behavior_mapping import BehaviorMapper


def generate_text_visualization(checkpoint_dir: Path, output_dir: Path):
    """生成文本可视化报告"""
    
    # 加载检查点
    exporter = LatentExporter()
    n_loaded = exporter.load_checkpoints(checkpoint_dir)
    
    if n_loaded == 0:
        print(f"未找到检查点: {checkpoint_dir}")
        return
    
    # 使用内部权重矩阵和驱动名称
    weights_matrix = exporter.weights_matrix
    drive_names = exporter.drive_names
    
    report = []
    report.append("=" * 70)
    report.append("MOSS v6.0 可视化报告")
    report.append("=" * 70)
    report.append(f"生成时间: {datetime.now().isoformat()}")
    report.append(f"检查点数量: {n_loaded}")
    report.append(f"驱动数量: {len(drive_names)}")
    report.append("")
    
    # 1. 权重时序表
    report.append("-" * 70)
    report.append("1. 权重时序分布")
    report.append("-" * 70)
    report.append(f"{'Cycle':<10} {' | '.join([f'{n[:8]:<8}' for n in drive_names])}")
    report.append("-" * 70)
    
    for i, cp in enumerate(exporter.checkpoints):
        cycle = cp.get('cycle', i * 1000)
        weights = [cp.get('final_drives', {}).get(d, {}).get('weight', 0) for d in drive_names]
        weight_str = ' | '.join([f'{w:<8.4f}' for w in weights])
        report.append(f"{cycle:<10} {weight_str}")
    
    report.append("")
    
    # 2. 权重变化趋势
    report.append("-" * 70)
    report.append("2. 权重变化趋势")
    report.append("-" * 70)
    
    for drive_idx, drive_name in enumerate(drive_names):
        weights = weights_matrix[:, drive_idx]
        initial = weights[0]
        final = weights[-1]
        change = final - initial
        change_pct = (change / initial * 100) if initial != 0 else 0
        
        trend = "↑" if change > 0.01 else ("↓" if change < -0.01 else "→")
        report.append(f"{drive_name:<20} {initial:.4f} → {final:.4f} ({change:+.4f}, {change_pct:+.1f}%) {trend}")
    
    report.append("")
    
    # 3. 聚类分析
    report.append("-" * 70)
    report.append("3. 聚类分析 (K-Means, k=3)")
    report.append("-" * 70)
    
    cluster_result, cluster_info = exporter.cluster_kmeans(n_clusters=3)
    if cluster_result:
        for cluster in cluster_result:
            report.append(f"\nCluster {cluster.cluster_id}:")
            report.append(f"  样本数: {len(cluster.samples)}")
            report.append(f"  平均权重:")
            for drive, weight in cluster.avg_weights.items():
                report.append(f"    {drive}: {weight:.4f}")
    
    report.append("")
    
    # 4. PCA降维
    report.append("-" * 70)
    report.append("4. PCA 降维分析")
    report.append("-" * 70)
    
    pca_result = exporter.reduce_pca(n_components=2)
    if pca_result:
        report.append(f"主成分数: {pca_result.n_components}")
        report.append(f"解释方差比: {pca_result.explained_variance_ratio}")
        report.append(f"累积方差: {sum(pca_result.explained_variance_ratio):.4f}")
        report.append(f"降维后数据形状: {len(pca_result.transformed)} x {len(pca_result.transformed[0]) if pca_result.transformed else 0}")
    
    report.append("")
    report.append("=" * 70)
    
    # 保存报告
    output_path = output_dir / 'visualization_report.txt'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"可视化报告已保存: {output_path}")
    print('\n'.join(report))


def main():
    parser = argparse.ArgumentParser(description='MOSS v6.0 可视化工具')
    parser.add_argument('--experiment-dir', type=str, required=True,
                        help='实验目录路径')
    parser.add_argument('--output', '-o', type=str, default='logs/visualization',
                        help='输出目录')
    
    args = parser.parse_args()
    
    experiment_dir = Path(args.experiment_dir)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not experiment_dir.exists():
        print(f"错误: 实验目录不存在: {experiment_dir}")
        return
    
    generate_text_visualization(experiment_dir, output_dir)


if __name__ == '__main__':
    main()
