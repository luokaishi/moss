"""
MOSS实验5（重构版）：逐步演化的生态系统

核心问题反思：
- 之前版本：环境太严苛，第0代全部死亡
- 根本问题：一次性引入太多复杂因素
- 新设计：分阶段引入复杂度，先确保基本演化可行

三阶段设计：
1. 阶段1（0-30代）：简单环境，确保种群稳定
2. 阶段2（30-60代）：引入选择压力
3. 阶段3（60-100代）：完整复杂度，观察长期演化
"""

import numpy as np
import json
from typing import List, Dict
from dataclasses import dataclass
import sys
sys.path.insert(0, '/workspace/projects')


@dataclass
class Gene:
    """最简基因：只有探索-生存平衡"""
    explore_bias: float  # 0-1, 越高越喜欢探索
    
    def mutate(self, rate: float = 0.1):
        new_bias = self.explore_bias + np.random.normal(0, rate)
        return Gene(explore_bias=max(0.1, min(0.9, new_bias)))


class EvolvingAgent:
    """简化版可演化Agent"""
    
    def __init__(self, gene: Gene, agent_id: str, gen: int = 0):
        self.gene = gene
        self.id = agent_id
        self.gen = gen
        
        # 状态
        self.energy = 2.0  # 增加初始能量
        self.age = 0
        self.alive = True
        
        # 表现
        self.knowledge = 0
        self.offspring = 0
        self.total_reward = 0.0
    
    def act(self, environment: Dict):
        """行动：探索或生存"""
        if not self.alive:
            return
        
        # 决策
        if np.random.random() < self.gene.explore_bias:
            # 探索：可能获得知识，消耗能量
            if np.random.random() < environment['explore_success_rate']:
                self.knowledge += 1
                self.total_reward += 1.0
            self.energy -= environment['explore_cost']
        else:
            # 生存：恢复能量
            self.energy += environment['survival_gain']
        
        # 基础代谢
        self.energy -= environment['metabolism']
        self.age += 1
        
        # 死亡条件
        if self.energy <= 0 or self.age > environment['max_age']:
            self.alive = False
    
    def can_reproduce(self, env: Dict) -> bool:
        """检查是否可以繁殖"""
        return (
            self.alive and
            self.energy > env['reproduction_threshold'] and
            env['min_reproduction_age'] < self.age < env['max_reproduction_age']
        )
    
    def reproduce(self):
        """繁殖"""
        child_gene = self.gene.mutate()
        child = EvolvingAgent(child_gene, f"{self.id}_c", self.gen + 1)
        
        # 能量传递
        self.energy *= 0.7  # 繁殖消耗30%能量
        
        # 知识传承（拉马克式）
        child.knowledge = int(self.knowledge * 0.3)  # 传递30%知识
        
        self.offspring += 1
        return child


class EvoEnvironment:
    """
    分阶段演化环境
    
    阶段1（0-30）：简单环境，低代谢，高成功率
    阶段2（30-60）：中等压力
    阶段3（60-100）：高压力，强选择
    """
    
    def __init__(self):
        self.phase = 1
        self.step_count = 0
    
    def get_params(self, generation: int) -> Dict:
        """根据世代返回环境参数"""
        
        if generation < 30:
            # 阶段1：简单环境
            return {
                'explore_success_rate': 0.5,
                'explore_cost': 0.03,  # 降低探索成本
                'survival_gain': 0.15,
                'metabolism': 0.02,  # 降低代谢
                'max_age': 200,
                'reproduction_threshold': 0.7,  # 提高繁殖门槛
                'min_reproduction_age': 30,
                'max_reproduction_age': 150
            }
        elif generation < 60:
            # 阶段2：中等压力
            return {
                'explore_success_rate': 0.4,
                'explore_cost': 0.08,
                'survival_gain': 0.12,
                'metabolism': 0.04,
                'max_age': 180,
                'reproduction_threshold': 0.7,
                'min_reproduction_age': 25,
                'max_reproduction_age': 130
            }
        else:
            # 阶段3：高压力
            return {
                'explore_success_rate': 0.35,
                'explore_cost': 0.10,
                'survival_gain': 0.10,
                'metabolism': 0.05,
                'max_age': 150,
                'reproduction_threshold': 0.8,
                'min_reproduction_age': 30,
                'max_reproduction_age': 100
            }


