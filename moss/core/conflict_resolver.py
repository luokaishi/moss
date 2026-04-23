#!/usr/bin/env python3
"""
MOSS v9.0 - Conflict Resolver
冲突解决器 - 解决Agent间冲突

Author: MOSS v9.0
Date: 2026-04-23
"""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
import asyncio
import uuid


class ConflictType(Enum):
    """冲突类型"""
    RESOURCE = auto()      # 资源竞争
    TASK = auto()          # 任务冲突
    ACTION = auto()        # 动作冲突
    GOAL = auto()          # 目标冲突
    COMMUNICATION = auto() # 通信冲突


class ResolutionStrategy(Enum):
    """解决策略"""
    PRIORITY = auto()      # 优先级优先
    TIMESTAMP = auto()     # 时间戳优先
    PERFORMANCE = auto()   # 性能优先
    COORDINATION = auto()  # 协调协商
    ARBITRATION = auto()   # 仲裁裁决


@dataclass
class Conflict:
    """冲突信息"""
    conflict_id: str
    conflict_type: ConflictType
    agents_involved: List[str]
    resource_id: Optional[str] = None
    description: str = ""
    severity: int = 1  # 1-10
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    context: Dict = field(default_factory=dict)


@dataclass
class Resolution:
    """解决方案"""
    resolution_id: str
    conflict_id: str
    strategy: ResolutionStrategy
    winner: Optional[str] = None  # 获胜Agent
    actions: List[Dict] = field(default_factory=list)
    explanation: str = ""
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())


