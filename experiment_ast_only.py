#!/usr/bin/env python3
"""
MOSS v8.0 - 纯AST变异对照实验
==============================

纯AST变异30代实验，用于与LLM混合实验进行对比
"""

import os
import sys
sys.path.insert(0, '/workspace/moss')

import warnings
warnings.filterwarnings('ignore')
import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

import json
import time
from moss.core.self_modification_engine import SelfModificationEngine, SMEConfig
from moss.core.hybrid_mutation import HybridStrategyConfig


def run_ast_only_experiment(generations: int = 30) -> dict:
    """运行纯AST对照实验"""
    print("="*70)
    print("Experiment: AST-Only 30gen (Control Group)")
    print("="*70)
    print("Mode: Pure AST mutation (no LLM)")

    # AST-only 模式
    hybrid_config = HybridStrategyConfig(
        mode="ast_only",
        llm_budget_fraction=0.0,  # 禁用LLM
    )

    config = SMEConfig(
        enable_llm_mutation=False,  # 禁用LLM
        llm_provider='bailian',
        llm_model='qwen3-coder-plus',
        population_size=6,
        max_generations=generations,
        acceptance_threshold=-0.01,
        enable_hot_reload=False,
        output_dir="experiments/e9_ast_only",
    )

    sme = SelfModificationEngine(config=config, hybrid_config=hybrid_config)

    print(f"\nHybrid mode: {sme._hybrid_strategy.config.mode if sme._hybrid_strategy else 'ast_only (no hybrid)'}")

    start_time = time.time()

    report = sme.run(
        max_generations=generations,
        early_stop_fitness=0.90,
    )

    elapsed = time.time() - start_time

    # 统计
    mutation_types = {}
    for m in sme.mutation_history:
        t = m.mutation_type
        mutation_types[t] = mutation_types.get(t, 0) + 1

    result = {
        'name': 'AST-Only 30gen (Control)',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'config': {
            'mode': 'ast_only',
            'population_size': config.population_size,
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
    }

    if sme._hybrid_strategy:
        result['hybrid_stats'] = sme._hybrid_strategy.get_stats()

    return result


def main():
    print("="*70)
    print("MOSS v8.0 - 纯AST变异对照实验")
    print("="*70)
    print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Expected duration: 3-5 minutes (faster than LLM experiment)")
    print("="*70)

    result = run_ast_only_experiment(generations=30)

    # 保存结果
    output_file = f"experiments/experiment_ast_only_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2, default=str)

    print(f"\n{'='*70}")
    print(f"✅ Control experiment completed!")
    print(f"Results saved to: {output_file}")
    print(f"End time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")

    # 打印摘要
    print(f"\nSummary:")
    print(f"  Generations: {result['generations']}")
    print(f"  Fitness: {result['initial_fitness']:.4f} → {result['final_fitness']:.4f}")
    print(f"  Improvement: {result['improvement']:+.4f}")
    print(f"  Time: {result['elapsed_seconds']/60:.1f} min")
    print(f"  Mutation types: {result['mutation_types']}")


if __name__ == "__main__":
    main()
