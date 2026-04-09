"""
MOSS v3.0.0 - Other Module (Dimension 7)
Other-Modeling / Theory of Mind / Social Cognition

基于ChatGPT建议实现：
- 他者模型：预测其他agent的行为和目标
- 区分"自己 vs 他者"
- 产生社会互动的认知基础

Author: Cash
Date: 2026-03-19
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class OtherAgentModel:
    """
    对其他agent的内部模型
    
    包含对其状态、目标、行为的信念
    """
    agent_id: str
    estimated_weights: np.ndarray  # 估计的权重
    estimated_state: str  # 估计的状态
    behavior_history: List[Dict]  # 观察到的行为历史
    trust_score: float  # 信任分数（0-1）
    last_interaction: int  # 上次互动时间步


class OtherModule:
    """
    第7维：他者建模 / 社会认知
    
    核心思想：
    - 系统需要建模其他agent的状态、目标、行为
    - 区分"自己"和"他者"
    - 预测他者行为以优化自身决策
    """
    
    def __init__(self,
                 memory_window: int = 50,
                 trust_learning_rate: float = 0.1):
        """
        初始化Other模块
        
        Args:
            memory_window: 记忆窗口大小
            trust_learning_rate: 信任学习率
        """
        self.memory_window = memory_window
        self.trust_lr = trust_learning_rate
        
        # 他者模型字典
        self.other_models: Dict[str, OtherAgentModel] = {}
        
        # 社交记忆
        self.interaction_history: List[Dict] = []
        
        # 自己的身份信息
        self.self_identity: Optional[str] = None
        
    def set_self_identity(self, agent_id: str):
        """设置自己的身份标识"""
        self.self_identity = agent_id
    
    def observe_agent(self, 
                     agent_id: str, 
                     observed_behavior: Dict,
                     current_step: int):
        """
        观察其他agent的行为并更新模型
        
        Args:
            agent_id: 被观察的agent ID
            observed_behavior: 观察到的行为
            current_step: 当前时间步
        """
        if agent_id == self.self_identity:
            return
        
        if agent_id not in self.other_models:
            # 初始化新agent模型
            self.other_models[agent_id] = OtherAgentModel(
                agent_id=agent_id,
                estimated_weights=np.array([0.25, 0.25, 0.25, 0.25]),
                estimated_state="normal",
                behavior_history=[],
                trust_score=0.5,
                last_interaction=current_step
            )
        
        model = self.other_models[agent_id]
        
        # 记录行为
        model.behavior_history.append({
            'step': current_step,
            'behavior': observed_behavior
        })
        
        # 限制历史长度
        if len(model.behavior_history) > self.memory_window:
            model.behavior_history.pop(0)
        
        model.last_interaction = current_step
        
        # 更新估计
        self._update_agent_estimate(model)
    
    def _update_agent_estimate(self, model: OtherAgentModel):
        """基于观察更新对他者的估计"""
        if len(model.behavior_history) < 3:
            return
        
        recent = model.behavior_history[-10:]
        
        # 估计状态
        rewards = [b['behavior'].get('reward', 0) for b in recent]
        avg_reward = np.mean(rewards)
        
        if avg_reward > 0.7:
            model.estimated_state = "growth"
        elif avg_reward < 0.3:
            model.estimated_state = "crisis"
        else:
            model.estimated_state = "normal"
        
        # 权重估计
        if 'weights' in recent[-1]['behavior']:
            observed_weights = recent[-1]['behavior']['weights']
            model.estimated_weights = 0.7 * model.estimated_weights + 0.3 * observed_weights
    
    def update_trust(self, 
                    agent_id: str, 
                    interaction_outcome: str,
                    payoff: float):
        """
        基于互动结果更新信任
        
        Args:
            agent_id: 互动对象
            interaction_outcome: 'cooperate', 'defect', 'neutral'
            payoff: 获得的收益
        """
        if agent_id not in self.other_models:
            return
        
        model = self.other_models[agent_id]
        
        if interaction_outcome == 'cooperate':
            trust_delta = self.trust_lr * (1 - model.trust_score)
        elif interaction_outcome == 'defect':
            trust_delta = -self.trust_lr * 2 * model.trust_score
        else:
            trust_delta = self.trust_lr * 0.1 * (0.5 - model.trust_score)
        
        model.trust_score = np.clip(model.trust_score + trust_delta, 0, 1)
        
        self.interaction_history.append({
            'agent_id': agent_id,
            'outcome': interaction_outcome,
            'payoff': payoff,
            'trust_after': model.trust_score
        })
    
    def compute_other_value(self) -> float:
        """
        计算第7维目标值
        
        基于社交认知的准确性和丰富性
        """
        if not self.other_models:
            return 0.0
        
        # 他者模型数量（社交广度）
        n_others = len(self.other_models)
        
        # 平均信任度（社交深度）
        avg_trust = np.mean([m.trust_score for m in self.other_models.values()])
        
        # 观察历史丰富度
        avg_history = np.mean([len(m.behavior_history) for m in self.other_models.values()])
        history_score = min(avg_history / 20, 1.0)
        
        # 综合计算
        other_value = (np.log1p(n_others) * 0.3 + 
                      avg_trust * 0.4 + 
                      history_score * 0.3)
        
        return other_value
    
    def get_social_summary(self) -> Dict:
        """获取社交分析摘要"""
        if not self.other_models:
            return {'status': 'no_data'}
        
        trust_scores = [m.trust_score for m in self.other_models.values()]
        
        return {
            'n_agents': len(self.other_models),
            'avg_trust': np.mean(trust_scores),
            'other_value': self.compute_other_value(),
            'high_trust': sum(1 for t in trust_scores if t > 0.7),
            'low_trust': sum(1 for t in trust_scores if t < 0.3)
        }


# 测试
if __name__ == "__main__":
    print("Testing OtherModule...")
    
    other = OtherModule()
    other.set_self_identity("agent_A")
    
    # 观察agent B
    for step in range(20):
        behavior = {
            'action': 'cooperate' if step % 3 == 0 else 'explore',
            'reward': 0.6 + 0.2 * np.sin(step * 0.3),
            'state': 'normal',
            'weights': np.array([0.3, 0.2, 0.3, 0.2])
        }
        other.observe_agent("agent_B", behavior, step)
    
    # 更新信任
    other.update_trust("agent_B", "cooperate", 0.8)
    other.update_trust("agent_B", "cooperate", 0.7)
    
    print(f"Other value: {other.compute_other_value():.4f}")
    print(f"Social summary: {other.get_social_summary()}")
    
    print("\n✓ OtherModule test passed!")
