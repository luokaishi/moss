#!/usr/bin/env python3
"""
MOSS v6.0 - Self Reflection Module
自我反思模块

核心功能:
- 错误分析
- 策略优化
- 知识整合
- 反思层次

Author: MOSS Project
Date: 2026-04-03
Version: 6.0.0-dev
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Reflection:
    """反思记录"""
    content: str
    depth: int  # 1-5
    insights: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'content': self.content,
            'depth': self.depth,
            'insights': self.insights,
            'action_items': self.action_items,
            'timestamp': self.timestamp.isoformat()
        }


class SelfReflection:
    """
    自我反思
    
    进行深度反思和策略优化
    """
    
    def __init__(self):
        self.reflection_history: List[Reflection] = []
        
        self.stats = {
            'total_reflections': 0,
            'avg_depth': 0.0,
            'insights_generated': 0,
            'actions_created': 0
        }
    
    def reflect_on_error(self, error_description: str,
                        context: Dict,
                        outcome: float) -> Reflection:
        """
        反思错误
        
        Args:
            error_description: 错误描述
            context: 上下文
            outcome: 结果分数
            
        Returns:
            反思记录
        """
        # 错误分析
        insights = []
        action_items = []
        
        # 深度 1: 描述错误
        content = f"Error: {error_description}"
        
        # 深度 2: 分析原因
        if outcome < 0.5:
            insights.append("Performance below threshold")
            action_items.append("Identify root cause")
        
        # 深度 3: 提取教训
        insights.append(f"Learned from outcome: {outcome:.2f}")
        
        # 深度 4: 策略调整
        action_items.append("Adjust strategy for similar situations")
        
        # 深度 5: 知识整合
        insights.append("Integrated into knowledge base")
        
        # 计算深度
        depth = min(5, 1 + len(insights) + len(action_items))
        
        reflection = Reflection(
            content=content,
            depth=depth,
            insights=insights,
            action_items=action_items
        )
        
        self._record_reflection(reflection)
        return reflection
    
    def reflect_on_success(self, success_description: str,
                          context: Dict,
                          outcome: float) -> Reflection:
        """
        反思成功
        
        Args:
            success_description: 成功描述
            context: 上下文
            outcome: 结果分数
            
        Returns:
            反思记录
        """
        insights = []
        action_items = []
        
        content = f"Success: {success_description}"
        
        # 分析成功因素
        insights.append(f"High performance: {outcome:.2f}")
        
        # 提取可重复策略
        action_items.append("Document successful strategy")
        
        # 知识整合
        insights.append("Strategy added to repertoire")
        
        depth = min(5, 1 + len(insights) + len(action_items))
        
        reflection = Reflection(
            content=content,
            depth=depth,
            insights=insights,
            action_items=action_items
        )
        
        self._record_reflection(reflection)
        return reflection
    
    def reflect_on_decision(self, decision: str,
                           alternatives: List[str],
                           outcome: float) -> Reflection:
        """
        反思决策
        
        Args:
            decision: 决策内容
            alternatives: 备选方案
            outcome: 结果分数
            
        Returns:
            反思记录
        """
        insights = []
        action_items = []
        
        content = f"Decision: {decision}"
        
        # 分析决策质量
        if outcome > 0.7:
            insights.append("Good decision quality")
        elif outcome < 0.3:
            insights.append("Poor decision quality")
            action_items.append("Review decision criteria")
        
        # 考虑备选方案
        insights.append(f"Considered {len(alternatives)} alternatives")
        
        # 改进建议
        if len(alternatives) < 3:
            action_items.append("Consider more alternatives next time")
        
        depth = min(5, 1 + len(insights) + len(action_items))
        
        reflection = Reflection(
            content=content,
            depth=depth,
            insights=insights,
            action_items=action_items
        )
        
        self._record_reflection(reflection)
        return reflection
    
    def _record_reflection(self, reflection: Reflection):
        """记录反思"""
        self.reflection_history.append(reflection)
        self.stats['total_reflections'] += 1
        self.stats['insights_generated'] += len(reflection.insights)
        self.stats['actions_created'] += len(reflection.action_items)
        
        # 更新平均深度
        depths = [r.depth for r in self.reflection_history]
        self.stats['avg_depth'] = np.mean(depths)
    
    def get_deepest_reflection(self) -> Optional[Reflection]:
        """获取最深的反思"""
        if not self.reflection_history:
            return None
        
        return max(self.reflection_history, key=lambda r: r.depth)
    
    def get_reflection_summary(self) -> Dict:
        """获取反思摘要"""
        if not self.reflection_history:
            return {'total': 0}
        
        depths = [r.depth for r in self.reflection_history]
        
        return {
            'total': len(self.reflection_history),
            'avg_depth': np.mean(depths),
            'max_depth': max(depths),
            'total_insights': self.stats['insights_generated'],
            'total_actions': self.stats['actions_created']
        }
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            'stats': self.stats,
            'summary': self.get_reflection_summary(),
            'history_length': len(self.reflection_history)
        }


# 测试代码
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v6.0 - Self Reflection Test")
    print("=" * 60)
    
    # 创建自我反思
    reflection = SelfReflection()
    
    # 反思错误
    print("\n1. 反思错误...")
    r1 = reflection.reflect_on_error(
        "Failed to solve problem",
        {'difficulty': 0.8},
        outcome=0.3
    )
    print(f"   深度：{r1.depth}")
    print(f"   洞察：{len(r1.insights)}")
    print(f"   行动项：{len(r1.action_items)}")
    
    # 反思成功
    print("\n2. 反思成功...")
    r2 = reflection.reflect_on_success(
        "Completed task successfully",
        {'complexity': 0.6},
        outcome=0.9
    )
    print(f"   深度：{r2.depth}")
    print(f"   洞察：{len(r2.insights)}")
    print(f"   行动项：{len(r2.action_items)}")
    
    # 反思决策
    print("\n3. 反思决策...")
    r3 = reflection.reflect_on_decision(
        "Chose algorithm A",
        ["A", "B", "C"],
        outcome=0.8
    )
    print(f"   深度：{r3.depth}")
    
    # 获取摘要
    print("\n4. 反思摘要:")
    summary = reflection.get_reflection_summary()
    print(f"   总反思数：{summary.get('total', 0)}")
    print(f"   平均深度：{summary.get('avg_depth', 0):.2f}")
    print(f"   最大深度：{summary.get('max_depth', 0)}")
    print(f"   总洞察：{summary.get('total_insights', 0)}")
    print(f"   总行动：{summary.get('total_actions', 0)}")
    
    # 获取状态
    print("\n5. 自我反思状态:")
    status = reflection.get_status()
    print(f"   历史记录：{status['history_length']}")
    print(f"   平均深度：{status['stats']['avg_depth']:.2f}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)
