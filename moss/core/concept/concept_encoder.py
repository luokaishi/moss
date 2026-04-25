"""
ConceptEncoder - 概念编码器

将高维状态空间压缩为低维概念空间
"""

import numpy as np
from typing import List, Tuple, Optional


class ConceptEncoder:
    """
    概念编码器
    
    将状态向量编码为概念分布（软聚类）
    使用可学习的线性变换 + softmax
    """
    
    def __init__(self, state_dim: int, concept_dim: int = 4, lr: float = 0.01):
        """
        Args:
            state_dim: 状态空间维度
            concept_dim: 概念空间维度（概念数量）
            lr: 学习率
        """
        self.state_dim = state_dim
        self.concept_dim = concept_dim
        self.lr = lr
        
        # 可学习的投影矩阵
        self.W = np.random.randn(state_dim, concept_dim) * 0.1
        
        # 概念历史（用于稳定性分析）
        self.concept_history: List[np.ndarray] = []
        self.max_history = 1000
        
    def encode(self, state: np.ndarray) -> np.ndarray:
        """
        将状态编码为概念分布
        
        Args:
            state: 状态向量 (state_dim,)
            
        Returns:
            概念分布 (concept_dim,) - softmax 输出，和为1
        """
        if state.shape != (self.state_dim,):
            state = state.reshape(-1)[:self.state_dim]
            if len(state) < self.state_dim:
                state = np.pad(state, (0, self.state_dim - len(state)))
        
        # 线性投影
        z = state @ self.W
        
        # Softmax 得到概念分布
        concept_dist = self._softmax(z)
        
        # 记录历史
        self.concept_history.append(concept_dist.copy())
        if len(self.concept_history) > self.max_history:
            self.concept_history = self.concept_history[-self.max_history:]
        
        return concept_dist
    
    def update(self, state: np.ndarray, target: np.ndarray):
        """
        根据预测误差更新编码器参数
        
        Args:
            state: 当前状态
            target: 目标概念分布（来自预测误差反向传播）
        """
        # 前向
        z = state @ self.W
        concept = self._softmax(z)
        
        # 梯度：softmax cross-entropy
        grad_z = concept - target
        
        # 更新权重
        self.W -= self.lr * np.outer(state, grad_z)
    
    def get_concept_stability(self) -> float:
        """
        计算概念稳定性
        
        Returns:
            稳定性分数 (0-1)，越高表示概念越稳定
        """
        if len(self.concept_history) < 20:
            return 0.5
        
        recent = np.array(self.concept_history[-20:])
        # 计算概念分布的方差
        mean_dist = np.mean(recent, axis=0)
        variance = np.mean([np.sum((c - mean_dist) ** 2) for c in recent])
        
        # 转换为稳定性（方差越小越稳定）
        stability = np.exp(-variance * 10)
        return float(np.clip(stability, 0, 1))
    
    def get_dominant_concept(self, state: np.ndarray) -> Tuple[int, float]:
        """
        获取主导概念及其置信度
        
        Returns:
            (concept_id, confidence)
        """
        concept_dist = self.encode(state)
        concept_id = int(np.argmax(concept_dist))
        confidence = float(concept_dist[concept_id])
        return concept_id, confidence
    
    def split_concept(self, concept_id: int):
        """
        概念分裂 - 当一个概念的预测失败时，细化概念
        
        这对应于认知分化：一个模糊概念分裂为两个更精确的概念
        """
        if self.concept_dim >= 16:  # 最大概念数限制
            return
        
        # 增加概念维度
        new_W = np.random.randn(self.state_dim, self.concept_dim + 1) * 0.1
        new_W[:, :self.concept_dim] = self.W
        
        # 将原概念分裂为两个相似但不同的概念
        new_W[:, concept_id] = self.W[:, concept_id] * 0.9
        new_W[:, self.concept_dim] = self.W[:, concept_id] * 1.1
        
        self.W = new_W
        self.concept_dim += 1
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """数值稳定的 softmax"""
        x = x - np.max(x)
        exp_x = np.exp(x)
        return exp_x / (np.sum(exp_x) + 1e-8)
    
    def get_stats(self) -> dict:
        """获取编码器统计信息"""
        return {
            'state_dim': self.state_dim,
            'concept_dim': self.concept_dim,
            'history_size': len(self.concept_history),
            'stability': self.get_concept_stability(),
            'weight_norm': float(np.linalg.norm(self.W))
        }
