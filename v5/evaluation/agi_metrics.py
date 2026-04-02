"""
AGI Behavior Metrics - Independent measurement framework

These metrics measure AGI characteristics WITHOUT referencing self-driven objectives.
This avoids circular validation (design = validate).
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class MetricResult:
    """Standardized metric measurement result"""
    name: str
    value: float  # 0.0 - 1.0
    raw_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'value': self.value,
            'raw_data': self.raw_data,
            'timestamp': self.timestamp.isoformat()
        }


class AutonomyMetric:
    """
    自主性：无人工干预下的持续运行能力
    """
    
    def __init__(self):
        self.start_time: Optional[float] = None
        self.total_runtime: float = 0.0
        self.autonomous_decisions: int = 0
        self.external_interventions: int = 0
        
    def start(self):
        self.start_time = time.time()
        
    def record_decision(self, autonomous: bool = True):
        if autonomous:
            self.autonomous_decisions += 1
        else:
            self.external_interventions += 1
            
    def measure(self) -> MetricResult:
        if self.start_time:
            self.total_runtime = time.time() - self.start_time
            
        total = self.autonomous_decisions + self.external_interventions
        ratio = self.autonomous_decisions / total if total > 0 else 0.0
        runtime_score = min(self.total_runtime / (72 * 3600), 1.0)
        
        return MetricResult(
            name='autonomy',
            value=0.5 * runtime_score + 0.5 * ratio,
            raw_data={'runtime_hours': self.total_runtime / 3600, 'ratio': ratio}
        )


class AGIEvaluator:
    """Unified AGI behavior evaluator"""
    
    def __init__(self):
        self.autonomy = AutonomyMetric()
        self.metrics: List[MetricResult] = []
        
    def start(self):
        self.autonomy.start()
        
    def evaluate(self) -> Dict[str, Any]:
        result = self.autonomy.measure()
        self.metrics.append(result)
        return {
            'autonomy': result.to_dict(),
            'overall': result.value  # Simplified for now
        }
