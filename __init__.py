"""
MOSS: Multi-Objective Self-Driven System
自主涌现驱动力 AGI Agent 框架
"""

__version__ = "5.4.0"
__author__ = "Cash, Fuxi"

from moss.agi.agent import AGIAgent
from moss.agi.drive_manager import DriveManager, Drive
from moss.agi.memory_engine import MemoryEngine
from moss.agi.environment import RealEnvironment, EnvState
from moss.agi.behavior_tracker import BehaviorTracker
from moss.agi.emergence_detector import EmergenceDetector, EmergentDrive

__all__ = [
    'AGIAgent', 'DriveManager', 'Drive', 'MemoryEngine',
    'RealEnvironment', 'EnvState', 'BehaviorTracker',
    'EmergenceDetector', 'EmergentDrive',
]
