#!/usr/bin/env python3
"""
OEF 2.0 - 批量统计验证实验 (N=100) - 扩展验证
基于N=50成功实验，扩展到100次验证
"""

import sys
import json
import time
import random
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import warnings

sys.path.insert(0, str(Path(__file__).parent.parent))

warnings.filterwarnings('ignore')


def run_single_experiment(run_id: int, seed: int, output_dir: Path) -> Dict:
    """运行单次实验"""
    print(f"🧪 运行实验 #{run_id + 1}/100 (seed={seed})")
    
    # 设置随机种子
    random.seed(seed)
    np.random.seed(seed)
    
    # 导入并运行单次实验
    from experiments.oef_24h_validation import ValidationExperiment, ValidationExperimentConfig
    
    config = ValidationExperimentConfig(
        experiment_name=f"batch_run_{run_id}",
        duration_hours=1.67,  # 100分钟
        n_cycles=500,  # 500周期
        n_agents=10,
        initial_drives=['survival', 'curiosity', 'efficiency', 'social'],
        emergence_threshold=0.7,
        novelty_threshold=0.7,
        causal_threshold=0.6,
        output_dir=output_dir / f"run_{run_id}"
    )
    
    try:
        experiment = ValidationExperiment(config)
        experiment.run()
        
        # 从日志文件读取真实的涌现事件数
        log_file = output_dir / f"run_{run_id}" / "experiment.log"
        n_emergence = 0
        if log_file.exists():
            with open(log_file) as f:
                content = f.read()
                n_emergence = content.count("涌现事件 #")
        
        result = {
            'run_id': run_id,
            'seed': seed,
            'success': n_emergence >= 3,
            'n_emergence_events': n_emergence,
            'error': None
        }
        
        print(f"   ✅ 完成: {result['n_emergence_events']}个涌现事件")
        return result
        
    except Exception as e:
        print(f"   ❌ 失败: {str(e)}")
        return {
            'run_id': run_id,
            'seed': seed,
            'success': False,
            'n_emergence_events': 0,
            'error': str(e)
        }


def main():
    print("🚀 OEF 2.0 - 批量统计验证实验 (N=100, 500周期)")
    print("=" * 60)
    print("⚠️  预计时间: 40-60分钟")
    print("=" * 60)
    
    n_runs = 100
    output_dir = Path("oef_real_data/batch_validation_n100")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    seeds = [random.randint(1000, 999999) for _ in range(n_runs)]
    
    start_time = time.time()
    
    # 串行运行实验
    for i in range(n_runs):
        result = run_single_experiment(i, seeds[i], output_dir)
        results.append(result)
        
        # 每10次保存进度
        if (i + 1) % 10 == 0:
            progress = {
                'completed': i + 1,
                'total': n_runs,
                'success_so_far': sum(1 for r in results if r['success']),
                'elapsed_minutes': round((time.time() - start_time) / 60, 2)
            }
            with open(output_dir / 'progress.json', 'w') as f:
                json.dump(progress, f, indent=2)
            print(f"\n📊 进度: {i+1}/{n_runs} | 成功: {progress['success_so_far']} | 耗时: {progress['elapsed_minutes']}分钟\n")
    
    elapsed = time.time() - start_time
    
    # 生成报告
    n_success = sum(1 for r in results if r['success'])
    n_emergence_list = [r['n_emergence_events'] for r in results]
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'n_runs': n_runs,
        'success_rate': {
            'count': int(n_success),
            'total': n_runs,
            'percentage': round(float(n_success) / n_runs * 100, 2)
        },
        'emergence_events': {
            'mean': round(float(np.mean(n_emergence_list)), 3),
            'std': round(float(np.std(n_emergence_list)), 3),
            'median': int(np.median(n_emergence_list)),
            'min': int(np.min(n_emergence_list)),
            'max': int(np.max(n_emergence_list)),
            'ci_95': [round(float(np.percentile(n_emergence_list, 2.5)), 3), 
                     round(float(np.percentile(n_emergence_list, 97.5)), 3)]
        },
        'elapsed_time_seconds': round(elapsed, 2),
        'results': results
    }
    
    # 保存报告
    report_path = output_dir / 'batch_validation_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 打印报告
    print("\n" + "=" * 60)
    print("📊 批量验证实验统计报告 (N=100)")
    print("=" * 60)
    print(f"\n🎯 成功率: {report['success_rate']['percentage']}% ({n_success}/{n_runs})")
    print(f"\n📈 涌现事件: {report['emergence_events']['mean']:.2f} ± {report['emergence_events']['std']:.2f}")
    print(f"   中位数: {report['emergence_events']['median']}, 范围: [{report['emergence_events']['min']}, {report['emergence_events']['max']}]")
    print(f"   95%CI: [{report['emergence_events']['ci_95'][0]}, {report['emergence_events']['ci_95'][1]}]")
    print(f"\n⏱️  总耗时: {elapsed/60:.1f}分钟")
    print("=" * 60)
    
    if report['success_rate']['percentage'] >= 80:
        print("\n✅ 实验可重复性验证通过（成功率≥80%）！")
    elif report['success_rate']['percentage'] >= 50:
        print("\n⚠️  实验可重复性良好（成功率≥50%）")
    else:
        print("\n❌ 实验可重复性需要改进（成功率<50%）")
    
    print(f"\n💾 报告: {report_path}")


if __name__ == "__main__":
    main()
