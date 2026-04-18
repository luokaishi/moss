"""
Procgen Adapter - MOSS v6.4

适配 Procgen 环境到 MOSS
"""

import numpy as np
from typing import Dict, List, Tuple, Optional


class ProcgenAdapter:
    """Procgen 环境适配器"""
    
    ENV_NAMES = [
        'coinrun', 'starpilot', 'caveflyer', 'dodgeball',
        'fruitbot', 'chaser', 'miner', 'jumper',
        'leaper', 'maze', 'heist', 'climber',
        'plunder', 'bossfight'
    ]
    
    def __init__(self, env_name='coinrun', num_levels=0, start_level=0):
        """
        Args:
            env_name: 环境名称
            num_levels: 关卡数量 (0=无限)
            start_level: 起始关卡
        """
        self.env_name = env_name
        self.num_levels = num_levels
        self.start_level = start_level
        
        try:
            import gym
            import procgen
            self.env = gym.make(
                f'procgen:procgen-{env_name}-v0',
                num_levels=num_levels,
                start_level=start_level
            )
            self.available = True
        except ImportError:
            print("Warning: procgen not installed")
            self.env = None
            self.available = False
        
        self.current_step = 0
        self.max_steps = 1000
    
    def reset(self) -> np.ndarray:
        """重置环境"""
        if not self.available:
            return np.zeros((64, 64, 3), dtype=np.uint8)
        
        obs = self.env.reset()
        self.current_step = 0
        return obs
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """执行动作"""
        if not self.available:
            return np.zeros((64, 64, 3)), 0.0, True, {}
        
        obs, reward, done, info = self.env.step(action)
        self.current_step += 1
        
        # 最大步数限制
        if self.current_step >= self.max_steps:
            done = True
        
        return obs, float(reward), done, info
    
    def get_state_vector(self, obs: np.ndarray) -> np.ndarray:
        """转换为状态向量"""
        # 简化：使用图像的统计特征
        # 实际应用中使用 CNN 编码
        features = [
            obs.mean(),  # 平均亮度
            obs.std(),   # 对比度
            obs[:, :, 0].mean(),  # R通道
            obs[:, :, 1].mean(),  # G通道
            obs[:, :, 2].mean(),  # B通道
        ]
        return np.array(features, dtype=np.float32)
    
    def get_action_space(self) -> int:
        """获取动作空间大小"""
        if not self.available:
            return 15  # Procgen 默认
        return self.env.action_space.n
    
    def close(self):
        """关闭环境"""
        if self.env:
            self.env.close()


class ProcgenMOSSWrapper:
    """Procgen MOSS 包装器"""
    
    def __init__(self, env_name='coinrun'):
        self.adapter = ProcgenAdapter(env_name)
        self.state_dim = 12
    
    def reset(self):
        """重置"""
        obs = self.adapter.reset()
        return self._process_observation(obs)
    
    def step(self, action):
        """执行动作"""
        obs, reward, done, info = self.adapter.step(action)
        return self._process_observation(obs), reward, done, info
    
    def _process_observation(self, obs):
        """处理观察"""
        # 使用适配器的状态向量
        state = self.adapter.get_state_vector(obs)
        
        # 扩展到 12 维
        if len(state) < self.state_dim:
            state = np.pad(state, (0, self.state_dim - len(state)))
        elif len(state) > self.state_dim:
            state = state[:self.state_dim]
        
        return state
