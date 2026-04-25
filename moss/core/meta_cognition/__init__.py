"""
MOSS v7.4 - Meta-Cognitive System
元认知系统

集成组件:
- BeliefSystem (信念系统)
- UncertaintyTracker (不确定性追踪)
- ReflectionEngine (反思引擎)

Author: MOSS Project
Date: 2026-04-19
"""

from .belief_system import BeliefSystem, Belief
from .uncertainty_tracker import UncertaintyTracker, UncertaintyMeasurement
from .reflection_engine import ReflectionEngine, Reflection

__all__ = [
    'MetaCognition',
    'BeliefSystem',
    'Belief',
    'UncertaintyTracker',
    'UncertaintyMeasurement',
    'ReflectionEngine',
    'Reflection'
]

import numpy as np
from typing import Dict, List, Optional
from datetime import datetime


class MetaCognition:
    """
    元认知系统
    
    集成信念系统、不确定性追踪和反思引擎
    """
    
    def __init__(self, enable_reflection: bool = True):
        """
        Args:
            enable_reflection: 是否启用反思
        """
        # 子系统
        self.belief_system = BeliefSystem()
        self.uncertainty_tracker = UncertaintyTracker()
        self.reflection_engine = ReflectionEngine() if enable_reflection else None
        
        # 状态
        self.step_count = 0
        self.enable_reflection = enable_reflection
        
        # 统计
        self.stats = {
            'total_steps': 0,
            'reflections_triggered': 0,
            'beliefs_updated': 0,
            'uncertainties_measured': 0
        }
    
    def step(self, context: Dict) -> Dict:
        """
        元认知步骤
        
        Args:
            context: 上下文信息
            
        Returns:
            步骤结果
        """
        self.step_count += 1
        self.stats['total_steps'] += 1
        
        result = {
            'step': self.step_count,
            'reflection_triggered': False,
            'reflection': None,
            'beliefs': [],
            'uncertainties': []
        }
        
        # 1. 更新信念
        if 'beliefs' in context:
            for belief_data in context['beliefs']:
                self.belief_system.add_belief(
                    belief_data['subject'],
                    belief_data['predicate'],
                    belief_data['confidence'],
                    belief_data.get('evidence')
                )
                result['beliefs'].append(f"{belief_data['subject']}:{belief_data['predicate']}")
                self.stats['beliefs_updated'] += 1
        
        # 2. 度量不确定性
        if 'uncertainties' in context:
            for unc_data in context['uncertainties']:
                self.uncertainty_tracker.measure_uncertainty(
                    unc_data['source'],
                    unc_data['value'],
                    unc_data.get('type', 'epistemic'),
                    unc_data.get('confidence', 0.8),
                    unc_data.get('context', {})
                )
                result['uncertainties'].append(unc_data['source'])
                self.stats['uncertainties_measured'] += 1
        
        # 3. 检查反思
        if self.reflection_engine and self.enable_reflection:
            should_reflect, trigger = self.reflection_engine.should_reflect(context)
            
            if should_reflect:
                reflection = self.reflection_engine.reflect(
                    focus=trigger.replace('_', ' '),
                    context=context
                )
                result['reflection_triggered'] = True
                result['reflection'] = reflection
                self.stats['reflections_triggered'] += 1
        
        return result
    
    def get_meta_cognitive_state(self) -> Dict:
        """获取元认知状态"""
        state = {
            'step_count': self.step_count,
            'belief_stats': self.belief_system.get_stats(),
            'uncertainty_stats': self.uncertainty_tracker.get_stats(),
            'meta_cognitive_stats': self.stats
        }
        
        if self.reflection_engine:
            state['reflection_stats'] = self.reflection_engine.get_stats()
        
        return state
    
    def get_self_model(self) -> Dict:
        """获取自我模型"""
        self_beliefs = self.belief_system.get_self_beliefs()
        capabilities = self.belief_system.get_capability_beliefs()
        
        return {
            'beliefs_about_self': [b.to_dict() for b in self_beliefs],
            'capabilities': [b.to_dict() for b in capabilities],
            'confidence_in_self': self.belief_system.get_confidence_distribution(),
            'total_self_beliefs': len(self_beliefs)
        }
    
    def get_uncertainty_summary(self) -> Dict:
        """获取不确定性摘要"""
        return {
            'total_uncertainty': self.uncertainty_tracker.get_total_uncertainty(),
            'distribution': self.uncertainty_tracker.get_uncertainty_distribution(),
            'high_uncertainty_areas': self.uncertainty_tracker.identify_high_uncertainty_areas(),
            'breakdown': self.uncertainty_tracker.get_uncertainty_breakdown()
        }
    
    def get_recent_reflections(self, n: int = 5) -> List[Dict]:
        """获取最近的反思"""
        if not self.reflection_engine:
            return []
        
        reflections = self.reflection_engine.get_recent_reflections(n)
        return [r.to_dict() for r in reflections]
    
    def export_state(self) -> Dict:
        """导出完整状态"""
        return {
            'timestamp': datetime.now().isoformat(),
            'step_count': self.step_count,
            'beliefs': self.belief_system.export_beliefs(),
            'uncertainties': list(self.uncertainty_tracker.measurements.values()),
            'reflections': [r.to_dict() for r in self.reflection_engine.reflections] if self.reflection_engine else [],
            'stats': self.stats
        }


