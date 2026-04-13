#!/usr/bin/env python3
"""
MOSS Run 4.x Strong - Aggressive Phase Transitions (Windows兼容修复版)

强力版Run 4.x: 实现强制phase扰动以达成S→C→I

增强机制:
1. 强制phase边界扰动 (30%+ adjustment)
2. 强制Purpose重新生成
3. 更长的时间尺度 (500k steps) (测试版: 10k steps)
4. 社交压力模拟

目标: 最终验证S→C→I路径

Usage:
    python experiments/run_4_x_strong_fixed.py --runs 2
"""

import sys
import os

# 修复路径问题 - Windows兼容
_MOSS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _MOSS_ROOT)

import numpy as np
import json
import argparse
from pathlib import Path
from typing import Dict, List
from datetime import datetime

# 尝试导入核心模块
try:
    from moss.core.unified_agent import UnifiedMOSSAgent, MOSSConfig
    from moss.core.causal_purpose import CausalPurposeGenerator, CausalPurposeConfig
    AGENT_TYPE = "unified"
except ImportError as e:
    print(f"⚠️  无法导入 unified agent: {e}")
    print("🔄 尝试使用 v9d 作为回退...")
    try:
        sys.path.insert(0, os.path.join(_MOSS_ROOT, '_archive_v3', 'core'))
        from agent_9d import MOSSv3Agent9D
        AGENT_TYPE = "v9d"
        print("✅ 成功导入 v9d agent 作为回退")
    except ImportError as e2:
        print(f"❌ 无法导入任何agent: {e2}")
        raise


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
        for name, start, end in self.phypes:
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
    
    total_steps = 10000  # 测试模式: 10k步
    
    # 使用因果Purpose生成器（更强的演化能力）
    if AGENT_TYPE == "unified":
        purpose_config = CausalPurposeConfig(
            initial_purpose_statement=initial_purpose,
            perturbation_strength=0.35,  # 强力扰动
            adaptability_rate=0.2,
            context_size=10
        )
        purpose_generator = CausalPurposeGenerator(purpose_config)
        
        agent_config = MOSSConfig(
            purpose_generator=purpose_generator,
            phase_switching_threshold=0.7,
            force_phase_transition=True  # 强制phase转换
        )
        agent = UnifiedMOSSAgent(agent_config)
    else:  # v9d
        try:
            from moss.core.causal_purpose import CausalPurposeConfig, CausalPurposeGenerator
            purpose_config = CausalPurposeConfig(
                initial_purpose_statement=initial_purpose,
                perturbation_strength=0.35,
                adaptability_rate=0.2,
                context_size=10
            )
            purpose_generator = CausalPurposeGenerator(purpose_config)
            
            # v9d agent初始化
            from _archive_v3.core.agent_9d import MOSSv3Agent9D
            
            agent = MOSSv3Agent9D()
            agent.purpose_generator = purpose_generator
        except Exception as e:
            print(f"❌ v9d agent初始化失败: {e}")
            return {}
    
    env = StrongPhasedEnvironment(total_steps)
    
    # 数据记录
    data = {
        'run_id': run_id,
        'initial_purpose': initial_purpose,
        'agent_type': AGENT_TYPE,
        'steps': [],
        'phases': [],
        'purpose_vectors': [],
        'coherence_scores': []
    }
    
    print(f"\n🚀 运行 {run_id}: {initial_purpose} ({AGENT_TYPE})")
    
    for step in range(total_steps):
        # 获取当前phase
        current_phase = env.get_phase(step)
        
        # 环境压力
        if env.is_phase_boundary(step):
            # 强制Purpose扰动
            if AGENT_TYPE == "unified":
                agent.force_purpose_perturbation(strength=0.4)
            else:
                # v9d的Purpose扰动
                agent.purpose_generator.perturb_purpose(perturbation_strength=0.4)
        
        # 生成观察
        observation = {
            'resource_level': 0.5 + 0.3 * np.sin(step * 0.001),
            'threat_level': 0.3 if current_phase != 'threat' else 0.7,
            'novelty': 0.6 if current_phase == 'growth' else 0.3,
            'social_feedback': 0.4 if current_phase == 'social' else 0.2,
            'phase': current_phase,
            'step': step,
            'progress': step / total_steps
        }
        
        # Agent执行
        try:
            if AGENT_TYPE == "unified":
                outcome = agent.step(observation)
            else:
                outcome = agent.step(observation)
            
            # 记录数据
            if step % 100 == 0:
                if AGENT_TYPE == "unified":
                    purpose_vec = agent.get_purpose_vector()
                    coherence = agent.get_coherence_score()
                else:
                    purpose_vec = list(agent.purpose_generator.purpose_vector)
                    coherence = 0.0  # v9d没有coherence score
                
                data['steps'].append(step)
                data['phases'].append(current_phase)
                data['purpose_vectors'].append(purpose_vec)
                data['coherence_scores'].append(coherence)
                
                if step % 1000 == 0:
                    print(f"  Step {step:,}: Phase={current_phase}, Purpose={purpose_vec[:4] if len(purpose_vec) >= 4 else purpose_vec}")
                    
        except Exception as e:
            print(f"❌ 步骤 {step} 错误: {e}")
            continue
    
    print(f"✅ 运行 {run_id} 完成: {len(data['steps'])} 记录点")
    return data


def main():
    parser = argparse.ArgumentParser(description='强力版Run 4.x实验')
    parser.add_argument('--runs', type=int, default=2, help='运行次数')
    parser.add_argument('--output', type=str, default='experiments/run_4_x_strong_results.json', help='输出文件')
    args = parser.parse_args()
    
    # Purpose陈述集合
    purpose_statements = [
        "探索新的知识领域并创新",
        "建立社会联系和影响力",
        "优化系统性能并提升效率",
        "确保长期生存和安全"
    ]
    
    print("=" * 70)
    print("MOSS Run 4.x Strong - Aggressive Phase Transitions")
    print(f"Agent类型: {AGENT_TYPE}")
    print(f"运行次数: {args.runs}")
    print(f"总步数: 10,000 (测试模式)")
    print("=" * 70)
    
    all_results = []
    
    for run_id in range(args.runs):
        purpose_idx = run_id % len(purpose_statements)
        initial_purpose = purpose_statements[purpose_idx]
        
        result = run_strong_experiment(run_id, initial_purpose)
        if result:  # 只记录成功的结果
            all_results.append(result)
    
    # 保存结果
    output_dir = Path(args.output).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'agent_type': AGENT_TYPE,
                'total_runs': len(all_results),
                'steps_per_run': 10000
            },
            'results': all_results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 所有运行完成!")
    print(f"总运行: {len(all_results)}")
    print(f"结果文件: {args.output}")
    print("=" * 70)
    
    # 简单统计
    if all_results:
        total_steps = sum(len(r['steps']) for r in all_results)
        avg_coherence = np.mean([np.mean(r['coherence_scores']) for r in all_results if r['coherence_scores']])
        print(f"总记录点: {total_steps:,}")
        print(f"平均coherence: {avg_coherence:.3f}")


if __name__ == "__main__":
    main()