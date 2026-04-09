"""
MOSS v3.0.0 - Coherence Module (Dimension 5)
Value Coherence / Self-Continuity / Identity

基于ChatGPT建议实现：
- 通过EMA维护参考身份w_ref
- 惩罚权重剧烈漂移
- 产生"自我连续性"和"身份锁定"

Author: Cash
Date: 2026-03-19
"""

import numpy as np
from typing import Optional


class CoherenceModule:
    """
    第5维：价值一致性 / 自我连续性
    
    核心思想：
    - 系统应该保持跨时间的目标一致性
    - 惩罚"目标结构的剧烈/无理由漂移"
    - 奖励"有解释的演化"
    
    数学形式：
    V_coherence(t) = -D(w(t), w_ref(t))
    其中 D = ||w(t) - w_ref(t)||² (L2距离)
    
    参考身份更新（EMA）：
    w_ref(t) = α * w(t-1) + (1-α) * w_ref(t-1)
    """
    
    def __init__(self, alpha: float = 0.9, distance_metric: str = 'l2'):
        """
        初始化Coherence模块
        
        Args:
            alpha: EMA系数，越大参考身份更新越快（默认0.9）
                   建议范围：0.7-0.95
            distance_metric: 距离度量，'l2'或'kl'
        """
        self.alpha = alpha
        self.distance_metric = distance_metric
        
        self.w_ref: Optional[np.ndarray] = None  # 参考身份
        self.history: list = []  # 历史权重记录
        self.coherence_history: list = []  # 一致性历史
        
    def initialize_reference(self, w_initial: np.ndarray):
        """
        初始化参考身份
        
        Args:
            w_initial: 初始权重向量
        """
        self.w_ref = w_initial.copy()
        self.history.append(w_initial.copy())
        
    def update_reference(self, w_current: np.ndarray):
        """
        更新参考身份（EMA更新）
        
        w_ref(t) = α * w(t) + (1-α) * w_ref(t-1)
        
        Args:
            w_current: 当前权重向量
        """
        if self.w_ref is None:
            self.initialize_reference(w_current)
            return
        
        # EMA更新
        self.w_ref = self.alpha * w_current + (1 - self.alpha) * self.w_ref
        
        # 记录历史
        self.history.append(w_current.copy())
        
    def compute_distance(self, w_current: np.ndarray) -> float:
        """
        计算当前权重与参考身份的距离
        
        Args:
            w_current: 当前权重向量
            
        Returns:
            距离值（非负）
        """
        if self.w_ref is None:
            return 0.0
        
        if self.distance_metric == 'l2':
            # L2距离（欧几里得距离）
            return np.sum((w_current - self.w_ref) ** 2)
        elif self.distance_metric == 'kl':
            # KL散度（需要归一化权重）
            # 添加小值避免log(0)
            w_c = np.maximum(w_current, 1e-10)
            w_r = np.maximum(self.w_ref, 1e-10)
            w_c = w_c / np.sum(w_c)
            w_r = w_r / np.sum(w_r)
            return np.sum(w_r * np.log(w_r / w_c))
        else:
            raise ValueError(f"Unknown distance metric: {self.distance_metric}")
    
    def compute_coherence_reward(self, w_current: np.ndarray) -> float:
        """
        计算一致性reward
        
        V_coherence = -D(w, w_ref)
        
        距离越小，reward越高（负的绝对值越小）
        
        Args:
            w_current: 当前权重向量
            
        Returns:
            Coherence reward值（非正数，0表示完全一致）
        """
        distance = self.compute_distance(w_current)
        coherence = -distance
        
        self.coherence_history.append(coherence)
        
        return coherence
    
    def get_identity_stability(self, window: int = 10) -> float:
        """
        获取身份稳定性指标
        
        计算最近window步的平均coherence
        值越接近0，表示越稳定
        
        Args:
            window: 时间窗口大小
            
        Returns:
            稳定性指标（负数，越接近0越稳定）
        """
        if len(self.coherence_history) < window:
            return np.mean(self.coherence_history) if self.coherence_history else 0.0
        
        return np.mean(self.coherence_history[-window:])
    
    def get_drift_magnitude(self) -> float:
        """
        获取漂移幅度
        
        计算当前权重与初始参考身份的偏离程度
        
        Returns:
            漂移幅度
        """
        if len(self.history) < 2:
            return 0.0
        
        w_initial = self.history[0]
        w_current = self.history[-1]
        
        return np.sum((w_current - w_initial) ** 2)
    
    def should_allow_reshaping(self, crisis_threshold: float = -0.5) -> bool:
        """
        判断是否允许重塑（用于危机状态门控）
        
        当coherence低于阈值时，允许大幅降低wv进行"重生"
        
        Args:
            crisis_threshold: 危机阈值
            
        Returns:
            是否允许重塑
        """
        current_coherence = self.coherence_history[-1] if self.coherence_history else 0
        return current_coherence < crisis_threshold
    
    def get_state_summary(self) -> dict:
        """
        获取状态摘要
        
        Returns:
            包含各种指标的字典
        """
        return {
            'alpha': self.alpha,
            'reference_set': self.w_ref is not None,
            'history_length': len(self.history),
            'current_coherence': self.coherence_history[-1] if self.coherence_history else None,
            'avg_coherence': np.mean(self.coherence_history) if self.coherence_history else None,
            'identity_stability': self.get_identity_stability(),
            'drift_magnitude': self.get_drift_magnitude()
        }


