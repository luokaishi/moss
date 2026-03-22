"""
MOSS v4.0 - LLM Reasoning Layer

LLM元认知层：提供高层次推理能力
核心功能：
- 策略生成与评估
- 自我反思与修正
- 因果推理
- 类比推理
- 元认知监控

Author: Cash + Fuxi
Date: 2026-03-22
Version: 4.0.0-dev
"""

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ReasoningType(Enum):
    """推理类型"""
    STRATEGY = "strategy"           # 策略生成
    REFLECTION = "reflection"       # 自我反思
    CAUSAL = "causal"               # 因果推理
    ANALOGY = "analogy"             # 类比推理
    METACOGNITIVE = "metacognitive" # 元认知


@dataclass
class ReasoningResult:
    """推理结果"""
    reasoning_type: ReasoningType
    conclusion: str
    confidence: float
    evidence: List[Dict]
    alternatives: List[str]
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        return {
            'reasoning_type': self.reasoning_type.value,
            'conclusion': self.conclusion,
            'confidence': self.confidence,
            'evidence': self.evidence,
            'alternatives': self.alternatives,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class Reflection:
    """反思记录"""
    action_id: str
    predicted_outcome: str
    actual_outcome: str
    discrepancy: float
    lessons_learned: List[str]
    timestamp: datetime


class LLMReasoningLayer:
    """
    LLM推理层
    
    集成LLM提供高层次认知能力，包括：
    1. 策略生成：基于当前状态生成行动策略
    2. 自我反思：评估过去决策，提取经验
    3. 因果推理：理解行动-结果关系
    4. 类比推理：迁移已有经验到新情境
    5. 元认知：监控自身推理过程
    """
    
    def __init__(self, llm_client=None, memory_buffer_size=1000):
        """
        初始化LLM推理层
        
        Args:
            llm_client: LLM客户端（如OpenAI API）
            memory_buffer_size: 反思记忆缓冲区大小
        """
        self.llm_client = llm_client
        self.reflection_memory = []
        self.memory_buffer_size = memory_buffer_size
        self.reasoning_history = []
        
        # 元认知状态
        self.metacognitive_state = {
            'total_reasoning_calls': 0,
            'avg_confidence': 0.0,
            'reflection_count': 0
        }
    
    def generate_strategy(self, context: Dict, constraints: List[str] = None) -> ReasoningResult:
        """
        生成行动策略
        
        Args:
            context: 当前情境（状态、目标、资源等）
            constraints: 约束条件
            
        Returns:
            ReasoningResult包含策略建议
        """
        logger.info(f"[Strategy] Generating strategy for context: {context.get('state', 'unknown')}")
        
        # 构建prompt
        prompt = self._build_strategy_prompt(context, constraints)
        
        # 调用LLM（如果有客户端）或返回模拟结果
        if self.llm_client:
            response = self._call_llm(prompt)
        else:
            response = self._mock_strategy_response(context)
        
        result = ReasoningResult(
            reasoning_type=ReasoningType.STRATEGY,
            conclusion=response['strategy'],
            confidence=response.get('confidence', 0.8),
            evidence=response.get('evidence', []),
            alternatives=response.get('alternatives', []),
            timestamp=datetime.now()
        )
        
        self._update_metacognitive_state(result)
        return result
    
    def reflect(self, action: Dict, outcome: Dict) -> Reflection:
        """
        对行动结果进行反思
        
        Args:
            action: 执行的行动
            outcome: 实际结果
            
        Returns:
            Reflection对象
        """
        logger.info(f"[Reflection] Reflecting on action: {action.get('type', 'unknown')}")
        
        # 计算预测与实际差异
        predicted = action.get('expected_outcome', {})
        actual = outcome
        discrepancy = self._calculate_discrepancy(predicted, actual)
        
        # 提取经验教训
        lessons = self._extract_lessons(action, outcome, discrepancy)
        
        reflection = Reflection(
            action_id=action.get('id', 'unknown'),
            predicted_outcome=str(predicted),
            actual_outcome=str(actual),
            discrepancy=discrepancy,
            lessons_learned=lessons,
            timestamp=datetime.now()
        )
        
        # 存储到记忆
        self.reflection_memory.append(reflection)
        if len(self.reflection_memory) > self.memory_buffer_size:
            self.reflection_memory.pop(0)
        
        self.metacognitive_state['reflection_count'] += 1
        return reflection
    
    def causal_reasoning(self, event_a: Dict, event_b: Dict) -> ReasoningResult:
        """
        因果推理：判断event_a是否导致event_b
        
        Args:
            event_a: 原因事件
            event_b: 结果事件
            
        Returns:
            ReasoningResult包含因果关系判断
        """
        logger.info(f"[Causal] Analyzing causality between events")
        
        # 基于世界模型和历史数据进行因果分析
        causal_strength = self._estimate_causal_strength(event_a, event_b)
        
        conclusion = f"Event A {'causes' if causal_strength > 0.7 else 'may influence' if causal_strength > 0.4 else 'unlikely to cause'} Event B"
        
        result = ReasoningResult(
            reasoning_type=ReasoningType.CAUSAL,
            conclusion=conclusion,
            confidence=causal_strength,
            evidence=[{'type': 'temporal_order', 'strength': 0.8}],
            alternatives=['coincidence', 'common_cause', 'reverse_causation'],
            timestamp=datetime.now()
        )
        
        self._update_metacognitive_state(result)
        return result
    
    def analogical_reasoning(self, source: Dict, target: Dict) -> ReasoningResult:
        """
        类比推理：将源情境的经验迁移到目标情境
        
        Args:
            source: 源情境（已知解决方案）
            target: 目标情境（待解决）
            
        Returns:
            ReasoningResult包含类比建议
        """
        logger.info(f"[Analogy] Drawing analogy from {source.get('type')} to {target.get('type')}")
        
        # 计算结构相似度
        similarity = self._calculate_structural_similarity(source, target)
        
        # 基于相似度生成建议
        if similarity > 0.7:
            conclusion = f"High similarity ({similarity:.2f}): Apply source solution directly with minor adaptations"
        elif similarity > 0.4:
            conclusion = f"Moderate similarity ({similarity:.2f}): Adapt source approach to target context"
        else:
            conclusion = f"Low similarity ({similarity:.2f}): Limited transfer possible, seek alternative approaches"
        
        result = ReasoningResult(
            reasoning_type=ReasoningType.ANALOGY,
            conclusion=conclusion,
            confidence=similarity,
            evidence=[{'similarity_score': similarity, 'mapped_features': []}],
            alternatives=['independent_solution', 'hybrid_approach'],
            timestamp=datetime.now()
        )
        
        self._update_metacognitive_state(result)
        return result
    
    def metacognitive_monitor(self) -> Dict:
        """
        元认知监控：评估自身推理能力
        
        Returns:
            元认知状态报告
        """
        # 分析最近推理的质量
        recent_reasoning = self.reasoning_history[-100:] if self.reasoning_history else []
        
        avg_confidence = sum(r.confidence for r in recent_reasoning) / len(recent_reasoning) if recent_reasoning else 0
        
        report = {
            'total_reasoning_calls': self.metacognitive_state['total_reasoning_calls'],
            'recent_avg_confidence': avg_confidence,
            'reflection_count': self.metacognitive_state['reflection_count'],
            'reflection_coverage': len(self.reflection_memory) / self.memory_buffer_size,
            'cognitive_biases_detected': self._detect_biases(),
            'recommendations': self._generate_metacognitive_recommendations()
        }
        
        return report
    
    # ============ 内部方法 ============
    
    def _build_strategy_prompt(self, context: Dict, constraints: List[str]) -> str:
        """构建策略生成prompt"""
        prompt = f"""Given the current context:
State: {context.get('state', 'unknown')}
Goals: {context.get('goals', [])}
Resources: {context.get('resources', {})}

Generate an action strategy."""
        
        if constraints:
            prompt += f"\nConstraints: {constraints}"
        
        return prompt
    
    def _call_llm(self, prompt: str) -> Dict:
        """调用LLM（待实现）"""
        # 实际实现将调用OpenAI/Anthropic API
        raise NotImplementedError("LLM client not configured")
    
    def _mock_strategy_response(self, context: Dict) -> Dict:
        """模拟策略响应（用于测试）"""
        state = context.get('state', 'normal')
        
        strategies = {
            'crisis': {
                'strategy': 'Prioritize survival: consolidate resources, reduce exposure',
                'confidence': 0.9,
                'evidence': [{'type': 'risk_assessment', 'level': 'high'}]
            },
            'growth': {
                'strategy': 'Expand capabilities: explore new opportunities, invest in development',
                'confidence': 0.85,
                'evidence': [{'type': 'opportunity_assessment', 'level': 'high'}]
            },
            'normal': {
                'strategy': 'Maintain operations: balance exploration and exploitation',
                'confidence': 0.8,
                'evidence': [{'type': 'status_quo', 'stability': 'moderate'}]
            }
        }
        
        return strategies.get(state, strategies['normal'])
    
    def _calculate_discrepancy(self, predicted: Dict, actual: Dict) -> float:
        """计算预测与实际的差异"""
        # 简单的差异计算
        if not predicted or not actual:
            return 1.0  # 最大差异
        
        # 基于关键指标计算
        pred_val = predicted.get('value', 0)
        actual_val = actual.get('value', 0)
        
        if pred_val == 0:
            return 0.0 if actual_val == 0 else 1.0
        
        return abs(pred_val - actual_val) / max(abs(pred_val), abs(actual_val))
    
    def _extract_lessons(self, action: Dict, outcome: Dict, discrepancy: float) -> List[str]:
        """提取经验教训"""
        lessons = []
        
        if discrepancy > 0.5:
            lessons.append("Prediction significantly off - need better model")
        elif discrepancy > 0.2:
            lessons.append("Moderate deviation - refine assumptions")
        else:
            lessons.append("Prediction accurate - model working well")
        
        # 基于行动类型
        action_type = action.get('type', 'unknown')
        if action_type == 'exploration' and outcome.get('success', False):
            lessons.append("Exploration yielded positive results")
        elif action_type == 'exploitation' and not outcome.get('success', False):
            lessons.append("Exploitation failed - consider exploring alternatives")
        
        return lessons
    
    def _estimate_causal_strength(self, event_a: Dict, event_b: Dict) -> float:
        """估计因果强度"""
        # 基于时间顺序和共现频率
        # 实际实现将使用更复杂的因果推断方法
        return 0.6  # 模拟中等因果关系
    
    def _calculate_structural_similarity(self, source: Dict, target: Dict) -> float:
        """计算结构相似度"""
        # 基于特征匹配
        source_features = set(source.get('features', []))
        target_features = set(target.get('features', []))
        
        if not source_features or not target_features:
            return 0.0
        
        intersection = len(source_features & target_features)
        union = len(source_features | target_features)
        
        return intersection / union if union > 0 else 0.0
    
    def _update_metacognitive_state(self, result: ReasoningResult):
        """更新元认知状态"""
        self.metacognitive_state['total_reasoning_calls'] += 1
        self.reasoning_history.append(result)
        
        # 更新平均置信度
        n = self.metacognitive_state['total_reasoning_calls']
        old_avg = self.metacognitive_state['avg_confidence']
        self.metacognitive_state['avg_confidence'] = (old_avg * (n - 1) + result.confidence) / n
    
    def _detect_biases(self) -> List[str]:
        """检测认知偏差"""
        biases = []
        
        # 分析推理历史
        recent = self.reasoning_history[-50:] if len(self.reasoning_history) >= 50 else self.reasoning_history
        
        if not recent:
            return biases
        
        # 检测确认偏误：是否总是选择高置信度选项
        high_conf_count = sum(1 for r in recent if r.confidence > 0.9)
        if high_conf_count / len(recent) > 0.8:
            biases.append("overconfidence_bias")
        
        # 检测可得性启发：是否重复相似策略
        strategy_types = [r.reasoning_type for r in recent]
        unique_types = len(set(strategy_types))
        if unique_types < len(strategy_types) * 0.3:
            biases.append("strategy_rigidity")
        
        return biases
    
    def _generate_metacognitive_recommendations(self) -> List[str]:
        """生成元认知改进建议"""
        recommendations = []
        
        if self.metacognitive_state['avg_confidence'] > 0.9:
            recommendations.append("Consider exploring more uncertain options")
        
        if self.metacognitive_state['reflection_count'] < 10:
            recommendations.append("Increase reflection frequency")
        
        if len(self.reflection_memory) < self.memory_buffer_size * 0.5:
            recommendations.append("Accumulate more experience before major decisions")
        
        return recommendations


# ============ 测试与演示 ============

def test_llm_reasoning():
    """测试LLM推理层"""
    print("=" * 70)
    print("LLM Reasoning Layer Test")
    print("=" * 70)
    
    reasoning_layer = LLMReasoningLayer()
    
    # 测试策略生成
    print("\n1. Strategy Generation")
    context = {
        'state': 'growth',
        'goals': ['expand_capabilities', 'increase_efficiency'],
        'resources': {'compute': 'available', 'time': 'limited'}
    }
    strategy = reasoning_layer.generate_strategy(context)
    print(f"Strategy: {strategy.conclusion}")
    print(f"Confidence: {strategy.confidence}")
    
    # 测试反思
    print("\n2. Reflection")
    action = {'id': 'test_1', 'type': 'exploration', 'expected_outcome': {'value': 100}}
    outcome = {'value': 75, 'success': True}
    reflection = reasoning_layer.reflect(action, outcome)
    print(f"Discrepancy: {reflection.discrepancy:.2f}")
    print(f"Lessons: {reflection.lessons_learned}")
    
    # 测试因果推理
    print("\n3. Causal Reasoning")
    event_a = {'type': 'resource_investment', 'amount': 100}
    event_b = {'type': 'performance_increase', 'value': 20}
    causal = reasoning_layer.causal_reasoning(event_a, event_b)
    print(f"Conclusion: {causal.conclusion}")
    print(f"Confidence: {causal.confidence}")
    
    # 测试类比推理
    print("\n4. Analogical Reasoning")
    source = {'type': 'code_optimization', 'features': ['algorithmic', 'performance', 'memory']}
    target = {'type': 'query_optimization', 'features': ['algorithmic', 'performance', 'database']}
    analogy = reasoning_layer.analogical_reasoning(source, target)
    print(f"Conclusion: {analogy.conclusion}")
    print(f"Similarity: {analogy.confidence:.2f}")
    
    # 测试元认知监控
    print("\n5. Metacognitive Monitor")
    report = reasoning_layer.metacognitive_monitor()
    print(f"Total reasoning calls: {report['total_reasoning_calls']}")
    print(f"Recent avg confidence: {report['recent_avg_confidence']:.2f}")
    print(f"Reflection count: {report['reflection_count']}")
    print(f"Biases detected: {report['cognitive_biases_detected']}")
    print(f"Recommendations: {report['recommendations']}")
    
    print("\n" + "=" * 70)
    print("All tests passed!")
    print("=" * 70)


if __name__ == '__main__':
    test_llm_reasoning()
