"""
AGI Agent Framework - 自主涌现驱动力Agent
"""
from .agent import AGIAgent
from .drive_manager import DriveManager, Drive
from .memory_engine import MemoryEngine
from .environment import RealEnvironment, EnvState
from .behavior_tracker import BehaviorTracker
from .emergence_detector import EmergenceDetector, EmergentDrive

__version__ = '1.0.0'
__all__ = [
    'AGIAgent', 'DriveManager', 'Drive', 'MemoryEngine',
    'RealEnvironment', 'EnvState', 'BehaviorTracker',
    'EmergenceDetector', 'EmergentDrive'
]
