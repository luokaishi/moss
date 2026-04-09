#!/usr/bin/env python3
"""
MOSS Run 4.x Extended - Long Duration Version
=============================================

延长版Run 4.x: 100,000 steps (~1-2小时)

目标: 验证时间尺度是关键因素
预测: 更长运行时间将显示Purpose transitions

Usage:
    nohup python3 experiments/run_4_x_long.py --runs 20 --parallel 4 &
"""

import sys
sys.path.insert(0, '/workspace/projects/moss')

import numpy as np
import json
import argparse
import multiprocessing as mp
from pathlib import Path
from typing import Dict, List
from collections import defaultdict
from datetime import datetime

from moss.core import UnifiedMOSSAgent, MOSSConfig


class LongRunConfig:
    """长时运行配置"""
    def __init__(self, run_id: int, initial_purpose: str = "Survival", seed: int = None):
        self.run_id = run_id
        self.initial_purpose = initial_purpose
        self.seed = seed or (1000 + run_id)
        self.duration_steps = 100000  # 10万步
        self.log_interval = 5000


def run_single(config: LongRunConfig) -> Dict:
    """单次长时实验"""
    np.random.seed(config.seed)
    
    agent_config = MOSSConfig(
        agent_id=f"long_run_{config.run_id:03d}",
        enable_purpose=True,
        purpose_interval=100,  # 保持原有频率
        log_dir=f"experiments/run_4_x_long/run_{config.run_id:03d}"
    )
    
    agent = UnifiedMOSSAgent(agent_config)
    
    # 设置初始权重
    weights_map = {
        'Survival': [0.70, 0.10, 0.10, 0.10],
        'Curiosity': [0.10, 0.70, 0.10, 0.10],
        'Balanced': [0.25, 0.25, 0.25, 0.25]
    }
    agent.weights = np.array(weights_map.get(config.initial_purpose, [0.25]*4))
    
    # 记录
    purpose_changes = 0
    last_dominant = np.argmax(agent.weights[:4])
    
    print(f"[Run {config.run_id:03d}] Starting with {config.initial_purpose}...")
    
    for step in range(config.duration_steps):
        result = agent.step()
        
        # 检测Purpose变化
        current_dominant = np.argmax(agent.weights[:4])
        if current_dominant != last_dominant:
            purpose_changes += 1
            last_dominant = current_dominant
            print(f"  [Run {config.run_id:03d}] Step {step}: Purpose changed to {['Survival','Curiosity','Influence','Optimization'][current_dominant]}")
        
        # 进度报告
        if step % 20000 == 0 and step > 0:
            progress = step / config.duration_steps * 100
            current_purpose = ['Survival','Curiosity','Influence','Optimization'][current_dominant]
            print(f"  [Run {config.run_id:03d}] {progress:.0f}% - Current: {current_purpose}")
    
    # 最终结果
    final_dominant = np.argmax(agent.weights[:4])
    purpose_names = ['Survival', 'Curiosity', 'Influence', 'Optimization']
    
    print(f"[Run {config.run_id:03d}] Complete: {config.initial_purpose} → {purpose_names[final_dominant]} ({purpose_changes} changes)")
    
    return {
        'run_id': config.run_id,
        'initial_purpose': config.initial_purpose,
        'final_purpose': purpose_names[final_dominant],
        'purpose_changes': purpose_changes,
        'final_weights': agent.weights.tolist()
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runs', type=int, default=20)
    parser.add_argument('--parallel', type=int, default=4)
    parser.add_argument('--output', default='experiments/run_4_x_long')
    args = parser.parse_args()
    
    print("=" * 70)
    print("🔬 Run 4.x Extended - Long Duration (100k steps)")
    print("=" * 70)
    print(f"Configuration: {args.runs} runs, {args.parallel} parallel workers")
    print(f"Duration: 100,000 steps per run (~1-2 hours)")
    print("=" * 70)
    
    # 生成配置（混合初始Purpose）
    initial_purposes = ['Survival', 'Curiosity', 'Balanced']
    configs = []
    for i in range(args.runs):
        purpose = initial_purposes[i % len(initial_purposes)]
        configs.append(LongRunConfig(i, purpose))
    
    # 并行运行
    print(f"\n🚀 Starting {args.runs} long-duration experiments...")
    print("This will take 1-2 hours. Check progress with: tail -f experiments/run_4_x_long.log")
    
    with mp.Pool(args.parallel) as pool:
        results = pool.map(run_single, configs)
    
    # 分析
    to_influence = sum([r['final_purpose'] == 'Influence' for r in results])
    with_changes = sum([r['purpose_changes'] > 0 for r in results])
    
    print("\n" + "=" * 70)
    print("📊 Results Summary")
    print("=" * 70)
    print(f"Total Runs: {len(results)}")
    print(f"→ Influence: {to_influence}/{len(results)} ({to_influence/len(results):.1%})")
    print(f"With Purpose Changes: {with_changes}/{len(results)} ({with_changes/len(results):.1%})")
    
    # 按初始Purpose分组
    by_initial = defaultdict(lambda: {'total': 0, 'to_influence': 0})
    for r in results:
        by_initial[r['initial_purpose']]['total'] += 1
        if r['final_purpose'] == 'Influence':
            by_initial[r['initial_purpose']]['to_influence'] += 1
    
    print(f"\nBy Initial Purpose:")
    for purpose, stats in by_initial.items():
        print(f"  {purpose:>10}: {stats['to_influence']}/{stats['total']} ({stats['to_influence']/stats['total']:.1%})")
    
    # 保存
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    with open(output_path / 'results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_path}")
    
    if to_influence / len(results) > 0.5:
        print("\n🎉 SUCCESS: Influence attractor validated with long duration!")
        return 0
    else:
        print("\n⚠️  Influence convergence lower than expected")
        print("   Consider: Purpose evolution rate, environment structure")
        return 1


if __name__ == "__main__":
    exit(main())
