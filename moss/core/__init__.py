"""
MOSS Unified Core Package
=========================

Unified core architecture integrating v0.3-v9.3 best practices.

Usage:
    from moss.core import UnifiedMOSSAgent, MOSSConfig
    from moss.core.objectives import ObjectiveManager
    from moss.core.purpose import PurposeGenerator
    from moss.core.causal_purpose import CausalPurposeGenerator
    from moss.core.gradient_safety_guard import GradientSafetyGuard
    from moss.core.moss_mathematical_framework import MOSSMultiObjectiveFramework

    # v9.3 Performance Engine
    from moss.core.performance_engine import PerformanceEngine, PerformanceConfig
    from moss.core.incremental_analyzer import IncrementalAnalyzer, MultiLevelCache
    from moss.core.parallel_analyzer import ParallelAnalyzer
    from moss.core.lsp_server import MossAnalysisProvider

Purpose System Note:
    - PurposeGenerator (v5.0): Behavior-derived purpose generation
      Used by UnifiedMOSSAgent by default.
    - CausalPurposeGenerator (v5.1): Independent purpose evolution
      Advanced feature for causal architecture experiments.
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

# v8.0: LLM-guided mutation components
from .llm_backend import LLMBackend, LLMConfig, LLMResponse, create_llm_backend
from .llm_mutator import LLMMutator, LLMMutationResult
from .hybrid_mutation import HybridMutationStrategy, HybridStrategyConfig
# v8.0: Local LLM deployment (HuggingFace) — optional, requires torch
try:
    from .local_llm_backend import LocalLLMBackend, LocalModelConfig, create_local_backend_for_moss
except ImportError:
    # torch/transformers not installed, LocalLLMBackend unavailable
    LocalLLMBackend = None
    LocalModelConfig = None
    create_local_backend_for_moss = None

# v9.2: Cross-file refactoring
try:
    from .cross_file_refactor import CrossFileRefactorEngine
    from .semantic_refactor import SemanticRefactorEngine
    from .split_operations import SplitOperations
    from .move_operations import MoveOperations
except ImportError:
    pass

# v9.3: Performance & Ecosystem
try:
    from .incremental_analyzer import IncrementalAnalyzer, MultiLevelCache, PerformanceBenchmark
    from .parallel_analyzer import ParallelAnalyzer, IncrementalParallelAnalyzer, ParallelBenchmark
    from .performance_engine import PerformanceEngine, PerformanceConfig
    from .lsp_server import MossAnalysisProvider, LSPProtocolHandler
    from .ml_recommender import RefactoringRecommender, CodeFeatures, RefactoringRecommendation
    from .pattern_learner import PatternLearningEngine, ProjectProfile, CodePattern, AntiPattern
    from .team_collaboration import TeamManager, TeamConfig, QualityDashboard
except ImportError:
    IncrementalAnalyzer = None
    MultiLevelCache = None
    PerformanceBenchmark = None
    ParallelAnalyzer = None
    IncrementalParallelAnalyzer = None
    ParallelBenchmark = None
    PerformanceEngine = None
    PerformanceConfig = None
    MossAnalysisProvider = None
    LSPProtocolHandler = None
    RefactoringRecommender = None
    CodeFeatures = None
    RefactoringRecommendation = None
    PatternLearningEngine = None
    ProjectProfile = None
    CodePattern = None
    AntiPattern = None
    TeamManager = None
    TeamConfig = None
    QualityDashboard = None

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
    # v8.0 LLM Mutation
    'LLMBackend',
    'LLMConfig',
    'LLMResponse',
    'create_llm_backend',
    'LLMMutator',
    'LLMMutationResult',
    'HybridMutationStrategy',
    'HybridStrategyConfig',
    # v8.0 Local LLM
    'LocalLLMBackend',
    'LocalModelConfig',
    'create_local_backend_for_moss',
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
    # v9.3 Performance & Ecosystem
    'IncrementalAnalyzer',
    'MultiLevelCache',
    'PerformanceBenchmark',
    'ParallelAnalyzer',
    'IncrementalParallelAnalyzer',
    'ParallelBenchmark',
    'PerformanceEngine',
    'PerformanceConfig',
    'MossAnalysisProvider',
    'LSPProtocolHandler',
    # v9.3 ML Features
    'RefactoringRecommender',
    'CodeFeatures',
    'RefactoringRecommendation',
    'PatternLearningEngine',
    'ProjectProfile',
    'CodePattern',
    'AntiPattern',
    # v9.3 Enterprise
    'TeamManager',
    'TeamConfig',
    'QualityDashboard',
]
