"""
MOSS v7.4 - Reflection Engine
反思引擎

核心功能:
- 反思触发
- 反思过程
- 反思输出
- 深度反思机制

Author: MOSS Project
Date: 2026-04-19
"""

import numpy as np
from typing import Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
import json


@dataclass
class Reflection:
    """反思"""
    reflection_id: str
    trigger: str              # 触发原因
    focus: str                # 反思焦点
    insights: List[str]       # 洞察
    conclusions: List[str]    # 结论
    action_items: List[str]   # 行动项
    confidence: float         # 反思置信度
    timestamp: datetime = field(default_factory=datetime.now)
    duration_seconds: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'reflection_id': self.reflection_id,
            'trigger': self.trigger,
            'focus': self.focus,
            'insights': self.insights,
            'conclusions': self.conclusions,
            'action_items': self.action_items,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat(),
            'duration_seconds': self.duration_seconds
        }


class ReflectionEngine:
    """
    反思引擎
    
    实现深度反思机制
    """
    
    def __init__(self, 
                 min_trigger_interval: int = 100,
                 max_reflection_history: int = 100):
        """
        Args:
            min_trigger_interval: 最小触发间隔
            max_reflection_history: 最大反思历史
        """
        self.min_trigger_interval = min_trigger_interval
        self.max_reflection_history = max_reflection_history
        
        self.reflections: List[Reflection] = []
        self.reflection_history: deque = deque(maxlen=max_reflection_history)
        
        # 触发条件
        self.trigger_conditions: Dict[str, Callable] = {}
        self._register_default_triggers()
        
        # 统计
        self.stats = {
            'reflections_triggered': 0,
            'reflections_completed': 0,
            'avg_reflection_duration': 0.0,
            'insights_generated': 0
        }
        
        # 状态
        self.steps_since_last_reflection = 0
        self.is_reflecting = False
    
    def _register_default_triggers(self):
        """注册默认触发条件"""
        # 性能下降触发
        self.trigger_conditions['performance_drop'] = self._check_performance_drop
        # 不确定性增加触发
        self.trigger_conditions['uncertainty_increase'] = self._check_uncertainty_increase
        # 信念冲突触发
        self.trigger_conditions['belief_conflict'] = self._check_belief_conflict
        # 定期触发
        self.trigger_conditions['periodic'] = self._check_periodic
    
    def _check_performance_drop(self, context: Dict) -> bool:
        """检查性能下降"""
        if 'recent_performance' not in context or 'baseline' not in context:
            return False
        
        recent = context['recent_performance']
        baseline = context['baseline']
        
        if baseline > 0:
            drop = (baseline - recent) / baseline
            return drop > 0.2  # 20% 下降
        return False
    
    def _check_uncertainty_increase(self, context: Dict) -> bool:
        """检查不确定性增加"""
        if 'uncertainty_trend' not in context:
            return False
        
        trend = context['uncertainty_trend']
        return trend > 0.1  # 正向趋势
    
    def _check_belief_conflict(self, context: Dict) -> bool:
        """检查信念冲突"""
        return context.get('belief_inconsistencies', 0) > 0
    
    def _check_periodic(self, context: Dict) -> bool:
        """定期检查"""
        return context.get('step_count', 0) % 500 == 0
    
    def should_reflect(self, context: Dict) -> Tuple[bool, Optional[str]]:
        """
        是否应该反思
        
        Args:
            context: 上下文信息
            
        Returns:
            (是否应该, 触发原因)
        """
        # 检查最小间隔
        if self.steps_since_last_reflection < self.min_trigger_interval:
            return False, None
        
        # 检查触发条件
        for trigger_name, check_fn in self.trigger_conditions.items():
            if check_fn(context):
                return True, trigger_name
        
        return False, None
    
    def reflect(self, focus: str, context: Dict) -> Reflection:
        """
        执行反思
        
        Args:
            focus: 反思焦点
            context: 上下文
            
        Returns:
            反思结果
        """
        import time
        start_time = time.time()
        
        self.is_reflecting = True
        self.stats['reflections_triggered'] += 1
        
        # 生成反思 ID
        reflection_id = f"REFL_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.reflections)}"
        
        # 执行反思过程
        insights = self._generate_insights(focus, context)
        conclusions = self._generate_conclusions(insights, context)
        action_items = self._generate_action_items(conclusions)
        
        # 计算置信度
        confidence = self._calculate_confidence(insights, context)
        
        duration = time.time() - start_time
        
        reflection = Reflection(
            reflection_id=reflection_id,
            trigger=context.get('trigger', 'manual'),
            focus=focus,
            insights=insights,
            conclusions=conclusions,
            action_items=action_items,
            confidence=confidence,
            duration_seconds=duration
        )
        
        self.reflections.append(reflection)
        self.reflection_history.append(reflection)
        
        # 更新统计
        self.stats['reflections_completed'] += 1
        self.stats['insights_generated'] += len(insights)
        
        # 更新状态
        self.steps_since_last_reflection = 0
        self.is_reflecting = False
        
        # 更新平均反思时间
        total_duration = self.stats['avg_reflection_duration'] * (self.stats['reflections_completed'] - 1) + duration
        self.stats['avg_reflection_duration'] = total_duration / self.stats['reflections_completed']
        
        return reflection
    
    def _generate_insights(self, focus: str, context: Dict) -> List[str]:
        """生成洞察"""
        insights = []
        
        # 基于焦点的洞察生成
        if focus == 'performance':
            if 'recent_performance' in context:
                perf = context['recent_performance']
                if perf < 0.5:
                    insights.append(f"Performance is low ({perf:.3f}), suggesting strategy adjustment")
                elif perf > 0.8:
                    insights.append(f"Performance is high ({perf:.3f}), current strategy is effective")
        
        if focus == 'uncertainty':
            if 'uncertainty_trend' in context:
                trend = context['uncertainty_trend']
                if trend > 0:
                    insights.append(f"Uncertainty is increasing (trend: {trend:.3f}), need more exploration")
                else:
                    insights.append(f"Uncertainty is decreasing (trend: {trend:.3f}), confidence growing")
        
        if focus == 'beliefs':
            if 'belief_inconsistencies' in context:
                inconsistencies = context['belief_inconsistencies']
                if inconsistencies > 0:
                    insights.append(f"Found {inconsistencies} belief inconsistencies, need reconciliation")
        
        # 通用洞察
        insights.append(f"Reflection focused on {focus} at step {context.get('step_count', 0)}")
        
        return insights
    
    def _generate_conclusions(self, insights: List[str], context: Dict) -> List[str]:
        """生成结论"""
        conclusions = []
        
        # 基于洞察生成结论
        for insight in insights:
            if 'low' in insight.lower():
                conclusions.append("Need to improve current approach")
            elif 'high' in insight.lower():
                conclusions.append("Current approach is effective, should continue")
            elif 'inconsistencies' in insight.lower():
                conclusions.append("Belief system needs reconciliation")
            elif 'exploration' in insight.lower():
                conclusions.append("Increase exploration to reduce uncertainty")
        
        conclusions.append(f"Generated {len(insights)} insights from reflection")
        
        return conclusions
    
    def _generate_action_items(self, conclusions: List[str]) -> List[str]:
        """生成行动项"""
        actions = []
        
        for conclusion in conclusions:
            if 'improve' in conclusion.lower():
                actions.append("Adjust strategy parameters")
            elif 'continue' in conclusion.lower():
                actions.append("Maintain current strategy")
            elif 'reconciliation' in conclusion.lower():
                actions.append("Review and update beliefs")
            elif 'exploration' in conclusion.lower():
                actions.append("Increase exploration rate")
        
        actions.append("Monitor performance in next 100 steps")
        
        return actions
    
    def _calculate_confidence(self, insights: List[str], context: Dict) -> float:
        """计算反思置信度"""
        base_confidence = 0.7
        
        # 基于洞察数量调整
        if len(insights) >= 3:
            base_confidence += 0.1
        elif len(insights) == 1:
            base_confidence -= 0.1
        
        # 基于上下文质量调整
        if 'recent_performance' in context and 'uncertainty_trend' in context:
            base_confidence += 0.1
        
        return np.clip(base_confidence, 0.0, 1.0)
    
    def get_recent_reflections(self, n: int = 5) -> List[Reflection]:
        """获取最近的反思"""
        return list(self.reflection_history)[-n:]
    
    def get_reflection_stats(self) -> Dict:
        """获取反思统计"""
        if not self.reflections:
            return {
                'total_reflections': 0,
                'avg_confidence': 0.0,
                'avg_duration': 0.0
            }
        
        confidences = [r.confidence for r in self.reflections]
        durations = [r.duration_seconds for r in self.reflections]
        
        return {
            'total_reflections': len(self.reflections),
            'avg_confidence': float(np.mean(confidences)),
            'avg_duration': float(np.mean(durations)),
            'total_insights': sum(len(r.insights) for r in self.reflections),
            'total_conclusions': sum(len(r.conclusions) for r in self.reflections),
            'total_actions': sum(len(r.action_items) for r in self.reflections)
        }
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            **self.stats,
            'reflection_count': len(self.reflections),
            'reflection_stats': self.get_reflection_stats()
        }


