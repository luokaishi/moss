"""
MOSS v5.0 "Causal" - Core Module

4维自驱力引擎：Survival / Curiosity / Influence / Optimization

核心命题：自驱力是AGI的必要条件（因果验证框架）
"""

__version__ = "5.0.0"
__codename__ = "Causal"

from .objectives import (
    SurvivalObjective,
    CuriosityObjective,
    InfluenceObjective,
    OptimizationObjective,
    FourDimEngine
)

from .agi_metrics import (
    AutonomyMetric,
    AdaptabilityMetric,
    CreativityMetric,
    GeneralizationMetric,
    PersistenceMetric,
    AGIEvaluator
)

from .ablation_runner import AblationRunner
from .causal_validator import CausalValidator

__all__ = [
    # Core objectives
    'SurvivalObjective',
    'CuriosityObjective', 
    'InfluenceObjective',
    'OptimizationObjective',
    'FourDimEngine',
    # AGI metrics
    'AutonomyMetric',
    'AdaptabilityMetric',
    'CreativityMetric',
    'GeneralizationMetric',
    'PersistenceMetric',
    'AGIEvaluator',
    # Validation
    'AblationRunner',
    'CausalValidator'
]
