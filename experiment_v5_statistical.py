#!/usr/bin/env python3
"""
MOSS v8.1 - Statistical Validation Experiment (5x Repeats)
===========================================================

5 次独立重复实验 × 30 代，对比：
- Group A: AST-only (对照组)
- Group B: LLM Hybrid (实验组，v8.1 配置)

输出：统计报告（Welch's t-test + Cohen's d + Bootstrap 95% CI）

使用方法:
  python experiment_v5_statistical.py --group ast --trials 5
  python experiment_v5_statistical.py --group llm --trials 5
  python experiment_v5_statistical.py --analyze  # 分析已有结果

预计单次运行时间：
  - AST-only: ~3 min × 5 = 15 min
  - LLM Hybrid: ~45 min × 5 = 3.75 hr
"""

import argparse
import json
import os
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/workspace/moss')

os.environ.setdefault('DASHSCOPE_API_KEY', 'sk-sp-6b9b0038cca142ea803eb02ee7aeb576')

warnings.filterwarnings('ignore')

import numpy as np


# ─── 实验配置 ─────────────────────────────────────────────

RESULTS_DIR = Path('/workspace/moss/experiments/v5_statistical')
GENERATIONS = 30
POPULATION = 6


def make_ast_config(trial_id: int) -> dict:
    """创建 AST-only 对照组配置"""
    from moss.core.self_modification_engine import SMEConfig
    config = SMEConfig(
        enable_llm_mutation=False,
        population_size=POPULATION,
        max_generations=GENERATIONS,
        acceptance_threshold=-0.01,
        enable_hot_reload=False,
        output_dir=f"experiments/v5_statistical/ast_trial_{trial_id}",
    )
    return config


def make_llm_config(trial_id: int) -> tuple:
    """创建 LLM Hybrid 实验组配置"""
    from moss.core.self_modification_engine import SMEConfig
    from moss.core.hybrid_mutation import HybridStrategyConfig

    hybrid_config = HybridStrategyConfig(
        mode="scheduled",
        schedule_pattern=["ast", "ast", "llm"],
        llm_budget_fraction=0.50,
        llm_cooldown_generations=0,
    )

    config = SMEConfig(
        enable_llm_mutation=True,
        llm_provider='bailian',
        llm_model='qwen3-coder-plus',
        llm_base_url='https://coding.dashscope.aliyuncs.com/v1',
        llm_max_tokens=4096,
        llm_mutation_strategy='adaptive',
        llm_budget_fraction=0.50,
        llm_daily_token_budget=500000,
        llm_daily_request_budget=500,
        population_size=POPULATION,
        max_generations=GENERATIONS,
        acceptance_threshold=-0.01,
        enable_hot_reload=False,
        output_dir=f"experiments/v5_statistical/llm_trial_{trial_id}",
        # v8.1 features
        enable_elitism=True,
        elitism_threshold=0.95,
        enable_adaptive_threshold=True,
        adaptive_threshold_start=-0.01,
        adaptive_threshold_end=-0.005,
        enable_multi_eval=False,
    )
    return config, hybrid_config


def run_single_trial(group: str, trial_id: int) -> dict:
    """运行单次实验"""
    from moss.core.self_modification_engine import SelfModificationEngine

    print(f"\n{'='*60}")
    print(f"  Trial {trial_id} | Group: {group} | Start: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}")

    start_time = time.time()

    if group == 'ast':
        config = make_ast_config(trial_id)
        sme = SelfModificationEngine(config=config)
    else:
        config, hybrid_config = make_llm_config(trial_id)
        sme = SelfModificationEngine(config=config, hybrid_config=hybrid_config)

    report = sme.run(max_generations=GENERATIONS, early_stop_fitness=0.90)

    elapsed = time.time() - start_time

    # 提取变异类型
    mutation_types = {}
    llm_calls = 0
    for m in sme.mutation_history:
        t = m.mutation_type
        mutation_types[t] = mutation_types.get(t, 0) + 1
        if hasattr(m, 'source') and m.source == 'llm':
            llm_calls += 1

    result = {
        'group': group,
        'trial_id': trial_id,
        'timestamp': datetime.now().isoformat(),
        'generations': report['total_generations'],
        'initial_fitness': report['initial_fitness'],
        'final_fitness': report['final_fitness'],
        'improvement': report['fitness_improvement'],
        'mutations_accepted': report.get('total_mutations_accepted', 0),
        'elapsed_seconds': round(elapsed, 2),
        'fitness_per_generation': [
            m.fitness_after for m in sme.mutation_history if m.accepted
        ],
        'mutation_types': mutation_types,
        'llm_calls': llm_calls,
    }

    # 附加 LLM 统计
    if sme._llm_backend:
        result['llm_stats'] = sme._llm_backend.get_usage_stats()
    if sme._hybrid_strategy:
        result['hybrid_stats'] = sme._hybrid_strategy.get_stats()

    return result


