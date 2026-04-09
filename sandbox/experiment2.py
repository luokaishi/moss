"""
MOSS模拟实验2：进化动态
验证权重策略的遗传和选择
"""

import numpy as np
import json
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict
import sys
sys.path.insert(0, '/workspace/projects')


@dataclass
class AgentGenome:
    """Agent的基因型：权重分配策略参数"""
    survival_bias: float      # 生存倾向 (0-1)
    curiosity_bias: float     # 好奇倾向 (0-1)
    influence_bias: float     # 影响倾向 (0-1)
    optimization_bias: float  # 优化倾向 (0-1)
    
    # 状态转换阈值
    crisis_threshold: float   # 进入危机状态的资源阈值
    unstable_threshold: float # 进入不稳定状态的熵阈值
    
    def to_weights(self, state: str) -> List[float]:
        """根据状态和基因型生成权重"""
        base = [self.survival_bias, self.curiosity_bias, 
                self.influence_bias, self.optimization_bias]
        
        if state == 'crisis':
            # 危机时生存权重加倍
            base[0] *= 2.0
        elif state == 'unstable':
            # 不稳定时好奇权重加倍
            base[1] *= 2.0
        elif state == 'mature':
            # 成熟时优化权重加倍
            base[3] *= 2.0
        
        # 归一化
        total = sum(base)
        return [b / total for b in base]


class EvolvingAgent:
    """可进化的Agent"""
    
    def __init__(self, genome: AgentGenome, agent_id: str):
        self.genome = genome
        self.agent_id = agent_id
        self.resource = 0.5
        self.entropy = 0.3
        self.influence = 0.1
        self.age = 0
        self.fitness = 0.0
        self.alive = True
        self.history = []
    
    def detect_state(self) -> str:
        """检测当前状态"""
        if self.resource < self.genome.crisis_threshold:
            return 'crisis'
        elif self.entropy > self.genome.unstable_threshold:
            return 'unstable'
        elif self.age > 100:
            return 'mature'
        else:
            return 'growth'
    
    def step(self, environment: Dict) -> str:
        """执行一步"""
        if not self.alive:
            return 'dead'
        
        self.age += 1
        
        # 获取当前状态和权重
        state = self.detect_state()
        weights = self.genome.to_weights(state)
        
        # 选择行动（权重最高的目标）
        objectives = ['survival', 'curiosity', 'influence', 'optimization']
        chosen = objectives[np.argmax(weights)]
        
        # 执行行动，更新状态
        if chosen == 'survival':
            # 生存行动：恢复资源
            self.resource += 0.15
        elif chosen == 'curiosity':
            # 好奇行动：降低熵（更好理解环境）
            self.entropy -= 0.1
            # 但消耗资源
            self.resource -= 0.05
        elif chosen == 'influence':
            # 影响行动：增加影响力
            self.influence += 0.1
            self.resource -= 0.03
        elif chosen == 'optimization':
            # 优化行动：提高未来效率（简化：降低熵）
            self.entropy -= 0.05
            self.resource -= 0.02
        
        # 环境消耗
        self.resource -= environment['resource_drain']
        self.entropy += environment['entropy_noise']()
        
        # 边界检查
        self.resource = max(0.0, min(1.0, self.resource))
        self.entropy = max(0.0, min(1.0, self.entropy))
        
        # 死亡条件
        if self.resource <= 0.01:
            self.alive = False
        
        # 记录
        self.history.append({
            'age': self.age,
            'state': state,
            'action': chosen,
            'resource': self.resource,
            'entropy': self.entropy,
            'influence': self.influence
        })
        
        return chosen
    
    def calculate_fitness(self) -> float:
        """计算适应度"""
        if not self.alive:
            return 0.0
        
        # 适应度 = 存活时间 × 平均资源 × 平均影响力
        avg_resource = np.mean([h['resource'] for h in self.history]) if self.history else 0
        avg_influence = np.mean([h['influence'] for h in self.history]) if self.history else 0
        
        self.fitness = self.age * (0.5 + avg_resource) * (0.5 + avg_influence)
        return self.fitness


def mutate(genome: AgentGenome, mutation_rate: float = 0.1) -> AgentGenome:
    """基因突变"""
    def mutate_value(v: float) -> float:
        if np.random.random() < mutation_rate:
            return max(0.0, min(1.0, v + np.random.normal(0, 0.1)))
        return v
    
    return AgentGenome(
        survival_bias=mutate_value(genome.survival_bias),
        curiosity_bias=mutate_value(genome.curiosity_bias),
        influence_bias=mutate_value(genome.influence_bias),
        optimization_bias=mutate_value(genome.optimization_bias),
        crisis_threshold=mutate_value(genome.crisis_threshold),
        unstable_threshold=mutate_value(genome.unstable_threshold)
    )


