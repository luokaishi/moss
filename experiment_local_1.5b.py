#!/usr/bin/env python3
"""
MOSS v8.0 - 本地 1.5B 模型进化实验
===================================

对比实验:
1. AST-only (基线)
2. Hybrid AST+LLM (1.5B 本地模型)

目标: 验证本地小模型是否能有效指导变异，减少 no_op 率
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

from moss.core.self_modification_engine import SelfModificationEngine, SMEConfig
import numpy as np


class ExperimentRunner:
    """实验运行器"""

    def __init__(self, name: str, config: SMEConfig):
        self.name = name
        self.config = config
        self.sme = SelfModificationEngine(config=config)

    def run(self, generations: int = 10) -> dict:
        """运行实验"""
        print(f"\n{'='*60}")
        print(f"Experiment: {self.name}")
        print(f"{'='*60}")
        print(f"Config: {self.config}")
        print(f"Generations: {generations}")

        start_time = time.time()

        # 运行进化
        report = self.sme.run(
            max_generations=generations,
            early_stop_fitness=0.95,  # 提前停止阈值
        )

        elapsed = time.time() - start_time

        # 统计结果
        result = {
            'name': self.name,
            'config': {
                'enable_llm_mutation': self.config.enable_llm_mutation,
                'llm_provider': self.config.llm_provider,
                'llm_model': self.config.llm_model,
                'llm_mutation_strategy': self.config.llm_mutation_strategy,
                'population_size': self.config.population_size,
            },
            'generations': report['total_generations'],
            'initial_fitness': report['initial_fitness'],
            'final_fitness': report['final_fitness'],
            'improvement': report['fitness_improvement'],
            'mutations_accepted': report.get('total_mutations_accepted', 0),
            'mutations_rejected': report.get('total_mutations_rejected', 0),
            'elapsed_seconds': elapsed,
            'fitness_per_generation': [
                m.fitness_after for m in self.sme.mutation_history
                if m.accepted
            ],
        }

        # 如果有 LLM，记录使用情况
        if self.sme._llm_backend:
            result['llm_stats'] = self.sme._llm_backend.get_usage_stats()

        return result


def print_results(results: list):
    """打印对比结果"""
    print("\n" + "="*80)
    print("EXPERIMENT RESULTS COMPARISON")
    print("="*80)

    for r in results:
        print(f"\n{r['name']}:")
        print(f"  Generations: {r['generations']}")
        print(f"  Initial fitness: {r['initial_fitness']:.4f}")
        print(f"  Final fitness: {r['final_fitness']:.4f}")
        print(f"  Improvement: {r['improvement']:+.4f}")
        print(f"  Accepted mutations: {r['mutations_accepted']}")
        print(f"  Rejected mutations: {r['mutations_rejected']}")
        print(f"  Success rate: {r['mutations_accepted']/(r['mutations_accepted']+r['mutations_rejected'])*100:.1f}%")
        print(f"  Elapsed time: {r['elapsed_seconds']:.1f}s")
        if 'llm_stats' in r:
            print(f"  LLM requests: {r['llm_stats'].get('total_requests', 0)}")


def main():
    print("="*80)
    print("MOSS v8.0 - Local 1.5B Model Experiment")
    print("="*80)
    print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Hardware: 32-core CPU, 123GB RAM")
    print(f"Model: Qwen2.5-Coder-1.5B-Instruct")

    results = []

    # 实验 1: AST-only (基线)
    config_ast = SMEConfig(
        enable_llm_mutation=False,
        population_size=4,
        max_generations=5,
        acceptance_threshold=-0.01,
        enable_hot_reload=False,
        output_dir="experiments/e1_ast_only",
    )
    exp_ast = ExperimentRunner("AST-only (Baseline)", config_ast)
    results.append(exp_ast.run(generations=5))

    # 实验 2: Hybrid with Local 1.5B
    config_hybrid = SMEConfig(
        enable_llm_mutation=True,
        llm_provider='local',
        llm_model='qwen2.5-coder-1.5b',
        llm_mutation_strategy='adaptive',
        llm_budget_fraction=0.3,
        population_size=4,
        max_generations=5,
        acceptance_threshold=-0.01,
        enable_hot_reload=False,
        output_dir="experiments/e2_hybrid_1.5b",
    )
    exp_hybrid = ExperimentRunner("Hybrid AST+LLM (1.5B local)", config_hybrid)
    results.append(exp_hybrid.run(generations=5))

    # 打印对比
    print_results(results)

    # 保存结果
    output_file = f"experiments/experiment_local_1.5b_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n✅ Results saved to: {output_file}")
    print(f"End time: {time.strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
