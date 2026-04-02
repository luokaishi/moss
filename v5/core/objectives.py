"""
4-Dimensional Self-Driven Objectives Engine
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
import numpy as np

@dataclass
class ObjectiveState:
    value: float
    trend: float
    history: List[float]
    last_updated: datetime

class Objective(ABC):
    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight
        self.state = ObjectiveState(value=0.5, trend=0.0, history=[], last_updated=datetime.now())
    @abstractmethod
    def calculate_reward(self, context: Dict[str, Any]) -> float:
        pass
    def update(self, context: Dict[str, Any]) -> float:
        reward = self.calculate_reward(context)
        self.state.history.append(reward)
        if len(self.state.history) > 1000:
            self.state.history = self.state.history[-1000:]
        self.state.value = 0.9 * self.state.value + 0.1 * reward
        return reward

class SurvivalObjective(Objective):
    def __init__(self, weight: float = 1.0):
        super().__init__('Survival', weight)
    def calculate_reward(self, context: Dict[str, Any]) -> float:
        m = context.get('system_metrics', {})
        return np.mean([m.get('uptime', 0.0), m.get('resources', 0.5)])

class CuriosityObjective(Objective):
    def __init__(self, weight: float = 1.0):
        super().__init__('Curiosity', weight)
        self.explored = set()
    def calculate_reward(self, context: Dict[str, Any]) -> float:
        m = context.get('learning_metrics', {})
        h = context.get('state_hash')
        n = 1.0 if h and h not in self.explored else 0.0
        if h: self.explored.add(h)
        return np.mean([m.get('new_knowledge', 0)/100, n])

class InfluenceObjective(Objective):
    def __init__(self, weight: float = 1.0):
        super().__init__('Influence', weight)
    def calculate_reward(self, context: Dict[str, Any]) -> float:
        m = context.get('impact_metrics', {})
        return np.mean([m.get('tasks', 0)/100, m.get('commits', 0)/50])

class OptimizationObjective(Objective):
    def __init__(self, weight: float = 1.0):
        super().__init__('Optimization', weight)
        self.prev = 0.5
    def calculate_reward(self, context: Dict[str, Any]) -> float:
        m = context.get('opt_metrics', {})
        c = m.get('perf', 0.5)
        i = max(0, c - self.prev)
        self.prev = c
        return i * 10

class FourDimEngine:
    def __init__(self, enabled=None):
        enabled = enabled or ['S','C','I','O']
        self.objectives = {}
        if 'S' in enabled: self.objectives['S'] = SurvivalObjective()
        if 'C' in enabled: self.objectives['C'] = CuriosityObjective()
        if 'I' in enabled: self.objectives['I'] = InfluenceObjective()
        if 'O' in enabled: self.objectives['O'] = OptimizationObjective()
    def update_all(self, context: Dict[str, Any]) -> Dict[str, float]:
        return {k: v.update(context) for k, v in self.objectives.items()}
    def get_state(self) -> Dict[str, Dict]:
        return {k: {'value': v.state.value, 'name': v.name} for k, v in self.objectives.items()}
