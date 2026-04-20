#!/usr/bin/env python3
"""
MOSS v8.0 - 阿里云百炼 Coding Plan 实验 v2
============================================

改进版本：强制Scheduled模式，确保LLM在整个30代中持续参与
"""

import os
import sys
sys.path.insert(0, '/workspace/moss')

# 设置 Coding Plan API Key
os.environ['DASHSCOPE_API_KEY'] = 'sk-sp-6b9b0038cca142ea803eb02ee7aeb576'

import warnings
warnings.filterwarnings('ignore')
import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

import json
import time
from moss.core.self_modification_engine import SelfModificationEngine, SMEConfig
from moss.core.hybrid_mutation import HybridStrategyConfig


def run_coding_plan_experiment_v2(generations: int = 30) -> dict:
    """运行 Coding Plan 实验 v2（强制Scheduled模式）"""
    print("="*70)
    print("Experiment: Coding Plan LLM 30gen v2 (Forced Scheduled)")
    print("="*70)
    print(f"API: https://coding.dashscope.aliyuncs.com/v1")
    print(f"Model: qwen3-coder-plus (via Coding Plan)")
    print("Mode: Forced Scheduled (LLM every 3rd gen, no cooldown)")

    # Scheduled 模式：每3代强制调用LLM，忽略冷却
    hybrid_config = HybridStrategyConfig(
        mode="scheduled",
        schedule_pattern=["ast", "ast", "llm"],  # 2 AST + 1 LLM
        llm_budget_fraction=0.33,
        llm_cooldown_generations=0,  # v2: 禁用冷却，强制按pattern执行
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
        max_generations=generations,
        acceptance_threshold=-0.01,
        enable_hot_reload=False,
        output_dir="experiments/e10_coding_plan_v2",
    )

    sme = SelfModificationEngine(config=config, hybrid_config=hybrid_config)

    print(f"\nHybrid mode: {sme._hybrid_strategy.config.mode}")
    print(f"Schedule: {sme._hybrid_strategy.config.schedule_pattern}")
    print(f"Cooldown: {sme._hybrid_strategy.config.llm_cooldown_generations} (disabled for forced scheduled)")

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
        'name': 'Coding Plan LLM 30gen v2 (Forced Scheduled)',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'config': {
            'llm_provider': 'bailian',
            'llm_model': 'qwen3-coder-plus',
            'llm_base_url': 'https://coding.dashscope.aliyuncs.com/v1',
            'population_size': config.population_size,
            'schedule_pattern': ['ast', 'ast', 'llm'],
            'cooldown': 0,
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
    print("MOSS v8.0 - 阿里云百炼 Coding Plan 实验 v2")
    print("="*70)
    print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API Key: sk-sp-6...{os.environ['DASHSCOPE_API_KEY'][-6:]}")
    print(f"Expected duration: 15-25 minutes")
    print("="*70)

    result = run_coding_plan_experiment_v2(generations=30)

    # 保存结果
    output_file = f"experiments/experiment_coding_plan_v2_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2, default=str)

    print(f"\n{'='*70}")
    print(f"✅ Experiment v2 completed!")
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
