"""
MOSS v3.1 - Purpose Society Experiment
======================================

多agent Purpose涌现实验
观察不同agent是否会发展出不同的Purpose

Author: Cash
Date: 2026-03-19
"""

import numpy as np
import json
from typing import Dict, List
from datetime import datetime
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.agent_9d import MOSSv3Agent9D


class PurposeSociety:
    """Purpose Society - 多agent Purpose涌现观察"""
    
    def __init__(self, n_agents: int = 6):
        """初始化Purpose社会"""
        self.n_agents = n_agents
        
        # 创建agents（相同初始条件）
        self.agents: Dict[str, MOSSv3Agent9D] = {}
        for i in range(n_agents):
            agent_id = f"purpose_agent_{i:02d}"
            
            # 所有agent相同初始权重
            init_weights = np.array([0.25, 0.25, 0.25, 0.25])
            
            self.agents[agent_id] = MOSSv3Agent9D(
                agent_id=agent_id,
                enable_social=True,
                enable_purpose=True,
                purpose_interval=150,  # 每150步生成purpose
                initial_weights=init_weights.copy()
            )
        
        self.interactions = []
        self.step_count = 0
        
    def step(self):
        """执行一步社会互动"""
        self.step_count += 1
        
        # 简单模拟：每个agent执行一步
        for agent_id, agent in self.agents.items():
            agent.step()
    
    def run(self, n_steps: int = 500):
        """运行实验"""
        print(f"\n{'='*70}")
        print(f"🌟 Purpose Society Experiment")
        print(f"{'='*70}")
        print(f"Agents: {self.n_agents}")
        print(f"Steps: {n_steps}")
        print(f"Initial condition: All identical (weights=[0.25, 0.25, 0.25, 0.25])")
        print(f"{'='*70}\n")
        
        for step in range(n_steps):
            self.step()
            
            if step % 100 == 0:
                print(f"Step {step}...")
        
        print(f"\n{'='*70}")
        print("📊 RESULTS")
        print(f"{'='*70}")
        
        # 分析Purpose分化
        purposes = {}
        for agent_id, agent in self.agents.items():
            if agent.purpose_generator:
                summary = agent.get_purpose_summary()
                purposes[agent_id] = summary
        
        print("\n🎯 Purpose Distribution:")
        dominant_dims = [p['dominant_dimension'] for p in purposes.values()]
        from collections import Counter
        dim_counts = Counter(dominant_dims)
        
        for dim, count in dim_counts.items():
            print(f"  {dim}: {count}/{self.n_agents} agents ({count/self.n_agents:.1%})")
        
        print("\n📝 Purpose Statements (Sample):")
        for i, (agent_id, p) in enumerate(purposes.items()):
            if i < 3:  # 只显示前3个
                print(f"  {agent_id}: {p['current_statement'][:80]}...")
        
        # Purpose漂移分析
        print("\n📈 Purpose Drift:")
        drifts = [p['purpose_drift'] for p in purposes.values()]
        print(f"  Mean drift: {np.mean(drifts):.4f}")
        print(f"  Max drift: {np.max(drifts):.4f}")
        print(f"  Min drift: {np.min(drifts):.4f}")
        
        # 保存结果
        results = {
            'timestamp': datetime.now().isoformat(),
            'config': {
                'n_agents': self.n_agents,
                'n_steps': n_steps,
                'initial_weights': [0.25, 0.25, 0.25, 0.25]
            },
            'purpose_distribution': dict(dim_counts),
            'agent_purposes': purposes
        }
        
        save_path = Path('experiments/purpose_society_results.json')
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {save_path}")
        print(f"{'='*70}\n")
        
        return results


if __name__ == "__main__":
    print("="*70)
    print("🚀 MOSS v3.1 - Purpose Society Experiment")
    print("="*70)
    print("\nTesting: Do identical agents develop different purposes?")
    print("Expected: Purpose divergence (different 'life philosophies')\n")
    
    society = PurposeSociety(n_agents=6)
    results = society.run(n_steps=500)
    
    # 分析
    n_types = len(results['purpose_distribution'])
    print(f"✓ Hypothesis H1 (Purpose Divergence): {'SUPPORTED' if n_types > 1 else 'NOT SUPPORTED'}")
    print(f"  → {n_types} distinct purpose types emerged from identical starts")
    
    print("\n" + "="*70)
    print("✓ Purpose Society experiment complete!")
    print("="*70)
