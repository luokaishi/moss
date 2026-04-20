#!/usr/bin/env python3
"""
MOSS v8.0 - 1.5B Model Hybrid Experiment
=========================================

对比实验:
1. AST-only (基线) - 50代
2. Scheduled LLM (1.5B) - 50代
3. Aggressive Adaptive (1.5B) - 50代

使用 Qwen2.5-Coder-1.5B-Instruct 快速验证 Hybrid 策略
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


class ExperimentRunner:
    """实验运行器"""

    def __init__(self, name: str, config: SMEConfig, hybrid_config: HybridStrategyConfig = None):
        self.name = name
        self.config = config
        self.hybrid_config = hybrid_config
        self.sme = SelfModificationEngine(config=config, hybrid_config=hybrid_config)

    def run(self, generations: int = 50) -> dict:
        """运行实验"""
        print(f"\n{'='*70}")
        print(f"Experiment: {self.name}")
        print(f"{'='*70}")
        print(f"Generations: {generations}")
        print(f"LLM enabled: {self.config.enable_llm_mutation}")
        if self.config.enable_llm_mutation:
            print(f"Model: {self.config.llm_model}")
            if self.hybrid_config:
                print(f"Mode: {self.hybrid_config.mode}")

        start_time = time.time()

        report = self.sme.run(
            max_generations=generations,
            early_stop_fitness=0.90,
        )

        elapsed = time.time() - start_time

        # 统计
        mutation_types = {}
        llm_calls = 0
        for m in self.sme.mutation_history:
            t = m.mutation_type
            mutation_types[t] = mutation_types.get(t, 0) + 1
            if hasattr(m, 'source') and m.source == 'llm':
                llm_calls += 1

        result = {
            'name': self.name,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'config': {
                'enable_llm_mutation': self.config.enable_llm_mutation,
                'llm_provider': self.config.llm_provider,
                'llm_model': self.config.llm_model,
                'population_size': self.config.population_size,
            },
            'hybrid_config': {
                'mode': self.hybrid_config.mode,
                'schedule_pattern': self.hybrid_config.schedule_pattern if hasattr(self.hybrid_config, 'schedule_pattern') else None,
                'consecutive_no_op_threshold': self.hybrid_config.consecutive_no_op_threshold,
                'llm_budget_fraction': self.hybrid_config.llm_budget_fraction,
            } if self.hybrid_config else None,
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

        if self.sme._llm_backend:
            result['llm_stats'] = self.sme._llm_backend.get_usage_stats()
        if self.sme._hybrid_strategy:
            result['hybrid_stats'] = self.sme._hybrid_strategy.get_stats()

        return result


def print_comparison(results: list):
    """打印对比结果"""
    print("\n" + "="*80)
    print("1.5B MODEL HYBRID EXPERIMENT RESULTS")
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
        print(f"  Success rate:         {r['success_rate']*100:.1f}%")
        print(f"  Elapsed time:         {r['elapsed_seconds']/60:.1f} min")

        if r.get('llm_calls', 0) > 0:
            print(f"  LLM calls:            {r['llm_calls']}")

        if 'hybrid_stats' in r and r['hybrid_stats']:
            stats = r['hybrid_stats']
            print(f"\n  Hybrid strategy stats:")
            print(f"    Mode: {stats.get('mode', 'N/A')}")
            print(f"    Consecutive no-ops: {stats.get('consecutive_no_ops', 0)}")
            print(f"    Last LLM generation: {stats.get('last_llm_generation', 'N/A')}")


def main():
    print("="*80)
    print("MOSS v8.0 - 1.5B Model Hybrid Experiment")
    print("="*80)
    print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Hardware: 32-core CPU, 123GB RAM")
    print(f"Model: Qwen2.5-Coder-1.5B-Instruct (~3GB)")
    print(f"Expected duration: 30-60 minutes")
    print("="*80)

    results = []

    # 实验 1: AST-only (基线)
    print("\n[1/3] Running AST-only baseline...")
    config_ast = SMEConfig(
        enable_llm_mutation=False,
        population_size=6,
        max_generations=50,
        acceptance_threshold=-0.01,
        enable_hot_reload=False,
        output_dir="experiments/e5_ast_50gen",
    )
    exp_ast = ExperimentRunner("AST-only 50gen (Baseline)", config_ast)
    results.append(exp_ast.run(generations=50))

    # 实验 2: Scheduled LLM (每5代)
    print("\n[2/3] Running Scheduled LLM (1.5B)...")
    hybrid_config_scheduled = HybridStrategyConfig(
        mode="scheduled",
        schedule_pattern=["ast", "ast", "ast", "ast", "llm"],
        llm_budget_fraction=0.20,
        llm_cooldown_generations=0,
    )
    config_scheduled = SMEConfig(
        enable_llm_mutation=True,
        llm_provider='local',
        llm_model='qwen2.5-coder-1.5b',
        llm_mutation_strategy='adaptive',
        llm_budget_fraction=0.20,
        population_size=6,
        max_generations=50,
        acceptance_threshold=-0.01,
        enable_hot_reload=False,
        output_dir="experiments/e6_scheduled_1.5b",
    )
    exp_scheduled = ExperimentRunner(
        "Scheduled LLM 50gen (1.5B)",
        config_scheduled,
        hybrid_config_scheduled
    )
    results.append(exp_scheduled.run(generations=50))

    # 实验 3: Aggressive Adaptive
    print("\n[3/3] Running Aggressive Adaptive (1.5B)...")
    hybrid_config_aggressive = HybridStrategyConfig(
        mode="adaptive",
        consecutive_no_op_threshold=1,
        consecutive_reject_threshold=2,
        fitness_plateau_threshold=0.005,
        fitness_plateau_window=3,
        llm_budget_fraction=0.40,
        llm_cooldown_generations=1,
    )
    config_aggressive = SMEConfig(
        enable_llm_mutation=True,
        llm_provider='local',
        llm_model='qwen2.5-coder-1.5b',
        llm_mutation_strategy='adaptive',
        llm_budget_fraction=0.40,
        population_size=6,
        max_generations=50,
        acceptance_threshold=-0.01,
        enable_hot_reload=False,
        output_dir="experiments/e7_aggressive_1.5b",
    )
    exp_aggressive = ExperimentRunner(
        "Aggressive Adaptive 50gen (1.5B)",
        config_aggressive,
        hybrid_config_aggressive
    )
    results.append(exp_aggressive.run(generations=50))

    # 打印对比
    print_comparison(results)

    # 保存结果
    output_file = f"experiments/experiment_1.5b_hybrid_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n{'='*80}")
    print(f"✅ All experiments completed!")
    print(f"Results saved to: {output_file}")
    print(f"End time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
