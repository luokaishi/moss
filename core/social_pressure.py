# v5/core/social_pressure.py
"""
社会压力模块 - v5.3 新增
实现规范传播、声誉系统、社会事件注入
"""

import numpy as np
from typing import List, Dict, Any


class SocialPressureModule:
    """
    社会压力模块
    
    核心功能:
    1. 规范传播 (Norm Propagation) - agent 间传递行为准则
    2. 声誉系统 (Reputation) - 量化 agent 的社会地位
    3. 社会事件 (Social Events) - 每 2000 步注入外部压力
    """
    
    def __init__(self):
        self.norm_propagation_rate = 0.0
        self.reputation_scores: Dict[str, float] = {}
        self.competition_factor = 0.0
        self.event_history: List[Dict] = []
        
    def update(self, agents: List, current_step: int):
        """更新社会压力状态"""
        # 计算规范传播率
        if agents:
            self.norm_propagation_rate = (
                sum(a.get_norm_score() if hasattr(a, 'get_norm_score') else 0.5 
                    for a in agents) / len(agents)
            )
        
        # 更新声誉评分
        for agent in agents:
            self.reputation_scores[agent.id] = self._calc_reputation(agent)
        
        # 每 2000 步注入社会事件
        if current_step % 2000 == 0 and current_step > 0:
            self._inject_event(agents, current_step)
    
    def get_pressure_on_purpose(self) -> float:
        """
        计算社会压力对 Purpose 的影响
        
        Returns:
            float: 压力值 [0, 1]
        """
        return 0.25 * self.norm_propagation_rate + 0.15 * self.competition_factor
    
    def get_competition_boost(self, agent_id: str) -> float:
        """获取竞争加成 (基于声誉排名)"""
        if not self.reputation_scores:
            return 0.0
        
        sorted_agents = sorted(self.reputation_scores.items(), key=lambda x: x[1], reverse=True)
        rank = next((i for i, (aid, _) in enumerate(sorted_agents) if aid == agent_id), len(sorted_agents))
        
        # 前 10% 获得最大加成
        return max(0.0, 0.3 - (rank / len(sorted_agents)) * 0.3)
    
    def _calc_reputation(self, agent) -> float:
        """
        计算 agent 声誉
        
        基于:
        - 历史成功率
        - 合作行为次数
        - 社会贡献度
        """
        # 简化实现 (可根据实际需求扩展)
        base_score = 0.5
        
        if hasattr(agent, 'success_rate'):
            base_score += 0.3 * agent.success_rate
        
        if hasattr(agent, 'cooperation_count'):
            base_score += 0.2 * min(1.0, agent.cooperation_count / 100)
        
        return np.clip(base_score, 0.0, 1.0)
    
    def _inject_event(self, agents: List, step: int):
        """
        注入社会事件
        
        事件类型:
        - 资源稀缺 (增加竞争)
        - 合作奖励 (鼓励协作)
        - 规范强化 (提升一致性)
        """
        event_types = ['resource_scarcity', 'cooperation_reward', 'norm_reinforcement']
        event_type = np.random.choice(event_types, p=[0.4, 0.3, 0.3])
        
        event = {
            'step': step,
            'type': event_type,
            'impact': np.random.uniform(0.1, 0.3)
        }
        
        self.event_history.append(event)
        
        # 应用事件效果
        if event_type == 'resource_scarcity':
            self.competition_factor = min(1.0, self.competition_factor + event['impact'])
        elif event_type == 'cooperation_reward':
            self.competition_factor = max(0.0, self.competition_factor - event['impact'])
        elif event_type == 'norm_reinforcement':
            self.norm_propagation_rate = min(1.0, self.norm_propagation_rate + event['impact'] * 0.5)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'norm_propagation_rate': self.norm_propagation_rate,
            'competition_factor': self.competition_factor,
            'avg_reputation': np.mean(list(self.reputation_scores.values())) if self.reputation_scores else 0.0,
            'total_events': len(self.event_history),
            'event_distribution': self._count_events_by_type()
        }
    
    def get_social_value_vector(self):
        """返回社会压力向量（供 PurposeDynamicsModule 融合使用）"""
        from core.multimodal_extension import ValueVector
        vec = ValueVector()
        
        pressure = np.zeros(64)
        pressure[0:16] = self.norm_propagation_rate * 0.8
        pressure[16:32] = self.competition_factor * 1.2
        pressure[32:48] = 0.5 * 0.9
        pressure[48:64] = 0.1 * 1.5
        
        norm = np.linalg.norm(pressure) + 1e-10
        pressure = pressure / norm
        
        vec.value_vector = pressure.astype(np.float32)
        vec.confidence = 0.7 + 0.3 * self.norm_propagation_rate
        return vec
    
    def get_pressure_weight(self) -> float:
        """标量压力权重（0.0~0.4）"""
        return 0.15 * self.norm_propagation_rate + 0.15 * self.competition_factor + 0.1 * 0.5
    
    def _count_events_by_type(self) -> Dict[str, int]:
        """统计各类型事件数量"""
        counts = {}
        for event in self.event_history:
            event_type = event['type']
            counts[event_type] = counts.get(event_type, 0) + 1
        return counts
