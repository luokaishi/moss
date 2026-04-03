#!/usr/bin/env python3
"""
MOSS v6.1 - Performance Optimizer
性能优化器

核心功能:
- 缓存优化
- 并发处理
- 内存管理
- 性能监控

Author: MOSS Project
Date: 2026-04-03
Version: 6.1.0-dev
"""

import time
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from collections import OrderedDict
import functools


@dataclass
class PerformanceMetrics:
    """性能指标"""
    response_time: float = 0.0
    throughput: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    cache_hit_rate: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'response_time': self.response_time,
            'throughput': self.throughput,
            'memory_usage': self.memory_usage,
            'cpu_usage': self.cpu_usage,
            'cache_hit_rate': self.cache_hit_rate
        }


class LRUCache:
    """
    LRU 缓存
    
    优化的缓存实现
    """
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()
        self.lock = threading.Lock()
        
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
                self.stats['hits'] += 1
                return self.cache[key]
            else:
                self.stats['misses'] += 1
                return None
    
    def set(self, key: str, value: Any):
        """设置缓存"""
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            else:
                if len(self.cache) >= self.max_size:
                    self.cache.popitem(last=False)
                    self.stats['evictions'] += 1
                self.cache[key] = value
    
    def get_hit_rate(self) -> float:
        """获取命中率"""
        total = self.stats['hits'] + self.stats['misses']
        return self.stats['hits'] / max(total, 1)


class ConcurrentExecutor:
    """
    并发执行器
    
    提供并发任务执行能力
    """
    
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.lock = threading.Lock()
        self.active_workers = 0
        
        self.stats = {
            'tasks_submitted': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'avg_execution_time': 0.0
        }
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        执行任务
        
        Args:
            func: 执行函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            执行结果
        """
        with self.lock:
            if self.active_workers >= self.max_workers:
                # 等待可用 worker
                time.sleep(0.1)
                return self.execute(func, *args, **kwargs)
            
            self.active_workers += 1
            self.stats['tasks_submitted'] += 1
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            
            elapsed = time.time() - start_time
            self._update_stats(True, elapsed)
            
            return result
        except Exception as e:
            self._update_stats(False, time.time() - start_time)
            raise
        finally:
            with self.lock:
                self.active_workers -= 1
    
    def _update_stats(self, success: bool, elapsed: float):
        """更新统计"""
        if success:
            self.stats['tasks_completed'] += 1
        else:
            self.stats['tasks_failed'] += 1
        
        # 更新平均执行时间
        n = self.stats['tasks_completed'] + self.stats['tasks_failed']
        old_avg = self.stats['avg_execution_time']
        self.stats['avg_execution_time'] = (old_avg * (n - 1) + elapsed) / n


class MemoryManager:
    """
    内存管理器
    
    优化内存使用
    """
    
    def __init__(self, max_memory_mb: int = 1024):
        self.max_memory_mb = max_memory_mb
        self.allocated_memory: Dict[str, int] = {}
        
        self.stats = {
            'current_usage_mb': 0.0,
            'peak_usage_mb': 0.0,
            'allocations': 0,
            'deallocations': 0
        }
    
    def allocate(self, key: str, size_mb: float) -> bool:
        """
        分配内存
        
        Args:
            key: 内存键
            size_mb: 大小 (MB)
            
        Returns:
            是否成功
        """
        if self.stats['current_usage_mb'] + size_mb > self.max_memory_mb:
            return False
        
        self.allocated_memory[key] = int(size_mb)
        self.stats['current_usage_mb'] += size_mb
        self.stats['allocations'] += 1
        
        if self.stats['current_usage_mb'] > self.stats['peak_usage_mb']:
            self.stats['peak_usage_mb'] = self.stats['current_usage_mb']
        
        return True
    
    def deallocate(self, key: str) -> bool:
        """
        释放内存
        
        Args:
            key: 内存键
            
        Returns:
            是否成功
        """
        if key not in self.allocated_memory:
            return False
        
        size = self.allocated_memory[key]
        del self.allocated_memory[key]
        self.stats['current_usage_mb'] -= size
        self.stats['deallocations'] += 1
        
        return True
    
    def get_usage(self) -> Dict:
        """获取内存使用情况"""
        return {
            'current_mb': self.stats['current_usage_mb'],
            'peak_mb': self.stats['peak_usage_mb'],
            'max_mb': self.max_memory_mb,
            'usage_percent': (self.stats['current_usage_mb'] / self.max_memory_mb) * 100
        }


class PerformanceOptimizer:
    """
    性能优化器
    
    统一管理性能优化
    """
    
    def __init__(self, config: Optional[Dict] = None):
        config = config or {}
        
        # 初始化组件
        self.cache = LRUCache(max_size=config.get('cache_size', 1000))
        self.executor = ConcurrentExecutor(max_workers=config.get('max_workers', 10))
        self.memory_manager = MemoryManager(max_memory_mb=config.get('max_memory', 1024))
        
        # 性能监控
        self.metrics_history: List[PerformanceMetrics] = []
        
        self.stats = {
            'optimizations_applied': 0,
            'performance_improvement': 0.0
        }
    
    def cached(self, key_prefix: str = ''):
        """
        缓存装饰器
        
        Args:
            key_prefix: 缓存键前缀
            
        Returns:
            装饰器函数
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # 生成缓存键
                cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
                
                # 尝试从缓存获取
                cached_result = self.cache.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # 执行函数
                result = func(*args, **kwargs)
                
                # 存入缓存
                self.cache.set(cache_key, result)
                
                return result
            
            return wrapper
        return decorator
    
    def parallel_map(self, func: Callable, items: List[Any]) -> List[Any]:
        """
        并行映射
        
        Args:
            func: 映射函数
            items: 输入列表
            
        Returns:
            结果列表
        """
        results = []
        
        def worker(item):
            return func(item)
        
        for item in items:
            result = self.executor.execute(worker, item)
            results.append(result)
        
        return results
    
    def measure_performance(self) -> PerformanceMetrics:
        """测量当前性能"""
        metrics = PerformanceMetrics(
            response_time=self.executor.stats['avg_execution_time'],
            throughput=self.executor.stats['tasks_completed'] / max(
                self.executor.stats['avg_execution_time'], 0.001
            ),
            memory_usage=self.memory_manager.stats['current_usage_mb'],
            cache_hit_rate=self.cache.get_hit_rate()
        )
        
        self.metrics_history.append(metrics)
        return metrics
    
    def optimize(self) -> Dict:
        """
        执行优化
        
        Returns:
            优化建议
        """
        suggestions = []
        
        # 检查缓存命中率
        cache_hit_rate = self.cache.get_hit_rate()
        if cache_hit_rate < 0.5:
            suggestions.append({
                'type': 'cache',
                'issue': 'Low cache hit rate',
                'suggestion': 'Increase cache size or review caching strategy',
                'current': cache_hit_rate,
                'target': 0.8
            })
        
        # 检查内存使用
        memory_usage = self.memory_manager.get_usage()
        if memory_usage['usage_percent'] > 80:
            suggestions.append({
                'type': 'memory',
                'issue': 'High memory usage',
                'suggestion': 'Increase memory limit or optimize memory allocation',
                'current': memory_usage['usage_percent'],
                'target': 60
            })
        
        # 检查并发
        if self.executor.active_workers >= self.executor.max_workers * 0.9:
            suggestions.append({
                'type': 'concurrency',
                'issue': 'High worker utilization',
                'suggestion': 'Increase max workers or optimize task distribution',
                'current': self.executor.active_workers,
                'target': self.executor.max_workers * 0.7
            })
        
        self.stats['optimizations_applied'] += len(suggestions)
        
        return {
            'suggestions': suggestions,
            'metrics': self.measure_performance().to_dict(),
            'cache_stats': self.cache.stats,
            'executor_stats': self.executor.stats,
            'memory_usage': memory_usage
        }
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            'stats': self.stats,
            'cache': {
                'size': len(self.cache.cache),
                'max_size': self.cache.max_size,
                'hit_rate': self.cache.get_hit_rate()
            },
            'executor': {
                'active_workers': self.executor.active_workers,
                'max_workers': self.executor.max_workers,
                'stats': self.executor.stats
            },
            'memory': self.memory_manager.get_usage()
        }


