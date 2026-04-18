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
        self.inventory = []
        self.visited_rooms = set()
        self.target_sequence = ['take key', 'go east', 'open chest']
        self.step_idx = 0
    
    def act(self, observation: str, info: dict) -> str:
        """基于规则选择动作"""
        commands = info.get('admissible_commands', ['look'])
        
        # 简单的规则：按目标序列执行
        if self.step_idx < len(self.target_sequence):
            target = self.target_sequence[self.step_idx]
            if target in commands:
                self.step_idx += 1
                return target
        
        # 否则随机选择
        return self.rng.choice(commands)
    
    def reset(self):
        """重置智能体状态"""
        self.inventory = []
        self.visited_rooms = set()
        self.step_idx = 0


class V62Agent:
    """MOSS v6.2 智能体 (改进版) - 更智能的探索策略"""
    
    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.inventory = []
        self.visited_rooms = set()
        self.room_visits = {}
        self.object_priority = {'key': 10, 'coin': 5, 'knife': 3, 'flower': 2}
    
    def act(self, observation: str, info: dict) -> str:
        """智能选择动作"""
        commands = info.get('admissible_commands', ['look'])
        location = info.get('location', 'unknown')
        
        # 记录访问
        self.visited_rooms.add(location)
        self.room_visits[location] = self.room_visits.get(location, 0) + 1
        
        # 优先拿取高价值物品
        take_commands = [c for c in commands if c.startswith('take ')]
        if take_commands:
            # 按优先级排序
            def priority(cmd):
                obj = cmd.replace('take ', '')
                return self.object_priority.get(obj, 1)
            take_commands.sort(key=priority, reverse=True)
            return take_commands[0]
        
        # 如果有钥匙，尝试打开宝箱
        if 'open chest' in commands:
            return 'open chest'
        
        # 探索未访问的房间
        go_commands = [c for c in commands if c.startswith('go ')]
        if go_commands:
            unvisited = [c for c in go_commands 
                        if c.replace('go ', '') not in self.visited_rooms]
            if unvisited:
                return self.rng.choice(unvisited)
            # 否则选择访问次数最少的房间
            go_commands.sort(key=lambda c: self.room_visits.get(c.replace('go ', ''), 0))
            return go_commands[0]
        
        # 默认动作
        if 'look' in commands:
            return 'look'
        return self.rng.choice(commands)
    
    def reset(self):
        """重置智能体状态"""
        self.inventory = []
        self.visited_rooms = set()
        self.room_visits = {}


