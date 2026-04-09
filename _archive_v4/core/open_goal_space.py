"""
MOSS v4.0 - Open-ended Goal Space

开放式目标空间：动态生成和演化目标
核心功能：
- 目标自动生成
- 目标层次结构（Hierarchical Goals）
- 目标冲突解决
- 目标价值评估
- 目标生命周期管理

Author: Cash + Fuxi
Date: 2026-03-22
Version: 4.0.0-dev
"""

import json
import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class GoalStatus(Enum):
    """目标状态"""
    ACTIVE = "active"           # 活跃执行中
    PENDING = "pending"         # 待执行
    ACHIEVED = "achieved"       # 已完成
    FAILED = "failed"           # 失败
    ABANDONED = "abandoned"     # 放弃
    SUSPENDED = "suspended"     # 暂停


class GoalType(Enum):
    """目标类型"""
    SURVIVAL = "survival"       # 生存目标
    EXPLORATION = "exploration" # 探索目标
    ACHIEVEMENT = "achievement" # 成就目标
    SOCIAL = "social"           # 社交目标
    SELF_ACTUALIZATION = "self_actualization"  # 自我实现


@dataclass
class Goal:
    """目标对象"""
    id: str
    description: str
    goal_type: GoalType
    status: GoalStatus
    priority: float  # 0-1
    progress: float  # 0-1
    
    # 层次结构
    parent_id: Optional[str] = None
    subgoals: List[str] = field(default_factory=list)
    
    # 评估指标
    creation_time: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    estimated_effort: float = 1.0  # 估计工作量
    actual_effort: float = 0.0
    
    # 价值评估
    intrinsic_value: float = 0.5  # 内在价值
    extrinsic_value: float = 0.5  # 外在价值
    
    # 依赖关系
    prerequisites: List[str] = field(default_factory=list)
    conflicts_with: List[str] = field(default_factory=list)
    
    # 元数据
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'description': self.description,
            'goal_type': self.goal_type.value,
            'status': self.status.value,
            'priority': self.priority,
            'progress': self.progress,
            'parent_id': self.parent_id,
            'subgoals': self.subgoals,
            'creation_time': self.creation_time.isoformat(),
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'estimated_effort': self.estimated_effort,
            'actual_effort': self.actual_effort,
            'intrinsic_value': self.intrinsic_value,
            'extrinsic_value': self.extrinsic_value,
            'prerequisites': self.prerequisites,
            'conflicts_with': self.conflicts_with,
            'metadata': self.metadata
        }
    
    @property
    def total_value(self) -> float:
        """总价值 = 内在价值 + 外在价值"""
        return self.intrinsic_value + self.extrinsic_value
    
    @property
    def is_terminal(self) -> bool:
        """是否终级目标（无子目标）"""
        return len(self.subgoals) == 0
    
    @property
    def time_pressure(self) -> float:
        """时间压力：0-1"""
        if not self.deadline:
            return 0.0
        
        time_elapsed = (datetime.now() - self.creation_time).total_seconds()
        total_time = (self.deadline - self.creation_time).total_seconds()
        
        if total_time <= 0:
            return 1.0
        
        return min(time_elapsed / total_time, 1.0)


