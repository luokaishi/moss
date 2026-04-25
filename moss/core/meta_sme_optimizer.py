"""
MOSS v7.3 - Meta-SME Performance Optimizer
Meta-SME 性能优化器

优化目标:
- 减少运行时开销 (2.4x → 1.2x)
- 批量检查机制
- 异步性能记录
- 缓存优化

Author: MOSS Project
Date: 2026-04-19
"""

import numpy as np
from typing import Dict, List, Optional, Callable
from collections import deque
import time
from functools import lru_cache


class PerformanceBuffer:
    """
    高性能性能缓冲区
    
    批量记录和计算性能指标
    """
    
    def __init__(self, max_size: int = 1000, batch_size: int = 100):
        self.max_size = max_size
        self.batch_size = batch_size
        self.buffer = deque(maxlen=max_size)
        self.batch_buffer = []
        self.cached_stats = {}
        self.cache_valid = False
    
    def add(self, value: float):
        """添加性能值 (批量处理)"""
        self.batch_buffer.append(value)
        self.cache_valid = False
        
        # 批量刷新
        if len(self.batch_buffer) >= self.batch_size:
            self._flush_batch()
    
    def _flush_batch(self):
        """刷新批量缓冲区"""
        self.buffer.extend(self.batch_buffer)
        self.batch_buffer = []
    
    def get_stats(self) -> Dict:
        """获取统计 (带缓存)"""
        if self.cache_valid and self.cached_stats:
            return self.cached_stats.copy()
        
        # 确保所有数据已刷新
        self._flush_batch()
        
        if not self.buffer:
            return {'mean': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0, 'count': 0}
        
        data = np.array(self.buffer)
        self.cached_stats = {
            'mean': float(np.mean(data)),
            'std': float(np.std(data)),
            'min': float(np.min(data)),
            'max': float(np.max(data)),
            'count': len(data)
        }
        self.cache_valid = True
        
        return self.cached_stats.copy()
    
    def get_recent(self, n: int = 100) -> List[float]:
        """获取最近的 n 个值"""
        self._flush_batch()
        return list(self.buffer)[-n:]


class SmartTrigger:
    """
    智能触发器
    
    基于趋势和冷却期的智能触发机制
    """
    
    def __init__(self,
                 trend_window: int = 50,
                 trend_threshold: float = 0.05,
                 cooldown_period: int = 100,
                 min_history: int = 100):
        self.trend_window = trend_window
        self.trend_threshold = trend_threshold
        self.cooldown_period = cooldown_period
        self.min_history = min_history
        
        self.performance_history = deque(maxlen=1000)
        self.steps_since_last_trigger = 0
        self.trigger_count = 0
        
        # 自适应阈值
        self.adaptive_threshold = trend_threshold
        self.threshold_history = deque(maxlen=100)
    
    def record(self, performance: float):
        """记录性能"""
        self.performance_history.append(performance)
        self.steps_since_last_trigger += 1
    
    def should_trigger(self) -> bool:
        """是否应该触发"""
        # 检查最小历史
        if len(self.performance_history) < self.min_history:
            return False
        
        # 检查冷却期
        if self.steps_since_last_trigger < self.cooldown_period:
            return False
        
        # 计算趋势
        trend = self._calculate_trend()
        
        # 检查阈值
        if abs(trend) > self.adaptive_threshold:
            self._trigger()
            return True
        
        return False
    
    def _calculate_trend(self) -> float:
        """计算性能趋势"""
        if len(self.performance_history) < self.trend_window * 2:
            return 0.0
        
        recent = list(self.performance_history)[-self.trend_window:]
        older = list(self.performance_history)[-(self.trend_window*2):-self.trend_window]
        
        recent_mean = np.mean(recent)
        older_mean = np.mean(older)
        
        # 相对变化
        if older_mean != 0:
            return (recent_mean - older_mean) / abs(older_mean)
        return 0.0
    
    def _trigger(self):
        """触发处理"""
        self.steps_since_last_trigger = 0
        self.trigger_count += 1
        
        # 更新自适应阈值
        self.threshold_history.append(self.adaptive_threshold)
        if len(self.threshold_history) >= 10:
            # 根据触发频率调整阈值
            if self.trigger_count > 10:
                self.adaptive_threshold *= 1.1  # 增加阈值
            elif self.trigger_count < 3:
                self.adaptive_threshold *= 0.9  # 降低阈值
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            'trigger_count': self.trigger_count,
            'steps_since_last': self.steps_since_last_trigger,
            'adaptive_threshold': self.adaptive_threshold,
            'history_length': len(self.performance_history)
        }


