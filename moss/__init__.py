"""
MOSS: Multi-Objective Self-Driven System
========================================

A framework for AI Agent self-driven evolution through parallel intrinsic objectives.

Core Modules:
- objectives: Four intrinsic objectives (Survival, Curiosity, Influence, Optimization)
- unified_agent: Unified agent architecture with 9-dimensional system
- causal_purpose: Causal Purpose Architecture (v5.1) - independent purpose evolution
- purpose_dynamics: Mathematical Purpose dynamics with attractor tracking
- gradient_safety_guard: 5-level gradient safety mechanism
- moss_mathematical_framework: Unified loss function and convergence proofs
- dimensions: Social dimensions (D5-D8): Coherence, Valence, OtherModeling, NormInternalization
"""

__version__ = "9.6.0"
__author__ = "MOSS Team"

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
