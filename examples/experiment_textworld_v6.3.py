"""
TextWorld 对比实验 - MOSS v6.3 验证

验证 v6.2 改进效果，对比三种策略：
- random: 随机策略 (基线)
- v6.1: MOSS v6.1 (旧版)
- v6.2: MOSS v6.2 (改进版)

目标成功率: > 50%

用法:
    python examples/experiment_textworld_v6.3.py --mode random --episodes 100
    python examples/experiment_textworld_v6.3.py --mode v6.1 --episodes 100
    python examples/experiment_textworld_v6.3.py --mode v6.2 --episodes 100
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
import time
import random
import argparse
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class EpisodeResult:
    """单局游戏结果"""
    episode: int
    success: bool
    steps: int
    total_reward: float
    max_score: float
    achieved_score: float
    duration: float
    command_history: List[str] = field(default_factory=list)
    drive_weights: Dict[str, float] = field(default_factory=dict)
    alignment_scores: List[float] = field(default_factory=list)
    task_progress: List[float] = field(default_factory=list)


class MockTextWorldEnv:
    """模拟 TextWorld 环境（用于验证实验）"""
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)
        self.max_steps = 50
        self.current_step = 0
        self.score = 0.0
        self.max_score = 10.0
        self.visited_rooms = set()
        self.inventory = []
        self.current_room = "start"
        
    def reset(self):
        """重置环境"""
        self.current_step = 0
        self.score = 0.0
        self.visited_rooms = set()
        self.inventory = []
        self.current_room = "kitchen"
        
        observation = """-= Kitchen =-
You are in a kitchen. There is a table here.
You see: a key, a knife
Exits: east to living room, north to garden
"""
        
        info = {
            'admissible_commands': [
                "go east", "go north", "take key", "take knife", 
                "examine table", "look", "inventory"
            ],
            'score': 0.0,
            'max_score': self.max_score,
            'won': False,
            'lost': False,
            'location': 'kitchen',
        }
        
        return observation, info
    
    def step(self, command: str):
        """执行一步"""
        self.current_step += 1
        
        cmd_lower = command.lower()
        
        # 模拟状态变化
        if "go east" in cmd_lower:
            self.current_room = "living room"
            self.visited_rooms.add("living room")
            obs = """-= Living Room =-
You are in a living room. There is a locked chest here.
You see: a chest, a coin
Exits: west to kitchen, north to garden
"""
        elif "go north" in cmd_lower:
            self.current_room = "garden"
            self.visited_rooms.add("garden")
            obs = """-= Garden =-
You are in a garden. There are flowers here.
You see: a flower
Exits: south to kitchen
"""
        elif "go west" in cmd_lower:
            self.current_room = "kitchen"
            obs = """-= Kitchen =-
You are back in the kitchen.
You see: a table
Exits: east to living room, north to garden
"""
        elif "go south" in cmd_lower:
            self.current_room = "kitchen"
            obs = """-= Kitchen =-
You are back in the kitchen.
Exits: east to living room, north to garden
"""
        elif "take key" in cmd_lower:
            if "key" not in self.inventory:
                self.inventory.append("key")
                self.score += 3.0
                obs = "You take the key."
            else:
                obs = "You already have the key."
        elif "take knife" in cmd_lower:
            if "knife" not in self.inventory:
                self.inventory.append("knife")
                self.score += 1.0
                obs = "You take the knife."
            else:
                obs = "You already have the knife."
        elif "take coin" in cmd_lower:
            if "coin" not in self.inventory:
                self.inventory.append("coin")
                self.score += 2.0
                obs = "You take the coin."
            else:
                obs = "You already have the coin."
        elif "take flower" in cmd_lower:
            if "flower" not in self.inventory:
                self.inventory.append("flower")
                self.score += 1.0
                obs = "You take the flower."
            else:
                obs = "You already have the flower."
        elif "open chest" in cmd_lower:
            if "key" in self.inventory:
                self.score += 3.0
                obs = "You unlock and open the chest. You found treasure!"
            else:
                obs = "The chest is locked. You need a key."
        elif "examine" in cmd_lower:
            obs = f"You examine the {cmd_lower.split()[-1]}."
        elif "inventory" in cmd_lower or cmd_lower == "i":
            if self.inventory:
                obs = f"You are carrying: {', '.join(self.inventory)}."
            else:
                obs = "You are carrying nothing."
        else:
            obs = "Nothing happens."
        
        # 计算奖励
        reward = self.score - (self.current_step * 0.1)
        
        # 判断是否获胜 (达到90%以上分数)
        won = self.score >= self.max_score * 0.9
        lost = self.current_step >= self.max_steps
        done = won or lost
        
        # 构建观察
        if not done:
            obs += f"\n\nScore: {self.score:.1f}/{self.max_score}"
            obs += f"\nLocation: {self.current_room}"
        
        info = {
            'admissible_commands': self._get_admissible_commands(),
            'score': self.score,
            'max_score': self.max_score,
            'won': won,
            'lost': lost,
            'location': self.current_room,
            'inventory': self.inventory.copy(),
        }
        
        return obs, reward, done, info
    
    def _get_admissible_commands(self):
        """获取可用命令"""
        commands = ["look", "inventory", "wait"]
        
        if self.current_room == "kitchen":
            commands.extend(["go east", "go north"])
            if "key" not in self.inventory:
                commands.append("take key")
            if "knife" not in self.inventory:
                commands.append("take knife")
            commands.append("examine table")
        elif self.current_room == "living room":
            commands.extend(["go west", "go north"])
            if "coin" not in self.inventory:
                commands.append("take coin")
            commands.append("examine chest")
            if "key" in self.inventory:
                commands.append("open chest")
        elif self.current_room == "garden":
            commands.append("go south")
            if "flower" not in self.inventory:
                commands.append("take flower")
            commands.append("examine flower")
        
        return commands


class RandomAgent:
    """随机策略基线"""
    
    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
    
    def act(self, observation: str, info: dict) -> str:
        """随机选择一个可用命令"""
        commands = info.get('admissible_commands', ['look'])
        return self.rng.choice(commands)
    
    def reset(self):
        """重置智能体状态"""
        pass


class V61Agent:
    """MOSS v6.1 智能体 (旧版) - 基于规则的目标导向策略"""
    
    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.inventory =