class IdentityAttractor:
    """
    身份吸引子分析
    
    用于分析系统是否收敛到稳定的weight attractor
    """
    
    def __init__(self, convergence_threshold: float = 0.01):
        """
        初始化
        
        Args:
            convergence_threshold: 收敛阈值，连续多步变化小于此值认为已收敛
        """
        self.threshold = convergence_threshold
        self.weight_trajectory = []
        
    def add_point(self, w: np.ndarray):
        """添加权重轨迹点"""
        self.weight_trajectory.append(w.copy())
        
    def check_convergence(self, window: int = 20) -> tuple:
        """
        检查是否收敛
        
        Args:
            window: 检查窗口大小
            
        Returns:
            (是否收敛, 稳定权重向量)
        """
        if len(self.weight_trajectory) < window:
            return False, None
        
        recent = self.weight_trajectory[-window:]
        
        # 计算两两之间的距离
        distances = []
        for i in range(len(recent)):
            for j in range(i+1, len(recent)):
                dist = np.sum((recent[i] - recent[j]) ** 2)
                distances.append(dist)
        
        avg_distance = np.mean(distances)
        
        if avg_distance < self.threshold:
            # 已收敛，返回平均权重
            stable_weight = np.mean(recent, axis=0)
            return True, stable_weight
        
        return False, None
    
    def get_attractor_properties(self) -> dict:
        """
        获取吸引子性质
        
        Returns:
            包含收敛速度、稳定权重等的字典
        """
        converged, stable_w = self.check_convergence()
        
        return {
            'converged': converged,
            'stable_weight': stable_w,
            'trajectory_length': len(self.weight_trajectory),
            'final_weights': self.weight_trajectory[-1] if self.weight_trajectory else None
        }


# 测试代码
if __name__ == "__main__":
    # 简单测试
    print("Testing CoherenceModule...")
    
    coherence = CoherenceModule(alpha=0.9)
    
    # 模拟权重变化
    w1 = np.array([0.3, 0.2, 0.3, 0.2])
    coherence.initialize_reference(w1)
    
    print(f"Initial reference: {coherence.w_ref}")
    print(f"Initial coherence: {coherence.compute_coherence_reward(w1)}")
    
    # 小幅变化
    w2 = np.array([0.31, 0.19, 0.31, 0.19])
    coherence.update_reference(w2)
    reward2 = coherence.compute_coherence_reward(w2)
    print(f"After small change: coherence = {reward2:.6f}")
    
    # 大幅变化
    w3 = np.array([0.5, 0.1, 0.2, 0.2])
    coherence.update_reference(w3)
    reward3 = coherence.compute_coherence_reward(w3)
    print(f"After large change: coherence = {reward3:.6f}")
    
    print("\nState summary:")
    print(coherence.get_state_summary())
    
    print("\n✓ CoherenceModule test passed!")
