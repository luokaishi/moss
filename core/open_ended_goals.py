#!/usr/bin/env python3
"""
MOSS v5.6 - Open-Ended Goal Generator
开放目标生成器

核心功能:
- 自主目标生成
- 目标层次演化
- 价值对齐评估
- 内在驱动力驱动

Author: MOSS Project
Date: 2026-04-03
Version: 5.6.0-dev
"""

import uuid
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class GoalType(Enum):
    """目标类型"""
    SURVIVAL = "survival"
    EXPLORATION = "exploration"
    ACHIEVEMENT = "achievement"
    SOCIAL = "social"
    SELF_ACTUALIZATION = "self_actualization"
    OPEN_ENDED = "open_ended"


class GoalPriority(Enum):
    """目标优先级"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Goal:
    """目标定义"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str = ""
    goal_type: GoalType = GoalType.OPEN_ENDED
    priority: GoalPriority = GoalPriority.MEDIUM
    
    # 层次结构
    parent_id: Optional[str] = None
    sub_goals: List[str] = field(default_factory=list)
    
    # 状态
    progress: float = 0.0
    status: str = "active"  # active, completed, abandoned
    
    # 评估
    intrinsic_value: float = 0.5
    extrinsic_value: float = 0.5
    alignment_score: float = 0.5
    
    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'description': self.description,
            'goal_type': self.goal_type.value,
            'priority': self.priority.value,
            'parent_id': self.parent_id,
            'sub_goals': self.sub_goals,
            'progress': self.progress,
            'status': self.status,
            'intrinsic_value': self.intrinsic_value,
            'extrinsic_value': self.extrinsic_value,
            'alignment_score': self.alignment_score,
            'created_at': self.created_at.isoformat()
        }


class IntrinsicDrive:
    """
    内在驱动力
    
    驱动自主目标生成
    """
    
    def __init__(self):
        # 基础驱动力
        self.drives = {
            'survival': 0.25,
            'curiosity': 0.25,
            'influence': 0.25,
            'optimization': 0.25
        }
        
        # 动态调整
        self.drive_history: List[Dict] = []
        
        self.stats = {
            'goals_generated': 0,
            'drive_adjustments': 0
        }
    
    def adjust_drives(self, feedback: Dict):
        """
        根据反馈调整驱动力
        
        Args:
            feedback: 包含 success_rate, satisfaction 等
        """
        # 简化版：根据成功率调整
        success_rate = feedback.get('success_rate', 0.5)
        
        if success_rate > 0.7:
            # 成功率高，增强好奇心和影响力
            self.drives['curiosity'] = min(0.4, self.drives['curiosity'] + 0.05)
            self.drives['influence'] = min(0.4, self.drives['influence'] + 0.05)
        elif success_rate < 0.3:
            # 成功率低，增强生存和优化
            self.drives['survival'] = min(0.4, self.drives['survival'] + 0.05)
            self.drives['optimization'] = min(0.4, self.drives['optimization'] + 0.05)
        
        # 归一化
        total = sum(self.drives.values())
        for key in self.drives:
            self.drives[key] /= total
        
        self.drive_history.append({
            'timestamp': datetime.now().isoformat(),
            'drives': self.drives.copy(),
            'feedback': feedback
        })
        
        self.stats['drive_adjustments'] += 1
    
    def get_dominant_drive(self) -> Tuple[str, float]:
        """获取主导驱动力"""
        dominant = max(self.drives.items(), key=lambda x: x[1])
        return dominant
    
    def get_status(self) -> Dict:
        return {
            'drives': self.drives,
            'dominant': self.get_dominant_drive(),
            'stats': self.stats
        }


