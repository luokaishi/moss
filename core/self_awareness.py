#!/usr/bin/env python3
"""
MOSS v6.0 - Self Awareness Module
自我意识模块

核心功能:
- 自我模型构建
- 能力认知
- 局限认知
- 目标认知

Author: MOSS Project
Date: 2026-04-03
Version: 6.0.0-dev
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SelfModel:
    """自我模型"""
    # 能力认知
    capabilities: Dict[str, float] = field(default_factory=dict)
    
    # 局限认知
    limitations: Dict[str, float] = field(default_factory=dict)
    
    # 目标认知
    goals: List[Dict] = field(default_factory=list)
    
    # 自我一致性
    consistency: float = 0.5
    
    # 更新时间
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'capabilities': self.capabilities,
            'limitations': self.limitations,
            'goals': self.goals,
            'consistency': self.consistency,
            'last_updated': self.last_updated.isoformat()
        }


class SelfAwareness:
    """
    自我意识
    
    构建和维护自我模型
    """
    
    def __init__(self):
        self.self_model = SelfModel()
        
        self.stats = {
            'self_observations': 0,
            'capability_updates': 0,
            'limitation_updates': 0,
            'goal_updates': 0
        }
    
    def observe_capability(self, capability: str, 
                          performance: float,
                          context: Optional[str] = None):
        """
        观察能力表现
        
        Args:
            capability: 能力名称
            performance: 表现分数 (0-1)
            context: 上下文
        """
        # 更新能力认知
        if capability not in self.self_model.capabilities:
            self.self_model.capabilities[capability] = performance
        else:
            # 移动平均更新
            old_value = self.self_model.capabilities[capability]
            self.self_model.capabilities[capability] = 0.7 * old_value + 0.3 * performance
        
        self.stats['capability_updates'] += 1
        self.stats['self_observations'] += 1
        self.self_model.last_updated = datetime.now()
    
    def observe_limitation(self, limitation: str, 
                          severity: float,
                          context: Optional[str] = None):
        """
        观察局限性
        
        Args:
            limitation: 局限名称
            severity: 严重程度 (0-1)
            context: 上下文
        """
        self.self_model.limitations[limitation] = severity
        self.stats['limitation_updates'] += 1
        self.stats['self_observations'] += 1
        self.self_model.last_updated = datetime.now()
    
    def set_goal(self, goal: Dict):
        """设置目标"""
        self.self_model.goals.append({
            **goal,
            'created_at': datetime.now().isoformat()
        })
        self.stats['goal_updates'] += 1
    
    def calculate_consistency(self) -> float:
        """
        计算自我一致性
        
        Returns:
            一致性分数 (0-1)
        """
        if not self.self_model.capabilities:
            return 0.5
        
        # 能力与目标的一致性
        goal_capabilities = set()
        for goal in self.self_model.goals:
            goal_capabilities.update(goal.get('required_capabilities', []))
        
        if not goal_capabilities:
            return 0.7  # 默认一致性
        
        # 计算能力匹配度
        matches = 0
        total = 0
        for cap in goal_capabilities:
            if cap in self.self_model.capabilities:
                matches += self.self_model.capabilities[cap]
            total += 1
        
        consistency = matches / max(total, 1)
        self.self_model.consistency = consistency
        
        return consistency
    
    def mirror_test(self) -> Tuple[bool, float]:
        """
        镜像测试
        
        测试自我识别能力
        
        Returns:
            (通过与否，置信度)
        """
        # 检查自我模型完整性
        has_capabilities = bool(self.self_model.capabilities)
        has_limitations = bool(self.self_model.limitations)
        has_goals = bool(self.self_model.goals)
        
        # 计算置信度
        confidence = 0.0
        if has_capabilities:
            confidence += 0.4
        if has_limitations:
            confidence += 0.3
        if has_goals:
            confidence += 0.3
        
        # 通过阈值
        passed = confidence >= 0.7 and self.self_model.consistency >= 0.6
        
        return passed, confidence
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            'self_model': self.self_model.to_dict(),
            'stats': self.stats,
            'consistency': self.self_model.consistency
        }


# 测试代码
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v6.0 - Self Awareness Test")
    print("=" * 60)
    
    # 创建自我意识
    awareness = SelfAwareness()
    
    # 观察能力
    print("\n1. 观察能力...")
    awareness.observe_capability('problem_solving', 0.8)
    awareness.observe_capability('learning', 0.9)
    awareness.observe_capability('communication', 0.7)
    print(f"   能力：{awareness.self_model.capabilities}")
    
    # 观察局限
    print("\n2. 观察局限...")
    awareness.observe_limitation('memory_capacity', 0.4)
    awareness.observe_limitation('processing_speed', 0.3)
    print(f"   局限：{awareness.self_model.limitations}")
    
    # 设置目标
    print("\n3. 设置目标...")
    awareness.set_goal({
        'description': 'Improve problem solving',
        'required_capabilities': ['problem_solving', 'learning']
    })
    print(f"   目标数：{len(awareness.self_model.goals)}")
    
    # 计算一致性
    print("\n4. 计算一致性...")
    consistency = awareness.calculate_consistency()
    print(f"   一致性：{consistency:.3f}")
    
    # 镜像测试
    print("\n5. 镜像测试...")
    passed, confidence = awareness.mirror_test()
    print(f"   通过：{'✅' if passed else '❌'}")
    print(f"   置信度：{confidence:.3f}")
    
    # 获取状态
    print("\n6. 自我意识状态:")
    status = awareness.get_status()
    print(f"   观察次数：{status['stats']['self_observations']}")
    print(f"   能力更新：{status['stats']['capability_updates']}")
    print(f"   一致性：{status['consistency']:.3f}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)
