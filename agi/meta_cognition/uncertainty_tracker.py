"""
MOSS v7.4 - Uncertainty Tracker
不确定性追踪系统

核心功能:
- 不确定性度量
- 不确定性传播
- 不确定性可视化
- 认知不确定性管理

Author: MOSS Project
Date: 2026-04-19
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
import json


@dataclass
class UncertaintyMeasurement:
    """不确定性度量"""
    source: str              # 来源
    uncertainty_type: str    # 类型 (aleatoric/epistemic)
    value: float            # 不确定性值 (0-1)
    confidence: float       # 对不确定性估计的置信度
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'source': self.source,
            'uncertainty_type': self.uncertainty_type,
            'value': self.value,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat(),
            'context': self.context
        }


class UncertaintyTracker:
    """
    不确定性追踪器
    
    追踪和管理认知不确定性
    """
    
    def __init__(self, history_size: int = 1000):
        """
        Args:
            history_size: 历史记录大小
        """
        self.measurements: Dict[str, UncertaintyMeasurement] = {}
        self.uncertainty_history: Dict[str, deque] = {}
        self.history_size = history_size
        
        # 不确定性传播图
        self.propagation_graph: Dict[str, List[str]] = {}
        
        # 统计
        self.stats = {
            'measurements_added': 0,
            'propagations_calculated': 0,
            'high_uncertainty_alerts': 0
        }
    
    def measure_uncertainty(self, source: str, value: float,
                           uncertainty_type: str = 'epistemic',
                           confidence: float = 0.8,
                           context: Optional[Dict] = None) -> UncertaintyMeasurement:
        """
        度量不确定性
        
        Args:
            source: 不确定性来源
            value: 不确定性值 (0-1)
            uncertainty_type: 类型 (aleatoric/epistemic)
            confidence: 置信度
            context: 上下文
            
        Returns:
            不确定性度量
        """
        measurement = UncertaintyMeasurement(
            source=source,
            uncertainty_type=uncertainty_type,
            value=np.clip(value, 0, 1),
            confidence=confidence,
            context=context or {}
        )
        
        self.measurements[source] = measurement
        
        # 添加到历史
        if source not in self.uncertainty_history:
            self.uncertainty_history[source] = deque(maxlen=self.history_size)
        self.uncertainty_history[source].append(measurement)
        
        self.stats['measurements_added'] += 1
        
        # 高不确定性警告
        if value > 0.8:
            self.stats['high_uncertainty_alerts'] += 1
        
        return measurement
    
    def get_uncertainty(self, source: str) -> Optional[UncertaintyMeasurement]:
        """获取不确定性度量"""
        return self.measurements.get(source)
    
    def get_uncertainty_trend(self, source: str, window: int = 100) -> Dict:
        """
        获取不确定性趋势
        
        Args:
            source: 来源
            window: 窗口大小
            
        Returns:
            趋势统计
        """
        if source not in self.uncertainty_history:
            return {'mean': 0.0, 'trend': 0.0, 'volatility': 0.0}
        
        history = list(self.uncertainty_history[source])[-window:]
        if len(history) < 2:
            return {'mean': history[0].value if history else 0.0, 'trend': 0.0, 'volatility': 0.0}
        
        values = [m.value for m in history]
        
        # 计算趋势 (线性回归斜率)
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0] if len(values) > 1 else 0.0
        
        return {
            'mean': float(np.mean(values)),
            'std': float(np.std(values)),
            'trend': float(slope),
            'volatility': float(np.std(values) / (np.mean(values) + 1e-8)),
            'min': float(np.min(values)),
            'max': float(np.max(values))
        }
    
    def propagate_uncertainty(self, source: str, 
                             affected_sources: List[str],
                             propagation_factor: float = 0.5) -> Dict[str, float]:
        """
        传播不确定性
        
        Args:
            source: 源不确定性
            affected_sources: 受影响的来源
            propagation_factor: 传播因子
            
        Returns:
            传播后的不确定性值
        """
        if source not in self.measurements:
            return {}
        
        source_uncertainty = self.measurements[source].value
        propagated = {}
        
        for affected in affected_sources:
            # 计算传播的不确定性
            propagated_value = source_uncertainty * propagation_factor
            
            # 如果已有不确定性，合并
            if affected in self.measurements:
                existing = self.measurements[affected].value
                # 使用平方和开方合并
                combined = np.sqrt(existing**2 + propagated_value**2)
                propagated_value = min(combined, 1.0)
            
            self.measure_uncertainty(
                source=affected,
                value=propagated_value,
                uncertainty_type='propagated',
                context={'propagated_from': source, 'factor': propagation_factor}
            )
            
            propagated[affected] = propagated_value
        
        self.propagation_graph[source] = affected_sources
        self.stats['propagations_calculated'] += 1
        
        return propagated
    
    def get_total_uncertainty(self) -> float:
        """获取总不确定性"""
        if not self.measurements:
            return 0.0
        
        # 使用熵的概念计算总不确定性
        values = [m.value for m in self.measurements.values()]
        return float(np.mean(values))
    
    def get_uncertainty_breakdown(self) -> Dict[str, Dict]:
        """获取不确定性分解"""
        breakdown = {}
        
        for source, measurement in self.measurements.items():
            trend = self.get_uncertainty_trend(source, window=50)
            breakdown[source] = {
                'current': measurement.value,
                'type': measurement.uncertainty_type,
                'trend': trend['trend'],
                'volatility': trend['volatility'],
                'history_length': len(self.uncertainty_history.get(source, []))
            }
        
        return breakdown
    
    def identify_high_uncertainty_areas(self, threshold: float = 0.7) -> List[Dict]:
        """识别高不确定性区域"""
        high_uncertainty = []
        
        for source, measurement in self.measurements.items():
            if measurement.value > threshold:
                trend = self.get_uncertainty_trend(source, window=50)
                high_uncertainty.append({
                    'source': source,
                    'value': measurement.value,
                    'trend': trend['trend'],
                    'type': measurement.uncertainty_type
                })
        
        # 按不确定性值排序
        high_uncertainty.sort(key=lambda x: x['value'], reverse=True)
        return high_uncertainty
    
    def get_uncertainty_distribution(self) -> Dict:
        """获取不确定性分布"""
        if not self.measurements:
            return {'mean': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0}
        
        values = [m.value for m in self.measurements.values()]
        return {
            'mean': float(np.mean(values)),
            'std': float(np.std(values)),
            'min': float(np.min(values)),
            'max': float(np.max(values)),
            'median': float(np.median(values))
        }
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            **self.stats,
            'total_sources': len(self.measurements),
            'total_uncertainty': self.get_total_uncertainty(),
            'distribution': self.get_uncertainty_distribution(),
            'high_uncertainty_count': len(self.identify_high_uncertainty_areas())
        }


# 测试
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v7.4 - Uncertainty Tracker Test")
    print("=" * 60)
    
    # 创建不确定性追踪器
    ut = UncertaintyTracker()
    
    # 度量不确定性
    print("\n1. Measuring uncertainties...")
    ut.measure_uncertainty('perception', 0.3, 'aleatoric', context={'sensor': 'camera'})
    ut.measure_uncertainty('decision', 0.5, 'epistemic', context={'action': 'move'})
    ut.measure_uncertainty('prediction', 0.7, 'epistemic', context={'horizon': '10_steps'})
    ut.measure_uncertainty('self_model', 0.2, 'epistemic', context={'aspect': 'capability'})
    
    print(f"   Added {ut.stats['measurements_added']} measurements")
    print(f"   High uncertainty alerts: {ut.stats['high_uncertainty_alerts']}")
    
    # 添加历史数据
    print("\n2. Adding historical measurements...")
    for i in range(50):
        ut.measure_uncertainty('perception', 0.3 + np.random.randn() * 0.1)
        ut.measure_uncertainty('decision', 0.5 + np.random.randn() * 0.15)
    
    # 获取趋势
    print("\n3. Uncertainty trends:")
    for source in ['perception', 'decision']:
        trend = ut.get_uncertainty_trend(source)
        print(f"   {source}:")
        print(f"     Mean: {trend['mean']:.3f}")
        print(f"     Trend: {trend['trend']:.4f}")
        print(f"     Volatility: {trend['volatility']:.3f}")
    
    # 传播不确定性
    print("\n4. Propagating uncertainty...")
    propagated = ut.propagate_uncertainty(
        'perception',
        ['decision', 'action_selection'],
        propagation_factor=0.6
    )
    print(f"   Propagated to: {list(propagated.keys())}")
    for target, value in propagated.items():
        print(f"     {target}: {value:.3f}")
    
    # 高不确定性区域
    print("\n5. High uncertainty areas:")
    high = ut.identify_high_uncertainty_areas(threshold=0.5)
    for area in high[:3]:
        print(f"   {area['source']}: {area['value']:.3f} ({area['type']})")
    
    # 总不确定性
    print("\n6. Total uncertainty:")
    print(f"   Value: {ut.get_total_uncertainty():.3f}")
    
    # 分布
    print("\n7. Uncertainty distribution:")
    dist = ut.get_uncertainty_distribution()
    print(f"   Mean: {dist['mean']:.3f}")
    print(f"   Std: {dist['std']:.3f}")
    print(f"   Range: [{dist['min']:.3f}, {dist['max']:.3f}]")
    
    # 统计
    print("\n8. System stats:")
    stats = ut.get_stats()
    print(f"   Total sources: {stats['total_sources']}")
    print(f"   Measurements added: {stats['measurements_added']}")
    print(f"   Propagations: {stats['propagations_calculated']}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)