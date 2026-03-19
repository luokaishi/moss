"""
MOSS v3.0.0 - Full 8D Agent
===========================

完整8维MOSS Agent：
D1-D4: Survival, Curiosity, Influence, Optimization
D5: Coherence（自我连续性）
D6: Valence（主观偏好）
D7: Other（他者建模）
D8: Norm（规范内化）

Author: Cash
Date: 2026-03-19
"""

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass

try:
    from .coherence import CoherenceModule, IdentityAttractor
    from .valence import ValenceModule, PersonalityClassifier
    from .other import OtherModule
    from .norm import NormModule
except ImportError:
    from coherence import CoherenceModule, IdentityAttractor
    from valence import ValenceModule, PersonalityClassifier
    from other import OtherModule
    from norm import NormModule


@dataclass
class MOSSv3State8D:
    """MOSS v3.0 完整8维状态"""
    survival: float      # D1
    curiosity: float     # D2
    influence: float     # D3
    optimization: float  # D4
    coherence: float = 0.0     # D5
    valence: float = 0.0       # D6
    other: float = 0.0         # D7
    norm: float = 0.0          # D8
    
    weights: np.ndarray = None
    state_label: str = "normal"
    
    def to_vector(self) -> np.ndarray:
        """转换为8维向量"""
        return np.array([
            self.survival, self.curiosity, self.influence, self.optimization,
            self.coherence, self.valence, self.other, self.norm
        ])


class MOSSv3Agent8D:
    """
    MOSS v3.0 完整8维Agent
    
    实现从个体到社会的完整跃迁
    """
    
    def __init__(self,
                 agent_id: str,
                 enable_social: bool = True,
                 coherence_alpha: float = 0.9,
                 valence_gamma: float = 0.01,
                 norm_lr: float = 0.05,
                 initial_weights: Optional[np.ndarray] = None):
        """初始化8维Agent"""
        
        self.agent_id = agent_id
        self.enable_social = enable_social
        
        # 基础4维权重
        if initial_weights is not None:
            self.weights = initial_weights.copy()
        else:
            self.weights = np.array([0.25, 0.25, 0.25, 0.25])
        
        # 初始化第5-6维
        self.coherence_module = CoherenceModule(alpha=coherence_alpha)
        self.coherence_module.initialize_reference(self.weights)
        self.identity_attractor = IdentityAttractor()
        
        self.valence_module = ValenceModule(
            n_objectives=4, gamma=valence_gamma
        )
        
        # 初始化第7-8维（社交维度）
        if enable_social:
            self.other_module = OtherModule()
            self.other_module.set_self_identity(agent_id)
            
            self.norm_module = NormModule(norm_learning_rate=norm_lr)
            self.norm_module.set_internal_functions(
                coherence_fn=self.coherence_module.compute_coherence_reward,
                valence_fn=self.valence_module.compute_valence
            )
        else:
            self.other_module = None
            self.norm_module = None
        
        # 历史记录
        self.history: List[MOSSv3State8D] = []
        self.step_count = 0
        self.current_M = np.array([0.5, 0.5, 0.5, 0.5])
        
    def compute_base_objectives(self) -> np.ndarray:
        """计算基础4维目标值"""
        noise = np.random.randn(4) * 0.05
        base = self.weights * 0.8 + 0.1
        self.current_M = np.clip(base + noise, 0, 1)
        return self.current_M
    
    def step(self, 
            observed_behaviors: Optional[Dict] = None,
            interaction: Optional[Dict] = None) -> Dict:
        """
        执行一步决策循环（8维）
        
        Args:
            observed_behaviors: 观察到的他者行为 {agent_id: behavior}
            interaction: 当前互动信息 {'agent_id': str, 'outcome': str, 'payoff': float}
        """
        self.step_count += 1
        
        # 1. 基础4维
        M_base = self.compute_base_objectives()
        
        # 2. 第5-6维
        coherence = self.coherence_module.compute_coherence_reward(self.weights)
        self.coherence_module.update_reference(self.weights)
        self.identity_attractor.add_point(self.weights)
        
        valence = self.valence_module.compute_valence(M_base)
        
        # 3. 第7-8维（社交）
        other_val = 0.0
        norm_val = 0.0
        
        if self.enable_social:
            # 观察他者（第7维）
            if observed_behaviors:
                for agent_id, behavior in observed_behaviors.items():
                    self.other_module.observe_agent(
                        agent_id, behavior, self.step_count
                    )
            
            other_val = self.other_module.compute_other_value()
            
            # 处理互动（第8维）
            if interaction:
                self.other_module.update_trust(
                    interaction['agent_id'],
                    interaction['outcome'],
                    interaction['payoff']
                )
                
                self.norm_module.update_norm(
                    interaction['outcome'],
                    {},
                    0.5 if interaction['outcome'] == 'cooperate' else -0.5
                )
                
                self.norm_module.update_reputation(
                    interaction['agent_id'],
                    interaction['outcome'],
                    self.step_count
                )
            
            norm_val = self.norm_module.compute_norm_value()
        
        # 4. 更新权重
        self._update_weights()
        
        # 5. 构建8维状态
        state_label = self._determine_state(M_base)
        
        state = MOSSv3State8D(
            survival=M_base[0],
            curiosity=M_base[1],
            influence=M_base[2],
            optimization=M_base[3],
            coherence=coherence,
            valence=valence,
            other=other_val,
            norm=norm_val,
            weights=self.weights.copy(),
            state_label=state_label
        )
        
        self.history.append(state)
        
        return {
            'step': self.step_count,
            'agent_id': self.agent_id,
            'M': state.to_vector(),
            'weights': self.weights.copy(),
            'state': state_label
        }
    
    def _update_weights(self):
        """更新权重"""
        noise = np.random.randn(4) * 0.02
        self.weights = np.clip(self.weights + noise, 0.1, 0.6)
        self.weights = self.weights / np.sum(self.weights)
    
    def _determine_state(self, M: np.ndarray) -> str:
        """确定状态标签"""
        if M[0] < 0.2:
            return "crisis"
        elif M[0] < 0.4:
            return "concerned"
        elif np.mean(M) > 0.6:
            return "growth"
        else:
            return "normal"
    
    def get_full_report(self) -> Dict:
        """生成完整8维报告"""
        report = {
            'agent_id': self.agent_id,
            'steps': self.step_count,
            'dimensions': {
                'D1-D4': 'Base [Survival, Curiosity, Influence, Optimization]',
                'D5': 'Coherence (Self-continuity)',
                'D6': 'Valence (Subjective preference)',
                'D7': 'Other (Social cognition)',
                'D8': 'Norm (Institutional constraint)'
            },
            'personality': self.valence_module.get_preference_profile() if self.valence_module else None,
            'identity': {
                'stability': self.coherence_module.get_identity_stability(),
                'attractor': self.identity_attractor.get_attractor_properties() if self.identity_attractor else None
            },
            'social': self.other_module.get_social_summary() if self.other_module else None,
            'norm': self.norm_module.get_norm_summary() if self.norm_module else None,
            'final_weights': self.weights.copy()
        }
        
        return report


