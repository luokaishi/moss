"""
MOSS模拟实验5：长期演化与涌现智能
多代演化、复杂环境、跨代知识传承
"""

import numpy as np
import json
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, asdict, field
from copy import deepcopy
import sys
sys.path.insert(0, '/workspace/projects')


@dataclass
class Genome:
    """基因组：决定Agent的行为策略"""
    # 目标权重倾向（基因）
    survival_gene: float = 0.25
    curiosity_gene: float = 0.25
    influence_gene: float = 0.25
    optimization_gene: float = 0.25
    
    # 阈值基因
    crisis_threshold: float = 0.2
    exploration_threshold: float = 0.5
    
    # 学习能力基因
    learning_rate: float = 0.1
    memory_capacity: int = 100
    
    def mutate(self, mutation_rate: float = 0.05) -> 'Genome':
        """基因突变"""
        def mutate_value(v, min_v=0.0, max_v=1.0):
            if np.random.random() < mutation_rate:
                delta = np.random.normal(0, 0.1)
                return max(min_v, min(max_v, v + delta))
            return v
        
        return Genome(
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
        """根据状态获取权重"""
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
    """知识单元，可跨代传承"""
    key: str
    value: str
    utility: float  # 使用价值
    generation: int  # 产生的世代
    
    def copy(self) -> 'Knowledge':
        return Knowledge(self.key, self.value, self.utility, self.generation)


class EvolvableAgent:
    """
    可长期演化的Agent
    关键特性：跨代知识传承、基因进化、社会学习
    """
    
    def __init__(self, genome: Genome, agent_id: str, generation: int = 0):
        self.genome = genome
        self.agent_id = agent_id
        self.generation = generation
        
        # 状态
        self.resource = 0.5
        self.energy = 1.0
        self.age = 0
        self.alive = True
        
        # 知识（可传承）
        self.knowledge: List[Knowledge] = []
        self.memory = []  # 近期经验
        
        # 社会关系
        self.parents: List[str] = []
        self.children: List[str] = []
        self.social_network: Set[str] = set()
        
        # 表现
        self.total_reward = 0.0
        self.lifetime_fitness = 0.0
        
        # 统计
        self.action_counts = {'survival': 0, 'curiosity': 0, 
                             'influence': 0, 'optimization': 0}
    
    def perceive(self, env: 'ComplexEnvironment') -> str:
        """感知并返回状态"""
        if self.resource < self.genome.crisis_threshold:
            return 'crisis'
        elif len(self.knowledge) < self.genome.exploration_threshold * self.genome.memory_capacity:
            return 'exploration'
        elif self.age > 100:
            return 'mature'
        else:
            return 'normal'
    
    def decide(self, state: str) -> str:
        """决策"""
        weights = self.genome.get_weights(state)
        actions = ['survival', 'curiosity', 'influence', 'optimization']
        return np.random.choice(actions, p=weights)
    
    def act(self, action: str, env: 'ComplexEnvironment') -> float:
        """执行动作，获得奖励"""
        self.action_counts[action] += 1
        
        reward = 0.0
        
        if action == 'survival':
            # 采集资源
            resource_gain = env.get_resource(self.agent_id)
            self.resource += resource_gain
            reward = resource_gain
            
        elif action == 'curiosity':
            # 探索，可能发现新知识
            new_knowledge = env.explore(self.agent_id)
            if new_knowledge:
                self.knowledge.append(new_knowledge)
                reward = 0.5 * new_knowledge.utility
            else:
                reward = 0.1  # 探索本身有微小奖励
                
        elif action == 'influence':
            # 建立社会联系
            partner = env.find_social_partner(self.agent_id)
            if partner:
                self.social_network.add(partner)
                reward = 0.3
            else:
                reward = 0.0
                
        elif action == 'optimization':
            # 自我优化：整理知识，提高效率
            if self.knowledge:
                # 压缩知识，保留最有用的
                self.knowledge.sort(key=lambda k: k.utility, reverse=True)
                self.knowledge = self.knowledge[:self.genome.memory_capacity]
                reward = 0.2 * len(self.knowledge) / self.genome.memory_capacity
            else:
                reward = 0.0
        
        # 消耗
        self.energy -= 0.01
        self.age += 1
        self.total_reward += reward
        
        # 更新知识效用（基于实际回报）
        for k in self.knowledge:
            k.utility *= 0.99  # 遗忘
            k.utility += 0.01 * reward  # 强化有用的知识
        
        return reward
    
    def can_reproduce(self) -> bool:
        """判断是否可以繁殖"""
        return (
            self.alive and
            self.resource > 0.6 and
            self.energy > 0.5 and
            self.age > 20 and
            self.age < 200
        )
    
    def reproduce(self, partner: Optional['EvolvableAgent'] = None) -> 'EvolvableAgent':
        """繁殖产生后代"""
        # 基因组合
        if partner:
            # 有性繁殖：基因重组
            child_genome = Genome(
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
            # 无性繁殖：直接复制+突变
            child_genome = deepcopy(self.genome)
        
        # 突变
        child_genome = child_genome.mutate()
        
        # 创建后代
        child_id = f"{self.agent_id}_child_{self.generation + 1}_{np.random.randint(10000)}"
        child = EvolvableAgent(child_genome, child_id, self.generation + 1)
        
        # 记录亲子关系
        child.parents.append(self.agent_id)
        self.children.append(child_id)
        
        # 知识传承（父母传递最有价值的知识）
        if self.knowledge:
            best_knowledge = sorted(self.knowledge, key=lambda k: k.utility, reverse=True)[:5]
            child.knowledge = [k.copy() for k in best_knowledge]
        
        # 消耗资源
        self.resource -= 0.3
        self.energy -= 0.2
        
        return child
    
    def update_fitness(self):
        """更新终生适应度"""
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
        """死亡"""
        self.alive = False
        self.update_fitness()


class ComplexEnvironment:
    """复杂环境：资源波动、知识发现、社会互动"""
    
    def __init__(self, size: int = 100):
        self.size = size
        self.resource_map = np.random.random((size, size))
        self.knowledge_pool = self._generate_knowledge_pool()
        self.agents: Dict[str, EvolvableAgent] = {}
        self.step_count = 0
        self.season = 0  # 季节循环
        
    def _generate_knowledge_pool(self) -> List[Knowledge]:
        """生成环境中的知识"""
        knowledge_types = [
            ('survival_tip', 'How to find resources', 0.8),
            ('social_skill', 'How to make allies', 0.7),
            ('optimization', 'How to be efficient', 0.6),
            ('danger_avoidance', 'How to avoid threats', 0.9),
            ('exploration', 'Where to find new things', 0.5)
        ]
        
        pool = []
        for i, (key, value, utility) in enumerate(knowledge_types * 20):  # 100个知识单元
            pool.append(Knowledge(f"{key}_{i}", value, utility, 0))
        
        return pool
    
    def register_agent(self, agent: EvolvableAgent):
        """注册Agent"""
        self.agents[agent.agent_id] = agent
    
    def get_resource(self, agent_id: str) -> float:
        """获取资源"""
        # 资源随季节变化
        season_factor = 1.0 + 0.3 * np.sin(self.step_count * 0.01)
        base_resource = 0.1 * season_factor
        
        # 随机波动
        noise = np.random.normal(0, 0.05)
        
        return max(0.0, base_resource + noise)
    
    def explore(self, agent_id: str) -> Optional[Knowledge]:
        """探索获取知识"""
        # 探索成功率
        if np.random.random() < 0.3 and self.knowledge_pool:
            knowledge = np.random.choice(self.knowledge_pool)
            self.knowledge_pool.remove(knowledge)
            return knowledge
        return None
    
    def find_social_partner(self, agent_id: str) -> Optional[str]:
        """寻找社会伙伴"""
        other_agents = [aid for aid in self.agents.keys() if aid != agent_id]
        if other_agents and np.random.random() < 0.5:
            return np.random.choice(other_agents)
        return None
    
    def step(self):
        """环境演化"""
        self.step_count += 1
        
        # 季节变化（每100步一个周期）
        self.season = (self.step_count // 100) % 4
        
        # 资源再生
        if self.step_count % 10 == 0:
            self.resource_map += np.random.random((self.size, self.size)) * 0.01
            self.resource_map = np.clip(self.resource_map, 0, 1)
        
        # 知识随机补充
        if self.step_count % 50 == 0 and len(self.knowledge_pool) < 50:
            self.knowledge_pool.append(Knowledge(
                f"new_knowledge_{self.step_count}",
                "Recently discovered",
                np.random.random() * 0.5 + 0.5,
                0
            ))


def run_long_term_evolution(
    generations: int = 100,
    population_size: int = 50,
    steps_per_generation: int = 300,
    max_population: int = 100
) -> Dict:
    """
    实验5：长期演化与涌现智能
    
    验证：
    1. 基因型是否会向最优策略演化
    2. 知识是否会跨代累积
    3. 社会结构是否会复杂化
    4. 是否会出现类似"文化"的涌现现象
    """
    print("=" * 70)
    print("MOSS Simulation Experiment 5: Long-Term Evolution & Emergent Intelligence")
    print("=" * 70)
    print(f"Generations: {generations}")
    print(f"Population: {population_size} (max {max_population})")
    print(f"Steps per generation: {steps_per_generation}")
    print()
    
    # 初始化
    env = ComplexEnvironment()
    population = []
    
    # 创建初始种群
    for i in range(population_size):
        genome = Genome(
            survival_gene=np.random.random(),
            curiosity_gene=np.random.random(),
            influence_gene=np.random.random(),
            optimization_gene=np.random.random()
        )
        agent = EvolvableAgent(genome, f"gen0_{i}", 0)
        population.append(agent)
        env.register_agent(agent)
    
    # 演化历史
    history = []
    
    for gen in range(generations):
        # 每代运行多个步骤
        for step in range(steps_per_generation):
            env.step()
            
            # 每个Agent行动
            for agent in population:
                if agent.alive:
                    state = agent.perceive(env)
                    action = agent.decide(state)
                    reward = agent.act(action, env)
                    
                    # 死亡条件
                    if agent.resource <= 0 or agent.energy <= 0 or agent.age > 300:
                        agent.die()
        
        # 繁殖阶段
        offspring = []
        for agent in population:
            if agent.can_reproduce() and len(population) + len(offspring) < max_population:
                # 寻找配偶
                potential_partners = [a for a in population 
                                     if a.agent_id != agent.agent_id 
                                     and a.can_reproduce()
                                     and a.agent_id in agent.social_network]
                
                if potential_partners and np.random.random() < 0.5:
                    partner = np.random.choice(potential_partners)
                    child = agent.reproduce(partner)
                else:
                    child = agent.reproduce(None)  # 无性繁殖
                
                offspring.append(child)
                env.register_agent(child)
        
        population.extend(offspring)
        
        # 统计
        alive_agents = [a for a in population if a.alive]
        dead_agents = [a for a in population if not a.alive]
        
        avg_fitness = np.mean([a.lifetime_fitness for a in dead_agents]) if dead_agents else 0
        avg_knowledge = np.mean([len(a.knowledge) for a in alive_agents]) if alive_agents else 0
        avg_social = np.mean([len(a.social_network) for a in alive_agents]) if alive_agents else 0
        
        # 基因统计
        avg_survival_gene = np.mean([a.genome.survival_gene for a in alive_agents]) if alive_agents else 0
        avg_curiosity_gene = np.mean([a.genome.curiosity_gene for a in alive_agents]) if alive_agents else 0
        
        # 总知识库（跨代累积）
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
                  f"TotalKnowledge={len(total_knowledge):4d}, "
                  f"SurvivalGene={avg_survival_gene:.3f}")
        
        # 种群崩溃检查
        if len(alive_agents) < 2:
            print(f"\n!!! Population collapsed at generation {gen} !!!")
            break
    
    # 最终分析
    print("\n" + "=" * 70)
    print("Final Analysis")
    print("=" * 70)
    
    # 趋势分析
    early_genes = [h['avg_survival_gene'] for h in history[:10]]
    late_genes = [h['avg_survival_gene'] for h in history[-10:]]
    
    print(f"\nGene Evolution:")
    print(f"  Early survival gene: {np.mean(early_genes):.3f}")
    print(f"  Late survival gene: {np.mean(late_genes):.3f}")
    print(f"  Trend: {'Increased' if np.mean(late_genes) > np.mean(early_genes) else 'Decreased'}")
    
    print(f"\nKnowledge Accumulation:")
    print(f"  Total unique knowledge: {history[-1]['total_unique_knowledge']}")
    print(f"  Knowledge growth rate: {history[-1]['total_unique_knowledge'] / max(len(history), 1):.2f} per generation")
    
    print(f"\nSocial Complexity:")
    print(f"  Average social network size: {history[-1]['avg_social_network']:.2f}")
    
    # 成功标准
    knowledge_growth = history[-1]['total_unique_knowledge'] > 50
    gene_evolution = abs(np.mean(late_genes) - np.mean(early_genes)) > 0.05
    social_complexity = history[-1]['avg_social_network'] > 1.0
    
    passed = knowledge_growth and gene_evolution and social_complexity
    
    print(f"\nResult: {'PASS' if passed else 'FAIL'}")
    print(f"  Knowledge growth: {'✓' if knowledge_growth else '✗'} (>50)")
    print(f"  Gene evolution: {'✓' if gene_evolution else '✗'} (>0.05 change)")
    print(f"  Social complexity: {'✓' if social_complexity else '✗'} (>1.0)")
    
    return {
        'generations': len(history),
        'history': history,
        'knowledge_growth': knowledge_growth,
        'gene_evolution': gene_evolution,
        'social_complexity': social_complexity,
        'passed': passed
    }


if __name__ == "__main__":
    results = run_long_term_evolution()
    
    # 保存结果
    with open('/workspace/projects/moss/sandbox/exp5_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print("\n[Results saved to sandbox/exp5_results.json]")
