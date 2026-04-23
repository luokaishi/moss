"""
Predictor - 概念预测模型

基于当前概念预测下一状态
用于评估概念的预测能力
"""

import numpy as np
from typing import List, Tuple


class Predictor:
    """
    概念预测模型
    
    学习 concept -> next_state 的映射
    预测误差用于：
    1. 评估概念的预测能力
    2. 反向塑造概念编码器
    3. 触发概念分裂（当误差持续高时）
    """
    
    def __init__(self, concept_dim: int, state_dim: int, lr: float = 0.01):
        """
        Args:
            concept_dim: 概念空间维度
            state_dim: 状态空间维度
            lr: 学习率
        """
        self.concept_dim = concept_dim
        self.state_dim = state_dim
        self.lr = lr
        
        # 概念→状态的投影矩阵
        self.W = np.random.randn(concept_dim, state_dim) * 0.1
        
        # 误差历史
        self.error_history: List[float] = []
        self.max_history = 500
        
    def predict(self, concept: np.ndarray) -> np.ndarray:
        """
        基于概念预测下一状态
        
        Args:
            concept: 概念分布 (concept_dim,)
            
        Returns:
            预测的下一状态 (state_dim,)
        """
        if concept.shape != (self.concept_dim,):
            # 维度不匹配时进行插值
            concept = self._resize_concept(concept)
        
        return concept @ self.W
    
    def update(self, concept: np.ndarray, actual_next_state: np.ndarray) -> float:
        """
        根据实际下一状态更新预测模型
        
        Args:
            concept: 当前概念
            actual_next_state: 实际的下一状态
            
        Returns:
            预测误差 (MSE)
        """
        if concept.shape != (self.concept_dim,):
            concept = self._resize_concept(concept)
        
        # 预测
        predicted = self.predict(concept)
        
        # 计算误差
        error = actual_next_state - predicted
        mse = float(np.mean(error ** 2))
        
        # 梯度下降更新
        grad = -2 * np.outer(concept, error) / len(error)
        self.W -= self.lr * grad
        
        # 记录误差
        self.error_history.append(mse)
        if len(self.error_history) > self.max_history:
            self.error_history = self.error_history[-self.max_history:]
        
        return mse
    
    def get_prediction_quality(self) -> float:
        """
        获取预测质量
        
        Returns:
            质量分数 (0-1)，基于最近预测误差
        """
        if len(self.error_history) < 10:
            return 0.5
        
        recent_error = np.mean(self.error_history[-20:])
        # 误差越小，质量越高
        quality = np.exp(-recent_error * 5)
        return float(np.clip(quality, 0, 1))
    
    def should_trigger_split(self) -> Tuple[bool, int]:
        """
        判断是否应该触发概念分裂
        
        Returns:
            (should_split, concept_id_to_split)
        """
        if len(self.error_history) < 50:
            return False, -1
        
        # 如果最近误差持续高，触发分裂
        recent_errors = self.error_history[-50:]
        if np.mean(recent_errors) > 0.5:
            # 找出误差最大的概念（简化：返回0）
            return True, 0
        
        return False, -1
    
    def _resize_concept(self, concept: np.ndarray) -> np.ndarray:
        """调整概念向量维度"""
        if len(concept) == self.concept_dim:
            return concept
        
        # 使用线性插值
        old_dim = len(concept)
        new_concept = np.zeros(self.concept_dim)
        for i in range(self.concept_dim):
            idx = i * (old_dim - 1) / (self.concept_dim - 1) if self.concept_dim > 1 else 0
            idx_low = int(np.floor(idx))
            idx_high = min(int(np.ceil(idx)), old_dim - 1)
            alpha = idx - idx_low
            new_concept[i] = concept[idx_low] * (1 - alpha) + concept[idx_high] * alpha
        
        return new_concept
    
    def adapt_to_new_concept_dim(self, new_dim: int):
        """适应新的概念维度（概念分裂后）"""
        if new_dim == self.concept_dim:
            return
        
        new_W = np.random.randn(new_dim, self.state_dim) * 0.1
        # 复制旧权重
        min_dim = min(self.concept_dim, new_dim)
        new_W[:min_dim, :] = self.W[:min_dim, :]
        
        self.W = new_W
        self.concept_dim = new_dim
    
    def get_stats(self) -> dict:
        """获取预测器统计信息"""
        return {
            'concept_dim': self.concept_dim,
            'state_dim': self.state_dim,
            'prediction_quality': self.get_prediction_quality(),
            'mean_error': float(np.mean(self.error_history[-50:])) if self.error_history else 0.0,
            'error_trend': 'decreasing' if len(self.error_history) >= 20 and 
                          np.mean(self.error_history[-20:]) < np.mean(self.error_history[-40:-20])
                          else 'stable/increasing'
        }
