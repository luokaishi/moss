"""
MOSS Unified Core Package
=========================

统一的核心架构模块

Usage:
    from moss.core import UnifiedMOSSAgent, MOSSConfig
    from moss.core.objectives import ObjectiveManager
    from moss.core.purpose import PurposeGenerator
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

from .purpose import PurposeGenerator
from .dimensions import (
    CoherenceModule,
    ValenceModule,
    OtherModelingModule,
    NormInternalizationModule
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
    'PurposeGenerator',
    'CoherenceModule',
    'ValenceModule',
    'OtherModelingModule',
    'NormInternalizationModule',
]
