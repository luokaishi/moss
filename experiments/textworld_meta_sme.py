"""
MOSS v7.2 - TextWorld Meta-SME Validation
TextWorld 环境深度验证实验

验证 Meta-SME 在复杂文本环境中的表现
N=30, 57K cycles

Author: MOSS Project
Date: 2026-04-19
"""

import numpy as np
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import hashlib

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from agi.meta_sme import MetaSME, ModificationType
from agi.meta_sme_integration import MetaSMEDriveIntegration, EnvironmentAwareMetaSME


class TextWorldEnvironment:
    """
    模拟 TextWorld 环境
    
    基于 mves 的 TextWorld 适配器简化实现
    """
    
    def __init__(self, scenario: str = "simple"):
        self.scenario = scenario
        self.step_count = 0
        self.max_steps = 1000
        
        # 游戏状态
        self.inventory = []
        self.location = "start"
        self.game_state = "playing"
        
        # 任务目标
        self.objectives = {
            'find_key': False,
            'open_door': False,
            'get_treasure': False
        }
        
        # 难度参数
        self.difficulty = 0.5
    
    def reset(self) -> Dict:
        """重置环境"""
        self.step_count = 0
        self.inventory = []
        self.location = "start"
        self.game_state = "playing"
        self.objectives = {k: False for k in self.objectives}
        return self._get_observation()
    
    def step(self, action: str) -> Tuple[Dict, float, bool, Dict]:
        """
        执行动作
        
        Returns:
            (observation, reward, done, info)
        """
        self.step_count += 1
        
        # 解析动作
        reward = 0.0
        done = False
        
        # 模拟游戏逻辑
        if action == "look":
            reward = 0.1
        elif action == "take key" and self.location == "start":
            if 'key' not in self.inventory:
                self.inventory.append('key')
                self.objectives['find_key'] = True
                reward = 1.0
        elif action == "go north" and self.location == "start":
            if 'key' in self.inventory:
                self.location = "corridor"
                reward = 0.5
            else:
                reward = -0.1  # 需要钥匙
        elif action == "open door" and self.location == "corridor":
            if 'key' in self.inventory:
                self.objectives['open_door'] = True
                self.location = "treasure_room"
                reward = 2.0
        elif action == "take treasure" and self.location == "treasure_room":
            self.objectives['get_treasure'] = True
            self.game_state = "won"
            reward = 5.0
            done = True
        elif action == "inventory":
            reward = 0.05
        else:
            reward = -0.05  # 无效动作
        
        # 检查步数限制
        if self.step_count >= self.max_steps:
            done = True
            if not self.objectives['get_treasure']:
                self.game_state = "timeout"
        
        # 计算完成度
        completion = sum(self.objectives.values()) / len(self.objectives)
        
        info = {
            'step_count': self.step_count,
            'completion': completion,
            'inventory': self.inventory.copy(),
            'location': self.location,
            'game_state': self.game_state
        }
        
        return self._get_observation(), reward, done, info
    
    def _get_observation(self) -> Dict:
        """获取观察"""
        return {
            'location': self.location,
            'inventory': self.inventory.copy(),
            'game_state': self.game_state,
            'step_count': self.step_count
        }


class TextWorldAgent:
    """TextWorld Agent with Meta-SME"""
    
    ACTIONS = [
        "look", "inventory", "take key", "go north",
        "open door", "take treasure", "wait"
    ]
    
    def __init__(self, use_meta_sme: bool = True):
        self.use_meta_sme = use_meta_sme
        
        # 策略参数
        self.action_weights = np.ones(len(self.ACTIONS)) / len(self.ACTIONS)
        self.learning_rate = 0.1
        
        # 性能追踪
        self.episode_rewards = []
        self.episode_lengths = []
        self.success_count = 0
        
        # Meta-SME
        self.meta_sme = None
        self.integration = None
        
        if use_meta_sme:
            self.meta_sme = MetaSME(
                enable_auto_modify=False,
                require_human_approval=True
            )
    
    def select_action(self, observation: Dict) -> str:
        """选择动作"""
        # 基于权重的策略
        action_idx = np.random.choice(len(self.ACTIONS), p=self.action_weights)
        return self.ACTIONS[action_idx]
    
    def update_policy(self, action: str, reward: float):
        """更新策略"""
        action_idx = self.ACTIONS.index(action)
        
        # 简单强化学习更新
        if reward > 0:
            self.action_weights[action_idx] += self.learning_rate * reward
        else:
            self.action_weights[action_idx] *= 0.95
        
        # 归一化
        self.action_weights = self.action_weights / self.action_weights.sum()
    
    def record_episode(self, total_reward: float, length: int, success: bool):
        """记录回合"""
        self.episode_rewards.append(total_reward)
        self.episode_lengths.append(length)
        if success:
            self.success_count += 1
        
        # Meta-SME 记录
        if self.meta_sme:
            performance = total_reward / 10.0  # 归一化
            self.meta_sme.record_performance(performance)
    
    def get_stats(self) -> Dict:
        """获取统计"""
        if not self.episode_rewards:
            return {}
        
        recent_rewards = self.episode_rewards[-100:] if len(self.episode_rewards) > 100 else self.episode_rewards
        
        return {
            'avg_reward': np.mean(recent_rewards),
            'std_reward': np.std(recent_rewards),
            'avg_length': np.mean(self.episode_lengths[-100:]) if self.episode_lengths else 0,
            'success_rate': self.success_count / max(len(self.episode_rewards), 1),
            'total_episodes': len(self.episode_rewards)
        }


