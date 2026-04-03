#!/usr/bin/env python3
"""
MOSS v5.6 - Cultural Transmission Engine
文化传递引擎

核心功能:
- 知识代际传递
- 社会学习算法
- 文化演化追踪
- 模因 (meme) 传播

Author: MOSS Project
Date: 2026-04-03
Version: 5.6.0-dev
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class CulturalTrait:
    """文化特质"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    fitness: float = 0.5
    frequency: float = 0.0
    generation_origin: int = 0
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'fitness': self.fitness,
            'frequency': self.frequency,
            'generation_origin': self.generation_origin
        }


@dataclass
class Agent:
    """文化传递 Agent"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    traits: List[CulturalTrait] = field(default_factory=list)
    generation: int = 0
    fitness: float = 0.5
    
    def get_trait_names(self) -> List[str]:
        return [t.name for t in self.traits]


class CulturalTransmission:
    """
    文化传递引擎
    
    实现文化演化和代际传递
    """
    
    def __init__(self, population_size: int = 20, 
                 generations: int = 10):
        self.population_size = population_size
        self.generations = generations
        
        self.population: List[Agent] = []
        self.cultural_pool: List[CulturalTrait] = []
        self.generation_history: List[List[Agent]] = []
        self.trait_frequency_history: List[Dict] = []
        
        self.stats = {
            'current_generation': 0,
            'total_traits': 0,
            'cultural_diversity': 0.0,
            'transmission_events': 0
        }
    
    def initialize_population(self, n_initial_traits: int = 5):
        """初始化种群"""
        # 创建初始文化特质池
        trait_templates = [
            ("cooperation", "Cooperative behavior"),
            ("competition", "Competitive strategy"),
            ("sharing", "Knowledge sharing"),
            ("innovation", "Innovative thinking"),
            ("tradition", "Traditional values"),
            ("efficiency", "Efficiency optimization"),
            ("curiosity", "Curiosity driven"),
            ("caution", "Risk aversion")
        ]
        
        for i, (name, desc) in enumerate(trait_templates[:n_initial_traits]):
            trait = CulturalTrait(
                name=name,
                description=desc,
                fitness=np.random.uniform(0.4, 0.8),
                generation_origin=0
            )
            self.cultural_pool.append(trait)
        
        # 创建初始 Agent 种群
        for i in range(self.population_size):
            agent = Agent(generation=0)
            # 随机分配 2-4 个文化特质
            n_traits = np.random.randint(2, min(5, len(self.cultural_pool) + 1))
            agent.traits = list(np.random.choice(
                self.cultural_pool, 
                size=n_traits, 
                replace=False
            ))
            agent.fitness = np.mean([t.fitness for t in agent.traits])
            self.population.append(agent)
        
        self.generation_history.append(self.population.copy())
        self.stats['total_traits'] = len(self.cultural_pool)
    
    def social_learning(self, learner: Agent, teacher: Agent):
        """
        社会学习
        
        Learner 从 Teacher 学习文化特质
        """
        # 从 Teacher 随机选择一个特质
        if not teacher.traits:
            return
        
        trait_to_learn = np.random.choice(teacher.traits)
        
        # 检查 Learner 是否已有该特质
        learner_trait_names = learner.get_trait_names()
        
        if trait_to_learn.name not in learner_trait_names:
            # 学习新特质
            learner.traits.append(trait_to_learn)
            self.stats['transmission_events'] += 1
        else:
            # 强化已有特质 (提高 fitness)
            for trait in learner.traits:
                if trait.name == trait_to_learn.name:
                    trait.fitness = min(1.0, trait.fitness + 0.05)
    
    def run_generation(self, mutation_rate: float = 0.05):
        """运行一代文化演化"""
        current_gen = self.stats['current_generation']
        
        # 1. 计算特质频率
        trait_counts = {}
        for agent in self.population:
            for trait in agent.traits:
                trait_counts[trait.id] = trait_counts.get(trait.id, 0) + 1
        
        for trait in self.cultural_pool:
            trait.frequency = trait_counts.get(trait.id, 0) / len(self.population)
        
        # 2. 社会学习阶段
        for learner in self.population:
            # 选择 fitness 最高的 Agent 作为 Teacher
            teacher = max(self.population, key=lambda a: a.fitness)
            if teacher.id != learner.id:
                self.social_learning(learner, teacher)
        
        # 3. 自然选择 (淘汰低 fitness Agent)
        self.population.sort(key=lambda a: a.fitness, reverse=True)
        survival_rate = 0.8
        n_survivors = int(len(self.population) * survival_rate)
        survivors = self.population[:n_survivors]
        
        # 4. 繁殖新 Agent
        new_agents = []
        while len(new_agents) + len(survivors) < self.population_size:
            # 选择两个父母
            parent1 = np.random.choice(survivors)
            parent2 = np.random.choice(survivors)
            
            # 后代继承父母特质
            child = Agent(generation=current_gen + 1)
            child.traits = list(set(parent1.traits + parent2.traits))
            
            # 变异
            if np.random.random() < mutation_rate and self.cultural_pool:
                new_trait = np.random.choice(self.cultural_pool)
                if new_trait.name not in child.get_trait_names():
                    child.traits.append(new_trait)
            
            child.fitness = np.mean([t.fitness for t in child.traits])
            new_agents.append(child)
        
        # 更新种群
        self.population = survivors + new_agents
        
        # 记录历史
        self.generation_history.append(self.population.copy())
        self.stats['current_generation'] += 1
        
        # 记录特质频率
        freq_record = {t.name: t.frequency for t in self.cultural_pool}
        self.trait_frequency_history.append(freq_record)
        
        # 更新多样性
        self.stats['cultural_diversity'] = self.calculate_diversity()
    
    def calculate_diversity(self) -> float:
        """计算文化多样性"""
        if not self.cultural_pool:
            return 0.0
        
        frequencies = [t.frequency for t in self.cultural_pool]
        # Shannon diversity index
        frequencies = [f for f in frequencies if f > 0]
        if not frequencies:
            return 0.0
        
        diversity = -sum(f * np.log(f) for f in frequencies)
        max_diversity = np.log(len(frequencies))
        
        return diversity / max_diversity if max_diversity > 0 else 0
    
    def run_simulation(self, mutation_rate: float = 0.05):
        """运行完整模拟"""
        print(f"\n🚀 开始文化传递模拟...")
        print(f"   种群大小：{self.population_size}")
        print(f"   代数：{self.generations}")
        print(f"   突变率：{mutation_rate}")
        
        for gen in range(self.generations):
            self.run_generation(mutation_rate)
            
            if gen % 3 == 0:
                status = self.get_status()
                print(f"   第{gen}代：多样性={status['cultural_diversity']:.3f}, "
                      f"平均适应度={status['avg_fitness']:.3f}, "
                      f"传递事件={status['stats']['transmission_events']}")
    
    def get_status(self) -> Dict:
        """获取引擎状态"""
        avg_fitness = np.mean([a.fitness for a in self.population]) if self.population else 0
        
        return {
            'stats': self.stats,
            'population_size': len(self.population),
            'cultural_pool_size': len(self.cultural_pool),
            'avg_fitness': avg_fitness,
            'cultural_diversity': self.stats['cultural_diversity'],
            'generations': len(self.generation_history),
            'trait_frequency_history': self.trait_frequency_history[-5:]
        }


# 测试代码
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v5.6 - Cultural Transmission Test")
    print("=" * 60)
    
    # 创建引擎
    engine = CulturalTransmission(population_size=20, generations=15)
    
    # 初始化
    print("\n1. 初始化种群...")
    engine.initialize_population(n_initial_traits=5)
    print(f"   种群大小：{len(engine.population)}")
    print(f"   文化特质数：{len(engine.cultural_pool)}")
    
    # 运行模拟
    print("\n2. 运行文化演化...")
    engine.run_simulation(mutation_rate=0.05)
    
    # 获取状态
    print("\n3. 最终状态:")
    status = engine.get_status()
    print(f"   总代数：{status['generations']}")
    print(f"   最终多样性：{status['cultural_diversity']:.3f}")
    print(f"   平均适应度：{status['avg_fitness']:.3f}")
    print(f"   传递事件：{status['stats']['transmission_events']}")
    
    # 特质频率演化
    print("\n4. 特质频率演化:")
    for trait_name in engine.trait_frequency_history[-1].keys():
        frequencies = [
            hist.get(trait_name, 0) 
            for hist in engine.trait_frequency_history
        ]
        print(f"   {trait_name}: {frequencies[0]:.2f} → {frequencies[-1]:.2f}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)
