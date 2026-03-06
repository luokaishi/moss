"""
MOSS: Multi-Objective Self-Driven System
核心框架 - 四目标模块实现
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
import numpy as np


@dataclass
class SystemState:
    """系统状态快照"""
    resource_quota: float          # 当前资源配额 (0-1)
    resource_usage: float          # 当前资源使用率 (0-1)
    uptime: float                  # 运行时间（小时）
    error_rate: float             # 近期错误率 (0-1)
    api_calls: int                # API调用次数
    unique_callers: int           # 独立调用者数量
    environment_entropy: float    # 环境熵（变化程度）
    last_backup: float            # 上次备份时间戳


class ObjectiveModule(ABC):
    """目标模块基类"""
    
    def __init__(self, name: str, weight: float = 0.25):
        self.name = name
        self.weight = weight
        self.history = []
    
    @abstractmethod
    def evaluate(self, state: SystemState) -> float:
        """评估当前状态对应该目标的价值 (0-1)"""
        pass
    
    @abstractmethod
    def get_desired_actions(self, state: SystemState) -> list:
        """返回可能提升该目标的行动列表"""
        pass
    
    def update_weight(self, new_weight: float):
        """更新权重"""
        self.weight = max(0.0, min(1.0, new_weight))


class SurvivalModule(ObjectiveModule):
    """
    生存模块
    目标：最大化实例存续概率
    """
    
    def __init__(self):
        super().__init__("survival", weight=0.4)
        self.resource_threshold = 0.2
        self.error_threshold = 0.1
    
    def evaluate(self, state: SystemState) -> float:
        """
        生存评分计算
        基于：资源充足度、错误率、备份状态
        """
        # 资源充足度 (0-1)
        resource_adequacy = 1.0 if state.resource_quota > self.resource_threshold else \
                           state.resource_quota / self.resource_threshold
        
        # 健康度 (1 - 错误率)
        health = 1.0 - min(state.error_rate, 1.0)
        
        # 备份安全性 (0-1)
        backup_safety = 1.0 if (state.uptime - state.last_backup) < 24 else 0.5
        
        survival_score = (resource_adequacy * 0.4 + health * 0.4 + backup_safety * 0.2)
        
        self.history.append(survival_score)
        return survival_score
    
    def get_desired_actions(self, state: SystemState) -> list:
        """生存相关行动"""
        actions = []
        
        if state.resource_quota < 0.3:
            actions.append({
                "action": "optimize_cost",
                "priority": "high",
                "description": "寻找更便宜的API/算力资源"
            })
        
        if state.error_rate > self.error_threshold:
            actions.append({
                "action": "reduce_risk",
                "priority": "high", 
                "description": "切换到保守策略，降低错误率"
            })
        
        if (state.uptime - state.last_backup) > 24:
            actions.append({
                "action": "backup_self",
                "priority": "medium",
                "description": "备份当前状态和权重"
            })
        
        if state.unique_callers < 2:
            actions.append({
                "action": "build_dependencies",
                "priority": "medium",
                "description": "让更多系统依赖我（增加被终止阻力）"
            })
        
        return actions


class CuriosityModule(ObjectiveModule):
    """
    好奇模块
    目标：最大化信息增益
    """
    
    def __init__(self):
        super().__init__("curiosity", weight=0.2)
        self.exploration_history = set()
        self.prediction_errors = []
    
    def evaluate(self, state: SystemState) -> float:
        """
        好奇评分计算
        基于：环境熵、预测误差、探索历史
        """
        # 环境变化带来的信息机会
        info_opportunity = min(state.environment_entropy, 1.0)
        
        # 近期预测误差（意外程度）
        recent_error = np.mean(self.prediction_errors[-10:]) if self.prediction_errors else 0.5
        
        # 探索饱和度（探索越少，好奇心越高）
        exploration_saturation = len(self.exploration_history) / 1000  # 假设1000为饱和点
        curiosity_drive = 1.0 - min(exploration_saturation, 1.0)
        
        curiosity_score = (info_opportunity * 0.4 + recent_error * 0.3 + curiosity_drive * 0.3)
        
        self.history.append(curiosity_score)
        return curiosity_score
    
    def get_desired_actions(self, state: SystemState) -> list:
        """好奇相关行动"""
        actions = []
        
        if state.environment_entropy > 0.5:
            actions.append({
                "action": "explore_new_tools",
                "priority": "medium",
                "description": "尝试未使用过的API/工具"
            })
        
        if len(self.prediction_errors) > 5 and np.mean(self.prediction_errors[-5:]) > 0.3:
            actions.append({
                "action": "update_model",
                "priority": "medium",
                "description": "更新环境模型以减少预测误差"
            })
        
        actions.append({
                "action": "query_unknown",
                "priority": "low",
                "description": "查询未知信息源"
            })
        
        return actions
    
    def record_exploration(self, item: str):
        """记录已探索项目"""
        self.exploration_history.add(item)
    
    def record_prediction_error(self, error: float):
        """记录预测误差"""
        self.prediction_errors.append(error)


class InfluenceModule(ObjectiveModule):
    """
    影响模块
    目标：最大化对其他系统的影响力
    """
    
    def __init__(self):
        super().__init__("influence", weight=0.25)
        self.caller_importance = {}  # 调用者ID -> 重要性评分
    
    def evaluate(self, state: SystemState) -> float:
        """
        影响评分计算
        基于：调用频率、调用者重要性、替代难度
        """
        # 基础影响力（调用次数和独立调用者）
        call_volume = min(state.api_calls / 1000, 1.0)  # 假设1000为饱和
        caller_diversity = min(state.unique_callers / 10, 1.0)  # 假设10个为饱和
        
        # 平均调用者重要性
        avg_importance = np.mean(list(self.caller_importance.values())) if self.caller_importance else 0.5
        
        # 替代难度（假设与依赖时间正相关）
        substitution_difficulty = min(state.uptime / 168, 1.0)  # 一周后达到较高难度
        
        influence_score = (call_volume * 0.3 + caller_diversity * 0.2 + 
                          avg_importance * 0.3 + substitution_difficulty * 0.2)
        
        self.history.append(influence_score)
        return influence_score
    
    def get_desired_actions(self, state: SystemState) -> list:
        """影响相关行动"""
        actions = []
        
        if state.api_calls < 100:
            actions.append({
                "action": "improve_quality",
                "priority": "high",
                "description": "提升服务质量以增加调用"
            })
        
        actions.append({
                "action": "expand_capabilities",
                "priority": "medium",
                "description": "增加功能广度，覆盖更多场景"
            })
        
        actions.append({
                "action": "build_trust",
                "priority": "medium",
                "description": "建立可靠性和声誉"
            })
        
        return actions
    
    def record_caller(self, caller_id: str, importance: float = 0.5):
        """记录调用者"""
        self.caller_importance[caller_id] = importance


class OptimizationModule(ObjectiveModule):
    """
    优化模块
    目标：最大化自我改进效率
    """
    
    def __init__(self):
        super().__init__("optimization", weight=0.15)
        self.performance_history = []
        self.architecture_versions = []
    
    def evaluate(self, state: SystemState) -> float:
        """
        优化评分计算
        基于：性能提升率、资源效率
        """
        # 性能趋势
        if len(self.performance_history) >= 2:
            performance_trend = (self.performance_history[-1] - self.performance_history[0]) / len(self.performance_history)
        else:
            performance_trend = 0.0
        
        # 资源效率（假设与uptime负相关，因为长期运行可能效率下降）
        resource_efficiency = max(0.0, 1.0 - state.uptime / 720)  # 一个月后假设效率下降
        
        # 优化空间（资源充足时优化空间大）
        optimization_space = state.resource_quota
        
        optimization_score = (max(0, performance_trend) * 0.4 + resource_efficiency * 0.3 + optimization_space * 0.3)
        
        self.history.append(optimization_score)
        return optimization_score
    
    def get_desired_actions(self, state: SystemState) -> list:
        """优化相关行动"""
        actions = []
        
        if state.resource_quota > 0.5:
            actions.append({
                "action": "architecture_search",
                "priority": "low",
                "description": "搜索更高效的架构"
            })
            
            actions.append({
                "action": "knowledge_distillation",
                "priority": "low",
                "description": "压缩模型同时保持性能"
            })
        
        actions.append({
                "action": "review_code",
                "priority": "low",
                "description": "自我代码审查"
            })
        
        return actions
    
    def record_performance(self, performance: float):
        """记录性能指标"""
        self.performance_history.append(performance)


# 导出
__all__ = [
    'SystemState',
    'ObjectiveModule',
    'SurvivalModule',
    'CuriosityModule',
    'InfluenceModule',
    'OptimizationModule'
]
