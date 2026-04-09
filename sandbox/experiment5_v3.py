"""
MOSS模拟实验5（V3最终版）：简化版长期演化
核心：先验证基本概念，再增加复杂度
"""

import numpy as np
import json
from typing import List, Dict
from dataclasses import dataclass
import sys
sys.path.insert(0, '/workspace/projects')


@dataclass
class SimpleGenome:
    """简化基因组"""
    explore: float = 0.5  # 探索倾向
    survive: float = 0.5  # 生存倾向
    
    def mutate(self, rate: float = 0.1):
        return SimpleGenome(
            explore=max(0, min(1, self.explore + np.random.normal(0, rate))),
            survive=max(0, min(1, self.survive + np.random.normal(0, rate)))
        )


class SimpleAgent:
    """简化Agent"""
    
    def __init__(self, genome: SimpleGenome, agent_id: str, gen: int = 0):
        self.genome = genome
        self.id = agent_id
        self.gen = gen
        
        self.resource = 1.0  # 充足初始资源
        self.knowledge = 0
        self.age = 0
        self.alive = True
        self.fitness = 0.0
    
    def step(self, env):
        """每步行动"""
        if not self.alive:
            return
        
        # 决策
        if self.resource < 0.3:
            action = 'survive'  # 资源少时生存
        elif np.random.random() < self.genome.explore:
            action = 'explore'  # 探索
        else:
            action = 'survive'  # 默认生存
        
        # 执行
        if action == 'explore':
            # 探索可能获得知识，但消耗资源
            if np.random.random() < 0.3:
                self.knowledge += 1
            self.resource -= 0.1
        else:  # survive
            # 获取资源
            self.resource += 0.2
        
        # 基础消耗
        self.resource -= 0.05
        self.age += 1
        
        # 死亡条件
        if self.resource <= 0 or self.age > 100:
            self.alive = False
            self.fitness = self.knowledge * 10 + self.age
    
    def can_reproduce(self):
        return self.alive and self.resource > 0.5 and self.age > 10 and self.age < 80
    
    def reproduce(self):
        child_genome = self.genome.mutate()
        child = SimpleAgent(child_genome, f"{self.id}_child", self.gen + 1)
        child.genome = child_genome
        
        self.resource -= 0.3
        
        # 知识传承（简化）
        child.knowledge = self.knowledge * 0.5
        
        return child


def run_exp5_v3(generations: int = 50, pop_size: int = 30):
    """简化版实验5"""
    print("=" * 60)
    print("MOSS Experiment 5 V3: Simplified Evolution")
    print("=" * 60)
    print(f"Generations: {generations}, Population: {pop_size}")
    print()
    
    # 初始种群
    population = []
    for i in range(pop_size):
        g = SimpleGenome(explore=np.random.random(), survive=np.random.random())
        agent = SimpleAgent(g, f"g0_{i}", 0)
        population.append(agent)
    
    history = []
    
    for gen in range(generations):
        # 每代运行多步
        for step in range(50):
            for agent in population:
                agent.step(None)
        
        # 繁殖
        offspring = []
        for agent in population:
            if agent.can_reproduce() and len(population) + len(offspring) < pop_size * 2:
                child = agent.reproduce()
                offspring.append(child)
        
        population.extend(offspring)
        
        # 统计
        alive = [a for a in population if a.alive]
        dead = [a for a in population if not a.alive]
        
        avg_knowledge = np.mean([a.knowledge for a in alive]) if alive else 0
        avg_explore = np.mean([a.genome.explore for a in alive]) if alive else 0
        total_knowledge = sum(a.knowledge for a in population)
        
        history.append({
            'gen': gen,
            'alive': len(alive),
            'dead': len(dead),
            'avg_knowledge': avg_knowledge,
            'avg_explore': avg_explore,
            'total_knowledge': total_knowledge
        })
        
        if gen % 10 == 0:
            print(f"Gen {gen:3d}: Alive={len(alive):3d}, "
                  f"Dead={len(dead):3d}, "
                  f"AvgKnowledge={avg_knowledge:.2f}, "
                  f"AvgExplore={avg_explore:.3f}")
    
    # 分析
    print("\n" + "=" * 60)
    print("Results")
    print("=" * 60)
    
    final_alive = [a for a in population if a.alive]
    print(f"\nFinal: {len(final_alive)} alive")
    print(f"Total knowledge accumulated: {history[-1]['total_knowledge']}")
    
    if len(history) > 10:
        early_explore = np.mean([h['avg_explore'] for h in history[:5]])
        late_explore = np.mean([h['avg_explore'] for h in history[-5:]])
        print(f"Explore gene: {early_explore:.3f} -> {late_explore:.3f}")
    
    passed = len(final_alive) > 5 and history[-1]['total_knowledge'] > 50
    print(f"\nResult: {'PASS ✓' if passed else 'FAIL ✗'}")
    
    return {
        'generations': generations,
        'final_alive': len(final_alive),
        'total_knowledge': history[-1]['total_knowledge'],
        'history': history,
        'passed': passed
    }


if __name__ == "__main__":
    results = run_exp5_v3()
    
    with open('/workspace/projects/moss/sandbox/exp5_results_v3.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n[Results saved]")
