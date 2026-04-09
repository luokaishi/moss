"""
MOSS v3.0.0 - Norm Module (Dimension 8)
Norm Internalization / Social Constraint / Institutional Emergence

基于ChatGPT建议实现：
- 规范函数：N(a, s) = 规范代价
- 社会惩罚 + 自我惩罚
- 从博弈到制度萌芽

Author: Cash
Date: 2026-03-19
"""

import numpy as np
from typing import Dict, List, Optional, Callable
from collections import defaultdict


class NormModule:
    """
    第8维：规范内化 / 社会约束
    
    核心思想：
    - 规范不是外部规则，而是内化约束
    - 即使没有人惩罚，系统也"不想这么做"
    - 将社会反馈和自我一致性整合为行为约束
    
    数学形式：
    N(a, s) = E_social_penalty(a, s) + E_self_penalty(a, s)
    V_norm = -N(a, s)
    
    关键能力：
    1. 规范学习：从互动中学习什么是"不做的"
    2. 内化机制：将外部约束转化为内部代价
    3. 声誉追踪：记住历史行为
    4. 长期结构：稳定的行为模式
    """
    
    def __init__(self,
                 norm_learning_rate: float = 0.05,
                 reputation_decay: float = 0.99,
                 self_penalty_weight: float = 0.5):
        """
        初始化Norm模块
        
        Args:
            norm_learning_rate: 规范学习率
            reputation_decay: 声誉衰减率
            self_penalty_weight: 自我惩罚权重
        """
        self.norm_lr = norm_learning_rate
        self.reputation_decay = reputation_decay
        self.self_penalty_weight = self_penalty_weight
        
        # 规范代价表：{action_type: norm_cost}
        self.norm_costs: Dict[str, float] = defaultdict(lambda: 0.0)
        
        # 声誉系统：{agent_id: reputation_score}
        self.reputation: Dict[str, float] = defaultdict(lambda: 0.5)
        
        # 规范历史
        self.norm_violations: List[Dict] = []
        self.norm_compliances: List[Dict] = []
        
        # 当前状态函数（用于计算自我惩罚）
        self.coherence_fn: Optional[Callable] = None
        self.valence_fn: Optional[Callable] = None
        
    def set_internal_functions(self, 
                              coherence_fn: Callable,
                              valence_fn: Callable):
        """
        设置内部函数引用
        
        Args:
            coherence_fn: 计算一致性的函数
            valence_fn: 计算偏好的函数
        """
        self.coherence_fn = coherence_fn
        self.valence_fn = valence_fn
    
    def compute_norm_cost(self,
                         action: str,
                         state: Dict,
                         social_context: Optional[Dict] = None) -> float:
        """
        计算行为的规范代价
        
        N(a, s) = E_social_penalty + E_self_penalty
        
        Args:
            action: 动作类型
            state: 当前状态
            social_context: 社交上下文（包含他者反馈等）
            
        Returns:
            规范代价（越高越违反规范）
        """
        # 1. 社会惩罚
        social_penalty = self._compute_social_penalty(action, social_context)
        
        # 2. 自我惩罚（违背一致性和偏好）
        self_penalty = self._compute_self_penalty(action, state)
        
        # 3. 已学习的规范代价
        learned_cost = self.norm_costs.get(action, 0.0)
        
        # 总规范代价
        total_cost = (social_penalty + 
                     self.self_penalty_weight * self_penalty +
                     0.3 * learned_cost)
        
        return total_cost
    
    def _compute_social_penalty(self,
                               action: str,
                               social_context: Optional[Dict]) -> float:
        """
        计算社会惩罚
        
        基于：
        - 他者反馈
        - 声誉影响
        - 合作失败风险
        """
        if social_context is None:
            return 0.0
        
        penalty = 0.0
        
        # 来自他者的负面反馈
        if 'negative_feedback' in social_context:
            penalty += social_context['negative_feedback'] * 0.5
        
        # 声誉损害
        if 'reputation_impact' in social_context:
            penalty += abs(social_context['reputation_impact']) * 0.3
        
        # 合作失败
        if action in ['defect', 'betray', 'cheat']:
            penalty += 0.4  # 高代价
        
        return penalty
    
    def _compute_self_penalty(self,
                             action: str,
                             state: Dict) -> float:
        """
        计算自我惩罚
        
        E_self_penalty = D(行为结果, 自我一致性/偏好)
        
        基于：
        - 与自我一致性的偏离
        - 与内在偏好的冲突
        """
        penalty = 0.0
        
        # 如果action违背之前的承诺或行为模式
        if 'previous_commitments' in state:
            if action not in state['previous_commitments']:
                penalty += 0.2  # 不一致代价
        
        # 如果action导致内在体验下降
        if self.valence_fn:
            # 假设：某些action天然与valence冲突
            if action in ['defect', 'harm', 'deceive']:
                penalty += 0.3
        
        return penalty
    
    def update_norm(self,
                   action: str,
                   outcome: Dict,
                   social_feedback: float):
        """
        基于结果更新规范
        
        N(a) ← N(a) + η * (social_penalty + coherence_violation + valence_conflict)
        
        Args:
            action: 执行的动作
            outcome: 结果
            social_feedback: 社会反馈（-1到1）
        """
        # 计算更新量
        violation = 0.0
        
        if social_feedback < -0.3:  # 负面反馈
            violation = abs(social_feedback)
            self.norm_violations.append({
                'action': action,
                'feedback': social_feedback,
                'time': len(self.norm_violations)
            })
        elif social_feedback > 0.3:  # 正面反馈
            # 降低该action的规范代价
            violation = -0.1 * social_feedback
            self.norm_compliances.append({
                'action': action,
                'feedback': social_feedback,
                'time': len(self.norm_compliances)
            })
        
        # 更新规范代价
        current_cost = self.norm_costs[action]
        self.norm_costs[action] = current_cost + self.norm_lr * violation
        
        # 限制范围
        self.norm_costs[action] = np.clip(self.norm_costs[action], -1, 2)
    
    def update_reputation(self,
                         agent_id: str,
                         behavior: str,
                         time_step: int):
        """
        更新对他者的声誉评价
        
        Args:
            agent_id: agent标识
            behavior: 行为类型
            time_step: 时间步
        """
        current_rep = self.reputation[agent_id]
        
        # 基于行为调整声誉
        if behavior in ['cooperate', 'help', 'share']:
            delta = 0.1 * (1 - current_rep)
        elif behavior in ['defect', 'betray', 'cheat']:
            delta = -0.2 * current_rep  # 背叛更影响声誉
        else:
            delta = 0.0
        
        # 时间衰减
        decay = self.reputation_decay ** (time_step * 0.01)
        
        self.reputation[agent_id] = np.clip(current_rep + delta * decay, 0, 1)
    
    def compute_norm_value(self) -> float:
        """
        计算第8维目标值
        
        V_norm = -N(a, s)
        
        基于：
        - 遵守规范的程度
        - 声誉质量
        - 长期行为一致性
        """
        if not self.norm_costs:
            return 0.0
        
        # 平均规范代价（越低越好，所以取负）
        avg_cost = np.mean(list(self.norm_costs.values()))
        
        # 声誉质量
        if self.reputation:
            avg_reputation = np.mean(list(self.reputation.values()))
        else:
            avg_reputation = 0.5
        
        # 遵守率
        total_interactions = len(self.norm_violations) + len(self.norm_compliances)
        if total_interactions > 0:
            compliance_rate = len(self.norm_compliances) / total_interactions
        else:
            compliance_rate = 0.5
        
        # 综合
        norm_value = (-avg_cost * 0.4 + 
                     avg_reputation * 0.3 + 
                     compliance_rate * 0.3)
        
        return norm_value
    
    def get_convergence_type(self) -> str:
        """
        判断规范收敛形态
        
        返回：
        - 'strong_norm': 强规范型（Stable Society）
        - 'opportunistic': 机会主义型
        - 'norm_collapse': 规范崩塌
        """
        if not self.norm_costs:
            return 'undetermined'
        
        avg_cost = np.mean(list(self.norm_costs.values()))
        
        # 计算规范权重（通过观察violation频率）
        total = len(self.norm_violations) + len(self.norm_compliances)
        if total > 10:
            violation_rate = len(self.norm_violations) / total
        else:
            violation_rate = 0.5
        
        if avg_cost > 0.5 and violation_rate < 0.2:
            return 'strong_norm'
        elif avg_cost > 0.2 and violation_rate < 0.4:
            return 'opportunistic'
        elif violation_rate > 0.6:
            return 'norm_collapse'
        else:
            return 'transitional'
    
    def get_norm_summary(self) -> Dict:
        """获取规范系统摘要"""
        return {
            'norm_costs': dict(self.norm_costs),
            'reputation': dict(self.reputation),
            'norm_value': self.compute_norm_value(),
            'convergence_type': self.get_convergence_type(),
            'n_violations': len(self.norm_violations),
            'n_compliances': len(self.norm_compliances),
            'violation_rate': (len(self.norm_violations) / 
                             (len(self.norm_violations) + len(self.norm_compliances))
                             if (len(self.norm_violations) + len(self.norm_compliances)) > 0 else 0.5)
        }


