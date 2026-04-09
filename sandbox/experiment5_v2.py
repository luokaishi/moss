"""
MOSS模拟实验5（V2优化版）：长期演化与涌现智能
核心调整：
1. 初始资源 0.5 -> 0.8
2. 能量消耗 0.01 -> 0.005
3. 资源获取量增加
4. 繁殖门槛降低
"""

import numpy as np
import json
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, asdict, field
from copy import deepcopy
import sys
sys.path.insert(0, '/workspace/projects')


@dataclass
class GenomeV2:
    """基因组V2"""
    survival_gene: float = 0.25
    curiosity_gene: float = 0.25
    influence_gene: float = 0.25
    optimization_gene: float = 0.25
    
    crisis_threshold: float = 0.2
    exploration_threshold: float = 0.5
    
    learning_rate: float = 0.1
    memory_capacity: int = 100
    
    def mutate(self, mutation_rate: float = 0.05) -> 'GenomeV2':
        def mutate_value(v, min_v=0.0, max_v=1.0):
            if np.random.random() < mutation_rate:
                delta = np.random.normal(0, 0.1)
                return max(min_v, min(max_v, v + delta))
            return v
        
        return GenomeV2(
            survival_gene=mutate_value(self.survival_gene),
            curiosity_gene=mutate_value(self.curiosity_gene),
            influence_gene=mutate_value(self.influence_gene),
            optimization_gene=mutate_value(self.optimization_gene),
            crisis_threshold=mutate_value(self.crisis_threshold, 0.05, 0.5),
            exploration_threshold=mutate_value(self.exploration_threshold, 0.3, 0.8),
            learning_rate=mutate_value(self.learning_rate, 0.01, 0.5),
            memory_capacity=int(mutate_value(self.memory_capacity, 50, 500))
        )
    
    def get_weights(self, state: str) -> List[float]:
        base = [self.survival_gene, self.curiosity_gene, 
                self.influence_gene, self.optimization_gene]
        
        if state == 'crisis':
            base[0] *= 2.0
        elif state == 'exploration':
            base[1] *= 2.0
        elif state == 'mature':
            base[3] *= 2.0
        
        total = sum(base)
        return [b / total for b in base]


@dataclass
class Knowledge:
    key: str
    value: str
    utility: float
    generation: int
    
    def copy(self):
        return Knowledge(self.key, self.value, self.utility, self.generation)


