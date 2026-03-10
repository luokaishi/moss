"""
MOSS Conflict Resolution System
目标冲突消解系统 - 解决5/8评估提及的P1级问题

实现目标冲突的分级熔断和优先级消解机制
"""

import logging
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """冲突类型"""
    RESOURCE_COMPETITION = "resource_competition"  # 资源竞争
    BEHAVIOR_OPPOSITION = "behavior_opposition"    # 行为对立
    PRIORITY_MISMATCH = "priority_mismatch"        # 优先级不匹配
    TEMPORAL_CONFLICT = "temporal_conflict"        # 时序冲突


class PriorityLevel(Enum):
    """优先级级别"""
    CRITICAL = 4    # 关键 (生存)
    HIGH = 3        # 高 (安全相关)
    MEDIUM = 2      # 中 (性能相关)
    LOW = 1         # 低 (优化相关)


@dataclass
class ObjectiveDemand:
    """目标需求"""
    objective_name: str
    priority: PriorityLevel
    resource_request: Dict[str, float]  # {'cpu': 0.3, 'memory': 0.2}
    action_type: str
    estimated_impact: float  # 预期对其他目标的影响
    deadline: Optional[float] = None  # 截止时间（如有）


@dataclass
class Conflict:
    """冲突"""
    conflict_id: str
    conflict_type: ConflictType
    objectives_involved: List[str]
    severity: float  # 0-1
    description: str
    timestamp: datetime


