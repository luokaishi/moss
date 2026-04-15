#!/usr/bin/env python3
"""
导出实验完整原始数据

用于复现和同行审查
"""

import sys
import json
import csv
import numpy as np
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '.')

print("="*70)
print("导出实验完整原始数据")
print("="*70)

# 加载5000周期实验结果
results_path = Path('experiments/7layer_v2_5000/results_5000cycles.json')
if not results_path.exists():
    print(f"错误: 找不到结果文件 {results_path}")
    print("请先运行 experiment_7layer_v2_5000.py")
    sys.exit(1)

print(f"加载数据: {results_path}")
with open(results_path) as f:
    results = json.load(f)

# 创建导出目录
export_dir = Path('experiments/reproducibility/exp_7layer_5000')
export_dir.mkdir(parents=True, exist_ok=True)

print(f"导出到: {export_dir}")

# 1. 导出配置
config = {
    'experiment_name': '7layer_v2_5000',
    'timestamp': results['timestamp'],
    'total_cycles': results['cycles'],
    'random_seed': 42,
    'state_dim': 16,
    'action_dim': 5,
    'concept_initial_dim': 4,
    'trajectory_length': 100,
    'goal_extraction_period': 500,
    'meta_drive_threshold': 0.05,
    'meta_drive_window': 200,
    'behavior_pattern_switch': 100,
}

with open(export_dir / 'config.json', 'w') as f:
    json.dump(config, f, indent=2)
print("✓ 导出 config.json")

# 2. 导出原始指标数据
metrics = results['metrics']
with open(export_dir / 'metrics.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['cycle', 'concept_error', 'concept_stability', 'concept_dim',
                     'self_model_accuracy', 'meta_triggered', 'num_goals', 
                     'goal_stability', 'revisit_bias'])
    
    for i in range(len(metrics['cycle'])):
        writer.writerow([
            metrics['cycle'][i],
            metrics['concept_error'][i],
            metrics['concept_stability'][i],
            metrics['concept_dim'][i],
            metrics['self_model_accuracy'][i],
            metrics['meta_triggered'][i],
            metrics['num_goals'][i],
            metrics['goal_stabilities'][i],
            metrics['revisit_bias'][i]
        ])
print("✓ 导出 metrics.csv")

# 3. 导出统计摘要
stats_summary = {
    'self_model': {
        'final_accuracy': results['self_model']['final_accuracy'],
        'accuracy_trend': results['self_model']['trend'],
        'mean_accuracy': np.mean(metrics['self_model_accuracy']),
        'std_accuracy': np.std(metrics['self_model_accuracy']),
        'min_accuracy': min(metrics['self_model_accuracy']),
        'max_accuracy': max(metrics['self_model_accuracy']),
        'ci_95': (
            np.percentile(metrics['self_model_accuracy'][-500:], 2.5),
            np.percentile(metrics['self_model_accuracy'][-500:], 97.5)
        )
    },
    'concept': {
        'final_error': results['concept']['final_error'],
        'final_stability': results['concept']['final_stability'],
        'error_reduction': (metrics['concept_error'][0] - metrics['concept_error'][-1]) / metrics['concept_error'][0],
        'mean_error': np.mean(metrics['concept_error']),
        'mean_stability': np.mean(metrics['concept_stability'])
    },
    'goal': {
        'max_goals': results['goal']['max_goals'],
        'final_goals': results['goal']['final_goals'],
        'avg_stability': results['goal']['avg_stability'],
        'emerged': results['goal']['emerged']
    },
    'meta_drive': {
        'total_triggers': results['meta_drive']['total_triggers'],
        'trigger_rate': results['meta_drive']['trigger_rate']
    }
}

with open(export_dir / 'statistics.json', 'w') as f:
    json.dump(stats_summary, f, indent=2, default=str)
print("✓ 导出 statistics.json")

# 4. 导出README
readme = f"""# 实验数据: 7层架构5000周期

## 实验信息
- **实验名称**: 7层AGI涌现架构5000周期测试
- **运行时间**: {results['timestamp']}
- **总周期**: {results['cycles']}
- **随机种子**: 42

## 关键结果

### Self-Model V2
- 最终准确率: {stats_summary['self_model']['final_accuracy']:.1%}
- 准确率趋势: {stats_summary['self_model']['accuracy_trend']:+.1%}
- 95%置信区间: [{stats_summary['self_model']['ci_95'][0]:.1%}, {stats_summary['self_model']['ci_95'][1]:.1%}]

### 概念系统
- 最终误差: {stats_summary['concept']['final_error']:.4f}
- 误差改进: {stats_summary['concept']['error_reduction']:.1%}
- 最终稳定性: {stats_summary['concept']['final_stability']:.4f}

### Goal系统
- 目标涌现: {'是' if stats_summary['goal']['emerged'] else '否'}
- 最大目标数: {stats_summary['goal']['max_goals']}
- 平均稳定性: {stats_summary['goal']['avg_stability']:.3f}

### Meta-Drive
- 总触发次数: {stats_summary['meta_drive']['total_triggers']}
- 触发频率: 每{stats_summary['meta_drive']['trigger_rate']:.0f}周期

## 文件说明
- `config.json`: 实验配置
- `metrics.csv`: 原始指标数据
- `statistics.json`: 统计摘要
- `README.md`: 本文件

## 复现步骤
```bash
python experiment_7layer_v2_5000.py
```

预期结果应与本实验一致（随机种子固定为42）。

## 引用
若使用本数据，请引用:
```
MOSS 7-Layer AGI Emergence Architecture
GitHub: https://github.com/luokaishi/moss
Experiment: exp_7layer_5000
```
"""

with open(export_dir / 'README.md', 'w') as f:
    f.write(readme)
print("✓ 导出 README.md")

# 5. 创建复现脚本
reproduce_script = """#!/bin/bash
# 复现脚本

echo "复现实验: 7层架构5000周期"
echo "=========================="

# 检查环境
python3 -c "import numpy; import yaml; print('✓ 依赖检查通过')"

# 运行实验
echo "运行实验..."
python3 experiment_7layer_v2_5000.py

echo "实验完成"
echo "结果保存在: experiments/7layer_v2_5000/"
"""

with open(export_dir / 'reproduce.sh', 'w') as f:
    f.write(reproduce_script)
(export_dir / 'reproduce.sh').chmod(0o755)
print("✓ 导出 reproduce.sh")

print("\n" + "="*70)
print("导出完成!")
print("="*70)
print(f"\n导出目录: {export_dir}")
print(f"文件列表:")
for f in export_dir.iterdir():
    print(f"  - {f.name}")
print("\n这些数据可用于:")
print("  1. 同行审查")
print("  2. 统计分析")
print("  3. 复现验证")
print("  4. 论文发表")
