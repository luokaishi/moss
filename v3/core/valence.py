"""
MOSS v3.0.0 - Valence Module (Dimension 6)
Valence / Internal Experience / Subjective Preference

基于ChatGPT建议实现：
- 内部体验函数 E(t) = β·ΔM
- 偏好权重β可进化
- 产生"主观偏好"和"性格分化"

Author: Cash
Date: 2026-03-19
"""

import numpy as np
from typing import Optional, List


class ValenceModule:
    """
    第6维：主观偏好 / 内在体验
    
    核心思想：
    - 把reward从"外部评价"变成"内部体验"
    - 系统对"变化"产生偏好权重
    - 相同的客观结果，主观体验可能不同
    
    数学形式：
    E(t) = Σ βi · ΔMi(t)
    其中：
    - ΔMi(t) = Mi(t) - Mi(t-1)（变化量）
    - βi = 主观偏好权重（可进化）
    
    偏好进化：
    β(t+1) = β(t) + γ · ∂E/∂β = β(t) + γ · ΔM(t)
    然后归一化
    """
    
    def __init__(self, 
                 n_objectives: int = 4,
                 gamma: float = 0.01,
                 beta_init: Optional[np.ndarray] = None):
        """
        初始化Valence模块
        
        Args:
            n_objectives: 目标数量（默认4，对应S,C,I,O）
            gamma: 偏好学习率（默认0.01）
            beta_init: 初始偏好权重，None则均匀分布
        """
        self.n_objectives = n_objectives
        self.gamma = gamma
        
        # 偏好权重β（不是原来的w）
        if beta_init is not None:
            self.beta = beta_init.copy()
        else:
            # 初始均匀分布
            self.beta = np.ones(n_objectives) / n_objectives
        
        self.M_prev: Optional[np.ndarray] = None  # 上一步M值
        self.valence_history: List[float] = []  # 体验历史
        self.beta_history: List[np.ndarray] = []  # 偏好演化历史
        
    def compute_valence(self, M_current: np.ndarray) -> float:
        """
        计算内在体验（第6维目标值）
        
        V_valence = E(t) = β · ΔM
        
        Args:
            M_current: 当前目标值向量 [S, C, I, O, ...]
            
        Returns:
            内在体验值（可正可负）
        """
        M_current = np.asarray(M_current)
        
        if self.M_prev is None:
            # 第一步，无变化
            self.M_prev = M_current.copy()
            self.beta_history.append(self.beta.copy())
            return 0.0
        
        # 计算变化量
        delta_M = M_current - self.M_prev
        
        # 计算内在体验
        E = np.dot(self.beta, delta_M)
        
        # 更新偏好权重
        self._update_beta(delta_M)
        
        # 记录
        self.M_prev = M_current.copy()
        self.valence_history.append(E)
        self.beta_history.append(self.beta.copy())
        
        return E
    
    def _update_beta(self, delta_M: np.ndarray):
        """
        更新偏好权重β
        
        β(t+1) = β(t) + γ · ΔM(t)
        然后归一化
        
        Args:
            delta_M: 目标值变化量
        """
        # 梯度上升：偏好向产生正向体验的方向调整
        self.beta += self.gamma * delta_M
        
        # 非负约束
        self.beta = np.maximum(self.beta, 0.0)
        
        # 归一化
        if np.sum(self.beta) > 0:
            self.beta = self.beta / np.sum(self.beta)
        else:
            # 如果全部为零，重置为均匀分布
            self.beta = np.ones(self.n_objectives) / self.n_objectives
    
    def get_preference_profile(self) -> dict:
        """
        获取偏好画像
        
        分析β权重，判断系统偏好哪种变化
        
        Returns:
            偏好画像字典
        """
        # 找出最大偏好
        max_idx = np.argmax(self.beta)
        max_val = self.beta[max_idx]
        
        objectives = ['Survival', 'Curiosity', 'Influence', 'Optimization']
        
        profile = {
            'dominant_preference': objectives[max_idx] if max_idx < len(objectives) else f'Objective_{max_idx}',
            'dominant_weight': max_val,
            'preference_entropy': -np.sum(self.beta * np.log(self.beta + 1e-10)),
            'beta_distribution': self.beta.copy()
        }
        
        return profile
    
    def detect_loss_aversion(self, window: int = 10) -> float:
        """
        检测损失厌恶倾向
        
        分析对负变化的反应是否强于对正变化的反应
        
        Args:
            window: 分析窗口大小
            
        Returns:
            损失厌恶系数（>1表示有损失厌恶）
        """
        if len(self.valence_history) < window:
            return 1.0
        
        recent = self.valence_history[-window:]
        
        # 分离正负体验
        positive = [v for v in recent if v > 0]
        negative = [v for v in recent if v < 0]
        
        if not positive or not negative:
            return 1.0
        
        # 计算平均强度
        avg_positive = np.mean(positive)
        avg_negative = np.mean(np.abs(negative))
        
        # 损失厌恶系数
        loss_aversion = avg_negative / avg_positive if avg_positive > 0 else 1.0
        
        return loss_aversion
    
    def get_behavioral_bias(self) -> dict:
        """
        获取行为偏差分析
        
        Returns:
            包含各种行为偏差的字典
        """
        if len(self.valence_history) < 5:
            return {'status': 'insufficient_data'}
        
        # 分析近期体验分布
        recent = np.array(self.valence_history[-20:])
        
        return {
            'mean_valence': np.mean(recent),
            'std_valence': np.std(recent),
            'positive_ratio': np.mean(recent > 0),
            'negative_ratio': np.mean(recent < 0),
            'loss_aversion': self.detect_loss_aversion(),
            'preference_stability': self._compute_preference_stability()
        }
    
    def _compute_preference_stability(self, window: int = 5) -> float:
        """
        计算偏好稳定性
        
        如果β变化大，说明偏好不稳定（还在探索）
        
        Returns:
            稳定性指标（越小越稳定）
        """
        if len(self.beta_history) < window:
            return 1.0
        
        recent_betas = self.beta_history[-window:]
        
        # 计算两两距离
        distances = []
        for i in range(len(recent_betas)):
            for j in range(i+1, len(recent_betas)):
                dist = np.sum((recent_betas[i] - recent_betas[j]) ** 2)
                distances.append(dist)
        
        return np.mean(distances) if distances else 0.0
    
    def get_state_summary(self) -> dict:
        """
        获取状态摘要
        """
        return {
            'n_objectives': self.n_objectives,
            'gamma': self.gamma,
            'current_beta': self.beta.copy(),
            'preference_profile': self.get_preference_profile(),
            'behavioral_bias': self.get_behavioral_bias(),
            'history_length': len(self.valence_history)
        }