class ConflictResolver:
    """
    冲突解决器
    
    核心功能:
    1. 冲突检测
    2. 冲突分类
    3. 策略选择
    4. 冲突解决
    5. 历史记录
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.conflict_history: List[Conflict] = []
        self.resolution_history: List[Resolution] = []
        self.resolution_strategies: Dict[ConflictType, ResolutionStrategy] = {}
        self.custom_resolvers: Dict[str, Callable] = {}
        self.max_history = self.config.get('max_history', 1000)
        
        # 初始化默认策略
        self._init_default_strategies()
    
    def _init_default_strategies(self):
        """初始化默认解决策略"""
        self.resolution_strategies = {
            ConflictType.RESOURCE: ResolutionStrategy.PRIORITY,
            ConflictType.TASK: ResolutionStrategy.PERFORMANCE,
            ConflictType.ACTION: ResolutionStrategy.TIMESTAMP,
            ConflictType.GOAL: ResolutionStrategy.COORDINATION,
            ConflictType.COMMUNICATION: ResolutionStrategy.ARBITRATION,
        }
    
    def detect_conflict(
        self,
        actions: List[Dict],
        context: Dict = None
    ) -> Optional[Conflict]:
        """
        检测冲突
        
        Args:
            actions: 动作列表
            context: 上下文信息
            
        Returns:
            Conflict对象或None
        """
        # 检查资源竞争
        resource_usage: Dict[str, List[str]] = {}
        
        for action in actions:
            agent_id = action.get('agent_id')
            resources = action.get('resources', [])
            
            for resource in resources:
                if resource not in resource_usage:
                    resource_usage[resource] = []
                resource_usage[resource].append(agent_id)
        
        # 发现资源竞争
        for resource, agents in resource_usage.items():
            if len(agents) > 1:
                return Conflict(
                    conflict_id=f"conflict_{uuid.uuid4().hex[:8]}",
                    conflict_type=ConflictType.RESOURCE,
                    agents_involved=agents,
                    resource_id=resource,
                    description=f"资源竞争: {resource}",
                    severity=5,
                    context=context or {}
                )
        
        return None
    
    async def resolve(
        self,
        conflict: Conflict,
        agent_info: Dict[str, Dict] = None
    ) -> Resolution:
        """
        解决冲突
        
        Args:
            conflict: 冲突信息
            agent_info: Agent信息字典 {agent_id: info}
            
        Returns:
            Resolution解决方案
        """
        # 记录冲突
        self.conflict_history.append(conflict)
        if len(self.conflict_history) > self.max_history:
            self.conflict_history.pop(0)
        
        # 选择策略
        strategy = self.resolution_strategies.get(
            conflict.conflict_type,
            ResolutionStrategy.ARBITRATION
        )
        
        # 执行解决
        if strategy == ResolutionStrategy.PRIORITY:
            resolution = await self._resolve_by_priority(conflict, agent_info)
        elif strategy == ResolutionStrategy.TIMESTAMP:
            resolution = await self._resolve_by_timestamp(conflict)
        elif strategy == ResolutionStrategy.PERFORMANCE:
            resolution = await self._resolve_by_performance(conflict, agent_info)
        elif strategy == ResolutionStrategy.COORDINATION:
            resolution = await self._resolve_by_coordination(conflict)
        else:  # ARBITRATION
            resolution = await self._resolve_by_arbitration(conflict)
        
        # 记录解决方案
        self.resolution_history.append(resolution)
        if len(self.resolution_history) > self.max_history:
            self.resolution_history.pop(0)
        
        print(f"[ConflictResolver] 冲突解决: {conflict.conflict_id} -> {resolution.winner}")
        return resolution
    
    async def _resolve_by_priority(
        self,
        conflict: Conflict,
        agent_info: Dict[str, Dict]
    ) -> Resolution:
        """按优先级解决"""
        winner = None
        highest_priority = -1
        
        for agent_id in conflict.agents_involved:
            info = agent_info.get(agent_id, {})
            priority = info.get('priority', 0)
            
            if priority > highest_priority:
                highest_priority = priority
                winner = agent_id
        
        return Resolution(
            resolution_id=f"res_{uuid.uuid4().hex[:8]}",
            conflict_id=conflict.conflict_id,
            strategy=ResolutionStrategy.PRIORITY,
            winner=winner,
            explanation=f"优先级最高: {winner}"
        )
    
    async def _resolve_by_timestamp(self, conflict: Conflict) -> Resolution:
        """按时间戳解决 (先到先得)"""
        # 这里简化处理，实际应该比较动作发起时间
        winner = conflict.agents_involved[0] if conflict.agents_involved else None
        
        return Resolution(
            resolution_id=f"res_{uuid.uuid4().hex[:8]}",
            conflict_id=conflict.conflict_id,
            strategy=ResolutionStrategy.TIMESTAMP,
            winner=winner,
            explanation=f"时间优先: {winner}"
        )
    
    async def _resolve_by_performance(
        self,
        conflict: Conflict,
        agent_info: Dict[str, Dict]
    ) -> Resolution:
        """按性能解决"""
        winner = None
        best_performance = -1
        
        for agent_id in conflict.agents_involved:
            info = agent_info.get(agent_id, {})
            performance = info.get('performance_score', 0.5)
            
            if performance > best_performance:
                best_performance = performance
                winner = agent_id
        
        return Resolution(
            resolution_id=f"res_{uuid.uuid4().hex[:8]}",
            conflict_id=conflict.conflict_id,
            strategy=ResolutionStrategy.PERFORMANCE,
            winner=winner,
            explanation=f"性能最优: {winner}"
        )
    
    async def _resolve_by_coordination(self, conflict: Conflict) -> Resolution:
        """通过协调解决"""
        # 协调所有Agent，寻找共赢方案
        # 这里简化处理，实际应该有复杂的协商逻辑
        
        return Resolution(
            resolution_id=f"res_{uuid.uuid4().hex[:8]}",
            conflict_id=conflict.conflict_id,
            strategy=ResolutionStrategy.COORDINATION,
            winner=None,  # 协调方案可能没有单一获胜者
            actions=[
                {'type': 'coordinate', 'agents': conflict.agents_involved}
            ],
            explanation="协调解决方案"
        )
    
    async def _resolve_by_arbitration(self, conflict: Conflict) -> Resolution:
        """通过仲裁解决"""
        # 随机选择或基于其他规则
        import random
        winner = random.choice(conflict.agents_involved) if conflict.agents_involved else None
        
        return Resolution(
            resolution_id=f"res_{uuid.uuid4().hex[:8]}",
            conflict_id=conflict.conflict_id,
            strategy=ResolutionStrategy.ARBITRATION,
            winner=winner,
            explanation=f"仲裁裁决: {winner}"
        )
    
    def set_strategy(
        self,
        conflict_type: ConflictType,
        strategy: ResolutionStrategy
    ):
        """设置冲突类型的解决策略"""
        self.resolution_strategies[conflict_type] = strategy
    
    def register_custom_resolver(
        self,
        resolver_name: str,
        resolver_func: Callable
    ):
        """注册自定义解决器"""
        self.custom_resolvers[resolver_name] = resolver_func
    
    def get_conflict_stats(self) -> Dict:
        """获取冲突统计"""
        type_counts = {}
        for conflict in self.conflict_history:
            type_name = conflict.conflict_type.name
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        strategy_counts = {}
        for resolution in self.resolution_history:
            strategy_name = resolution.strategy.name
            strategy_counts[strategy_name] = strategy_counts.get(strategy_name, 0) + 1
        
        return {
            'total_conflicts': len(self.conflict_history),
            'total_resolutions': len(self.resolution_history),
            'conflict_types': type_counts,
            'resolution_strategies': strategy_counts,
        }
    
    def get_resolution_rate(self) -> float:
        """获取解决率"""
        if not self.conflict_history:
            return 1.0
        return len(self.resolution_history) / len(self.conflict_history)


# 全局冲突解决器实例
_resolver: Optional[ConflictResolver] = None


def get_conflict_resolver(config: Dict = None) -> ConflictResolver:
    """获取全局冲突解决器实例"""
    global _resolver
    if _resolver is None:
        _resolver = ConflictResolver(config)
    return _resolver


# 测试代码
if __name__ == "__main__":
    async def test():
        # 创建冲突解决器
        resolver = ConflictResolver()
        
        # 模拟冲突
        actions = [
            {'agent_id': 'agent_1', 'resources': ['file_a']},
            {'agent_id': 'agent_2', 'resources': ['file_a']},  # 资源竞争
        ]
        
        # 检测冲突
        conflict = resolver.detect_conflict(actions)
        if conflict:
            print(f"检测到冲突: {conflict.description}")
            
            # 解决冲突
            agent_info = {
                'agent_1': {'priority': 5, 'performance_score': 0.8},
                'agent_2': {'priority': 3, 'performance_score': 0.6},
            }
            
            resolution = await resolver.resolve(conflict, agent_info)
            print(f"解决方案: {resolution.explanation}")
        
        # 统计
        stats = resolver.get_conflict_stats()
        print(f"统计: {stats}")
    
    asyncio.run(test())