def run_group(group: str, trials: int):
    """运行一组实验"""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    for i in range(1, trials + 1):
        result = run_single_trial(group, i)
        results.append(result)

        # 实时保存
        out_path = RESULTS_DIR / f"{group}_trial_{i}.json"
        with open(out_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"  → Saved to {out_path}")

    # 汇总
    summary_path = RESULTS_DIR / f"{group}_summary.json"
    summary = {
        'group': group,
        'trials': trials,
        'timestamp': datetime.now().isoformat(),
        'results': results,
        'statistics': compute_group_stats(results),
    }
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\n✅ Group {group} summary: {summary_path}")


def compute_group_stats(results: list) -> dict:
    """计算组内统计"""
    improvements = [r['improvement'] for r in results]
    peak_fitnesses = [max(r['fitness_per_generation']) if r['fitness_per_generation'] else r['final_fitness'] for r in results]
    final_fitnesses = [r['final_fitness'] for r in results]
    accepted = [r['mutations_accepted'] for r in results]

    return {
        'improvement_mean': float(np.mean(improvements)),
        'improvement_std': float(np.std(improvements, ddof=1)) if len(improvements) > 1 else 0.0,
        'peak_fitness_mean': float(np.mean(peak_fitnesses)),
        'peak_fitness_std': float(np.std(peak_fitnesses, ddof=1)) if len(peak_fitnesses) > 1 else 0.0,
        'final_fitness_mean': float(np.mean(final_fitnesses)),
        'final_fitness_std': float(np.std(final_fitnesses, ddof=1)) if len(final_fitnesses) > 1 else 0.0,
        'mutations_accepted_mean': float(np.mean(accepted)),
        'n_trials': len(results),
    }


