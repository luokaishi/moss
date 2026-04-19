#!/usr/bin/env python3
"""
MOSS v8.0 - 7B 模型 30 代进化实验
==================================

对比实验:
1. AST-only (基线) - 30代
2. Hybrid AST+LLM (7B 本地模型) - 30代

目标: 验证7B模型是否能显著提升变异质量和收敛速度
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

import numpy as np
from moss.core.self_modification_engine import SelfModificationEngine, SMEConfig


class ExperimentRunner:
    """实验运行器"""

    def __init__(self, name: str, config: SMEConfig):
        self.name = name
        self.config = config
        self.sme = SelfModificationEngine(config=config)

    def run(self, generations: int = 30) -> dict:
        """运行实验"""
        print(f"\n{'='*70}")
        print(f"Experiment: {self.name}")
        print(f"{'='*70}")
        print(f"Generations: {generations}")
        print(f"LLM enabled: {self.config.enable_llm_mutation}")
        if self.config.enable_llm_mutation:
            print(f"Model: {self.config.llm_model}")
            print(f"Strategy: {self.config.llm_mutation_strategy}")

        start_time = time.time()

        # 运行进化
        report = self.sme.run(
            max_generations=generations,
            early_stop_fitness=0.90,  # 提前停止阈值
        )

        elapsed = time.time() - start_time

        # 详细统计
        mutation_types = {}
        llm_calls = 0
        for m in self.sme.mutation_history:
            t = m.mutation_type
            mutation_types[t] = mutation_types.get(t, 0) + 1
            if 'llm' in t.lower():
                llm_calls += 1

        result = {
            'name': self.name,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'config': {
                'enable_llm_mutation': self.config.enable_llm_mutation,
                'llm_provider': self.config.llm_provider,
                'llm_model': self.config.llm_model,
                'llm_mutation_strategy': self.config.llm_mutation_strategy,
                'llm_budget_fraction': self.config.llm_budget_fraction,
                'population_size': self.config.population_size,
                'acceptance_threshold': self.config.acceptance_threshold,
            },
            'generations': report['total_generations'],
            'initial_fitness': report['initial_fitness'],
            'final_fitness': report['final_fitness'],
            'improvement': report['fitness_improvement'],
            'mutations_accepted': report.get('total_mutations_accepted', 0),
            'mutations_rejected': report.get('total_mutations_rejected', 0),
            'success_rate': report.get('total_mutations_accepted', 0) / max(1, 
                report.get('total_mutations_accepted', 0) + report.get('total_mutations_rejected', 0)),
            'elapsed_seconds': elapsed,
            'fitness_per_generation': [
                m.fitness_after for m in self.sme.mutation_history if m.accepted
            ],
            'mutation_types': mutation_types,
            'llm_calls': llm_calls,
        }

        # 如果有 LLM，记录详细使用统计
        if self.sme._llm_backend:
            result['llm_stats'] = self.sme._llm_backend.get_usage_stats()
            result['hybrid_stats'] = self.sme._hybrid_strategy.get_stats() if self.sme._hybrid_strategy else {}

        return result


def print_comparison(results: list):
    """打印对比结果"""
    print("\n" + "="*80)
    print("30-GENERATION EXPERIMENT RESULTS COMPARISON")
    print("="*80)

    for r in results:
        print(f"\n{'='*40}")
        print(f"{r['name']}")
        print(f"{'='*40}")
        print(f"  Generations:          {r['generations']}")
        print(f"  Initial fitness:      {r['initial_fitness']:.4f}")
        print(f"  Final fitness:        {r['final_fitness']:.4f}")
        print(f"  Improvement:          {r['improvement']:+.4f}")
        print(f"  Accepted mutations:   {r['mutations_accepted']}")
        print(f"  Rejected mutations:   {r['mutations_rejected']}")
        print(f"  Success rate:         {r['success_rate']*100:.1f}%")
        print(f"  Elapsed time:         {r['elapsed_seconds']/60:.1f} min")

        if r['llm_calls'] > 0:
            print(f"  LLM calls:            {r['llm_calls']}")
            llm_cost = r.get('llm_stats', {}).get('total_cost_usd', 0)
            print(f"  LLM cost:             ${llm_cost:.4f}")

        print(f"\n  Mutation type distribution:")
        for mtype, count in sorted(r['mutation_types'].items(), key=lambda x: -x[1]):
            print(f"    {mtype}: {count}")


def main():
    print("="*80)
    print("MOSS v8.0 - 7B Model 30-Generation Evolution Experiment")
    print("="*80)
    print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Hardware: 32-core CPU, 123GB RAM")
    print(f"Model: Qwen2.5-Coder-7B-Instruct")
    print(f"Expected duration: 30-60 minutes per experiment")

    results = []

    # 实验 1: AST-only (基线)
    config_ast = SMEConfig(
        enable_llm_mutation=False,
        population_size=6,
        max_generations=30,
        acceptance_threshold=-0.01,
        enable_hot_reload=False,
        output_dir="experiments/e1_ast_30gen",
    )
    exp_ast = ExperimentRunner("AST-only 30gen (Baseline)", config_ast)
    results.append(exp_ast.run(generations=30))

    # 实验 2: Hybrid with Local 7B
    config_hybrid = SMEConfig(
        enable_llm_mutation=True,
        llm_provider='local',
        llm_model='qwen2.5-coder-7b',
        llm_mutation_strategy='adaptive',
        llm_budget_fraction=0.3,
        llm_consecutive_no_op_threshold=3,
        population_size=6,
        max_generations=30,
        acceptance_threshold=-0.01,
        enable_hot_reload=False,
        output_dir="experiments/e2_hybrid_7b_30gen",
    )
    exp_hybrid = ExperimentRunner("Hybrid 7B 30gen", config_hybrid)
    results.append(exp_hybrid.run(generations=30))

    # 打印对比
    print_comparison(results)

    # 保存详细结果
    output_file = f"experiments/experiment_7b_30gen_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n{'='*80}")
    print(f"✅ All experiments completed!")
    print(f"Results saved to: {output_file}")
    print(f"End time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
