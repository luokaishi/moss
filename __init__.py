"""
MOSS: Multi-Objective Self-Driven System
========================================

A framework for AI Agent self-driven evolution through parallel intrinsic objectives.

Usage:
    from moss import UnifiedMOSSAgent, MOSSConfig
    from moss import CausalPurposeGenerator, GradientSafetyGuard
"""

__version__ = "8.0.0-dev"
__author__ = "Cash, Fuxi"

# Re-export from the actual moss.core package
from moss.core import (
    UnifiedMOSSAgent,
    MOSSConfig,
    CausalPurposeGenerator,
    CausalPurposeConfig,
    GradientSafetyGuard,
    SafetyLevel,
    MOSSMultiObjectiveFramework,
    StateDecisionModel,
    PurposeDynamics,
    PurposeDynamicsTracker,
    # v8.0: LLM-guided mutation
    LLMConfig,
    LLMMutator,
    LLMMutationResult,
    HybridMutationStrategy,
    HybridStrategyConfig,
)

__all__ = [
    'UnifiedMOSSAgent',
    'MOSSConfig',
    'CausalPurposeGenerator',
    'CausalPurposeConfig',
    'GradientSafetyGuard',
    'SafetyLevel',
    'MOSSMultiObjectiveFramework',
    'StateDecisionModel',
    'PurposeDynamics',
    'PurposeDynamicsTracker',
    # v8.0: LLM-guided mutation
    'LLMConfig',
    'LLMMutator',
    'LLMMutationResult',
    'HybridMutationStrategy',
    'HybridStrategyConfig',
]