def analyze_results():
    """统计对比分析（Welch's t-test + Cohen's d + Bootstrap CI）"""
    from scipy import stats

    ast_path = RESULTS_DIR / "ast_summary.json"
    llm_path = RESULTS_DIR / "llm_summary.json"

    if not ast_path.exists() or not llm_path.exists():
        print("❌ 需要先运行两组实验:")
        print("   python experiment_v5_statistical.py --group ast --trials 5")
        print("   python experiment_v5_statistical.py --group llm --trials 5")
        return

    with open(ast_path) as f:
        ast_data = json.load(f)
    with open(llm_path) as f:
        llm_data = json.load(f)

    ast_improvements = [r['improvement'] for r in ast_data['results']]
    llm_improvements = [r['improvement'] for r in llm_data['results']]

    ast_peaks = [max(r['fitness_per_generation']) if r['fitness_per_generation'] else r['final_fitness'] for r in ast_data['results']]
    llm_peaks = [max(r['fitness_per_generation']) if r['fitness_per_generation'] else r['final_fitness'] for r in llm_data['results']]

    # Welch's t-test
    t_stat, p_value = stats.ttest_ind(llm_improvements, ast_improvements, equal_var=False)

    # Cohen's d
    pooled_std = np.sqrt(
        (np.var(llm_improvements, ddof=1) + np.var(ast_improvements, ddof=1)) / 2
    )
    cohens_d = (np.mean(llm_improvements) - np.mean(ast_improvements)) / pooled_std if pooled_std > 0 else 0

    # Bootstrap 95% CI for difference of means
    n_bootstrap = 10000
    rng = np.random.RandomState(42)
    boot_diffs = []
    for _ in range(n_bootstrap):
        llm_sample = rng.choice(llm_improvements, size=len(llm_improvements), replace=True)
        ast_sample = rng.choice(ast_improvements, size=len(ast_improvements), replace=True)
        boot_diffs.append(np.mean(llm_sample) - np.mean(ast_sample))
    ci_lower, ci_upper = np.percentile(boot_diffs, [2.5, 97.5])

    # Report
    report = {
        'timestamp': datetime.now().isoformat(),
        'n_ast_trials': len(ast_improvements),
        'n_llm_trials': len(llm_improvements),
        'ast_improvement': {'mean': float(np.mean(ast_improvements)), 'std': float(np.std(ast_improvements, ddof=1))},
        'llm_improvement': {'mean': float(np.mean(llm_improvements)), 'std': float(np.std(llm_improvements, ddof=1))},
        'ast_peak_fitness': {'mean': float(np.mean(ast_peaks)), 'std': float(np.std(ast_peaks, ddof=1))},
        'llm_peak_fitness': {'mean': float(np.mean(llm_peaks)), 'std': float(np.std(llm_peaks, ddof=1))},
        'welch_t_test': {'t_statistic': float(t_stat), 'p_value': float(p_value)},
        'cohens_d': float(cohens_d),
        'bootstrap_95ci': {'lower': float(ci_lower), 'upper': float(ci_upper)},
        'significant_at_005': bool(p_value < 0.05),
        'effect_size': 'large' if abs(cohens_d) > 0.8 else ('medium' if abs(cohens_d) > 0.5 else 'small'),
    }

    # Print
    print("\n" + "="*70)
    print("  MOSS v8.1 Statistical Validation Report")
    print("="*70)
    print(f"\n  AST-only (n={len(ast_improvements)}):")
    print(f"    Improvement: {np.mean(ast_improvements):.6f} ± {np.std(ast_improvements, ddof=1):.6f}")
    print(f"    Peak fitness: {np.mean(ast_peaks):.6f} ± {np.std(ast_peaks, ddof=1):.6f}")
    print(f"\n  LLM Hybrid (n={len(llm_improvements)}):")
    print(f"    Improvement: {np.mean(llm_improvements):.6f} ± {np.std(llm_improvements, ddof=1):.6f}")
    print(f"    Peak fitness: {np.mean(llm_peaks):.6f} ± {np.std(llm_peaks, ddof=1):.6f}")
    print(f"\n  Statistical Tests:")
    print(f"    Welch's t-test: t={t_stat:.4f}, p={p_value:.4f}")
    print(f"    Cohen's d: {cohens_d:.4f} ({report['effect_size']})")
    print(f"    Bootstrap 95% CI for Δ: [{ci_lower:.6f}, {ci_upper:.6f}]")
    print(f"    Significant at α=0.05: {'Yes ✅' if p_value < 0.05 else 'No ❌'}")
    print("="*70)

    # Save
    report_path = RESULTS_DIR / "statistical_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\n  Report saved: {report_path}")

    return report


def main():
    parser = argparse.ArgumentParser(description="MOSS v8.1 Statistical Validation")
    parser.add_argument('--group', choices=['ast', 'llm'], help='Run experiment group')
    parser.add_argument('--trials', type=int, default=5, help='Number of trials per group')
    parser.add_argument('--analyze', action='store_true', help='Analyze existing results')
    args = parser.parse_args()

    if args.analyze:
        analyze_results()
    elif args.group:
        print(f"\n🔬 MOSS v8.1 Statistical Validation")
        print(f"   Group: {args.group}")
        print(f"   Trials: {args.trials}")
        print(f"   Generations: {GENERATIONS}")
        print(f"   Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        run_group(args.group, args.trials)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
