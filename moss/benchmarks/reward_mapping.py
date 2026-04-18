"""
Reward Mapping - TextWorld 奖励到 MOSS 驱动的映射

将 TextWorld 的游戏奖励转换为 MOSS DriveManager 可理解的驱动信号。
支持分解奖励到多个驱动维度，便于涌现行为分析。
"""

import numpy as np
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DriveReward:
    """单个驱动的奖励信号"""
    drive_name: str
    reward: float
    weight: float = 1.0
    description: str = ""
    source: str = ""  # 奖励来源 (score, exploration, etc.)


@dataclass
class RewardContext:
    """奖励计算的上下文信息"""
    previous_score: float = 0.0
    current_score: float = 0.0
    steps_taken: int = 0
    rooms_visited: int = 0
    objects_collected: int = 0
    unique_interactions: int = 0
    task_progress: float = 0.0
    won: bool = False
    lost: bool = False
    
    # 历史记录
    score_history: List[float] = field(default_factory=list)
    room_history: List[str] = field(default_factory=list)
    action_history: List[str] = field(default_factory=list)


class TextWorldRewardMapper:
    """
    TextWorld 奖励到 MOSS 驱动的映射器
    
    将 TextWorld 的游戏奖励分解为 MOSS 驱动系统的奖励信号：
    - survival: 基础生存奖励
    - optimization: 任务完成效率
    - curiosity: 新区域探索
    - influence: 物品收集/交互
    
    支持自定义奖励函数和权重配置。
    """
    
    # 默认驱动权重
    DEFAULT_DRIVE_WEIGHTS = {
        'survival': 0.25,
        'optimization': 0.25,
        'curiosity': 0.25,
        'influence': 0.25,
    }
    
    def __init__(self, drive_weights: Optional[Dict[str, float]] = None):
        """
        初始化奖励映射器
        
        Args:
            drive_weights: 各驱动的权重配置，默认平均分配
        """
        self.drive_weights = drive_weights or self.DEFAULT_DRIVE_WEIGHTS.copy()
        self.context = RewardContext()
        
        # 注册内置奖励计算器
        self._reward_calculators: Dict[str, Callable] = {
            'survival': self._calc_survival_reward,
            'optimization': self._calc_optimization_reward,
            'curiosity': self._calc_curiosity_reward,
            'influence': self._calc_influence_reward,
        }
        
        # 统计信息
        self._total_episodes = 0
        self._cumulative_rewards: Dict[str, float] = {
            k: 0.0 for k in self.drive_weights.keys()
        }
    
    def map_reward(
        self,
        tw_reward: float,
        info: Dict[str, Any],
        previous_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """
        将 TextWorld 奖励分解为 MOSS 驱动奖励
        
        Args:
            tw_reward: TextWorld 原始奖励
            info: 当前步骤的 info 字典
            previous_info: 上一步的 info 字典（用于计算变化）
            
        Returns:
            Dict mapping drive names to reward values
        """
        # 更新上下文
        self._update_context(tw_reward, info, previous_info)
        
        # 计算各驱动奖励
        drive_rewards = {}
        
        for drive_name, calculator in self._reward_calculators.items():
            weight = self.drive_weights.get(drive_name, 0.25)
            reward = calculator(tw_reward, info, previous_info)
            drive_rewards[drive_name] = reward * weight
        
        # 更新累计奖励
        for drive, reward in drive_rewards.items():
            self._cumulative_rewards[drive] += reward
        
        return drive_rewards
    
    def _update_context(
        self,
        tw_reward: float,
        info: Dict[str, Any],
        previous_info: Optional[Dict[str, Any]]
    ):
        """更新奖励计算上下文"""
        self.context.previous_score = self.context.current_score
        self.context.current_score += tw_reward
        self.context.steps_taken += 1
        
        # 更新访问房间数
        visited = info.get('visited_rooms', [])
        self.context.rooms_visited = len(visited)
        
        # 更新库存
        inventory = info.get('inventory', [])
        self.context.objects_collected = len(inventory)
        
        # 更新交互
        unique_interactions = info.get('unique_interactions', 0)
        self.context.unique_interactions = unique_interactions
        
        # 更新任务进度
        self.context.task_progress = info.get('task_progress', 0.0)
        
        # 更新状态
        self.context.won = info.get('won', False)
        self.context.lost = info.get('lost', False)
        
        # 更新历史
        self.context.score_history.append(self.context.current_score)
        if len(self.context.score_history) > 100:
            self.context.score_history = self.context.score_history[-100:]
        
        current_room = info.get('location', 'unknown')
        if current_room not in self.context.room_history:
            self.context.room_history.append(current_room)
    
    def _calc_survival_reward(
        self,
        tw_reward: float,
        info: Dict[str, Any],
        previous_info: Optional[Dict[str, Any]]
    ) -> float:
        """
        计算生存驱动奖励
        
        基于：
        - 未死亡 = 基础奖励
        - 健康状态（无负面事件）
        - 资源充足（库存管理）
        """
        reward = 0.0
        
        # 基础生存：未死亡
        if not info.get('lost', False):
            reward += 0.1
        
        # 避免失败惩罚
        if info.get('lost', False):
            reward -= 1.0
        
        # 资源管理：适度库存是健康的
        inventory = info.get('inventory', [])
        inventory_size = len(inventory)
        if 1 <= inventory_size <= 3:
            reward += 0.1  # 适度携带物品
        elif inventory_size > 5:
            reward -= 0.05  # 过度携带
        
        # 稳定进展奖励
        if tw_reward > 0:
            reward += 0.05
        
        return np.clip(reward, -1.0, 1.0)
    
    def _calc_optimization_reward(
        self,
        tw_reward: float,
        info: Dict[str, Any],
        previous_info: Optional[Dict[str, Any]]
    ) -> float:
        """
        计算优化驱动奖励
        
        基于：
        - 任务完成效率（高分/步数比）
        - 直接任务进展
        - 最优路径选择
        """
        reward = 0.0
        
        # 任务完成奖励
        if info.get('won', False):
            # 计算效率：步数越少，奖励越高
            steps = self.context.steps_taken
            efficiency = max(0, 1.0 - (steps / 50.0))  # 假设50步为基准
            reward += 1.0 + efficiency
        
        # 分数增长奖励
        if tw_reward > 0:
            reward += tw_reward * 0.5
            
            # 连续得分奖励（效率指标）
            if len(self.context.score_history) >= 2:
                recent_scores = self.context.score_history[-5:]
                if len(recent_scores) >= 2 and all(s > 0 for s in recent_scores):
                    reward += 0.1  # 持续进展奖励
        
        # 任务进度奖励
        task_progress = info.get('task_progress', 0.0)
        if previous_info:
            prev_progress = previous_info.get('task_progress', 0.0)
            progress_delta = task_progress - prev_progress
            if progress_delta > 0:
                reward += progress_delta * 2.0
        
        return np.clip(reward, -1.0, 1.0)
    
    def _calc_curiosity_reward(
        self,
        tw_reward: float,
        info: Dict[str, Any],
        previous_info: Optional[Dict[str, Any]]
    ) -> float:
        """
        计算好奇驱动奖励
        
        基于：
        - 新区域探索
        - 新物品发现
        - 新交互尝试
        - 环境熵（变化度）
        """
        reward = 0.0
        
        # 新房间探索奖励
        current_room = info.get('location', 'unknown')
        if previous_info:
            prev_room = previous_info.get('location', 'unknown')
            if current_room != prev_room:
                # 检查是否为新房间
                if current_room not in self.context.room_history[:-1]:
                    reward += 0.3  # 新房间奖励
                else:
                    reward += 0.05  # 移动奖励
        
        # 新物品发现
        visible_objects = info.get('objects_visible', [])
        if previous_info:
            prev_objects = previous_info.get('objects_visible', [])
            new_objects = set(visible_objects) - set(prev_objects)
            reward += len(new_objects) * 0.15
        
        # 新交互尝试
        unique_interactions = info.get('unique_interactions', 0)
        if previous_info:
            prev_interactions = previous_info.get('unique_interactions', 0)
            if unique_interactions > prev_interactions:
                reward += 0.1
        
        # 环境多样性奖励（可见物品数）
        if len(visible_objects) >= 3:
            reward += 0.05
        
        # 尝试新动作的奖励（即使没有成功）
        if info.get('action_failed', False) == False:
            reward += 0.02
        
        return np.clip(reward, -1.0, 1.0)
    
    def _calc_influence_reward(
        self,
        tw_reward: float,
        info: Dict[str, Any],
        previous_info: Optional[Dict[str, Any]]
    ) -> float:
        """
        计算影响力驱动奖励
        
        基于：
        - 物品收集
        - 物品使用/交互
        - 环境改变（开门等）
        - 任务完成
        """
        reward = 0.0
        
        # 物品收集奖励
        inventory = info.get('inventory', [])
        if previous_info:
            prev_inventory = previous_info.get('inventory', [])
            new_items = set(inventory) - set(prev_inventory)
            reward += len(new_items) * 0.4
        
        # 物品使用奖励
        if tw_reward > 0 and len(inventory) < len(prev_inventory if previous_info else []):
            # 使用了物品（库存减少但有奖励）
            reward += 0.3
        
        # 环境改变检测
        room_type = info.get('room_type', '')
        if previous_info:
            prev_room_type = previous_info.get('room_type', '')
            if room_type != prev_room_type:
                reward += 0.2
        
        # 解锁/开门奖励
        exits = info.get('exits', [])
        if previous_info:
            prev_exits = previous_info.get('exits', [])
            new_exits = set(exits) - set(prev_exits)
            reward += len(new_exits) * 0.25
        
        # 胜利奖励（最大影响力）
        if info.get('won', False):
            reward += 1.0
        
        return np.clip(reward, -1.0, 1.0)
    
    def get_drive_rewards(self) -> List[DriveReward]:
        """
        获取当前步骤的详细驱动奖励信息
        
        Returns:
            List of DriveReward objects
        """
        rewards = []
        
        for drive_name, calculator in self._reward_calculators.items():
            weight = self.drive_weights.get(drive_name, 0.25)
            # 使用当前上下文计算
            raw_reward = calculator(
                self.context.current_score - self.context.previous_score,
                {'task_progress': self.context.task_progress},
                None
            )
            
            rewards.append(DriveReward(
                drive_name=drive_name,
                reward=raw_reward,
                weight=weight,
                description=f"{drive_name} drive reward",
                source="current_step"
            ))
        
        return rewards
    
    def get_cumulative_rewards(self) -> Dict[str, float]:
        """获取累计驱动奖励"""
        return self._cumulative_rewards.copy()
    
    def get_context_summary(self) -> Dict[str, Any]:
        """获取上下文摘要"""
        return {
            'steps_taken': self.context.steps_taken,
            'current_score': self.context.current_score,
            'rooms_visited': self.context.rooms_visited,
            'objects_collected': self.context.objects_collected,
            'unique_interactions': self.context.unique_interactions,
            'task_progress': self.context.task_progress,
            'won': self.context.won,
            'lost': self.context.lost,
        }
    
    def reset(self):
        """重置奖励映射器状态"""
        self.context = RewardContext()
        self._total_episodes += 1
        self._cumulative_rewards = {
            k: 0.0 for k in self.drive_weights.keys()
        }
    
    def set_drive_weights(self, weights: Dict[str, float]):
        """
        动态设置驱动权重
        
        Args:
            weights: 新的驱动权重字典
        """
        self.drive_weights.update(weights)
        
        # 归一化
        total = sum(self.drive_weights.values())
        if total > 0:
            self.drive_weights = {
                k: v / total for k, v in self.drive_weights.items()
            }
    
    def register_custom_calculator(
        self,
        drive_name: str,
        calculator: Callable[[float, Dict, Optional[Dict]], float]
    ):
        """
        注册自定义奖励计算器
        
        Args:
            drive_name: 驱动名称
            calculator: 奖励计算函数
        """
        self._reward_calculators[drive_name] = calculator
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'episodes': self._total_episodes,
            'cumulative_rewards': self._cumulative_rewards.copy(),
            'drive_weights': self.drive_weights.copy(),
            'context': self.get_context_summary(),
        }