class CachedCalculator:
    """
    缓存计算器
    
    缓存常用计算结果
    """
    
    def __init__(self, cache_size: int = 128):
        self.cache_size = cache_size
        self._cache = {}
        self._access_count = {}
    
    @lru_cache(maxsize=128)
    def calculate_trend(self, values_tuple: tuple) -> float:
        """计算趋势 (缓存)"""
        values = np.array(values_tuple)
        if len(values) < 2:
            return 0.0
        
        # 线性回归斜率
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        return float(slope)
    
    def calculate_volatility(self, values: List[float]) -> float:
        """计算波动率"""
        if len(values) < 2:
            return 0.0
        return float(np.std(values) / (np.mean(values) + 1e-8))
    
    def clear_cache(self):
        """清除缓存"""
        self.calculate_trend.cache_clear()


class OptimizedMetaSME:
    """
    优化的 Meta-SME
    
    集成所有优化组件
    """
    
    def __init__(self,
                 enable_auto_modify: bool = False,
                 require_human_approval: bool = True,
                 batch_size: int = 100,
                 cooldown_period: int = 100):
        self.enable_auto_modify = enable_auto_modify
        self.require_human_approval = require_human_approval
        
        # 优化组件
        self.performance_buffer = PerformanceBuffer(batch_size=batch_size)
        self.smart_trigger = SmartTrigger(cooldown_period=cooldown_period)
        self.calculator = CachedCalculator()
        
        # 统计
        self.stats = {
            'records_added': 0,
            'triggers': 0,
            'cache_hits': 0,
            'runtime_optimized': True
        }
    
    def record_performance(self, performance: float):
        """记录性能 (优化版)"""
        # 批量添加
        self.performance_buffer.add(performance)
        
        # 智能触发记录
        self.smart_trigger.record(performance)
        
        self.stats['records_added'] += 1
    
    def should_generate_proposal(self) -> bool:
        """是否应该生成提案 (优化版)"""
        return self.smart_trigger.should_trigger()
    
    def get_performance_stats(self) -> Dict:
        """获取性能统计"""
        return self.performance_buffer.get_stats()
    
    def get_trigger_stats(self) -> Dict:
        """获取触发统计"""
        return self.smart_trigger.get_stats()
    
    def get_optimization_stats(self) -> Dict:
        """获取优化统计"""
        return {
            **self.stats,
            'buffer_stats': self.performance_buffer.get_stats(),
            'trigger_stats': self.smart_trigger.get_stats()
        }


# 性能测试
if __name__ == '__main__':
    print("=" * 60)
    print("Meta-SME Performance Optimizer Test")
    print("=" * 60)
    
    # 测试优化版
    print("\n1. Testing OptimizedMetaSME...")
    opt_sme = OptimizedMetaSME(
        enable_auto_modify=True,
        cooldown_period=50
    )
    
    import time
    start = time.time()
    
    # 模拟 10K 记录
    triggers = 0
    for i in range(10000):
        perf = 0.5 + np.sin(i / 100) * 0.2 + np.random.randn() * 0.05
        opt_sme.record_performance(perf)
        if opt_sme.should_generate_proposal():
            triggers += 1
    
    elapsed = time.time() - start
    
    print(f"   Records: 10,000")
    print(f"   Time: {elapsed:.3f}s")
    print(f"   Throughput: {10000/elapsed:.0f} records/s")
    print(f"   Triggers: {triggers}")
    
    # 统计
    stats = opt_sme.get_optimization_stats()
    print(f"\n2. Optimization Stats:")
    print(f"   Records added: {stats['records_added']}")
    print(f"   Trigger count: {stats['trigger_stats']['trigger_count']}")
    print(f"   Adaptive threshold: {stats['trigger_stats']['adaptive_threshold']:.4f}")
    
    perf_stats = stats['buffer_stats']
    print(f"\n3. Performance Stats:")
    print(f"   Mean: {perf_stats['mean']:.4f}")
    print(f"   Std: {perf_stats['std']:.4f}")
    print(f"   Count: {perf_stats['count']}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)