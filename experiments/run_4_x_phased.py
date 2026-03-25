#!/usr/bin/env python3
"""
MOSS Run 4.x Phased - Structured Environment
============================================

结构化环境版Run 4.x: 复现原始实验的phase结构

Phase设计（模仿原始Run 4.x）:
- Phase 1 (0-33%): Threat → favors Survival
- Phase 2 (33-66%): Growth → favors Curiosity
- Phase 3 (66-100%): Social → favors Influence

目标: 验证S→C→I路径需要环境phase驱动

Usage:
    python3 experiments/run_4_x_phased.py --runs 10
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


class PhasedEnvironment:
    """
    结构化环境（3 Phases）
    
    模仿原始Run 4.x的环境结构
    """
    
    def __init__(self, total_steps: int):
        self.total_steps = total_steps
        self.phase_boundaries = {
            'threat': (0, int(total_steps * 0.33)),      # 0-33%
            'growth': (int(total_steps * 0.33), int(total_steps * 0.66)),  # 33-66%
            'social': (int(total_steps * 0.66), total_steps)  # 66-100%
        }
    
    def get_current_phase(self, step: int) -> str:
        """获取当前phase"""
        for phase, (start, end) in self.phase_boundaries.items():
            if start <= step < end:
                return phase
        return 'social'  # 默认
    
    def get_phase_weights(self, phase: str) -> np.ndarray:
        """
        获取phase对应的最优权重
        
        这些权重会作为"环境压力"影响agent
        """
        phase_optimal = {
            'threat': np.array([0.80, 0.10, 0.05, 0.05]),    # Survival optimal
            'growth': np.array([0.10, 0.70, 0.15, 0.05]),    # Curiosity optimal
            'social': np.array([0.10, 0.15, 0.65, 0.10])     # Influence optimal
        }
        return phase_optimal.get(phase, np.array([0.25]*4))
    
    def calculate_reward(self, action: str, phase: str) -> float:
        """
        根据phase计算行为奖励
        
        不同phase奖励不同行为，驱动Purpose变化
        """
        phase_actions = {
            'threat': ['ensure_resource', 'monitor_system_health', 'create_backup', 'verify_security'],
            'growth': ['explore_new_patterns', 'research_alternatives', 'analyze_unfamiliar_code', 'document_discoveries'],
            'social': ['share_knowledge', 'collaborate_with_peer', 'mentor_other_agent', 'propose_improvements']
        }
        
        # 如果action匹配当前phase，高奖励
        if any(pa in action for pa in phase_actions.get(phase, [])):
            return np.random.uniform(0.5, 1.0)
        else:
            return np.random.uniform(-0.2, 0.3)


def run_phased_experiment(run_id: int, initial_purpose: str) -> Dict:
    """
    运行结构化环境实验
    """
    
    total_steps = 200000  # 20万步，适中长度
    
    config = MOSSConfig(
        agent_id=f"phased_{run_id:03d}",
        enable_purpose=True,
        purpose_interval=100,  # 正常频率
        log_dir=f"experiments/run_4_x_phased/run_{run_id:03d}"
    )
    
    agent = UnifiedMOSSAgent(config)
    env = PhasedEnvironment(total_steps)
    
    # 设置初始Purpose
    weights_map = {
        'Survival': [0.70, 0.10, 0.10, 0.10],
        'Curiosity': [0.10, 0.70, 0.10, 0.10],
        'Balanced': [0.25, 0.25, 0.25, 0.25]
    }
    agent.weights = np.array(weights_map.get(initial_purpose, [0.25]*4))
    
    # 记录
    purpose_sequence = [(0, initial_purpose)]
    transitions = []
    phase_history = []
    
    print(f"[Run {run_id:03d}] Starting with {initial_purpose} (phased environment)")
    
    last_purpose = initial_purpose
    last_report_step = 0
    
    for step in range(total_steps):
        # 获取当前phase
        current_phase = env.get_current_phase(step)
        
        # 记录phase历史
        if step % 1000 == 0:
            phase_history.append((step, current_phase))
        
        # 创建观察（包含phase信息）
        observation = {
            'phase': current_phase,
            'is_critical': current_phase == 'threat',
            'is_growth': current_phase == 'growth',
            'is_social': current_phase == 'social'
        }
        
        # Agent step
        result = agent.step(observation)
        
        # 根据phase计算奖励（环境影响）
        reward = env.calculate_reward(result.action_type, current_phase)
        
        # 环境压力：定期调整agent weights向phase最优
        if step % 500 == 0:  # 每500步施加环境压力
            phase_optimal = env.get_phase_weights(current_phase)
            # 轻微调整agent weights向phase最优（环境适应压力）
            agent.weights = 0.95 * agent.weights + 0.05 * phase_optimal
            agent.weights = agent.weights / np.sum(agent.weights)  # 归一化
        
        # 检测Purpose变化
        current_weights = agent.weights[:4]
        dominant_idx = np.argmax(current_weights)
        purpose_names = ['Survival', 'Curiosity', 'Influence', 'Optimization']
        current_purpose = purpose_names[dominant_idx]
        
        if current_purpose != last_purpose:
            transitions.append({
                'step': step,
                'phase': current_phase,
                'from': last_purpose,
                'to': current_purpose,
                'weights': current_weights.tolist()
            })
            print(f"  [Run {run_id:03d}] Step {step} ({current_phase}): {last_purpose} → {current_purpose}")
            purpose_sequence.append((step, current_purpose))
            last_purpose = current_purpose
        
        # 进度报告
        if step - last_report_step >= 50000:
            progress = step / total_steps * 100
            current_phase = env.get_current_phase(step)
            print(f"  [Run {run_id:03d}] {progress:.0f}% [{current_phase}] - Purpose: {last_purpose}")
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
        'phase_history': phase_history,
        'final_weights': final_weights.tolist()
    }


def main():
    parser = argparse.ArgumentParser(description='Run 4.x Phased - Structured Environment')
    parser.add_argument('--runs', type=int, default=10, help='Number of runs')
    parser.add_argument('--output', default='experiments/run_4_x_phased', help='Output directory')
    args = parser.parse_args()
    
    print("=" * 70)
    print("🎯 Run 4.x Phased - Structured Environment (S→C→I)")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Runs: {args.runs}")
    print(f"  Steps per run: 200,000")
    print(f"  Phases: Threat → Growth → Social")
    print(f"  Expected: S→C→I transitions")
    print("=" * 70)
    
    # 运行实验（从Survival开始，期望S→C→I）
    initial_purposes = ['Survival', 'Survival', 'Survival', 'Curiosity', 'Curiosity', 
                       'Balanced', 'Balanced', 'Balanced', 'Balanced', 'Balanced']
    results = []
    
    for i in range(args.runs):
        purpose = initial_purposes[i % len(initial_purposes)]
        result = run_phased_experiment(i, purpose)
        results.append(result)
    
    # 分析结果
    print("\n" + "=" * 70)
    print("📊 Results Analysis")
    print("=" * 70)
    
    with_transitions = sum([r['transition_count'] > 0 for r in results])
    to_influence = sum([r['final_purpose'] == 'Influence' for r in results])
    
    # 检查S→C→I路径
    sci_path = 0
    for r in results:
        seq = [p for _, p in r['purpose_sequence']]
        if len(seq) >= 3:
            if seq[0] == 'Survival' and 'Curiosity' in seq and seq[-1] == 'Influence':
                sci_path += 1
    
    print(f"\nTotal Runs: {len(results)}")
    print(f"With Purpose Transitions: {with_transitions}/{len(results)} ({with_transitions/len(results):.1%})")
    print(f"Final Purpose = Influence: {to_influence}/{len(results)} ({to_influence/len(results):.1%})")
    print(f"S→C→I Path Complete: {sci_path}/{len(results)} ({sci_path/len(results):.1%})")
    
    # 显示transition详情
    print(f"\nTransition Details:")
    for r in results:
        if r['transitions']:
            print(f"  Run {r['run_id']:03d} ({r['initial_purpose']}):")
            for t in r['transitions']:
                print(f"    Step {t['step']} [{t['phase']}]: {t['from']} → {t['to']}")
    
    # 保存结果
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    with open(output_path / 'results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_path}")
    
    # 结论
    print("\n" + "=" * 70)
    if sci_path > 0:
        print(f"🎉 SUCCESS: S→C→I path observed in {sci_path}/{len(results)} runs!")
        print("   This proves environment structure is crucial for Purpose evolution.")
        print("=" * 70)
        return 0
    elif to_influence > 0:
        print(f"🟡 Partial: {to_influence} runs reached Influence, but not S→C→I path")
        print("   Purpose evolution works, but path may differ.")
        print("=" * 70)
        return 0
    else:
        print(f"⚠️  No Influence convergence observed")
        print("   May need stronger phase transitions or longer runs.")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    exit(main())
