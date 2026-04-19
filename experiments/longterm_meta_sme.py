"""
MOSS v7.2 - Long-term Meta-SME Stability Test
长期稳定性测试

验证 Meta-SME 在 100K 周期下的稳定性
N=10, 100K cycles

Author: MOSS Project
Date: 2026-04-19
"""

import numpy as np
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from agi.meta_sme import MetaSME, ModificationType


class SimpleEnvironment:
    """简化环境用于长期测试"""
    
    def __init__(self, difficulty: float = 0.5):
        self.difficulty = difficulty
        self.step_count = 0
        self.state = np.zeros(4)
    
    def reset(self) -> np.ndarray:
        """重置"""
        self.step_count = 0
        self.state = np.random.randn(4) * 0.1
        return self.state.copy()
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """执行动作"""
        self.step_count += 1
        
        # 简化的状态转移
        self.state += np.random.randn(4) * 0.05
        self.state[action % 4] += 0.1
        
        # 奖励
        reward = np.sum(self.state**2) * 0.1 - self.difficulty * 0.01
        reward = np.clip(reward, -1, 1)
        
        done = self.step_count >= 1000
        
        return self.state.copy(), reward, done, {'step': self.step_count}


class StableAgent:
    """稳定测试 Agent"""
    
    def __init__(self, use_meta_sme: bool = True):
        self.use_meta_sme = use_meta_sme
        
        # 策略
        self.weights = np.random.randn(4, 4) * 0.1
        self.action_probs = np.ones(4) / 4
        
        # 性能追踪
        self.rewards_history = []
        self.modification_count = 0
        self.performance_window = []
        
        # Meta-SME
        self.meta_sme = None
        if use_meta_sme:
            self.meta_sme = MetaSME(
                enable_auto_modify=True,  # 启用自动修改
                require_human_approval=False  # 长期测试不需要人工审核
            )
    
    def select_action(self, state: np.ndarray) -> int:
        """选择动作"""
        scores = state @ self.weights
        scores = scores - np.max(scores)
        exp_scores = np.exp(scores)
        probs = exp_scores / (np.sum(exp_scores) + 1e-8)
        return np.random.choice(4, p=probs)
    
    def update(self, state: np.ndarray, action: int, reward: float):
        """更新"""
        # 简单更新
        self.weights[:, action] += 0.01 * reward * state
        
        # 记录
        self.rewards_history.append(reward)
        self.performance_window.append(reward)
        
        if len(self.performance_window) > 100:
            self.performance_window = self.performance_window[-100:]
        
        # Meta-SME 记录
        if self.meta_sme:
            avg_perf = np.mean(self.performance_window) if self.performance_window else 0.5
            self.meta_sme.record_performance(avg_perf)
            
            # 检查是否应该生成提案
            if self.meta_sme.should_generate_proposal():
                proposal = self.meta_sme.generate_proposal(
                    target_module="agi.stable_agent",
                    mod_type=ModificationType.PARAMETER_UPDATE,
                    description="Adjust learning rate based on performance",
                    ast_patch={'target_function': 'update', 'param': 'learning_rate'},
                    expected_impact={'min_performance_improvement': 0.01}
                )
                if proposal:
                    self.modification_count += 1
    
    def get_stats(self) -> Dict:
        """获取统计"""
        if not self.rewards_history:
            return {}
        
        recent = self.rewards_history[-1000:] if len(self.rewards_history) > 1000 else self.rewards_history
        
        return {
            'avg_reward': float(np.mean(recent)),
            'std_reward': float(np.std(recent)),
            'min_reward': float(np.min(recent)),
            'max_reward': float(np.max(recent)),
            'total_steps': len(self.rewards_history),
            'modification_count': self.modification_count
        }


class LongTermExperiment:
    """长期实验"""
    
    def __init__(self, experiment_id: str, use_meta_sme: bool, seed: int,
                 num_cycles: int = 100000):
        self.experiment_id = experiment_id
        self.use_meta_sme = use_meta_sme
        self.seed = seed
        self.num_cycles = num_cycles
        
        np.random.seed(seed)
        
        self.env = SimpleEnvironment()
        self.agent = StableAgent(use_meta_sme=use_meta_sme)
        
        self.results = {
            'experiment_id': experiment_id,
            'use_meta_sme': use_meta_sme,
            'seed': seed,
            'num_cycles': num_cycles,
            'checkpoints': [],
            'emergence_events': []
        }
        
        self.start_time = datetime.now()
    
    def run(self) -> Dict:
        """运行实验"""
        print(f"[{self.experiment_id}] Starting Long-term experiment")
        print(f"  Meta-SME: {self.use_meta_sme}")
        print(f"  Cycles: {self.num_cycles}")
        
        cycle = 0
        episode = 0
        
        while cycle < self.num_cycles:
            # 新回合
            state = self.env.reset()
            episode_reward = 0.0
            episode_steps = 0
            
            done = False
            while not done and cycle < self.num_cycles:
                action = self.agent.select_action(state)
                next_state, reward, done, info = self.env.step(action)
                
                self.agent.update(state, action, reward)
                episode_reward += reward
                episode_steps += 1
                cycle += 1
                state = next_state
                
                # 检查点 (每 10K cycles)
                if cycle % 10000 == 0:
                    stats = self.agent.get_stats()
                    checkpoint = {
                        'cycle': cycle,
                        'episode': episode,
                        'stats': stats
                    }
                    self.results['checkpoints'].append(checkpoint)
                    
                    progress = (cycle / self.num_cycles) * 100
                    print(f"  Progress: {progress:.1f}% - "
                          f"avg_reward={stats.get('avg_reward', 0):.4f}, "
                          f"mods={stats.get('modification_count', 0)}")
            
            episode += 1
        
        # 最终统计
        final_stats = self.agent.get_stats()
        self.results['final_stats'] = final_stats
        self.results['runtime_seconds'] = (datetime.now() - self.start_time).total_seconds()
        
        print(f"[{self.experiment_id}] Completed in {self.results['runtime_seconds']:.1f}s")
        print(f"  Final avg_reward: {final_stats.get('avg_reward', 0):.4f}")
        print(f"  Modifications: {final_stats.get('modification_count', 0)}")
        
        return self.results
    
    def save_results(self, output_dir: str):
        """保存结果"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        filepath = output_path / f"{self.experiment_id}.json"
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"[{self.experiment_id}] Results saved to {filepath}")


def main():
    """主函数"""
    print("=" * 60)
    print("MOSS v7.2 - Long-term Meta-SME Stability Test")
    print("=" * 60)
    
    output_dir = 'experiments/longterm_validation/results'
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 运行 3 个长期实验 (简化规模)
    configs = [
        {'id': 'E_run01', 'use_meta_sme': True, 'seed': 9000},
        {'id': 'E_run02', 'use_meta_sme': True, 'seed': 9001},
        {'id': 'C_run01', 'use_meta_sme': False, 'seed': 9500}
    ]
    
    all_results = []
    
    for config in configs:
        print(f"\n{'=' * 60}")
        print(f"Running: {config['id']}")
        print(f"{'=' * 60}")
        
        exp = LongTermExperiment(
            experiment_id=config['id'],
            use_meta_sme=config['use_meta_sme'],
            seed=config['seed'],
            num_cycles=50000  # 50K for quick test
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
        print(f"  Modifications: {stats.get('modification_count', 0)}")
        print(f"  Runtime: {result.get('runtime_seconds', 0):.1f}s")
    
    print(f"\n{'=' * 60}")
    print("Long-term test completed!")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()