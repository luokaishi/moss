#!/usr/bin/env python3
"""
MOSS v8.0 - 阿里云百炼 Coding Plan 实验
========================================

使用阿里云百炼 Coding Plan API 进行 LLM 引导变异实验
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


def run_coding_plan_experiment(generations: int = 30) -> dict:
    """运行 Coding Plan 实验"""
    print("="*70)
    print("Experiment: Coding Plan LLM 30gen")
    print("="*70)
    print(f"API: https://coding.dashscope.aliyuncs.com/v1")
    print(f"Model: qwen-coder-plus (via Coding Plan)")

    # Scheduled 模式：每 3 代调用一次 LLM
    hybrid_config = HybridStrategyConfig(
        mode="scheduled",
        schedule_pattern=["ast", "ast", "llm"],  # 2 AST + 1 LLM
        llm_budget_fraction=0.33,
        llm_cooldown_generations=0,
    )

    config = SMEConfig(
        enable_llm_mutation=True,
        llm_provider='bailian',  # 使用百炼后端
        llm_model='qwen3-coder-plus',  # Coding Plan 模型名
        llm_base_url='https://coding.dashscope.aliyuncs.com/v1',  # Coding Plan endpoint
        llm_max_tokens=4096,  # 增加 token 限制以输出完整文件
        llm_mutation_strategy='adaptive',
        llm_budget_fraction=0.33,
        population_size=6,
        max_generations=generations,
        acceptance_threshold=-0.01,
        enable_hot_reload=False,
        output_dir="experiments/e8_coding_plan",
    )

    sme = SelfModificationEngine(config=config, hybrid_config=hybrid_config)

    print(f"\nHybrid mode: {sme._hybrid_strategy.config.mode}")
    print(f"Schedule: {sme._hybrid_strategy.config.schedule_pattern}")

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
        'name': 'Coding Plan LLM 30gen',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'config': {
            'llm_provider': 'bailian',
            'llm_model': 'qwen-coder-plus',
            'llm_base_url': 'https://coding.dashscope.aliyuncs.com/v1',
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
        'llm_calls': llm_calls,
    }

    if sme._llm_backend:
        result['llm_stats'] = sme._llm_backend.get_usage_stats()
    if sme._hybrid_strategy:
        result['hybrid_stats'] = sme._hybrid_strategy.get_stats()

    return result


def main():
    print("="*70)
    print("MOSS v8.0 - 阿里云百炼 Coding Plan 实验")
    print("="*70)
    print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API Key: sk-sp-6...{os.environ['DASHSCOPE_API_KEY'][-6:]}")
    print(f"Expected duration: 10-20 minutes")
    print("="*70)

    result = run_coding_plan_experiment(generations=30)

    # 保存结果
    output_file = f"experiments/experiment_coding_plan_{time.strftime('%Y%m%d_%H%M%S')}.json"
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
    print(f"  LLM calls: {result.get('llm_calls', 0)}")
    if 'hybrid_stats' in result:
        print(f"  Hybrid stats: {result['hybrid_stats']}")


if __name__ == "__main__":
    main()
