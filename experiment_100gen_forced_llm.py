#!/usr/bin/env python3
"""
MOSS v8.0 - 100代强制LLM实验
==============================

对比实验:
1. AST-only (基线) - 100代
2. Hybrid with Forced LLM - 100代（每5代强制调用LLM）
3. LLM-only - 100代（纯LLM变异）

目标: 验证LLM在长期进化中的实际作用
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
from moss.core.hybrid_mutation import HybridStrategyConfig


class ExperimentRunner:
    """实验运行器"""

    def __init__(self, name: str, config: SMEConfig, hybrid_config: HybridStrategyConfig = None):
        self.name = name
        self.config = config
        self.hybrid_config = hybrid_config
        self.sme = SelfModificationEngine(config=config, hybrid_config=hybrid_config)

    def run(self, generations: int = 100) -> dict:
        """运行实验"""
        print(f"\n{'='*70}")
        print(f"Experiment: {self.name}")
        print(f"{'='*70}")
        print(f"Generations: {generations}")
        print(f"LLM enabled: {self.config.enable_llm_mutation}")
        if self.config.enable_llm_mutation:
            print(f"Model: {self.config.llm_model}")
            print(f"Strategy: {self.config.llm_mutation_strategy}")
            if self.hybrid_config:
                print(f"Mode: {self.hybrid_config.mode}")
                print(f"No-op threshold: {self.hybrid_config.consecutive_no_op_threshold}")
                print(f"LLM budget: {self.hybrid_config.llm_budget_fraction:.0%}")

        start_time = time.time()

        # 运行进化
        report = self.sme.run(
            max_generations=generations,
            early_stop_fitness=0.95,  # 提高提前停止阈值
        )

        elapsed = time.time() - start_time

        # 详细统计
        mutation_types = {}
        llm_calls = 0
        ast_calls = 0
        for m in self.sme.mutation_history:
            t = m.mutation_type
            mutation_types[t] = mutation_types.get(t, 0) + 1
            if hasattr(m, 'source') and m.source == 'llm':
                llm_calls += 1
            elif hasattr(m, 'source') and m.source == 'ast':
                ast_calls += 1

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
            'hybrid_config': {
                'mode': self.hybrid_config.mode if self.hybrid_config else None,
                'consecutive_no_op_threshold': self.hybrid_config.consecutive_no_op_threshold if self.hybrid_config else None,
                'consecutive_reject_threshold': self.hybrid_config.consecutive_reject_threshold if self.hybrid_config else None,
                'fitness_plateau_threshold': self.hybrid_config.fitness_plateau_threshold if self.hybrid_config else None,
                'llm_budget_fraction': self.hybrid_config.llm_budget_fraction if self.hybrid_config else None,
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
            'ast_calls': ast_calls,
        }

        # 如果有 LLM，记录详细使用统计
        if self.sme._llm_backend:
            result['llm_stats'] = self.sme._llm_backend.get_usage_stats()
            result['hybrid_stats'] = self.sme._hybrid_strategy.get_stats() if self.sme._hybrid_strategy else {}

        return result


def print_comparison(results: list):
    """打印对比结果"""
    print("\n" + "="*80)
    print("100-GENERATION EXPERIMENT RESULTS COMPARISON")
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

        if r.get('llm_calls', 0) > 0:
            print(f"  LLM calls:            {r['llm_calls']}")
        if r.get('ast_calls', 0) > 0:
            print(f"  AST calls:            {r['ast_calls']}")

        if 'llm_stats' in r:
            llm_cost = r['llm_stats'].get('total_cost_usd', 0)
            print(f"  LLM cost:             ${llm_cost:.4f}")

        print(f"\n  Top mutation types:")
        for mtype, count in sorted(r['mutation_types'].items(), key=lambda x: -x[1])[:5]:
            print(f"    {mtype}: {count}")


def main():
    print("="*80)
    print("MOSS v8.0 - 100-Generation Forced LLM Experiment")
    print("="*80)
    print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Hardware: 32-core CPU, 123GB RAM")
    print(f"Model: Qwen2.5-Coder-7B-Instruct")
    print(f"Expected duration: 60-120 minutes")
    print("")
    print("This experiment forces LLM calls to measure actual impact.")
    print("="*80)

    results = []

    # 实验 1: AST-only (基线)
    print("\n[1/3] Running AST-only baseline...")
    config_ast = SMEConfig(
        enable_llm_mutation=False,
        population_size=6,
        max_generations=100,
        acceptance_threshold=-0.01,
        enable_hot_reload=False,
        output_dir="experiments/e3_ast_100gen",
    )
    exp_ast = ExperimentRunner("AST-only 100gen (Baseline)", config_ast)
    results.append(exp_ast.run(generations=100))

    # 实验 2: Scheduled LLM (每5代强制调用)
    print("\n[2/3] Running Scheduled LLM (every 5 gen)...")
    hybrid_config_scheduled = HybridStrategyConfig(
        mode="scheduled",
        schedule_pattern=["ast", "ast", "ast", "ast", "llm"],  # 4 AST + 1 LLM
        llm_budget_fraction=0.25,
        llm_cooldown_generations=0,  # 无冷却，强制调用
    )
    config_scheduled = SMEConfig(
        enable_llm_mutation=True,
        llm_provider='local',
        llm_model='qwen2.5-coder-7b',
        llm_mutation_strategy='adaptive',
        llm_budget_fraction=0.3,
        population_size=6,
        max_generations=100,
        acceptance_threshold=-0.01,
        enable_hot_reload=False,
        output_dir="experiments/e4_scheduled_100gen",
    )
    exp_scheduled = ExperimentRunner(
        "Scheduled LLM 100gen (4AST+1LLM)", 
        config_scheduled, 
        hybrid_config_scheduled
    )
    results.append(exp_scheduled.run(generations=100))

    # 实验 3: Aggressive Adaptive (降低阈值)
    print("\n[3/3] Running Aggressive Adaptive...")
    hybrid_config_aggressive = HybridStrategyConfig(
        mode="adaptive",
        consecutive_no_op_threshold=1,  # 1次no_op就触发LLM
        consecutive_reject_threshold=2,  # 2次拒绝就触发LLM
        fitness_plateau_threshold=0.01,  # 更低的平台阈值
        fitness_plateau_window=3,
        llm_budget_fraction=0.5,  # 50%预算给LLM
        llm_cooldown_generations=1,  # 最小冷却
    )
    config_aggressive = SMEConfig(
        enable_llm_mutation=True,
        llm_provider='local',
        llm_model='qwen2.5-coder-7b',
        llm_mutation_strategy='adaptive',
        llm_budget_fraction=0.5,
        population_size=6,
        max_generations=100,
        acceptance_threshold=-0.01,
        enable_hot_reload=False,
        output_dir="experiments/e5_aggressive_100gen",
    )
    exp_aggressive = ExperimentRunner(
        "Aggressive Adaptive 100gen", 
        config_aggressive,
        hybrid_config_aggressive
    )
    results.append(exp_aggressive.run(generations=100))

    # 打印对比
    print_comparison(results)

    # 保存详细结果
    output_file = f"experiments/experiment_100gen_forced_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n{'='*80}")
    print(f"✅ All experiments completed!")
    print(f"Results saved to: {output_file}")
    print(f"End time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
