"""
MOSS Unified Core Package
=========================

Unified core architecture integrating v0.3-v5.1 best practices.

Usage:
    from moss.core import UnifiedMOSSAgent, MOSSConfig
    from moss.core.objectives import ObjectiveManager
    from moss.core.purpose import PurposeGenerator
    from moss.core.causal_purpose import CausalPurposeGenerator
    from moss.core.gradient_safety_guard import GradientSafetyGuard
    from moss.core.moss_mathematical_framework import MOSSMultiObjectiveFramework
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
from .causal_purpose import (
    CausalPurposeGenerator,
    CausalPurposeConfig,
    PurposeState as CausalPurposeState,
)
from .dimensions import (
    CoherenceModule,
    ValenceModule,
    OtherModelingModule,
    NormInternalizationModule
)
from .gradient_safety_guard import GradientSafetyGuard, SafetyLevel
from .moss_mathematical_framework import MOSSMultiObjectiveFramework
from .state_decision_model import StateDecisionModel, SystemState as SystemStateLevel
from .purpose_dynamics import PurposeDynamics, PurposeDynamicsTracker

__all__ = [
    # Agent
    'BaseMOSSAgent',
    'UnifiedMOSSAgent',
    'MOSSConfig',
    'ActionResult',
    'AgentState',
    # Objectives
    'BaseObjective',
    'SurvivalObjective',
    'CuriosityObjective',
    'InfluenceObjective',
    'OptimizationObjective',
    'ObjectiveManager',
    # Purpose
    'PurposeGenerator',
    'CausalPurposeGenerator',
    'CausalPurposeConfig',
    'CausalPurposeState',
    'PurposeDynamics',
    'PurposeDynamicsTracker',
    # Dimensions
    'CoherenceModule',
    'ValenceModule',
    'OtherModelingModule',
    'NormInternalizationModule',
    # Safety
    'GradientSafetyGuard',
    'SafetyLevel',
    # Math Framework
    'MOSSMultiObjectiveFramework',
    # State Decision
    'StateDecisionModel',
    'SystemStateLevel',
]
