"""
MOSS v7.3 - Ultra Long-term Meta-SME Validation
超长期稳定性验证 (100K cycles)

使用 OptimizedMetaSME v2

Author: MOSS Project
Date: 2026-04-19
"""

import numpy as np
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from agi.meta_sme_v2 import OptimizedMetaSME


class SimpleEnvironment:
    """简化环境"""
    
    def __init__(self):
        self.state = np.zeros(4)
        self.step_count = 0
    
    def reset(self):
        self.step_count = 0
        self.state = np.random.randn(4) * 0.1
        return self.state.copy()
    
    def step(self, action: int):
        self.step_count += 1
        self.state += np.random.randn(4) * 0.05
        self.state[action % 4] += 0.1
        reward = np.sum(self.state**2) * 0.1
        done = self.step_count >= 100
        return self.state.copy(), np.clip(reward, -1, 1), done


class OptimizedAgent:
    """优化版 Agent"""
    
    def __init__(self, use_optimized: bool = True):
        self.use_optimized = use_optimized
        self.weights = np.random.randn(4, 4) * 0.1
        self.rewards_history = []
        
        self.meta_sme = None
        if use_optimized:
            self.meta_sme = OptimizedMetaSME(
                enable_auto_modify=True,
                require_human_approval=False,
                cooldown_period=1000,  # 1000 周期冷却
                use_optimization=True
            )
    
    def select_action(self, state):
        scores = state @ self.weights
        scores = scores - np.max(scores)
        exp_scores = np.exp(scores)
        probs = exp_scores / (np.sum(exp_scores) + 1e-8)
        return np.random.choice(4, p=probs)
    
    def update(self, state, action, reward):
        self.weights[:, action] += 0.01 * reward * state
        self.rewards_history.append(reward)
        
        if self.meta_sme and len(self.rewards_history) % 10 == 0:
            recent = self.rewards_history[-100:] if len(self.rewards_history) > 100 else self.rewards_history
            avg_perf = np.mean(recent) if recent else 0.5
            self.meta_sme.record_performance(avg_perf)
    
    def get_stats(self):
        if not self.rewards_history:
            return {}
        recent = self.rewards_history[-1000:] if len(self.rewards_history) > 1000 else self.rewards_history
        return {
            'avg_reward': float(np.mean(recent)),
            'std_reward': float(np.std(recent)),
            'count': len(self.rewards_history)
        }


class UltraLongTermExperiment:
    """超长期实验"""
    
    def __init__(self, experiment_id: str, use_optimized: bool, seed: int, num_cycles: int = 100000):
        self.experiment_id = experiment_id
        self.use_optimized = use_optimized
        self.seed = seed
        self.num_cycles = num_cycles
        
        np.random.seed(seed)
        
        self.env = SimpleEnvironment()
        self.agent = OptimizedAgent(use_optimized=use_optimized)
        
        self.results = {
            'experiment_id': experiment_id,
            'use_optimized': use_optimized,
            'seed': seed,
            'num_cycles': num_cycles,
            'checkpoints': []
        }
        
        self.start_time = datetime.now()
    
    def run(self):
        print(f"[{self.experiment_id}] Starting Ultra Long-term experiment")
        print(f"  Optimized: {self.use_optimized}")
        print(f"  Cycles: {self.num_cycles}")
        
        cycle = 0
        
        while cycle < self.num_cycles:
            state = self.env.reset()
            
            done = False
            while not done and cycle < self.num_cycles:
                action = self.agent.select_action(state)
                next_state, reward, done = self.env.step(action)
                self.agent.update(state, action, reward)
                cycle += 1
                state = next_state
                
                # 检查点 (每 10K cycles)
                if cycle % 10000 == 0:
                    stats = self.agent.get_stats()
                    checkpoint = {'cycle': cycle, 'stats': stats}
                    self.results['checkpoints'].append(checkpoint)
                    
                    progress = (cycle / self.num_cycles) * 100
                    print(f"  Progress: {progress:.1f}% - avg_reward={stats.get('avg_reward', 0):.4f}")
        
        # 最终
        final_stats = self.agent.get_stats()
        self.results['final_stats'] = final_stats
        self.results['runtime_seconds'] = (datetime.now() - self.start_time).total_seconds()
        
        # Meta-SME 统计
        if self.agent.meta_sme:
            self.results['meta_sme_stats'] = self.agent.meta_sme.get_optimization_stats()
        
        print(f"[{self.experiment_id}] Completed in {self.results['runtime_seconds']:.1f}s")
        print(f"  Final avg_reward: {final_stats.get('avg_reward', 0):.4f}")
        
        return self.results
    
    def save_results(self, output_dir: str):
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        filepath = output_path / f"{self.experiment_id}.json"
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"[{self.experiment_id}] Results saved to {filepath}")


def main():
    print("=" * 60)
    print("MOSS v7.3 - Ultra Long-term Meta-SME Validation")
    print("100K cycles with OptimizedMetaSME v2")
    print("=" * 60)
    
    output_dir = 'experiments/ultra_longterm_validation/results'
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 运行 2 个 100K 实验
    configs = [
        {'id': 'E_100K_run01', 'use_optimized': True, 'seed': 10000},
        {'id': 'E_100K_run02', 'use_optimized': True, 'seed': 10001}
    ]
    
    all_results = []
    
    for config in configs:
        print(f"\n{'=' * 60}")
        print(f"Running: {config['id']}")
        print(f"{'=' * 60}")
        
        exp = UltraLongTermExperiment(
            experiment_id=config['id'],
            use_optimized=config['use_optimized'],
            seed=config['seed'],
            num_cycles=100000
        )
        
        result = exp.run()
        exp.save_results(output_dir)
        all_results.append(result)
    
    # 汇总
    print(f"\n{'=' * 60}")
    print("Summary")
    print(f"{'=' * 60}")
    
    for result in all_results:
        stats = result['final_stats']
        print(f"\n{result['experiment_id']}:")
        print(f"  Avg Reward: {stats.get('avg_reward', 0):.4f}")
        print(f"  Runtime: {result.get('runtime_seconds', 0):.1f}s")
        
        if 'meta_sme_stats' in result:
            ms_stats = result['meta_sme_stats']
            print(f"  Triggers: {ms_stats.get('trigger_stats', {}).get('trigger_count', 0)}")
    
    print(f"\n{'=' * 60}")
    print("Ultra Long-term test completed!")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()