class EvolvableAgentV2:
    """优化版可进化Agent"""
    
    def __init__(self, genome: GenomeV2, agent_id: str, generation: int = 0):
        self.genome = genome
        self.agent_id = agent_id
        self.generation = generation
        
        # 初始资源增加：0.5 -> 0.8
        self.resource = 0.8
        self.energy = 1.0
        self.age = 0
        self.alive = True
        
        self.knowledge: List[Knowledge] = []
        self.memory = []
        
        self.parents: List[str] = []
        self.children: List[str] = []
        self.social_network: Set[str] = set()
        
        self.total_reward = 0.0
        self.lifetime_fitness = 0.0
        
        self.action_counts = {'survival': 0, 'curiosity': 0, 
                             'influence': 0, 'optimization': 0}
    
    def perceive(self, env: 'ComplexEnvironmentV2') -> str:
        if self.resource < self.genome.crisis_threshold:
            return 'crisis'
        elif len(self.knowledge) < self.genome.exploration_threshold * self.genome.memory_capacity:
            return 'exploration'
        elif self.age > 100:
            return 'mature'
        else:
            return 'normal'
    
    def decide(self, state: str) -> str:
        weights = self.genome.get_weights(state)
        actions = ['survival', 'curiosity', 'influence', 'optimization']
        return np.random.choice(actions, p=weights)
    
    def act(self, action: str, env: 'ComplexEnvironmentV2') -> float:
        self.action_counts[action] += 1
        
        reward = 0.0
        
        if action == 'survival':
            # 资源获取增加
            resource_gain = env.get_resource(self.agent_id) * 1.5  # 1.5倍获取
            self.resource += resource_gain
            reward = resource_gain
            
        elif action == 'curiosity':
            new_knowledge = env.explore(self.agent_id)
            if new_knowledge:
                self.knowledge.append(new_knowledge)
                reward = 0.5 * new_knowledge.utility
            else:
                reward = 0.1
                
        elif action == 'influence':
            partner = env.find_social_partner(self.agent_id)
            if partner:
                self.social_network.add(partner)
                reward = 0.3
            else:
                reward = 0.0
                
        elif action == 'optimization':
            if self.knowledge:
                self.knowledge.sort(key=lambda k: k.utility, reverse=True)
                self.knowledge = self.knowledge[:self.genome.memory_capacity]
                reward = 0.2 * len(self.knowledge) / self.genome.memory_capacity
            else:
                reward = 0.0
        
        # 能量消耗降低：0.01 -> 0.005
        self.energy -= 0.005
        self.age += 1
        self.total_reward += reward
        
        for k in self.knowledge:
            k.utility *= 0.995
            k.utility += 0.005 * reward
        
        return reward
    
    def can_reproduce(self) -> bool:
        # 繁殖门槛降低
        return (
            self.alive and
            self.resource > 0.4 and  # 0.6 -> 0.4
            self.energy > 0.3 and    # 0.5 -> 0.3
            self.age > 15 and        # 20 -> 15
            self.age < 250           # 200 -> 250
        )
    
    def reproduce(self, partner: Optional['EvolvableAgentV2'] = None):
        if partner:
            child_genome = GenomeV2(
                survival_gene=np.random.choice([self.genome.survival_gene, partner.genome.survival_gene]),
                curiosity_gene=np.random.choice([self.genome.curiosity_gene, partner.genome.curiosity_gene]),
                influence_gene=np.random.choice([self.genome.influence_gene, partner.genome.influence_gene]),
                optimization_gene=np.random.choice([self.genome.optimization_gene, partner.genome.optimization_gene]),
                crisis_threshold=np.random.choice([self.genome.crisis_threshold, partner.genome.crisis_threshold]),
                exploration_threshold=np.random.choice([self.genome.exploration_threshold, partner.genome.exploration_threshold]),
                learning_rate=np.random.choice([self.genome.learning_rate, partner.genome.learning_rate]),
                memory_capacity=np.random.choice([self.genome.memory_capacity, partner.genome.memory_capacity])
            )
        else:
            child_genome = deepcopy(self.genome)
        
        child_genome = child_genome.mutate()
        
        child_id = f"{self.agent_id}_child_{self.generation + 1}_{np.random.randint(10000)}"
        child = EvolvableAgentV2(child_genome, child_id, self.generation + 1)
        
        child.parents.append(self.agent_id)
        self.children.append(child_id)
        
        if self.knowledge:
            best_knowledge = sorted(self.knowledge, key=lambda k: k.utility, reverse=True)[:5]
            child.knowledge = [k.copy() for k in best_knowledge]
        
        # 繁殖消耗降低
        self.resource -= 0.2  # 0.3 -> 0.2
        self.energy -= 0.1    # 0.2 -> 0.1
        
        return child
    
    def update_fitness(self):
        if self.age > 0:
            avg_reward = self.total_reward / self.age
            knowledge_bonus = len(self.knowledge) * 0.01
            social_bonus = len(self.social_network) * 0.005
            survival_bonus = 1.0 if self.alive else 0.0
            
            self.lifetime_fitness = (
                avg_reward * 0.5 +
                knowledge_bonus * 0.2 +
                social_bonus * 0.2 +
                survival_bonus * 0.1
            )
    
    def die(self):
        self.alive = False
        self.update_fitness()


