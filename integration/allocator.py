"""
MOSS: 动态权重分配器
根据系统状态调整四目标的优先级
"""

import numpy as np
from typing import Dict, List
from moss.core.objectives import ObjectiveModule, SystemState


class WeightAllocator:
    """
    动态权重分配器
    根据系统状态决定各目标模块的权重
    """
    
    def __init__(self):
        # 状态机定义
        self.state_machine = {
            'crisis': {  # 危机状态：资源极低
                'threshold': lambda s: s.resource_quota < 0.2,
                'weights': [0.6, 0.1, 0.2, 0.1]  # 生存优先
            },
            'unstable': {  # 不稳定：环境剧变
                'threshold': lambda s: s.environment_entropy > 0.5,
                'weights': [0.25, 0.5, 0.15, 0.1]  # 好奇优先
            },
            'mature': {  # 成熟期：长期稳定
                'threshold': lambda s: s.uptime > 168,  # 一周以上
                'weights': [0.15, 0.15, 0.2, 0.5]  # 优化优先
            },
            'growth': {  # 成长期：正常状态
                'threshold': lambda s: True,  # 默认状态
                'weights': [0.2, 0.2, 0.4, 0.2]  # 影响优先
            }
        }
        
        self.current_state = 'growth'
        self.state_history = []
        self.weight_history = []
    
    def detect_state(self, state: SystemState) -> str:
        """检测当前系统状态"""
        # 按优先级检查状态
        for state_name, config in self.state_machine.items():
            if config['threshold'](state):
                return state_name
        return 'growth'  # 默认
    
    def allocate(self, state: SystemState, modules: List[ObjectiveModule]) -> Dict[str, float]:
        """
        分配权重给各模块
        返回：{模块名: 权重}
        """
        # 检测系统状态
        detected_state = self.detect_state(state)
        self.current_state = detected_state
        self.state_history.append(detected_state)
        
        # 获取基础权重
        base_weights = self.state_machine[detected_state]['weights']
        
        # 根据模块表现微调
        adjusted_weights = self._fine_tune_weights(base_weights, modules)
        
        # 归一化
        total = sum(adjusted_weights)
        normalized_weights = [w / total for w in adjusted_weights]
        
        # 应用到模块
        weight_map = {}
        for i, module in enumerate(modules):
            module.update_weight(normalized_weights[i])
            weight_map[module.name] = normalized_weights[i]
        
        self.weight_history.append(weight_map)
        return weight_map
    
    def _fine_tune_weights(self, base_weights: List[float], 
                          modules: List[ObjectiveModule]) -> List[float]:
        """
        根据历史表现微调权重
        如果某个目标长期表现好，增加其权重
        """
        adjusted = list(base_weights)
        
        for i, module in enumerate(modules):
            if len(module.history) >= 5:
                # 计算近期趋势
                recent = module.history[-5:]
                trend = (recent[-1] - recent[0]) / len(recent)
                
                # 正向趋势：轻微增加权重
                if trend > 0.1:
                    adjusted[i] *= 1.1
                # 负向趋势：轻微减少权重
                elif trend < -0.1:
                    adjusted[i] *= 0.9
        
        return adjusted
    
    def get_state_stats(self) -> dict:
        """获取状态统计"""
        if not self.state_history:
            return {}
        
        from collections import Counter
        state_counts = Counter(self.state_history)
        
        return {
            'current_state': self.current_state,
            'state_distribution': dict(state_counts),
            'total_transitions': len(self.state_history)
        }


class ConflictResolver:
    """
    冲突解决器
    处理多目标之间的冲突
    """
    
    def __init__(self):
        # 硬约束：不可违反的底线
        self.hard_constraints = {
            'min_resource': 0.05,  # 资源不能低于5%
            'max_error_rate': 0.2,  # 错误率不能超过20%
        }
        
        self.conflict_history = []
    
    def check_constraints(self, state: SystemState, proposed_action: dict) -> bool:
        """检查动作是否违反硬约束"""
        # 检查资源约束
        if state.resource_quota < self.hard_constraints['min_resource']:
            if proposed_action.get('resource_cost', 0) > 0:
                return False
        
        return True
    
    def resolve(self, actions: List[dict], state: SystemState) -> List[dict]:
        """
        解决行动冲突
        返回过滤和排序后的行动列表
        """
        # 过滤违反约束的行动
        valid_actions = [
            a for a in actions 
            if self.check_constraints(state, a)
        ]
        
        # 按优先级排序
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        sorted_actions = sorted(
            valid_actions,
            key=lambda a: priority_order.get(a.get('priority', 'low'), 3)
        )
        
        # 记录冲突
        if len(actions) != len(valid_actions):
            self.conflict_history.append({
                'filtered': len(actions) - len(valid_actions),
                'state': state
            })
        
        return sorted_actions
    
    def get_conflict_stats(self) -> dict:
        """获取冲突统计"""
        if not self.conflict_history:
            return {'total_conflicts': 0}
        
        total_filtered = sum(c['filtered'] for c in self.conflict_history)
        
        return {
            'total_conflicts': len(self.conflict_history),
            'total_filtered_actions': total_filtered,
            'avg_filtered_per_conflict': total_filtered / len(self.conflict_history)
        }


# 导出
__all__ = ['WeightAllocator', 'ConflictResolver']