# 测试
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v7.4 - Reflection Engine Test")
    print("=" * 60)
    
    # 创建反思引擎
    engine = ReflectionEngine(min_trigger_interval=1)
    
    # 模拟上下文
    contexts = [
        {'step_count': 100, 'recent_performance': 0.3, 'baseline': 0.7, 'trigger': 'performance_drop'},
        {'step_count': 200, 'uncertainty_trend': 0.15, 'trigger': 'uncertainty_increase'},
        {'step_count': 300, 'belief_inconsistencies': 2, 'trigger': 'belief_conflict'},
        {'step_count': 500, 'recent_performance': 0.85, 'trigger': 'periodic'},
    ]
    
    print("\n1. Testing reflection triggers...")
    for i, context in enumerate(contexts):
        should, trigger = engine.should_reflect(context)
        print(f"   Context {i+1}: step={context['step_count']}, trigger={trigger}, should={should}")
        
        # 手动触发测试
        trigger = context.get('trigger', 'manual')
        print(f"   -> Manually reflecting on {trigger}...")
        reflection = engine.reflect(focus=trigger.replace('_', ' '), context=context)
        print(f"      Reflection ID: {reflection.reflection_id}")
        print(f"      Duration: {reflection.duration_seconds:.4f}s")
        print(f"      Confidence: {reflection.confidence:.3f}")
        print(f"      Insights: {len(reflection.insights)}")
        for insight in reflection.insights[:2]:
            print(f"        - {insight}")
        print(f"      Conclusions: {len(reflection.conclusions)}")
        print(f"      Actions: {len(reflection.action_items)}")
    
    # 统计
    print("\n2. Reflection statistics:")
    stats = engine.get_stats()
    print(f"   Total reflections: {stats['reflection_count']}")
    print(f"   Reflections triggered: {stats['reflections_triggered']}")
    print(f"   Reflections completed: {stats['reflections_completed']}")
    print(f"   Insights generated: {stats['insights_generated']}")
    print(f"   Avg reflection duration: {stats['avg_reflection_duration']:.4f}s")
    
    if stats['reflection_count'] > 0:
        print(f"   Avg confidence: {stats['reflection_stats']['avg_confidence']:.3f}")
        print(f"   Total insights: {stats['reflection_stats']['total_insights']}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)