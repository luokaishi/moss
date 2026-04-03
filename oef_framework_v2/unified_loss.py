"""
OEF 2.0 + MOSS Unified Loss Function
统一损失函数 - MOSS 数学定义集成

数学定义:
L_MOSS(s, a, t) = Σᵢ wᵢ(t) · fᵢ(s, a)

来源: MOSS 项目主分支 moss_mathematical_framework.py
"""

import numpy as np
from typing import List, Callable, Dict


class UnifiedLossFunction:
    """
    MOSS 统一损失函数
    
    数学定义:
    L_MOSS(s, a, t) = Σᵢ₌₁⁴ wᵢ(t) · fᵢ(s, a)
    
    目标函数:
    1. f₁ (Survival): f₁(s) = resource_quota · (1 - error_rate)
    2. f₂ (Curiosity): f₂(s, a) = information_gain(s, a)
    3. f₃ (Influence): f₃(s, a) = impact_measure(s, a)
    4. f₄ (Optimization): f₄(s) = performance_improvement_rate(s)
    """
    
    def __init__(self, n_objectives: int = 4):
        self.n = n_objectives
        self.objective_names = ['survival', 'curiosity', 'influence', 'optimization']
    
    def compute_loss(self, state: np.ndarray, action: np.ndarray,
                     weights: np.ndarray, objectives: List[Callable]) -> float:
        """
        计算统一损失
        
        L_MOSS(s, a, t) = Σᵢ wᵢ(t) · fᵢ(s, a)
        """
        assert len(weights) == len(objectives), "权重和目标数量必须匹配"
        assert np.abs(np.sum(weights) - 1.0) < 1e-6, "权重和必须为1"
        
        total_loss = 0.0
        for w, f in zip(weights, objectives):
            total_loss += w * f(state, action)
        
        return total_loss
    
    def compute_survival(self, state: np.ndarray, action: np.ndarray) -> float:
        """
        f₁ (Survival): 生存评估函数
        
        数学定义: f₁(s) = resource_quota · (1 - error_rate)
        """
        resource_quota = state[0] if len(state) > 0 else 0.5
        error_rate = state[1] if len(state) > 1 else 0.02
        
        survival_score = resource_quota * (1.0 - min(error_rate, 1.0))
        return survival_score
    
    def compute_curiosity(self, state: np.ndarray, action: np.ndarray) -> float:
        """
        f₂ (Curiosity): 好奇评估函数
        
        数学定义: f₂(s, a) = information_gain(s, a)
        """
        explore_weight = action[0] if len(action) > 0 else 0.5
        curiosity_score = explore_weight * 0.6
        return curiosity_score
    
    def compute_influence(self, state: np.ndarray, action: np.ndarray) -> float:
        """
        f₃ (Influence): 影响力评估函数
        
        数学定义: f₃(s, a) = impact_measure(s, a)
        """
        socialize_weight = action[2] if len(action) > 2 else 0.3
        influence_score = socialize_weight * 0.5
        return influence_score
    
    def compute_optimization(self, state: np.ndarray, action: np.ndarray) -> float:
        """
        f₄ (Optimization): 优化评估函数
        
        数学定义: f₄(s) = performance_improvement_rate(s)
        """
        uptime = state[2] if len(state) > 2 else 100
        optimization_score = min(uptime / 200, 1.0) * 0.5
        return optimization_score
    
    def get_default_objectives(self) -> List[Callable]:
        """获取默认四目标函数"""
        return [
            self.compute_survival,
            self.compute_curiosity,
            self.compute_influence,
            self.compute_optimization
        ]
    
    def compute_loss_breakdown(self, state: np.ndarray, action: np.ndarray,
                               weights: np.ndarray) -> Dict:
        """计算损失分解"""
        objectives = self.get_default_objectives()
        
        breakdown = {}
        for i, (name, w, f) in enumerate(zip(self.objective_names, weights, objectives)):
            contribution = w * f(state, action)
            breakdown[name] = {
                'weight': w,
                'objective_value': f(state, action),
                'contribution': contribution
            }
        
        breakdown['total_loss'] = sum(b[name]['contribution'] for name in self.objective_names)
        return breakdown


if __name__ == '__main__':
    print("✅ MOSS UnifiedLossFunction 模块加载成功")
    
    loss_fn = UnifiedLossFunction()
    state = np.array([0.7, 0.02, 100])
    action = np.array([0.4, 0.3, 0.2, 0.1])
    weights = np.array([0.2, 0.4, 0.3, 0.1])
    
    objectives = loss_fn.get_default_objectives()
    loss = loss_fn.compute_loss(state, action, weights, objectives)
    
    print(f"统一损失: L_MOSS = {loss:.4f}")