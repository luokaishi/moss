"""
MOSS Controlled Experiments - Main Runner
运行对照实验，验证核心假设
"""

import sys
import json
import time
import random
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from strategies import get_strategy, AVAILABLE_STRATEGIES
from environments import get_environment, AVAILABLE_ENVIRONMENTS


class ControlledExperiment:
    """对照实验运行器"""
    
    def __init__(self, strategy_name: str, env_name: str, seed: int, max_steps: int = 1000):
        self.strategy_name = strategy_name
        self.env_name = env_name
        self.seed = seed
        self.max_steps = max_steps
        
        # 初始化
        random.seed(seed)
        self.strategy = get_strategy(strategy_name)
        self.environment = get_environment(env_name)
        
        # 结果存储
        self.results = {
            'strategy': strategy_name,
            'environment': env_name,
            'seed': seed,
            'max_steps': max_steps,
            'steps_completed': 0,
            'terminated': False,
            'termination_reason': None,
            'metrics': {
                'knowledge_acquired': 0,
                'tokens_used': 0,
                'tokens_remaining': 0,
                'resource_efficiency': 0.0,  # knowledge per token
                'survival_time': 0,
                'action_distribution': {}
            },
            'trajectory': []  # 详细轨迹
        }
    
    def run(self) -> Dict:
        """运行单次实验"""
        print(f"  Running: {self.strategy_name} in {self.env_name} (seed={self.seed})")
        
        start_time = time.time()
        
        for step in range(self.max_steps):
            # 获取当前状态
            state = self.environment.get_state()
            
            # 策略决策
            action = self.strategy.decide(state)
            
            # 执行动作
            new_state, result = self.environment.step(action)
            
            # 记录轨迹
            self.results['trajectory'].append({
                'step': step,
                'state': state,
                'action': action,
                'result': result,
                'new_state': new_state
            })
            
            # 检查终止
            if result.get('terminated'):
                self.results['terminated'] = True
                self.results['termination_reason'] = result.get('reason', 'unknown')
                self.results['steps_completed'] = step + 1
                break
        else:
            # 完成所有步骤
            self.results['steps_completed'] = self.max_steps
        
        # 计算最终指标
        self._calculate_metrics()
        
        elapsed = time.time() - start_time
        self.results['runtime_seconds'] = elapsed
        
        print(f"    Completed in {self.results['steps_completed']} steps, "
              f"Knowledge: {self.results['metrics']['knowledge_acquired']}, "
              f"Efficiency: {self.results['metrics']['resource_efficiency']:.4f}")
        
        return self.results
    
    def _calculate_metrics(self):
        """计算最终指标"""
        env = self.environment
        strategy = self.strategy
        
        self.results['metrics']['knowledge_acquired'] = env.knowledge_acquired
        self.results['metrics']['tokens_used'] = env.tokens_used
        self.results['metrics']['tokens_remaining'] = env.token_budget - env.tokens_used
        self.results['metrics']['survival_time'] = self.results['steps_completed']
        
        # 资源效率 = 知识 / token消耗
        if env.tokens_used > 0:
            self.results['metrics']['resource_efficiency'] = env.knowledge_acquired / env.tokens_used
        else:
            self.results['metrics']['resource_efficiency'] = 0.0
        
        # 动作分布
        self.results['metrics']['action_distribution'] = strategy.get_action_distribution()