# 测试
if __name__ == "__main__":
    print("Testing NormModule...")
    
    norm = NormModule()
    
    # 模拟一系列互动
    actions = ['cooperate', 'cooperate', 'defect', 'cooperate', 'share',
               'defect', 'cooperate', 'help', 'cooperate', 'cooperate']
    
    feedbacks = [0.5, 0.6, -0.8, 0.4, 0.7,
                -0.7, 0.5, 0.6, 0.5, 0.4]
    
    for i, (action, feedback) in enumerate(zip(actions, feedbacks)):
        # 计算规范代价
        cost = norm.compute_norm_cost(action, {})
        
        # 更新规范
        norm.update_norm(action, {}, feedback)
        
        # 更新声誉
        other_id = f"agent_{i % 3}"
        if 'defect' in action:
            norm.update_reputation(other_id, 'defect', i)
        else:
            norm.update_reputation(other_id, 'cooperate', i)
        
        if i % 3 == 0:
            print(f"Step {i}: action={action}, cost={cost:.3f}, norm_value={norm.compute_norm_value():.3f}")
    
    print(f"\nFinal summary:")
    summary = norm.get_norm_summary()
    print(f"  Norm value: {summary['norm_value']:.4f}")
    print(f"  Convergence type: {summary['convergence_type']}")
    print(f"  Violation rate: {summary['violation_rate']:.2%}")
    print(f"  Learned norm costs: {summary['norm_costs']}")
    
    print("\n✓ NormModule test passed!")