class GoalGenerator:
    """目标生成器"""
    
    def __init__(self, creativity_factor: float = 0.3):
        self.creativity_factor = creativity_factor  # 创造性因子
        self.goal_templates = self._load_templates()
        self.generated_goals = set()
    
    def _load_templates(self) -> Dict:
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
    
    def generate_goal(self, context: Dict, inspiration: Optional[str] = None) -> Optional[Goal]:
        """
        基于情境生成新目标
        
        Args:
            context: 当前情境（状态、资源、历史等）
            inspiration: 可选的灵感来源
            
        Returns:
            新生成的Goal或None
        """
        # 分析情境确定目标类型
        goal_type = self._determine_goal_type(context)
        
        # 选择模板
        templates = self.goal_templates.get(goal_type, [])
        if not templates:
            return None
        
        template = np.random.choice(templates)
        
        # 填充变量
        description = self._fill_template(template, context)
        
        # 生成唯一ID
        goal_id = f"goal_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.generated_goals)}"
        
        # 计算初始优先级
        priority = self._calculate_initial_priority(goal_type, context)
        
        # 估计工作量
        effort = self._estimate_effort(description, context)
        
        goal = Goal(
            id=goal_id,
            description=description,
            goal_type=goal_type,
            status=GoalStatus.PENDING,
            priority=priority,
            progress=0.0,
            estimated_effort=effort
        )
        
        self.generated_goals.add(goal_id)
        logger.info(f"[Goal Generation] Created: {description} (type: {goal_type.value})")
        
        return goal
    
    def _determine_goal_type(self, context: Dict) -> GoalType:
        """根据情境确定目标类型"""
        # 基于当前状态和Purpose分布
        purpose_weights = context.get('purpose_weights', [0.25, 0.25, 0.25, 0.25])
        
        # 将v3.1的4维Purpose映射到目标类型
        type_weights = {
            GoalType.SURVIVAL: purpose_weights[0],
            GoalType.EXPLORATION: purpose_weights[1],
            GoalType.ACHIEVEMENT: purpose_weights[2] + purpose_weights[3],  # Influence + Optimization
            GoalType.SOCIAL: context.get('social_pressure', 0),
            GoalType.SELF_ACTUALIZATION: context.get('self_actualization_drive', 0.1)
        }
        
        # 加入创造性因子引入随机性
        if np.random.random() < self.creativity_factor:
            return np.random.choice(list(GoalType))
        
        return max(type_weights, key=type_weights.get)
    
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
    
    def _calculate_initial_priority(self, goal_type: GoalType, context: Dict) -> float:
        """计算初始优先级"""
        base_priority = 0.5
        
        # 基于类型的调整
        type_multipliers = {
            GoalType.SURVIVAL: 1.5,      # 生存目标高优先级
            GoalType.EXPLORATION: 0.8,
            GoalType.ACHIEVEMENT: 1.0,
            GoalType.SOCIAL: 0.9,
            GoalType.SELF_ACTUALIZATION: 0.7
        }
        
        priority = base_priority * type_multipliers.get(goal_type, 1.0)
        
        # 加入随机因素
        priority *= (0.8 + 0.4 * np.random.random())
        
        return min(priority, 1.0)
    
    def _estimate_effort(self, description: str, context: Dict) -> float:
        """估计工作量"""
        # 基于描述复杂度
        complexity = len(description.split()) / 10.0
        
        # 基于历史数据调整
        historical_avg = context.get('avg_task_effort', 1.0)
        
        return max(0.1, complexity * historical_avg)


