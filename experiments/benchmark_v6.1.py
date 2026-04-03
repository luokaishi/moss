#!/usr/bin/env python3
"""
MOSS v6.1 - Performance Benchmark
性能基准测试

测试所有 v6.1 性能优化模块:
- 缓存性能
- 并发性能
- 内存性能

Author: MOSS Project
Date: 2026-04-03
Version: 6.1.0-dev
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime
import numpy as np

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.performance_optimizer import PerformanceOptimizer
from core.concurrent_executor import ConcurrentExecutor
from core.memory_manager import MemoryManager


class PerformanceBenchmark:
    """性能基准测试管理器"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'benchmarks': [],
            'summary': {}
        }
        
        # 初始化模块
        print("🔧 初始化性能模块...")
        self.optimizer = PerformanceOptimizer({
            'cache_size': 1000,
            'max_workers': 10,
            'max_memory': 512
        })
        self.executor = ConcurrentExecutor(max_workers=10)
        self.memory = MemoryManager(max_memory_mb=256)
        
        print("   ✅ 性能优化器")
        print("   ✅ 并发执行器")
        print("   ✅ 内存管理器")
    
    def run_benchmark(self, name: str, test_func, 
                     iterations: int = 100) -> dict:
        """运行基准测试"""
        print(f"\n📊 基准测试：{name}")
        
        times = []
        for i in range(iterations):
            start = time.time()
            test_func()
            elapsed = time.time() - start
            times.append(elapsed)
        
        avg_time = np.mean(times)
        min_time = np.min(times)
        max_time = np.max(times)
        std_time = np.std(times)
        
        result = {
            'name': name,
            'iterations': iterations,
            'avg_time_ms': avg_time * 1000,
            'min_time_ms': min_time * 1000,
            'max_time_ms': max_time * 1000,
            'std_time_ms': std_time * 1000
        }
        
        self.results['benchmarks'].append(result)
        
        print(f"   平均：{avg_time * 1000:.2f}ms ± {std_time * 1000:.2f}ms")
        print(f"   范围：{min_time * 1000:.2f}ms - {max_time * 1000:.2f}ms")
        
        return result
    
    def benchmark_cache(self):
        """测试缓存性能"""
        call_count = [0]
        
        @self.optimizer.cached('test')
        def cached_function(x):
            call_count[0] += 1
            time.sleep(0.01)
            return x * 2
        
        # 第一次调用 (缓存未命中)
        def test_miss():
            cached_function(np.random.random())
        
        self.run_benchmark("缓存未命中", test_miss, iterations=10)
        
        # 预热缓存
        for i in range(10):
            cached_function(i)
        
        # 第二次调用 (缓存命中)
        def test_hit():
            cached_function(5)
        
        self.run_benchmark("缓存命中", test_hit, iterations=100)
        
        # 计算命中率
        hit_rate = self.optimizer.cache.get_hit_rate()
        print(f"\n   缓存命中率：{hit_rate:.1%}")
    
    def benchmark_concurrent(self):
        """测试并发性能"""
        def task(x):
            time.sleep(0.05)
            return x * x
        
        # 串行执行
        def test_serial():
            [task(i) for i in range(10)]
        
        self.run_benchmark("串行执行 (10 任务)", test_serial, iterations=5)
        
        # 并行执行
        def test_parallel():
            self.executor.map(task, range(10), parallel=True)
        
        self.run_benchmark("并行执行 (10 任务)", test_parallel, iterations=5)
        
        # 计算加速比
        serial_result = self.results['benchmarks'][-2]
        parallel_result = self.results['benchmarks'][-1]
        
        speedup = serial_result['avg_time_ms'] / parallel_result['avg_time_ms']
        print(f"\n   加速比：{speedup:.2f}x")
    
    def benchmark_memory(self):
        """测试内存性能"""
        # 内存分配
        def test_allocate():
            self.memory.allocate(f'test_{np.random.random()}', 1.0)
        
        self.run_benchmark("内存分配 (1MB)", test_allocate, iterations=50)
        
        # 内存释放
        keys = list(self.memory.allocations.keys())[:10]
        
        def test_deallocate():
            if keys:
                key = keys.pop(0)
                self.memory.deallocate(key)
        
        self.run_benchmark("内存释放", test_deallocate, iterations=10)
        
        # 获取使用情况
        usage = self.memory.get_usage()
        print(f"\n   当前使用：{usage['stats']['current_usage_mb']:.1f}MB")
        print(f"   使用率：{usage['pool']['usage_percent']:.1f}%")
    
    def run_all_benchmarks(self):
        """运行所有基准测试"""
        print("\n" + "=" * 60)
        print("🚀 MOSS v6.1 性能基准测试")
        print("=" * 60)
        
        self.benchmark_cache()
        self.benchmark_concurrent()
        self.benchmark_memory()
        
        # 生成摘要
        self.generate_summary()
        
        # 打印结果
        self.print_results()
        
        # 保存结果
        self.save_results()
    
    def generate_summary(self):
        """生成摘要"""
        benchmarks = self.results['benchmarks']
        
        if benchmarks:
            total_time = sum(b['avg_time_ms'] for b in benchmarks)
            
            self.results['summary'] = {
                'total_benchmarks': len(benchmarks),
                'total_time_ms': total_time,
                'avg_time_ms': total_time / len(benchmarks),
                'fastest': min(benchmarks, key=lambda b: b['avg_time_ms'])['name'],
                'slowest': max(benchmarks, key=lambda b: b['avg_time_ms'])['name']
            }
    
    def print_results(self):
        """打印结果"""
        print("\n" + "=" * 60)
        print("📊 基准测试结果")
        print("=" * 60)
        
        for benchmark in self.results['benchmarks']:
            print(f"\n{benchmark['name']}:")
            print(f"   平均：{benchmark['avg_time_ms']:.2f}ms ± {benchmark['std_time_ms']:.2f}ms")
            print(f"   范围：{benchmark['min_time_ms']:.2f}ms - {benchmark['max_time_ms']:.2f}ms")
        
        if self.results['summary']:
            print(f"\n总体统计:")
            print(f"   测试数量：{self.results['summary']['total_benchmarks']}")
            print(f"   总耗时：{self.results['summary']['total_time_ms']:.2f}ms")
            print(f"   平均耗时：{self.results['summary']['avg_time_ms']:.2f}ms")
            print(f"   最快测试：{self.results['summary']['fastest']}")
            print(f"   最慢测试：{self.results['summary']['slowest']}")
        
        print("=" * 60)
    
    def save_results(self, output_path: str = "experiments/results/v6.1/benchmark.json"):
        """保存结果"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 结果已保存：{output_file}")


def main():
    benchmark = PerformanceBenchmark()
    benchmark.run_all_benchmarks()


if __name__ == '__main__':
    main()
