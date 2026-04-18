"""
BabyAI Adapter - MOSS v6.2 多环境训练

适配 BabyAI 环境到 MOSS Agent
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

# 尝试导入 BabyAI
try:
    import gym
    import babyai
    BABYAI_AVAILABLE = True
except ImportError:
    BABYAI_AVAILABLE = False
    gym = None
    babyai = None


@dataclass
class BabyAIState:
    """BabyAI 游戏状态封装"""
    observation: np.ndarray = field(default_factory=lambda: np.zeros((7, 7, 3), dtype=np.int32))
    mission: str = ""
    direction: int = 0  # 0-3: right, down, left, up
    position: Tuple[int, int] = (0, 0)
    carrying: Optional[str] = None
    done: bool = False
    success: bool = False
    
    # MOSS 特定
    step_count: int = 0
    visited_positions: set = field(default_factory=set)
    interacted_objects: set = field(default_factory=set)
    task_progress: float = 0.0


class BabyAIAdapter:
    """BabyAI 环境适配器"""
    
    # 状态向量维度 (固定 12 维)
    STATE_DIM = 12
    
    # 动作映射
    ACTION_NAMES = ['turn_left', 'turn_right', 'move_forward', 'pickup', 'drop', 'toggle', 'done']
    ACTION_IDS = {name: i for i, name in enumerate(ACTION_NAMES)}
    
    # 方向映射
    DIRECTION_NAMES = ['right', 'down', 'left', 'up']
    
    # 对象类型映射 (BabyAI 对象编码)
    OBJECT_TYPES = {
        'wall': 0, 'floor': 1, 'door': 2, 'locked_door': 3,
        'key': 4, 'ball': 5, 'box': 6, 'goal': 7,
        'agent': 8, 'lava': 9, 'empty': 10
    }
    
    def __init__(self, level='BabyAI-GoToObj-v0'):
        self.level = level
        self.env = None
        self.current_state = BabyAIState()
        self._prev_obs = None
        
        # 统计信息
        self.episode_count = 0
        self.total_steps = 0
        self.total_reward = 0.0
        self.success_count = 0
        
        self._init_env()
    
    def _init_env(self):
        try:
            if BABYAI_AVAILABLE and gym is not None:
                self.env = gym.make(self.level)
            else:
                print("BabyAI not installed. Install with: pip install babyai")
        except Exception as e:
            print(f"Error initializing BabyAI environment: {e}")
    
    def reset(self) -> Tuple[np.ndarray, str]:
        """重置环境"""
        if self.env is None:
            return None, ""
        
        self.episode_count += 1
        obs = self.env.reset()
        
        # 解析观察
        if isinstance(obs, tuple):
            obs_img, mission = obs
        else:
            obs_img = obs
            mission = getattr(self.env, 'mission', '')
        
        self._parse_observation(obs_img, mission)
        self.current_state.visited_positions.clear()
        self.current_state.interacted_objects.clear()
        self.current_state.step_count = 0
        
        return obs_img, mission
    
    def step(self, action: Union[str, int]) -> Tuple[np.ndarray, float, bool, Dict]:
        """执行动作"""
        if self.env is None:
            return None, 0, True, {}
        
        # 转换动作
        if isinstance(action, str):
            action_id = self.ACTION_IDS.get(action, 0)
        else:
            action_id = action
        
        # 执行动作
        obs, reward, done, info = self.env.step(action_id)
        
        # 更新统计
        self.total_steps += 1
        self.total_reward += reward
        self.current_state.step_count += 1
        
        # 解析新观察
        mission = getattr(self.env, 'mission', '')
        self._parse_observation(obs, mission)
        
        # 跟踪位置
        self.current_state.visited_positions.add(self.current_state.position)
        
        # 更新任务进度
        self._update_task_progress(reward, done)
        
        return obs, float(reward), done, info
    
    def _parse_observation(self, obs: np.ndarray, mission: str):
        """解析观察"""
        self.current_state.observation = obs
        self.current_state.mission = mission
        
        if obs is not None and len(obs.shape) >= 2:
            # 从观察中提取代理位置和方向
            # BabyAI 观察是 (7, 7, 3) 的网格
            self._extract_agent_info(obs)
    
    def _extract_agent_info(self, obs: np.ndarray):
        """从观察中提取代理信息"""
        # 在 BabyAI 观察中，代理通常用特定值表示
        # 这里简化处理，假设观察包含方向信息
        center = obs.shape[0] // 2 if len(obs.shape) > 0 else 3
        
        # 提取方向 (通常在观察的特定位置)
        if obs.shape[-1] >= 3:
            # 方向编码在第三个通道
            direction_layer = obs[:, :, 2]
            if direction_layer.max() > 0:
                # 找到代理位置
                agent_pos = np.where(direction_layer > 0)
                if len(agent_pos[0]) > 0:
                    self.current_state.position = (int(agent_pos[0][0]), int(agent_pos[1][0]))
                    self.current_state.direction = int(direction_layer[agent_pos[0][0], agent_pos[1][0]]) % 4
    
    def _update_task_progress(self, reward: float, done: bool):
        """更新任务进度"""
        if reward > 0:
            self.current_state.task_progress = min(1.0, self.current_state.task_progress + reward)
        
        if done and reward > 0:
            self.current_state.success = True
            self.success_count += 1
    
    def get_state_vector(self) -> np.ndarray:
        """
        获取状态向量 (12维)
        
        维度说明:
        0: 归一化 x 位置
        1: 归一化 y 位置
        2: 方向编码 (0-1)
        3: 是否携带物品
        4: 探索覆盖率
        5: 任务进度
        6: 步数效率
        7: 交互多样性
        8: 成功状态
        9: 房间类型 (BabyAI 中固定)
        10: 可见目标距离
        11: 环境熵
        """
        vector = np.zeros(self.STATE_DIM, dtype=np.float32)
        
        if self.env is None:
            return vector
        
        # 0-1: 归一化位置
        grid_size = 8.0  # BabyAI 标准网格大小
        vector[0] = self.current_state.position[0] / grid_size
        vector[1] = self.current_state.position[1] / grid_size
        
        # 2: 方向编码
        vector[2] = self.current_state.direction / 3.0
        
        # 3: 是否携带物品
        vector[3] = 1.0 if self.current_state.carrying else 0.0
        
        # 4: 探索覆盖率
        vector[4] = min(len(self.current_state.visited_positions) / 20.0, 1.0)
        
        # 5: 任务进度
        vector[5] = self.current_state.task_progress
        
        # 6: 步数效率
        vector[6] = max(0.0, 1.0 - (self.current_state.step_count / 100.0))
        
        # 7: 交互多样性
        vector[7] = min(len(self.current_state.interacted_objects) / 10.0, 1.0)
        
        # 8: 成功状态
        vector[8] = 1.0 if self.current_state.success else 0.0
        
        # 9: 房间类型 (BabyAI 中固定为 generic)
        vector[9] = 0.5
        
        # 10: 可见目标距离 (简化处理)
        vector[10] = 0.5
        
        # 11: 环境熵 (基于访问位置的变化)
        if len(self.current_state.visited_positions) > 0:
            vector[11] = min(len(self.current_state.visited_positions) / 30.0, 1.0)
        
        return vector
    
    def get_available_actions(self) -> List[str]:
        """获取可用动作"""
        return self.ACTION_NAMES.copy()
    
    def render(self, mode='human'):
        """渲染环境"""
        if self.env:
            return self.env.render(mode=mode)
        return None
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'episodes': self.episode_count,
            'total_steps': self.total_steps,
            'total_reward': self.total_reward,
            'success_count': self.success_count,
            'success_rate': self.success_count / max(self.episode_count, 1),
            'avg_steps': self.total_steps / max(self.episode_count, 1),
            'visited_positions': len(self.current_state.visited_positions),
        }
    
    def close(self):
        """关闭环境"""
        if self.env:
            self.env.close()
            self.env = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


# 兼容性别名
MOSS_BabyAI_Interface = BabyAIAdapter