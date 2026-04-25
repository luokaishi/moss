"""
Self Model V2 - 条件自我模型

关键改进：
- 输入从 state → (state, drives)
- 解决非平稳策略预测问题
- 预期准确率：40~60%
"""

import numpy as np
from typing import Dict, List, Optional
from collections import deque


class SelfModelV2:
    """
    条件自我模型 V2
    
    核心改进：
    M_self: (state, drives) → action
    
    而非原来的：
    M_self: state → action
    
    这解决了非平稳策略的预测问题。
    """
    
    def __init__(self, state_dim: int, action_dim: int, drive_dim: int = 4):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.drive_dim = drive_dim
        
        # 条件模型：state + drives → action
        input_dim = state_dim + drive_dim
        self.W = np.random.randn(input_dim, action_dim) * 0.1
        self.lr = 0.01
        
        # 历史
        self.experience_buffer: deque = deque(maxlen=1000)
        
        # 性能
        self.policy_accuracy = 0.5
        self.correct_predictions = 0
        self.total_predictions = 0
    
    def _encode_drives(self, drives: Dict) -> np.ndarray:
        """
        编码驱动状态
        
        简化表示：
        - 驱动数量
        - 平均权重
        - 权重方差（多样性）
        """
        if not drives:
            return np.zeros(self.drive_dim)
        
        weights = []
        for d in drives.values():
            if hasattr(d, 'weight'):
                weights.append(d.weight)
            elif isinstance(d, dict) and 'weight' in d:
                weights.append(d['weight'])
            else:
                weights.append(0.25)
        
        n_drives = len(weights)
        mean_weight = np.mean(weights) if weights else 0.0
        std_weight = np.std(weights) if len(weights) > 1 else 0.0
        max_weight = np.max(weights) if weights else 0.0
        
        # 扩展到 drive_dim
        drive_vec = np.array([n_drives, mean_weight, std_weight, max_weight])
        
        # 如果维度不匹配，填充或截断
        if len(drive_vec) < self.drive_dim:
            drive_vec = np.pad(drive_vec, (0, self.drive_dim - len(drive_vec)))
        elif len(drive_vec) > self.drive_dim:
            drive_vec = drive_vec[:self.drive_dim]
        
        return drive_vec
    
    def predict(self, state: np.ndarray, drives: Dict) -> np.ndarray:
        """
        预测行动
        
        Args:
            state: 当前状态
            drives: 当前驱动状态
            
        Returns:
            行动分布 (action_dim,)
        """
        state = self._normalize_state(state)
        drive_vec = self._encode_drives(drives)
        
        # 拼接状态和驱动
        x = np.concatenate([state, drive_vec])
        
        # 预测
        logits = x @ self.W
        return self._softmax(logits)
    
    def update(self, state: np.ndarray, drives: Dict, action: int):
        """
        根据实际观察更新模型
        
        Args:
            state: 状态
            drives: 驱动状态
            action: 实际采取的行动（整数索引）
        """
        state = self._normalize_state(state)
        drive_vec = self._encode_drives(drives)
        
        # 拼接
        x = np.concatenate([state, drive_vec])
        
        # 前向预测
        predicted = self.predict(state, drives)
        
        # 更新准确率统计
        pred_action = np.argmax(predicted)
        if pred_action == action:
            self.correct_predictions += 1
        self.total_predictions += 1
        self.policy_accuracy = self.correct_predictions / max(1, self.total_predictions)
        
        # 梯度下降更新
        # 目标：增加实际动作的预测概率
        target = np.zeros(self.action_dim)
        target[action] = 1.0
        
        # 梯度
        grad = np.outer(x, predicted - target)
        
        # 更新权重
        self.W -= self.lr * grad
        
        # 存储经验
        self.experience_buffer.append({
            'state': state.copy(),
            'drives': drive_vec.copy(),
            'action': action
        })
    
    def evaluate_novelty(self, state: np.ndarray, drives: Dict, 
                         actual_action: int) -> float:
        """
        评估行动的新颖性
        
        Returns:
            新颖性分数 (0-1)
        """
        predicted = self.predict(state, drives)
        pred_action = np.argmax(predicted)
        confidence = predicted[pred_action]
        
        # 如果预测错误且置信度高，说明行为新颖
        if pred_action != actual_action and confidence > 0.6:
            return 0.8
        elif pred_action != actual_action:
            return 0.4
        else:
            return 0.1
    
    def get_self_awareness_score(self) -> float:
        """获取自我意识分数"""
        # 基于预测准确率，但做平滑
        return float(np.clip(self.policy_accuracy, 0, 1))
    
    def _normalize_state(self, state: np.ndarray) -> np.ndarray:
        """归一化状态"""
        if len(state) < self.state_dim:
            state = np.pad(state, (0, self.state_dim - len(state)))
        elif len(state) > self.state_dim:
            state = state[:self.state_dim]
        
        # L2归一化
        norm = np.linalg.norm(state)
        if norm > 0:
            state = state / norm
        return state
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """数值稳定的softmax"""
        x = x - np.max(x)
        exp_x = np.exp(x)
        return exp_x / (np.sum(exp_x) + 1e-8)
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            'state_dim': self.state_dim,
            'action_dim': self.action_dim,
            'drive_dim': self.drive_dim,
            'policy_accuracy': float(self.policy_accuracy),
            'total_predictions': self.total_predictions,
            'correct_predictions': self.correct_predictions,
            'self_awareness_score': self.get_self_awareness_score(),
            'experience_buffer_size': len(self.experience_buffer)
        }