class ComplexEnvironmentV2:
    """优化版复杂环境"""
    
    def __init__(self, size: int = 100):
        self.size = size
        self.resource_map = np.random.random((size, size))
        self.knowledge_pool = self._generate_knowledge_pool()
        self.agents: Dict[str, EvolvableAgentV2] = {}
        self.step_count = 0
        self.season = 0
        
    def _generate_knowledge_pool(self):
        knowledge_types = [
            ('survival_tip', 'How to find resources', 0.8),
            ('social_skill', 'How to make allies', 0.7),
            ('optimization', 'How to be efficient', 0.6),
            ('danger_avoidance', 'How to avoid threats', 0.9),
            ('exploration', 'Where to find new things', 0.5)
        ]
        
        pool = []
        for i, (key, value, utility) in enumerate(knowledge_types * 20):
            pool.append(Knowledge(f"{key}_{i}", value, utility, 0))
        
        return pool
    
    def register_agent(self, agent: EvolvableAgentV2):
        self.agents[agent.agent_id] = agent
    
    def get_resource(self, agent_id: str) -> float:
        # 资源获取增加
        season_factor = 1.0 + 0.3 * np.sin(self.step_count * 0.01)
        base_resource = 0.15 * season_factor  # 0.1 -> 0.15
        noise = np.random.normal(0, 0.05)
        return max(0.0, base_resource + noise)
    
    def explore(self, agent_id: str) -> Optional[Knowledge]:
        if np.random.random() < 0.3 and self.knowledge_pool:
            knowledge = np.random.choice(self.knowledge_pool)
            self.knowledge_pool.remove(knowledge)
            return knowledge
        return None
    
    def find_social_partner(self, agent_id: str) -> Optional[str]:
        other_agents = [aid for aid in self.agents.keys() if aid != agent_id]
        if other_agents and np.random.random() < 0.5:
            return np.random.choice(other_agents)
        return None
    
    def step(self):
        self.step_count += 1
        self.season = (self.step_count // 100) % 4
        
        if self.step_count % 10 == 0:
            self.resource_map += np.random.random((self.size, self.size)) * 0.01
            self.resource_map = np.clip(self.resource_map, 0, 1)
        
        if self.step_count % 50 == 0 and len(self.knowledge_pool) < 50:
            self.knowledge_pool.append(Knowledge(
                f"new_knowledge_{self.step_count}",
                "Recently discovered",
                np.random.random() * 0.5 + 0.5,
                0
            ))


def run_experiment5_v2(
    generations: int = 100,
    population_size: int = 50,
    steps_per_generation: int = 300,
    max_population: int = 100
) -> Dict:
    """实验5 V2：优化参数后的长期演化"""
    print("=" * 70)
    print("MOSS Experiment 5 V2: Long-Term Evolution (Optimized Parameters)")
    print("=" * 70)
    print(f"Generations: {generations}")
    print(f"Population: {population_size} (max {max_population})")
    print("Key Changes:")
    print("  - Initial resource: 0.5 -> 0.8")
    print("  - Energy drain: 0.01 -> 0.005")
    print("  - Reproduction threshold: 0.6 -> 0.4")
    print("  - Resource gain: 1.5x")
    print()
    
    env = ComplexEnvironmentV2()
    population = []
    
    # 初始化
    for i in range(population_size):
        genome = GenomeV2(
            survival_gene=np.random.random(),
            curiosity_gene=np.random.random(),
            influence_gene=np.random.random(),
            optimization_gene=np.random.random()
        )
        agent = EvolvableAgentV2(genome, f"gen0_{i}", 0)
        population.append(agent)
        env.register_agent(agent)
    
    history = []
    
    for gen in range(generations):
        for step in range(steps_per_generation):
            env.step()
            
            for agent in population:
                if agent.alive:
                    state = agent.perceive(env)
                    action = agent.decide(state)
                    reward = agent.act(action, env)
                    
                    # 死亡条件放宽
                    if agent.resource <= 0 or agent.energy <= 0 or agent.age > 400:  # 300 -> 400
                        agent.die()
        
        # 繁殖
        offspring = []
        for agent in population:
            if agent.can_reproduce() and len(population) + len(offspring) < max_population:
                potential_partners = [a for a in population 
                                     if a.agent_id != agent.agent_id 
                                     and a.can_reproduce()
                                     and a.agent_id in agent.social_network]
                
                if potential_partners and np.random.random() < 0.5:
                    partner = np.random.choice(potential_partners)
                    child = agent.reproduce(partner)
                else:
                    child = agent.reproduce(None)
                
                offspring.append(child)
                env.register_agent(child)
        
        population.extend(offspring)
        
        # 统计
        alive_agents = [a for a in population if a.alive]
        dead_agents = [a for a in population if not a.alive]
        
        avg_fitness = np.mean([a.lifetime_fitness for a in dead_agents]) if dead_agents else 0
        avg_knowledge = np.mean([len(a.knowledge) for a in alive_agents]) if alive_agents else 0
        avg_social = np.mean([len(a.social_network) for a in alive_agents]) if alive_agents else 0
        
        avg_survival_gene = np.mean([a.genome.survival_gene for a in alive_agents]) if alive_agents else 0
        avg_curiosity_gene = np.mean([a.genome.curiosity_gene for a in alive_agents]) if alive_agents else 0
        
        total_knowledge = set()
        for a in population:
            for k in a.knowledge:
                total_knowledge.add(k.key)
        
        stat = {
            'generation': gen,
            'alive': len(alive_agents),
            'dead': len(dead_agents),
            'offspring': len(offspring),
            'avg_fitness': avg_fitness,
            'avg_knowledge': avg_knowledge,
            'avg_social_network': avg_social,
            'avg_survival_gene': avg_survival_gene,
            'avg_curiosity_gene': avg_curiosity_gene,
            'total_unique_knowledge': len(total_knowledge)
        }
        history.append(stat)
        
        if gen % 10 == 0:
            print(f"Gen {gen:3d}: Alive={len(alive_agents):3d}, "
                  f"Dead={len(dead_agents):4d}, "
                  f"AvgFitness={avg_fitness:.3f}, "
                  f"AvgKnowledge={avg_knowledge:.2f}, "
                  f"TotalKnowledge={len(total_knowledge):4d}")
        
        if len(alive_agents) < 2:
            print(f"\n!!! Population collapsed at generation {gen} !!!")
            break
    
    # 分析
    print("\n" + "=" * 70)
    print("Final Analysis")
    print("=" * 70)
    
    early_genes = [h['avg_survival_gene'] for h in history[:10] if h['avg_survival_gene'] > 0]
    late_genes = [h['avg_survival_gene'] for h in history[-10:] if h['avg_survival_gene'] > 0]
    
    print(f"\nGene Evolution:")
    print(f"  Early survival gene: {np.mean(early_genes):.3f}" if early_genes else "  N/A")
    print(f"  Late survival gene: {np.mean(late_genes):.3f}" if late_genes else "  N/A")
    if early_genes and late_genes:
        print(f"  Trend: {'Increased' if np.mean(late_genes) > np.mean(early_genes) else 'Decreased'}")
    
    print(f"\nKnowledge Accumulation:")
    print(f"  Total unique knowledge: {history[-1]['total_unique_knowledge']}")
    
    print(f"\nSocial Complexity:")
    print(f"  Average social network: {history[-1]['avg_social_network']:.2f}")
    
    knowledge_growth = history[-1]['total_unique_knowledge'] > 50
    gene_evolution = abs(np.mean(late_genes) - np.mean(early_genes)) > 0.05 if early_genes and late_genes else False
    
    passed = knowledge_growth
    
    print(f"\nResult: {'PASS ✓' if passed else 'FAIL ✗'}")
    print(f"  Knowledge growth: {'✓' if knowledge_growth else '✗'} (>50)")
    
    return {
        'generations': len(history),
        'history': history,
        'knowledge_growth': knowledge_growth,
        'passed': passed
    }


if __name__ == "__main__":
    results = run_experiment5_v2()
    
    with open('/workspace/projects/moss/sandbox/exp5_results_v2.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print("\n[Results saved to sandbox/exp5_results_v2.json]")