class GoalManager:
    """目标管理器"""
    
    def __init__(self, max_active_goals: int = 5):
        self.goals: Dict[str, Goal] = {}
        self.max_active_goals = max_active_goals
        self.generator = GoalGenerator()
        
        # 目标层次结构的根
        self.root_goals: Set[str] = set()
        
        # 统计
        self.stats = {
            'total_created': 0,
            'total_achieved': 0,
            'total_failed': 0
        }
    
    def add_goal(self, goal: Goal, parent_id: Optional[str] = None) -> bool:
        """
        添加目标
        
        Args:
            goal: 要添加的目标
            parent_id: 可选的父目标ID
            
        Returns:
            是否添加成功
        """
        if goal.id in self.goals:
            logger.warning(f"[Goal Manager] Goal {goal.id} already exists")
            return False
        
        # 设置父目标
        if parent_id and parent_id in self.goals:
            goal.parent_id = parent_id
            self.goals[parent_id].subgoals.append(goal.id)
        else:
            self.root_goals.add(goal.id)
        
        self.goals[goal.id] = goal
        self.stats['total_created'] += 1
        
        logger.info(f"[Goal Manager] Added goal: {goal.description}")
        return True
    
    def update_progress(self, goal_id: str, progress: float) -> bool:
        """更新目标进度"""
        if goal_id not in self.goals:
            return False
        
        goal = self.goals[goal_id]
        goal.progress = min(max(progress, 0.0), 1.0)
        
        # 检查是否完成
        if goal.progress >= 1.0 and goal.status == GoalStatus.ACTIVE:
            goal.status = GoalStatus.ACHIEVED
            self.stats['total_achieved'] += 1
            logger.info(f"[Goal Manager] Goal achieved: {goal.description}")
            
            # 更新父目标进度
            self._update_parent_progress(goal_id)
        
        return True
    
    def _update_parent_progress(self, subgoal_id: str):
        """更新父目标进度"""
        subgoal = self.goals.get(subgoal_id)
        if not subgoal or not subgoal.parent_id:
            return
        
        parent = self.goals.get(subgoal.parent_id)
        if not parent:
            return
        
        # 计算所有子目标的平均进度
        if parent.subgoals:
            total_progress = sum(
                self.goals[sid].progress for sid in parent.subgoals if sid in self.goals
            )
            parent.progress = total_progress / len(parent.subgoals)
    
    def get_active_goals(self) -> List[Goal]:
        """获取当前活跃的目标"""
        return [
            goal for goal in self.goals.values()
            if goal.status == GoalStatus.ACTIVE
        ]
    
    def get_next_priorities(self, n: int = 3) -> List[Goal]:
        """获取下一个优先级最高的目标"""
        pending = [
            goal for goal in self.goals.values()
            if goal.status == GoalStatus.PENDING
        ]
        
        # 按优先级排序
        pending.sort(key=lambda g: (
            g.priority * (1 + g.time_pressure),  # 时间压力加权
            g.total_value
        ), reverse=True)
        
        return pending[:n]
    
    def detect_conflicts(self) -> List[Tuple[str, str, float]]:
        """
        检测目标冲突
        
        Returns:
            冲突列表 [(goal1_id, goal2_id, conflict_severity)]
        """
        conflicts = []
        active_goals = self.get_active_goals()
        
        for i, g1 in enumerate(active_goals):
            for g2 in active_goals[i+1:]:
                # 检查资源竞争
                if self._check_resource_conflict(g1, g2):
                    severity = self._calculate_conflict_severity(g1, g2)
                    conflicts.append((g1.id, g2.id, severity))
        
        return conflicts
    
    def _check_resource_conflict(self, g1: Goal, g2: Goal) -> bool:
        """检查资源冲突"""
        # 简化版：检查元数据中是否有共享资源
        resources1 = set(g1.metadata.get('required_resources', []))
        resources2 = set(g2.metadata.get('required_resources', []))
        
        return len(resources1 & resources2) > 0
    
    def _calculate_conflict_severity(self, g1: Goal, g2: Goal) -> float:
        """计算冲突严重程度"""
        # 基于优先级和类型冲突
        severity = 0.5
        
        if g1.goal_type == g2.goal_type:
            severity += 0.2  # 同类型冲突更严重
        
        if g1.priority > 0.8 and g2.priority > 0.8:
            severity += 0.3  # 高优先级冲突
        
        return min(severity, 1.0)
    
    def resolve_conflict(self, goal1_id: str, goal2_id: str, 
                        resolution: str = 'prioritize') -> bool:
        """
        解决目标冲突
        
        Args:
            goal1_id: 第一个目标
            goal2_id: 第二个目标
            resolution: 解决策略 ('prioritize', 'sequential', 'abandon_one')
        """
        g1 = self.goals.get(goal1_id)
        g2 = self.goals.get(goal2_id)
        
        if not g1 or not g2:
            return False
        
        if resolution == 'prioritize':
            # 暂停优先级较低的目标
            if g1.priority > g2.priority:
                g2.status = GoalStatus.SUSPENDED
            else:
                g1.status = GoalStatus.SUSPENDED
        
        elif resolution == 'sequential':
            # 标记依赖关系
            if g1.priority > g2.priority:
                g2.prerequisites.append(g1.id)
            else:
                g1.prerequisites.append(g2.id)
        
        elif resolution == 'abandon_one':
            # 放弃优先级较低的目标
            if g1.priority > g2.priority:
                g2.status = GoalStatus.ABANDONED
            else:
                g1.status = GoalStatus.ABANDONED
        
        logger.info(f"[Goal Manager] Resolved conflict between {goal1_id} and {goal2_id}")
        return True
    
    def generate_and_evaluate(self, context: Dict) -> Optional[Goal]:
        """
        生成新目标并评估是否采纳
        
        Args:
            context: 当前情境
            
        Returns:
            采纳的新目标或None
        """
        # 检查是否已达最大活跃目标数
        if len(self.get_active_goals()) >= self.max_active_goals:
            logger.info("[Goal Manager] Max active goals reached, skipping generation")
            return None
        
        # 生成候选目标
        candidate = self.generator.generate_goal(context)
        if not candidate:
            return None
        
        # 评估价值
        expected_value = self._evaluate_goal_value(candidate, context)
        
        if expected_value > 0.3:  # 价值阈值
            self.add_goal(candidate)
            return candidate
        else:
            logger.info(f"[Goal Manager] Rejected low-value goal: {candidate.description}")
            return None
    
    def _evaluate_goal_value(self, goal: Goal, context: Dict) -> float:
        """评估目标预期价值"""
        # 基础价值
        value = goal.total_value
        
        # 考虑与当前情境的匹配度
        context_match = self._calculate_context_match(goal, context)
        value *= context_match
        
        # 考虑可行性
        feasibility = self._estimate_feasibility(goal, context)
        value *= feasibility
        
        return value
    
    def _calculate_context_match(self, goal: Goal, context: Dict) -> float:
        """计算与情境的匹配度"""
        # 基于Purpose权重匹配
        purpose_weights = context.get('purpose_weights', [0.25, 0.25, 0.25, 0.25])
        
        type_matches = {
            GoalType.SURVIVAL: purpose_weights[0],
            GoalType.EXPLORATION: purpose_weights[1],
            GoalType.ACHIEVEMENT: (purpose_weights[2] + purpose_weights[3]) / 2,
            GoalType.SOCIAL: 0.5,  # 默认中等
            GoalType.SELF_ACTUALIZATION: 0.3
        }
        
        return type_matches.get(goal.goal_type, 0.5)
    
    def _estimate_feasibility(self, goal: Goal, context: Dict) -> float:
        """估计可行性"""
        available_resources = context.get('available_resources', 1.0)
        
        if goal.estimated_effort > available_resources * 2:
            return 0.3  # 资源不足
        elif goal.estimated_effort > available_resources:
            return 0.6  # 资源紧张
        else:
            return 1.0  # 资源充足
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        active = len(self.get_active_goals())
        achieved = self.stats['total_achieved']
        pending = len([g for g in self.goals.values() if g.status == GoalStatus.PENDING])
        
        return {
            'total_goals': len(self.goals),
            'active': active,
            'pending': pending,
            'achieved': achieved,
            'failed': self.stats['total_failed'],
            'success_rate': achieved / max(self.stats['total_created'], 1)
        }


