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
    UnifiedMOSSAgentV2,
    AgentMode,
    MOSSConfig,
    ActionResult,
    AgentState
)

# v8.6 Components (merged from mves)
from .agi_agent import AGIAgent
from .drive_manager import DriveManager, Drive
from .drive_competition import DriveCompetition
from .drive_weight_cap import DriveWeightCap
from .memory_engine import MemoryEngine
from .behavior_tracker import BehaviorTracker
from .emergence_detector import EmergenceDetector
from .environment import RealEnvironment, EnvState
from .genetic_programmer import GeneticProgrammer
from .genetic_programmer_v2 import GeneticProgrammerV2
from .genetic_programmer_v3 import GeneticProgrammerV3
from .task_aware_agent import TaskAwareAgent
from .task_discovery import TaskDiscovery
from .multi_agent_coordinator import MultiAgentCoordinator
from .adaptive_action_selector import AdaptiveActionSelector
from .llm_integration_mves import AGILLMIntegrator
from .event_driven_purpose import EventDrivenPurpose
from .auto_recovery import AutoRecovery
from .monitoring_dashboard import MonitoringDashboard
from .real_world_bridge import MVESRealWorldBridge
from .llm_cost_controller import LLMCostController, CostBudget
from .statistical_validator import StatisticalValidator, ValidationConfig

# Phase 4: P2 Meta-learning components
from .meta_learner import MetaLearner
from .meta_sme import MetaSME
from .meta_sme_v2 import MetaSMEv2
from .meta_sme_integration import MetaSMEIntegration
from .meta_sme_optimizer import MetaSMEOptimizer

# Phase 4: P2 Performance & Optimization
from .performance_optimizer import PerformanceOptimizer
from .generalization_optimizer import GeneralizationOptimizer
from .intervention_validator import InterventionValidator
from .reward_aligner import RewardAligner

# Phase 4: P2 Training infrastructure
from .distributed_trainer import DistributedTrainer
from .gpu_trainer import GPUTrainer
from .model_compression import ModelCompression

# Phase 4: P2 Advanced agents
from .self_modifying_agent import SelfModifyingAgent
from .seven_layer_agent import SevenLayerAgent

# Phase 4: P2 TextWorld
from .textworld_enhanced_understanding import TextWorldEnhancedUnderstanding
from .textworld_memory import TextWorldMemory
from .textworld_rl_agent import TextWorldRLAgent
from .textworld_rl_agent_v65 import TextWorldRLAgentV65
from .textworld_understanding import TextWorldUnderstanding

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

# v9.4: Quality & Plugin Architecture
try:
    from .exceptions import (
        MossError, AnalysisError, ParseError, DependencyError, CacheError, FileWatchError,
        RefactoringError, UnsafeRefactoringError, ImpactAnalysisError, RollbackError, CrossFileError,
        LSPError, ProtocolError, TransportError, ServerStartError,
        ConfigError, ValidationError, MigrationError,
        PluginError, PluginLoadError, PluginConflictError,
    )
    from .plugin_system import (
        MossPlugin, PluginManager, PluginContext, PluginInfo,
        HookType, HookPriority,
        GitPlugin, CoveragePlugin, TypeCheckPlugin,
    )
    from .config_manager import (
        ConfigManager, MossProjectConfig,
        AnalysisConfig, PerformanceConfig as V94PerformanceConfig,
        LSPConfig, MLConfig, TeamConfig as V94TeamConfig, LoggingConfig,
    )
except ImportError:
    MossError = None
    AnalysisError = None
    ParseError = None
    DependencyError = None
    CacheError = None
    FileWatchError = None
    RefactoringError = None
    UnsafeRefactoringError = None
    ImpactAnalysisError = None
    RollbackError = None
    CrossFileError = None
    LSPError = None
    ProtocolError = None
    TransportError = None
    ServerStartError = None
    ConfigError = None
    ValidationError = None
    MigrationError = None
    PluginError = None
    PluginLoadError = None
    PluginConflictError = None
    MossPlugin = None
    PluginManager = None
    PluginContext = None
    PluginInfo = None
    HookType = None
    HookPriority = None
    GitPlugin = None
    CoveragePlugin = None
    TypeCheckPlugin = None
    ConfigManager = None
    MossProjectConfig = None
    V94PerformanceConfig = None
    LSPConfig = None
    MLConfig = None
    V94TeamConfig = None
    LoggingConfig = None

__all__ = [
    # Agent (v9)
    'BaseMOSSAgent',
    'UnifiedMOSSAgent',
    'UnifiedMOSSAgentV2',
    'AgentMode',
    'MOSSConfig',
    'ActionResult',
    'AgentState',
    # Agent (v8.6)
    'AGIAgent',
    # Drive
    'DriveManager',
    'Drive',
    'DriveCompetition',
    'DriveWeightCap',
    # Environment
    'RealEnvironment',
    'EnvState',
    # Memory & Behavior
    'MemoryEngine',
    'BehaviorTracker',
    'EmergenceDetector',
    # GP
    'GeneticProgrammer',
    'GeneticProgrammerV2',
    'GeneticProgrammerV3',
    # Task
    'TaskAwareAgent',
    'TaskDiscovery',
    # Multi-Agent
    'MultiAgentCoordinator',
    # Action
    'AdaptiveActionSelector',
    # LLM
    'AGILLMIntegrator',
    # Event & Recovery
    'EventDrivenPurpose',
    'AutoRecovery',
    # Monitoring
    'MonitoringDashboard',
    # Real World
    'MVESRealWorldBridge',
    # Cost Control
    'LLMCostController',
    'CostBudget',
    # Statistical
    'StatisticalValidator',
    'ValidationConfig',
    # Phase 4: Meta-learning
    'MetaLearner',
    'MetaSME',
    'MetaSMEv2',
    'MetaSMEIntegration',
    'MetaSMEOptimizer',
    # Phase 4: Performance & Optimization
    'PerformanceOptimizer',
    'GeneralizationOptimizer',
    'InterventionValidator',
    'RewardAligner',
    # Phase 4: Training infrastructure
    'DistributedTrainer',
    'GPUTrainer',
    'ModelCompression',
    # Phase 4: Advanced agents
    'SelfModifyingAgent',
    'SevenLayerAgent',
    # Phase 4: TextWorld
    'TextWorldEnhancedUnderstanding',
    'TextWorldMemory',
    'TextWorldRLAgent',
    'TextWorldRLAgentV65',
    'TextWorldUnderstanding',
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
    # v9.4 Exception Hierarchy
    'MossError', 'AnalysisError', 'ParseError', 'DependencyError', 'CacheError', 'FileWatchError',
    'RefactoringError', 'UnsafeRefactoringError', 'ImpactAnalysisError', 'RollbackError', 'CrossFileError',
    'LSPError', 'ProtocolError', 'TransportError', 'ServerStartError',
    'ConfigError', 'ValidationError', 'MigrationError',
    'PluginError', 'PluginLoadError', 'PluginConflictError',
    # v9.4 Plugin System
    'MossPlugin', 'PluginManager', 'PluginContext', 'PluginInfo',
    'HookType', 'HookPriority',
    'GitPlugin', 'CoveragePlugin', 'TypeCheckPlugin',
    # v9.4 Config Management
    'ConfigManager', 'MossProjectConfig',
    'V94PerformanceConfig', 'LSPConfig', 'MLConfig', 'V94TeamConfig', 'LoggingConfig',
]