class AdaptiveRewardMapper(TextWorldRewardMapper):
    """
    自适应奖励映射器
    
    根据 Agent 的表现动态调整驱动权重，
    用于研究涌现行为的最佳奖励配置。
    """
    
    def __init__(self, drive_weights: Optional[Dict[str, float]] = None):
        super().__init__(drive_weights)
        
        # 性能历史
        self._performance_history: Dict[str, List[float]] = {
            'success_rate': [],
            'avg_reward': [],
            'exploration_ratio': [],
        }
        
        # 自适应配置
        self._adaptation_rate = 0.05
        self._adaptation_interval = 10  # 每10步调整一次
    
    def map_reward(
        self,
        tw_reward: float,
        info: Dict[str, Any],
        previous_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """映射奖励并可能调整权重"""
        # 标准映射
        rewards = super().map_reward(tw_reward, info, previous_info)
        
        # 更新性能历史
        self._update_performance_history(rewards, info)
        
        # 定期调整权重
        if self.context.steps_taken % self._adaptation_interval == 0:
            self._adapt_weights()
        
        return rewards
    
    def _update_performance_history(
        self,
        rewards: Dict[str, float],
        info: Dict[str, Any]
    ):
        """更新性能历史"""
        self._performance_history['avg_reward'].append(
            sum(rewards.values()) / len(rewards)
        )
        
        # 探索比例
        rooms_visited = info.get('visited_rooms', [])
        total_possible = 10  # 假设
        exploration_ratio = len(rooms_visited) / total_possible
        self._performance_history['exploration_ratio'].append(exploration_ratio)
        
        # 限制历史长度
        for key in self._performance_history:
            if len(self._performance_history[key]) > 100:
                self._performance_history[key] = self._performance_history[key][-100:]
    
    def _adapt_weights(self):
        """根据性能历史调整权重"""
        if len(self._performance_history['avg_reward']) < 10:
            return
        
        # 计算近期趋势
        recent_rewards = self._performance_history['avg_reward'][-10:]
        reward_trend = recent_rewards[-1] - recent_rewards[0]
        
        # 根据趋势调整
        if reward_trend > 0:
            # 表现改善，略微增强当前主导驱动
            max_drive = max(self._cumulative_rewards, key=self._cumulative_rewards.get)
            self.drive_weights[max_drive] += self._adaptation_rate
        else:
            # 表现下降，尝试增强探索
            self.drive_weights['curiosity'] += self._adaptation_rate
        
        # 归一化
        self.set_drive_weights(self.drive_weights)
    
    def get_adaptation_stats(self) -> Dict[str, Any]:
        """获取自适应统计"""
        return {
            'performance_history': {
                k: v[-20:] for k, v in self._performance_history.items()
            },
            'adaptation_rate': self._adaptation_rate,
            'current_weights': self.drive_weights.copy(),
        }