# 测试代码
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v6.1 - Performance Optimizer Test")
    print("=" * 60)
    
    # 创建优化器
    optimizer = PerformanceOptimizer({
        'cache_size': 100,
        'max_workers': 5,
        'max_memory': 512
    })
    
    # 测试缓存装饰器
    print("\n1. 测试缓存装饰器...")
    
    @optimizer.cached('test')
    def expensive_function(x):
        time.sleep(0.1)
        return x * 2
    
    # 第一次调用 (缓存未命中)
    start = time.time()
    result1 = expensive_function(5)
    elapsed1 = time.time() - start
    
    # 第二次调用 (缓存命中)
    start = time.time()
    result2 = expensive_function(5)
    elapsed2 = time.time() - start
    
    print(f"   首次执行：{elapsed1*1000:.1f}ms")
    print(f"   缓存命中：{elapsed2*1000:.1f}ms")
    print(f"   加速比：{elapsed1/elapsed2:.1f}x")
    
    # 测试并行映射
    print("\n2. 测试并行映射...")
    
    def square(x):
        time.sleep(0.05)
        return x * x
    
    start = time.time()
    results = optimizer.parallel_map(square, range(10))
    elapsed = time.time() - start
    
    print(f"   执行时间：{elapsed*1000:.1f}ms")
    print(f"   结果：{results[:5]}...")
    
    # 测试内存管理
    print("\n3. 测试内存管理...")
    optimizer.memory_manager.allocate('test1', 100)
    optimizer.memory_manager.allocate('test2', 200)
    usage = optimizer.memory_manager.get_usage()
    print(f"   内存使用：{usage['current_mb']:.1f}MB / {usage['max_mb']}MB")
    
    # 获取优化建议
    print("\n4. 获取优化建议...")
    optimization = optimizer.optimize()
    print(f"   建议数：{len(optimization['suggestions'])}")
    print(f"   缓存命中率：{optimization['metrics']['cache_hit_rate']:.1%}")
    
    # 获取状态
    print("\n5. 优化器状态:")
    status = optimizer.get_status()
    print(f"   缓存大小：{status['cache']['size']}/{status['cache']['max_size']}")
    print(f"   活跃 worker: {status['executor']['active_workers']}/{status['executor']['max_workers']}")
    print(f"   内存使用：{status['memory']['current_mb']:.1f}MB")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)
