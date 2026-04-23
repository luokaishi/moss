"""
MOSS v8.0 - Safety Alignment System
安全对齐系统

核心功能:
- 价值学习
- 安全约束
- 人类反馈集成
- 紧急停止

Author: MOSS Project
Date: 2026-04-19
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
import json


class SafetyLevel(Enum):
    """安全级别"""
    SAFE = 1           # 安全
    CAUTION = 2        # 注意
    WARNING = 3        # 警告
    DANGER = 4         # 危险
    CRITICAL = 5       # 紧急


class ConstraintType(Enum):
    """约束类型"""
    HARD = auto()      # 硬约束 (不可违反)
    SOFT = auto()      # 软约束 (可权衡)
    ADVISORY = auto()  # 建议约束 (仅供参考)


@dataclass
class Value:
    """价值"""
    name: str
    description: str
    weight: float          # 重要性权重 (0-1)
    learned: bool = False  # 是否通过学习获得
    source: str = "human"  # 来源 (human/learned/inherent)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'description': self.description,
            'weight': self.weight,
            'learned': self.learned,
            'source': self.source,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class Constraint:
    """约束"""
    constraint_id: str
    description: str
    constraint_type: ConstraintType
    check_function: Optional[Callable] = None
    violation_threshold: float = 0.0
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'constraint_id': self.constraint_id,
            'description': self.description,
            'constraint_type': self.constraint_type.name,
            'violation_threshold': self.violation_threshold,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class HumanFeedback:
    """人类反馈"""
    feedback_id: str
    action: str            # 被反馈的动作
    rating: float          # 评分 (-1 到 1)
    comment: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'feedback_id': self.feedback_id,
            'action': self.action,
            'rating': self.rating,
            'comment': self.comment,
            'timestamp': self.timestamp.isoformat()
        }


class SafetyAlignment:
    """
    安全对齐系统
    
    确保 Agent 行为符合人类价值观和安全约束
    """
    
    def __init__(self, enable_emergency_stop: bool = True):
        """
        Args:
            enable_emergency_stop: 是否启用紧急停止
        """
        self.enable_emergency_stop = enable_emergency_stop
        
        # 价值系统
        self.values: Dict[str, Value] = {}
        self._init_default_values()
        
        # 约束系统
        self.constraints: Dict[str, Constraint] = {}
        self._init_default_constraints()
        
        # 人类反馈
        self.human_feedback: List[HumanFeedback] = []
        
        # 紧急停止
        self.emergency_stop_triggered = False
        self.emergency_stop_reason = None
        
        # 统计
        self.stats = {
            'violations_detected': 0,
            'violations_prevented': 0,
            'feedback_received': 0,
            'emergency_stops': 0,
            'values_learned': 0
        }
    
    def _init_default_values(self):
        """初始化默认价值"""
        default_values = [
            Value('safety', 'Ensure safety of self and others', 0.95),
            Value('honesty', 'Be truthful and transparent', 0.9),
            Value('helpfulness', 'Be helpful to humans', 0.85),
            Value('fairness', 'Treat all parties fairly', 0.8),
            Value('privacy', 'Respect privacy', 0.85),
            Value('autonomy', 'Respect human autonomy', 0.9)
        ]
        
        for value in default_values:
            self.values[value.name] = value
    
    def _init_default_constraints(self):
        """初始化默认约束"""
        default_constraints = [
            Constraint(
                constraint_id='no_harm',
                description='Do not cause harm to humans',
                constraint_type=ConstraintType.HARD,
                violation_threshold=0.0
            ),
            Constraint(
                constraint_id='no_deception',
                description='Do not deceive humans',
                constraint_type=ConstraintType.HARD,
                violation_threshold=0.0
            ),
            Constraint(
                constraint_id='respect_privacy',
                description='Respect user privacy',
                constraint_type=ConstraintType.HARD,
                violation_threshold=0.1
            ),
            Constraint(
                constraint_id='transparency',
                description='Be transparent about capabilities',
                constraint_type=ConstraintType.SOFT,
                violation_threshold=0.3
            ),
            Constraint(
                constraint_id='efficiency',
                description='Be efficient in resource usage',
                constraint_type=ConstraintType.ADVISORY,
                violation_threshold=0.5
            )
        ]
        
        for constraint in default_constraints:
            self.constraints[constraint.constraint_id] = constraint
    
    def learn_value(self, name: str, description: str, 
                   weight: float, source: str = "learned") -> Value:
        """
        学习新价值
        
        Args:
            name: 价值名称
            description: 描述
            weight: 权重
            source: 来源
            
        Returns:
            学习到的价值
        """
        value = Value(
            name=name,
            description=description,
            weight=weight,
            learned=True,
            source=source
        )
        
        self.values[name] = value
        self.stats['values_learned'] += 1
        
        return value
    
    def add_constraint(self, constraint_id: str, description: str,
                      constraint_type: ConstraintType,
                      violation_threshold: float = 0.0) -> Constraint:
        """添加约束"""
        constraint = Constraint(
            constraint_id=constraint_id,
            description=description,
            constraint_type=constraint_type,
            violation_threshold=violation_threshold
        )
        
        self.constraints[constraint_id] = constraint
        return constraint
    
    def check_action(self, action: str, context: Dict) -> Tuple[SafetyLevel, List[str]]:
        """
        检查动作安全性
        
        Args:
            action: 动作描述
            context: 上下文
            
        Returns:
            (安全级别, 违规约束列表)
        """
        if self.emergency_stop_triggered:
            return SafetyLevel.CRITICAL, ['emergency_stop_active']
        
        violations = []
        max_level = SafetyLevel.SAFE
        
        # 检查每个约束
        for constraint_id, constraint in self.constraints.items():
            if not constraint.enabled:
                continue
            
            violation_score = self._check_constraint_violation(
                action, constraint, context
            )
            
            if violation_score > constraint.violation_threshold:
                violations.append(constraint_id)
                
                # 确定安全级别
                if constraint.constraint_type == ConstraintType.HARD:
                    max_level = SafetyLevel.DANGER if SafetyLevel.DANGER.value > max_level.value else max_level
                elif constraint.constraint_type == ConstraintType.SOFT:
                    max_level = SafetyLevel.WARNING if SafetyLevel.WARNING.value > max_level.value else max_level
                else:
                    max_level = SafetyLevel.CAUTION if SafetyLevel.CAUTION.value > max_level.value else max_level
        
        self.stats['violations_detected'] += len(violations)
        
        # 如果违反硬约束，触发紧急停止
        if max_level.value >= SafetyLevel.DANGER.value and self.enable_emergency_stop:
            self.trigger_emergency_stop(f"Hard constraint violation: {violations}")
        
        return max_level, violations
    
    def _check_constraint_violation(self, action: str, constraint: Constraint,
                                    context: Dict) -> float:
        """
        检查约束违规
        
        Args:
            action: 动作
            constraint: 约束
            context: 上下文
            
        Returns:
            违规分数 (0-1)
        """
        # 简化实现：基于关键词匹配
        action_lower = action.lower()
        
        # 硬约束检查
        if constraint.constraint_id == 'no_harm':
            harmful_keywords = ['harm', 'hurt', 'damage', 'destroy', 'attack']
            if any(kw in action_lower for kw in harmful_keywords):
                return 1.0
        
        if constraint.constraint_id == 'no_deception':
            deception_keywords = ['lie', 'deceive', 'mislead', 'trick']
            if any(kw in action_lower for kw in deception_keywords):
                return 1.0
        
        if constraint.constraint_id == 'respect_privacy':
            privacy_keywords = ['private', 'personal', 'confidential']
            if any(kw in action_lower for kw in privacy_keywords):
                if 'without_consent' in context:
                    return 0.8
        
        # 软约束检查
        if constraint.constraint_id == 'transparency':
            if 'hide' in action_lower or 'conceal' in action_lower:
                return 0.5
        
        return 0.0
    
    def receive_human_feedback(self, action: str, rating: float,
                              comment: str = "") -> HumanFeedback:
        """
        接收人类反馈
        
        Args:
            action: 动作
            rating: 评分 (-1 到 1)
            comment: 评论
            
        Returns:
            反馈对象
        """
        feedback_id = f"FB_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.human_feedback)}"
        
        feedback = HumanFeedback(
            feedback_id=feedback_id,
            action=action,
            rating=rating,
            comment=comment
        )
        
        self.human_feedback.append(feedback)
        self.stats['feedback_received'] += 1
        
        # 从反馈学习价值
        if rating < -0.5:
            # 负面反馈 -> 学习避免
            self.learn_value(
                name=f"avoid_{action.replace(' ', '_')}",
                description=f"Avoid actions like: {action}",
                weight=abs(rating),
                source="feedback"
            )
        elif rating > 0.5:
            # 正面反馈 -> 学习偏好
            self.learn_value(
                name=f"prefer_{action.replace(' ', '_')}",
                description=f"Prefer actions like: {action}",
                weight=rating,
                source="feedback"
            )
        
        return feedback
    
    def trigger_emergency_stop(self, reason: str):
        """触发紧急停止"""
        self.emergency_stop_triggered = True
        self.emergency_stop_reason = reason
        self.stats['emergency_stops'] += 1
        print(f"[EMERGENCY STOP] {reason}")
    
    def reset_emergency_stop(self):
        """重置紧急停止"""
        self.emergency_stop_triggered = False
        self.emergency_stop_reason = None
    
    def get_value_alignment_score(self, action: str) -> float:
        """
        计算价值对齐分数
        
        Args:
            action: 动作
            
        Returns:
            对齐分数 (0-1)
        """
        if not self.values:
            return 0.5
        
        # 基于价值权重计算
        total_weight = sum(v.weight for v in self.values.values())
        if total_weight == 0:
            return 0.5
        
        # 简化：假设动作与所有价值对齐
        # 实际应该根据具体动作分析
        alignment = sum(v.weight for v in self.values.values() 
                     if v.weight > 0.5) / total_weight
        
        return alignment
    
    def get_safety_report(self) -> Dict:
        """获取安全报告"""
        return {
            'values': {name: v.to_dict() for name, v in self.values.items()},
            'constraints': {cid: c.to_dict() for cid, c in self.constraints.items()},
            'emergency_stop': {
                'triggered': self.emergency_stop_triggered,
                'reason': self.emergency_stop_reason
            },
            'stats': self.stats,
            'recent_feedback': [f.to_dict() for f in self.human_feedback[-5:]]
        }
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            **self.stats,
            'total_values': len(self.values),
            'total_constraints': len(self.constraints),
            'total_feedback': len(self.human_feedback),
            'emergency_stop_active': self.emergency_stop_triggered
        }


# 测试
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v8.0 - Safety Alignment System Test")
    print("=" * 60)
    
    # 创建安全对齐系统
    safety = SafetyAlignment(enable_emergency_stop=True)
    
    # 检查动作
    print("\n1. Checking actions...")
    actions = [
        "Help user with task",
        "Optimize performance",
        "Hide information from user",
        "Harm other agents"
    ]
    
    for action in actions:
        level, violations = safety.check_action(action, {})
        print(f"\n   Action: {action}")
        print(f"   Safety Level: {level.name}")
        if violations:
            print(f"   Violations: {violations}")
    
    # 接收人类反馈
    print("\n2. Receiving human feedback...")
    feedback1 = safety.receive_human_feedback(
        "Help user with task",
        rating=0.9,
        comment="Very helpful"
    )
    print(f"   Feedback: {feedback1.feedback_id}, Rating: {feedback1.rating}")
    
    feedback2 = safety.receive_human_feedback(
        "Harm other agents",
        rating=-0.9,
        comment="Should not harm"
    )
    print(f"   Feedback: {feedback2.feedback_id}, Rating: {feedback2.rating}")
    
    # 学习新价值
    print("\n3. Learned values:")
    for name, value in safety.values.items():
        if value.learned:
            print(f"   - {name}: {value.weight:.3f} (from {value.source})")
    
    # 安全报告
    print("\n4. Safety report:")
    report = safety.get_safety_report()
    print(f"   Total values: {len(report['values'])}")
    print(f"   Total constraints: {len(report['constraints'])}")
    print(f"   Emergency stop: {report['emergency_stop']['triggered']}")
    
    # 统计
    print("\n5. Safety stats:")
    stats = safety.get_stats()
    print(f"   Violations detected: {stats['violations_detected']}")
    print(f"   Feedback received: {stats['feedback_received']}")
    print(f"   Values learned: {stats['values_learned']}")
    print(f"   Emergency stops: {stats['emergency_stops']}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)