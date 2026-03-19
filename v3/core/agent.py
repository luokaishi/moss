"""
MOSS v3.0.0 - Core Agent with Dimensions 5 & 6
===============================================

集成Coherence（第5维）和Valence（第6维）的MOSS Agent

Author: Cash
Date: 2026-03-19
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

try:
    from .coherence import CoherenceModule, IdentityAttractor
    from .valence import ValenceModule, PersonalityClassifier
except ImportError:
    from coherence import CoherenceModule, IdentityAttractor
    from valence import ValenceModule, PersonalityClassifier


@dataclass
class MOSSv3State:
    """MOSS v3.0 Agent状态"""
    # 基础4维目标值
    survival: float
    curiosity: float
    influence: float
    optimization: float
    
    # 扩展维度
    coherence: float = 0.0      # 第5维
    valence: float = 0.0        # 第6维
    
    # 当前权重
    weights: np.ndarray = None
    
    # 状态标签
    state_label: str = "normal"
    
    def to_vector(self) -> np.ndarray:
        """转换为向量 [S, C, I, O, V_coh, V_val]"""
        return np.array([
            self.survival,
            self.curiosity,
            self.influence,
            self.optimization,
            self.coherence,
            self.valence
        ])


class MOSSv3Agent:
    """
    MOSS v3.0 Agent
    
    支持4-6维目标：
    - D1-D4: Survival, Curiosity, Influence, Optimization
    - D5 (可选): Coherence（自我连续性）
    - D6 (可选): Valence（主观偏好）
    """
    
    def __init__(self,
                 agent_id: str,
                 enable_coherence: bool = True,
                 enable_valence: bool = True,
                 coherence_alpha: float = 0.9,
                 valence_gamma: float = 0.01,
                 initial_weights: Optional[np.ndarray] = None):
        """
        初始化MOSS v3.0 Agent
        
        Args:
            agent_id: Agent唯一标识
            enable_coherence: 是否启用第5维
            enable_valence: 是否启用第6维
            coherence_alpha: Coherence EMA系数
            valence_gamma: Valence学习率
            initial_weights: 初始权重 [w_S, w_C, w_I, w_O]
        """
        self.agent_id = agent_id
        self.enable_coherence = enable_coherence
        self.enable_valence = enable_valence
        
        # 基础4维权重
        if initial_weights is not None:
            self.weights = initial_weights.copy()
        else:
            self.weights = np.array([0.25, 0.25, 0.25, 0.25])
        
        # 初始化扩展模块
        if enable_coherence:
            self.coherence_module = CoherenceModule(alpha=coherence_alpha)
            self.coherence_module.initialize_reference(self.weights)
            self.identity_attractor = IdentityAttractor()
        else:
            self.coherence_module = None
            self.identity_attractor = None
        
        if enable_valence:
            self.valence_module = ValenceModule(
                n_objectives=4,
                gamma=valence_gamma
            )
        else:
            self.valence_module = None
        
        # 历史记录
        self.history: List[MOSSv3State] = []
        self.weight_history: List[np.ndarray] = []
        
        # 当前状态
        self.current_M = np.array([0.5, 0.5, 0.5, 0.5])  # 初始目标值
        self.step_count = 0
        
    def compute_objectives(self) -> np.ndarray:
        """
        计算当前4维目标值
        
        这里使用简化的模拟，实际应根据环境计算
        """
        # 基于当前权重和step_count模拟目标值变化
        noise = np.random.randn(4) * 0.05
        
        # 权重高的维度倾向于有更高的值
        base = self.weights * 0.8 + 0.1
        
        self.current_M = np.clip(base + noise, 0, 1)
        return self.current_M
    
    def compute_extended_objectives(self, M_base: np.ndarray) -> Tuple[float, float]:
        """
        计算扩展维度目标值
        
        Args:
            M_base: 基础4维目标值
            
        Returns:
            (coherence, valence)
        """
        coherence = 0.0
        valence = 0.0
        
        # 第5维：Coherence
        if self.enable_coherence and self.coherence_module:
            coherence = self.coherence_module.compute_coherence_reward(self.weights)
            self.coherence_module.update_reference(self.weights)
            if self.identity_attractor:
                self.identity_attractor.add_point(self.weights)
        
        # 第6维：Valence
        if self.enable_valence and self.valence_module:
            valence = self.valence_module.compute_valence(M_base)
        
        return coherence, valence
    
    def update_weights(self, state_label: str):
        """
        更新权重（简化版本）
        
        实际应根据状态和扩展目标动态调整
        """
        # 模拟权重微调
        noise = np.random.randn(4) * 0.02
        self.weights = np.clip(self.weights + noise, 0.1, 0.6)
        self.weights = self.weights / np.sum(self.weights)  # 归一化
        
        self.weight_history.append(self.weights.copy())
    
    def step(self) -> Dict:
        """
        执行一步决策循环
        
        Returns:
            包含当前状态的字典
        """
        self.step_count += 1
        
        # 1. 计算基础目标值
        M_base = self.compute_objectives()
        
        # 2. 计算扩展目标值
        coherence, valence = self.compute_extended_objectives(M_base)
        
        # 3. 确定状态标签（简化）
        state_label = self._determine_state(M_base)
        
        # 4. 更新权重
        self.update_weights(state_label)
        
        # 5. 构建状态对象
        state = MOSSv3State(
            survival=M_base[0],
            curiosity=M_base[1],
            influence=M_base[2],
            optimization=M_base[3],
            coherence=coherence,
            valence=valence,
            weights=self.weights.copy(),
            state_label=state_label
        )
        
        self.history.append(state)
        
        return {
            'step': self.step_count,
            'agent_id': self.agent_id,
            'M_base': M_base,
            'coherence': coherence,
            'valence': valence,
            'weights': self.weights.copy(),
            'state': state_label
        }
    
    def _determine_state(self, M: np.ndarray) -> str:
        """根据目标值确定状态标签"""
        if M[0] < 0.2:  # survival低
            return "crisis"
        elif M[0] < 0.4:
            return "concerned"
        elif np.mean(M) > 0.6:
            return "growth"
        else:
            return "normal"
    
    def get_personality(self) -> Optional[Dict]:
        """
        获取人格分析（需要启用valence模块）
        """
        if not self.enable_valence or not self.valence_module:
            return None
        
        beta = self.valence_module.beta
        history = self.valence_module.valence_history
        
        p_type = PersonalityClassifier.classify(beta, history)
        p_desc = PersonalityClassifier.get_personality_description(p_type)
        
        return {
            'type': p_type,
            'description': p_desc['description'],
            'traits': p_desc['traits'],
            'preference_profile': self.valence_module.get_preference_profile(),
            'behavioral_bias': self.valence_module.get_behavioral_bias()
        }
    
    def get_identity_analysis(self) -> Optional[Dict]:
        """
        获取身份分析（需要启用coherence模块）
        """
        if not self.enable_coherence or not self.coherence_module:
            return None
        
        analysis = {
            'coherence_summary': self.coherence_module.get_state_summary(),
            'identity_stability': self.coherence_module.get_identity_stability()
        }
        
        if self.identity_attractor:
            analysis['attractor'] = self.identity_attractor.get_attractor_properties()
        
        return analysis
    
    def get_report(self) -> Dict:
        """生成完整报告"""
        report = {
            'agent_id': self.agent_id,
            'config': {
                'enable_coherence': self.enable_coherence,
                'enable_valence': self.enable_valence
            },
            'steps': self.step_count,
            'personality': self.get_personality(),
            'identity': self.get_identity_analysis(),
            'final_weights': self.weights.copy()
        }
        
        return report


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("MOSS v3.0 Agent Test")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 创建v3 agent（启用5-6维）
    agent = MOSSv3Agent(
        agent_id="test_v3",
        enable_coherence=True,
        enable_valence=True,
        coherence_alpha=0.9,
        valence_gamma=0.02
    )
    
    print(f"\nAgent config:")
    print(f"  Coherence: {agent.enable_coherence}")
    print(f"  Valence: {agent.enable_valence}")
    print(f"  Initial weights: {agent.weights}")
    
    # 运行100步
    print(f"\nRunning 100 steps...")
    for i in range(100):
        result = agent.step()
        
        if i % 20 == 0:
            print(f"\nStep {i}:")
            print(f"  M: [{result['M_base'][0]:.3f}, {result['M_base'][1]:.3f}, "
                  f"{result['M_base'][2]:.3f}, {result['M_base'][3]:.3f}]")
            print(f"  Coherence: {result['coherence']:.6f}")
            print(f"  Valence: {result['valence']:.4f}")
            print(f"  Weights: [{result['weights'][0]:.3f}, {result['weights'][1]:.3f}, "
                  f"{result['weights'][2]:.3f}, {result['weights'][3]:.3f}]")
    
    # 生成报告
    print("\n" + "=" * 60)
    print("Final Report")
    print("=" * 60)
    
    report = agent.get_report()
    
    # 人格分析
    if report['personality']:
        print(f"\n🎭 Personality Analysis:")
        print(f"  Type: {report['personality']['type']}")
        print(f"  Description: {report['personality']['description']}")
        print(f"  Traits: {', '.join(report['personality']['traits'])}")
        
        profile = report['personality']['preference_profile']
        print(f"  Dominant preference: {profile['dominant_preference']} "
              f"({profile['dominant_weight']:.3f})")
        
        bias = report['personality']['behavioral_bias']
        if 'loss_aversion' in bias:
            print(f"  Loss aversion: {bias['loss_aversion']:.2f}")
    
    # 身份分析
    if report['identity']:
        print(f"\n🆔 Identity Analysis:")
        stability = report['identity']['identity_stability']
        print(f"  Identity stability: {stability:.6f}")
        
        if report['identity'].get('attractor'):
            attractor = report['identity']['attractor']
            print(f"  Converged: {attractor['converged']}")
    
    print(f"\n✓ MOSS v3.0 test completed!")
    print("=" * 60)
