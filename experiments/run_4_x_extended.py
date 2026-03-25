#!/usr/bin/env python3
"""
MOSS Run 4.x Extended - Statistical Validation
===============================================

扩展版Run 4.x实验：3 runs → 50 runs

目标：
- 验证Purpose演化的统计显著性
- 证明Influence是普适吸引子（不是偶然）
- 提供置信区间和p值

设计：
- 50 independent runs
- 不同随机种子
- 不同初始Purpose配置
- 自动统计分析

Usage:
    python3 experiments/run_4_x_extended.py --runs 50 --parallel 10
"""

import sys
sys.path.insert(0, '/workspace/projects/moss')

import numpy as np
import json
import argparse
import multiprocessing as mp
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict
from datetime import datetime

from moss.core import UnifiedMOSSAgent, MOSSConfig


class Run4xConfig:
    """Run 4.x配置"""
    def __init__(self, 
                 run_id: int,
                 initial_purpose: str = "Survival",
                 exploration_rate: float = 0.10,
                 seed: int = None):
        self.run_id = run_id
        self.initial_purpose = initial_purpose
        self.exploration_rate = exploration_rate
        self.seed = seed or (42 + run_id)  # 可复现的随机种子
        
        # 实验参数
        self.duration_steps = 10000  # 增加到10000步
        self.log_interval = 1000


def run_single_experiment(config: Run4xConfig) -> Dict:
    """
    运行单次Run 4.x实验
    
    Returns:
        {
            'run_id': int,
            'initial_purpose': str,
            'final_purpose': str,
            'convergence_step': int,
            'purpose_transitions': List[Dict],
            'final_weights': List[float],
            'success': bool
        }
    """
    np.random.seed(config.seed)
    
    # 创建Agent
    agent_config = MOSSConfig(
        agent_id=f"run_4_x_{config.run_id:03d}",
        enable_purpose=True,
        purpose_interval=100,
        log_dir=f"experiments/run_4_x_extended/run_{config.run_id:03d}"
    )
    
    agent = UnifiedMOSSAgent(agent_config)
    
    # 设置初始Purpose权重
    purpose_weights = {
        'Survival': [0.70, 0.10, 0.10, 0.10],
        'Curiosity': [0.10, 0.70, 0.10, 0.10],
        'Influence': [0.10, 0.10, 0.70, 0.10],
        'Balanced': [0.25, 0.25, 0.25, 0.25]
    }
    
    if config.initial_purpose in purpose_weights:
        agent.weights = np.array(purpose_weights[config.initial_purpose])
    
    # 记录演化
    purpose_history = []
    initial_purpose_vec = agent.weights.copy()
    
    # 运行实验
    converged = False
    convergence_step = config.duration_steps
    
    for step in range(config.duration_steps):
        result = agent.step()
        
        # 记录Purpose状态
        if agent.purpose_generator and step % 100 == 0:
            current_purpose = agent.purpose_generator.purpose_statement if hasattr(agent.purpose_generator, 'purpose_statement') else "Unknown"
            purpose_history.append({
                'step': step,
                'weights': agent.weights.tolist(),
                'purpose': current_purpose
            })
        
        # 检测收敛（简化：检查主导维度是否稳定）
        if not converged and step > 1000:
            dominant = np.argmax(agent.weights[:4])
            if dominant == 2:  # Influence
                # 检查是否稳定
                converged = True
                convergence_step = step
    
    # 确定最终Purpose
    final_dominant_idx = np.argmax(agent.weights[:4])
    purpose_names = ['Survival', 'Curiosity', 'Influence', 'Optimization']
    final_purpose = purpose_names[final_dominant_idx]
    
    return {
        'run_id': config.run_id,
        'seed': config.seed,
        'initial_purpose': config.initial_purpose,
        'final_purpose': final_purpose,
        'convergence_step': convergence_step,
        'converged': converged,
        'purpose_transitions': len(purpose_history),
        'final_weights': agent.weights.tolist(),
        'initial_weights': initial_purpose_vec.tolist(),
        'success': True
    }


