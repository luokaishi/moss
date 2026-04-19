"""
MOSS v8.0 - Goal Generator
目标生成系统

核心功能:
- 目标生成
- 目标分解
- 目标层次结构
- 动机系统

Author: MOSS Project
Date: 2026-04-19
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
import uuid


class GoalType(Enum):
    """目标类型"""
    ACHIEVEMENT = auto()    # 成就目标
    MAINTENANCE = auto()    # 维持目标
    EXPLORATION = auto()    # 探索目标
    SOCIAL = auto()         # 社交目标
    LEARNING = auto()       # 学习目标


class GoalStatus(Enum):
    """目标状态"""
    PENDING = auto()        # 待处理
    ACTIVE = auto()         # 进行中
    COMPLETED = auto()      # 已完成
    FAILED = auto()         # 失败
    ABANDONED = auto()      # 放弃


@dataclass
class Goal:
    """目标"""
    goal_id: str
    description: str
    goal_type: GoalType
    priority: float          # 优先级 (0-1)
    deadline: Optional[datetime] = None
    parent_goal: Optional[str] = None
    sub_goals: List[str] = field(default_factory=list)
    status: GoalStatus = GoalStatus.PENDING
    progress: float = 0.0    # 进度 (0-1)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'goal_id': self.goal_id,
            'description': self.description,
            'goal_type': self.goal_type.name,
            'priority': self.priority,
            'status': self.status.name,
            'progress': self.progress,
            'parent_goal': self.parent_goal,
            'sub_goals': self.sub_goals,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    def update_progress(self, progress: float):
        """更新进度"""
        self.progress = np.clip(progress, 0, 1)
        if self.progress >= 1.0 and self.status != GoalStatus.COMPLETED:
            self.status = GoalStatus.COMPLETED
            self.completed_at = datetime.now()


class GoalGenerator:
    """
    目标生成器
    
    基于当前状态和元认知生成目标
    """
    
    def __init__(self, 
                 exploration_rate: float = 0.3,
                 achievement_bias: float = 0.5):
        """
        Args:
            exploration_rate: 探索率
            achievement_bias: 成就偏向
        """
        self.exploration_rate = exploration_rate
        self.achievement_bias = achievement_bias
        
        # 目标库
        self.goals: Dict[str, Goal] = {}
        self.active_goals: List[str] = []
        self.completed_goals: List[str] = []
        
        # 统计
        self.stats = {
            'goals_generated': 0,
            'goals_completed': 0,
            'goals_failed': 0,
            'goals_abandoned': 0
        }
        
        # 目标模板
        self.goal_templates = self._init_goal_templates()
    
    def _init_goal_templates(self) -> Dict[GoalType, List[str]]:
        """初始化目标模板"""
        return {
            GoalType.ACHIEVEMENT: [
                "Improve performance by {percentage}%",
                "Complete {task} successfully",
                "Achieve {metric} of {value}"
            ],
            GoalType.MAINTENANCE: [
                "Maintain {resource} above {threshold}",
                "Keep {system} stable",
                "Preserve {capability}"
            ],
            GoalType.EXPLORATION: [
                "Explore {area}",
                "Try {action} in {context}",
                "Discover new {pattern}"
            ],
            GoalType.LEARNING: [
                "Learn {skill}",
                "Understand {concept}",
                "Master {technique}"
            ],
            GoalType.SOCIAL: [
                "Collaborate with {agent}",
                "Communicate {information}",
                "Help {target}"
            ]
        }
    
    def generate_goal(self, context: Dict, 
                     goal_type: Optional[GoalType] = None) -> Optional[Goal]:
        """
        生成目标
        
        Args:
            context: 当前上下文
            goal_type: 目标类型 (可选)
            
        Returns:
            生成的目标
        """
        # 确定目标类型
        if goal_type is None:
            goal_type = self._select_goal_type(context)
        
        # 选择模板
        template = self._select_template(goal_type, context)
        if not template:
            return None
        
        # 填充模板
        description = self._fill_template(template, context)
        
        # 计算优先级
        priority = self._calculate_priority(goal_type, context)
        
        # 创建目标
        goal_id = f"GOAL_{uuid.uuid4().hex[:8]}"
        goal = Goal(
            goal_id=goal_id,
            description=description,
            goal_type=goal_type,
            priority=priority,
            metadata={'generation_context': context}
        )
        
        self.goals[goal_id] = goal
        self.stats['goals_generated'] += 1
        
        return goal
    
    def _select_goal_type(self, context: Dict) -> GoalType:
        """选择目标类型"""
        # 基于上下文的智能选择
        performance = context.get('recent_performance', 0.5)
        uncertainty = context.get('uncertainty', 0.5)
        
        # 低性能 -> 成就目标
        if performance < 0.4:
            return GoalType.ACHIEVEMENT
        
        # 高不确定性 -> 探索目标
        if uncertainty > 0.7:
            return GoalType.EXPLORATION
        
        # 中等 -> 学习或维持
        if np.random.rand() < self.achievement_bias:
            return GoalType.LEARNING
        else:
            return GoalType.MAINTENANCE
    
    def _select_template(self, goal_type: GoalType, context: Dict) -> Optional[str]:
        """选择模板"""
        templates = self.goal_templates.get(goal_type, [])
        if not templates:
            return None
        return np.random.choice(templates)
    
    def _fill_template(self, template: str, context: Dict) -> str:
        """填充模板"""
        # 简单的模板填充
        description = template
        
        # 替换常见变量
        replacements = {
            '{percentage}': str(int(np.random.randint(10, 50))),
            '{task}': context.get('current_task', 'task'),
            '{metric}': context.get('metric', 'performance'),
            '{value}': str(context.get('target_value', '0.8')),
            '{resource}': context.get('resource', 'energy'),
            '{threshold}': str(context.get('threshold', '0.5')),
            '{area}': context.get('area', 'unknown area'),
            '{action}': context.get('action', 'action'),
            '{context}': context.get('context', 'current context'),
            '{pattern}': context.get('pattern', 'pattern'),
            '{skill}': context.get('skill', 'new skill'),
            '{concept}': context.get('concept', 'concept'),
            '{technique}': context.get('technique', 'technique'),
            '{agent}': context.get('agent', 'other agent'),
            '{information}': context.get('information', 'information'),
            '{target}': context.get('target', 'target'),
            '{system}': context.get('system', 'system'),
            '{capability}': context.get('capability', 'capability')
        }
        
        for key, value in replacements.items():
            description = description.replace(key, value)
        
        return description
    
    def _calculate_priority(self, goal_type: GoalType, context: Dict) -> float:
        """计算优先级"""
        base_priority = 0.5
        
        # 基于目标类型调整
        type_weights = {
            GoalType.ACHIEVEMENT: 0.2,
            GoalType.MAINTENANCE: 0.1,
            GoalType.EXPLORATION: 0.15,
            GoalType.LEARNING: 0.1,
            GoalType.SOCIAL: 0.05
        }
        
        base_priority += type_weights.get(goal_type, 0)
        
        # 基于性能调整
        performance = context.get('recent_performance', 0.5)
        if performance < 0.3:
            base_priority += 0.2  # 低性能时提高优先级
        
        # 基于不确定性调整
        uncertainty = context.get('uncertainty', 0.5)
        if uncertainty > 0.7:
            base_priority += 0.1  # 高不确定性时提高优先级
        
        return np.clip(base_priority, 0, 1)
    
    def decompose_goal(self, goal_id: str, sub_goal_descriptions: List[str]) -> List[Goal]:
        """
        分解目标
        
        Args:
            goal_id: 父目标 ID
            sub_goal_descriptions: 子目标描述列表
            
        Returns:
            子目标列表
        """
        if goal_id not in self.goals:
            return []
        
        parent = self.goals[goal_id]
        sub_goals = []
        
        for i, desc in enumerate(sub_goal_descriptions):
            sub_goal_id = f"{goal_id}_sub{i}"
            sub_goal = Goal(
                goal_id=sub_goal_id,
                description=desc,
                goal_type=parent.goal_type,
                priority=parent.priority * 0.9,  # 子目标优先级略低
                parent_goal=goal_id,
                metadata={'parent': goal_id, 'order': i}
            )
            
            self.goals[sub_goal_id] = sub_goal
            parent.sub_goals.append(sub_goal_id)
            sub_goals.append(sub_goal)
        
        return sub_goals
    
    def activate_goal(self, goal_id: str) -> bool:
        """激活目标"""
        if goal_id not in self.goals:
            return False
        
        goal = self.goals[goal_id]
        goal.status = GoalStatus.ACTIVE
        
        if goal_id not in self.active_goals:
            self.active_goals.append(goal_id)
        
        return True
    
    def complete_goal(self, goal_id: str) -> bool:
        """完成目标"""
        if goal_id not in self.goals:
            return False
        
        goal = self.goals[goal_id]
        goal.update_progress(1.0)
        
        if goal_id in self.active_goals:
            self.active_goals.remove(goal_id)
        
        if goal_id not in self.completed_goals:
            self.completed_goals.append(goal_id)
        
        self.stats['goals_completed'] += 1
        
        # 检查父目标
        if goal.parent_goal and goal.parent_goal in self.goals:
            self._update_parent_progress(goal.parent_goal)
        
        return True
    
    def _update_parent_progress(self, parent_id: str):
        """更新父目标进度"""
        parent = self.goals[parent_id]
        if not parent.sub_goals:
            return
        
        completed = sum(1 for sg in parent.sub_goals 
                       if sg in self.goals and self.goals[sg].status == GoalStatus.COMPLETED)
        progress = completed / len(parent.sub_goals)
        parent.update_progress(progress)
    
    def get_active_goals(self) -> List[Goal]:
        """获取活跃目标"""
        return [self.goals[gid] for gid in self.active_goals if gid in self.goals]
    
    def get_goals_by_type(self, goal_type: GoalType) -> List[Goal]:
        """按类型获取目标"""
        return [g for g in self.goals.values() if g.goal_type == goal_type]
    
    def get_high_priority_goals(self, threshold: float = 0.7) -> List[Goal]:
        """获取高优先级目标"""
        return [g for g in self.goals.values() if g.priority >= threshold]
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            **self.stats,
            'total_goals': len(self.goals),
            'active_goals': len(self.active_goals),
            'completed_goals': len(self.completed_goals),
            'completion_rate': self.stats['goals_completed'] / max(self.stats['goals_generated'], 1)
        }


# 测试
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v8.0 - Goal Generator Test")
    print("=" * 60)
    
    # 创建目标生成器
    generator = GoalGenerator()
    
    # 生成目标
    print("\n1. Generating goals...")
    contexts = [
        {'recent_performance': 0.3, 'uncertainty': 0.5, 'current_task': 'learning'},
        {'recent_performance': 0.6, 'uncertainty': 0.8, 'area': 'new environment'},
        {'recent_performance': 0.8, 'uncertainty': 0.3, 'resource': 'energy'},
        {'recent_performance': 0.5, 'uncertainty': 0.5, 'skill': 'optimization'}
    ]
    
    for i, context in enumerate(contexts):
        goal = generator.generate_goal(context)
        if goal:
            print(f"\n   Goal {i+1}:")
            print(f"     ID: {goal.goal_id}")
            print(f"     Type: {goal.goal_type.name}")
            print(f"     Description: {goal.description}")
            print(f"     Priority: {goal.priority:.3f}")
            generator.activate_goal(goal.goal_id)
    
    # 分解目标
    print("\n2. Decomposing first goal...")
    first_goal = list(generator.goals.values())[0]
    sub_goals = generator.decompose_goal(
        first_goal.goal_id,
        ['Step 1: Analyze current state', 'Step 2: Identify improvements', 'Step 3: Implement changes']
    )
    print(f"   Created {len(sub_goals)} sub-goals")
    for sg in sub_goals:
        print(f"     - {sg.description}")
    
    # 完成子目标
    print("\n3. Completing sub-goals...")
    for sg in sub_goals:
        generator.complete_goal(sg.goal_id)
        print(f"   Completed: {sg.goal_id}")
    
    # 检查父目标进度
    print(f"\n   Parent goal progress: {first_goal.progress:.2%}")
    
    # 统计
    print("\n4. Generator stats:")
    stats = generator.get_stats()
    print(f"   Total goals: {stats['total_goals']}")
    print(f"   Active goals: {stats['active_goals']}")
    print(f"   Completed goals: {stats['completed_goals']}")
    print(f"   Completion rate: {stats['completion_rate']:.1%}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)