"""
MOSS v7.4 - Meta-Cognition + Meta-SME Integration
元认知与 Meta-SME 集成

实现元认知驱动的自我修改

Author: MOSS Project
Date: 2026-04-19
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from meta_cognition import MetaCognition
from meta_sme_v2 import OptimizedMetaSME, ModificationType
from typing import Dict, List, Optional
import numpy as np


class MetaCognitiveMetaSME:
    """
    元认知驱动的 Meta-SME
    
    使用元认知系统指导自我修改
    """
    
    def __init__(self):
        # 元认知系统
        self.meta_cognition = MetaCognition(enable_reflection=True)
        
        # Meta-SME (优化版)
        self.meta_sme = OptimizedMetaSME(
            enable_auto_modify=True,
            require_human_approval=False,
            cooldown_period=500,
            use_optimization=True
        )
        
        # 集成统计
        self.integration_stats = {
            'meta_cognitive_guided_modifications': 0,
            'reflection_based_changes': 0,
            'uncertainty_driven_exploration': 0
        }
    
    def step(self, state: Dict, performance: float) -> Dict:
        """
        集成步骤
        
        Args:
            state: 当前状态
            performance: 性能指标
            
        Returns:
            步骤结果
        """
        result = {
            'meta_cognitive_update': None,
            'modification_proposed': False,
            'modification_applied': False
        }
        
        # 1. 元认知步骤
        meta_context = self._build_meta_context(state, performance)
        mc_result = self.meta_cognition.step(meta_context)
        result['meta_cognitive_update'] = mc_result
        
        # 2. 基于元认知的修改决策
        if self._should_modify_based_on_meta_cognition():
            proposal = self._generate_meta_cognitive_proposal()
            if proposal:
                result['modification_proposed'] = True
                self.integration_stats['meta_cognitive_guided_modifications'] += 1
        
        # 3. 记录性能到 Meta-SME
        self.meta_sme.record_performance(performance)
        
        # 4. 检查 Meta-SME 修改
        if self.meta_sme.should_generate_proposal():
            # 这里可以结合元认知信息生成更智能的提案
            pass
        
        return result
    
    def _build_meta_context(self, state: Dict, performance: float) -> Dict:
        """构建元认知上下文"""
        context = {
            'step_count': self.meta_cognition.step_count,
            'recent_performance': performance,
            'beliefs': [],
            'uncertainties': []
        }
        
        # 添加性能相关信念
        if performance < 0.5:
            context['beliefs'].append({
                'subject': 'self',
                'predicate': 'performance_low',
                'confidence': 1.0 - performance
            })
        elif performance > 0.8:
            context['beliefs'].append({
                'subject': 'self',
                'predicate': 'performance_high',
                'confidence': performance
            })
        
        # 添加不确定性
        context['uncertainties'].append({
            'source': 'performance_prediction',
            'value': 1.0 - abs(performance - 0.5) * 2,
            'type': 'epistemic'
        })
        
        return context
    
    def _should_modify_based_on_meta_cognition(self) -> bool:
        """基于元认知判断是否应该修改"""
        # 获取高不确定性区域
        high_uncertainty = self.meta_cognition.uncertainty_tracker.identify_high_uncertainty_areas(
            threshold=0.6
        )
        
        # 如果有高不确定性，考虑修改
        if len(high_uncertainty) > 0:
            return True
        
        # 检查信念一致性
        inconsistencies = self.meta_cognition.belief_system.check_consistency()
        if len(inconsistencies) > 0:
            return True
        
        return False
    
    def _generate_meta_cognitive_proposal(self) -> Optional[Dict]:
        """生成基于元认知的修改提案"""
        # 基于高不确定性区域生成提案
        high_uncertainty = self.meta_cognition.uncertainty_tracker.identify_high_uncertainty_areas(
            threshold=0.6
        )
        
        if high_uncertainty:
            target = high_uncertainty[0]['source']
            return {
                'target': target,
                'reason': f'High uncertainty in {target}',
                'type': 'uncertainty_reduction'
            }
        
        # 基于信念冲突生成提案
        inconsistencies = self.meta_cognition.belief_system.check_consistency()
        if inconsistencies:
            return {
                'target': 'belief_system',
                'reason': 'Belief inconsistencies detected',
                'type': 'belief_reconciliation'
            }
        
        return None
    
    def get_meta_cognitive_state(self) -> Dict:
        """获取元认知状态"""
        return {
            'meta_cognition': self.meta_cognition.get_meta_cognitive_state(),
            'meta_sme': self.meta_sme.get_status(),
            'integration_stats': self.integration_stats
        }
    
    def get_self_awareness_report(self) -> Dict:
        """获取自我意识报告"""
        self_model = self.meta_cognition.get_self_model()
        uncertainty_summary = self.meta_cognition.get_uncertainty_summary()
        
        return {
            'self_model': self_model,
            'uncertainty_summary': uncertainty_summary,
            'awareness_level': self._calculate_awareness_level(),
            'recommendations': self._generate_recommendations()
        }
    
    def _calculate_awareness_level(self) -> float:
        """计算自我意识水平"""
        # 基于信念数量和不确定性计算
        belief_count = self.meta_cognition.belief_system.get_stats()['total_beliefs']
        uncertainty_mean = self.meta_cognition.uncertainty_tracker.get_total_uncertainty()
        
        # 更多信念且适当的不确定性表示更高的自我意识
        belief_score = min(belief_count / 10, 1.0)  # 最多 10 个信念得满分
        uncertainty_score = 1.0 - abs(uncertainty_mean - 0.5) * 2  # 0.5 附近最佳
        
        return (belief_score + uncertainty_score) / 2
    
    def _generate_recommendations(self) -> List[str]:
        """生成建议"""
        recommendations = []
        
        # 基于高不确定性
        high_unc = self.meta_cognition.uncertainty_tracker.identify_high_uncertainty_areas(0.7)
        if high_unc:
            recommendations.append(f"Reduce uncertainty in: {high_unc[0]['source']}")
        
        # 基于低置信度信念
        low_conf = self.meta_cognition.belief_system.get_low_confidence_beliefs(0.3)
        if low_conf:
            recommendations.append(f"Gather more evidence for: {low_conf[0].predicate}")
        
        # 基于信念冲突
        inconsistencies = self.meta_cognition.belief_system.check_consistency()
        if inconsistencies:
            recommendations.append("Resolve belief inconsistencies")
        
        return recommendations


# 测试
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v7.4 - Meta-Cognitive Meta-SME Integration Test")
    print("=" * 60)
    
    # 创建集成系统
    mc_meta_sme = MetaCognitiveMetaSME()
    
    # 模拟运行
    print("\n1. Running integrated steps...")
    
    performances = [0.6, 0.5, 0.4, 0.7, 0.8, 0.3, 0.6, 0.9]
    
    for i, perf in enumerate(performances):
        print(f"\n   Step {i+1}: performance={perf:.2f}")
        
        result = mc_meta_sme.step(
            state={'step': i, 'value': perf},
            performance=perf
        )
        
        print(f"     Beliefs updated: {len(result['meta_cognitive_update']['beliefs'])}")
        print(f"     Uncertainties: {len(result['meta_cognitive_update']['uncertainties'])}")
        print(f"     Modification proposed: {result['modification_proposed']}")
    
    # 自我意识报告
    print("\n2. Self-awareness report:")
    report = mc_meta_sme.get_self_awareness_report()
    print(f"   Awareness level: {report['awareness_level']:.3f}")
    print(f"   Self beliefs: {report['self_model']['total_self_beliefs']}")
    print(f"   Recommendations: {len(report['recommendations'])}")
    for rec in report['recommendations'][:3]:
        print(f"     - {rec}")
    
    # 集成统计
    print("\n3. Integration stats:")
    print(f"   Meta-cognitive guided modifications: {mc_meta_sme.integration_stats['meta_cognitive_guided_modifications']}")
    print(f"   Total beliefs: {mc_meta_sme.meta_cognition.belief_system.get_stats()['total_beliefs']}")
    print(f"   Total uncertainties: {mc_meta_sme.meta_cognition.uncertainty_tracker.get_stats()['total_sources']}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)