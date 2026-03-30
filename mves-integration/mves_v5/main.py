#!/usr/bin/env python3
"""
MVES v5 - 主程序（简化版，资源优化）

运行模式:
- 快速测试：python3 main.py --quick (1 小时)
- 标准实验：python3 main.py --hours 24 (24 小时)
- 完整实验：python3 main.py --hours 168 (168 小时)

资源限制:
- 内存：<200 MB
- 磁盘：<50 MB
- CPU: <50%
"""

import argparse
import time
import os
from datetime import datetime

from evolution import EvolutionEngine, SimpleEnvironment


def run_experiment(hours: int = 1, quick: bool = False, generations: int = None):
    """
    运行实验
    
    Args:
        hours: 实验时长（小时）
        quick: 快速测试模式
    """
    if quick:
        hours = 1
        population_size = 5
        checkpoint_interval = 5
    else:
        # 根据时长调整参数
        if hours <= 24:
            population_size = 10
            checkpoint_interval = 10
        else:
            population_size = 10
            checkpoint_interval = 20
    
    # 如果指定了 generations，直接使用（否则按小时计算）
    if generations is not None:
        total_generations = generations
        print(f"Running for {total_generations} generations...")
    else:
        total_generations = hours * 6  # 每代约 10 分钟
        print(f"Running for {hours} hours (~{total_generations} generations)...")
    
    # 配置
    config = {
        'population_size': population_size,
        'mutation_rate': 0.15,
        'checkpoint_interval': checkpoint_interval,
        'duration_hours': hours
    }
    
    print("="*70)
    print("MVES v5 - Minimal Evolutionary AGI Prototype")
    print("="*70)
    print(f"Mode: {'Quick Test' if quick else 'Standard Experiment'}")
    print(f"Duration: {hours} hours")
    print(f"Population: {population_size} agents")
    print(f"Start time: {datetime.now().isoformat()}")
    print("="*70)
    
    # 初始化
    engine = EvolutionEngine(config)
    env = SimpleEnvironment(size=(20, 20), initial_resources=1500)
    
    # 实验循环
    start_time = time.time()
    generations_per_hour = 6  # 每代约 10 分钟
    
    print(f"\nStarting experiment... (Target: {total_generations} generations)")
    print()
    
    try:
        for gen in range(total_generations):
            # 运行一代
            result = engine.run_generation(env)
            
            # 每小时打印详细统计
            if gen % generations_per_hour == 0:
                hour = gen // generations_per_hour
                stats = engine.get_statistics()
                
                print(f"Hour {hour:2d} | Gen {stats['generation']:3d} | "
                      f"Pop {stats['population_size']:2d} | "
                      f"Fitness {stats['avg_fitness']:.3f} | "
                      f"Energy {stats['avg_energy']:.1f} | "
                      f"Deaths {stats['total_deaths']:2d} | "
                      f"Births {stats['total_births']:2d} | "
                      f"Mutations {stats['total_mutations']:2d}")
                
                # 资源检查（每 5 小时）
                if hour % 5 == 0 and hour > 0:
                    engine.check_resources()
            
            # 保存检查点
            if engine.generation % engine.checkpoint_interval == 0:
                engine.save_checkpoint()
            
            # 模拟时间流逝（快速测试加速）
            if quick:
                time.sleep(0.1)  # 快速测试：每代 0.1 秒
            else:
                time.sleep(10)  # 标准：每代 10 秒（实际应为 10 分钟，这里加速用于测试）
        
        # 实验完成
        elapsed = (time.time() - start_time) / 3600  # 小时
        print()
        print("="*70)
        print("Experiment Complete!")
        print("="*70)
        print(f"Duration: {elapsed:.2f} hours")
        print(f"Generations: {engine.generation}")
        
        # 最终统计
        stats = engine.get_statistics()
        print(f"Final population: {stats['population_size']}")
        print(f"Average fitness: {stats['avg_fitness']:.3f}")
        print(f"Total deaths: {stats['total_deaths']}")
        print(f"Total births: {stats['total_births']}")
        print(f"Total mutations: {stats['total_mutations']}")
        
        # 保存最终检查点
        engine.save_checkpoint("checkpoints/final_result.json.gz")
        
        print("="*70)
        
        return engine
    
    except KeyboardInterrupt:
        print("\n\nExperiment interrupted by user")
        engine.save_checkpoint("checkpoints/interrupted_result.json.gz")
        return engine
    
    except Exception as e:
        print(f"\n\nExperiment error: {e}")
        import traceback
        traceback.print_exc()
        engine.save_checkpoint("checkpoints/error_result.json.gz")
        return None


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='MVES v5 - Minimal Evolutionary AGI Prototype')
    parser.add_argument('--hours', type=int, default=1, help='Experiment duration in hours')
    parser.add_argument('--quick', action='store_true', help='Quick test mode (1 hour, accelerated)')
    parser.add_argument('--population', type=int, default=None, help='Population size (default: auto)')
    
    args = parser.parse_args()
    
    # 确保检查点目录存在
    os.makedirs('checkpoints', exist_ok=True)
    os.makedirs('agents', exist_ok=True)
    
    # 运行实验
    run_experiment(hours=args.hours, quick=args.quick)


if __name__ == "__main__":
    main()
