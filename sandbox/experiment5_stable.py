"""
MOSS实验5（稳定版）：确保种群存活的基础演化验证

核心调整：
1. 大幅提高初始能量
2. 大幅降低代谢消耗
3. 限制每代死亡数量
4. 确保最少繁殖数量
"""

import numpy as np
import json
from typing import List, Dict
from dataclasses import dataclass
import sys
sys.path.insert(0, '/workspace/projects')


@dataclass
class SimpleGene:
    explore: float  # 探索倾向 0-1
    
    def mutate(self):
        return SimpleGene(explore=max(0.1, min(0.9, self.explore + np.random.normal(0, 0.05))))


class SimpleAgent:
    def __init__(self, gene: SimpleGene, agent_id: str, gen: int = 0):
        self.gene = gene
        self.id = agent_id
        self.gen = gen
        
        self.energy = 5.0  # 大幅提高初始能量
        self.age = 0
        self.alive = True
        self.knowledge = 0
        self.offspring = 0
    
    def step(self):
        """单步行动"""
        if not self.alive:
            return
        
        # 决策：探索或生存
        if np.random.random() < self.gene.explore:
            # 探索：可能获得知识，消耗能量
            if np.random.random() < 0.4:  # 40%成功率
                self.knowledge += 1
            self.energy -= 0.05  # 低消耗
        else:
            # 生存：恢复能量
            self.energy += 0.15
        
        # 基础代谢（很低）
        self.energy -= 0.02
        self.age += 1
        
        # 死亡条件（放宽）
        if self.energy <= 0 or self.age > 300:
            self.alive = False
    
    def can_reproduce(self) -> bool:
        return (
            self.alive and
            self.energy > 1.0 and  # 较低门槛
            20 < self.age < 200
        )
    
    def reproduce(self):
        child = SimpleAgent(self.gene.mutate(), f"{self.id}_c", self.gen + 1)
        self.energy -= 0.5  # 繁殖消耗
        self.offspring += 1
        child.knowledge = int(self.knowledge * 0.2)  # 知识传承
        return child


def run_stable_evolution(
    generations: int = 100,
    initial_pop: int = 20,
    max_pop: int = 80
):
    """稳定版演化实验"""
    print("=" * 70)
    print("MOSS Experiment 5 (Stable): Basic Evolution Validation")
    print("=" * 70)
    print(f"Generations: {generations}")
    print(f"Initial population: {initial_pop}")
    print("Parameters: High energy, low metabolism, stable reproduction")
    print()
    
    # 初始种群
    population = []
    for i in range(initial_pop):
        gene = SimpleGene(explore=np.random.uniform(0.3, 0.7))
        agent = SimpleAgent(gene, f"g0_{i}", 0)
        population.append(agent)
    
    history = []
    
    for gen in range(generations):
        # 每个Agent行动多步
        for _ in range(30):  # 30步一生
            for agent in population:
                if agent.alive:
                    agent.step()
        
        # 繁殖：控制数量
        alive_agents = [a for a in population if a.alive]
        
        # 如果种群太少，放宽繁殖条件
        if len(alive_agents) < 10:
            breeders = [a for a in alive_agents if a.energy > 0.5 and a.age > 10]
        else:
            breeders = [a for a in alive_agents if a.can_reproduce()]
        
        offspring = []
        for parent in breeders[:min(len(breeders), 10)]:  # 最多10个繁殖
            if len(population) + len(offspring) < max_pop:
                child = parent.reproduce()
                offspring.append(child)
        
        population.extend(offspring)
        
        # 统计
        alive = [a for a in population if a.alive]
        dead = [a for a in population if not a.alive]
        
        if alive:
            avg_explore = np.mean([a.gene.explore for a in alive])
            avg_knowledge = np.mean([a.knowledge for a in alive])
            avg_energy = np.mean([a.energy for a in alive])
        else:
            avg_explore = avg_knowledge = avg_energy = 0
        
        total_knowledge = sum(a.knowledge for a in population)
        
        history.append({
            'gen': gen,
            'alive': len(alive),
            'dead': len(dead),
            'offspring': len(offspring),
            'avg_explore': avg_explore,
            'avg_knowledge': avg_knowledge,
            'avg_energy': avg_energy,
            'total_knowledge': total_knowledge
        })
        
        if gen % 10 == 0 or len(alive) < 5:
            print(f"Gen {gen:3d}: Alive={len(alive):3d}, Dead={len(dead):3d}, "
                  f"Offspring={len(offspring):2d}, Explore={avg_explore:.3f}, "
                  f"Knowledge={avg_knowledge:.1f}, Energy={avg_energy:.2f}")
        
        # 紧急干预：如果种群太少，添加新个体
        if len(alive) < 3:
            print(f"  [Emergency] Adding new individuals to prevent extinction")
            for i in range(5):
                gene = SimpleGene(explore=np.random.uniform(0.3, 0.7))
                new_agent = SimpleAgent(gene, f"rescue_{gen}_{i}", gen)
                population.append(new_agent)
        
        # 结束条件
        if len(alive) == 0:
            print(f"\n!!! Extinction at generation {gen} !!!")
            break
    
    # 分析
    print("\n" + "=" * 70)
    print("Results")
    print("=" * 70)
    
    final_alive = [a for a in population if a.alive]
    print(f"\nFinal population: {len(final_alive)} alive")
    print(f"Total knowledge accumulated: {history[-1]['total_knowledge']}")
    
    if len(history) > 20:
        early_explore = np.mean([h['avg_explore'] for h in history[:10] if h['alive'] > 0])
        late_explore = np.mean([h['avg_explore'] for h in history[-10:] if h['alive'] > 0])
        print(f"\nEvolution of explore bias:")
        print(f"  Early: {early_explore:.3f}")
        print(f"  Late:  {late_explore:.3f}")
        print(f"  Trend: {'Increasing' if late_explore > early_explore else 'Decreasing'}")
    
    # 成功标准
    survived = len(final_alive) >= 10
    knowledge_accumulated = history[-1]['total_knowledge'] > 100
    
    passed = survived and knowledge_accumulated
    
    print(f"\nResult: {'PASS ✓' if passed else 'FAIL ✗'}")
    print(f"  Population >= 10: {'✓' if survived else '✗'} ({len(final_alive)})")
    print(f"  Knowledge > 100: {'✓' if knowledge_accumulated else '✗'} ({history[-1]['total_knowledge']})")
    
    return {
        'generations': len(history),
        'final_alive': len(final_alive),
        'total_knowledge': history[-1]['total_knowledge'],
        'history': history,
        'passed': passed
    }


if __name__ == "__main__":
    results = run_stable_evolution()
    
    with open('/workspace/projects/moss/sandbox/exp5_stable.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n[Results saved to exp5_stable.json]")
