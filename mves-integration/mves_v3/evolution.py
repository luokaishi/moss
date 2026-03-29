#!/usr/bin/env python3
"""
MVES v3 - 演化引擎
核心：选择、繁殖、变异
"""

import random
import os
import shutil

class Evolution:
    def __init__(self):
        self.self_modify_rate = 0.1  # 10% 概率自修改
        self.mutation_rate = 0.15    # 15% 概率额外变异
    
    def should_self_modify(self):
        return random.random() < self.self_modify_rate
    
    def should_mutate(self):
        return random.random() < self.mutation_rate
    
    def select_for_reproduction(self, agents, n=1):
        """
        选择最适合的 agent 进行繁殖
        使用轮盘赌选择（适应度越高，概率越大）
        """
        if not agents:
            return None
        
        # 计算总适应度
        fitnesses = [a.get_fitness() for a in agents]
        total_fitness = sum(fitnesses)
        
        if total_fitness <= 0:
            return random.choice(agents)
        
        # 轮盘赌选择
        selected = []
        for _ in range(n):
            r = random.random() * total_fitness
            cumulative = 0
            for i, fitness in enumerate(fitnesses):
                cumulative += fitness
                if r <= cumulative:
                    selected.append(agents[i])
                    break
        
        return selected[0] if len(selected) == 1 else selected
    
    def cull_weakest(self, agents, n=1):
        """
        淘汰最弱的 agent（当种群过大时）
        """
        if len(agents) <= n:
            return []
        
        # 按适应度排序
        sorted_agents = sorted(agents, key=lambda a: a.get_fitness())
        
        # 淘汰最弱的 n 个
        culled = sorted_agents[:n]
        remaining = sorted_agents[n:]
        
        # 删除被淘汰的 agent
        for agent in culled:
            self._delete_agent(agent)
        
        return culled
    
    def _delete_agent(self, agent):
        """删除 agent 及其文件"""
        try:
            shutil.rmtree(agent.agent_dir)
        except:
            pass
    
    def introduce_variation(self, agent):
        """
        引入变异
        返回：是否成功变异
        """
        if self.should_mutate():
            return agent.self_modify()
        return False
    
    def get_population_stats(self, agents):
        """获取群体统计信息"""
        if not agents:
            return {
                "count": 0,
                "avg_energy": 0,
                "avg_fitness": 0,
                "avg_mutations": 0,
                "total_offspring": 0
            }
        
        energies = [a.state["energy"] for a in agents]
        fitnesses = [a.get_fitness() for a in agents]
        mutations = [a.genome["mutation_count"] for a in agents]
        offspring = [a.state["offspring_count"] for a in agents]
        
        return {
            "count": len(agents),
            "avg_energy": sum(energies) / len(energies),
            "avg_fitness": sum(fitnesses) / len(fitnesses),
            "avg_mutations": sum(mutations) / len(mutations),
            "total_offspring": sum(offspring),
            "min_energy": min(energies),
            "max_energy": max(energies),
            "min_fitness": min(fitnesses),
            "max_fitness": max(fitnesses)
        }
