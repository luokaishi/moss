#!/usr/bin/env python3
"""
MOSS Run 4.x Accelerated - Fast Purpose Evolution
=================================================

加速版Run 4.x: Purpose evolution 10x faster

目标: 验证 Purpose transitions 可以在较短时间（20万步）内发生

加速参数:
- purpose_interval: 100 → 10 steps (10x faster)
- 预期: 在 200k steps 内看到 S→C→I transitions

Usage:
    python3 experiments/run_4_x_accelerated.py --runs 10
"""

import sys
sys.path.insert(0, '/workspace/projects/moss')

import numpy as np
import json
import argparse
from pathlib import Path
from typing import Dict, List
from collections import defaultdict
from datetime import datetime

from moss.core import UnifiedMOSSAgent, MOSSConfig


def run_accelerated_experiment(run_id: int, initial_purpose: str) -> Dict:
    """
    运行加速版Run 4.x实验
    
    关键加速:
    - purpose_interval: 10 (vs 100 in original)
    - 预期transitions在200k步内发生
    """
    
    config = MOSSConfig(
        agent_id=f"accelerated_{run_id:03d}",
        enable_purpose=True,
        purpose_interval=10,  # 🔥 10x faster evolution
        log_dir=f"experiments/run_4_x_accelerated/run_{run_id:03d}"
    )
    
    agent = UnifiedMOSSAgent(config)
    
    # 设置初始Purpose
    weights_map = {
        'Survival': [0.70, 0.10, 0.10, 0.10],
        'Curiosity': [0.10, 0.70, 0.10, 0.10],
        'Balanced': [0.25, 0.25, 0.25, 0.25]
    }
    agent.weights = np.array(weights_map.get(initial_purpose, [0.25]*4))
    
    # 记录
    initial_p = initial_purpose
    purpose_sequence = [(0, initial_purpose)]
    transitions = []
    
    # 运行200k步（预期足够看到transitions）
    total_steps = 200000
    
    print(f"[Run {run_id:03d}] Starting with {initial_purpose} (accelerated 10x)")
    
    last_purpose = initial_purpose
    last_report_step = 0
    
    for step in range(total_steps):
        result = agent.step()
        
        # 检测Purpose变化
        if agent.purpose_generator:
            # 获取当前Purpose（从purpose statement或weights）
            current_weights = agent.weights[:4]
            dominant_idx = np.argmax(current_weights)
            purpose_names = ['Survival', 'Curiosity', 'Influence', 'Optimization']
            current_purpose = purpose_names[dominant_idx]
            
            # 记录transition
            if current_purpose != last_purpose:
                transitions.append({
                    'step': step,
                    'from': last_purpose,
                    'to': current_purpose,
                    'weights': current_weights.tolist()
                })
                purpose_sequence.append((step, current_purpose))
                print(f"  [Run {run_id:03d}] Step {step}: {last_purpose} → {current_purpose}")
                last_purpose = current_purpose
        
        # 进度报告（每50k步）
        if step - last_report_step >= 50000:
            progress = step / total_steps * 100
            print(f"  [Run {run_id:03d}] {progress:.0f}% - Current: {last_purpose}")
            last_report_step = step
    
    # 最终结果
    final_weights = agent.weights[:4]
    final_dominant = np.argmax(final_weights)
    purpose_names = ['Survival', 'Curiosity', 'Influence', 'Optimization']
    final_purpose = purpose_names[final_dominant]
    
    print(f"[Run {run_id:03d}] Complete: {initial_purpose} → {final_purpose}")
    print(f"  Transitions: {len(transitions)}")
    
    return {
        'run_id': run_id,
        'initial_purpose': initial_purpose,
        'final_purpose': final_purpose,
        'transitions': transitions,
        'transition_count': len(transitions),
        'purpose_sequence': purpose_sequence,
        'final_weights': final_weights.tolist()
    }


def main():
    parser = argparse.ArgumentParser(description='Run 4.x Accelerated (10x faster Purpose evolution)')
    parser.add_argument('--runs', type=int, default=10, help='Number of runs')
    parser.add_argument('--output', default='experiments/run_4_x_accelerated', help='Output directory')
    args = parser.parse_args()
    
    print("=" * 70)
    print("🔥 Run 4.x Accelerated - 10x Faster Purpose Evolution")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Runs: {args.runs}")
    print(f"  Steps per run: 200,000")
    print(f"  Purpose interval: 10 steps (10x faster than original)")
    print(f"  Expected: Purpose transitions in <200k steps")
    print("=" * 70)
    
    # 运行实验（混合初始Purpose）
    initial_purposes = ['Survival', 'Curiosity', 'Balanced']
    results = []
    
    for i in range(args.runs):
        purpose = initial_purposes[i % len(initial_purposes)]
        result = run_accelerated_experiment(i, purpose)
        results.append(result)
    
    # 分析结果
    print("\n" + "=" * 70)
    print("📊 Results Analysis")
    print("=" * 70)
    
    with_transitions = sum([r['transition_count'] > 0 for r in results])
    to_influence = sum([r['final_purpose'] == 'Influence' for r in results])
    
    print(f"\nTotal Runs: {len(results)}")
    print(f"With Purpose Transitions: {with_transitions}/{len(results)} ({with_transitions/len(results):.1%})")
    print(f"Final Purpose = Influence: {to_influence}/{len(results)} ({to_influence/len(results):.1%})")
    
    # 按初始Purpose分组
    by_initial = defaultdict(lambda: {'total': 0, 'with_transitions': 0, 'to_influence': 0})
    for r in results:
        initial = r['initial_purpose']
        by_initial[initial]['total'] += 1
        if r['transition_count'] > 0:
            by_initial[initial]['with_transitions'] += 1
        if r['final_purpose'] == 'Influence':
            by_initial[initial]['to_influence'] += 1
    
    print(f"\nBy Initial Purpose:")
    for purpose, stats in by_initial.items():
        trans_rate = stats['with_transitions'] / stats['total']
        infl_rate = stats['to_influence'] / stats['total']
        print(f"  {purpose:>10}: {stats['with_transitions']}/{stats['total']} transitions ({trans_rate:.1%}), {stats['to_influence']}/{stats['total']} → Influence ({infl_rate:.1%})")
    
    # 显示transition详情
    print(f"\nTransition Details:")
    for r in results:
        if r['transitions']:
            print(f"  Run {r['run_id']:03d} ({r['initial_purpose']}):")
            for t in r['transitions']:
                print(f"    Step {t['step']}: {t['from']} → {t['to']}")
    
    # 保存结果
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    with open(output_path / 'results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_path}")
    
    # 结论
    print("\n" + "=" * 70)
    if with_transitions > 0:
        print("🎉 SUCCESS: Purpose transitions observed with accelerated evolution!")
        print("   This proves time scale was the limiting factor.")
        print("=" * 70)
        return 0
    else:
        print("⚠️  No transitions observed even with 10x acceleration.")
        print("   May need even faster evolution or different mechanism.")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    exit(main())
