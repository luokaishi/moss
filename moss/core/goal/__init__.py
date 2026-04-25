"""
Goal System - 目标系统 (第6层)

目标 = 在长时间尺度上保持稳定，并对行为产生持续约束的内部状态函数

核心组件：
- TrajectoryBuffer: 轨迹缓冲区
- GoalExtractor: 目标提取器
- GoalEvaluator: 目标评估器
- GoalSystem: 目标系统主控
"""

from .goal_system import GoalSystem, Goal

__all__ = ['GoalSystem', 'Goal']