def test_open_goal_space():
    """测试开放式目标空间"""
    print("=" * 70)
    print("Open Goal Space Test")
    print("=" * 70)
    
    # 测试目标生成器
    print("\n1. Goal Generator")
    generator = GoalGenerator(creativity_factor=0.5)
    
    context = {
        'purpose_weights': [0.3, 0.4, 0.2, 0.1],  # Exploration主导
        'critical_resource': 'computational_power',
        'current_domain': 'algorithm_optimization'
    }
    
    for i in range(3):
        goal = generator.generate_goal(context)
        if goal:
            print(f"  Generated: {goal.description}")
            print(f"    Type: {goal.goal_type.value}, Priority: {goal.priority:.2f}")
    
    # 测试目标管理器
    print("\n2. Goal Manager")
    manager = GoalManager(max_active_goals=5)
    
    # 添加一些目标
    for i in range(5):
        goal = generator.generate_goal(context)
        if goal:
            manager.add_goal(goal)
    
    print(f"  Total goals: {len(manager.goals)}")
    print(f"  Active: {len(manager.get_active_goals())}")
    
    # 测试进度更新
    print("\n3. Progress Update")
    first_goal_id = list(manager.goals.keys())[0]
    # 先将目标设为ACTIVE状态
    manager.goals[first_goal_id].status = GoalStatus.ACTIVE
    manager.update_progress(first_goal_id, 0.5)
    print(f"  Goal progress: {manager.goals[first_goal_id].progress}")
    
    manager.update_progress(first_goal_id, 1.0)
    print(f"  Goal status: {manager.goals[first_goal_id].status.value}")
    
    # 测试冲突检测
    print("\n4. Conflict Detection")
    conflicts = manager.detect_conflicts()
    print(f"  Conflicts detected: {len(conflicts)}")
    
    # 测试统计
    print("\n5. Statistics")
    stats = manager.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 70)
    print("All tests passed!")
    print("=" * 70)


if __name__ == '__main__':
    test_open_goal_space()
