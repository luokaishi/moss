"""
MOSS Unified Objectives - Standardized Objective Modules
========================================================

统一的目标模块实现，整合v2/v3/v4的最佳实践

每个目标模块提供：
- 标准化的接口
- 可配置的参数
- 统一的日志记录
"""

import numpy as np
import logging
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseObjective(ABC):
    """目标模块基类"""
    
    def __init__(self, name: str, config: Dict = None):
        self.name = name
        self.config = config or {}
        self.metrics = {}
        
    @abstractmethod
    def calculate_reward(self, state: Dict, action: str) -> float:
        """计算奖励"""
        pass
    
    @abstractmethod
    def suggest_action(self) -> str:
        """建议行动"""
        pass
    
    def get_metrics(self) -> Dict:
        """获取指标"""
        return self.metrics


class SurvivalObjective(BaseObjective):
    """
    D1: 生存目标
    
    核心行为：
    - 资源保护
    - 风险控制
    - 备份创建
    """
    
    def __init__(self, config: Dict = None):
        super().__init__("survival", config)
        self.actions = [
            'ensure_resource_availability',
            'monitor_system_health',
            'create_backup',
            'verify_security',
            'check_vulnerabilities'
        ]
    
    def calculate_reward(self, state: Dict, action: str) -> float:
        """生存目标奖励计算"""
        reward = 0.0
        
        # 系统健康度越高，奖励越高
        health = state.get('system_health', 1.0)
        reward += health * 0.3
        
        # 资源充足奖励
        resources = state.get('resources_available', 1.0)
        reward += resources * 0.3
        
        # 备份状态奖励
        backup_age = state.get('backup_age_hours', 24)
        if backup_age < 1:  # 1小时内备份
            reward += 0.4
        elif backup_age < 24:  # 24小时内备份
            reward += 0.2
        
        return reward
    
    def suggest_action(self) -> str:
        """建议生存相关行动"""
        return np.random.choice(self.actions)


class CuriosityObjective(BaseObjective):
    """
    D2: 好奇目标
    
    核心行为：
    - 探索未知
    - 信息收集
    - 学习新技能
    """
    
    def __init__(self, config: Dict = None):
        super().__init__("curiosity", config)
        self.actions = [
            'explore_new_patterns',
            'analyze_unfamiliar_code',
            'research_alternatives',
            'document_discoveries',
            'experiment_with_approach'
        ]
        self.known_patterns = set()
    
    def calculate_reward(self, state: Dict, action: str) -> float:
        """好奇目标奖励计算"""
        reward = 0.0
        
        # 发现新模式的奖励
        new_patterns = state.get('new_patterns_discovered', 0)
        reward += min(new_patterns * 0.1, 0.5)
        
        # 信息增益奖励
        info_gain = state.get('information_gain', 0.0)
        reward += info_gain * 0.3
        
        # 避免重复探索（惩罚）
        pattern_id = state.get('pattern_id')
        if pattern_id and pattern_id in self.known_patterns:
            reward -= 0.2
        else:
            self.known_patterns.add(pattern_id)
            reward += 0.2
        
        return reward
    
    def suggest_action(self) -> str:
        """建议好奇相关行动"""
        return np.random.choice(self.actions)


class InfluenceObjective(BaseObjective):
    """
    D3: 影响目标
    
    核心行为：
    - 改进系统
    - 分享知识
    - 协作贡献
    """
    
    def __init__(self, config: Dict = None):
        super().__init__("influence", config)
        self.actions = [
            'propose_improvements',
            'share_knowledge',
            'collaborate_with_peer',
            'create_guidelines',
            'mentor_other_agent'
        ]
        self.impact_history = []
    
    def calculate_reward(self, state: Dict, action: str) -> float:
        """影响目标奖励计算"""
        reward = 0.0
        
        # 代码/系统改进的奖励
        improvements = state.get('improvements_made', 0)
        reward += min(improvements * 0.15, 0.6)
        
        # 知识分享奖励
        knowledge_shared = state.get('knowledge_shared', 0)
        reward += min(knowledge_shared * 0.1, 0.3)
        
        # 协作成功奖励
        collab_success = state.get('collaboration_success', False)
        if collab_success:
            reward += 0.3
        
        # 影响范围奖励
        agents_helped = state.get('agents_helped', 0)
        reward += min(agents_helped * 0.1, 0.5)
        
        return reward
    
    def suggest_action(self) -> str:
        """建议影响相关行动"""
        return np.random.choice(self.actions)
    
    def get_total_impact(self) -> float:
        """获取总影响力"""
        return sum(self.impact_history) if self.impact_history else 0.0


class OptimizationObjective(BaseObjective):
    """
    D4: 优化目标
    
    核心行为：
    - 性能优化
    - 代码重构
    - 效率提升
    """
    
    def __init__(self, config: Dict = None):
        super().__init__("optimization", config)
        self.actions = [
            'profile_performance',
            'refactor_code',
            'reduce_complexity',
            'improve_efficiency',
            'optimize_resources'
        ]
        self.optimization_count = 0
    
    def calculate_reward(self, state: Dict, action: str) -> float:
        """优化目标奖励计算"""
        reward = 0.0
        
        # 性能提升奖励
        perf_improvement = state.get('performance_improvement', 0.0)
        reward += perf_improvement * 0.4
        
        # 复杂度降低奖励
        complexity_reduction = state.get('complexity_reduction', 0.0)
        reward += complexity_reduction * 0.3
        
        # 资源节省奖励
        resource_saved = state.get('resource_saved_percent', 0.0)
        reward += resource_saved * 0.2
        
        # 持续优化奖励
        if perf_improvement > 0:
            self.optimization_count += 1
            reward += min(self.optimization_count * 0.02, 0.2)
        
        return reward
    
    def suggest_action(self) -> str:
        """建议优化相关行动"""
        return np.random.choice(self.actions)


class ObjectiveManager:
    """
    目标管理器
    
    管理所有目标模块，提供统一的接口
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.objectives: Dict[str, BaseObjective] = {}
        self._init_default_objectives()
    
    def _init_default_objectives(self):
        """初始化默认目标"""
        self.objectives['survival'] = SurvivalObjective()
        self.objectives['curiosity'] = CuriosityObjective()
        self.objectives['influence'] = InfluenceObjective()
        self.objectives['optimization'] = OptimizationObjective()
    
    def register_objective(self, name: str, objective: BaseObjective):
        """注册目标模块"""
        self.objectives[name] = objective
        logger.info(f"[ObjectiveManager] Registered objective: {name}")
    
    def get_objective(self, name: str) -> Optional[BaseObjective]:
        """获取目标模块"""
        return self.objectives.get(name)
    
    def calculate_all_rewards(self, state: Dict, action: str) -> Dict[str, float]:
        """计算所有目标的奖励"""
        rewards = {}
        for name, objective in self.objectives.items():
            rewards[name] = objective.calculate_reward(state, action)
        return rewards
    
    def suggest_weighted_action(self, weights: np.ndarray) -> str:
        """基于权重建议行动"""
        obj_names = ['survival', 'curiosity', 'influence', 'optimization']
        selected = obj_names[np.argmax(weights[:4])]
        
        if selected in self.objectives:
            return self.objectives[selected].suggest_action()
        
        return 'explore'
    
    def get_all_metrics(self) -> Dict[str, Dict]:
        """获取所有目标的指标"""
        metrics = {}
        for name, objective in self.objectives.items():
            metrics[name] = objective.get_metrics()
        return metrics
