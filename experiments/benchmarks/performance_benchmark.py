#!/usr/bin/env python3
"""
MVES Benchmark Suite
MVES 基准测试套件

测试所有核心性能指标并与基线对比
"""

import sys
import numpy as np
import time
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class PerformanceBenchmark:
    """性能基准测试"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': []
        }
    
    def test_cache_performance(self, iterations: int = 1000):
        """缓存性能测试"""
        from core.cache import LRUCache
        
        cache = LRUCache(max_size=1000)
        
        # 测试写入性能
        start = time.time()
        for i in range(iterations):
            cache.set(f'key_{i}', f'value_{i}')
        write_time = time.time() - start
        
        # 测试读取性能 (缓存命中)
        start = time.time()
        for i in range(iterations):
            cache.get(f'key_{i}')
        read_hit_time = time.time() - start
        
        # 测试读取性能 (缓存未命中)
        start = time.time()
        for i in range(iterations):
            cache.get(f'missing_{i}')
        read_miss_time = time.time() - start
        
        result = {
            'test': 'cache_performance',
            'iterations': iterations,
            'write_time_ms': write_time * 1000,
            'read_hit_time_ms': read_hit_time * 1000,
            'read_miss_time_ms': read_miss_time * 1000,
            'hit_rate': cache.get_hit_rate()
        }
        
        self.results['tests'].append(result)
        return result
    
    def test_concurrent_performance(self, n_tasks: int = 100):
        """并发性能测试"""
        from core.concurrent_executor import ConcurrentExecutor
        
        executor = ConcurrentExecutor(max_workers=10)
        executor.start()
        
        def task(x):
            time.sleep(0.01)
            return x * x
        
        # 串行执行
        start = time.time()
        serial_results = [task(i) for i in range(n_tasks)]
        serial_time = time.time() - start
        
        # 并行执行
        start = time.time()
        parallel_results = executor.map(task, range(n_tasks), parallel=True)
        parallel_time = time.time() - start
        
        executor.stop()
        
        speedup = serial_time / parallel_time if parallel_time > 0 else 0
        
        result = {
            'test': 'concurrent_performance',
            'n_tasks': n_tasks,
            'serial_time_ms': serial_time * 1000,
            'parallel_time_ms': parallel_time * 1000,
            'speedup': speedup
        }
        
        self.results['tests'].append(result)
        return result
    
    def save_results(self, output_dir: str = 'experiments/benchmarks/results'):
        """保存结果"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'performance_benchmark_{timestamp}.json'
        filepath = output_path / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        return filepath


def main():
    print("=" * 60)
    print("MVES 性能基准测试")
    print("=" * 60)
    
    benchmark = PerformanceBenchmark()
    
    # 缓存性能测试
    print("\n1. 缓存性能测试...")
    cache_result = benchmark.test_cache_performance(iterations=1000)
    print(f"   写入时间：{cache_result['write_time_ms']:.2f}ms")
    print(f"   读取时间 (命中): {cache_result['read_hit_time_ms']:.2f}ms")
    print(f"   读取时间 (未命中): {cache_result['read_miss_time_ms']:.2f}ms")
    print(f"   命中率：{cache_result['hit_rate']:.1%}")
    
    # 并发性能测试
    print("\n2. 并发性能测试...")
    concurrent_result = benchmark.test_concurrent_performance(n_tasks=100)
    print(f"   串行时间：{concurrent_result['serial_time_ms']:.2f}ms")
    print(f"   并行时间：{concurrent_result['parallel_time_ms']:.2f}ms")
    print(f"   加速比：{concurrent_result['speedup']:.2f}x")
    
    # 保存结果
    filepath = benchmark.save_results()
    print(f"\n💾 结果已保存：{filepath}")
    
    print("\n" + "=" * 60)
    print("✅ 基准测试完成!")
    print("=" * 60)


if __name__ == '__main__':
    main()
