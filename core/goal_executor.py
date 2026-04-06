"""
目标执行与评估系统 - 阶段2
Goal Executor and Evaluation System
"""

import numpy as np
import random
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class GoalType(Enum):
    EXPLORATION = "exploration"
    RESOURCE_COLLECTION = "resource"
    STRUCTURE_BUILDING = "structure"
    ENERGY_MANAGEMENT = "energy"
    SURVIVAL = "survival"

@dataclass
class Goal:
    name: str
    goal_type: GoalType
    description: str
    target_state: Dict
    priority: float = 1.0

class IntrinsicMotivation:
    """内在动机系统 - 好奇心驱动"""
    
    def __init__(self, grid_size: int = 10):
        self.grid_size = grid_size
        self.visit_count = np.zeros((grid_size, grid_size), dtype=float)
        self.total_visits = 0
        
    def update_visit(self, x: int, y: int):
        if 0 <= x < self.grid_size and 0 <= y < self.grid_size:
            self.visit_count[x, y] += 1
            self.total_visits += 1
    
    def compute_curiosity(self, x: int, y: int) -> float:
        if self.total_visits == 0:
            return 1.0
        visit_freq = self.visit_count[x, y] / (self.total_visits + 1)
        return 1.0 - visit_freq
    
    def compute_entropy(self) -> float:
        if self.total_visits == 0:
            return 1.0
        probs = self.visit_count / (self.total_visits + 1e-10)
        probs = probs.flatten()
        probs = probs[probs > 0]
        if len(probs) == 0:
            return 1.0
        entropy = -np.sum(probs * np.log2(probs + 1e-10))
        max_entropy = np.log2(self.grid_size * self.grid_size)
        return entropy / max_entropy if max_entropy > 0 else 0
    
    def get_exploration_score(self) -> float:
        explored = np.sum(self.visit_count > 0)
        total = self.grid_size * self.grid_size
        return explored / total

class GoalExecutor:
    """目标执行器"""
    
    def __init__(self, grid_size: int = 10):
        self.motivation = IntrinsicMotivation(grid_size)
        self.execution_history = []
        
    def execute_goal_step(self, goal: Goal, env, action) -> Dict:
        result = env.execute_action(action)
        agent_pos = env.get_state().get("agent_position", (0, 0))
        self.motivation.update_visit(agent_pos[0], agent_pos[1])
        
        env_state = env.get_state()
        energy = env_state.get("agent_energy", 0)
        
        # 计算好奇心奖励
        curiosity = self.motivation.compute_curiosity(agent_pos[0], agent_pos[1])
        curiosity_reward = curiosity * 0.5
        
        # 生存奖励
        if energy <= 0:
            survival_reward = -100.0
        elif energy < 20:
            survival_reward = -10.0
        elif energy < 50:
            survival_reward = -1.0
        else:
            survival_reward = 1.0
        
        total_reward = result.get("reward", 0) + survival_reward + curiosity_reward
        
        return {
            "step": env.time_step,
            "goal": goal.name,
            "action": action.value,
            "base_reward": result.get("reward", 0),
            "survival_reward": survival_reward,
            "curiosity_reward": curiosity_reward,
            "total_reward": total_reward,
            "energy": energy,
            "curiosity": curiosity
        }

if __name__ == "__main__":
    print("Goal Executor System Ready!")
    print("Stage 2: Intrinsic Motivation & Goal Evaluation")
