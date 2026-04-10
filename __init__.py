"""
MOSS: Multi-Objective Self-Driven System
自主涌现驱动力 AGI Agent 框架
"""

__version__ = "5.4.0"
__author__ = "Cash, Fuxi"

from agi.agent import AGIAgent
from agi.drive_manager import DriveManager, Drive
from agi.memory_engine import MemoryEngine
from agi.environment import RealEnvironment, EnvState
from agi.behavior_tracker import BehaviorTracker
from agi.emergence_detector import EmergenceDetector, EmergentDrive

__all__ = [
    'AGIAgent', 'DriveManager', 'Drive', 'MemoryEngine',
    'RealEnvironment', 'EnvState', 'BehaviorTracker',
    'EmergenceDetector', 'EmergentDrive',
]
