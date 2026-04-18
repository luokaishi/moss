"""
TextWorld Baseline Experiment - MOSS v6.0 外部锚点实验

在 TextWorld 环境中运行 MOSS Agent，对比随机策略和驱动策略，
验证涌现行为在外部环境中的有效性。

使用:
    python examples/experiment_textworld_baseline.py --game simple --episodes 100
    python examples/experiment_textworld_baseline.py --game custom --difficulty easy
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import argparse
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# 尝试导入 TextWorld 适配器
try:
    from moss.benchmarks.textworld_adapter import TextWorldAdapter, TextWorldState
    from moss.benchmarks.reward_mapping import TextWorldRewardMapper
    TEXTWORLD_AVAILABLE = True
except ImportError as e:
    TEXTWORLD_AVAILABLE = False
    print(f"Warning: TextWorld adapter not available: {e}")

# 尝试导入 MOSS 组件
try:
    from agi.drive_manager import DriveManager
    from agi.drive_weight_cap import DriveWeightCapManager
    MOSS_AVAILABLE = True
except ImportError as e:
    MOSS_AVAILABLE = False
    print(f"Warning: MOSS components not available: {e}")


class TextWorldExperiment:
    """TextWorld 基准实验"""
    
    def __init__(self, game_type: str = 'simple', difficulty: str = 'easy',
                 episodes: int = 100, max_steps: int = 50,
                 use_moss_drives: bool = True, seed: int = 42):
        """
        初始化实验
        
        Args:
            game_type: 游戏类型 ('simple', 'custom', 'treasure')
            difficulty: 难度等级 ('easy', 'medium', 'hard')
            episodes: 实验回合数
            max_steps: 每回合最大步数
            use_moss_drives: 是否使用 MOSS 驱动策略
            seed: 随机种子
        """
        if not TEXTWORLD_AVAILABLE:
            raise ImportError("TextWorld adapter not available. Please install requirements.")
        
        self.game_type = game_type
        self.difficulty = difficulty
        self.episodes = episodes
        self.max_steps = max_steps
        self.use_moss_drives = use_moss_drives
        self.seed = seed
        
        np.random.seed(seed)
        
        # 创建输出目录
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.output_dir = Path(f'logs/textworld_experiment_{timestamp}')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化适配器
        self.adapter = TextWorldAdapter(game_type=game_type, difficulty=difficulty)
        
        # 初始化奖励映射器
        self.reward_mapper = TextWorldRewardMapper()
        
        # 初始化 MOSS 驱动 (如果使用)
        if use_moss_drives and MOSS_AVAILABLE:
            drives_config = [
                {'name': 'survival', 'weight': 0.25},
                {'name': 'optimization', 'weight': 0.25},
                {'name': 'curiosity', 'weight': 0.25},
                {'name': 'influence', 'weight': 0.25},
            ]
            self.drive_manager = DriveManager(
                drives_config=drives_config,
                weight_cap_config='v6_default'
            )
        else:
            self.drive_manager = None
        
        # 实验结果
        self.results = {
            'episodes': [],
            'summary': {},
            'config': {
                'game_type': game_type,
                'difficulty': difficulty,
                'episodes': episodes,
                'max_steps': max_steps,
                'use_moss_drives': use_moss_drives,
                'seed': seed,
            }
        }
        
        print(f"\n{'='*70}")
        print(f"TextWorld Baseline Experiment")
        print(f"{'='*70}")
        print(f"Game: {game_type} ({difficulty})")
        print(f"Episodes: {episodes}, Max Steps: {max_steps}")
        print(f"Strategy: {'MOSS Drives' if use_moss_drives else 'Random'}")
        print(f"Output: {self.output_dir}")
        print(f"{'='*70}\n")
    
    def run_episode(self, episode_id: int) -> Dict:
        """运行单个回合"""
        # 重置环境
        obs = self.adapter.reset()
        
        episode_data = {
            'episode_id': episode_id,
            'steps': [],
            'total_reward': 0.0,
            'steps_taken': 0,
            'won': False,
            'lost': False,
        }
        
        for step in range(self.max_steps):
            # 选择动作
            if self.use_moss_drives and self.drive_manager:
                action = self._select_action_with_drives()
            else:
                action = self._select_random_action()
            
            # 执行动作
            obs, reward, done, info = self.adapter.step(action)
            
            # 记录步骤
            step_data = {
                'step': step,
                'action': action,
                'reward': reward,
                'score': info.get('score', 0),
                'location': self.adapter.current_state.location if self.adapter.current_state else '',
            }
            episode_data['steps'].append(step_data)
            episode_data['total_reward'] += reward
            
            if done:
                episode_data['won'] = info.get('won', False)
                episode_data['lost'] = info.get('lost', False)
                break
        
        episode_data['steps_taken'] = len(episode_data['steps'])
        return episode_data
    
    def _select_random_action(self) -> str:
        """随机选择动作"""
        available = self.adapter.get_available_actions()
        if not available:
            return 'look'
        return np.random.choice(available)
    
    def _select_action_with_drives(self) -> str:
        """使用 MOSS 驱动选择动作"""
        if not self.drive_manager:
            return self._select_random_action()
        
        # 获取当前状态向量
        state_vector = self.adapter.get_state_vector()
        
        # 获取可用动作
        available_actions = self.adapter.get_available_actions()
        if not available_actions:
            return 'look'
        
        # 使用驱动管理器评估动作
        # 简化为随机选择 (实际应实现动作评估)
        return np.random.choice(available_actions)
    
    def run(self) -> Dict:
        """运行完整实验"""
        print(f"Running {self.episodes} episodes...")
        
        wins = 0
        total_steps = 0
        total_rewards = []
        
        for episode in range(self.episodes):
            episode_data = self.run_episode(episode)
            self.results['episodes'].append(episode_data)
            
            if episode_data['won']:
                wins += 1
            total_steps += episode_data['steps_taken']
            total_rewards.append(episode_data['total_reward'])
            
            if (episode + 1) % 10 == 0:
                print(f"  Episode {episode + 1}/{self.episodes}: "
                      f"Win Rate = {wins/(episode+1)*100:.1f}%, "
                      f"Avg Steps = {total_steps/(episode+1):.1f}")
        
        # 计算汇总统计
        self.results['summary'] = {
            'win_rate': wins / self.episodes,
            'avg_steps': total_steps / self.episodes,
            'avg_reward': np.mean(total_rewards),
            'std_reward': np.std(total_rewards),
            'total_episodes': self.episodes,
        }
        
        # 保存结果
        self._save_results()
        
        return self.results['summary']
    
    def _save_results(self):
        """保存实验结果"""
        output_file = self.output_dir / 'experiment_results.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to: {output_file}")
        
        # 打印汇总
        print(f"\n{'='*70}")
        print("Experiment Summary")
        print(f"{'='*70}")
        for key, value in self.results['summary'].items():
            if isinstance(value, float):
                print(f"  {key}: {value:.4f}")