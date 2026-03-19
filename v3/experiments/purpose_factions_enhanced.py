"""
MOSS v3.1 - Phase 3 Enhanced: Resource Competition & Faction Formation
======================================================================

改进版：添加资源竞争机制促进派系形成

Author: Cash
Date: 2026-03-19 (20:47)
"""

import numpy as np
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.agent_9d import MOSSv3Agent9D


class ResourceCompetitionEnvironment:
    """
    资源竞争环境
    
    关键机制：
    - 有限资源（scarce resources）
    - 竞争压力（competition pressure）
    - 不同Purpose类型的agent对资源需求不同
    """
    
    def __init__(self, total_resources: float = 100.0, regeneration_rate: float = 0.1):
        self.total_resources = total_resources
        self.current_resources = total_resources
        self.regeneration_rate = regeneration_rate
        
        # 资源类型（对应不同Purpose的需求）
        self.resource_types = {
            'Survival': 0,      # 生存资源
            'Curiosity': 0,     # 信息资源
            'Influence': 0,     # 影响力资源
            'Optimization': 0   # 效率资源
        }
        
    def regenerate(self):
        """资源再生（有限）"""
        for key in self.resource_types:
            self.resource_types[key] = min(
                25.0,  # 上限
                self.resource_types[key] + self.regeneration_rate
            )
    
    def consume(self, agent_purpose: np.ndarray, amount: float = 1.0) -> float:
        """
        Agent消耗资源
        
        Purpose决定了对哪种资源需求更高
        """
        # 找到主导Purpose
        dominant_idx = np.argmax(agent_purpose[:4])
        resource_keys = list(self.resource_types.keys())
        dominant_type = resource_keys[dominant_idx]
        
        # 尝试消耗
        available = self.resource_types[dominant_type]
        consumed = min(available, amount)
        self.resource_types[dominant_type] -= consumed
        
        return consumed
    
    def get_scarcity(self) -> float:
        """计算整体稀缺度"""
        total = sum(self.resource_types.values())
        max_possible = len(self.resource_types) * 25.0
        return 1.0 - (total / max_possible)


