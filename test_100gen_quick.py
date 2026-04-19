#!/usr/bin/env python3
"""快速测试 100 代实验的前几代"""

import os
import sys
sys.path.insert(0, '/workspace/moss')
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

import warnings
warnings.filterwarnings('ignore')

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

from moss.core.self_modification_engine import SelfModificationEngine, SMEConfig
from moss.core.hybrid_mutation import HybridStrategyConfig

print("="*70)
print("Quick Test: 100gen experiment (first 5 generations)")
print("="*70)

# 测试 Scheduled 模式
print("\n[TEST] Scheduled LLM mode...")
hybrid_config = HybridStrategyConfig(
    mode="scheduled",
    schedule_pattern=["ast", "llm"],  # 简化为 1 AST + 1 LLM
    llm_budget_fraction=0.5,
    llm_cooldown_generations=0,
)

config = SMEConfig(
    enable_llm_mutation=True,
    llm_provider='local',
    llm_model='qwen2.5-coder-7b',
    llm_mutation_strategy='adaptive',
    llm_budget_fraction=0.5,
    population_size=4,
    max_generations=5,  # 只跑5代
    acceptance_threshold=-0.01,
    enable_hot_reload=False,
    output_dir="experiments/test_scheduled",
)

sme = SelfModificationEngine(config=config, hybrid_config=hybrid_config)
print(f"✓ SME initialized")
print(f"  Hybrid mode: {sme._hybrid_strategy.config.mode}")
print(f"  Schedule: {sme._hybrid_strategy.config.schedule_pattern}")

# 运行5代
report = sme.run(max_generations=5)

print(f"\n✓ Test completed!")
print(f"  Generations: {report['total_generations']}")
print(f"  Fitness: {report['initial_fitness']:.4f} → {report['final_fitness']:.4f}")
print(f"  Hybrid stats: {sme._hybrid_strategy.get_stats()}")
