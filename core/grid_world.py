"""
最小可验证AGI涌现系统 - Grid World环境
Minimal Verifiable Emergent Agent System (MVEAS)

阶段1：引入最小环境
- 10x10网格世界
- 3种地形：空地(0)、障碍(1)、资源(2)
- 智能体：位置、能量、库存
- 行为：移动、收集、建造、休息
- 目标执行与反馈闭环
"""

import numpy as np
import random
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class Terrain(Enum):
    EMPTY = 0
    OBSTACLE = 1
    RESOURCE = 2

class Action(Enum):
    MOVE_UP = "move_up"
    MOVE_DOWN = "move_down"
    MOVE_LEFT = "move_left"
    MOVE_RIGHT = "move_right"
    COLLECT = "collect"
    BUILD = "build"
    REST = "rest"

@dataclass
class Agent:
    x: int
    y: int
    energy: float = 100.0
    inventory: Dict[str, int] = None
    
    def __post_init__(self):
        if self.inventory is None:
            self.inventory = {"resource": 0, "structure": 0}

class GridWorld:
    """极简Grid World环境"""
    
    def __init__(self, size: int = 10):
        self.size = size
        self.grid = np.zeros((size, size), dtype=int)
        self.agent = Agent(x=size//2, y=size//2)
        self.time_step = 0
        self.history = []
        
        # 初始化地形
        self._init_terrain()
    
    def _init_terrain(self):
        """随机初始化地形"""
        for i in range(self.size):
            for j in range(self.size):
                if random.random() < 0.1:  # 10%障碍
                    self.grid[i, j] = Terrain.OBSTACLE.value
                elif random.random() < 0.15:  # 15%资源
                    self.grid[i, j] = Terrain.RESOURCE.value
    
    def is_valid_position(self, x: int, y: int) -> bool:
        """检查位置是否有效"""
        return 0 <= x < self.size and 0 <= y < self.size
    
    def is_obstacle(self, x: int, y: int) -> bool:
        """检查是否为障碍"""
        return self.is_valid_position(x, y) and self.grid[x, y] == Terrain.OBSTACLE.value
    
    def is_resource(self, x: int, y: int) -> bool:
        """检查是否为资源"""
        return self.is_valid_position(x, y) and self.grid[x, y] == Terrain.RESOURCE.value
    
    def execute_action(self, action: Action) -> Dict:
        """执行行为并返回结果"""
        result = {
            "action": action.value,
            "success": False,
            "reward": 0.0,
            "energy_change": 0.0,
            "message": ""
        }
        
        if action in [Action.MOVE_UP, Action.MOVE_DOWN, Action.MOVE_LEFT, Action.MOVE_RIGHT]:
            result = self._execute_move(action)
        elif action == Action.COLLECT:
            result = self._execute_collect()
        elif action == Action.BUILD:
            result = self._execute_build()
        elif action == Action.REST:
            result = self._execute_rest()
        
        # 记录历史
        self.history.append({
            "time": self.time_step,
            "action": action.value,
            "result": result
        })
        self.time_step += 1
        
        return result
    
    def _execute_move(self, action: Action) -> Dict:
        """执行移动"""
        dx, dy = 0, 0
        if action == Action.MOVE_UP:
            dx, dy = -1, 0
        elif action == Action.MOVE_DOWN:
            dx, dy = 1, 0
        elif action == Action.MOVE_LEFT:
            dx, dy = 0, -1
        elif action == Action.MOVE_RIGHT:
            dx, dy = 0, 1
        
        new_x = self.agent.x + dx
        new_y = self.agent.y + dy
        
        if not self.is_valid_position(new_x, new_y):
            return {
                "action": action.value,
                "success": False,
                "reward": -1.0,
                "energy_change": -2.0,
                "message": "Hit boundary"
            }
        
        if self.is_obstacle(new_x, new_y):
            return {
                "action": action.value,
                "success": False,
                "reward": -1.0,
                "energy_change": -2.0,
                "message": "Hit obstacle"
            }
        
        # 成功移动
        self.agent.x = new_x
        self.agent.y = new_y
        self.agent.energy -= 2.0
        
        return {
            "action": action.value,
            "success": True,
            "reward": 0.1,
            "energy_change": -2.0,
            "message": f"Moved to ({new_x}, {new_y})"
        }
    
    def _execute_collect(self) -> Dict:
        """执行收集"""
        if not self.is_resource(self.agent.x, self.agent.y):
            return {
                "action": Action.COLLECT.value,
                "success": False,
                "reward": -0.5,
                "energy_change": -3.0,
                "message": "No resource here"
            }
        
        # 成功收集
        self.agent.inventory["resource"] += 1
        self.grid[self.agent.x, self.agent.y] = Terrain.EMPTY.value
        self.agent.energy -= 3.0
        
        return {
            "action": Action.COLLECT.value,
            "success": True,
            "reward": 5.0,
            "energy_change": -3.0,
            "message": "Collected resource"
        }
    
    def _execute_build(self) -> Dict:
        """执行建造"""
        if self.agent.inventory["resource"] < 1:
            return {
                "action": Action.BUILD.value,
                "success": False,
                "reward": -1.0,
                "energy_change": -5.0,
                "message": "No resources to build"
            }
        
        # 成功建造
        self.agent.inventory["resource"] -= 1
        self.agent.inventory["structure"] += 1
        self.agent.energy -= 5.0
        
        return {
            "action": Action.BUILD.value,
            "success": True,
            "reward": 10.0,
            "energy_change": -5.0,
            "message": "Built structure"
        }
    
    def _execute_rest(self) -> Dict:
        """执行休息"""
        energy_gain = min(20.0, 100.0 - self.agent.energy)
        self.agent.energy += energy_gain
        
        return {
            "action": Action.REST.value,
            "success": True,
            "reward": 0.5,
            "energy_change": energy_gain,
            "message": f"Rested, gained {energy_gain:.1f} energy"
        }
    
    def get_state(self) -> Dict:
        """获取当前状态"""
        return {
            "agent_position": (self.agent.x, self.agent.y),
            "agent_energy": self.agent.energy,
            "agent_inventory": self.agent.inventory.copy(),
            "time_step": self.time_step,
            "nearby_terrain": self._get_nearby_terrain()
        }
    
    def _get_nearby_terrain(self) -> Dict:
        """获取周围地形"""
        nearby = {}
        for dx, dy, name in [(-1,0,"up"), (1,0,"down"), (0,-1,"left"), (0,1,"right")]:
            nx, ny = self.agent.x + dx, self.agent.y + dy
            if self.is_valid_position(nx, ny):
                nearby[name] = self.grid[nx, ny]
            else:
                nearby[name] = -1  # 边界
        return nearby
    
    def render(self) -> str:
        """渲染环境"""
        lines = []
        lines.append(f"Time: {self.time_step} | Energy: {self.agent.energy:.1f}")
        lines.append(f"Inventory: {self.agent.inventory}")
        lines.append("-" * (self.size * 2 + 1))
        
        for i in range(self.size):
            row = []
            for j in range(self.size):
                if i == self.agent.x and j == self.agent.y:
                    row.append("A")  # 智能体
                elif self.grid[i, j] == Terrain.EMPTY.value:
                    row.append(".")
                elif self.grid[i, j] == Terrain.OBSTACLE.value:
                    row.append("#")
                elif self.grid[i, j] == Terrain.RESOURCE.value:
                    row.append("R")
            lines.append("|" + "|".join(row) + "|")
        lines.append("-" * (self.size * 2 + 1))
        return "\n".join(lines)


if __name__ == "__main__":
    # 测试环境
    print("=" * 50)
    print("Grid World Environment Test")
    print("=" * 50)
    
    env = GridWorld(size=10)
    print("\nInitial state:")
    print(env.render())
    
    # 测试移动
    print("\nTest: Move right")
    result = env.execute_action(Action.MOVE_RIGHT)
    print(f"Result: {result}")
    print(env.render())
    
    # 测试收集
    print("\nTest: Collect")
    result = env.execute_action(Action.COLLECT)
    print(f"Result: {result}")
    
    # 测试休息
    print("\nTest: Rest")
    result = env.execute_action(Action.REST)
    print(f"Result: {result}")
    print(env.render())
    
    print("\n" + "=" * 50)
    print("Grid World Environment Ready!")
    print("=" * 50)
