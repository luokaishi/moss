"""
MOSS: Multi-Objective Self-Driven System
"""

__version__ = "0.1.0"
__author__ = "Cash, Fuxi"

from moss.agents.moss_agent import MOSSAgent
from moss.core.objectives import (
    SystemState,
    SurvivalModule,
    CuriosityModule,
    InfluenceModule,
    OptimizationModule
)

__all__ = [
    'MOSSAgent',
    'SystemState',
    'SurvivalModule',
    'CuriosityModule',
    'InfluenceModule',
    'OptimizationModule'
]