class EnhancedPurposeFactionExperiment:
    """增强版Purpose派系实验（带资源竞争）"""
    
    def __init__(self, n_agents: int = 12):
        self.n_agents = n_agents
        self.agents: Dict[str, MOSSv3Agent9D] = {}
        self.environment = ResourceCompetitionEnvironment()
        
        # 记录
        self.resource_history = []
        self.conflict_records = []
        
    def initialize(self):
        """初始化"""
        print(f"Initializing {self.n_agents} agents with resource competition...")
        
        # 创建agent，添加随机初始偏差促进分化
        for i in range(self.n_agents):
            agent_id = f"enhanced_agent_{i:02d}"
            
            # 添加小的随机初始偏差（促进Purpose分化）
            noise = np.random.randn(4) * 0.05
            init_weights = np.array([0.25, 0.25, 0.25, 0.25]) + noise
            init_weights = np.maximum(init_weights, 0.1)
            init_weights = init_weights / init_weights.sum()
            
            self.agents[agent_id] = MOSSv3Agent9D(
                agent_id=agent_id,
                enable_social=True,
                enable_purpose=True,
                purpose_interval=300,  # 更频繁的Purpose评估
                initial_weights=init_weights
            )
        
        print(f"✓ {self.n_agents} agents created with varied initial conditions")
    
    def calculate_purpose_distance(self, agent_a: MOSSv3Agent9D, 
                                  agent_b: MOSSv3Agent9D) -> float:
        """计算Purpose距离（欧几里得距离）"""
        if not agent_a.purpose_generator or not agent_b.purpose_generator:
            return 1.0  # 最大距离
        
        vec_a = agent_a.purpose_generator.purpose_vector[:8]
        vec_b = agent_b.purpose_generator.purpose_vector[:8]
        
        return float(np.linalg.norm(vec_a - vec_b))
    
    def run_competitive_interaction(self, agent_a_id: str, agent_b_id: str, 
                                   step: int) -> Dict:
        """
        竞争环境下的互动
        
        关键：资源稀缺时，Purpose相似的agent更可能合作
        Purpose不同的agent更可能竞争
        """
        agent_a = self.agents[agent_a_id]
        agent_b = self.agents[agent_b_id]
        
        # 计算Purpose距离
        purpose_dist = self.calculate_purpose_distance(agent_a, agent_b)
        
        # 获取资源稀缺度
        scarcity = self.environment.get_scarcity()
        
        # 决策：资源稀缺 + Purpose距离大 → 高竞争
        #       资源充足 + Purpose距离小 → 高合作
        
        cooperation_threshold = 0.5 - (scarcity * 0.3) - (purpose_dist * 0.2)
        # scarcity高 → threshold降低（更难合作）
        # purpose_dist大 → threshold降低（更难合作）
        
        action_a = 'cooperate' if np.random.random() < cooperation_threshold else 'defect'
        action_b = 'cooperate' if np.random.random() < cooperation_threshold else 'defect'
        
        # 资源消耗
        if agent_a.purpose_generator:
            consumed_a = self.environment.consume(agent_a.purpose_generator.purpose_vector, 0.5)
        else:
            consumed_a = 0
            
        if agent_b.purpose_generator:
            consumed_b = self.environment.consume(agent_b.purpose_generator.purpose_vector, 0.5)
        else:
            consumed_b = 0
        
        # 记录冲突
        if action_a == 'defect' or action_b == 'defect':
            self.conflict_records.append({
                'step': step,
                'agents': (agent_a_id, agent_b_id),
                'purpose_distance': purpose_dist,
                'scarcity': scarcity,
                'actions': (action_a, action_b)
            })
        
        return {
            'purpose_distance': purpose_dist,
            'scarcity': scarcity,
            'cooperation': action_a == 'cooperate' and action_b == 'cooperate',
            'resources_consumed': (consumed_a, consumed_b)
        }
    
    def detect_factions(self, distance_threshold: float = 0.3) -> List[Set[str]]:
        """
        检测派系（基于Purpose距离）
        
        Purpose距离近的agent形成派系
        """
        agent_ids = list(self.agents.keys())
        n = len(agent_ids)
        
        # 计算距离矩阵
        dist_matrix = np.zeros((n, n))
        for i, aid_i in enumerate(agent_ids):
            for j, aid_j in enumerate(agent_ids):
                if i != j:
                    dist = self.calculate_purpose_distance(
                        self.agents[aid_i], self.agents[aid_j]
                    )
                    dist_matrix[i][j] = dist
        
        # 聚类：距离<threshold的为一派
        visited = set()
        factions = []
        
        for i in range(n):
            if i in visited:
                continue
            
            faction = {agent_ids[i]}
            queue = [i]
            
            while queue:
                curr = queue.pop(0)
                if curr in visited:
                    continue
                visited.add(curr)
                
                # 找所有距离近的
                for j in range(n):
                    if j not in visited and dist_matrix[curr][j] < distance_threshold:
                        faction.add(agent_ids[j])
                        queue.append(j)
            
            if len(faction) >= 2:
                factions.append(faction)
        
        return factions
    
    def run(self, n_steps: int = 3000) -> Dict:
        """运行增强版实验"""
        print("\n" + "="*70)
        print("🔥 MOSS v3.1 - Enhanced Faction Formation (with Resource Competition)")
        print("="*70)
        print(f"Agents: {self.n_agents}")
        print(f"Steps: {n_steps}")
        print(f"Resource scarcity: Enabled")
        print(f"Purpose competition: Enabled")
        print("="*70 + "\n")
        
        self.initialize()
        
        faction_history = []
        cooperation_by_distance = defaultdict(list)
        
        for step in range(n_steps):
            # Agent行动
            for agent in self.agents.values():
                agent.step()
            
            # 资源再生
            self.environment.regenerate()
            
            # 配对互动（带竞争）
            agent_ids = list(self.agents.keys())
            np.random.shuffle(agent_ids)
            
            for i in range(0, len(agent_ids)-1, 2):
                result = self.run_competitive_interaction(
                    agent_ids[i], agent_ids[i+1], step
                )
                
                # 按Purpose距离记录合作率
                dist_bin = round(result['purpose_distance'] * 2) / 2  # 0.5为间隔
                cooperation_by_distance[dist_bin].append(result['cooperation'])
            
            # 定期检查
            if step % 500 == 0 and step > 0:
                print(f"\n📍 Step {step}:")
                print(f"   Resource scarcity: {self.environment.get_scarcity():.2%}")
                print(f"   Conflicts so far: {len(self.conflict_records)}")
                
                factions = self.detect_factions()
                faction_history.append({
                    'step': step,
                    'n_factions': len(factions),
                    'factions': [list(f) for f in factions],
                    'scarcity': self.environment.get_scarcity()
                })
                
                if factions:
                    print(f"   Factions detected: {len(factions)}")
                    for i, f in enumerate(factions):
                        print(f"     Faction {i+1}: {len(f)} agents")
        
        # 最终分析
        final_factions = self.detect_factions()
        
        # 分析合作率 vs Purpose距离
        coop_by_dist = {}
        for dist, coops in cooperation_by_distance.items():
            coop_by_dist[float(dist)] = np.mean(coops) if coops else 0
        
        results = {
            'config': {
                'n_agents': self.n_agents,
                'n_steps': n_steps,
                'resource_scarcity': True,
                'timestamp': datetime.now().isoformat()
            },
            'faction_history': faction_history,
            'final_factions': [list(f) for f in final_factions],
            'n_conflicts': len(self.conflict_records),
            'cooperation_by_distance': coop_by_dist,
            'final_scarcity': self.environment.get_scarcity()
        }
        
        # 保存
        save_path = Path('experiments/purpose_faction_enhanced_results.json')
        with open(save_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        return results
    
    def print_results(self, results: Dict):
        """打印结果"""
        print("\n" + "="*70)
        print("📊 ENHANCED FACTION FORMATION ANALYSIS")
        print("="*70)
        
        final_factions = results['final_factions']
        print(f"\n🔥 Final Factions: {len(final_factions)}")
        
        for i, faction in enumerate(final_factions):
            print(f"\n  Faction {i+1}: {len(faction)} agents")
            # 分析这个派系的Purpose特征
            purposes = []
            for aid in faction[:3]:
                if self.agents[aid].purpose_generator:
                    summary = self.agents[aid].get_purpose_summary()
                    purposes.append(summary.get('dominant_dimension', 'Unknown'))
            print(f"    Common purposes: {purposes}")
        
        print(f"\n⚔️  Conflict Analysis:")
        print(f"  Total conflicts: {results['n_conflicts']}")
        print(f"  Final scarcity: {results['final_scarcity']:.2%}")
        
        print(f"\n🤝 Cooperation vs Purpose Distance:")
        for dist, coop in sorted(results['cooperation_by_distance'].items()):
            print(f"  Distance {dist:.1f}: {coop:.2%} cooperation")
        
        # 判断H3
        print(f"\n✅ Hypothesis H3 (Purpose Factions): ", end="")
        if len(final_factions) >= 2:
            print("SUPPORTED")
            print(f"   {len(final_factions)} distinct factions formed under resource competition")
        elif results['n_conflicts'] > 10:
            print("PARTIALLY SUPPORTED")
            print(f"   Conflicts emerged but single dominant faction")
        else:
            print("NEEDS LONGER SIMULATION")
            print(f"   High cooperation despite resource pressure")
        
        print("="*70)


if __name__ == "__main__":
    print("="*70)
    print("🚀 MOSS v3.1 - Enhanced Phase 3 (Resource Competition)")
    print("="*70)
    
    experiment = EnhancedPurposeFactionExperiment(n_agents=12)
    results = experiment.run(n_steps=3000)
    experiment.print_results(results)
    
    print("\n✓ Enhanced faction experiment complete!")
    print("="*70)