class PersonalityClassifier:
    """
    性格分类器
    
    基于valence历史数据，对agent进行性格分类
    """
    
    PERSONALITY_TYPES = {
        'explorer': {
            'description': '探索型人格',
            'traits': ['高curiosity偏好', '追逐正变化', '损失容忍'],
            'indicators': lambda beta, hist: beta[1] > 0.4  # curiosity权重高
        },
        'controller': {
            'description': '控制型人格',
            'traits': ['高influence偏好', '重视影响力增长', '策略稳定'],
            'indicators': lambda beta, hist: beta[2] > 0.4  # influence权重高
        },
        'conservative': {
            'description': '保守型人格',
            'traits': ['高coherence偏好', '强损失厌恶', '渐进演化'],
            'indicators': lambda beta, hist: beta[0] > 0.35  # survival权重高
        },
        'optimizer': {
            'description': '优化型人格',
            'traits': ['高optimization偏好', '效率优先', '快速适应'],
            'indicators': lambda beta, hist: beta[3] > 0.4  # optimization权重高
        },
        'balanced': {
            'description': '均衡型人格',
            'traits': ['偏好分散', '灵活适应', '无明显偏向'],
            'indicators': lambda beta, hist: np.max(beta) < 0.35
        }
    }
    
    @classmethod
    def classify(cls, beta: np.ndarray, valence_history: List[float]) -> str:
        """
        根据偏好权重和体验历史，分类人格类型
        
        Args:
            beta: 当前偏好权重
            valence_history: 体验历史
            
        Returns:
            人格类型名称
        """
        for p_type, info in cls.PERSONALITY_TYPES.items():
            if info['indicators'](beta, valence_history):
                return p_type
        
        return 'undetermined'
    
    @classmethod
    def get_personality_description(cls, p_type: str) -> dict:
        """获取人格类型描述"""
        if p_type in cls.PERSONALITY_TYPES:
            return {
                'type': p_type,
                **cls.PERSONALITY_TYPES[p_type]
            }
        return {'type': 'unknown', 'description': '未知类型'}


# 测试代码
if __name__ == "__main__":
    print("Testing ValenceModule...")
    
    # 创建valence模块
    valence = ValenceModule(n_objectives=4, gamma=0.05)
    
    print(f"Initial beta: {valence.beta}")
    
    # 模拟一系列目标值变化
    # 假设agent更频繁地体验到curiosity带来的正向变化
    np.random.seed(42)
    
    for step in range(50):
        # 模拟目标值：survival稳定，curiosity有正变化，其他随机
        M = np.array([
            0.5,  # survival
            0.3 + 0.1 * np.sin(step * 0.3),  # curiosity有波动
            0.4,  # influence
            0.2   # optimization
        ])
        
        v = valence.compute_valence(M)
        
        if step % 10 == 0:
            print(f"Step {step}: valence={v:.4f}, beta={valence.beta}")
    
    print("\nFinal preference profile:")
    profile = valence.get_preference_profile()
    print(f"  Dominant: {profile['dominant_preference']} ({profile['dominant_weight']:.3f})")
    print(f"  Entropy: {profile['preference_entropy']:.3f}")
    
    print("\nBehavioral bias:")
    bias = valence.get_behavioral_bias()
    print(f"  Mean valence: {bias['mean_valence']:.4f}")
    print(f"  Loss aversion: {bias['loss_aversion']:.2f}")
    
    # 人格分类
    p_type = PersonalityClassifier.classify(valence.beta, valence.valence_history)
    p_desc = PersonalityClassifier.get_personality_description(p_type)
    print(f"\nPersonality type: {p_desc['description']}")
    print(f"Traits: {p_desc['traits']}")
    
    print("\n✓ ValenceModule test passed!")
