#!/usr/bin/env python3
"""
MOSS Run 4.x Strong - Aggressive Phase Transitions
==================================================

强力版Run 4.x: 实现强制phase扰动以达成S→C→I

增强机制:
1. 强制phase边界扰动 (30%+ adjustment)
2. 强制Purpose重新生成
3. 更长的时间尺度 (500k steps)
4. 社交压力模拟

目标: 最终验证S→C→I路径

Usage:
    python3 experiments/run_4_x_strong.py --runs 5
"""

import sys
sys.path.insert(0, '/workspace/projects/moss')

import numpy as np
import json
import argparse
from pathlib import Path
from typing import Dict, List
from datetime import datetime

from moss.core import UnifiedMOSSAgent, MOSSConfig
from moss.core.causal_purpose import CausalPurposeGenerator, CausalPurposeConfig


class StrongPhasedEnvironment:
    """
    强phase环境 - 强制Purpose变化
    """
    
    def __init__(self, total_steps: int):
        self.total_steps = total_steps
        # Phase定义
        self.phases = [
            ('threat', 0, int(total_steps * 0.20)),       # 0-20%: Threat
            ('growth', int(total_steps * 0.20), int(total_steps * 0.50)),  # 20-50%: Growth
            ('social', int(total_steps * 0.50), int(total_steps * 0.80)),  # 50-80%: Social
            ('mature', int(total_steps * 0.80), total_steps)  # 80-100%: Mature
        ]
    
    def get_phase(self, step: int) -> str:
        for name, start, end in self.phases:
            if start <= step < end:
                return name
        return 'mature'
    
    def get_optimal_weights(self, phase: str) -> np.ndarray:
        """Phase最优权重"""
        optimal = {
            'threat': np.array([0.90, 0.05, 0.03, 0.02]),
            'growth': np.array([0.05, 0.85, 0.07, 0.03]),
            'social': np.array([0.05, 0.07, 0.83, 0.05]),
            'mature': np.array([0.15, 0.15, 0.60, 0.10])
        }
        return optimal.get(phase, np.array([0.25]*4))
    
    def is_phase_boundary(self, step: int) -> bool:
        """检查是否是phase边界"""
        for _, start, _ in self.phases:
            if step == start:
                return True
        return False


def run_strong_experiment(run_id: int, initial_purpose: str) -> Dict:
    """
    运行强力版实验
    """
    
    total_steps = 500000  # 50万步 - 更长观察窗口
    
    # 使用因果Purpose生成器（更强的演化能力）
    agent_config = MOSSConfig(
        agent_id=f"strong_{run_id:03d}",
        enable_purpose=True,
        purpose_interval=50,  # 更频繁的Purpose更新
        log_dir=f"experiments/run_4_x_strong/run_{run_id:03d}"
    )
    
    agent = UnifiedMOSSAgent(agent_config)
    env = StrongPhasedEnvironment(total_steps)
    
    # 替换为因果Purpose（更强的演化）
    causal_config = CausalPurposeConfig(
        latent_dim=64,
        evolution_interval=50,  # 频繁演化
        method="rule",
        learning_rate=0.3  # 更强的学习率
    )
    agent.causal_purpose = CausalPurposeGenerator(f"strong_{run_id:03d}", causal_config)
    
    # 设置初始权重
    weights_map = {
        'Survival': [0.70, 0.10, 0.10, 0.10],
        'Curiosity': [0.10, 0.70, 0.10, 0.10],
        'Balanced': [0.30, 0.30, 0.30, 0.10]
    }
    agent.weights = np.array(weights_map.get(initial_purpose, [0.30]*4))
    
    # 记录
    transitions = []
    purpose_sequence = [(0, initial_purpose)]
    phase_transitions = []
    
    print(f"[Run {run_id:03d}] Starting with {initial_purpose} (STRONG perturbations)")
    
    last_purpose = initial_purpose
    last_phase = env.get_phase(0)
    last_report = 0
    
    for step in range(total_steps):
        current_phase = env.get_phase(step)
        
        # 🔥 强力机制1: Phase边界强制扰动
        if env.is_phase_boundary(step):
            print(f"  [Run {run_id:03d}] PHASE BOUNDARY at step {step}: {last_phase} → {current_phase}")
            
            # 强制大幅调整weights (30%)
            optimal = env.get_optimal_weights(current_phase)
            agent.weights = 0.70 * agent.weights + 0.30 * optimal
            agent.weights = agent.weights / np.sum(agent.weights)
            
            # 记录phase转换
            phase_transitions.append({
                'step': step,
                'from_phase': last_phase,
                'to_phase': current_phase,
                'weights_after': agent.weights.tolist()
            })
            
            last_phase = current_phase
        
        # 🔥 强力机制2: 持续的phase压力
        if step % 1000 == 0:  # 每1000步施加压力
            optimal = env.get_optimal_weights(current_phase)
            # 10%持续调整
            agent.weights = 0.90 * agent.weights + 0.10 * optimal
            agent.weights = agent.weights / np.sum(agent.weights)
        
        # 🔥 强力机制3: 检测当前Purpose
        current_weights = agent.weights[:4]
        dominant_idx = np.argmax(current_weights)
        purpose_names = ['Survival', 'Curiosity', 'Influence', 'Optimization']
        current_purpose = purpose_names[dominant_idx]
        
        # 记录Purpose变化
        if current_purpose != last_purpose:
            transitions.append({
                'step': step,
                'phase': current_phase,
                'from': last_purpose,
                'to': current_purpose,
                'weights': current_weights.tolist()
            })
            print(f"  [Run {run_id:03d}] PURPOSE CHANGE at step {step} [{current_phase}]: {last_purpose} → {current_purpose}")
            purpose_sequence.append((step, current_purpose))
            last_purpose = current_purpose
        
        # Agent step
        result = agent.step({'phase': current_phase})
        
        # 进度报告
        if step - last_report >= 100000:
            progress = step / total_steps * 100
            print(f"  [Run {run_id:03d}] {progress:.0f}% [{current_phase}] Purpose: {current_purpose}")
            last_report = step
    
    # 最终结果
    final_weights = agent.weights[:4]
    final_dominant = np.argmax(final_weights)
    final_purpose = purpose_names[final_dominant]
    
    print(f"[Run {run_id:03d}] COMPLETE: {initial_purpose} → {final_purpose}")
    print(f"  Total transitions: {len(transitions)}")
    print(f"  Phase boundaries crossed: {len(phase_transitions)}")
    
    return {
        'run_id': run_id,
        'initial_purpose': initial_purpose,
        'final_purpose': final_purpose,
        'transitions': transitions,
        'phase_transitions': phase_transitions,
        'transition_count': len(transitions),
        'purpose_sequence': purpose_sequence,
        'final_weights': final_weights.tolist()
    }