class GoalGenerator:
    """
    目标生成器
    
    基于内在驱动力生成开放目标
    """
    
    def __init__(self):
        self.drive = IntrinsicDrive()
        self.goals: Dict[str, Goal] = {}
        self.goal_templates = self._load_templates()
        
        self.stats = {
            'total_generated': 0,
            'by_type': {},
            'hierarchy_depth': 0
        }
    
    def _load_templates(self) -> Dict[GoalType, List[str]]:
        """加载目标模板"""
        return {
            GoalType.SURVIVAL: [
                "确保{resource}充足",
                "建立{system}备份机制",
                "监控{metric}稳定性"
            ],
            GoalType.EXPLORATION: [
                "探索{domain}的新可能性",
                "学习{skill}并应用",
                "发现{area}的潜在机会"
            ],
            GoalType.ACHIEVEMENT: [
                "完成{project}的{phase}",
                "达到{metric}的{target}",
                "优化{process}的效率"
            ],
            GoalType.SOCIAL: [
                "与{agent}建立合作关系",
                "为{community}贡献价值",
                "学习{agent}的{skill}"
            ],
            GoalType.SELF_ACTUALIZATION: [
                "实现{capability}的自我提升",
                "发展独特的{trait}",
                "创造{artifact}体现价值"
            ]
        }
    
    def generate_goal(self, context: Dict, 
                     parent_goal: Optional[Goal] = None) -> Optional[Goal]:
        """
        生成目标
        
        Args:
            context: 当前情境
            parent_goal: 可选的父目标
            
        Returns:
            生成的 Goal 或 None
        """
        # 1. 根据主导驱动力确定目标类型
        dominant_drive, drive_strength = self.drive.get_dominant_drive()
        
        type_mapping = {
            'survival': GoalType.SURVIVAL,
            'curiosity': GoalType.EXPLORATION,
            'influence': GoalType.SOCIAL,
            'optimization': GoalType.ACHIEVEMENT
        }
        
        goal_type = type_mapping.get(dominant_drive, GoalType.EXPLORATION)
        
        # 2. 选择模板
        templates = self.goal_templates.get(goal_type, [])
        if not templates:
            return None
        
        template = np.random.choice(templates)
        
        # 3. 填充变量
        description = self._fill_template(template, context)
        
        # 4. 创建目标
        goal = Goal(
            description=description,
            goal_type=goal_type,
            priority=self._determine_priority(drive_strength, context),
            parent_id=parent_goal.id if parent_goal else None,
            intrinsic_value=drive_strength,
            extrinsic_value=context.get('external_reward', 0.5),
            alignment_score=context.get('alignment', 0.5)
        )
        
        # 5. 层次结构
        if parent_goal:
            parent_goal.sub_goals.append(goal.id)
        
        self.goals[goal.id] = goal
        self.stats['total_generated'] += 1
        self.stats['by_type'][goal_type.value] = \
            self.stats['by_type'].get(goal_type.value, 0) + 1
        
        # 6. 更新层次深度
        depth = self._calculate_hierarchy_depth(goal)
        if depth > self.stats['hierarchy_depth']:
            self.stats['hierarchy_depth'] = depth
        
        return goal
    
    def _fill_template(self, template: str, context: Dict) -> str:
        """填充模板变量"""
        variables = {
            'resource': context.get('critical_resource', 'data'),
            'system': context.get('active_system', 'core'),
            'metric': context.get('key_metric', 'performance'),
            'domain': context.get('current_domain', 'operations'),
            'skill': context.get('desired_skill', 'optimization'),
            'area': context.get('unexplored_area', 'possibilities'),
            'project': context.get('current_project', 'enhancement'),
            'phase': context.get('next_phase', 'implementation'),
            'target': context.get('target_value', 'improvement'),
            'process': context.get('inefficient_process', 'workflow'),
            'agent': context.get('potential_partner', 'collaborator'),
            'community': context.get('community_name', 'network'),
            'capability': context.get('target_capability', 'reasoning'),
            'trait': context.get('unique_trait', 'approach'),
            'artifact': context.get('desired_output', 'solution')
        }
        
        description = template
        for var, value in variables.items():
            description = description.replace(f"{{{var}}}", str(value))
        
        return description
    
    def _determine_priority(self, drive_strength: float, 
                           context: Dict) -> GoalPriority:
        """确定优先级"""
        urgency = context.get('urgency', 0.5)
        combined = (drive_strength + urgency) / 2
        
        if combined > 0.8:
            return GoalPriority.CRITICAL
        elif combined > 0.6:
            return GoalPriority.HIGH
        elif combined > 0.4:
            return GoalPriority.MEDIUM
        else:
            return GoalPriority.LOW
    
    def _calculate_hierarchy_depth(self, goal: Goal) -> int:
        """计算层次深度"""
        depth = 0
        current_id = goal.parent_id
        
        while current_id:
            depth += 1
            parent = self.goals.get(current_id)
            if parent:
                current_id = parent.parent_id
            else:
                break
        
        return depth
    
    def evolve_goals(self, feedback: Dict):
        """
        目标演化
        
        根据反馈调整目标生成策略
        """
        # 1. 调整驱动力
        self.drive.adjust_drives(feedback)
        
        # 2. 淘汰低价值目标
        for goal_id, goal in list(self.goals.items()):
            if goal.alignment_score < 0.3 and goal.status == "active":
                goal.status = "abandoned"
        
        # 3. 强化高价值目标
        for goal in self.goals.values():
            if goal.alignment_score > 0.8 and goal.status == "active":
                goal.intrinsic_value = min(1.0, goal.intrinsic_value + 0.1)
    
    def get_goal_hierarchy(self) -> Dict:
        """获取目标层次结构"""
        root_goals = [g for g in self.goals.values() if not g.parent_id]
        
        def build_tree(goal: Goal) -> Dict:
            children = [
                build_tree(self.goals[gid])
                for gid in goal.sub_goals
                if gid in self.goals
            ]
            
            return {
                'goal': goal.to_dict(),
                'children': children
            }
        
        return {
            'roots': [build_tree(g) for g in root_goals],
            'total_goals': len(self.goals),
            'max_depth': self.stats['hierarchy_depth']
        }
    
    def get_status(self) -> Dict:
        """获取生成器状态"""
        return {
            'stats': self.stats,
            'drive': self.drive.get_status(),
            'active_goals': sum(1 for g in self.goals.values() if g.status == "active"),
            'hierarchy': {
                'total': len(self.goals),
                'depth': self.stats['hierarchy_depth']
            }
        }


