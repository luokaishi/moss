"""
Reward Aligner - 奖励对齐器

将环境奖励与驱动奖励对齐，实现多源奖励信号的有效融合。
支持环境奖励、驱动奖励和进度奖励的动态组合。
"""

import numpy as np
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AlignedReward:
    """对齐后的奖励信号"""
    total: float
    env_component: float
    drive_component: float
    progress_component: float
    raw_env_reward: float
    raw_drive_rewards: Dict[str, float]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RewardConfig:
    """奖励对齐配置"""
    env_weight: float = 0.6
    drive_weight: float = 0.3
    progress_weight: float = 0.1
    
    # 动态调整参数
    enable_adaptive: bool = True
    adaptation_rate: float = 0.05
    
    # 奖励裁剪
    reward_clip_min: float = -10.0
    reward_clip_max: float = 10.0
    
    # 时间折扣
    discount_factor: float = 0.95


class TaskProgressTracker:
    """任务进度跟踪器"""
    
    def __init__(self):
        self.score_history: List[float] = []
        self.step_count: int = 0
        self.room_visits: Dict[str, int] = {}
        self.object_collected: set = set()
        self.interaction_history: List[str] = []
        self.progress_history: List[float] = []
        
    def update(self, score: float, room: str, objects: List[str], 
               interaction: str, max_score: float = 1.0):
        """更新进度状态"""
        self.step_count += 1
        self.score_history.append(score)
        
        # 记录房间访问
        self.room_visits[room] = self.room_visits.get(room, 0) + 1
        
        # 记录收集的物品
        for obj in objects:
            self.object_collected.add(obj)
        
        # 记录交互
        self.interaction_history.append(interaction)
        
        # 计算进度
        progress = self._calculate_progress(score, max_score)
        self.progress_history.append(progress)
        
        return progress
    
    def _calculate_progress(self, score: float, max_score: float) -> float:
        """计算任务进度"""
        if max_score > 0:
            score_progress = score / max_score
        else:
            score_progress = 0.0
        
        # 探索进度
        exploration_progress = min(len(self.room_visits) / 10.0, 1.0)
        
        # 收集进度
        collection_progress = min(len(self.object_collected) / 5.0, 1.0)
        
        # 综合进度
        return 0.6 * score_progress + 0.2 * exploration_progress + 0.2 * collection_progress
    
    def get_progress_delta(self) -> float:
        """获取最近进度变化"""
        if len(self.progress_history) < 2:
            return 0.0
        return self.progress_history[-1] - self.progress_history[-2]
    
    def get_efficiency(self) -> float:
        """计算任务效率（进度/步数）"""
        if self.step_count == 0:
            return 0.0
        current_progress = self.progress_history[-1] if self.progress_history else 0.0
        return current_progress / self.step_count
    
    def reset(self):
        """重置跟踪器"""
        self.score_history.clear()
        self.step_count = 0
        self.room_visits.clear()
        self.object_collected.clear()
        self.interaction_history.clear()
        self.progress_history.clear()


class RewardAligner:
    """
    奖励对齐器
    
    将环境奖励与驱动奖励对齐，支持：
    - 环境奖励 (任务完成)
    - 驱动奖励 (内部动机)
    - 进度奖励 (向目标进展)
    """
    
    def __init__(self, config: Optional[RewardConfig] = None):
        """
        初始化奖励对齐器
        
        Args:
            config: 奖励对齐配置
        """
        self.config = config or RewardConfig()
        
        # 进度跟踪
        self.progress_tracker = TaskProgressTracker()
        
        # 历史记录
        self.reward_history: List[AlignedReward] = []
        self.env_reward_history: List[float] = []
        self.drive_reward_history: List[float] = []
        
        # 动态权重
        self.current_env_weight = self.config.env_weight
        self.current_drive_weight = self.config.drive_weight
        self.current_progress_weight = self.config.progress_weight
        
        # 性能统计
        self.total_episodes = 0
        self.cumulative_reward = 0.0
        
    def align(self, 
              env_reward: float,
              drive_rewards: Dict[str, float],
              task_progress: Optional[float] = None,
              info: Optional[Dict[str, Any]] = None) -> AlignedReward:
        """
        对齐奖励信号
        
        Args:
            env_reward: 环境奖励
            drive_rewards: 驱动奖励字典
            task_progress: 任务进度 (0-1)
            info: 额外信息
            
        Returns:
            对齐后的奖励
        """
        # 裁剪环境奖励
        env_reward = np.clip(env_reward, 
                            self.config.reward_clip_min, 
                            self.config.reward_clip_max)
        
        # 计算驱动奖励总和
        drive_sum = sum(drive_rewards.values())
        
        # 计算进度奖励
        if task_progress is None and info:
            task_progress = self._estimate_progress_from_info(info)
        task_progress = task_progress or 0.0
        
        # 进度变化奖励
        progress_delta = 0.0
        if len(self.progress_tracker.progress_history) > 0:
            progress_delta = task_progress - self.progress_tracker.progress_history[-1]
        
        # 动态调整权重
        if self.config.enable_adaptive:
            self._adapt_weights(env_reward, drive_sum, progress_delta)
        
        # 计算对齐奖励
        env_component = self.current_env_weight * env_reward
        drive_component = self.current_drive_weight * drive_sum
        progress_component = self.current_progress_weight * (progress_delta * 10.0)  # 放大变化
        
        total_reward = env_component + drive_component + progress_component
        
        # 创建对齐奖励对象
        aligned = AlignedReward(
            total=total_reward,
            env_component=env_component,
            drive_component=drive_component,
            progress_component=progress_component,
            raw_env_reward=env_reward,
            raw_drive_rewards=drive_rewards.copy()
        )
        
        # 记录历史
        self.reward_history.append(aligned)
        self.env_reward_history.append(env_reward)
        self.drive_reward_history.append(drive_sum)
        self.cumulative_reward += total_reward
        
        # 更新进度跟踪
        if info:
            self.progress_tracker.update(
                score=info.get('score', 0.0),
                room=info.get('location', 'unknown'),
                objects=info.get('inventory', []),
                interaction=info.get('last_action', ''),
                max_score=info.get('max_score', 1.0)
            )
        
        return aligned
    
    def _estimate_progress_from_info(self, info: Dict[str, Any]) -> float:
        """从信息字典估计进度"""
        score = info.get('score', 0.0)
        max_score = info.get('max_score', 1.0)
        
        if max_score > 0:
            score_progress = score / max_score
        else:
            score_progress = 0.0
        
        # 考虑其他指标
        visited_rooms = len(info.get('visited_rooms', []))
        room_progress = min(visited_rooms / 10.0, 1.0)
        
        inventory = info.get('inventory', [])
        collection_progress = min(len(inventory) / 5.0, 1.0)
        
        return 0.6 * score_progress + 0.2 * room_progress + 0.2 * collection_progress
    
    def _adapt_weights(self, env_reward: float, drive_sum: float, progress_delta: float):
        """动态调整权重"""
        # 如果环境奖励高，增强环境权重
        if env_reward > 1.0:
            self.current_env_weight = min(0.8, self.current_env_weight + self.config.adaptation_rate)
        
        # 如果进度停滞，增强驱动权重

    def _default_task_reward(self, state, info):
        return 0.0

    def _collection_task_reward(self, state, info):
        return 0.0

    def _delivery_task_reward(self, state, info):
        return 0.0
