#!/usr/bin/env python3
"""
MVES v2 - 环境模块
升级：动态噪声 + 稀疏奖励 + 随机事件
"""

import random

class Environment:
    def __init__(self):
        self.base_costs = {
            "read": -1.0,
            "write": -2.0,
            "idle": -0.5
        }
        self.noise_level = 0.2  # 环境噪声
        self.resource_discovery_rate = 0.05  # 5% 概率发现资源
    
    def execute(self, action):
        """执行动作，返回结果（带噪声）"""
        noise = random.uniform(-self.noise_level, self.noise_level)
        
        if action == "read":
            energy_change = self.base_costs["read"] + noise
            message = f"Read information (cost: {abs(energy_change):.2f})"
        elif action == "write":
            energy_change = self.base_costs["write"] + noise
            # write 有小概率产生价值
            if random.random() < 0.1:
                energy_change += 3  # 创造价值！
                message = "Created valuable output! (+3 energy bonus)"
            else:
                message = f"Created output (cost: {abs(energy_change):.2f})"
        elif action == "idle":
            energy_change = self.base_costs["idle"] + noise
            message = f"Rested (cost: {abs(energy_change):.2f})"
        else:
            energy_change = -1.0
            message = "Unknown action"
        
        # 稀疏奖励：随机发现资源（关键：鼓励探索）
        if random.random() < self.resource_discovery_rate:
            bonus = random.uniform(5, 15)
            energy_change += bonus
            message += f" *** Discovered resource! (+{bonus:.1f})"
        
        return {
            "energy": energy_change,
            "message": message
        }
    
    def evaluate(self, agent):
        """评估适应度（核心：真实选择压力）"""
        # 新公式：能量是硬约束
        energy_score = max(0, agent.state["energy"])
        step_efficiency = agent.state["steps"] / max(1, agent.state["steps"] + 100)
        
        # 记忆质量：多样性奖励
        if len(agent.memory) > 0:
            unique_actions = len(set(m["action"] for m in agent.memory))
            diversity_bonus = unique_actions * 2
        else:
            diversity_bonus = 0
        
        fitness = energy_score + (step_efficiency * 20) + diversity_bonus
        return fitness
    
    def is_dead(self, agent):
        """死亡判断（核心跃迁：直接用能量）"""
        return agent.state["energy"] <= 0
    
    def random_event(self):
        """随机环境事件"""
        events = [
            {"type": "none", "prob": 0.8},
            {"type": "resource", "prob": 0.1, "bonus": 10},
            {"type": "hazard", "prob": 0.1, "penalty": -5}
        ]
        
        roll = random.random()
        cumulative = 0
        for event in events:
            cumulative += event["prob"]
            if roll < cumulative:
                return event
        return events[0]
