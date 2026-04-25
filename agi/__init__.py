"""
AGI 兼容层 (Phase 3)
===================

提供向后兼容的导入重定向，将 agi.* 映射到 moss.core.*

Usage:
    # 旧代码 (仍然可用)
    from agi import AGIAgent
    from agi.drive_manager import DriveManager
    
    # 新代码 (推荐)
    from moss.core import AGIAgent
    from moss.core.drive_manager import DriveManager

Note:
    此模块将在 v10.0 中移除，请尽快迁移到 moss.core
"""

import warnings
import sys
from typing import Any

# 发出弃用警告
warnings.warn(
    "The 'agi' module is deprecated and will be removed in v10.0. "
    "Please use 'moss.core' instead. "
    "See: https://github.com/luokaishi/moss/blob/main/docs/MIGRATION.md",
    DeprecationWarning,
    stacklevel=2
)

# 从 moss.core 导入所有内容
from moss.core import (
    # Agent
    BaseMOSSAgent,
    UnifiedMOSSAgent,
    UnifiedMOSSAgentV2,
    MOSSConfig,
    ActionResult,
    AgentState,
    # v8.6 Agent
    AGIAgent,
    # Drive
    DriveManager,
    Drive,
    DriveCompetition,
    DriveWeightCap,
    # Environment
    RealEnvironment,
    EnvState,
    # Memory & Behavior
    MemoryEngine,
    BehaviorTracker,
    EmergenceDetector,
    # GP
    GeneticProgrammer,
    GeneticProgrammerV2,
    GeneticProgrammerV3,
    # Task
    TaskAwareAgent,
    TaskDiscovery,
    # Multi-Agent
    MultiAgentCoordinator,
    # Action
    AdaptiveActionSelector,
    # LLM
    LLMBackend,
    LLMConfig,
    LLMMutator,
    HybridMutationStrategy,
    AGILLMIntegrator,
    # Event & Recovery
    EventDrivenPurpose,
    AutoRecovery,
    # Monitoring
    MonitoringDashboard,
    # Real World
    MVESRealWorldBridge,
    # Cost Control
    LLMCostController,
    CostBudget,
    # Statistical
    StatisticalValidator,
    ValidationConfig,
)

# 导出列表
__all__ = [
    # Agent
    'BaseMOSSAgent',
    'UnifiedMOSSAgent',
    'UnifiedMOSSAgentV2',
    'MOSSConfig',
    'ActionResult',
    'AgentState',
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
    'LLMBackend',
    'LLMConfig',
    'LLMMutator',
    'HybridMutationStrategy',
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
]


def __getattr__(name: str) -> Any:
    """
    动态属性访问，处理未显式导入的模块
    
    例如: from agi.genetic_programmer import GeneticProgrammer
    """
    # 尝试从 moss.core 获取
    try:
        import moss.core
        return getattr(moss.core, name)
    except AttributeError:
        pass
    
    # 尝试从 moss.core 子模块获取
    try:
        module = __import__(f'moss.core.{name}', fromlist=[name])
        return module
    except ImportError:
        pass
    
    raise AttributeError(f"module 'agi' has no attribute '{name}'")


# 版本信息
__version__ = "9.5.0"
__deprecated__ = True
__migration_guide__ = "https://github.com/luokaishi/moss/blob/main/docs/MIGRATION.md"
