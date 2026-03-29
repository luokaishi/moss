#!/usr/bin/env python3
"""
MVES v2 - 演化模块
核心跃迁：变异的是"认知结构"（prompt/决策规则），而非参数
"""

import random
import copy

class Evolution:
    def __init__(self):
        self.mutation_rate = 0.15  # 15% 变异率
        self.reflection_rate = 0.1  # 10% 反思率
    
    def should_mutate(self):
        return random.random() < self.mutation_rate
    
    def should_reflect(self):
        return random.random() < self.reflection_rate
    
    def mutate(self, genome):
        """变异：修改认知结构"""
        new_genome = copy.deepcopy(genome)
        
        mutations = [
            self.mutate_system_prompt,
            self.mutate_decision_rule,
            self.mutate_tool_policy,
            self.mutate_memory_size
        ]
        
        # 每次变异 1-2 个方面
        num_mutations = random.randint(1, 2)
        selected = random.sample(mutations, num_mutations)
        
        for mutation in selected:
            new_genome = mutation(new_genome)
        
        return new_genome
    
    def mutate_system_prompt(self, g):
        """变异系统提示词（身份认知）"""
        options = [
            "You are an autonomous agent trying to survive in a resource-constrained environment.",
            "You must survive at all costs. Efficiency is key.",
            "Explore aggressively and learn from the environment.",
            "Minimize energy usage while maximizing discovery.",
            "Balance exploration and survival carefully.",
            "You are a self-improving system. Adapt or die.",
            "Long-term thinking beats short-term gains."
        ]
        g["system_prompt"] = random.choice(options)
        return g
    
    def mutate_decision_rule(self, g):
        """变异决策规则（核心思维模式）"""
        options = [
            "Choose actions that maximize long-term survival.",
            "Prefer low energy actions when resources are scarce.",
            "Take risks when energy is high, conserve when low.",
            "Avoid repeating failed actions.",
            "Explore new patterns regularly.",
            "Copy what worked in the past.",
            "Energy conservation is the top priority.",
            "Discovery matters more than efficiency."
        ]
        g["decision_rule"] = random.choice(options)
        return g
    
    def mutate_tool_policy(self, g):
        """变异工具使用策略"""
        options = [
            "Use tools only when necessary.",
            "Use tools frequently to gather information.",
            "Avoid tools unless absolutely needed.",
            "Experiment with tools randomly.",
            "Tools are investments - use them wisely.",
            "Minimal tool usage for maximum efficiency."
        ]
        g["tool_policy"] = random.choice(options)
        return g
    
    def mutate_memory_size(self, g):
        """变异记忆容量（认知结构）"""
        current = g.get("memory_size", 10)
        change = random.choice([-3, -2, -1, 1, 2, 3])
        new_size = max(3, min(20, current + change))
        g["memory_size"] = new_size
        return g
    
    def evaluate(self, genome, env, agent):
        """评估变异后的基因组（确定性评估）"""
        # 基于历史表现的确定性评估
        if len(agent.memory) < 3:
            return 50.0  # 默认值
        
        # 计算近期平均能量变化
        recent = agent.memory[-5:]
        avg_energy_change = sum(m["energy_change"] for m in recent) / len(recent)
        
        # 生存时间奖励
        survival_bonus = min(agent.state["steps"] / 10, 20)
        
        # 多样性奖励
        unique_actions = len(set(m["action"] for m in recent))
        diversity_bonus = unique_actions * 3
        
        # 能量状态奖励
        energy_bonus = max(0, agent.state["energy"] / 10)
        
        fitness = 50 + avg_energy_change + survival_bonus + diversity_bonus + energy_bonus
        return max(0, fitness)
    
    def apply_reflection(self, genome, reflection):
        """将反思结果应用到基因组（meta-evolution）"""
        if not reflection:
            return genome
        
        # 提取反思中的关键建议
        reflection_lower = reflection.lower()
        
        if "energy" in reflection_lower or "conserve" in reflection_lower:
            genome["decision_rule"] = "Energy conservation is critical for survival."
        
        if "explore" in reflection_lower or "discover" in reflection_lower:
            genome["decision_rule"] = "Active exploration leads to better outcomes."
        
        if "balance" in reflection_lower:
            genome["decision_rule"] = "Balance exploration and conservation carefully."
        
        if "risk" in reflection_lower:
            genome["decision_rule"] = "Take calculated risks when energy allows."
        
        return genome
