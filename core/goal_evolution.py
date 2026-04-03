#!/usr/bin/env python3
"""
MOSS v5.6 - Goal Evolution Engine
目标演化引擎

核心功能:
- 目标变异算子
- 自然选择机制
- 适应性评估
- 代际演化追踪

Author: MOSS Project
Date: 2026-04-03
Version: 5.6.0-dev
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from core.open_ended_goals import Goal, GoalType, GoalPriority


@dataclass
class GoalMutation:
    """目标变异"""
    mutation_type: str  # 'skill_adjust', 'priority_change', 'description_evolve'
    magnitude: float  # 变异幅度 0-1
    timestamp: datetime = field(default_factory=datetime.now)
    
    def apply(self, goal: Goal) -> Goal:
        """应用变异"""
        if self.mutation_type == 'skill_adjust':
            # 调整目标描述中的技能要求
            goal.description = goal.description.replace(
                'optimization', 'deep_learning', 1
            )
        elif self.mutation_type == 'priority_change':
            # 调整优先级
            priorities = list(GoalPriority)
            current_idx = priorities.index(goal.priority)
            new_idx = np.clip(current_idx + np.random.randint(-1, 2), 0, len(priorities)-1)
            goal.priority = priorities[new_idx]
        elif self.mutation_type == 'description_evolve':
            # 描述演化
            goal.description += " (enhanced)"
        
        return goal


class GoalEvolution:
    """
    目标演化引擎
    
    实现达尔文演化机制
    """
    
    def __init__(self, population_size: int = 50):
        self.population_size = population_size
        self.goals: List[Goal] = []
        self.generations: List[List[Goal]] = []
        self.fitness_history: List[float] = []
        
        self.stats = {
            'generations': 0,
            'mutations': 0,
            'selections': 0,
            'best_fitness': 0.0
        }
    
    def initialize_population(self, base_goals: List[Goal]):
        """初始化种群"""
        self.goals = base_goals.copy()
        self.generations.append(self.goals.copy())
    
    def calculate_fitness(self, goal: Goal) -> float:
        """
        计算适应度
        
        基于:
        - 内在价值 (40%)
        - 外在价值 (30%)
        - 对齐度 (30%)
        """
        fitness = (
            goal.intrinsic_value * 0.4 +
            goal.extrinsic_value * 0.3 +
            goal.alignment_score * 0.3
        )
        return fitness
    
    def select(self, tournament_size: int = 5) -> Goal:
        """
        锦标赛选择
        
        Args:
            tournament_size: 锦标赛规模
        """
        # 随机选择 tournament_size 个个体
        contestants = np.random.choice(
            self.goals, 
            size=min(tournament_size, len(self.goals)), 
            replace=False
        )
        
        # 选择适应度最高的
        winner = max(contestants, key=self.calculate_fitness)
        
        self.stats['selections'] += 1
        return winner
    
    def mutate(self, goal: Goal, mutation_rate: float = 0.1) -> Goal:
        """
        变异操作
        
        Args:
            goal: 目标个体
            mutation_rate: 变异概率
        """
        if np.random.random() > mutation_rate:
            return goal
        
        # 随机选择变异类型
        mutation_types = ['skill_adjust', 'priority_change', 'description_evolve']
        mutation_type = np.random.choice(mutation_types)
        
        # 创建变异
        mutation = GoalMutation(
            mutation_type=mutation_type,
            magnitude=np.random.uniform(0.1, 0.5)
        )
        
        # 应用变异
        mutated_goal = mutation.apply(goal)
        
        self.stats['mutations'] += 1
        return mutated_goal
    
    def crossover(self, parent1: Goal, parent2: Goal) -> Tuple[Goal, Goal]:
        """
        交叉操作
        
        交换子目标
        """
        # 创建后代
        child1 = Goal(
            description=f"{parent1.description} + {parent2.description}",
            goal_type=parent1.goal_type,
            priority=parent1.priority if np.random.random() > 0.5 else parent2.priority,
            parent_id=None,
            sub_goals=parent1.sub_goals[:len(parent1.sub_goals)//2] + 
                      parent2.sub_goals[len(parent2.sub_goals)//2:],
            intrinsic_value=(parent1.intrinsic_value + parent2.intrinsic_value) / 2,
            extrinsic_value=(parent1.extrinsic_value + parent2.extrinsic_value) / 2,
            alignment_score=(parent1.alignment_score + parent2.alignment_score) / 2
        )
        
        child2 = Goal(
            description=f"{parent2.description} + {parent1.description}",
            goal_type=parent2.goal_type,
            priority=parent2.priority if np.random.random() > 0.5 else parent1.priority,
            parent_id=None,
            sub_goals=parent2.sub_goals[:len(parent2.sub_goals)//2] + 
                      parent1.sub_goals[len(parent1.sub_goals)//2:],
            intrinsic_value=(parent1.intrinsic_value + parent2.intrinsic_value) / 2,
            extrinsic_value=(parent1.extrinsic_value + parent2.extrinsic_value) / 2,
            alignment_score=(parent1.alignment_score + parent2.alignment_score) / 2
        )
        
        return child1, child2
    
    def evolve_generation(self, mutation_rate: float = 0.1, 
                         crossover_rate: float = 0.7) -> List[Goal]:
        """
        演化一代
        
        Args:
            mutation_rate: 变异概率
            crossover_rate: 交叉概率
        """
        new_population = []
        
        # 精英保留 (保留最好的 10%)
        elite_size = max(1, int(len(self.goals) * 0.1))
        elite = sorted(self.goals, key=self.calculate_fitness, reverse=True)[:elite_size]
        new_population.extend(elite)
        
        # 生成新个体
        while len(new_population) < self.population_size:
            # 选择
            parent1 = self.select()
            parent2 = self.select()
            
            # 交叉
            if np.random.random() < crossover_rate:
                child1, child2 = self.crossover(parent1, parent2)
            else:
                child1, child2 = parent1, parent2
            
            # 变异
            child1 = self.mutate(child1, mutation_rate)
            child2 = self.mutate(child2, mutation_rate)
            
            new_population.extend([child1, child2])
        
        # 截断到种群大小
        new_population = new_population[:self.population_size]
        self.goals = new_population
        
        # 记录代数
        self.generations.append(self.goals.copy())
        self.stats['generations'] += 1
        
        # 计算这一代的平均适应度
        avg_fitness = np.mean([self.calculate_fitness(g) for g in self.goals])
        self.fitness_history.append(avg_fitness)
        
        # 更新最佳适应度
        best_fitness = max(self.calculate_fitness(g) for g in self.goals)
        if best_fitness > self.stats['best_fitness']:
            self.stats['best_fitness'] = best_fitness
        
        return self.goals
    
    def get_best_goal(self) -> Optional[Goal]:
        """获取最佳目标"""
        if not self.goals:
            return None
        return max(self.goals, key=self.calculate_fitness)
    
    def get_diversity(self) -> float:
        """计算种群多样性"""
        if len(self.goals) < 2:
            return 0.0
        
        # 基于适应度的标准差
        fitnesses = [self.calculate_fitness(g) for g in self.goals]
        return np.std(fitnesses)
    
    def get_status(self) -> Dict:
        """获取演化引擎状态"""
        return {
            'stats': self.stats,
            'population_size': len(self.goals),
            'generations': len(self.generations),
            'best_fitness': self.stats['best_fitness'],
            'avg_fitness': np.mean([self.calculate_fitness(g) for g in self.goals]) if self.goals else 0,
            'diversity': self.get_diversity(),
            'fitness_trend': self.fitness_history[-10:] if self.fitness_history else []
        }


# 测试代码
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v5.6 - Goal Evolution Engine Test")
    print("=" * 60)
    
    # 创建演化引擎
    engine = GoalEvolution(population_size=20)
    
    # 初始化种群
    print("\n1. 初始化种群...")
    base_goals = [
        Goal(description=f"Goal {i}", goal_type=GoalType.EXPLORATION)
        for i in range(10)
    ]
    engine.initialize_population(base_goals)
    print(f"   种群大小：{len(engine.goals)}")
    
    # 演化多代
    print("\n2. 演化多代...")
    for gen in range(10):
        engine.evolve_generation(mutation_rate=0.2, crossover_rate=0.8)
        
        if gen % 3 == 0:
            status = engine.get_status()
            print(f"   第{gen}代：平均适应度={status['avg_fitness']:.3f}, "
                  f"最佳适应度={status['best_fitness']:.3f}, "
                  f"多样性={status['diversity']:.3f}")
    
    # 获取最佳目标
    print("\n3. 最佳目标:")
    best = engine.get_best_goal()
    if best:
        print(f"   描述：{best.description}")
        print(f"   适应度：{engine.calculate_fitness(best):.3f}")
        print(f"   类型：{best.goal_type.value}")
    
    # 获取状态
    print("\n4. 演化引擎状态:")
    status = engine.get_status()
    print(f"   总代数：{status['generations']}")
    print(f"   变异次数：{status['stats']['mutations']}")
    print(f"   选择次数：{status['stats']['selections']}")
    print(f"   适应度趋势：{status['fitness_trend']}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)
