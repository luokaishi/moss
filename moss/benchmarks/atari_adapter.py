"""
Atari Adapter - MOSS v6.4

将 Atari 环境适配到 MOSS Agent 的接口，支持：
- 经典 Atari 游戏 (Pong, Breakout, etc.)
- 帧预处理 (灰度、缩放)
- 帧堆叠 (4帧)
- 状态向量转换
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from collections import deque
from dataclasses import dataclass, field


@dataclass
class AtariState:
    """Atari 游戏状态封装"""
    frame: np.ndarray = field(default_factory=lambda: np.zeros((84, 84), dtype=np.uint8))
    stacked_frames: np.ndarray = field(default_factory=lambda: np.zeros((4, 84, 84), dtype=np.uint8))
    score: float = 0.0
    lives: int = 0
    done: bool = False
    episode_step: int = 0
    total_reward: float = 0.0
    
    # 统计信息
    frame_count: int = 0
    action_count: int = 0
    reward_history: List[float] = field(default_factory=list)


class AtariAdapter:
    """
    MOSS 与 Atari 的接口适配器
    
    兼容 MOSS v6.0 DriveManager 接口，支持图像预处理
    和固定维度的状态向量输出。
    """
    
    # 支持的 Atari 游戏
    SUPPORTED_GAMES = [
        'Pong', 'Breakout', 'SpaceInvaders', 'Seaquest',
        'MsPacman', 'Qbert', 'Montezuma', 'Pitfall',
        'PrivateEye', 'Freeway', 'BeamRider', 'Enduro',
        'RoadRunner', 'Jamesbond', 'Kangaroo', 'Krull'
    ]
    
    # 状态向量维度 (固定 12 维)
    STATE_DIM = 12
    
    # 帧堆叠数量
    FRAME_STACK = 4
    
    # 目标帧尺寸
    FRAME_SIZE = (84, 84)
    
    def __init__(self, game_name: str = 'Pong', 
                 frame_skip: int = 4,
                 noop_max: int = 30,
                 max_episode_steps: int = 108000):
        """
        初始化 Atari 适配器
        
        Args:
            game_name: 游戏名称 (如 'Pong', 'Breakout')
            frame_skip: 帧跳过数 (动作重复)
            noop_max: 开始时随机执行 no-op 的最大次数
            max_episode_steps: 每回合最大步数
        """
        self.game_name = game_name
        self.frame_skip = frame_skip
        self.noop_max = noop_max
        self.max_episode_steps = max_episode_steps
        
        self.env = None
        self.current_state = AtariState()
        self.frame_buffer = deque(maxlen=self.FRAME_STACK)
        
        # 统计信息
        self.episode_count = 0
        self.total_steps = 0
        self.best_score = float('-inf')
        
        # 初始化环境
        self._init_environment()
    
    def _init_environment(self):
        """初始化 Atari 环境"""
        try:
            import gym
            env_id = f'{self.game_name}NoFrameskip-v4'
            self.env = gym.make(env_id)
            self.available = True
        except Exception as e:
            print(f"Warning: Could not load Atari game {self.game_name}: {e}")
            self.env = None
            self.available = False
            return
        
        # 获取动作空间
        self.action_space = self.env.action_space
        self.n_actions = self.action_space.n
        
        # 获取初始观察
        self.reset()
    
    def reset(self) -> np.ndarray:
        """
        重置环境，返回初始帧
        
        Returns:
            初始帧 (84x84)
        """
        if not self.available:
            return np.zeros(self.FRAME_SIZE, dtype=np.uint8)
        
        self.episode_count += 1
        
        # 重置环境
        obs = self.env.reset()
        
        # 随机执行 no-op 以改变初始状态
        import random
        for _ in range(random.randint(1, self.noop_max)):
            obs, _, done, _ = self.env.step(0)
            if done:
                obs = self.env.reset()
        
        # 预处理帧
        processed_frame = self._preprocess_frame(obs)
        
        # 初始化帧缓冲区
        self.frame_buffer.clear()
        for _ in range(self.FRAME_STACK):
            self.frame_buffer.append(processed_frame.copy())
        
        # 更新状态
        self.current_state = AtariState()
        self.current_state.frame = processed_frame
        self.current_state.stacked_frames = self._get_stacked_frames()
        self.current_state.lives = self._get_lives()
        
        return processed_frame
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """
        执行动作，返回 (observation, reward, done, info)
        
        Args:
            action: 动作索引
            
        Returns:
            Tuple of (frame, reward, done, info)
        """
        if not self.available:
            return np.zeros(self.FRAME_SIZE), 0.0, True, {}
        
        total_reward = 0.0
        done = False
        
        # 帧跳过 (重复动作)
        for _ in range(self.frame_skip):
            obs, reward, done, info = self.env.step(action)
            total_reward += reward
            
            # 生命检查 (用于某些游戏)
            current_lives = self._get_lives()
            if current_lives < self.current_state.lives:
                done = True  # 失去生命视为回合结束
            
            if done:
                break
        
        # 更新统计
        self.total_steps += 1
        self.current_state.episode_step += 1
        self.current_state.total_reward += total_reward
        self.current_state.action_count += 1
        self.current_state.reward_history.append(total_reward)
        
        # 预处理帧
        processed_frame = self._preprocess_frame(obs)
        self.frame_buffer.append(processed_frame)
        
        # 更新状态
        self.current_state.frame = processed_frame
        self.current_state.stacked_frames = self._get_stacked_frames()
        self.current_state.score = self._get_score()
        self.current_state.lives = current_lives
        self.current_state.done = done
        
        # 检查最大步数
        if self.current_state.episode_step >= self.max_episode_steps:
            done = True
        
        # 更新最佳分数
        if self.current_state.score > self.best_score:
            self.best_score = self.current_state.score
        
        return processed_frame, float(total_reward), done, self._build_info_dict()
    
    def _preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        预处理帧：灰度转换 + 缩放
        
        Args:
            frame: 原始 RGB 帧 (210x160x3)
            
        Returns:
            预处理后的灰度帧 (84x84)
        """
        # RGB 转灰度
        if len(frame.shape) == 3:
            gray = np.dot(frame[..., :3], [0.299, 0.587, 0.114])
        else:
            gray = frame
        
        # 缩放至 84x84
        from PIL import Image
        img = Image.fromarray(gray.astype(np.uint8))
        img = img.resize(self.FRAME_SIZE, Image.BILINEAR)
        
        return np.array(img, dtype=np.uint8)
    
    def _get_stacked_frames(self) -> np.ndarray:
        """获取堆叠的帧"""
        if len(self.frame_buffer) < self.FRAME_STACK:
            # 填充
            frames = list(self.frame_buffer)
            while len(frames) < self.FRAME_STACK:
                frames.insert(0, frames[0] if frames else np.zeros(self.FRAME_SIZE, dtype=np.uint8))
            return np.array(frames)
        return np.array(self.frame_buffer)
    
    def _get_lives(self) -> int:
        """获取剩余生命数"""
        if hasattr(self.env, 'ale'):
            return self.env.ale.lives()
        return 0
    
    def _get_score(self) -> float:
        """获取当前分数"""
        if hasattr(self.env, '_get_episode_rewards'):
            rewards = self.env._get_episode_rewards()
            return sum(rewards) if rewards else 0.0
        return self.current_state.total_reward
    
    def _build_info_dict(self) -> Dict:
        """构建 info 字典"""
        return {
            'score': self.current_state.score,
            'lives': self.current_state.lives,
            'episode_step': self.current_state.episode_step,
            'episode': self.episode_count,
            'total_steps': self.total_steps,
            'best_score': self.best_score,
            'game_name': self.game_name,
        }
    
    def get_state_vector(self) -> np.ndarray:
        """
        将当前状态转换为向量，供 MOSS 驱动评估使用
        
        维度 (12维):
        0: 归一化分数
        1: 剩余生命比例
        2: 回合进度
        3: 帧平均亮度
        4: 帧亮度方差
        5: 最近奖励
        6: 奖励移动平均
        7: 动作计数
        8: 帧差异 (运动检测)
        9: 游戏特定特征 1
        10: 游戏特定特征 2
        11: 环境熵
        
        Returns:
            12维 numpy 数组
        """
        vector = np.zeros(self.STATE_DIM, dtype=np.float32)
        
        # 0: 归一化分数 (假设最大分数为 1000)
        vector[0] = np.clip(self.current_state.score / 1000.0, 0, 1)
        
        # 1: 剩余生命比例 (假设最大生命为 5)
        vector[1] = np.clip(self.current_state.lives / 5.0, 0, 1)
        
        # 2: 回合进度
        vector[2] = np.clip(self.current_state.episode_step / self.max_episode_steps, 0, 1)
        
        # 3: 帧平均亮度
        current_frame = self.current_state.frame.astype(np.float32) / 255.0
        vector[3] = current_frame.mean()
        
        # 4: 帧亮度方差
        vector[4] = current_frame.std()
        
        # 5: 最近奖励 (归一化)
        if self.current_state.reward_history:
            vector[5] = np.clip(self.current_state.reward_history[-1] / 10.0, -1, 1)
        
        # 6: 奖励移动平均 (最近 10 步)
        if len(self.current_state.reward_history) >= 10:
            recent_rewards = self.current_state.reward_history[-10:]
            vector[6] = np.clip(np.mean(recent_rewards) / 10.0, -1, 1)
        
        # 7: 动作计数 (归一化)
        vector[7] = np.clip(self.current_state.action_count / 1000.0, 0, 1)
        
        # 8: 帧差异 (与上一帧的差异)
        if len(self.frame_buffer) >= 2:
            frames = list(self.frame_buffer)
            diff = np.abs(frames[-1].astype(np.float32) - frames[-2].astype(np.float32))
            vector[8] = np.clip(diff.mean() / 255.0, 0, 1)
        
        # 9-10: 游戏特定特征
        if 'Pong' in self.game_name:
            # Pong: 球的位置估计
            vector[9] = self._estimate_ball_position()[0]
            vector[10] = self._estimate_ball_position()[1]
        elif 'Breakout' in self.game_name:
            # Breakout: 球和挡板位置
            vector[9] = self._estimate_breakout_features()[0]
            vector[10] = self._estimate_breakout_features()[1]
        else:
            # 通用特征
            vector[9] = vector[3]  # 亮度
            vector[10] = vector[4]  # 对比度
        
        # 11: 环境熵 (基于帧变化的熵)
        if len(self.frame_buffer) >= self.FRAME_STACK:
            frames = np.array(self.frame_buffer)
            # 计算帧间变化的熵
            diffs = np.abs(np.diff(frames.astype(np.float32), axis=0))
            entropy = -np.sum(
                (diffs / (diffs.sum() + 1e-10)) * np.log(diffs / (diffs.sum() + 1e-10) + 1e-10)
            ) if diffs.sum() > 0 else 0
            vector[11] = np.clip(entropy / 1000.0, 0, 1)
        
        return vector
    
    def _estimate_ball_position(self) -> Tuple[float, float]:
        """估计 Pong 球的位置 (简化版)"""
        frame = self.current_state.frame
        # 寻找亮度最高的区域 (球的近似位置)
        max_val = frame.max()
        if max_val > 100:  # 阈值
            y, x = np.where(frame > max_val * 0.8)
            if len(x) > 0 and len(y) > 0:
                return x.mean() / 84.0, y.mean() / 84.0
        return 0.5, 0.5
    
    def _estimate_breakout_features(self) -> Tuple[float, float]:
        """估计 Breakout 特征 (简化版)"""
        frame = self.current_state.frame
        # 底部区域扫描 (挡板)
        bottom = frame[-10:, :]
        paddle_x = bottom.mean(axis=0).argmax() / 84.0 if bottom.mean() > 0 else 0.5
        
        # 整体亮度分布 (球的近似)
        ball_y = frame.mean(axis=1).argmax() / 84.0
        
        return paddle_x, ball_y
    
    def get_available_actions(self) -> List[str]:
        """
        返回动作名称列表
        
        Returns:
            动作名称列表
        """
        if not self.available:
            return []
        
        # Atari 动作含义 (通用)
        action_meanings = {
            0: 'NOOP',
            1: 'FIRE',
            2: 'UP',
            3: 'RIGHT',
            4: 'LEFT',
            5: 'DOWN',
            6: 'UPRIGHT',
            7: 'UPLEFT',
            8: 'DOWNRIGHT',
            9: 'DOWNLEFT',
            10: 'UPFIRE',
            11: 'RIGHTFIRE',
            12: 'LEFTFIRE',
            13: 'DOWNFIRE',
        }
        
        return [action_meanings.get(i, f'ACTION_{i}') for i in range(self.n_actions)]
    
    def render(self, mode='human'):
        """渲染环境"""
        if self.available:
            return self.env.render(mode=mode)
        return None
    
    def get_stats(self) -> Dict:
        """获取运行统计信息"""
        return {
            'episodes': self.episode_count,
            'total_steps': self.total_steps,
            'best_score': self.best_score,
            'current_score': self.current_state.score,
            'game_name': self.game_name,
            'action_space': self.n_actions if self.available else 0,
        }
    
    def close(self):
        """关闭环境"""
        if self.env is not None:
            self.env.close()
            self.env = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