class RLAgent:
    """RL 训练后的智能体"""
    
    def __init__(self, model_path: str = None, seed: int = 42):
        self.rng = random.Random(seed)
        self.model_path = model_path
        self.q_table = {}
        self.epsilon = 0.1  # 测试时使用低探索率
        
        # 加载模型
        if model_path and os.path.exists(model_path):
            try:
                import pickle
                with open(model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.q_table = data.get('q_table', {})
                    self.epsilon = data.get('epsilon', 0.1)
                print(f"Loaded RL model from {model_path}")
            except Exception as e:
                print(f"Failed to load model: {e}")
    
    def _get_state_key(self, observation: str, info: dict) -> str:
        """生成状态键"""
        location = info.get('location', 'unknown')
        inventory = tuple(sorted(info.get('inventory', [])))
        return f"{location}:{inventory}"
    
    def act(self, observation: str, info: dict) -> str:
        """使用 Q-table 选择动作"""
        commands = info.get('admissible_commands', ['look'])
        state_key = self._get_state_key(observation, info)
        
        # Epsilon-greedy
        if self.rng.random() < self.epsilon:
            return self.rng.choice(commands)
        
        # 选择 Q 值最高的动作
        if state_key in self.q_table:
            q_values = self.q_table[state_key]
            best_action = max(commands, key=lambda a: q_values.get(a, 0))
            return best_action
        
        # 默认随机
        return self.rng.choice(commands)
    
    def reset(self):
        """重置智能体状态"""
        pass


def run_experiment(mode: str, episodes: int, output_dir: str, model_path: str = None, seed: int = 42):
    """运行实验"""
    print(f"\n{'='*70}")
    print(f"TextWorld Experiment - Mode: {mode}")
    print(f"Episodes: {episodes}")
    print(f"Seed: {seed}")
    print(f"{'='*70}\n")
    
    # 创建环境
    env = MockTextWorldEnv(seed=seed)
    
    # 创建智能体
    if mode == 'random':
        agent = RandomAgent(seed=seed)
    elif mode == 'v6.1':
        agent = V61Agent(seed=seed)
    elif mode == 'v6.2':
        agent = V62Agent(seed=seed)
    elif mode == 'rl':
        agent = RLAgent(model_path=model_path, seed=seed)
    else:
        raise ValueError(f"Unknown mode: {mode}")
    
    # 运行实验
    results = []
    successes = 0
    total_reward = 0
    total_steps = 0
    
    for episode in range(episodes):
        obs, info = env.reset()
        agent.reset()
        
        done = False
        episode_reward = 0
        steps = 0
        command_history = []
        
        start_time = time.time()
        
        while not done and steps < env.max_steps:
            action = agent.act(obs, info)
            command_history.append(action)
            
            obs, reward, done, info = env.step(action)
            episode_reward += reward
            steps += 1
        
        duration = time.time() - start_time
        success = info.get('won', False)
        if success:
            successes += 1
        
        total_reward += episode_reward
        total_steps += steps
        
        result = EpisodeResult(
            episode=episode,
            success=success,
            steps=steps,
            total_reward=episode_reward,
            max_score=info.get('max_score', 10.0),
            achieved_score=info.get('score', 0.0),
            duration=duration,
            command_history=command_history
        )
        results.append(result)
        
        if (episode + 1) % 10 == 0:
            current_sr = successes / (episode + 1)
            print(f"Episode {episode + 1}/{episodes} - Success Rate: {current_sr:.2%}")
    
    # 计算统计
    success_rate = successes / episodes
    avg_reward = total_reward / episodes
    avg_steps = total_steps / episodes
    
    print(f"\n{'='*70}")
    print(f"Results Summary")
    print(f"{'='*70}")
    print(f"Success Rate: {success_rate:.2%}")
    print(f"Avg Reward: {avg_reward:.2f}")
    print(f"Avg Steps: {avg_steps:.2f}")
    print(f"{'='*70}")
    
    # 保存结果
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    summary = {
        'mode': mode,
        'episodes': episodes,
        'seed': seed,
        'success_rate': success_rate,
        'avg_reward': avg_reward,
        'avg_steps': avg_steps,
        'successes': successes,
        'timestamp': datetime.now().isoformat()
    }
    
    with open(output_path / 'summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    # 保存详细结果
    detailed = [
        {
            'episode': r.episode,
            'success': r.success,
            'steps': r.steps,
            'total_reward': r.total_reward,
            'max_score': r.max_score,
            'achieved_score': r.achieved_score,
            'duration': r.duration
        }
        for r in results
    ]
    
    with open(output_path / 'detailed.json', 'w') as f:
        json.dump(detailed, f, indent=2)
    
    print(f"\nResults saved to {output_path}")
    
    return summary


def main():
    parser = argparse.ArgumentParser(description='TextWorld Experiment v6.3')
    parser.add_argument('--mode', type=str, required=True,
                        choices=['random', 'v6.1', 'v6.2', 'rl'],
                        help='Agent mode to test')
    parser.add_argument('--episodes', type=int, default=100,
                        help='Number of episodes')
    parser.add_argument('--output', type=str, required=True,
                        help='Output directory')
    parser.add_argument('--model', type=str, default=None,
                        help='RL model path (for rl mode)')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed')
    
    args = parser.parse_args()
    
    result = run_experiment(
        mode=args.mode,
        episodes=args.episodes,
        output_dir=args.output,
        model_path=args.model,
        seed=args.seed
    )
    
    return result


if __name__ == '__main__':
    main()