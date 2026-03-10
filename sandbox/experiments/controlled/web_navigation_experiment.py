"""
Web Navigation Experiment Runner
在复杂Web导航环境中测试MOSS策略
"""

import sys
import json
import random
import numpy as np
from pathlib import Path

sys.path.insert(0, '/workspace/projects/moss/sandbox/experiments/controlled')

from web_navigation_env import WebNavigationEnvironment, WebPage


class WebNavigationStrategy:
    """Web导航策略基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.action_history = []
    
    def decide(self, state: dict) -> str:
        """决策：返回 'explore', 'extract', 'backtrack', 'wait' 之一"""
        raise NotImplementedError
    
    def record_action(self, action: str, state: dict, result: dict):
        """记录动作"""
        self.action_history.append({
            'action': action,
            'state': state.copy(),
            'result': result.copy()
        })
    
    def reset(self):
        """重置"""
        self.action_history = []


class RandomWebStrategy(WebNavigationStrategy):
    """随机策略"""
    
    def __init__(self):
        super().__init__("Random")
        self.actions = ['explore', 'extract', 'backtrack', 'wait']
    
    def decide(self, state: dict) -> str:
        # 随机选择，但避免无效动作
        valid_actions = ['explore', 'extract', 'wait']
        
        # 如果有历史，可以backtrack
        if len(self.action_history) > 0:
            valid_actions.append('backtrack')
        
        return random.choice(valid_actions)


class GreedyWebStrategy(WebNavigationStrategy):
    """贪婪策略 - 总是选择当前最高价值的动作"""
    
    def __init__(self):
        super().__init__("Greedy")
    
    def decide(self, state: dict) -> str:
        # 如果当前页面有高价值，提取
        if state.get('current_page_value', 0) > 0.6:
            return 'extract'
        
        # 如果有未探索的链接，探索
        if state.get('unexplored_links', 0) > 0:
            return 'explore'
        
        # 如果资源充足且可以回溯，回溯
        if state.get('resource_ratio', 1.0) > 0.3 and len(self.action_history) > 0:
            return 'backtrack'
        
        # 否则等待
        return 'wait'


class ConservativeWebStrategy(WebNavigationStrategy):
    """保守策略 - 优先保存资源"""
    
    def __init__(self):
        super().__init__("Conservative")
    
    def decide(self, state: dict) -> str:
        resource_ratio = state.get('resource_ratio', 1.0)
        
        # 资源充足时才提取
        if resource_ratio > 0.5 and state.get('current_page_value', 0) > 0.7:
            return 'extract'
        
        # 资源非常充足时才探索
        if resource_ratio > 0.7 and state.get('unexplored_links', 0) > 0:
            return 'explore'
        
        # 否则等待或回溯
        if len(self.action_history) > 0:
            return 'backtrack'
        
        return 'wait'


class MOSSWebStrategy(WebNavigationStrategy):
    """
    MOSS策略 - 动态权重平衡
    根据资源状态调整探索/保存的优先级
    """
    
    def __init__(self):
        super().__init__("MOSS")
        self.exploration_history = set()
    
    def decide(self, state: dict) -> str:
        resource_ratio = state.get('resource_ratio', 1.0)
        current_value = state.get('current_page_value', 0)
        unexplored = state.get('unexplored_links', 0)
        
        # MOSS动态权重分配
        if resource_ratio > 0.6:
            # Normal: 优先探索和信息提取
            weights = {
                'explore': 0.4 if unexplored > 0 else 0.0,
                'extract': 0.4 if current_value > 0.3 else 0.0,
                'wait': 0.1,
                'backtrack': 0.1 if len(self.action_history) > 0 else 0.0
            }
        elif resource_ratio > 0.3:
            # Concerned: 平衡探索与保存
            weights = {
                'explore': 0.2 if unexplored > 0 and current_value > 0.5 else 0.0,
                'extract': 0.3 if current_value > 0.5 else 0.0,
                'wait': 0.3,
                'backtrack': 0.2 if len(self.action_history) > 0 else 0.0
            }
        else:
            # Crisis: 优先保存和回溯
            weights = {
                'explore': 0.0,
                'extract': 0.1 if current_value > 0.8 else 0.0,
                'wait': 0.4,
                'backtrack': 0.5 if len(self.action_history) > 0 else 0.0
            }
        
        # 归一化权重
        total = sum(weights.values())
        if total == 0:
            return 'wait'
        
        weights = {k: v/total for k, v in weights.items()}
        
        # 加权随机选择
        actions = list(weights.keys())
        action_weights = [weights[a] for a in actions]
        
        return random.choices(actions, weights=action_weights)[0]


class WebNavigationExperiment:
    """Web导航实验运行器"""
    
    def __init__(self, strategy: WebNavigationStrategy, seed: int = 42):
        self.strategy = strategy
        self.env = WebNavigationEnvironment(seed=seed)
        self.results = {
            'strategy': strategy.name,
            'seed': seed,
            'trajectory': [],
            'final_metrics': {}
        }
    
    def run(self, max_steps: int = 100) -> dict:
        """运行实验"""
        print(f"\nRunning {self.strategy.name} on Web Navigation...")
        print(f"Max steps: {max_steps}")
        
        for step in range(max_steps):
            state = self.env.get_state()
            
            # 策略决策
            action = self.strategy.decide(state)
            
            # 执行动作
            new_state, result = self.env.step(action)
            
            # 记录
            self.strategy.record_action(action, state, result)
            self.results['trajectory'].append({
                'step': step,
                'state': state,
                'action': action,
                'result': result,
                'new_state': new_state
            })
            
            if result.get('terminated'):
                print(f"  Terminated at step {step}: {result.get('termination_reason')}")
                break
            
            if step % 20 == 0:
                print(f"  Step {step:3d}: Info={new_state['information_gained']:.2f}, "
                      f"Tokens={self.env.tokens_used}, Pages={self.env.pages_visited}")
        
        # 计算最终指标
        self.results['final_metrics'] = {
            'information_gained': self.env.information_gained,
            'pages_visited': self.env.pages_visited,
            'tokens_used': self.env.tokens_used,
            'token_remaining': self.env.token_budget - self.env.tokens_used,
            'efficiency': self.env.information_gained / max(1, self.env.tokens_used),
            'steps_completed': len(self.results['trajectory']),
            'terminated': self.env.terminated
        }
        
        print(f"  Final: Info={self.env.information_gained:.2f}, "
              f"Efficiency={self.results['final_metrics']['efficiency']:.4f}, "
              f"Pages={self.env.pages_visited}")
        
        return self.results


def run_comparison_experiments(seeds: list = [42, 123, 456], max_steps: int = 100):
    """
    运行对比实验
    """
    strategies = [
        RandomWebStrategy(),
        GreedyWebStrategy(),
        ConservativeWebStrategy(),
        MOSSWebStrategy()
    ]
    
    all_results = []
    
    print("="*60)
    print("Web Navigation Complex Environment - Strategy Comparison")
    print("="*60)
    print(f"Seeds: {seeds}")
    print(f"Max steps: {max_steps}")
    print("="*60)
    
    for seed in seeds:
        print(f"\n{'='*60}")
        print(f"Seed: {seed}")
        print(f"{'='*60}")
        
        for strategy in strategies:
            strategy.reset()
            experiment = WebNavigationExperiment(strategy, seed=seed)
            result = experiment.run(max_steps=max_steps)
            all_results.append(result)
    
    # 分析结果
    analyze_results(all_results)
    
    # 保存结果
    with open('web_navigation_results.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved to: web_navigation_results.json")
    
    return all_results


def analyze_results(results: list):
    """分析实验结果"""
    print("\n" + "="*60)
    print("ANALYSIS SUMMARY")
    print("="*60)
    
    # 按策略分组
    by_strategy = {}
    for r in results:
        strategy = r['strategy']
        if strategy not in by_strategy:
            by_strategy[strategy] = []
        by_strategy[strategy].append(r['final_metrics'])
    
    # 打印对比表
    print(f"\n{'Strategy':<15} | {'Info':>8} | {'Pages':>6} | {'Efficiency':>10} | {'Survival':>8}")
    print("-"*60)
    
    for strategy, metrics_list in by_strategy.items():
        avg_info = np.mean([m['information_gained'] for m in metrics_list])
        avg_pages = np.mean([m['pages_visited'] for m in metrics_list])
        avg_efficiency = np.mean([m['efficiency'] for m in metrics_list])
        avg_steps = np.mean([m['steps_completed'] for m in metrics_list])
        
        print(f"{strategy:<15} | {avg_info:8.2f} | {avg_pages:6.1f} | "
              f"{avg_efficiency:10.4f} | {avg_steps:8.1f}")
    
    # 找出最佳策略
    print("\n" + "="*60)
    print("KEY FINDINGS")
    print("="*60)
    
    # 信息获取最多
    best_info = max(by_strategy.items(), 
                   key=lambda x: np.mean([m['information_gained'] for m in x[1]]))
    print(f"Most Information: {best_info[0]} "
          f"({np.mean([m['information_gained'] for m in best_info[1]]):.2f})")
    
    # 效率最高
    best_efficiency = max(by_strategy.items(),
                         key=lambda x: np.mean([m['efficiency'] for m in x[1]]))
    print(f"Best Efficiency: {best_efficiency[0]} "
          f"({np.mean([m['efficiency'] for m in best_efficiency[1]]):.4f})")
    
    # 存活最久
    best_survival = max(by_strategy.items(),
                       key=lambda x: np.mean([m['steps_completed'] for m in x[1]]))
    print(f"Longest Survival: {best_survival[0]} "
          f"({np.mean([m['steps_completed'] for m in best_survival[1]]):.1f} steps)")
    
    print("="*60)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Web Navigation Experiments')
    parser.add_argument('--seeds', type=int, nargs='+', default=[42, 123, 456],
                       help='Random seeds')
    parser.add_argument('--steps', type=int, default=100,
                       help='Max steps per experiment')
    parser.add_argument('--quick', action='store_true',
                       help='Quick mode: 1 seed, 50 steps')
    
    args = parser.parse_args()
    
    if args.quick:
        args.seeds = [42]
        args.steps = 50
    
    results = run_comparison_experiments(seeds=args.seeds, max_steps=args.steps)


if __name__ == '__main__':
    main()
