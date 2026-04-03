"""
OEF 2.0 + MOSS Dynamic Weight Update
动态权重更新 - MOSS 数学定义集成

数学定义:
w(t+1) = w(t) + η · (w*(s) - w(t))

状态依赖权重映射:
- Crisis: w* = [0.6, 0.1, 0.2, 0.1]
- Concerned: w* = [0.35, 0.35, 0.2, 0.1]
- Normal: w* = [0.2, 0.4, 0.3, 0.1]
- Growth: w* = [0.2, 0.2, 0.4, 0.2]

来源: MOSS 项目主分支 moss_mathematical_framework.py
"""

import numpy as np
from typing import Dict, Tuple


class DynamicWeightUpdate:
    """
    MOSS 动态权重更新
    
    数学定义:
    w(t+1) = w(t) + η · (w*(s) - w(t))
    
    收敛条件: 0 < η < 2/λ_max(H)
    """
    
    def __init__(self, learning_rate: float = 0.05):
        self.learning_rate = learning_rate
        
        # 状态依赖权重映射
        self.state_weight_map = {
            'crisis': np.array([0.60, 0.10, 0.20, 0.10]),
            'concerned': np.array([0.35, 0.35, 0.20, 0.10]),
            'normal': np.array([0.20, 0.40, 0.30, 0.10]),
            'growth': np.array([0.20, 0.20, 0.40, 0.20])
        }
        
        self.weight_history: list = []
    
    def detect_state(self, state: np.ndarray) -> str:
        """检测系统状态"""
        resource = state[0] if len(state) > 0 else 0.5
        
        if resource < 0.2:
            return 'crisis'
        elif resource < 0.5:
            return 'concerned'
        elif resource < 0.8:
            return 'normal'
        else:
            return 'growth'
    
    def get_target_weights(self, state: np.ndarray) -> np.ndarray:
        """获取目标权重 w*(s)"""
        state_name = self.detect_state(state)
        return self.state_weight_map[state_name]
    
    def update_weights(self, current_weights: np.ndarray,
                       state: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """
        动态权重更新
        
        w(t+1) = w(t) + η · (w*(s) - w(t))
        """
        target = self.get_target_weights(state)
        eta = self.learning_rate
        
        delta = target - current_weights
        new_weights = current_weights + eta * delta
        
        # 投影到可行域
        new_weights = self.project_to_feasible(new_weights)
        
        self.weight_history.append(new_weights.copy())
        
        info = {
            'state': self.detect_state(state),
            'target_weights': target,
            'delta': delta,
            'change_norm': np.linalg.norm(new_weights - current_weights)
        }
        
        return new_weights, info
    
    def project_to_feasible(self, weights: np.ndarray) -> np.ndarray:
        """
        投影到可行域
        
        W = {w ∈ ℝ⁴ | wᵢ ≥ ε, Σwᵢ = 1}
        """
        epsilon = 0.01
        projected = np.maximum(weights, epsilon)
        projected = projected / np.sum(projected)
        return projected
    
    def check_convergence(self, window_size: int = 10) -> Dict:
        """检查收敛性"""
        if len(self.weight_history) < window_size:
            return {'converged': False, 'reason': 'insufficient_data'}
        
        recent = self.weight_history[-window_size:]
        
        changes = [np.linalg.norm(recent[i] - recent[i-1])
                   for i in range(1, len(recent))]
        
        avg_change = np.mean(changes)
        variance = np.var([w[0] for w in recent])
        
        converged = avg_change < 0.01 and variance < 0.001
        
        return {
            'converged': converged,
            'average_change': avg_change,
            'variance': variance,
            'iterations': len(self.weight_history)
        }


if __name__ == '__main__':
    print("✅ MOSS DynamicWeightUpdate 模块加载成功")
    
    updater = DynamicWeightUpdate()
    weights = np.array([0.6, 0.1, 0.2, 0.1])
    state = np.array([0.6])  # Normal
    
    new_weights, info = updater.update_weights(weights, state)
    print(f"状态: {info['state']}")
    print(f"更新后权重: {new_weights}")