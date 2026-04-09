"""
MOSS v3.1 - H4 Validation: Purpose Self-Fulfillment
====================================================

验证假设H4: Agents acting according to their Purpose achieve higher satisfaction

测试：Purpose-guided vs Non-Purpose-guided agents

Author: Cash
Date: 2026-03-19 (21:06)
"""

import numpy as np
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.agent_9d import MOSSv3Agent9D


class PurposeFulfillmentExperiment:
    """Purpose自我实现实验"""
    
    def __init__(self, n_agents_per_group: int = 6):
        self.n_agents = n_agents_per_group
        
        # 实验组：Purpose-guided
        self.purpose_guided_agents: Dict[str, MOSSv3Agent9D] = {}
        
        # 对照组：Non-Purpose-guided (base 8D)
        self.non_purpose_agents: Dict[str, MOSSv3Agent9D] = {}
        
    def initialize(self):
        """初始化两组agent"""
        print("\nInitializing two groups...")
        
        # 实验组：启用Purpose，Purpose指导行为
        for i in range(self.n_agents):
            agent_id = f"purpose_guided_{i:02d}"
            self.purpose_guided_agents[agent_id] = MOSSv3Agent9D(
                agent_id=agent_id,
                enable_social=True,
                enable_purpose=True,
                purpose_interval=200
            )
        
        # 对照组：禁用Purpose，纯8D行为
        for i in range(self.n_agents):
            agent_id = f"non_purpose_{i:02d}"
            self.non_purpose_agents[agent_id] = MOSSv3Agent9D(
                agent_id=agent_id,
                enable_social=True,
                enable_purpose=False  # 禁用Purpose
            )
        
        print(f"✓ Purpose-guided group: {self.n_agents} agents")
        print(f"✓ Non-Purpose group: {self.n_agents} agents")
    
    def calculate_fulfillment_score(self, agent: MOSSv3Agent9D) -> float:
        """
        计算满足感/实现分数
        
        基于：
        1. Coherence (自我一致性)
        2. Valence (正向体验)
        3. 是否按照Purpose行动
        """
        if not agent.history_9d:
            return 0.0
        
        recent = agent.history_9d[-100:] if len(agent.history_9d) > 100 else agent.history_9d
        
        # 1. Coherence分数（负的绝对值越小越好）
        coherence_scores = [s.coherence for s in recent]
        avg_coherence = np.mean(coherence_scores)
        coherence_normalized = 1.0 / (1.0 + abs(avg_coherence))
        
        # 2. Valence分数（正向体验比例）
        valence_scores = [s.valence for s in recent]
        positive_valence = sum(1 for v in valence_scores if v > 0) / len(valence_scores)
        
        # 3. Purpose对齐度（如果有Purpose）
        purpose_alignment = 0.5  # 默认值
        if agent.purpose_generator and len(agent.history_9d) > 10:
            # 检查行为是否符合Purpose
            purpose_vec = agent.purpose_generator.purpose_vector[:4]  # 前4维
            current_weights = agent.weights
            
            # 计算当前权重与Purpose的相似度
            dot = np.dot(purpose_vec, current_weights)
            norm_p = np.linalg.norm(purpose_vec)
            norm_w = np.linalg.norm(current_weights)
            
            if norm_p > 0 and norm_w > 0:
                purpose_alignment = dot / (norm_p * norm_w)
        
        # 综合分数
        fulfillment = (
            coherence_normalized * 0.3 +
            positive_valence * 0.3 +
            purpose_alignment * 0.4
        )
        
        return float(fulfillment)
    
    def run_group(self, agents: Dict[str, MOSSv3Agent9D], 
                  group_name: str, n_steps: int) -> Dict:
        """运行一组agent"""
        print(f"\n{'='*70}")
        print(f"Running {group_name} ({n_steps} steps)...")
        print(f"{'='*70}")
        
        fulfillment_history = []
        
        for step in range(n_steps):
            # 每个agent执行
            for agent in agents.values():
                agent.step()
            
            # 每100步记录满足感
            if step % 100 == 0 and step > 0:
                scores = [self.calculate_fulfillment_score(a) for a in agents.values()]
                avg_fulfillment = np.mean(scores)
                fulfillment_history.append({
                    'step': step,
                    'mean_fulfillment': float(avg_fulfillment),
                    'std_fulfillment': float(np.std(scores))
                })
                
                if step % 500 == 0:
                    print(f"  Step {step}: Fulfillment = {avg_fulfillment:.4f}")
        
        # 最终评估
        final_scores = [self.calculate_fulfillment_score(a) for a in agents.values()]
        
        return {
            'fulfillment_history': fulfillment_history,
            'final_mean': float(np.mean(final_scores)),
            'final_std': float(np.std(final_scores)),
            'final_scores': final_scores
        }
    
    def run(self, n_steps: int = 2000) -> Dict:
        """运行完整实验"""
        print("="*70)
        print("🎯 MOSS v3.1 - H4 Validation: Purpose Self-Fulfillment")
        print("="*70)
        print(f"\nHypothesis H4: Purpose-guided agents achieve higher satisfaction")
        print(f"Steps: {n_steps}")
        print(f"Agents per group: {self.n_agents}")
        
        # 初始化
        self.initialize()
        
        # 运行实验组
        purpose_results = self.run_group(
            self.purpose_guided_agents, 
            "Purpose-Guided Group", 
            n_steps
        )
        
        # 运行对照组
        non_purpose_results = self.run_group(
            self.non_purpose_agents,
            "Non-Purpose Group",
            n_steps
        )
        
        # 对比分析
        results = {
            'config': {
                'n_agents_per_group': self.n_agents,
                'n_steps': n_steps,
                'timestamp': datetime.now().isoformat()
            },
            'purpose_guided': purpose_results,
            'non_purpose': non_purpose_results,
            'comparison': {
                'fulfillment_difference': (
                    purpose_results['final_mean'] - non_purpose_results['final_mean']
                ),
                'relative_improvement': (
                    (purpose_results['final_mean'] - non_purpose_results['final_mean']) /
                    non_purpose_results['final_mean'] * 100
                    if non_purpose_results['final_mean'] > 0 else 0
                )
            }
        }
        
        # 保存
        save_path = Path('experiments/purpose_fulfillment_results.json')
        with open(save_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        return results
    
    def print_results(self, results: Dict):
        """打印结果"""
        print("\n" + "="*70)
        print("📊 PURPOSE SELF-FULFILLMENT ANALYSIS")
        print("="*70)
        
        purpose = results['purpose_guided']
        non_purpose = results['non_purpose']
        comp = results['comparison']
        
        print(f"\n🎯 Fulfillment Scores:")
        print(f"  Purpose-Guided: {purpose['final_mean']:.4f} ± {purpose['final_std']:.4f}")
        print(f"  Non-Purpose:    {non_purpose['final_mean']:.4f} ± {non_purpose['final_std']:.4f}")
        
        print(f"\n📈 Comparison:")
        print(f"  Absolute difference: {comp['fulfillment_difference']:+.4f}")
        print(f"  Relative improvement: {comp['relative_improvement']:+.2f}%")
        
        print(f"\n✅ Hypothesis H4 (Purpose Self-Fulfillment): ", end="")
        if comp['fulfillment_difference'] > 0.05:  # 显著正向差异
            print("SUPPORTED")
            print(f"   Purpose-guided agents show {comp['relative_improvement']:.1f}% higher fulfillment")
        elif comp['fulfillment_difference'] > 0:
            print("PARTIALLY SUPPORTED")
            print(f"   Small positive effect ({comp['relative_improvement']:.1f}%)")
        else:
            print("NOT SUPPORTED")
            print(f"   No significant benefit observed")
        
        print("="*70)


if __name__ == "__main__":
    print("="*70)
    print("🚀 MOSS v3.1 - H4 Validation: Purpose Self-Fulfillment")
    print("="*70)
    
    experiment = PurposeFulfillmentExperiment(n_agents_per_group=6)
    results = experiment.run(n_steps=2000)
    experiment.print_results(results)
    
    print("\n✓ H4 validation experiment complete!")
    print("="*70)
