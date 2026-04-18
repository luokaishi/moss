"""
MiniGrid Adapter - MOSS v6.2 多环境训练

适配 MiniGrid 环境到 MOSS Agent
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path

# 尝试导入 MiniGrid
try:
    import gym
    import gymnasium
    from gymnasium import spaces
    MINIGRID_AVAILABLE = True
except ImportError:
    MINIGRID_AVAILABLE = False
    gymnasium = None
    gym = None
    spaces = None

try:
    from minigrid.minigrid_env import MiniGridEnv
    from minigrid.core.world_object import WorldObj
    MINIGRID_IMPORT_SUCCESS = True
except ImportError:
    MINIGRID_IMPORT_SUCCESS = False
    MiniGridEnv = None
    WorldObj = None


@dataclass
class MiniGridState:
    """MiniGrid 游戏状态封装"""
    observation: Dict = field(default_factory=dict)
    mission: str = ""
    direction: int = 0  # 0-3: right, down, left, up
    position: Tuple[int, int] = (0, 0)
    carrying: Optional[Any] = None
    done: bool = False
    success: bool = False
    
    # MOSS 特定
    step_count: int = 0
    visited_positions: set = field(default_factory=set)
    interacted_objects: set = field(default_factory=set)
    task_progress: float = 0.0
    
    # MiniGrid 特定
    grid_width: int = 8
    grid_height: int = 8


class MiniGridAdapter:
    """MiniGrid 环境适配器"""
    
    # 状态向量维度 (固定 12 维)
    STATE_DIM = 12
    
    # 动作映射 (MiniGrid 标准动作)
    ACTION_NAMES = [
        'turn_left',      # 0
        'turn_right',     # 1
        'move_forward',   # 2
        'pickup',         # 3
        'drop',           # 4
        'toggle',         # 5
        'done',           # 6
    ]
    ACTION_IDS = {name: i for i, name in enumerate(ACTION_NAMES)}
    
    # 方向映射
    DIRECTION_NAMES = ['right', 'down', 'left', 'up']
    
    # 对象类型映射
    OBJECT_TYPES = {
        'unseen': 0, 'empty': 1, 'wall': 2, 'floor': 3,
        'door': 4, 'locked_door': 5, 'key': 6, 'ball': 7,
        'box': 8, 'goal': 9, 'lava': 10, 'agent': 11
    }
    
    def __init__(self, env_name='MiniGrid-Empty-5x5-v0'):
        self.env_name = env_name
        self.env = None
        self.current_state = MiniGridState()
        self._prev_obs = None
        
        # 统计信息
        self.episode_count = 0
        self.total_steps = 0
        self.total_reward = 0.0
        self.success_count = 0
        
        self._init_env()
    
    def _init_env(self):
        """初始化环境"""
        try:
            if MINIGRID_AVAILABLE:
                # 优先使用 gymnasium
                if gymnasium is not None:
                    self.env = gymnasium.make(self.env_name)
                elif gym is not None:
                    self.env = gym.make(self.env_name)
                else:
                    print("Neither gymnasium nor gym available")
            else:
                print("MiniGrid not installed. Install with: pip install minigrid")
        except Exception as e:
            print(f"Error initializing MiniGrid environment: {e}")
    
    def reset(self, seed: Optional[int] = None) -> Tuple[Dict, str]:
        """重置环境"""
        if self.env is None:
            return None, ""
        
        self.episode_count += 1
        
        # 支持不同的 reset 接口
        try:
            if seed is not None:
                obs, info = self.env.reset(seed=seed)
            else:
                result = self.env.reset()
                if isinstance(result, tuple):
                    obs, info = result
                else:
                    obs = result
                    info = {}
        except Exception as e:
            # 回退到简单 reset
            obs = self.env.reset()
            info = {}
        
        # 解析观察
        mission = obs.get('mission', '') if isinstance(obs, dict) else getattr(self.env, 'mission', '')
        self._parse_observation(obs, mission)
        self.current_state.visited_positions.clear()
        self.current_state.interacted_objects.clear()
        self.current_state.step_count = 0
        self.current_state.success = False
        
        return obs, mission
    
    def step(self, action: Union[str, int]) -> Tuple[Dict, float, bool, Dict]:
        """执行动作"""
        if self.env is None:
            return None, 0.0, True, {}
        
        # 转换动作
        if isinstance(action, str):
            action_id = self.ACTION_IDS.get(action, 0)
        else:
            action_id = action
        
        # 执行动作
        try:
            result = self.env.step(action_id)
            if len(result) == 5:
                obs, reward, terminated, truncated, info = result
                done = terminated or truncated
            else:
                obs, reward, done, info = result
        except Exception as e:
            print(f"Error in step: {e}")
            return None, 0.0, True, {}
        
        # 更新统计
        self.total_steps += 1
        self.total_reward += reward
        self.current_state.step_count += 1
        
        # 解析新观察
        mission = obs.get('mission', '') if isinstance(obs, dict) else getattr(self.env, 'mission', '')
        self._parse_observation(obs, mission)
        
        # 跟踪位置
        if self.current_state.position:
            self.current_state.visited_positions.add(self.current_state.position)
        
        # 更新任务进度
        self._update_task_progress(reward, done)
        
        return obs, float(reward), done, info
    
    def _parse_observation(self, obs: Any, mission: str):
        """解析观察"""
        self.current_state.observation = obs if isinstance(obs, dict) else {'image': obs}
        self.current_state.mission = mission
        
        # 从环境中提取代理状态
        if self.env is not None:
            try:
                # MiniGrid 环境通常有 agent_pos 和 agent_dir 属性
                if hasattr(self.env, 'agent_pos'):
                    self.current_state.position = tuple(self.env.agent_pos)
                if hasattr(self.env, 'agent_dir'):
                    self.current_state.direction = self.env.agent_dir
                if hasattr(self.env, 'carrying'):
                    self.current_state.carrying = self.env.carrying
                if hasattr(self.env, 'width'):
                    self.current_state.grid_width = self.env.width
                if hasattr(self.env, 'height'):
                    self.current_state.grid_height = self.env.height
            except Exception as e:
                pass  # 忽略解析错误
    
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
        9: 网格大小 (归一化)
        10: 到目标的估计距离
        11: 环境熵
        """
        vector = np.zeros(self.STATE_DIM, dtype=np.float32)
        
        if self.env is None:
            return vector
        
        # 0-1: 归一化位置
        vector[0] = self.current_state.position[0] / max(self.current_state.grid_width, 1)
        vector[1] = self.current_state.position[1] / max(self.current_state.grid_height, 1)
        
        # 2: 方向编码
        vector[2] = self.current_state.direction / 3.0
        
        # 3: 是否携带物品
        vector[3] = 1.0 if self.current_state.carrying else 0.0
        
        # 4: 探索覆盖率
        grid_size = self.current_state.grid_width * self.current_state.grid_height
        vector[4] = min(len(self.current_state.visited_positions) / max(grid_size * 0.5, 1), 1.0)
        
        # 5: 任务进度
        vector[5] = self.current_state.task_progress
        
        # 6: 步数效率
        vector[6] = max(0.0, 1.0 - (self.current_state.step_count / 100.0))
        
        # 7: 交互多样性
        vector[7] = min(len(self.current_state.interacted_objects) / 10.0, 1.0)
        
        # 8: 成功状态
        vector[8] = 1.0 if self.current_state.success else 0.0
        
        # 9: 网格大小
        vector[9] = min((self.current_state.grid_width * self.current_state.grid_height) / 100.0, 1.0)
        
        # 10: 到目标的估计距离
        # 简化：使用到中心点的距离作为代理
        center_x = self.current_state.grid_width / 2
        center_y = self.current_state.grid_height / 2
        dist = np.sqrt((self.current_state.position[0] - center_x) ** 2 + 
                       (self.current_state.position[1] - center_y) ** 2)
        max_dist = np.sqrt(center_x ** 2 + center_y ** 2)
        vector[10] = 1.0 - min(dist / max(max_dist, 1), 1.0)
        
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
            try:
                return self.env.render(mode=mode)
            except:
                # 尝试不同的 render 接口
                return self.env.render()
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
            'grid_size': (self.current_state.grid_width, self.current_state.grid_height),
        }
    
    def close(self):
        """关闭环境"""
        if self.env:
            try:
                self.env.close()
            except:
                pass
            self.env = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


# 兼容性别名
MOSS_MiniGrid_Interface = MiniGridAdapter
