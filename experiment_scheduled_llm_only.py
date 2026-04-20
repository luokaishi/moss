#!/usr/bin/env python3
"""
MOSS v8.0 - Scheduled LLM 实验（简化版）
=========================================

只运行 Scheduled LLM 实验，跳过已完成的 AST-only
"""

import os
import sys
import json
import time
from pathlib import Path

sys.path.insert(0, '/workspace/moss')
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

import warnings
warnings.filterwarnings('ignore')

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

import numpy as np
from moss.core.self_modification_engine import SelfModificationEngine, SMEConfig
from moss.core.hybrid_mutation import HybridStrategyConfig


def run_scheduled_experiment(generations: int = 100) -> dict:
    """运行 Scheduled LLM 实验"""
    print("="*70)
    print("Experiment: Scheduled LLM 100gen (4AST+1LLM)")
    print("="*70)

    hybrid_config = HybridStrategyConfig(
        mode="scheduled",
        schedule_pattern=["ast", "ast", "ast", "ast", "llm"],  # 4 AST + 1 LLM
        llm_budget_fraction=0.25,
        llm_cooldown_generations=0,
    )

    config = SMEConfig(
        enable_llm_mutation=True,
        llm_provider='local',
        llm_model='qwen2.5-coder-7b',
        llm_mutation_strategy='adaptive',
        llm_budget_fraction=0.25,
        population_size=6,
        max_generations=generations,
        acceptance_threshold=-0.01,
        enable_hot_reload=False,
        output_dir="experiments/e4_scheduled_100gen",
    )

    sme = SelfModificationEngine(config=config, hybrid_config=hybrid_config)

    print(f"\nHybrid mode: {sme._hybrid_strategy.config.mode}")
    print(f"Schedule: {sme._hybrid_strategy.config.schedule_pattern}")
    print(f"LLM budget: {sme._hybrid_strategy.config.llm_budget_fraction:.0%}")

    start_time = time.time()

    report = sme.run(
        max_generations=generations,
        early_stop_fitness=0.95,
    )

    elapsed = time.time() - start_time

    # 统计
    mutation_types = {}
    llm_calls = 0
    for m in sme.mutation_history:
        t = m.mutation_type
        mutation_types[t] = mutation_types.get(t, 0) + 1

    result = {
        'name': 'Scheduled LLM 100gen (4AST+1LLM)',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'config': {
            'enable_llm_mutation': config.enable_llm_mutation,
            'llm_provider': config.llm_provider,
            'llm_model': config.llm_model,
            'llm_budget_fraction': config.llm_budget_fraction,
            'population_size': config.population_size,
        },
        'hybrid_config': {
            'mode': hybrid_config.mode,
            'schedule_pattern': hybrid_config.schedule_pattern,
            'llm_budget_fraction': hybrid_config.llm_budget_fraction,
        },
        'generations': report['total_generations'],
        'initial_fitness': report['initial_fitness'],
        'final_fitness': report['final_fitness'],
        'improvement': report['fitness_improvement'],
        'mutations_accepted': report.get('total_mutations_accepted', 0),
        'mutations_rejected': report.get('total_mutations_rejected', 0),
        'elapsed_seconds': elapsed,
        'fitness_per_generation': [
            m.fitness_after for m in sme.mutation_history if m.accepted
        ],
        'mutation_types': mutation_types,
    }

    if sme._llm_backend:
        result['llm_stats'] = sme._llm_backend.get_usage_stats()
    if sme._hybrid_strategy:
        result['hybrid_stats'] = sme._hybrid_strategy.get_stats()

    return result


def main():
    print("="*70)
    print("MOSS v8.0 - Scheduled LLM Experiment (Simplified)")
    print("="*70)
    print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Hardware: 32-core CPU, 123GB RAM")
    print(f"Model: Qwen2.5-Coder-7B-Instruct")
    print(f"Expected duration: 60-180 minutes (due to 7B model loading)")
    print("="*70)

    result = run_scheduled_experiment(generations=100)

    # 保存结果
    output_file = f"experiments/experiment_scheduled_llm_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2, default=str)

    print(f"\n{'='*70}")
    print(f"✅ Experiment completed!")
    print(f"Results saved to: {output_file}")
    print(f"End time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")

    # 打印摘要
    print(f"\nSummary:")
    print(f"  Generations: {result['generations']}")
    print(f"  Fitness: {result['initial_fitness']:.4f} → {result['final_fitness']:.4f}")
    print(f"  Improvement: {result['improvement']:+.4f}")
    print(f"  Time: {result['elapsed_seconds']/60:.1f} min")
    if 'hybrid_stats' in result:
        print(f"  Hybrid stats: {result['hybrid_stats']}")


if __name__ == "__main__":
    main()