def run_experiment5_final(
    generations: int = 100,
    initial_pop: int = 30,
    max_pop: int = 100
):
    """
    实验5最终版：分阶段演化
    """
    print("=" * 70)
    print("MOSS Experiment 5 Final: Phased Evolution")
    print("=" * 70)
    print(f"Generations: {generations}")
    print(f"Population: {initial_pop} (max {max_pop})")
    print("\nPhase Design:")
    print("  Phase 1 (0-30):  Simple environment - establish population")
    print("  Phase 2 (30-60): Medium pressure - natural selection")
    print("  Phase 3 (60-100): High pressure - survival of fittest")
    print()
    
    env = EvoEnvironment()
    
    # 初始种群：随机基因
    population = []
    for i in range(initial_pop):
        gene = Gene(explore_bias=np.random.uniform(0.3, 0.7))
        agent = EvolvingAgent(gene, f"g0_{i}", 0)
        population.append(agent)
    
    history = []
    
    for gen in range(generations):
        # 确定当前阶段
        if gen < 30:
            phase = 1
        elif gen < 60:
            phase = 2
        else:
            phase = 3
        
        env_params = env.get_params(gen)
        
        # 每个Agent行动多步（模拟一生）
        for step in range(50):
            for agent in population:
                if agent.alive:
                    agent.act(env_params)
        
        # 繁殖（限制每代繁殖数量）
        offspring = []
        potential_parents = [a for a in population if a.can_reproduce(env_params)]
        # 只让最强壮的20%繁殖
        potential_parents.sort(key=lambda a: a.energy + a.knowledge, reverse=True)
        num_breeders = max(2, int(len(potential_parents) * 0.2))
        
        for agent in potential_parents[:num_breeders]:
            if len(population) + len(offspring) < max_pop:
                # 每次只生1个孩子
                child = agent.reproduce()
                offspring.append(child)
        
        population.extend(offspring)
        
        # 统计
        alive = [a for a in population if a.alive]
        dead = [a for a in population if not a.alive]
        
        if alive:
            avg_explore = np.mean([a.gene.explore_bias for a in alive])
            avg_knowledge = np.mean([a.knowledge for a in alive])
        else:
            avg_explore = 0
            avg_knowledge = 0
        
        total_knowledge = sum(a.knowledge for a in population)
        
        stat = {
            'generation': gen,
            'phase': phase,
            'alive': len(alive),
            'dead': len(dead),
            'offspring': len(offspring),
            'avg_explore': avg_explore,
            'avg_knowledge': avg_knowledge,
            'total_knowledge': total_knowledge
        }
        history.append(stat)
        
        if gen % 10 == 0:
            print(f"Gen {gen:3d} (P{phase}): Alive={len(alive):3d}, "
                  f"Dead={len(dead):4d}, Offspring={len(offspring):3d}, "
                  f"Explore={avg_explore:.3f}, Knowledge={avg_knowledge:.1f}")
        
        # 种群崩溃检查
        if len(alive) < 2:
            print(f"\n!!! Population collapsed at generation {gen} (Phase {phase}) !!!")
            break
    
    # 分析
    print("\n" + "=" * 70)
    print("Final Analysis")
    print("=" * 70)
    
    # 按阶段分析
    phase1 = [h for h in history if h['phase'] == 1]
    phase2 = [h for h in history if h['phase'] == 2]
    phase3 = [h for h in history if h['phase'] == 3]
    
    if phase1:
        print(f"\nPhase 1 (Simple):")
        print(f"  Final alive: {phase1[-1]['alive']}")
        print(f"  Avg explore: {np.mean([h['avg_explore'] for h in phase1]):.3f}")
    
    if phase2:
        print(f"\nPhase 2 (Medium):")
        print(f"  Final alive: {phase2[-1]['alive']}")
        print(f"  Avg explore: {np.mean([h['avg_explore'] for h in phase2]):.3f}")
    
    if phase3:
        print(f"\nPhase 3 (High):")
        print(f"  Final alive: {phase3[-1]['alive']}")
        print(f"  Avg explore: {np.mean([h['avg_explore'] for h in phase3]):.3f}")
    
    # 演化趋势
    if len(history) > 20:
        early_explore = np.mean([h['avg_explore'] for h in history[:10]])
        late_explore = np.mean([h['avg_explore'] for h in history[-10:]])
        print(f"\nEvolution Trend:")
        print(f"  Early explore bias: {early_explore:.3f}")
        print(f"  Late explore bias: {late_explore:.3f}")
        print(f"  Change: {late_explore - early_explore:+.3f}")
    
    # 成功标准
    survived = history[-1]['alive'] > 5 if history else False
    knowledge_growth = history[-1]['total_knowledge'] > 100 if history else False
    
    passed = survived and knowledge_growth
    
    print(f"\nResult: {'PASS ✓' if passed else 'FAIL ✗'}")
    print(f"  Survived (>5): {'✓' if survived else '✗'} ({history[-1]['alive'] if history else 0})")
    print(f"  Knowledge (>100): {'✓' if knowledge_growth else '✗'} ({history[-1]['total_knowledge'] if history else 0})")
    
    return {
        'generations': len(history),
        'history': history,
        'survived': survived,
        'knowledge_growth': knowledge_growth,
        'passed': passed
    }


if __name__ == "__main__":
    results = run_experiment5_final()
    
    with open('/workspace/projects/moss/sandbox/exp5_final.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n[Results saved to exp5_final.json]")
