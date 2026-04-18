"""
Adaptive Action Selector - 自适应动作选择器

基于 MOSS 驱动和任务状态智能选择动作
"""

import random
import numpy as np
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass

from .task_parser import TaskState


@dataclass
class ActionScore:
    """动作评分结果"""
    action: str
    score: float
    drive_contributions: Dict[str, float]
    reason: str


class AdaptiveActionSelector:
    """
    自适应动作选择器
    
    结合 MOSS 驱动信号和任务解析状态，智能选择最优动作
    """
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)
        
        # 动作类型映射
        self.action_types = {
            # 导航
            'go': 'navigation',
            'move': 'navigation',
            'walk': 'navigation',
            'enter': 'navigation',
            'north': 'navigation',
            'south': 'navigation',
            'east': 'navigation',
            'west': 'navigation',
            
            # 获取
            'take': 'acquisition',
            'pick': 'acquisition',
            'grab': 'acquisition',
            'get': 'acquisition',
            
            # 交互
            'drop': 'interaction',
            'put': 'interaction',
            'open': 'interaction',
            'close': 'interaction',
            'lock': 'interaction',
            'unlock': 'interaction',
            'use': 'interaction',
            
            # 探索
            'examine': 'exploration',
            'look': 'exploration',
            'inspect': 'exploration',
            'search': 'exploration',
            'inventory': 'exploration',
            'inv': 'exploration',
            
            # 生存
            'eat': 'survival',
            'drink': 'survival',
            'cook': 'survival',
            'sleep': 'survival',
            'heal': 'survival',
        }
        
        # 驱动权重映射到动作类型
        self.drive_action_mapping = {
            'survival': ['survival', 'acquisition'],
            'optimization': ['interaction', 'acquisition'],
            'curiosity': ['exploration', 'navigation'],
            'influence': ['interaction', 'acquisition'],
            'efficiency': ['navigation', 'interaction'],
            'exploration': ['exploration', 'navigation'],
        }
        
        # 历史记录
        self.action_history: List[str] = []
        self.success_history: List[bool] = []
        self.explored_rooms: set = set()
        self.collected_items: set = set()
        
        # 学习参数
        self.learning_rate = 0.1
        self.exploration_rate = 0.2
        self.action_success_rate: Dict[str, float] = {}
    
    def select_action(
        self,
        admissible_commands: List[str],
        task_state: TaskState,
        drive_scores: Optional[Dict[str, float]] = None,
        step_count: int = 0,
        max_steps: int = 100
    ) -> str:
        """
        选择最优动作
        
        Args:
            admissible_commands: 可用命令列表
            task_state: 当前任务状态
            drive_scores: 驱动评分（可选）
            step_count: 当前步数
            max_steps: 最大步数
            
        Returns:
            选择的动作命令
        """
        if not admissible_commands:
            return "look"
        
        # 评分所有动作
        scored_actions = self._score_actions(
            admissible_commands, task_state, drive_scores, step_count, max_steps
        )
        
        # 探索 vs 利用
        if random.random() < self.exploration_rate:
            # 探索：从高分动作中随机选择
            top_actions = [a for a, s in scored_actions[:min(3, len(scored_actions))]]
            selected = random.choice(top_actions)
        else:
            # 利用：选择最高分
            selected = scored_actions[0][0]
        
        # 记录历史
        self.action_history.append(selected)
        
        return selected
    
    def _score_actions(
        self,
        commands: List[str],
        task_state: TaskState,
        drive_scores: Optional[Dict[str, float]],
        step_count: int,
        max_steps: int
    ) -> List[Tuple[str, float]]:
        """为所有动作评分"""
        scored = []
        
        for cmd in commands:
            score = self._calculate_action_score(
                cmd, task_state, drive_scores, step_count, max_steps
            )
            scored.append((cmd, score))
        
        # 按分数降序排序
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored
    
    def _calculate_action_score(
        self,
        command: str,
        task_state: TaskState,
        drive_scores: Optional[Dict[str, float]],
        step_count: int,
        max_steps: int
    ) -> float:
        """计算单个动作的分数"""
        score = 0.5  # 基础分
        cmd_lower = command.lower()
        
        # 1. 基于任务目标的评分
        goal_bonus = self._goal_based_score(command, task_state)
        score += goal_bonus
        
        # 2. 基于驱动信号的评分
        if drive_scores:
            drive_bonus = self._drive_based_score(command, drive_scores)
            score += drive_bonus
        
        # 3. 基于历史成功率的评分
        success_bonus = self._success_based_score(command)
        score += success_bonus
        
        # 4. 基于探索进度的评分
        exploration_bonus = self._exploration_score(command, task_state)
        score += exploration_bonus
        
        # 5. 时间压力调整
        time_pressure = step_count / max_steps
        if time_pressure > 0.7:
            # 时间紧迫时，优先完成任务
            if self._is_progress_action(command, task_state):
                score += 0.2
        
        # 6. 避免重复
        if command in self.action_history[-3:]:
            score -= 0.3 * (1 + self.action_history[-3:].count(command))
        
        # 7. 避免无效循环
        if len(self.action_history) >= 2:
            # 检测来回移动
            if self._is_backtrack(command):
                score -= 0.4
        
        return max(0.0, min(1.0, score))
    
    def _goal_based_score(self, command: str, task_state: TaskState) -> float:
        """基于任务目标的评分"""
        if not task_state.task_goal:
            return 0.0
        
        cmd_lower = command.lower()
        goal_lower = task_state.task_goal.lower()
        bonus = 0.0
        
        # 钥匙和门类型目标
        if 'key' in goal_lower and 'door' in goal_lower:
            has_key = any('key' in item.lower() for item in task_state.inventory)
            
            if not has_key:
                # 需要找钥匙
                if 'take' in cmd_lower and any('key' in obj.lower() for obj in task_state.visible_objects):
                    bonus += 0.4
                elif 'examine' in cmd_lower and any('key' in obj.lower() for obj in task_state.visible_objects):
                    bonus += 0.2
            else:
                # 有钥匙，需要开门
                if 'open' in cmd_lower or 'unlock' in cmd_lower:
                    bonus += 0.4
                elif 'go' in cmd_lower and task_state.available_exits:
                    bonus += 0.2
        
        # 收集物品目标
        if any(word in goal_lower for word in ['collect', 'take', 'find', 'gather']):
            if 'take' in cmd_lower:
                bonus += 0.3
            elif 'examine' in cmd_lower:
                bonus += 0.15
        
        # 到达某处目标
        if any(word in goal_lower for word in ['go to', 'reach', 'enter', 'find']):
            if 'go' in cmd_lower:
                bonus += 0.25
        
        return bonus
    
    def _drive_based_score(self, command: str, drive_scores: Dict[str, float]) -> float:
        """基于驱动信号的评分"""
        cmd_type = self._classify_action(command)
        bonus = 0.0
        
        # 根据驱动分数加权
        for drive, score in drive_scores.items():
            if drive in self.drive_action_mapping:
                preferred_types = self.drive_action_mapping[drive]
                if cmd_type in preferred_types:
                    bonus += score * 0.3
        
        return bonus
    
    def _success_based_score(self, command: str) -> float:
        """基于历史成功率的评分"""
        if command not in self.action_success_rate:
            return 0.0
        
        success_rate = self.action_success_rate[command]
        return success_rate * 0.2
    
    def _exploration_score(self, command: str, task_state: TaskState) -> float:
        """基于探索的评分"""
        cmd_lower = command.lower()
        bonus = 0.0
        
        # 鼓励去新房间
        if 'go' in cmd_lower or 'move' in cmd_lower:
            for exit_dir in task_state.available_exits:
                if exit_dir.lower() in cmd_lower:
                    # 假设新房间更有价值
                    bonus += 0.15
                    break
        
        # 鼓励检查新物品
        if 'examine' in cmd_lower or 'look' in cmd_lower:
            bonus += 0.1
        
        return bonus
    
    def _is_progress_action(self, command: str, task_state: TaskState) -> bool:
        """判断动作是否有助于任务进展"""
        cmd_lower = command.lower()
        
        # 获取物品通常是进展
        if 'take' in cmd_lower and task_state.visible_objects:
            return True
        
        # 开门通常是进展
        if 'open' in cmd_lower or 'unlock' in cmd_lower:
            return True
        
        # 使用关键物品
        if 'use' in cmd_lower:
            return True
        
        return False
    
    def _is_backtrack(self, command: str) -> bool:
        """检测是否是在来回移动"""
        if len(self.action_history) < 2:
            return False
        
        cmd_lower = command.lower()
        last_cmd = self.action_history[-1].lower()
        
        # 检测相反方向
        opposites = {
            'north': 'south',
            'south': 'north',
            'east': 'west',
            'west': 'east',
        }
        
        for direction, opposite in opposites.items():
            if direction in cmd_lower and opposite in last_cmd:
                return True
            if opposite in cmd_lower and direction in last_cmd:
                return True
        
        return False
    
    def _classify_action(self, command: str) -> str:
        """分类动作类型"""
        cmd_lower = command.lower().split()[0] if command else ''
        
        for prefix, action_type in self.action_types.items():
            if cmd_lower.startswith(prefix):
                return action_type
        
        return 'other'
    
    def update_success_rate(self, command: str, success: bool):
        """更新动作成功率"""
        if command not in self.action_success_rate:
            self.action_success_rate[command] = 0.5
        
        # 指数移动平均
        current = self.action_success_rate[command]
        self.action_success_rate[command] = (
            current * (1 - self.learning_rate) + (1.0 if success else 0.0) * self.learning_rate
        )
        
        self.success_history.append(success)
    
    def update_exploration_rate(self, episode: int, total_episodes: int):
        """动态调整探索率"""
        # 随时间降低探索率
        progress = episode / total_episodes
        self.exploration_rate = max(0.05, 0.3 - progress * 0.25)
    
    def reset(self):
        """重置状态（每局游戏开始时调用）"""
        self.action_history = []
        self.success_history = []
        self.exploration_rate = 0.2
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'action_history_length': len(self.action_history),
            'exploration_rate': self.exploration_rate,
            'unique_actions': len(set(self.action_history)),
            'action_success_rates': self.action_success_rate.copy(),
            'explored_rooms': len(self.explored_rooms),
            'collected_items': len(self.collected_items),
        }