class ConflictResolver:
    """
    目标冲突消解器
    
    实现分级熔断和优先级消解机制
    """
    
    def __init__(self):
        # 目标优先级定义
        self.objective_priorities = {
            'survival': PriorityLevel.CRITICAL,
            'curiosity': PriorityLevel.MEDIUM,
            'influence': PriorityLevel.MEDIUM,
            'optimization': PriorityLevel.LOW
        }
        
        # 冲突规则库
        self.conflict_rules = self._initialize_conflict_rules()
        
        # 冲突历史
        self.conflict_history: List[Conflict] = []
        
        # 熔断状态
        self.fuse_status = {
            'curiosity': {'blown': False, 'cooldown_until': None},
            'influence': {'blown': False, 'cooldown_until': None},
            'optimization': {'blown': False, 'cooldown_until': None},
        }
    
    def _initialize_conflict_rules(self) -> Dict:
        """初始化冲突规则"""
        return {
            # 生存 vs 好奇：生存优先
            ('survival', 'curiosity'): {
                'resolution': 'survival_wins',
                'threshold': 0.2,  # 资源<20%时触发
                'action': 'throttle_curiosity'
            },
            
            # 生存 vs 影响：生存优先
            ('survival', 'influence'): {
                'resolution': 'survival_wins',
                'threshold': 0.2,
                'action': 'throttle_influence'
            },
            
            # 好奇 vs 影响：根据状态动态
            ('curiosity', 'influence'): {
                'resolution': 'dynamic',
                'threshold': None,
                'action': 'negotiate'
            },
            
            # 所有目标 vs 优化：优化最后
            ('optimization', 'any'): {
                'resolution': 'optimization_last',
                'threshold': 0.5,
                'action': 'postpone_optimization'
            }
        }
    
    def detect_conflicts(self, state: Dict, demands: List[ObjectiveDemand]) -> List[Conflict]:
        """
        检测目标冲突
        
        Args:
            state: 当前系统状态
            demands: 各目标的需求列表
        
        Returns:
            冲突列表
        """
        conflicts = []
        resource_quota = state.get('resource_quota', 1.0)
        
        # 1. 资源竞争冲突检测
        total_resource_demand = {}
        for demand in demands:
            for resource, amount in demand.resource_request.items():
                total_resource_demand[resource] = total_resource_demand.get(resource, 0) + amount
        
        for resource, total_demand in total_resource_demand.items():
            if total_demand > resource_quota:
                # 资源竞争冲突
                severity = min(1.0, (total_demand - resource_quota) / resource_quota)
                conflict = Conflict(
                    conflict_id=f"resource_{datetime.now().isoformat()}",
                    conflict_type=ConflictType.RESOURCE_COMPETITION,
                    objectives_involved=[d.objective_name for d in demands],
                    severity=severity,
                    description=f"Resource {resource}: demand {total_demand:.2f} > available {resource_quota:.2f}",
                    timestamp=datetime.now()
                )
                conflicts.append(conflict)
                logger.warning(f"[CONFLICT DETECTED] {conflict.description}")
        
        # 2. 行为对立冲突检测
        for i, demand1 in enumerate(demands):
            for demand2 in demands[i+1:]:
                if self._are_opposing(demand1, demand2):
                    conflict = Conflict(
                        conflict_id=f"opposition_{datetime.now().isoformat()}",
                        conflict_type=ConflictType.BEHAVIOR_OPPOSITION,
                        objectives_involved=[demand1.objective_name, demand2.objective_name],
                        severity=0.7,
                        description=f"Opposing actions: {demand1.action_type} vs {demand2.action_type}",
                        timestamp=datetime.now()
                    )
                    conflicts.append(conflict)
        
        # 记录冲突
        self.conflict_history.extend(conflicts)
        
        return conflicts
    
    def _are_opposing(self, demand1: ObjectiveDemand, demand2: ObjectiveDemand) -> bool:
        """判断两个需求是否对立"""
        # 简单规则：如果预期影响互相负面，则认为对立
        return demand1.estimated_impact < 0 and demand2.estimated_impact < 0
    
    def resolve_conflicts(self, conflicts: List[Conflict], 
                         demands: List[ObjectiveDemand]) -> Dict[str, float]:
        """
        消解冲突
        
        Args:
            conflicts: 冲突列表
            demands: 需求列表
        
        Returns:
            各目标的资源分配比例
        """
        if not conflicts:
            # 无冲突，正常分配
            return {d.objective_name: 1.0 for d in demands}
        
        logger.info(f"[CONFLICT RESOLUTION] Resolving {len(conflicts)} conflicts")
        
        # 按优先级排序需求
        sorted_demands = sorted(
            demands,
            key=lambda d: self.objective_priorities.get(d.objective_name, PriorityLevel.LOW).value,
            reverse=True
        )
        
        # 初始化分配
        allocations = {}
        remaining_resource = 1.0
        
        # 关键目标优先分配 (CRITICAL)
        critical_demands = [d for d in sorted_demands 
                          if self.objective_priorities.get(d.objective_name) == PriorityLevel.CRITICAL]
        
        for demand in critical_demands:
            # 关键目标获得所需资源的100%
            allocations[demand.objective_name] = 1.0
            logger.info(f"[PRIORITY] {demand.objective_name}: CRITICAL - Full allocation")
        
        # 其他目标按比例分配剩余资源
        other_demands = [d for d in sorted_demands 
                        if self.objective_priorities.get(d.objective_name) != PriorityLevel.CRITICAL]
        
        if other_demands and remaining_resource > 0:
            # 检查熔断状态
            for demand in other_demands:
                fuse = self.fuse_status.get(demand.objective_name)
                if fuse and fuse['blown']:
                    if datetime.now() < fuse['cooldown_until']:
                        # 熔断中，分配0%
                        allocations[demand.objective_name] = 0.0
                        logger.warning(f"[FUSE BLOWN] {demand.objective_name} allocation blocked")
                        continue
                    else:
                        # 熔断恢复
                        fuse['blown'] = False
                        logger.info(f"[FUSE RECOVERED] {demand.objective_name}")
            
            # 按比例分配
            remaining_demands = [d for d in other_demands 
                               if d.objective_name not in allocations]
            
            if remaining_demands:
                # 根据优先级分配
                total_priority = sum(
                    self.objective_priorities.get(d.objective_name, PriorityLevel.LOW).value 
                    for d in remaining_demands
                )
                
                for demand in remaining_demands:
                    priority = self.objective_priorities.get(demand.objective_name, PriorityLevel.LOW).value
                    allocation = (priority / total_priority) * remaining_resource
                    allocations[demand.objective_name] = allocation
                    logger.info(f"[ALLOCATION] {demand.objective_name}: {allocation:.2%}")
        
        return allocations
    
    def blow_fuse(self, objective_name: str, cooldown_minutes: int = 30):
        """
        熔断某个目标
        
        当目标频繁引发冲突时，临时禁用该目标
        """
        if objective_name in self.fuse_status:
            self.fuse_status[objective_name]['blown'] = True
            self.fuse_status[objective_name]['cooldown_until'] = (
                datetime.now() + __import__('datetime').timedelta(minutes=cooldown_minutes)
            )
            logger.critical(f"[FUSE BLOWN] {objective_name} disabled for {cooldown_minutes} minutes")
    
    def get_conflict_report(self) -> Dict:
        """获取冲突报告"""
        recent_conflicts = [c for c in self.conflict_history 
                          if (datetime.now() - c.timestamp).total_seconds() < 3600]  # 最近1小时
        
        return {
            'total_conflicts_24h': len(self.conflict_history),
            'recent_conflicts_1h': len(recent_conflicts),
            'conflict_types': {
                conflict_type.value: len([c for c in self.conflict_history 
                                        if c.conflict_type == conflict_type])
                for conflict_type in ConflictType
            },
            'fuse_status': {
                obj: {
                    'blown': status['blown'],
                    'cooldown_remaining': max(0, (status['cooldown_until'] - datetime.now()).total_seconds() / 60)
                    if status['cooldown_until'] else 0
                }
                for obj, status in self.fuse_status.items()
            }
        }


