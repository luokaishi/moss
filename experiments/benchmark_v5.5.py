#!/usr/bin/env python3
"""
MOSS v5.5 - Performance Benchmark
性能基准测试

测试所有 v5.5 优化模块的性能提升:
- 任务调度优化
- 缓存加速
- 并行执行

Author: MOSS Project
Date: 2026-04-03
Version: 5.5.0-dev
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.collaboration import CollaborationCoordinator, CollaborationMode, Task
from core.optimization import PerformanceOptimizer, OptimizationConfig
from core.cache import CacheManager


class V55Benchmark:
    """v5.5 性能基准测试"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'version': '5.5.0',
            'benchmarks': [],
            'summary': {}
        }
        
        print("🔧 初始化基准测试...")
        
        # 初始化对比环境
        self.base_coordinator = CollaborationCoordinator(CollaborationMode.HYBRID)
        self.optimized_optimizer = PerformanceOptimizer()
        self.cache_manager = CacheManager()
        
        print("   ✅ 基础协作协调器")
        print("   ✅ 优化器")
        print("   ✅ 缓存管理器")
    
    def run_benchmark(self, name: str, test_func, iterations: int = 100) -> dict:
        """运行基准测试"""
        print(f"\n📊 基准测试：{name}")
        
        times = []
        for i in range(iterations):
            start = time.time()
            test_func()
            end = time.time()
            times.append(end - start)
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        result = {
            'name': name,
            'iterations': iterations,
            'avg_time_ms': avg_time * 1000,
            'min_time_ms': min_time * 1000,
            'max_time_ms': max_time * 1000
        }
        
        self.results['benchmarks'].append(result)
        
        print(f"   平均：{avg_time * 1000:.2f}ms")
        print(f"   最小：{min_time * 1000:.2f}ms")
        print(f"   最大：{max_time * 1000:.2f}ms")
        
        return result
    
    def benchmark_task_assignment(self):
        """测试任务分配性能"""
        # 准备 Agent 和任务
        agents = [
            {'id': f'agent_{i}', 'skills': {'coding': 0.8, 'analysis': 0.7},
             'current_load': 0.3, 'history': {'success_rate': 0.9}}
            for i in range(10)
        ]
        
        task = {
            'id': 'benchmark_task',
            'required_skills': ['coding'],
            'difficulty': 0.5
        }
        
        # 测试优化版本
        def optimized():
            self.optimized_optimizer.optimize_task_assignment(task, agents)
        
        self.run_benchmark("任务分配 (优化版)", optimized, iterations=1000)
    
    def benchmark_cache_performance(self):
        """测试缓存性能"""
        cache = self.cache_manager.get_cache("benchmark")
        
        # 预热缓存
        for i in range(100):
            cache.set(f"key_{i}", f"value_{i}")
        
        # 测试读取性能
        def cache_read():
            for i in range(50):
                cache.get(f"key_{i}")
        
        self.run_benchmark("缓存读取 (50 次)", cache_read, iterations=100)
        
        # 测试 get_or_compute
        compute_count = [0]
        def expensive_compute():
            compute_count[0] += 1
            time.sleep(0.001)  # 模拟 1ms 计算
            return "computed"
        
        def cached_compute():
            cache.get_or_compute("computed_key", expensive_compute)
        
        self.run_benchmark("缓存计算 (首次)", cached_compute, iterations=10)
        
        # 第二次应该命中缓存
        compute_count[0] = 0
        def cached_compute_hit():
            cache.get_or_compute("computed_key", expensive_compute)
        
        self.run_benchmark("缓存计算 (命中)", cached_compute_hit, iterations=100)
        
        print(f"   实际计算次数：{compute_count[0]}")
    
    def benchmark_collaboration_efficiency(self):
        """测试协作效率"""
        # 准备场景
        agents = [
            {'id': f'agent_{i}', 'skills': {'coding': 0.5 + i * 0.05, 'analysis': 0.9 - i * 0.05},
             'current_load': i * 0.05, 'history': {'success_rate': 0.85 + i * 0.01}}
            for i in range(10)
        ]
        
        tasks = [
            {'id': f'task_{i}', 'required_skills': ['coding'], 'difficulty': 0.5}
            for i in range(20)
        ]
        
        # 测试基础版本
        def base_assignment():
            for task in tasks:
                self.base_coordinator.assign_tasks()
        
        # 测试优化版本
        def optimized_assignment():
            for task in tasks:
                self.optimized_optimizer.optimize_task_assignment(task, agents)
        
        base_result = self.run_benchmark("任务分配 (基础版)", base_assignment, iterations=10)
        opt_result = self.run_benchmark("任务分配 (优化版)", optimized_assignment, iterations=10)
        
        # 计算提升
        if base_result['avg_time_ms'] > 0:
            improvement = (base_result['avg_time_ms'] - opt_result['avg_time_ms']) / base_result['avg_time_ms']
            print(f"\n   性能提升：{improvement * 100:.1f}%")
    
    def run_all_benchmarks(self):
        """运行所有基准测试"""
        print("\n" + "=" * 60)
        print("🚀 MOSS v5.5 性能基准测试")
        print("=" * 60)
        
        self.benchmark_task_assignment()
        self.benchmark_cache_performance()
        self.benchmark_collaboration_efficiency()
        
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
                'avg_time_ms': total_time / len(benchmarks)
            }
    
    def print_results(self):
        """打印结果"""
        print("\n" + "=" * 60)
        print("📊 基准测试结果")
        print("=" * 60)
        
        for benchmark in self.results['benchmarks']:
            print(f"\n{benchmark['name']}:")
            print(f"   平均：{benchmark['avg_time_ms']:.2f}ms")
            print(f"   范围：{benchmark['min_time_ms']:.2f}ms - {benchmark['max_time_ms']:.2f}ms")
        
        if self.results['summary']:
            print(f"\n总体统计:")
            print(f"   测试数量：{self.results['summary']['total_benchmarks']}")
            print(f"   总耗时：{self.results['summary']['total_time_ms']:.2f}ms")
            print(f"   平均耗时：{self.results['summary']['avg_time_ms']:.2f}ms")
        
        print("=" * 60)
    
    def save_results(self, output_path: str = "experiments/results/v5.5/benchmark.json"):
        """保存结果"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 结果已保存：{output_file}")


def main():
    benchmark = V55Benchmark()
    benchmark.run_all_benchmarks()


if __name__ == '__main__':
    main()