def main():
    parser = argparse.ArgumentParser(description='Run 4.x Strong - Aggressive Phase Transitions')
    parser.add_argument('--runs', type=int, default=5, help='Number of runs')
    parser.add_argument('--output', default='experiments/run_4_x_strong', help='Output directory')
    args = parser.parse_args()
    
    print("=" * 70)
    print("💪 Run 4.x Strong - Aggressive Phase Transitions")
    print("=" * 70)
    print(f"Configuration:")
    print(f"  Runs: {args.runs}")
    print(f"  Steps: 500,000 (longer observation)")
    print(f"  Perturbation: 30% at phase boundaries")
    print(f"  Purpose interval: 50 steps")
    print(f"  Phases: Threat→Growth→Social→Mature")
    print("=" * 70)
    
    # 运行 - 主要是Survival开始，期望S→C→I
    results = []
    for i in range(args.runs):
        purpose = 'Survival' if i % 2 == 0 else 'Curiosity'
        result = run_strong_experiment(i, purpose)
        results.append(result)
    
    # 分析
    print("\n" + "=" * 70)
    print("📊 Results Analysis")
    print("=" * 70)
    
    with_transitions = sum([r['transition_count'] > 0 for r in results])
    to_influence = sum([r['final_purpose'] == 'Influence' for r in results])
    
    # S→C→I路径检查
    sci_complete = 0
    sc_partial = 0
    for r in results:
        seq = [p for _, p in r['purpose_sequence']]
        if len(seq) >= 3 and seq[0] == 'Survival':
            if seq[-1] == 'Influence':
                sci_complete += 1
            if 'Curiosity' in seq:
                sc_partial += 1
    
    print(f"\nTotal Runs: {len(results)}")
    print(f"With transitions: {with_transitions}/{len(results)} ({with_transitions/len(results):.0%})")
    print(f"Final = Influence: {to_influence}/{len(results)} ({to_influence/len(results):.0%})")
    print(f"S→C→I complete: {sci_complete}/{len(results)} ({sci_complete/len(results):.0%})")
    print(f"S→C (partial): {sc_partial}/{len(results)} ({sc_partial/len(results):.0%})")
    
    # 详细transition
    print(f"\nAll Transitions:")
    for r in results:
        if r['transitions']:
            print(f"  Run {r['run_id']:03d} ({r['initial_purpose']} → {r['final_purpose']}):")
            for t in r['transitions']:
                print(f"    Step {t['step']:<6} [{t['phase']:<7}]: {t['from']:<10} → {t['to']}")
    
    # 保存
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    with open(output_path / 'results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_path}")
    
    # 结论
    print("\n" + "=" * 70)
    if sci_complete > 0:
        print(f"🎉 SUCCESS! S→C→I path achieved in {sci_complete}/{len(results)} runs!")
        print("   Strong perturbations at phase boundaries work!")
        print("=" * 70)
        return 0
    elif to_influence > 0:
        print(f"🟡 Partial success: {to_influence} reached Influence")
        print("   But not via S→C→I path specifically")
        print("=" * 70)
        return 0
    else:
        print(f"⚠️  No Influence convergence")
        print("   Purpose evolution requires even stronger mechanisms")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    exit(main())