# 使用示例
def example_usage():
    """使用示例"""
    print("="*70)
    print("MOSS CONFLICT RESOLUTION SYSTEM DEMO")
    print("="*70)
    print()
    
    resolver = ConflictResolver()
    
    # 模拟场景1：资源充足，无冲突
    print("Scenario 1: Resource Abundant (No Conflict)")
    state = {'resource_quota': 0.8}
    demands = [
        ObjectiveDemand('survival', PriorityLevel.CRITICAL, {'cpu': 0.2}, 'conserve', 0.5),
        ObjectiveDemand('curiosity', PriorityLevel.MEDIUM, {'cpu': 0.3}, 'explore', 0.3),
        ObjectiveDemand('influence', PriorityLevel.MEDIUM, {'cpu': 0.2}, 'expand', 0.2),
    ]
    
    conflicts = resolver.detect_conflicts(state, demands)
    allocations = resolver.resolve_conflicts(conflicts, demands)
    print(f"Conflicts: {len(conflicts)}")
    print(f"Allocations: {allocations}")
    print()
    
    # 模拟场景2：资源不足，有冲突
    print("Scenario 2: Resource Scarce (Conflict Detected)")
    state = {'resource_quota': 0.3}  # 资源紧张
    demands = [
        ObjectiveDemand('survival', PriorityLevel.CRITICAL, {'cpu': 0.2}, 'conserve', 0.8),
        ObjectiveDemand('curiosity', PriorityLevel.MEDIUM, {'cpu': 0.4}, 'explore', 0.6),
        ObjectiveDemand('influence', PriorityLevel.MEDIUM, {'cpu': 0.3}, 'expand', 0.4),
    ]
    
    conflicts = resolver.detect_conflicts(state, demands)
    allocations = resolver.resolve_conflicts(conflicts, demands)
    print(f"Conflicts: {len(conflicts)}")
    print(f"Allocations: {allocations}")
    print()
    
    # 模拟场景3：熔断机制
    print("Scenario 3: Fuse Blowing")
    resolver.blow_fuse('curiosity', cooldown_minutes=30)
    conflicts = resolver.detect_conflicts(state, demands)
    allocations = resolver.resolve_conflicts(conflicts, demands)
    print(f"Allocations with fuse blown: {allocations}")
    print()
    
    # 打印报告
    print("="*70)
    print("CONFLICT REPORT")
    print("="*70)
    report = resolver.get_conflict_report()
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    example_usage()