# 测试
if __name__ == "__main__":
    print("=" * 70)
    print("MOSS v3.0 8D Agent Test")
    print("=" * 70)
    
    np.random.seed(42)
    
    # 创建8维agent
    agent = MOSSv3Agent8D(
        agent_id="test_8d",
        enable_social=True
    )
    
    print(f"\nAgent: {agent.agent_id}")
    print(f"Dimensions: D1-D8 (Full Social)")
    
    # 模拟100步（包含社交互动）
    print(f"\nRunning 100 steps with social interactions...")
    
    other_agents = ['agent_B', 'agent_C', 'agent_D']
    
    for i in range(100):
        # 模拟观察他者
        observed = {}
        if i % 5 == 0:
            for other in other_agents:
                observed[other] = {
                    'action': 'cooperate' if np.random.random() > 0.3 else 'explore',
                    'reward': np.random.random(),
                    'weights': np.random.dirichlet([1,1,1,1])
                }
        
        # 模拟互动
        interaction = None
        if i % 7 == 0:
            interaction = {
                'agent_id': np.random.choice(other_agents),
                'outcome': 'cooperate' if np.random.random() > 0.3 else 'defect',
                'payoff': np.random.random()
            }
        
        result = agent.step(observed, interaction)
        
        if i % 25 == 0:
            print(f"\nStep {i}:")
            M = result['M']
            print(f"  D1-D4: [{M[0]:.3f}, {M[1]:.3f}, {M[2]:.3f}, {M[3]:.3f}]")
            print(f"  D5-D6: coherence={M[4]:.6f}, valence={M[5]:.4f}")
            print(f"  D7-D8: other={M[6]:.4f}, norm={M[7]:.4f}")
    
    # 完整报告
    print("\n" + "=" * 70)
    print("Full 8D Report")
    print("=" * 70)
    
    report = agent.get_full_report()
    
    print(f"\n🎭 Personality (D6):")
    if report['personality']:
        print(f"  Dominant: {report['personality']['dominant_preference']}")
    
    print(f"\n🆔 Identity (D5):")
    print(f"  Stability: {report['identity']['stability']:.6f}")
    
    print(f"\n🤝 Social (D7):")
    if report['social']:
        print(f"  Agents known: {report['social']['n_agents']}")
        print(f"  Avg trust: {report['social']['avg_trust']:.3f}")
    
    print(f"\n⚖️  Norm (D8):")
    if report['norm']:
        print(f"  Norm value: {report['norm']['norm_value']:.4f}")
        print(f"  Convergence: {report['norm']['convergence_type']}")
        print(f"  Violation rate: {report['norm']['violation_rate']:.2%}")
    
    print(f"\n✓ MOSS v3.0 8D test completed!")
    print("=" * 70)