# 测试
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v7.4 - Meta-Cognitive System Test")
    print("=" * 60)
    
    # 创建元认知系统
    mc = MetaCognition(enable_reflection=True)
    
    # 模拟多个步骤
    print("\n1. Running meta-cognitive steps...")
    
    contexts = [
        {
            'step_count': 1,
            'beliefs': [
                {'subject': 'self', 'predicate': 'can_learn', 'confidence': 0.8},
                {'subject': 'self', 'predicate': 'can_adapt', 'confidence': 0.7}
            ],
            'uncertainties': [
                {'source': 'perception', 'value': 0.3, 'type': 'aleatoric'},
                {'source': 'decision', 'value': 0.5, 'type': 'epistemic'}
            ],
            'recent_performance': 0.6,
            'baseline': 0.7
        },
        {
            'step_count': 2,
            'beliefs': [
                {'subject': 'self', 'predicate': 'can_learn', 'confidence': 0.85}
            ],
            'uncertainties': [
                {'source': 'perception', 'value': 0.25}
            ],
            'recent_performance': 0.5,
            'baseline': 0.7
        },
        {
            'step_count': 3,
            'uncertainties': [
                {'source': 'prediction', 'value': 0.7, 'type': 'epistemic'}
            ],
            'belief_inconsistencies': 1
        }
    ]
    
    for i, context in enumerate(contexts):
        print(f"\n   Step {i+1}:")
        result = mc.step(context)
        print(f"     Beliefs updated: {len(result['beliefs'])}")
        print(f"     Uncertainties measured: {len(result['uncertainties'])}")
        if result['reflection_triggered']:
            print(f"     Reflection triggered: {result['reflection'].reflection_id}")
    
    # 获取状态
    print("\n2. Meta-cognitive state:")
    state = mc.get_meta_cognitive_state()
    print(f"   Total steps: {state['step_count']}")
    print(f"   Total beliefs: {state['belief_stats']['total_beliefs']}")
    print(f"   Total uncertainties: {state['uncertainty_stats']['total_sources']}")
    print(f"   Reflections triggered: {state['meta_cognitive_stats']['reflections_triggered']}")
    
    # 自我模型
    print("\n3. Self model:")
    self_model = mc.get_self_model()
    print(f"   Self beliefs: {self_model['total_self_beliefs']}")
    print(f"   Mean confidence: {self_model['confidence_in_self']['mean']:.3f}")
    
    # 不确定性摘要
    print("\n4. Uncertainty summary:")
    unc_summary = mc.get_uncertainty_summary()
    print(f"   Total uncertainty: {unc_summary['total_uncertainty']:.3f}")
    print(f"   High uncertainty areas: {len(unc_summary['high_uncertainty_areas'])}")
    
    # 最近的反思
    if mc.reflection_engine:
        print("\n5. Recent reflections:")
        reflections = mc.get_recent_reflections(3)
        for r in reflections:
            print(f"   - {r['reflection_id']}: {r['focus']} (confidence: {r['confidence']:.3f})")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)