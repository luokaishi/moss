#!/usr/bin/env python3
"""
MOSS v8.0 - Coding Plan 实验 v4 (Optimized)
============================================

基于其他实例上的优化：
1. Scheduled模式修复（已在本仓库实现）
2. LLM预算提升到50%
3. 结合v8.1新特性：精英保留 + 动态阈值 + 多轮评估
"""

import os
import sys
sys.path.insert(0, '/workspace/moss')

os.environ['DASHSCOPE_API_KEY'] = 'sk-sp-6b9b0038cca142ea803eb02ee7aeb576'

import warnings
warnings.filterwarnings('ignore')
import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

import json
import time
from moss.core.self_modification_engine import SelfModificationEngine, SMEConfig
from moss.core.hybrid_mutation import HybridStrategyConfig


def run_coding_plan_experiment_v4(generations: int = 30) -> dict:
    """运行优化的 Coding Plan v4 实验"""
    print("="*70)
    print("Experiment: Coding Plan LLM 30gen v4 (Optimized)")
    print("="*70)
    print("Optimizations:")
    print("  1. Scheduled mode: forced LLM every 3rd gen (no cooldown)")
    print("  2. LLM budget: 50% (increased from 33%)")
    print("  3. Elite protection: v8.1 new feature")
    print("  4. Adaptive threshold: v8.1 new feature")
    print("  5. Multi-eval: v8.1 new feature (optional)")

    # 优化的Hybrid配置
    hybrid_config = HybridStrategyConfig(
        mode="scheduled",
        schedule_pattern=["ast", "ast", "llm"],  # 2 AST + 1 LLM
        llm_budget_fraction=0.50,  # 优化2: 从33%提升到50%
        llm_cooldown_generations=0,  # 优化1: 禁用冷却
    )

    # 优化的SME配置
    config = SMEConfig(
        enable_llm_mutation=True,
        llm_provider='bailian',
        llm_model='qwen3-coder-plus',
        llm_base_url='https://coding.dashscope.aliyuncs.com/v1',
        llm_max_tokens=4096,
        llm_mutation_strategy='adaptive',
        llm_budget_fraction=0.50,  # 50% LLM预算
        llm_daily_token_budget=500000,  # 关键修复：增加token预算（默认10万不够）
        llm_daily_request_budget=500,   # 增加请求预算
        population_size=6,
        max_generations=generations,
        acceptance_threshold=-0.01,
        enable_hot_reload=False,
        output_dir="experiments/e13_coding_plan_v4",
        # v8.1新特性
        enable_elitism=True,  # 启用精英保留
        elitism_threshold=0.95,
        enable_adaptive_threshold=True,  # 启用动态阈值
        adaptive_threshold_start=-0.01,
        adaptive_threshold_end=-0.005,
        enable_multi_eval=False,  # 多轮评估（可选，会显著增加时间）
        multi_eval_runs=3,
    )

    sme = SelfModificationEngine(config=config, hybrid_config=hybrid_config)

    print(f"\nConfiguration:")
    print(f"  Hybrid mode: {sme._hybrid_strategy.config.mode}")
    print(f"  Schedule: {sme._hybrid_strategy.config.schedule_pattern}")
    print(f"  LLM budget: {sme._hybrid_strategy.config.llm_budget_fraction:.0%}")
    print(f"  Elite protection: {config.enable_elitism}")
    print(f"  Adaptive threshold: {config.enable_adaptive_threshold}")
    print(f"  Multi-eval: {config.enable_multi_eval}")

    start_time = time.time()

    report = sme.run(
        max_generations=generations,
        early_stop_fitness=0.90,
    )

    elapsed = time.time() - start_time

    # 统计
    mutation_types = {}
    llm_calls = 0
    for m in sme.mutation_history:
        t = m.mutation_type
        mutation_types[t] = mutation_types.get(t, 0) + 1
        if hasattr(m, 'source') and m.source == 'llm':
            llm_calls += 1

    result = {
        'name': 'Coding Plan LLM 30gen v4 (Optimized)',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'config': {
            'llm_provider': 'bailian',
            'llm_model': 'qwen3-coder-plus',
            'llm_budget_fraction': 0.50,
            'schedule_pattern': ['ast', 'ast', 'llm'],
            'enable_elitism': config.enable_elitism,
            'enable_adaptive_threshold': config.enable_adaptive_threshold,
            'enable_multi_eval': config.enable_multi_eval,
        },
        'generations': report['total_generations'],
        'initial_fitness': report['initial_fitness'],
        'final_fitness': report['final_fitness'],
        'improvement': report['fitness_improvement'],
        'mutations_accepted': report.get('total_mutations_accepted', 0),
        'elapsed_seconds': elapsed,
        'fitness_per_generation': [
            m.fitness_after for m in sme.mutation_history if m.accepted
        ],
        'mutation_types': mutation_types,
        'llm_calls': llm_calls,
    }

    if sme._llm_backend:
        result['llm_stats'] = sme._llm_backend.get_usage_stats()
    if sme._hybrid_strategy:
        result['hybrid_stats'] = sme._hybrid_strategy.get_stats()

    return result


def main():
    print("="*70)
    print("MOSS v8.1 - Optimized Coding Plan Experiment v4")
    print("="*70)
    print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Expected duration: 40-50 minutes")
    print("="*70)

    result = run_coding_plan_experiment_v4(generations=30)

    # 保存结果
    output_file = f"experiments/experiment_coding_plan_v4_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2, default=str)

    print(f"\n{'='*70}")
    print(f"✅ Experiment v4 completed!")
    print(f"Results saved to: {output_file}")
    print(f"End time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")

    # 打印摘要
    print(f"\nSummary:")
    print(f"  Generations: {result['generations']}")
    print(f"  Fitness: {result['initial_fitness']:.4f} → {result['final_fitness']:.4f}")
    print(f"  Improvement: {result['improvement']:+.4f}")
    print(f"  Time: {result['elapsed_seconds']/60:.1f} min")
    print(f"  LLM calls: {result.get('llm_calls', 0)}")
    if 'llm_stats' in result:
        print(f"  API cost: ${result['llm_stats'].get('total_cost_usd', 0):.4f}")
    if 'hybrid_stats' in result:
        print(f"  Last LLM gen: {result['hybrid_stats'].get('last_llm_generation', 'N/A')}")


if __name__ == "__main__":
    main()
