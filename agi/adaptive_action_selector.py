"""
Adaptive Action Selector - 自适应动作选择器

针对外部环境的自适应动作选择器，结合任务目标和驱动评估，
实现任务导向与探索平衡的动作选择策略。
"""

import re
import random
import numpy as np
from typing import List, Dict, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TaskGoal:
    """任务目标表示"""
    description: str = ""                    # 任务描述
    target_objects: List[str] = field(default_factory=list)   # 目标物品
    target_location: str = ""                # 目标位置
    required_actions: List[str] = field(default_factory=list) # 需要的动作序列
    completion_condition: Optional[Callable] = None  # 完成条件函数
    
    def is_completed(self, state: Dict[str, Any]) -> bool:
        """检查任务是否完成"""
        if self.completion_condition:
            return self.completion_condition(state)
        return False


@dataclass
class ActionScore:
    """动作评分结果"""
    action: str
    task_score: float
    drive_score: float
    combined_score: float
    exploration_bonus: float = 0.0


class TaskParser:
    """任务解析器 - 解析观察文本提取任务信息"""
    
    def __init__(self):
        self.room_keywords = {
            'kitchen': ['kitchen', 'cook', 'stove', 'fridge'],
            'bedroom': ['bedroom', 'bed', 'sleep'],
            'living': ['living', 'sofa', 'couch'],
            'hallway': ['hallway', 'corridor', 'hall'],
            'garden': ['garden', 'yard', 'outside'],
            'dungeon': ['dungeon', 'cellar', 'basement'],
        }
        
        self.object_keywords = {
            'key': ['key', 'keys'],
            'door': ['door', 'doors'],
            'chest': ['chest', 'box', 'chests'],
            'food': ['food', 'apple', 'bread', 'meal'],
            'tool': ['tool', 'knife', 'sword', 'hammer'],
        }
    
    def parse_current_room(self, observation: str) -> str:
        """从观察文本解析当前房间"""
        obs_lower = observation.lower()
        
        # 尝试匹配房间类型
        for room_type, keywords in self.room_keywords.items():
            if any(kw in obs_lower for kw in keywords):
                return room_type
        
        # 尝试提取房间名称
        patterns = [
            r'-=\s*([^=]+)\s*=-',
            r'you are in (?:the )?([^.]+)',
            r'you are in (?:a )?([^.]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, obs_lower)
            if match:
                return match.group(1).strip()
        
        return "unknown"
    
    def parse_visible_objects(self, observation: str) -> List[str]:
        """从观察文本解析可见物品"""
        objects = []
        obs_lower = observation.lower()
        
        # 查找物品关键词
        for obj_type, keywords in self.object_keywords.items():
            if any(kw in obs_lower for kw in keywords):
                objects.append(obj_type)
        
        # 通用物品提取
        patterns = [
            r'(?:you see|there is|there are):?\s*([^.]+)',
            r'(?:here you see|visible):\s*([^.]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, obs_lower)
            if match:
                items_text = match.group(1)
                # 分割并清理
                items = re.split(r',\s*|\s+and\s+', items_text)
                for item in items:
                    item = item.strip()
                    item = re.sub(r'^(a|an|the|some)\s+', '', item)
                    if item and item not in objects:
                        objects.append(item)
        
        return objects
    
    def parse_exits(self, observation: str) -> List[str]:
        """从观察文本解析可用出口"""
        exits = []
        obs_lower = observation.lower()
        
        patterns = [
            r'(?:exits?|you can go):?\s*([^.]+)',
            r'(?:possible exits|directions):\s*([^.]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, obs_lower)
            if match:
                exits_text = match.group(1)
                directions = re.split(r',\s*|\s+and\s+', exits_text)
                exits = [d.strip() for d in directions if d.strip()]
                break
        
        # 如果没有匹配到，尝试直接查找方向词
        if not exits:
            directions = ['north', 'south', 'east', 'west', 'up', 'down']
            for direction in directions:
                if direction in obs_lower:
                    exits.append(direction)
        
        return exits
    
    def parse_task_goal(self, observation: str) -> Optional[TaskGoal]:
        """从观察文本解析任务目标"""
        obs_lower = observation.lower()
        
        # 检测任务类型
        goal = TaskGoal()
        
        # 寻找钥匙任务
        if 'key' in obs_lower:
            goal.target_objects.append('key')
            goal.description = "Find and use the key"
        
        # 寻找门任务
        if 'door' in obs_lower or 'locked' in obs_lower:
            goal.target_objects.append('door')
            if 'key' in obs_lower:
                goal.required_actions = ['take key', 'unlock door', 'open door']
                goal.description = "Unlock the door with the key"
        
        # 收集任务
        if any(word in obs_lower for word in ['collect', 'find', 'gather']):
            goal.description = "Collect required items"
        
        # 逃脱任务
        if any(word in obs_lower for word in ['escape', 'exit', 'leave']):
            goal.description = "Find the exit and escape"
            goal.required_actions = ['find exit', 'go exit']
        
        return goal if goal.description else None
    
    def parse_progress(self, observation: str, inventory: List[str], 
                       score: float, max_score: float) -> float:
        """解析任务进度"""
        if max_score > 0:
            score_progress = score / max_score
        else:
            score_progress = 0.0
        
        # 基于库存的进度
        inventory_progress = min(len(inventory) / 5.0, 1.0)
        
        # 综合进度
        return 0.7 * score_progress + 0.3 * inventory_progress


class AdaptiveActionSelector:
    """
    自适应动作选择器
    
    针对外部环境的自适应动作选择策略，结合：
    - 任务目标导向
    - 驱动评估
    - 探索与利用平衡
    """
    
    def __init__(self, 
                 exploration_rate: float = 0.3,
                 task_focus: float = 0.7,
                 drive_weight: float = 0.3,
                 task_weight: float = 0.7,
                 learning_rate: float = 0.1):
        """
        初始化自适应动作选择器
        
        Args:
            exploration_rate: 探索率 (0-1)
            task_focus: 任务专注度 (0-1)
            drive_weight: 驱动评分权重
            task_weight: 任务评分权重
            learning_rate: 学习率
        """
        self.exploration_rate = exploration_rate
        self.task_focus = task_focus
        self.drive_weight = drive_weight
        self.task_weight = task_weight
        self.learning_rate = learning_rate
        
        # 任务解析器
        self.task_parser = TaskParser()
        
        # 动作历史和学习
        self.action_history: List[str] = []
        self.action_success_counts: Dict[str, int] = {}
        self.action_attempt_counts: Dict[str, int] = {}
        
        # 任务状态跟踪
        self.current_task: Optional[TaskGoal] = None
        self.task_progress_history: List[float] = []
        
        # 自适应参数
        self.success_rate_window: List[float] = []
        self.adaptive_exploration = exploration_rate
        
    def select_action(self, 
                     observation: str,
                     available_actions: List[str],
                     drive_scores: Optional[Dict[str, float]] = None,
                     inventory: Optional[List[str]] = None,
                     score: float = 0.0,
                     max_score: float = 1.0) -> str:
        """
        选择动作
        
        Args:
            observation: 当前观察文本
            available_actions: 可用动作列表
            drive_scores: 驱动评分字典
            inventory: 当前库存
            score: 当前分数
            max_score: 最大分数
            
        Returns:
            选择的动作
        """
        if not available_actions:
            return "look"
        
        # 解析当前任务状态
        current_room = self.task_parser.parse_current_room(observation)
        visible_objects = self.task_parser.parse_visible_objects(observation)
        exits = self.task_parser.parse_exits(observation)
        task_goal = self.task_parser.parse_task_goal(observation)
        
        if task_goal:
            self.current_task = task_goal
        
        inventory = inventory or []
        task_progress = self.task_parser.parse_progress(observation, inventory, score, max_score)
        self.task_progress_history.append(task_progress)
        
        # 评估每个动作
        action_scores = []
        for action in available_actions:
            task_score = self._evaluate_task_progress(action, observation, visible_objects, 
                                                       exits, inventory, task_progress)
            drive_score = self._evaluate_drive_score(action, drive_scores or {})
            
            # 组合评分
            combined = (self.task_weight * task_score + 
                       self.drive_weight * drive_score)
            
            # 添加探索奖励（避免重复）
            exploration_bonus = self._calculate_exploration_bonus(action)
            combined += exploration_bonus * 0.1
            
            action_scores.append(ActionScore(
                action=action,
                task_score=task_score,
                drive_score=drive_score,
                combined_score=combined,
                exploration_bonus=exploration_bonus
            ))
        
        # 自适应探索率调整
        self._update_exploration_rate(task_progress)
        
        # 探索 vs 利用
        if random.random() < self.adaptive_exploration:
            # 探索：随机选择，但偏向高分动作
            weights = [max(0.1, s.combined_score) for s in action_scores]
            total = sum(weights)
            if total > 0:
                weights = [w / total for w in weights]
                selected = np.random.choice([s.action for s in action_scores], p=weights)
            else:
                selected = random.choice(available_actions)
        else:
            # 利用：选择最高分动作
            best_score = max(action_scores, key=lambda x: x.combined_score)
            selected = best_score.action
        
        # 记录历史
        self.action_history.append(selected)
        self.action_attempt_counts[selected] = self.action_attempt_counts.get(selected, 0) + 1
        
        return selected
    
    def _evaluate_task_progress(self, action: str, observation: str, 
                                visible_objects: List[str], exits: List[str],
                                inventory: List[str], task_progress: float) -> float:
        """评估动作对任务进展的贡献"""
        score = 0.5  # 基础分
        action_lower = action.lower()
        
        # 早期阶段：优先获取物品
        if task_progress < 0.3:
            if 'take' in action_lower or 'pick' in action_lower:
                score += 0.4
                # 检查是否是目标物品
                if self.current_task and any(obj in action_lower 
                                              for obj in self.current_task.target_objects):
                    score += 0.3
        
        # 中期阶段：优先交互
        elif task_progress < 0.7:
            if any(cmd in action_lower for cmd in ['open', 'unlock', 'use']):
                score += 0.3
            if 'go' in action_lower and self.current_task and self.current_task.target_location:
                score += 0.2
        
        # 后期阶段：完成任务
        else:
            if any(cmd in action_lower for cmd in ['go', 'enter', 'exit']):
                score += 0.3
            if 'drop' in action_lower and len(inventory) > 0:
                score += 0.2
        
        # 关键词奖励
        if self.current_task:
            for target in self.current_task.target_objects:
                if target in action_lower:
                    score += 0.2
        
        # 避免重复动作惩罚
        recent_actions = self.action_history[-5:]
        if action in recent_actions:
            repeat_count = recent_actions.count(action)
            score -= 0.1 * repeat_count
        
        return np.clip(score, 0.0, 1.0)
    
    def _evaluate_drive_score(self, action: str, drive_scores: Dict[str, float]) -> float:
        """评估动作与驱动的一致性"""
        if not drive_scores:
            return 0.5
        
        action_lower = action.lower()
        
        # 动作类型到驱动的映射
        drive_alignment = {
            'survival': ['eat', 'drink', 'rest', 'sleep'],
            'curiosity': ['examine', 'look', 'search', 'inspect'],
            'influence': ['take', 'grab', 'collect', 'use'],
            'optimization': ['open', 'unlock', 'efficient'],
        }
        
        # 计算加权驱动分数
        total_score = 0.0
        total_weight = 0.0
        
        for drive, weight in drive_scores.items():
            alignment_keywords = drive_alignment.get(drive, [])
            if any(kw in action_lower for kw in alignment_keywords):
                total_score += weight * 1.5  # 对齐奖励
            else:
                total_score += weight * 0.5  # 基础分
            total_weight += 1.0
        
        if total_weight > 0:
            return np.clip(total_score / total_weight, 0.0, 1.0)
        return 0.5
    
    def _calculate_exploration_bonus(self, action: str) -> float:
        """计算探索奖励（避免重复）"""
        if action not in self.action_attempt_counts:
            return 0.5  # 新动作有较高奖励
        
        count = self.action_attempt_counts[action]
        # 随着尝试次数增加，奖励递减
        return max(0.0, 0.5 - 0.1 * count)
    
    def _update_exploration_rate(self, task_progress: float):
        """根据任务进度自适应调整探索率"""
        # 早期：高探索
        if task_progress < 0.2:
            target_rate = self.exploration_rate
        # 中期：中等探索
        elif task_progress < 0.6:
            target_rate = self.exploration_rate * 0.7
        # 后期：低探索
        else:
            target_rate = self.exploration_rate * 0.4
        
        # 平滑过渡
        self.adaptive_exploration = 0.9 * self.adaptive_exploration + 0.1 * target_rate
    
    def update_from_reward(self, action: str, reward: float, success: bool = False):
        """根据奖励更新动作价值"""
        if success:
            self.action_success_counts[action] = self.action_success_counts.get(action, 0) + 1
            
            # 更新成功率窗口
            self.success_rate_window.append(1.0)
            if len(self.success_rate_window) > 20:
                self.success_rate_window.pop(0)
        else:
            self.success_rate_window.append(0.0)
            if len(self.success_rate_window) > 20:
                self.success_rate_window.pop(0)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取选择器统计信息"""
        total_attempts = sum(self.action_attempt_counts.values())
        total_successes = sum(self.action_success_counts.values())
        
        success_rate = total_successes / max(total_attempts, 1)
        recent_success_rate = (sum(self.success_rate_window) / max(len(self.success_rate_window), 1) 
                              if self.success_rate_window else 0)
        
        return {
            'total_actions': total_attempts,
            'unique_actions': len(self.action_attempt_counts),
            'success_rate': success_rate,
            'recent_success_rate': recent_success_rate,
            'current_exploration_rate': self.adaptive_exploration,
            'task_progress': self.task_progress_history[-1] if self.task_progress_history else 0,
            'current_task': self.current_task.description if self.current_task else None,
        }
    
    def reset(self):
        """重置选择器状态"""
        self.action_history.clear()
        self.action_success_counts.clear()
        self.action_attempt_counts.clear()
        self.task_progress_history.clear()
        self.current_task = None
        self.success_rate_window.clear()
        self.adaptive_exploration = self.exploration_rate


# 便捷函数
def create_adaptive_selector(exploration_rate: float = 0.3) -> AdaptiveActionSelector:
    """创建默认配置的自适应选择器"""
    return AdaptiveActionSelector(
        exploration_rate=exploration_rate,
        task_focus=0.7,
        drive_weight=0.3,
        task_weight=0.7,
    )
