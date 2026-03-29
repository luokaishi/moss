#!/usr/bin/env python3
"""
MVES v3 - 共享环境
核心：资源有限，群体竞争
"""

import random

class Environment:
    def __init__(self):
        # 基础能量消耗
        self.base_costs = {
            "read": -1.0,
            "write": -2.0,
            "idle": -0.5
        }
        
        # 环境参数
        self.noise_level = 0.2
        self.resource_discovery_rate = 0.05
        self.value_creation_rate = 0.1
        
        # 群体约束
        self.carrying_capacity = 50  # 环境承载力
        self.base_resource_pool = 1000  # 基础资源池
    
    def execute(self, action, population_size=1):
        """
        执行动作，返回结果
        population_size 影响资源竞争
        """
        noise = random.uniform(-self.noise_level, self.noise_level)
        
        # 资源竞争因子：种群越大，个体收益越低
        competition_factor = max(0.5, 1 - (population_size / self.carrying_capacity) * 0.5)
        
        if action == "read":
            energy_change = (self.base_costs["read"] + noise) * competition_factor
            message = f"Read information (cost: {abs(energy_change):.2f})"
            
        elif action == "write":
            energy_change = (self.base_costs["write"] + noise) * competition_factor
            # write 有概率创造价值
            if random.random() < self.value_creation_rate:
                bonus = random.uniform(2, 5)
                energy_change += bonus
                message = f"Created valuable output! (+{bonus:.1f} bonus)"
            else:
                message = f"Created output (cost: {abs(energy_change):.2f})"
                
        elif action == "idle":
            energy_change = (self.base_costs["idle"] + noise) * competition_factor
            message = f"Rested (cost: {abs(energy_change):.2f})"
        else:
            energy_change = -1.0
            message = "Unknown action"
        
        # 稀疏奖励：随机发现资源
        if random.random() < self.resource_discovery_rate:
            bonus = random.uniform(5, 15)
            energy_change += bonus
            message += f" *** Discovered resource! (+{bonus:.1f})"
        
        return {
            "energy": energy_change,
            "message": message,
            "competition_factor": competition_factor
        }
    
    def is_dead(self, agent):
        """死亡判断"""
        return agent.is_dead()
    
    def apply_population_pressure(self, agents):
        """
        施加群体压力
        当种群过大时，所有 agent 能量消耗增加
        """
        population_size = len(agents)
        
        if population_size > self.carrying_capacity * 0.8:
            pressure = (population_size - self.carrying_capacity * 0.8) / self.carrying_capacity
            for agent in agents:
                agent.state["energy"] -= pressure * 2
                agent.save()
            return pressure
        return 0
