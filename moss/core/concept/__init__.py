"""
Concept System - 概念系统 (第7层)

概念 = 对状态空间的压缩划分，使得系统在该划分下具有更高预测能力或决策稳定性

核心组件：
- ConceptEncoder: 状态→概念的编码器
- Predictor: 概念→下一状态的预测模型
- ConceptSystem: 概念系统主控
"""

from .concept_encoder import ConceptEncoder
from .predictor import Predictor
from .concept_system import ConceptSystem

__all__ = ['ConceptEncoder', 'Predictor', 'ConceptSystem']
