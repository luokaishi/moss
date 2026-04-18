"""
Reward Aligner - 奖励对齐器

将 TextWorld 奖励与 MOSS 驱动对齐，支持多目标优化
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from .task_parser import TaskState


@dataclass
class AlignedReward:
    """对齐后的奖励信号"""
    total_reward: float
    drive_rewards: Dict[str, float]
    alignment_score: float  # 对齐程度 0-1
    components: Dict[str, float]


class RewardAligner:
    """
    奖励对齐器
    
    将 TextWorld 的外部奖励与 MOSS 内部驱动目标对齐，
    支持多目标优化和奖励分解。
    """
    
    def __init__(self, drive_names: Optional[List[str]] = None):
        self.drive_names = drive_names or [
            'survival', 'optimization', 'curiosity', 'influence'
        ]
        
        # 奖励权重配置
        self.reward_weights = {
            'task_completion': 0.35,
            'efficiency': 0.20,
            'exploration': 0.20,
            'inventory_management': 0.15,
            'safety': 0.10,
        }
        
        # 驱动到奖励的映射权重
        self.drive_reward_mapping = {
            'survival': {
                'safety': 0.5,
                'task_completion': 0.3,
                'inventory_management': 0.2,
            },
            'optimization': {
                'efficiency': 0.5,
                'task_completion': 0.5,
            },
            'curiosity': {
                'exploration': 0.7,
                'efficiency': 0.3,
            },
            'influence': {
                'inventory_management': 0.4,
                'task_completion': 0.4,
                'exploration': 0.2,
            },
        }
        
        # 历史记录
        self.reward_history: List[float] = []
        self.alignment_history: List[float] = []
        
        # 参考值
        self.max_expected_reward = 10.0
        self.optimal_steps = 30
    
    def align(
        self,
        external_reward: float,
        task_state: TaskState,
        step_count: int,
        max_steps: int,
        previous_state: Optional[TaskState] = None
    ) -> AlignedReward:
        """
        对齐外部奖励与 MOSS 驱动
        
        Args:
            external_reward: TextWorld 外部奖励
            task_state: 当前任务状态
            step_count: 当前步数
            max_steps: 最大步数
            previous_state: 上一个状态（用于计算变化）
            
        Returns:
            对齐后的奖励
        """
        # 计算各组件奖励
        components = self._compute_reward_components(
            external_reward, task_state, step_count, max_steps, previous_state
        )
        
        # 计算总奖励
        total_reward = sum(
            components.get(key, 0) * weight
            for key, weight in self.reward_weights.items()
        )
        
        # 计算驱动奖励
        drive_rewards = self._compute_drive_rewards(components)
        
        # 计算对齐分数
        alignment_score = self._compute_alignment_score(
            external_reward, drive_rewards, task_state
        )
        
        # 记录历史
        self.reward_history.append(total_reward)
        self.alignment_history.append(alignment_score)
        
        return AlignedReward(
            total_reward=total_reward,
            drive_rewards=drive_rewards,
            alignment_score=alignment_score,
            components=components
        )
    
    def _compute_reward_components(
        self,
        external_reward: float,
        task_state: TaskState,
        step_count: int,
        max_steps: int,
        previous_state: Optional[TaskState]
    ) -> Dict[str, float]:
        """计算奖励的各个组件"""
        components = {}
        
        # 1. 任务完成奖励
        components['task_completion'] = self._compute_task_completion_reward(
            external_reward, task_state
        )
        
        # 2. 效率奖励
        components['efficiency'] = self._compute_efficiency_reward(
            step_count, max_steps, task_state
        )
        
        # 3. 探索奖励
        components['exploration'] = self._compute_exploration_reward(
            task_state, previous_state
        )
        
        # 4. 库存管理奖励
        components['inventory_management'] = self._compute_inventory_reward(
            task_state, previous_state
        )
        
        # 5. 安全奖励
        components['safety'] = self._compute_safety_reward(
            step_count, max_steps, task_state
        )
        
        return components
    
    def _compute_task_completion_reward(
        self, external_reward: float, task_state: TaskState
    ) -> float:
        """计算任务完成奖励"""
        # 基于外部奖励和进度
        reward = external_reward / max(self.max_expected_reward, 1.0)
        
        # 加上进度奖励
        progress_bonus = task_state.progress * 0.5
        
        return np.clip(reward + progress_bonus, 0, 1)
    
    def _compute_efficiency_reward(
        self, step_count: int, max_steps: int, task_state: TaskState
    ) -> float:
        """计算效率奖励"""
        if task_state.progress <= 0:
            return 0.0
        
        # 理想步数 = 进度 * 最优步数
        ideal_steps = task_state.progress * self.optimal_steps
        actual_steps = step_count
        
        # 效率 = 理想步数 / 实际步数
        if actual_steps > 0:
            efficiency = ideal_steps / actual_steps
        else:
            efficiency = 1.0
        
        return np.clip(efficiency, 0, 1)
    
    def _compute_exploration_reward(
        self, task_state: TaskState, previous_state: Optional[TaskState]
    ) -> float:
        """计算探索奖励"""
        reward = 0.0
        
        # 新房间奖励
        if previous_state and task_state.current_room != previous_state.current_room:
            reward += 0.3
        
        # 新物品奖励
        if previous_state:
            new_objects = set(task_state.visible_objects) - set(previous_state.visible_objects)
            reward += len(new_objects) * 0.1
        
        # 访问出口奖励
        if task_state.available_exits:
            reward += len(task_state.available_exits) * 0.05
        
        return np.clip(reward, 0, 1)
    
    def _compute_inventory_reward(
        self, task_state: TaskState, previous_state: Optional[TaskState]
    ) -> float:
        """计算库存管理奖励"""
        reward = 0.0
        
        # 获取新物品奖励
        if previous_state:
            new_items = set(task_state.inventory) - set(previous_state.inventory)
            reward += len(new_items) * 0.3
        
        # 适度库存奖励（1-3个物品）
        inventory_size = len(task_state.inventory)
        if 1 <= inventory_size <= 3:
            reward += 0.2
        elif inventory_size > 5:
            reward -= 0.1  # 过多物品惩罚
        
        return np.clip(reward, 0, 1)
    
    def _compute_safety_reward(
        self, step_count: int, max_steps: int, task_state: TaskState
    ) -> float:
        """计算安全奖励"""
        # 基于剩余步数
        step_ratio = step_count / max_steps
        safety = 1.0 - step_ratio
        
        # 如果有进度，安全性更高
        if task_state.progress > 0:
            safety += 0.2
        
        return np.clip(safety, 0, 1)
    
    def _compute_drive_rewards(self, components: Dict[str, float]) -> Dict[str, float]:
        """计算各驱动的奖励"""
        drive_rewards = {}
        
        for drive in self.drive_names:
            if drive in self.drive_reward_mapping:
                mapping = self.drive_reward_mapping[drive]
                reward = sum(
                    components.get(component, 0) * weight
                    for component, weight in mapping.items()
                )
                drive_rewards[drive] = np.clip(reward, -1, 1)
            else:
                # 默认：平均分配
                drive_rewards[drive] = np.clip(
                    sum(components.values()) / len(components), -1, 1
                )
        
        return drive_rewards
    
    def _compute_alignment_score(
        self,
        external_reward: float,
        drive_rewards: Dict[str, float],
        task_state: TaskState
    ) -> float:
        """计算对齐分数"""
        # 外部奖励归一化
        normalized_external = external_reward / max(self.max_expected_reward, 1.0)
        
        # 驱动奖励平均值
        avg_drive_reward = np.mean(list(drive_rewards.values())) if drive_rewards else 0
        
        # 对齐程度 = 1 - |外部奖励 - 驱动奖励|
        alignment = 1.0 - abs(normalized_external - avg_drive_reward)
        
        # 进度对齐
        progress_alignment = 1.0 - abs(task_state.progress - avg_drive_reward)
        
        # 综合对齐分数
        return np.clip((alignment + progress_alignment) / 2, 0, 1)
    
    def update_weights(self, performance_feedback: Dict[str, float]):
        """
        基于性能反馈更新奖励权重
        
        Args:
            performance_feedback: 各组件的性能反馈
        """
        for key, feedback in performance_feedback.items():
            if key in self.reward_weights:
                # 根据反馈调整权重
                current_weight = self.reward_weights[key]
                adjustment = feedback * 0.05  # 小幅度调整
                new_weight = np.clip(current_weight + adjustment, 0.05, 0.5)
                self.reward_weights[key] = new_weight
        
        # 归一化
        total = sum(self.reward_weights.values())
        if total > 0:
            self.reward_weights = {
                k: v / total for k, v in self.reward_weights.items()
            }
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        if not self.reward_history:
            return {
                'avg_reward': 0.0,
                'avg_alignment': 0.0,
                'reward_variance': 0.0,
                'current_weights': self.reward_weights.copy(),
            }
        
        return {
            'avg_reward': np.mean(self.reward_history),
            'avg_alignment': np.mean(self.alignment_history),
            'reward_variance': np.var(self.reward_history),
            'current_weights': self.reward_weights.copy(),
            'recent_rewards': self.reward_history[-10:],
        }
    
    def reset(self):
        """重置状态"""
        self.reward_history = []
        self.alignment_history = []


class MultiObjectiveRewardAligner(RewardAligner):
    """
    多目标奖励对齐器
    
    支持帕累托最优的多目标优化
    """
    
    def __init__(self, drive_names: Optional[List[str]] = None, n_objectives: int = 3):
        super().__init__(drive_names)
        self.n_objectives = n_objectives
        self.objective_names = ['completion', 'efficiency', 'exploration']
        self.pareto_front: List[Tuple[float, ...]] = []
    
    def align_multi_objective(
        self,
        external_reward: float,
        task_state: TaskState,
        step_count: int,
        max_steps: int,
        previous_state: Optional[TaskState] = None
    ) -> Dict[str, float]:
        """
        多目标对齐
        
        Returns:
            各目标的奖励值
        """
        # 计算基础组件
        components = self._compute_reward_components(
            external_reward, task_state, step_count, max_steps, previous_state
        )
        
        # 计算多目标
        objectives = {
            'completion': components['task_completion'],
            'efficiency': components['efficiency'],
            'exploration': components['exploration'],
        }
        
        # 更新帕累托前沿
        self._update_pareto_front(tuple(objectives.values()))
        
        return objectives
    
    def _update_pareto_front(self, objectives: Tuple[float, ...]):
        """更新帕累托前沿"""
        # 检查是否被支配
        dominated = False
        to_remove = []
        
        for existing in self.pareto_front:
            # 如果 existing 支配 objectives，则 objectives 被支配
            if all(e >= o for e, o in zip(existing, objectives)) and any(e > o for e, o in zip(existing, objectives)):
                dominated = True
                break
            # 如果 objectives 支配 existing，则移除 existing
            if all(o >= e for o, e in zip(objectives, existing)) and any(o > e for o, e in zip(objectives, existing)):
                to_remove.append(existing)
        
        if not dominated:
            # 移除被支配的解
            for dominated_solution in to_remove:
                self.pareto_front.remove(dominated_solution)
            # 添加新解
            self.pareto_front.append(objectives)
    
    def get_pareto_stats(self) -> Dict:
        """获取帕累托前沿统计"""
        if not self.pareto_front:
            return {'size': 0, 'coverage': 0.0}
        
        return {
            'size': len(self.pareto_front),
            'coverage': len(self.pareto_front) / max(self.n_objectives * 2, 1),
            'solutions': self.pareto_front,
        }