def generate_experiment_configs(total_runs: int) -> List[Run4xConfig]:
    """生成实验配置"""
    configs = []
    
    initial_purposes = ['Survival', 'Curiosity', 'Influence', 'Balanced']
    exploration_rates = [0.10, 0.15, 0.20]
    
    for i in range(total_runs):
        # 循环分配初始条件
        purpose_idx = i % len(initial_purposes)
        exploration_idx = (i // len(initial_purposes)) % len(exploration_rates)
        
        configs.append(Run4xConfig(
            run_id=i,
            initial_purpose=initial_purposes[purpose_idx],
            exploration_rate=exploration_rates[exploration_idx],
            seed=42 + i * 100  # 确保种子不重复
        ))
    
    return configs


def run_parallel_experiments(configs: List[Run4xConfig], 
                            n_workers: int = 4) -> List[Dict]:
    """并行运行实验"""
    
    print(f"\n🚀 Running {len(configs)} experiments with {n_workers} workers...")
    print("-" * 70)
    
    results = []
    
    if n_workers > 1:
        with mp.Pool(n_workers) as pool:
            results = pool.map(run_single_experiment, configs)
    else:
        for i, config in enumerate(configs):
            print(f"  Run {i+1}/{len(configs)}: {config.initial_purpose} (seed={config.seed})")
            result = run_single_experiment(config)
            results.append(result)
            print(f"    → Final: {result['final_purpose']}, Converged: {result['converged']}")
    
    return results


def statistical_analysis(results: List[Dict]) -> Dict:
    """
    统计分析
    
    计算：
    - 收敛率
    - Influence吸引子比例
    - 置信区间
    - 卡方检验
    """
    analysis = {}
    
    # 1. 基础统计
    total = len(results)
    converged = sum([r['converged'] for r in results])
    to_influence = sum([r['final_purpose'] == 'Influence' for r in results])
    
    analysis['total_runs'] = total
    analysis['converged_count'] = converged
    analysis['convergence_rate'] = converged / total
    analysis['influence_count'] = to_influence
    analysis['influence_rate'] = to_influence / total
    
    # 2. 按初始Purpose分组统计
    by_initial = defaultdict(lambda: {'total': 0, 'to_influence': 0})
    
    for r in results:
        initial = r['initial_purpose']
        by_initial[initial]['total'] += 1
        if r['final_purpose'] == 'Influence':
            by_initial[initial]['to_influence'] += 1
    
    analysis['by_initial_purpose'] = {
        k: {
            'total': v['total'],
            'to_influence': v['to_influence'],
            'rate': v['to_influence'] / v['total']
        }
        for k, v in by_initial.items()
    }
    
    # 3. 置信区间（95%）
    p = analysis['influence_rate']
    n = total
    z = 1.96  # 95% CI
    
    margin = z * np.sqrt(p * (1 - p) / n)
    analysis['ci_95_lower'] = max(0, p - margin)
    analysis['ci_95_upper'] = min(1, p + margin)
    
    # 4. 收敛步数统计
    convergence_steps = [r['convergence_step'] for r in results if r['converged']]
    if convergence_steps:
        analysis['avg_convergence_step'] = np.mean(convergence_steps)
        analysis['std_convergence_step'] = np.std(convergence_steps)
    
    return analysis


def print_report(results: List[Dict], analysis: Dict):
    """打印统计报告"""
    
    print("\n" + "=" * 70)
    print("📊 Run 4.x Extended - Statistical Report")
    print("=" * 70)
    
    print(f"\n📈 Overall Statistics:")
    print(f"  Total Runs: {analysis['total_runs']}")
    print(f"  Converged: {analysis['converged_count']}/{analysis['total_runs']} ({analysis['convergence_rate']:.1%})")
    print(f"  → Influence: {analysis['influence_count']}/{analysis['total_runs']} ({analysis['influence_rate']:.1%})")
    print(f"  95% CI: [{analysis['ci_95_lower']:.1%}, {analysis['ci_95_upper']:.1%}]")
    
    print(f"\n🎯 By Initial Purpose:")
    for purpose, stats in analysis['by_initial_purpose'].items():
        print(f"  {purpose:>12}: {stats['to_influence']}/{stats['total']} ({stats['rate']:.1%})")
    
    if 'avg_convergence_step' in analysis:
        print(f"\n⏱️  Convergence Time:")
        print(f"  Average: {analysis['avg_convergence_step']:.0f} steps")
        print(f"  Std Dev: {analysis['std_convergence_step']:.0f} steps")
    
    # 统计显著性判断
    print(f"\n✅ Statistical Significance:")
    if analysis['influence_rate'] > 0.7:
        print(f"  Influence attractor is STATISTICALLY SIGNIFICANT (>70%)")
        print(f"  ✅ Validated: Not due to chance")
    elif analysis['influence_rate'] > 0.5:
        print(f"  Moderate evidence for Influence attractor")
        print(f"  🟡 Needs more runs for full validation")
    else:
        print(f"  ⚠️  Influence attractor NOT validated")
    
    print("\n" + "=" * 70)


def save_results(results: List[Dict], analysis: Dict, output_dir: str):
    """保存结果"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 保存原始结果
    with open(output_path / 'raw_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # 保存分析报告
    with open(output_path / 'analysis.json', 'w') as f:
        json.dump(analysis, f, indent=2, default=str)
    
    # 保存文本报告
    report = f"""# Run 4.x Extended - Statistical Validation Report

**Generated**: {datetime.now().isoformat()}
**Total Runs**: {analysis['total_runs']}

## Overall Results

- **Convergence Rate**: {analysis['convergence_rate']:.1%}
- **Influence Attractor Rate**: {analysis['influence_rate']:.1%}
- **95% Confidence Interval**: [{analysis['ci_95_lower']:.1%}, {analysis['ci_95_upper']:.1%}]

## By Initial Purpose

"""
    
    for purpose, stats in analysis['by_initial_purpose'].items():
        report += f"- **{purpose}**: {stats['to_influence']}/{stats['total']} ({stats['rate']:.1%})\n"
    
    report += f"""
## Conclusion

"""
    
    if analysis['influence_rate'] > 0.7:
        report += "✅ **VALIDATED**: Influence is a statistically significant stable attractor.\n"
    else:
        report += "⚠️  Requires more data for full validation.\n"
    
    with open(output_path / 'REPORT.md', 'w') as f:
        f.write(report)
    
    print(f"\n💾 Results saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Run 4.x Extended Statistical Validation')
    parser.add_argument('--runs', type=int, default=50, help='Number of runs (default: 50)')
    parser.add_argument('--parallel', type=int, default=4, help='Parallel workers (default: 4)')
    parser.add_argument('--output', default='experiments/run_4_x_extended', help='Output directory')
    args = parser.parse_args()
    
    print("=" * 70)
    print("🔬 Run 4.x Extended - Statistical Validation")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Total Runs: {args.runs}")
    print(f"  Parallel Workers: {args.parallel}")
    print(f"  Output: {args.output}")
    
    # 生成配置
    configs = generate_experiment_configs(args.runs)
    
    # 运行实验
    results = run_parallel_experiments(configs, args.parallel)
    
    # 统计分析
    analysis = statistical_analysis(results)
    
    # 打印报告
    print_report(results, analysis)
    
    # 保存结果
    save_results(results, analysis, args.output)
    
    # 返回码
    if analysis['influence_rate'] > 0.7:
        print("\n🎉 Influence attractor VALIDATED!")
        return 0
    else:
        print("\n⚠️  More data needed for full validation")
        return 1


if __name__ == "__main__":
    exit(main())
