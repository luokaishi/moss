#!/usr/bin/env python3
"""
MOSS v8.0 - Coding Plan 5代快速实验
======================================
5代版本，确保在sandbox 5分钟超时前完成
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


def run_experiment():
    print("="*70)
    print("Experiment: Coding Plan 5gen (Fast - Completes in <5min)")
    print("="*70)

    hybrid_config = HybridStrategyConfig(
        mode="scheduled",
        schedule_pattern=["ast", "ast", "llm"],
        llm_budget_fraction=0.33,
        llm_cooldown_generations=0,
    )

    config = SMEConfig(
        enable_llm_mutation=True,
        llm_provider='bailian',
        llm_model='qwen3-coder-plus',
        llm_base_url='https://coding.dashscope.aliyuncs.com/v1',
        llm_max_tokens=4096,
        llm_mutation_strategy='adaptive',
        llm_budget_fraction=0.33,
        population_size=6,
        max_generations=5,
        acceptance_threshold=-0.01,
        enable_hot_reload=False,
        output_dir="experiments/e12_coding_plan_5gen",
    )

    sme = SelfModificationEngine(config=config, hybrid_config=hybrid_config)

    start_time = time.time()
    report = sme.run(max_generations=5, early_stop_fitness=0.90)
    elapsed = time.time() - start_time

    mutation_types = {}
    llm_calls = 0
    for m in sme.mutation_history:
        t = m.mutation_type
        mutation_types[t] = mutation_types.get(t, 0) + 1
        if hasattr(m, 'source') and m.source == 'llm':
            llm_calls += 1

    result = {
        'name': 'Coding Plan 5gen',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'generations': report['total_generations'],
        'initial_fitness': report['initial_fitness'],
        'final_fitness': report['final_fitness'],
        'improvement': report['fitness_improvement'],
        'mutations_accepted': report.get('total_mutations_accepted', 0),
        'elapsed_seconds': elapsed,
        'mutation_types': mutation_types,
    }

    if sme._llm_backend:
        result['llm_stats'] = sme._llm_backend.get_usage_stats()

    output_file = f"experiments/experiment_coding_plan_5gen_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2, default=str)

    print(f"\n{'='*70}")
    print(f"✅ 5-gen experiment completed!")
    print(f"Results: {output_file}")
    print(f"Fitness: {result['initial_fitness']:.4f} → {result['final_fitness']:.4f}")
    print(f"Time: {elapsed/60:.1f} min")
    print(f"{'='*70}")

    return result


if __name__ == "__main__":
    run_experiment()
