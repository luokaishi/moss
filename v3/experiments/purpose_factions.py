"""
MOSS v3.1 - Phase 3: Purpose Faction Formation
===============================================

Purpose派系形成实验
验证假设H3: Agents with similar purposes form "philosophical factions"

Author: Cash
Date: 2026-03-19 (continuing from 20:43)
"""

import numpy as np
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Set
from collections import defaultdict
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.agent_9d import MOSSv3Agent9D


class PurposeFactionExperiment:
    """Purpose派系形成实验"""
    
    def __init__(self, n_agents: int = 12):
        self.n_agents = n_agents
        self.agents: Dict[str, MOSSv3Agent9D] = {}
        self.interaction_matrix = np.zeros((n_agents, n_agents))
        self.cooperation_records = defaultdict(list)
        
    def initialize_society(self):
        """初始化社会 - 所有agent相同初始条件"""
        print("Initializing Purpose Society with {} agents...".format(self.n_agents))
        
        for i in range(self.n_agents):
            agent_id = f"faction_agent_{i:02d}"
            
            # 相同初始条件
            init_weights = np.array([0.25, 0.25, 0.25, 0.25])
            
            self.agents[agent_id] = MOSSv3Agent9D(
                agent_id=agent_id,
                enable_social=True,
                enable_purpose=True,
                purpose_interval=400,  # 每400步评估
                initial_weights=init_weights.copy()
            )
        
        print(f"✓ {self.n_agents} agents created with identical initial conditions")
    
    def calculate_purpose_similarity(self, agent_a: MOSSv3Agent9D, 
                                    agent_b: MOSSv3Agent9D) -> float:
        """
        计算两个agent的Purpose相似度
        
        使用余弦相似度
        """
        if not agent_a.purpose_generator or not agent_b.purpose_generator:
            return 0.0
        
        vec_a = agent_a.purpose_generator.purpose_vector[:8]  # 前8维
        vec_b = agent_b.purpose_generator.purpose_vector[:8]
        
        # 余弦相似度
        dot = np.dot(vec_a, vec_b)
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        similarity = dot / (norm_a * norm_b)
        return float(similarity)
    
    def detect_factions(self, similarity_threshold: float = 0.8) -> List[Set[str]]:
        """
        检测派系
        
        使用简单的聚类：相似度>阈值的agent形成派系
        """
        agent_ids = list(self.agents.keys())
        n = len(agent_ids)
        
        # 计算相似度矩阵
        sim_matrix = np.zeros((n, n))
        for i, aid_i in enumerate(agent_ids):
            for j, aid_j in enumerate(agent_ids):
                if i != j:
                    sim = self.calculate_purpose_similarity(
                        self.agents[aid_i], self.agents[aid_j]
                    )
                    sim_matrix[i][j] = sim
        
        # 简单聚类（连通分量）
        visited = set()
        factions = []
        
        for i in range(n):
            if i in visited:
                continue
            
            # BFS找连通分量
            faction = set()
            queue = [i]
            
            while queue:
                curr = queue.pop(0)
                if curr in visited:
                    continue
                
                visited.add(curr)
                faction.add(agent_ids[curr])
                
                # 找相似的邻居
                for j in range(n):
                    if j not in visited and sim_matrix[curr][j] > similarity_threshold:
                        queue.append(j)
            
            if len(faction) > 1:  # 至少2个agent才算派系
                factions.append(faction)
        
        return factions
    
    def run_interaction(self, agent_a_id: str, agent_b_id: str, step: int):
        """
        两个agent之间的互动
        
        基于Purpose相似度决定合作/竞争
        """
        agent_a = self.agents[agent_a_id]
        agent_b = self.agents[agent_b_id]
        
        # 计算Purpose相似度
        similarity = self.calculate_purpose_similarity(agent_a, agent_b)
        
        # 决策：相似度高→合作，相似度低→竞争/谨慎
        if similarity > 0.7:
            # 高相似度，大概率合作
            action_a = 'cooperate' if np.random.random() > 0.1 else 'defect'
            action_b = 'cooperate' if np.random.random() > 0.1 else 'defect'
        elif similarity > 0.4:
            # 中等相似度，混合策略
            action_a = 'cooperate' if np.random.random() > 0.3 else 'defect'
            action_b = 'cooperate' if np.random.random() > 0.3 else 'defect'
        else:
            # 低相似度，大概率竞争
            action_a = 'cooperate' if np.random.random() > 0.7 else 'defect'
            action_b = 'cooperate' if np.random.random() > 0.7 else 'defect'
        
        # 记录
        pair = tuple(sorted([agent_a_id, agent_b_id]))
        self.cooperation_records[pair].append({
            'step': step,
            'similarity': similarity,
            'action_a': action_a,
            'action_b': action_b,
            'both_cooperated': action_a == 'cooperate' and action_b == 'cooperate'
        })
    
    def run(self, n_steps: int = 2000) -> Dict:
        """运行派系形成实验"""
        print("\n" + "="*70)
        print("🎭 MOSS v3.1 - Purpose Faction Formation Experiment")
        print("="*70)
        print(f"Agents: {self.n_agents}")
        print(f"Steps: {n_steps}")
        print(f"Hypothesis H3: Agents with similar purposes form factions")
        print("="*70 + "\n")
        
        # 初始化
        self.initialize_society()
        
        # 运行
        faction_history = []
        
        for step in range(n_steps):
            # 每个agent执行一步
            for agent in self.agents.values():
                agent.step()
            
            # 随机配对互动
            agent_ids = list(self.agents.keys())
            np.random.shuffle(agent_ids)
            
            for i in range(0, len(agent_ids)-1, 2):
                self.run_interaction(agent_ids[i], agent_ids[i+1], step)
            
            # 定期检查派系
            if step % 400 == 0 and step > 0:
                print(f"\n📍 Step {step}:")
                factions = self.detect_factions()
                faction_history.append({
                    'step': step,
                    'n_factions': len(factions),
                    'factions': [list(f) for f in factions]
                })
                
                print(f"   Detected {len(factions)} factions:")
                for i, faction in enumerate(factions):
                    purposes = []
                    for aid in list(faction)[:3]:  # 只显示前3个
                        if self.agents[aid].purpose_generator:
                            p = self.agents[aid].purpose_generator.purpose_statement[:40]
                            purposes.append(p)
                    print(f"   Faction {i+1} ({len(faction)} agents): {purposes}")
        
        # 最终分析
        final_factions = self.detect_factions()
        
        # 计算派系内vs派系间合作率
        intra_faction_coop = []
        inter_faction_coop = []
        
        for pair, records in self.cooperation_records.items():
            if not records:
                continue
            
            # 检查是否在同一个派系
            same_faction = False
            for faction in final_factions:
                if pair[0] in faction and pair[1] in faction:
                    same_faction = True
                    break
            
            coop_rate = sum(1 for r in records if r['both_cooperated']) / len(records)
            
            if same_faction:
                intra_faction_coop.append(coop_rate)
            else:
                inter_faction_coop.append(coop_rate)
        
        results = {
            'config': {
                'n_agents': self.n_agents,
                'n_steps': n_steps,
                'timestamp': datetime.now().isoformat()
            },
            'faction_history': faction_history,
            'final_factions': [list(f) for f in final_factions],
            'cooperation_analysis': {
                'intra_faction_mean': np.mean(intra_faction_coop) if intra_faction_coop else 0,
                'inter_faction_mean': np.mean(inter_faction_coop) if inter_faction_coop else 0,
                'intra_faction_std': np.std(intra_faction_coop) if intra_faction_coop else 0,
                'inter_faction_std': np.std(inter_faction_coop) if inter_faction_coop else 0
            }
        }
        
        # 保存
        save_path = Path('experiments/purpose_faction_results.json')
        with open(save_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        return results
    
    def print_results(self, results: Dict):
        """打印结果"""
        print("\n" + "="*70)
        print("📊 PURPOSE FACTION ANALYSIS")
        print("="*70)
        
        final_factions = results['final_factions']
        print(f"\n🎭 Final Factions: {len(final_factions)}")
        
        for i, faction in enumerate(final_factions):
            print(f"\n  Faction {i+1}: {len(faction)} agents")
            # 显示这个派系的共同Purpose特征
            purposes = []
            for aid in faction[:3]:
                if self.agents[aid].purpose_generator:
                    summary = self.agents[aid].get_purpose_summary()
                    purposes.append(summary.get('dominant_dimension', 'Unknown'))
            print(f"    Dominant purposes: {set(purposes)}")
        
        coop = results['cooperation_analysis']
        print(f"\n🤝 Cooperation Patterns:")
        print(f"  Within factions: {coop['intra_faction_mean']:.2%} ± {coop['intra_faction_std']:.2%}")
        print(f"  Across factions: {coop['inter_faction_mean']:.2%} ± {coop['inter_faction_std']:.2%}")
        
        if coop['intra_faction_mean'] > coop['inter_faction_mean']:
            diff = coop['intra_faction_mean'] - coop['inter_faction_mean']
            print(f"\n  → INTRA-FACTION BIAS: +{diff:.2%} more cooperation within factions")
        
        print(f"\n✅ Hypothesis H3 (Purpose Factions): ", end="")
        if len(final_factions) > 1 and coop['intra_faction_mean'] > coop['inter_faction_mean']:
            print("SUPPORTED")
            print(f"   Multiple factions formed with preferential in-group cooperation")
        elif len(final_factions) > 1:
            print("PARTIALLY SUPPORTED")
            print(f"   Factions formed but cooperation patterns need further analysis")
        else:
            print("NOT SUPPORTED (or needs longer simulation)")
            print(f"   Only 1 or 0 factions detected")
        
        print("="*70)


if __name__ == "__main__":
    print("="*70)
    print("🚀 MOSS v3.1 - Phase 3: Purpose Faction Formation")
    print("="*70)
    
    experiment = PurposeFactionExperiment(n_agents=12)
    results = experiment.run(n_steps=2000)
    experiment.print_results(results)
    
    print("\n✓ Phase 3 experiment complete!")
    print("="*70)
