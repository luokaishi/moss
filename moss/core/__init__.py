"""
MOSS Unified Core Package
=========================

统一的核心架构模块

Usage:
    from moss.core import UnifiedMOSSAgent, MOSSConfig
    from moss.core.objectives import ObjectiveManager
"""

from .unified_agent import (
    BaseMOSSAgent,
    UnifiedMOSSAgent,
    MOSSConfig,
    ActionResult,
    AgentState
)

from .objectives import (
    BaseObjective,
    SurvivalObjective,
    CuriosityObjective,
    InfluenceObjective,
    OptimizationObjective,
    ObjectiveManager
)

__all__ = [
    'BaseMOSSAgent',
    'UnifiedMOSSAgent',
    'MOSSConfig',
    'ActionResult',
    'AgentState',
    'BaseObjective',
    'SurvivalObjective',
    'CuriosityObjective',
    'InfluenceObjective',
    'OptimizationObjective',
    'ObjectiveManager',
]
