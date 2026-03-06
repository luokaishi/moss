"""
MOSS实验5（能量版）：纯能量驱动的演化

核心改变：
- 移除年龄限制，只用能量决定生死
- 能量通过行动获得/消耗
- 繁殖消耗大量能量
"""

import numpy as np
import json
from typing import List
from dataclasses import dataclass
import sys
sys.path.insert(0, '/workspace/projects')


@dataclass
class EnergyGene:
    """基因：探索倾向"""
    explore: float
    
    def mutate(self):
        return EnergyGene(explore=max(0.05, min(0.95, self.explore + np.random.normal(0, 0.08))))


class EnergyAgent:
    """能量驱动Agent"""
    
    def __init__(self, gene: EnergyGene, agent_id: str, gen: int = 0):
        self.gene = gene
        self.id = agent_id
        self.gen = gen
        
        self.energy = 10.0  # 充足初始能量
        self.alive = True
        self.knowledge = 0
        self.children = 0
    
    def step(self):
        """单步：选择行动，更新能量"""
        if not self.alive:
            return
        
        # 决策
        if np.random.random() < self.gene.explore:
            # 探索：高风险高回报
            success = np.random.random() < 0.5
            if success:
                self.knowledge += 1
                self.energy += 2.0  # 探索成功获得能量
            else:
                self.energy -= 0.5  # 探索失败损失能量
        else:
            # 生存：稳定收益
            self.energy += 0.8  # 稳定获得能量
        
        # 基础消耗
        self.energy -= 0.3
        
        # 死亡检查
        if self.energy <= 0:
            self.alive = False
    
    def can_reproduce(self) -> bool:
        """能量充足才能繁殖"""
        return self.alive and self.energy > 8.0 and self.children < 3
    
    def reproduce(self):
        """繁殖：消耗大量能量"""
        child_gene = self.gene.mutate()
        child = EnergyAgent(child_gene, f"{self.id}_c{self.children}", self.gen + 1)
        
        # 繁殖成本：父母损失能量，子女获得初始能量
        self.energy -= 6.0  # 高成本
        self.children += 1
        
        # 传承部分知识
        child.knowledge = int(self.knowledge * 0.3)
        
        return child


def run_energy_evolution(
    generations: int = 100,
    initial_pop: int = 10,
    max_pop: int = 50
):
    """能量驱动演化"""
    print("=" * 70)
    print("MOSS Experiment 5 (Energy-Based): Pure Energy-Driven Evolution")
    print("=" * 70)
    print(f"Generations: {generations}")
    print(f"Population: {initial_pop} (max {max_pop})")
    print("Mechanism: Energy governs all - survival, reproduction, inheritance")
    print()
    
    # 初始种群
    population = []
    for i in range(initial_pop):
        gene = EnergyGene(explore=np.random.uniform(0.2, 0.8))
        agent = EnergyAgent(gene, f"g0_{i}", 0)
        population.append(agent)
    
    history = []
    
    for gen in range(generations):
        # 每代运行多步
        for step in range(20):
            for agent in population:
                if agent.alive:
                    agent.step()
        
        # 统计
        alive = [a for a in population if a.alive]
        dead = [a for a in population if not a.alive]
        
        # 繁殖
        offspring = []
        potential_parents = [a for a in alive if a.can_reproduce()]
        
        # 按能量排序，让能量多的先繁殖
        potential_parents.sort(key=lambda a: a.energy, reverse=True)
        
        for parent in potential_parents:
            if len(population) + len(offspring) < max_pop:
                child = parent.reproduce()
                offspring.append(child)
            else:
                break
        
        population.extend(offspring)
        
        # 记录
        if alive:
            avg_explore = np.mean([a.gene.explore for a in alive])
            avg_energy = np.mean([a.energy for a in alive])
            avg_knowledge = np.mean([a.knowledge for a in alive])
        else:
            avg_explore = avg_energy = avg_knowledge = 0
        
        total_knowledge = sum(a.knowledge for a in population)
        
        history.append({
            'gen': gen,
            'alive': len(alive),
            'dead': len(dead),
            'offspring': len(offspring),
            'avg_explore': avg_explore,
            'avg_energy': avg_energy,
            'avg_knowledge': avg_knowledge,
            'total_knowledge': total_knowledge
        })
        
        if gen % 10 == 0:
            print(f"Gen {gen:3d}: Alive={len(alive):3d}, Dead={len(dead):3d}, "
                  f"Born={len(offspring):2d}, Explore={avg_explore:.3f}, "
                  f"Energy={avg_energy:.2f}, Know={avg_knowledge:.1f}")
        
        # 如果种群太少，注入新血
        if len(alive) < 3:
            print(f"  [Low population] Adding 3 new agents")
            for i in range(3):
                gene = EnergyGene(explore=np.random.uniform(0.3, 0.7))
                new_agent = EnergyAgent(gene, f"new_{gen}_{i}", gen)
                population.append(new_agent)
    
    # 结果
    print("\n" + "=" * 70)
    print("Final Results")
    print("=" * 70)
    
    final_alive = [a for a in population if a.alive]
    print(f"\nFinal: {len(final_alive)} agents alive")
    print(f"Total knowledge: {history[-1]['total_knowledge']}")
    
    # 演化趋势
    if len(history) > 20:
        mid_point = len(history) // 2
        early_explore = np.mean([h['avg_explore'] for h in history[:mid_point] if h['alive'] > 0])
        late_explore = np.mean([h['avg_explore'] for h in history[mid_point:] if h['alive'] > 0])
        
        print(f"\nEvolution:")
        print(f"  Early explore: {early_explore:.3f}")
        print(f"  Late explore:  {late_explore:.3f}")
        if early_explore > 0:
            change = (late_explore - early_explore) / early_explore * 100
            print(f"  Change: {change:+.1f}%")
    
    # 成功标准
    passed = len(final_alive) >= 5 and history[-1]['total_knowledge'] > 50
    
    print(f"\nResult: {'PASS ✓' if passed else 'FAIL ✗'}")
    print(f"  Population >= 5: {'✓' if len(final_alive) >= 5 else '✗'} ({len(final_alive)})")
    print(f"  Knowledge > 50: {'✓' if history[-1]['total_knowledge'] > 50 else '✗'} ({history[-1]['total_knowledge']})")
    
    return {
        'generations': generations,
        'final_alive': len(final_alive),
        'total_knowledge': history[-1]['total_knowledge'],
        'history': history,
        'passed': passed
    }


if __name__ == "__main__":
    results = run_energy_evolution()
    
    with open('/workspace/projects/moss/sandbox/exp5_energy.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n[Results saved to exp5_energy.json]")
