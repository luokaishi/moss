"""
ConceptSystem - 概念系统主控

整合编码器和预测器，实现概念的涌现、稳定和分化
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from .concept_encoder import ConceptEncoder
from .predictor import Predictor


class ConceptSystem:
    """
    概念系统
    
    核心功能：
    1. 状态→概念的编码
    2. 概念→下一状态的预测
    3. 基于预测误差优化概念
    4. 概念分裂（认知分化）
    
    这是认知层的核心：让系统从逐状态反应升级为基于抽象的决策
    """
    
    def __init__(self, state_dim: int, initial_concepts: int = 4):
        """
        Args:
            state_dim: 状态空间维度
            initial_concepts: 初始概念数量
        """
        self.state_dim = state_dim
        self.concept_dim = initial_concepts
        
        # 核心组件
        self.encoder = ConceptEncoder(state_dim, initial_concepts)
        self.predictor = Predictor(initial_concepts, state_dim)
        
        # 概念→行为的映射（用于泛化）
        self.concept_behavior_map: Dict[int, Dict[str, float]] = {}
        
        # 统计
        self.step_count = 0
        self.split_count = 0
        
    def step(self, state: np.ndarray, next_state: np.ndarray, 
             action: Optional[str] = None) -> Tuple[np.ndarray, float, dict]:
        """
        概念系统的主循环步骤
        
        Args:
            state: 当前状态
            next_state: 下一状态
            action: 执行的动作（可选，用于学习概念-行为映射）
            
        Returns:
            (concept, error, info)
        """
        # 1. 编码当前状态为概念
        concept = self.encoder.encode(state)
        
        # 2. 更新预测模型
        error = self.predictor.update(concept, next_state)
        
        # 3. 用预测误差反向塑造概念
        # 如果预测误差高，强化概念的区分度
        target = concept.copy()
        if error > 0.5:
            # 高误差：强化主导概念，抑制其他
            target = concept * 1.2
            target = target / (np.sum(target) + 1e-8)
        else:
            # 低误差：轻微抑制，保持多样性
            target = concept * 0.95
            target = target / (np.sum(target) + 1e-8)
        
        self.encoder.update(state, target)
        
        # 4. 更新概念-行为映射
        if action:
            self._update_concept_behavior_mapping(concept, action)
        
        # 5. 检查是否需要概念分裂
        should_split, split_id = self.predictor.should_trigger_split()
        if should_split and self.concept_dim < 16:
            self._trigger_concept_split(split_id)
        
        self.step_count += 1
        
        info = {
            'concept_id': int(np.argmax(concept)),
            'concept_confidence': float(np.max(concept)),
            'prediction_error': error,
            'concept_stability': self.encoder.get_concept_stability(),
            'prediction_quality': self.predictor.get_prediction_quality()
        }
        
        return concept, error, info
    
    def get_concept_for_state(self, state: np.ndarray) -> Tuple[int, float]:
        """获取状态对应的概念ID和置信度"""
        return self.encoder.get_dominant_concept(state)
    
    def get_behavior_for_concept(self, concept_id: int) -> Optional[str]:
        """
        获取概念推荐的行为（用于泛化）
        
        当遇到新状态时，如果其概念已知，则使用历史最优行为
        """
        if concept_id not in self.concept_behavior_map:
            return None
        
        behaviors = self.concept_behavior_map[concept_id]
        if not behaviors:
            return None
        
        # 返回得分最高的行为
        return max(behaviors.items(), key=lambda x: x[1])[0]
    
    def _update_concept_behavior_mapping(self, concept: np.ndarray, action: str):
        """更新概念-行为映射"""
        concept_id = int(np.argmax(concept))
        confidence = float(np.max(concept))
        
        if concept_id not in self.concept_behavior_map:
            self.concept_behavior_map[concept_id] = {}
        
        # 使用指数移动平均更新行为得分
        if action not in self.concept_behavior_map[concept_id]:
            self.concept_behavior_map[concept_id][action] = 0.0
        
        old_score = self.concept_behavior_map[concept_id][action]
        self.concept_behavior_map[concept_id][action] = 0.9 * old_score + 0.1 * confidence
    
    def _trigger_concept_split(self, concept_id: int):
        """触发概念分裂"""
        self.encoder.split_concept(concept_id)
        self.concept_dim += 1
        self.predictor.adapt_to_new_concept_dim(self.concept_dim)
        self.split_count += 1
    
    def get_generalization_suggestion(self, state: np.ndarray) -> Optional[str]:
        """
        获取泛化建议
        
        基于概念系统，对新状态推荐行为
        """
        concept_id, confidence = self.get_concept_for_state(state)
        
        # 只有高置信度时才使用泛化
        if confidence < 0.6:
            return None
        
        return self.get_behavior_for_concept(concept_id)
    
    def get_stats(self) -> dict:
        """获取概念系统统计信息"""
        return {
            'state_dim': self.state_dim,
            'concept_dim': self.concept_dim,
            'step_count': self.step_count,
            'split_count': self.split_count,
            'encoder': self.encoder.get_stats(),
            'predictor': self.predictor.get_stats(),
            'learned_concept_behavior_pairs': sum(len(v) for v in self.concept_behavior_map.values())
        }