class AtariMOSSWrapper:
    """
    Atari MOSS 包装器
    
    提供更高级的接口供 MOSS 使用
    """
    
    def __init__(self, game_name='Pong'):
        self.adapter = AtariAdapter(game_name)
        self.state_dim = 12
    
    def reset(self):
        """重置"""
        frame = self.adapter.reset()
        return self._process_frame(frame)
    
    def step(self, action):
        """执行动作"""
        frame, reward, done, info = self.adapter.step(action)
        return self._process_frame(frame), reward, done, info
    
    def _process_frame(self, frame):
        """处理帧为状态向量"""
        return self.adapter.get_state_vector()
    
    def get_action_space(self) -> int:
        """获取动作空间大小"""
        return self.adapter.n_actions if self.adapter.available else 0
    
    def close(self):
        """关闭"""
        self.adapter.close()


# 兼容性别名
MOSS_Atari_Interface = AtariAdapter


def create_atari_env(game_name='Pong', **kwargs):
    """
    创建 Atari 环境的工厂函数
    
    Args:
        game_name: 游戏名称
        **kwargs: 其他参数
        
    Returns:
        AtariAdapter 实例
    """
    return AtariAdapter(game_name, **kwargs)


def list_supported_games() -> List[str]:
    """列出支持的 Atari 游戏"""
    return AtariAdapter.SUPPORTED_GAMES.copy()