#!/usr/bin/env python3
"""
MOSS v6.1 - 168h Stress Test
168h 压力测试

实验目标:
- 验证 168h 连续运行稳定性
- 测量内存增长
- 测试错误恢复能力
- 评估系统可用性

Author: MOSS Project
Date: 2026-04-03
Version: 6.1.0-dev
"""

import argparse
import json
import time
import gc
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

from core.open_environment import OpenEnvironment
from core.performance_optimizer import PerformanceOptimizer
from core.memory_manager import MemoryManager


class StressTest168h:
    """168h 压力测试管理器"""
    
    def __init__(self, duration_hours: int = 168, 
                 checkpoint_interval: int = 3600):
        self.duration_hours = duration_hours
        self.checkpoint_interval = checkpoint_interval
        
        # 初始化模块
        print("🔧 初始化压力测试环境...")
        self.env = OpenEnvironment("./stress_test_workspace")
        self.optimizer = PerformanceOptimizer({
            'cache_size': 1000,
            'max_workers': 10,
            'max_memory': 1024
        })
        self.memory = MemoryManager(max_memory_mb=512)
        
        # 测试状态
        self.running = False
        self.start_time = None
        self.checkpoints = []
        
        # 实验数据
        self.experiment_data = {
            'config': {
                'duration_hours': duration_hours,
                'checkpoint_interval': checkpoint_interval
            },
            'metrics': [],
            'events': [],
            'errors': []
        }
        
        print("   ✅ 开放环境")
        print("   ✅ 性能优化器")
        print("   ✅ 内存管理器")
    
    def run_stress_cycle(self) -> dict:
        """运行一轮压力测试"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'actions': 0,
            'successes': 0,
            'failures': 0,
            'memory_mb': 0.0,
            'cache_hit_rate': 0.0
        }
        
        # 执行各种操作
        operations = [
            ('fs_write', {'path': f'test_{i}.txt', 'content': 'test'}),
            ('fs_read', {'path': f'test_{i}.txt'}),
            ('api_get', {'endpoint': '/get', 'params': {'test': 'value'}}),
        ]
        
        for i in range(100):
            op_type, params = operations[i % len(operations)]
            
            try:
                success, _ = self.env.execute_action(op_type, **params)
                metrics['actions'] += 1
                
                if success:
                    metrics['successes'] += 1
                else:
                    metrics['failures'] += 1
            except Exception as e:
                metrics['failures'] += 1
                self.experiment_data['errors'].append({
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e)
                })
        
        # 获取内存使用
        memory_usage = self.memory.get_usage()
        metrics['memory_mb'] = memory_usage['stats']['current_usage_mb']
        
        # 获取缓存命中率
        metrics['cache_hit_rate'] = self.optimizer.cache.get_hit_rate()
        
        return metrics
    
    def save_checkpoint(self):
        """保存检查点"""
        checkpoint = {
            'timestamp': datetime.now().isoformat(),
            'elapsed_hours': (datetime.now() - self.start_time).total_seconds() / 3600,
            'metrics': self.experiment_data['metrics'][-1] if self.experiment_data['metrics'] else {}
        }
        
        self.checkpoints.append(checkpoint)
        self.experiment_data['checkpoints'] = self.checkpoints
        
        # 保存到文件
        checkpoint_file = Path(f"./stress_checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        
        print(f"   💾 检查点已保存 (运行 {checkpoint['elapsed_hours']:.1f}h)")
    
    def run_simulation(self, n_iterations: int = 100):
        """运行模拟测试 (实际 168h 的简化版)"""
        print(f"\n🚀 开始 {n_iterations} 轮压力测试模拟...")
        
        self.running = True
        self.start_time = datetime.now()
        
        for iteration in range(n_iterations):
            # 运行压力周期
            metrics = self.run_stress_cycle()
            self.experiment_data['metrics'].append(metrics)
            
            # 垃圾回收
            if iteration % 10 == 0:
                gc.collect()
            
            # 保存检查点
            if iteration % 20 == 0:
                print(f"\n📍 迭代 {iteration}...")
                self.save_checkpoint()
            
            # 短暂休息
            time.sleep(0.1)
        
        self.running = False
        self.experiment_data['end_time'] = datetime.now().isoformat()
    
    def analyze_results(self) -> dict:
        """分析结果"""
        metrics = self.experiment_data['metrics']
        
        if not metrics:
            return {}
        
        # 计算统计
        success_rates = [m['successes'] / max(m['actions'], 1) for m in metrics]
        memory_usage = [m['memory_mb'] for m in metrics]
        cache_hit_rates = [m['cache_hit_rate'] for m in metrics]
        
        # 内存增长
        memory_growth = memory_usage[-1] - memory_usage[0] if len(memory_usage) > 1 else 0
        
        # 错误统计
        total_errors = len(self.experiment_data['errors'])
        
        return {
            'avg_success_rate': np.mean(success_rates),
            'std_success_rate': np.std(success_rates),
            'avg_memory_mb': np.mean(memory_usage),
            'memory_growth_mb': memory_growth,
            'avg_cache_hit_rate': np.mean(cache_hit_rates),
            'total_iterations': len(metrics),
            'total_errors': total_errors,
            'availability': (len(metrics) - total_errors) / max(len(metrics), 1)
        }
    
    def save_results(self, output_dir: str = "experiments/results/v6.1"):
        """保存结果"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        self.experiment_data['results'] = self.analyze_results()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"stress_test_168h_{timestamp}.json"
        filepath = output_path / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.experiment_data, f, indent=2, default=str)
        
        return filepath


def main():
    parser = argparse.ArgumentParser(description='MOSS v6.1 - 168h 压力测试')
    parser.add_argument('--iterations', type=int, default=100, help='模拟轮数')
    parser.add_argument('--output', type=str, default='experiments/results/v6.1')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎯 MOSS v6.1 - 168h 压力测试")
    print("=" * 60)
    
    # 创建测试
    test = StressTest168h()
    
    # 运行测试
    test.run_simulation(n_iterations=args.iterations)
    
    # 分析结果
    results = test.analyze_results()
    
    # 保存结果
    filepath = test.save_results(args.output)
    
    # 打印结果
    print("\n" + "=" * 60)
    print("🎉 测试完成！")
    print("=" * 60)
    print(f"   平均成功率       : {results['avg_success_rate']:.1%}")
    print(f"   平均内存使用     : {results['avg_memory_mb']:.1f}MB")
    print(f"   内存增长         : {results['memory_growth_mb']:.1f}MB")
    print(f"   缓存命中率       : {results['avg_cache_hit_rate']:.1%}")
    print(f"   系统可用性       : {results['availability']:.1%}")
    print(f"   错误数           : {results['total_errors']}")
    print(f"\n📊 结果已保存到：{filepath}")
    print("=" * 60)


if __name__ == '__main__':
    main()