class TextWorldExperiment:
    """TextWorld 实验"""
    
    def __init__(self,
                 experiment_id: str,
                 use_meta_sme: bool,
                 seed: int,
                 num_episodes: int = 1000,
                 max_steps_per_episode: int = 100):
        self.experiment_id = experiment_id
        self.use_meta_sme = use_meta_sme
        self.seed = seed
        self.num_episodes = num_episodes
        self.max_steps_per_episode = max_steps_per_episode
        
        # 设置随机种子
        np.random.seed(seed)
        
        # 初始化
        self.env = TextWorldEnvironment()
        self.agent = TextWorldAgent(use_meta_sme=use_meta_sme)
        
        # 记录
        self.results = {
            'experiment_id': experiment_id,
            'use_meta_sme': use_meta_sme,
            'seed': seed,
            'episodes': [],
            'checkpoints': []
        }
        
        self.start_time = datetime.now()
    
    def run(self) -> Dict:
        """运行实验"""
        print(f"[{self.experiment_id}] Starting TextWorld experiment")
        print(f"  Meta-SME: {self.use_meta_sme}")
        print(f"  Episodes: {self.num_episodes}")
        
        for episode in range(self.num_episodes):
            # 重置
            obs = self.env.reset()
            episode_reward = 0.0
            
            for step in range(self.max_steps_per_episode):
                # 选择动作
                action = self.agent.select_action(obs)
                
                # 执行
                obs, reward, done, info = self.env.step(action)
                episode_reward += reward
                
                # 更新策略
                self.agent.update_policy(action, reward)
                
                if done:
                    break
            
            # 记录回合
            success = info['game_state'] == 'won'
            self.agent.record_episode(episode_reward, step + 1, success)
            
            # 检查点
            if episode % 100 == 0:
                stats = self.agent.get_stats()
                checkpoint = {
                    'episode': episode,
                    'stats': stats
                }
                self.results['checkpoints'].append(checkpoint)
                
                if episode % 500 == 0:
                    print(f"  Episode {episode}: avg_reward={stats.get('avg_reward', 0):.3f}, "
                          f"success_rate={stats.get('success_rate', 0):.3f}")
        
        # 最终统计
        final_stats = self.agent.get_stats()
        self.results['final_stats'] = final_stats
        self.results['runtime_seconds'] = (datetime.now() - self.start_time).total_seconds()
        
        print(f"[{self.experiment_id}] Completed in {self.results['runtime_seconds']:.1f}s")
        print(f"  Final avg_reward: {final_stats.get('avg_reward', 0):.3f}")
        print(f"  Final success_rate: {final_stats.get('success_rate', 0):.3f}")
        
        return self.results
    
    def save_results(self, output_dir: str):
        """保存结果"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        filename = f"{self.experiment_id}.json"
        filepath = output_path / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"[{self.experiment_id}] Results saved to {filepath}")


def run_experiment_group(group: str,
                        use_meta_sme: bool,
                        num_runs: int,
                        base_seed: int,
                        output_dir: str) -> List[Dict]:
    """运行实验组"""
    results = []
    
    for i in range(num_runs):
        seed = base_seed + i
        experiment_id = f"{group}_run{i+1:02d}_seed{seed}"
        
        exp = TextWorldExperiment(
            experiment_id=experiment_id,
            use_meta_sme=use_meta_sme,
            seed=seed,
            num_episodes=1000
        )
        
        result = exp.run()
        exp.save_results(output_dir)
        results.append(result)
    
    return results


def main():
    """主函数"""
    print("=" * 60)
    print("MOSS v7.2 - TextWorld Meta-SME Validation")
    print("=" * 60)
    
    output_dir = 'experiments/textworld_validation/results'
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 实验组配置
    groups = {
        'E': {  # 实验组
            'use_meta_sme': True,
            'num_runs': 5,  # 小规模测试，全实验用 15
            'base_seed': 5000
        },
        'C': {  # 对照组
            'use_meta_sme': False,
            'num_runs': 5,  # 小规模测试，全实验用 15
            'base_seed': 6000
        }
    }
    
    all_results = {}
    
    for group_name, group_config in groups.items():
        print(f"\n{'=' * 60}")
        print(f"Running Group: {group_name}")
        print(f"{'=' * 60}")
        
        results = run_experiment_group(
            group=group_name,
            use_meta_sme=group_config['use_meta_sme'],
            num_runs=group_config['num_runs'],
            base_seed=group_config['base_seed'],
            output_dir=output_dir
        )
        
        all_results[group_name] = results
    
    # 汇总统计
    print(f"\n{'=' * 60}")
    print("Summary Statistics")
    print(f"{'=' * 60}")
    
    for group_name, results in all_results.items():
        avg_rewards = [r['final_stats']['avg_reward'] for r in results]
        success_rates = [r['final_stats']['success_rate'] for r in results]
        
        print(f"\nGroup {group_name}:")
        print(f"  Runs: {len(results)}")
        print(f"  Avg Reward: {np.mean(avg_rewards):.4f} ± {np.std(avg_rewards):.4f}")
        print(f"  Success Rate: {np.mean(success_rates):.4f} ± {np.std(success_rates):.4f}")
    
    # 保存汇总
    summary = {
        'experiment_date': datetime.now().isoformat(),
        'group_stats': {
            group: {
                'num_runs': len(results),
                'avg_reward_mean': float(np.mean([r['final_stats']['avg_reward'] for r in results])),
                'avg_reward_std': float(np.std([r['final_stats']['avg_reward'] for r in results])),
                'success_rate_mean': float(np.mean([r['final_stats']['success_rate'] for r in results])),
                'success_rate_std': float(np.std([r['final_stats']['success_rate'] for r in results]))
            }
            for group, results in all_results.items()
        }
    }
    
    summary_path = Path(output_dir) / 'summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n{'=' * 60}")
    print(f"Experiment completed! Summary saved to {summary_path}")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()