"""
MOSS: Multi-Objective Self-Driven System
========================================

A framework for AI Agent self-driven evolution through parallel intrinsic objectives.

Usage:
    from moss import UnifiedMOSSAgent, MOSSConfig
    from moss import CausalPurposeGenerator, GradientSafetyGuard
"""

__version__ = "7.1.0-dev"
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
]