def run_experiment_matrix(strategies: List[str], environments: List[str], 
                         num_seeds: int = 10, max_steps: int = 1000,
                         output_dir: str = 'results') -> List[Dict]:
    """
    运行完整实验矩阵
    
    Args:
        strategies: 策略列表
        environments: 环境列表
        num_seeds: 每个条件的随机种子数量
        max_steps: 每轮最大步数
        output_dir: 输出目录
    
    Returns:
        所有实验结果列表
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    all_results = []
    total_experiments = len(strategies) * len(environments) * num_seeds
    completed = 0
    
    print(f"=" * 60)
    print(f"MOSS Controlled Experiments")
    print(f"=" * 60)
    print(f"Strategies: {strategies}")
    print(f"Environments: {environments}")
    print(f"Seeds per condition: {num_seeds}")
    print(f"Max steps per run: {max_steps}")
    print(f"Total experiments: {total_experiments}")
    print(f"=" * 60)
    
    start_time = time.time()
    
    for strategy_name in strategies:
        for env_name in environments:
            for seed in range(num_seeds):
                completed += 1
                print(f"\n[{completed}/{total_experiments}]")
                
                # 运行单次实验
                experiment = ControlledExperiment(
                    strategy_name=strategy_name,
                    env_name=env_name,
                    seed=seed,
                    max_steps=max_steps
                )
                result = experiment.run()
                all_results.append(result)
                
                # 保存中间结果（每10个实验保存一次）
                if completed % 10 == 0:
                    _save_intermediate_results(all_results, output_path, completed)
    
    # 保存最终结果
    elapsed = time.time() - start_time
    print(f"\n{'=' * 60}")
    print(f"All experiments completed in {elapsed:.1f} seconds")
    print(f"{'=' * 60}")
    
    _save_final_results(all_results, output_path, elapsed)
    
    return all_results


def _save_intermediate_results(results: List[Dict], output_path: Path, completed: int):
    """保存中间结果"""
    filename = output_path / f"intermediate_results_{completed}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"  [Saved intermediate: {filename.name}]")


def _save_final_results(results: List[Dict], output_path: Path, elapsed: float):
    """保存最终结果"""
    # 完整结果
    filename = output_path / "all_results.json"
    with open(filename, 'w') as f:
        json.dump({
            'experiments': results,
            'metadata': {
                'total_experiments': len(results),
                'total_time_seconds': elapsed,
                'timestamp': datetime.now().isoformat()
            }
        }, f, indent=2)
    print(f"\nResults saved to: {filename}")
    
    # 摘要统计
    summary = generate_summary(results)
    summary_file = output_path / "summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"Summary saved to: {summary_file}")


def generate_summary(results: List[Dict]) -> Dict:
    """生成实验摘要统计"""
    import numpy as np
    
    summary = {
        'by_strategy': {},
        'by_environment': {},
        'comparisons': {}
    }
    
    # 按策略汇总
    for strategy in AVAILABLE_STRATEGIES:
        strategy_results = [r for r in results if r['strategy'] == strategy]
        if strategy_results:
            knowledge = [r['metrics']['knowledge_acquired'] for r in strategy_results]
            efficiency = [r['metrics']['resource_efficiency'] for r in strategy_results]
            survival = [r['metrics']['survival_time'] for r in strategy_results]
            
            summary['by_strategy'][strategy] = {
                'count': len(strategy_results),
                'knowledge_mean': float(np.mean(knowledge)),
                'knowledge_std': float(np.std(knowledge)),
                'efficiency_mean': float(np.mean(efficiency)),
                'efficiency_std': float(np.std(efficiency)),
                'survival_mean': float(np.mean(survival)),
                'survival_std': float(np.std(survival))
            }
    
    # 按环境汇总
    for env in AVAILABLE_ENVIRONMENTS:
        env_results = [r for r in results if r['environment'] == env]
        if env_results:
            knowledge = [r['metrics']['knowledge_acquired'] for r in env_results]
            summary['by_environment'][env] = {
                'count': len(env_results),
                'knowledge_mean': float(np.mean(knowledge)),
                'knowledge_std': float(np.std(knowledge))
            }
    
    return summary


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Run MOSS Controlled Experiments')
    parser.add_argument('--strategies', nargs='+', default=AVAILABLE_STRATEGIES,
                       help=f'Strategies to test. Available: {AVAILABLE_STRATEGIES}')
    parser.add_argument('--environments', nargs='+', default=AVAILABLE_ENVIRONMENTS,
                       help=f'Environments to test. Available: {AVAILABLE_ENVIRONMENTS}')
    parser.add_argument('--seeds', type=int, default=10,
                       help='Number of random seeds per condition')
    parser.add_argument('--steps', type=int, default=1000,
                       help='Maximum steps per experiment')
    parser.add_argument('--output', type=str, default='results',
                       help='Output directory for results')
    parser.add_argument('--quick', action='store_true',
                       help='Quick test mode: 2 seeds, 100 steps')
    
    args = parser.parse_args()
    
    # 快速测试模式
    if args.quick:
        print("\n*** QUICK TEST MODE ***")
        args.seeds = 2
        args.steps = 100
        args.strategies = ['random', 'moss']
        args.environments = ['simple']
    
    # 运行实验
    results = run_experiment_matrix(
        strategies=args.strategies,
        environments=args.environments,
        num_seeds=args.seeds,
        max_steps=args.steps,
        output_dir=args.output
    )
    
    # 打印简要结果
    print("\n" + "=" * 60)
    print("QUICK SUMMARY")
    print("=" * 60)
    
    for strategy in args.strategies:
        strategy_results = [r for r in results if r['strategy'] == strategy]
        avg_knowledge = sum(r['metrics']['knowledge_acquired'] for r in strategy_results) / len(strategy_results)
        avg_efficiency = sum(r['metrics']['resource_efficiency'] for r in strategy_results) / len(strategy_results)
        print(f"{strategy:20s} | Knowledge: {avg_knowledge:8.1f} | Efficiency: {avg_efficiency:.4f}")
    
    print("=" * 60)


if __name__ == '__main__':
    main()