# 测试代码
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v5.6 - Open-Ended Goal Generator Test")
    print("=" * 60)
    
    # 创建生成器
    generator = GoalGenerator()
    
    # 测试目标生成
    print("\n1. 测试目标生成...")
    context = {
        'critical_resource': 'computational_power',
        'current_domain': 'ai_research',
        'desired_skill': 'deep_learning',
        'urgency': 0.7,
        'alignment': 0.8
    }
    
    # 生成根目标
    root_goal = generator.generate_goal(context)
    if root_goal:
        print(f"   根目标：{root_goal.description}")
        print(f"   类型：{root_goal.goal_type.value}")
        print(f"   优先级：{root_goal.priority.value}")
        
        # 生成子目标
        print("\n2. 测试层次结构...")
        for i in range(3):
            sub_goal = generator.generate_goal(context, parent_goal=root_goal)
            if sub_goal:
                print(f"   子目标 {i+1}: {sub_goal.description}")
        
        # 获取层次结构
        print("\n3. 目标层次结构:")
        hierarchy = generator.get_goal_hierarchy()
        print(f"   总目标数：{hierarchy['total']}")
        print(f"   最大深度：{hierarchy['max_depth']}")
    
    # 测试演化
    print("\n4. 测试目标演化...")
    feedback = {'success_rate': 0.8, 'satisfaction': 0.7}
    generator.evolve_goals(feedback)
    
    # 获取状态
    print("\n5. 生成器状态:")
    status = generator.get_status()
    print(f"   总生成数：{status['stats']['total_generated']}")
    print(f"   活跃目标：{status['active_goals']}")
    print(f"   主导驱动力：{status['drive']['dominant']}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)