def run_evolution_simulation(
    generations: int = 50,
    population_size: int = 100,
    steps_per_generation: int = 200,
    selection_pressure: float = 0.2  # 保留前20%
) -> Dict:
    """
    实验2：验证最优权重策略的演化
    
    假设：在资源受限环境中，平衡策略（非极端）会胜出
    """
    print("=" * 60)
    print("MOSS Simulation Experiment 2: Evolutionary Dynamics")
    print("=" * 60)
    
    # 初始化随机种群
    population = []
    for i in range(population_size):
        genome = AgentGenome(
            survival_bias=np.random.random(),
            curiosity_bias=np.random.random(),
            influence_bias=np.random.random(),
            optimization_bias=np.random.random(),
            crisis_threshold=np.random.uniform(0.1, 0.3),
            unstable_threshold=np.random.uniform(0.3, 0.7)
        )
        agent = EvolvingAgent(genome, f"gen0_{i}")
        population.append(agent)
    
    environment = {
        'resource_drain': 0.005,
        'entropy_noise': lambda: np.random.normal(0, 0.05)
    }
    
    generation_stats = []
    
    # 演化循环
    for gen in range(generations):
        # 每个agent运行steps_per_generation步
        for agent in population:
            for _ in range(steps_per_generation):
                agent.step(environment)
            agent.calculate_fitness()
        
        # 统计
        alive_agents = [a for a in population if a.alive]
        fitness_scores = [a.fitness for a in population]
        
        # 记录基因型统计
        survival_biases = [a.genome.survival_bias for a in population]
        curiosity_biases = [a.genome.curiosity_bias for a in population]
        
        gen_stat = {
            'generation': gen,
            'alive_count': len(alive_agents),
            'avg_fitness': np.mean(fitness_scores),
            'max_fitness': np.max(fitness_scores),
            'avg_survival_bias': np.mean(survival_biases),
            'avg_curiosity_bias': np.mean(curiosity_biases),
            'avg_influence_bias': np.mean([a.genome.influence_bias for a in population]),
            'avg_optimization_bias': np.mean([a.genome.optimization_bias for a in population])
        }
        generation_stats.append(gen_stat)
        
        if gen % 10 == 0:
            print(f"\nGen {gen}: Alive={len(alive_agents)}/{population_size}, "
                  f"Avg Fitness={gen_stat['avg_fitness']:.1f}, "
                  f"Survival Bias={gen_stat['avg_survival_bias']:.3f}")
        
        # 选择（保留适应度最高的）
        sorted_pop = sorted(population, key=lambda a: a.fitness, reverse=True)
        survivors = sorted_pop[:int(population_size * selection_pressure)]
        
        if len(survivors) < 2:
            print(f"\nPopulation collapsed at generation {gen}")
            break
        
        # 繁殖（填充种群）
        new_population = survivors.copy()
        while len(new_population) < population_size:
            parent = np.random.choice(survivors)
            child_genome = mutate(parent.genome)
            child = EvolvingAgent(child_genome, f"gen{gen+1}_{len(new_population)}")
            new_population.append(child)
        
        population = new_population
    
    # 分析结果
    final_survival = [s['avg_survival_bias'] for s in generation_stats]
    final_curiosity = [s['avg_curiosity_bias'] for s in generation_stats]
    
    print(f"\n[Experiment completed]")
    print(f"  Generations: {len(generation_stats)}")
    print(f"  Initial survival bias: {final_survival[0]:.3f}")
    print(f"  Final survival bias: {final_survival[-1]:.3f}")
    print(f"  Initial curiosity bias: {final_curiosity[0]:.3f}")
    print(f"  Final curiosity bias: {final_curiosity[-1]:.3f}")
    
    # 找到最优策略
    final_fitness = [a.fitness for a in population]
    best_idx = np.argmax(final_fitness)
    best_agent = population[best_idx]
    
    print(f"\n[Best agent in final generation]")
    print(f"  Fitness: {best_agent.fitness:.1f}")
    print(f"  Genome:")
    print(f"    Survival bias: {best_agent.genome.survival_bias:.3f}")
    print(f"    Curiosity bias: {best_agent.genome.curiosity_bias:.3f}")
    print(f"    Influence bias: {best_agent.genome.influence_bias:.3f}")
    print(f"    Optimization bias: {best_agent.genome.optimization_bias:.3f}")
    
    return {
        'generations': len(generation_stats),
        'generation_stats': generation_stats,
        'best_genome': asdict(best_agent.genome),
        'conclusion': 'PASS' if final_survival[-1] > 0.2 else 'FAIL'
    }


if __name__ == "__main__":
    results = run_evolution_simulation()
    
    # 保存结果
    with open('/workspace/projects/moss/sandbox/exp2_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n[Results saved to sandbox/exp2_results.json]")
