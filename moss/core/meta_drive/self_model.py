"""
Self Model - 自我模型

Self-Model 是一个可被查询、预测、并用于决策的内部模型，
描述 agent 自身的结构与动态。

形式化：M_self: (s, d, θ) → (a, s', Δd)

与 World Model 的区别：
- World Model 预测环境
- Self Model 预测自己（策略+驱动+演化）
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import deque


class SelfModel:
    """
    自我模型
    
    学习预测：
    1. 给定状态下自己会采取什么行动
    2. 驱动会如何演化
    3. 策略参数会如何变化
    """
    
    def __init__(self, state_dim: int, action_dim: int, drive_dim: int = 4):
        """
        Args:
            state_dim: 状态维度
            action_dim: 动作空间维度（或动作embedding维度）
            drive_dim: 驱动空间维度
        """
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.drive_dim = drive_dim
        
        # 策略预测模型：state → action distribution
        self.policy_W = np.random.randn(state_dim, action_dim) * 0.1
        
        # 驱动演化模型：(state, current_drive) → next_drive
        self.drive_W = np.random.randn(state_dim + drive_dim, drive_dim) * 0.1
        
        # 学习率
        self.lr = 0.01
        
        # 历史记录
        self.experience_buffer: deque = deque(maxlen=1000)
        
        # 预测质量
        self.policy_accuracy = 0.5
        self.drive_accuracy = 0.5
    
    def predict_action(self, state: np.ndarray) -> np.ndarray:
        """
        预测自己会采取的行动
        
        Args:
            state: 当前状态
            
        Returns:
            动作分布 (action_dim,)
        """
        state = self._normalize_state(state)
        logits = state @ self.policy_W
        return self._softmax(logits)
    
    def predict_drive_evolution(self, state: np.ndarray, 
                                 current_drive: np.ndarray) -> np.ndarray:
        """
        预测驱动的演化
        
        Args:
            state: 当前状态
            current_drive: 当前驱动状态
            
        Returns:
            预测的下一驱动状态
        """
        state = self._normalize_state(state)
        
        # 确保维度匹配
        if len(current_drive) < self.drive_dim:
            current_drive = np.pad(current_drive, (0, self.drive_dim - len(current_drive)))
        elif len(current_drive) > self.drive_dim:
            current_drive = current_drive[:self.drive_dim]
        
        # 拼接状态和驱动
        combined = np.concatenate([state, current_drive])
        
        # 预测下一驱动
        next_drive = combined @ self.drive_W
        
        # 归一化
        return self._softmax(next_drive)
    
    def update(self, state: np.ndarray, 
               actual_action: Optional[np.ndarray] = None,
               actual_next_drive: Optional[np.ndarray] = None):
        """
        根据实际观察更新自我模型
        
        Args:
            state: 状态
            actual_action: 实际采取的动作（one-hot或分布）
            actual_next_drive: 实际的下一驱动状态
        """
        state = self._normalize_state(state)
        
        # 存储经验
        self.experience_buffer.append({
            'state': state.copy(),
            'action': actual_action.copy() if actual_action is not None else None,
            'next_drive': actual_next_drive.copy() if actual_next_drive is not None else None
        })
        
        # 更新策略预测模型
        if actual_action is not None:
            self._update_policy_model(state, actual_action)
        
        # 更新驱动演化模型
        if actual_next_drive is not None:
            # 需要当前驱动，从buffer获取
            if len(self.experience_buffer) >= 2:
                prev_exp = list(self.experience_buffer)[-2]
                current_drive = prev_exp.get('next_drive')
                if current_drive is not None:
                    self._update_drive_model(state, current_drive, actual_next_drive)
    
    def _update_policy_model(self, state: np.ndarray, actual_action: np.ndarray):
        """更新策略预测模型"""
        # 前向
        predicted = self.predict_action(state)
        
        # 确保维度匹配
        if len(actual_action) != self.action_dim:
            if len(actual_action) < self.action_dim:
                actual_action = np.pad(actual_action, (0, self.action_dim - len(actual_action)))
            else:
                actual_action = actual_action[:self.action_dim]
        
        # 梯度
        grad = predicted - actual_action
        
        # 更新
        self.policy_W -= self.lr * np.outer(state, grad)
        
        # 更新准确率
        pred_idx = np.argmax(predicted)
        actual_idx = np.argmax(actual_action)
        self.policy_accuracy = 0.95 * self.policy_accuracy + 0.05 * (1.0 if pred_idx == actual_idx else 0.0)
    
    def _update_drive_model(self, state: np.ndarray, 
                           current_drive: np.ndarray,
                           actual_next_drive: np.ndarray):
        """更新驱动演化模型"""
        # 确保维度
        if len(current_drive) < self.drive_dim:
            current_drive = np.pad(current_drive, (0, self.drive_dim - len(current_drive)))
        if len(actual_next_drive) < self.drive_dim:
            actual_next_drive = np.pad(actual_next_drive, (0, self.drive_dim - len(actual_next_drive)))
        
        # 前向
        combined = np.concatenate([state, current_drive])
        predicted = self.predict_drive_evolution(state, current_drive)
        
        # 梯度
        grad = predicted - actual_next_drive
        
        # 更新
        self.drive_W -= self.lr * np.outer(combined, grad)
        
        # 更新准确率
        self.drive_accuracy = 0.95 * self.drive_accuracy + 0.05 * (
            1.0 - np.mean(np.abs(predicted - actual_next_drive))
        )
    
    def evaluate_action_novelty(self, state: np.ndarray, 
                                 actual_action: np.ndarray) -> float:
        """
        评估行动的新颖性
        
        如果实际行为与自我模型预测差异大，说明是新颖/探索性行为
        
        Returns:
            新颖性分数 (0-1)
        """
        predicted = self.predict_action(state)
        
        # 确保维度匹配
        if len(actual_action) != len(predicted):
            min_len = min(len(actual_action), len(predicted))
            actual_action = actual_action[:min_len]
            predicted = predicted[:min_len]
            # 归一化
            actual_action = actual_action / (np.sum(actual_action) + 1e-8)
            predicted = predicted / (np.sum(predicted) + 1e-8)
        
        # KL散度作为差异度量
        kl = np.sum(actual_action * np.log((actual_action + 1e-8) / (predicted + 1e-8)))
        novelty = 1.0 - np.exp(-kl)
        
        return float(np.clip(novelty, 0, 1))
    
    def get_self_awareness_score(self) -> float:
        """
        获取自我意识分数
        
        基于自我模型的预测准确率
        """
        return (self.policy_accuracy + self.drive_accuracy) / 2
    
    def _normalize_state(self, state: np.ndarray) -> np.ndarray:
        """归一化状态向量"""
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
        """获取自我模型统计"""
        return {
            'state_dim': self.state_dim,
            'action_dim': self.action_dim,
            'drive_dim': self.drive_dim,
            'policy_accuracy': float(self.policy_accuracy),
            'drive_accuracy': float(self.drive_accuracy),
            'self_awareness_score': self.get_self_awareness_score(),
            'experience_buffer_size': len(self.experience_buffer)
        }
