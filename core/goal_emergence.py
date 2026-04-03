#!/usr/bin/env python3
"""
MOSS v7.0 - Goal Emergence Engine
目标涌现引擎

核心功能:
- 自主目标生成
- 价值对齐评估
- 目标层次演化
- 涌现检测

Author: MOSS Project
Date: 2026-04-03
Version: 7.0.0-dev
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class EmergentGoal:
    """涌现目标"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str = ""
    value_alignment: float = 0.5
    complexity: float = 0.5
    emergence_level: int = 1
    parent_goals: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'description': self.description,
            'value_alignment': self.value_alignment,
            'complexity': self.complexity,
            'emergence_level': self.emergence_level,
            'parent_goals': self.parent_goals,
            'created_at': self.created_at.isoformat()
        }


class GoalEmergence:
    """
    目标涌现引擎
    
    检测和生成涌现目标
    """
    
    def __init__(self, n_agents: int = 50):
        self.n_agents = n_agents
        
        self.goals: Dict[str, EmergentGoal] = {}
        self.agent_goals: Dict[str, List[str]] = {}
        
        self.stats = {
            'goals_generated': 0,
            'emergence_events': 0,
            'avg_alignment': 0.0,
            'max_complexity': 0.0
        }
    
    def generate_emergent_goal(self, 
                              agent_goals: List[str],
                              context: Dict) -> Optional[EmergentGoal]:
        """
        生成涌现目标
        
        Args:
            agent_goals: Agent 目标列表
            context: 上下文
            
        Returns:
            涌现目标或 None
        """
        if len(agent_goals) < 3:
            return None
        
        # 检测共同模式
        common_themes = self._detect_common_themes(agent_goals)
        
        if not common_themes:
            return None
        
        # 生成涌现目标
        goal = EmergentGoal(
            description=f"Emergent: {common_themes[0]}",
            value_alignment=self._calculate_alignment(common_themes, context),
            complexity=min(1.0, len(agent_goals) / 10),
            emergence_level=min(5, len(common_themes)),
            parent_goals=agent_goals[:5]
        )
        
        self.goals[goal.id] = goal
        self.stats['goals_generated'] += 1
        self.stats['emergence_events'] += 1
        
        # 更新统计
        alignments = [g.value_alignment for g in self.goals.values()]
        self.stats['avg_alignment'] = np.mean(alignments) if alignments else 0
        
        complexities = [g.complexity for g in self.goals.values()]
        self.stats['max_complexity'] = max(complexities) if complexities else 0
        
        return goal
    
    def _detect_common_themes(self, goals: List[str]) -> List[str]:
        """检测共同主题"""
        # 简化实现：提取关键词
        keywords = {}
        
        for goal in goals:
            words = goal.lower().split()
            for word in words:
                if len(word) > 4:  # 忽略短词
                    keywords[word] = keywords.get(word, 0) + 1
        
        # 返回出现频率高的词
        common = [k for k, v in keywords.items() if v >= len(goals) * 0.3]
        return common[:3]
    
    def _calculate_alignment(self, themes: List[str], 
                            context: Dict) -> float:
        """计算价值对齐度"""
        # 简化实现：基于上下文相似度
        base_alignment = 0.7
        
        # 考虑上下文因素
        if context.get('cooperation', False):
            base_alignment += 0.1
        if context.get('altruism', False):
            base_alignment += 0.1
        
        return min(1.0, base_alignment)
    
    def get_emergence_hierarchy(self) -> Dict:
        """获取涌现层次"""
        hierarchy = {
            'level_1': [],
            'level_2': [],
            'level_3': [],
            'level_4': [],
            'level_5': []
        }
        
        for goal in self.goals.values():
            level_key = f'level_{min(goal.emergence_level, 5)}'
            hierarchy[level_key].append(goal.to_dict())
        
        return hierarchy
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            'stats': self.stats,
            'total_goals': len(self.goals),
            'hierarchy': self.get_emergence_hierarchy()
        }


# 测试代码
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v7.0 - Goal Emergence Test")
    print("=" * 60)
    
    # 创建涌现引擎
    emergence = GoalEmergence(n_agents=50)
    
    # 测试涌现目标生成
    print("\n1. 测试涌现目标生成...")
    
    agent_goals = [
        "Improve coding skills",
        "Learn machine learning",
        "Build AI system",
        "Optimize performance",
        "Create intelligent agent"
    ]
    
    context = {'cooperation': True, 'altruism': False}
    
    goal = emergence.generate_emergent_goal(agent_goals, context)
    
    if goal:
        print(f"   ✅ 涌现目标：{goal.description}")
        print(f"   价值对齐：{goal.value_alignment:.2f}")
        print(f"   复杂度：{goal.complexity:.2f}")
        print(f"   涌现层次：{goal.emergence_level}")
    else:
        print("   ❌ 未检测到涌现")
    
    # 获取更多状态
    print("\n2. 涌现引擎状态:")
    status = emergence.get_status()
    print(f"   总目标数：{status['total_goals']}")
    print(f"   涌现事件：{status['stats']['emergence_events']}")
    print(f"   平均对齐：{status['stats']['avg_alignment']:.2f}")
    print(f"   最大复杂度：{status['stats']['max_complexity']:.2f}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)
