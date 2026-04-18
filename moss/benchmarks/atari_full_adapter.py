"""
Atari Full Adapter - MOSS v6.6

支持 20+ Atari 游戏
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path


class AtariFullAdapter:
    """Atari 完整适配器 - 支持 20+ 游戏"""
    
    # 20+ Atari 游戏配置
    GAMES = {
        # 经典游戏
        'Pong': {'difficulty': 'easy', 'category': 'classic', 'action_meaning': ['NOOP', 'FIRE', 'UP', 'DOWN']},
        'Breakout': {'difficulty': 'easy', 'category': 'classic', 'action_meaning': ['NOOP', 'FIRE', 'RIGHT', 'LEFT']},
        'SpaceInvaders': {'difficulty': 'medium', 'category': 'shooter', 'action_meaning': ['NOOP', 'FIRE', 'RIGHT', 'LEFT']},
        
        # 迷宫游戏
        'MsPacman': {'difficulty': 'medium', 'category': 'maze', 'action_meaning': ['NOOP', 'UP', 'RIGHT', 'LEFT', 'DOWN']},
        'Pacman': {'difficulty': 'medium', 'category': 'maze', 'action_meaning': ['NOOP', 'UP', 'RIGHT', 'LEFT', 'DOWN']},
        
        # 射击游戏
        'Asteroids': {'difficulty': 'hard', 'category': 'shooter', 'action_meaning': ['NOOP', 'FIRE', 'RIGHT', 'LEFT', 'UP']},
        'Galaxian': {'difficulty': 'medium', 'category': 'shooter', 'action_meaning': ['NOOP', 'FIRE', 'RIGHT', 'LEFT']},
        
        # 平台游戏
        'MontezumaRevenge': {'difficulty': 'hard', 'category': 'platformer', 'action_meaning': ['NOOP', 'FIRE', 'UP', 'RIGHT', 'LEFT', 'DOWN']},
        'Pitfall': {'difficulty': 'hard', 'category': 'platformer', 'action_meaning': ['NOOP', 'FIRE', 'UP', 'RIGHT', 'LEFT', 'DOWN']},
        
        # 赛车游戏
        'Enduro': {'difficulty': 'medium', 'category': 'racing', 'action_meaning': ['NOOP', 'FIRE', 'RIGHT', 'LEFT']},
        'RoadRunner': {'difficulty': 'medium', 'category': 'racing', 'action_meaning': ['NOOP', 'FIRE', 'UP', 'RIGHT', 'LEFT', 'DOWN']},
        
        # 体育游戏
        'Boxing': {'difficulty': 'medium', 'category': 'sports', 'action_meaning': ['NOOP', 'FIRE', 'UP', 'RIGHT', 'LEFT', 'DOWN']},
        'Tennis': {'difficulty': 'hard', 'category': 'sports', 'action_meaning': ['NOOP', 'FIRE', 'UP', 'RIGHT', 'LEFT', 'DOWN']},
        
        # 策略游戏
        'Qbert': {'difficulty': 'hard', 'category': 'puzzle', 'action_meaning': ['NOOP', 'FIRE', 'UP', 'RIGHT', 'LEFT', 'DOWN']},
        'Frostbite': {'difficulty': 'hard', 'category': 'puzzle', 'action_meaning': ['NOOP', 'FIRE', 'UP', 'RIGHT', 'LEFT', 'DOWN']},
        
        # 其他
        'Seaquest': {'difficulty': 'medium', 'category': 'shooter', 'action_meaning': ['NOOP', 'FIRE', 'UP', 'RIGHT', 'LEFT', 'DOWN']},
        'BeamRider': {'difficulty': 'medium', 'category': 'shooter', 'action_meaning': ['NOOP', 'FIRE', 'UP', 'RIGHT', 'LEFT', 'DOWN']},
        'DemonAttack': {'difficulty': 'medium', 'category': 'shooter', 'action_meaning': ['NOOP', 'FIRE', 'RIGHT', 'LEFT']},
        'Carnival': {'difficulty': 'easy', 'category': 'shooter', 'action_meaning': ['NOOP', 'FIRE', 'RIGHT', 'LEFT']},
        'Jamesbond': {'difficulty': 'medium', 'category': 'action', 'action_meaning': ['NOOP', 'FIRE', 'UP', 'RIGHT', 'LEFT', 'DOWN']},
        'Krull': {'difficulty': 'medium', 'category': 'action', 'action_meaning': ['NOOP', 'FIRE', 'UP', 'RIGHT', 'LEFT', 'DOWN']},
    }
    
    def __init__(self, game='Pong', frame_skip=4, max_episode_steps=10000):
        """
        Args:
            game: 游戏名称
            frame_skip: 帧跳过
            max_episode_steps: 最大步数
        """
        self.game = game
        self.frame_skip = frame_skip
        self.max_episode_steps = max_episode_steps
        self.current_step = 0
        
        # 游戏配置
        self.config = self.GAMES.get(game, {})
        
        # 创建环境
        try:
            import gym
            self.env = gym.make(f'ALE/{game}-v5')
            self.available = True
        except:
            try:
                import gym
                self.env = gym.make(f'{game}NoFrameskip-v4')
                self.available = True
            except:
                self.env = None
                self.available = False
        
        # 帧缓冲区
        self.frame_buffer = []
        self.buffer_size = 4
    
    def reset(self) -> np.ndarray:
        """重置环境"""
        if not self.available:
            return np.zeros((84, 84, 4), dtype=np.uint8)
        
        obs = self.env.reset()
        self.current_step = 0
        self.frame_buffer = []
        
        # 预处理并填充帧缓冲
        processed = self._preprocess(obs)
        for _ in range(self.buffer_size):
            self.frame_buffer.append(processed)
        
        return self._get_stacked_frames()
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """执行动作"""
        if not self.available:
            return np.zeros((84, 84, 4)), 0.0, True, {}
        
        total_reward = 0
        done = False
        
        # 帧跳过
        for _ in range(self.frame_skip):
            obs, reward, done, info = self.env.step(action)
            total_reward += reward
            self.current_step += 1
            
            if done or self.current_step >= self.max_episode_steps:
                break
        
        # 预处理和帧堆叠
        processed = self._preprocess(obs)
        self.frame_buffer.append(processed)
        if len(self.frame_buffer) > self.buffer_size:
            self.frame_buffer.pop(0)
        
        return self._get_stacked_frames(), float(total_reward), done, info
    
    def _preprocess(self, obs: np.ndarray) -> np.ndarray:
        """预处理图像"""
        # 转灰度
        if len(obs.shape) == 3:
            gray = np.dot(obs[..., :3], [0.299, 0.587, 0.114])
        else:
            gray = obs
        
        # 缩放
        from PIL import Image
        img = Image.fromarray(gray.astype(np.uint8))
        img = img.resize((84, 84), Image.BILINEAR)
        
        return np.array(img, dtype=np.uint8)
    
    def _get_stacked_frames(self) -> np.ndarray:
        """获取堆叠帧"""
        if len(self.frame_buffer) < self.buffer_size:
            # 填充
            while len(self.frame_buffer) < self.buffer_size:
                self.frame_buffer.append(self.frame_buffer[-1])
        
        return np.stack(self.frame_buffer, axis=-1)
    
    def get_action_space(self) -> int:
        """获取动作空间"""
        if not self.available:
            return 6  # 默认
        return self.env.action_space.n
    
    def get_observation_shape(self) -> Tuple:
        """获取观察形状"""
        return (84, 84, 4)
    
    def get_state_vector(self) -> np.ndarray:
        """获取状态向量 (简化版)"""
        if not self.frame_buffer:
            return np.zeros(12, dtype=np.float32)
        
        # 使用最新帧的统计特征
        latest_frame = self.frame_buffer[-1]
        
        features = [
            latest_frame.mean() / 255.0,
            latest_frame.std() / 255.0,
            (latest_frame > 128).sum() / (84 * 84),  # 亮度比例
        ]
        
        # 扩展到 12 维
        features = features * 4
        
        return np.array(features[:12], dtype=np.float32)
    
    def get_game_info(self) -> Dict:
        """获取游戏信息"""
        return {
            'name': self.game,
            'difficulty': self.config.get('difficulty', 'unknown'),
            'category': self.config.get('category', 'unknown'),
            'action_space': self.get_action_space(),
            'observation_shape': self.get_observation_shape(),
            'frame_skip': self.frame_skip,
            'max_steps': self.max_episode_steps
        }
    
    def close(self):
        """关闭环境"""
        if self.env:
            self.env.close()
    
    @classmethod
    def list_games(cls) -> List[str]:
        """列出所有游戏"""
        return list(cls.GAMES.keys())
    
    @classmethod
    def get_by_difficulty(cls, difficulty: str) -> List[str]:
        """按难度获取游戏"""
        return [name for name, config in cls.GAMES.items() 
                if config['diff