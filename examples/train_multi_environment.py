"""
多环境训练脚本 - MOSS v6.2

在 TextWorld、BabyAI、MiniGrid 上训练 MOSS
支持元学习和跨环境泛化
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
from datetime import datetime

# 添加项目根目录到路径
workspace_root = Path(__file__).parent.parent
sys.path.insert(0, str(workspace_root))

# 导入适配器
from moss.benchmarks.textworld_adapter import TextWorldAdapter
from moss.benchmarks.babyai_adapter import BabyAIAdapter
from moss.benchmarks.minigrid_adapter import MiniGridAdapter

# 尝试导入 MOSS Agent
try:
    from agi.agent import MOSSAgent
    from agi.drive_manager import DriveManager
    from agi.meta_learner import MetaLearner
    MOSS_AVAILABLE = True
except ImportError:
    MOSS_AVAILABLE = False
    print("Warning: MOSS Agent not available. Running in demo mode.")


class MultiEnvironmentTrainer:
    """多环境训练器"""
    
    # 环境配置
    ENV_CONFIGS = {
        'textworld': {
            'adapter_class': TextWorldAdapter,
            'default_config': 'tw-cooking-v0',  # 或自定义游戏文件
            'state_dim': 12,
        },
        'babyai': {
            'adapter_class': BabyAIAdapter,
            'default_config': 'BabyAI-GoToObj-v0',
            'state_dim': 12,
        },
        'minigrid': {
            'adapter_class': MiniGridAdapter,
            'default_config': 'MiniGrid-Empty-5x5-v0',
            'state_dim': 12,
        },
    }
    
    def __init__(self, 
                 environments: List[str] = None,
                 use_meta_learning: bool = True,
                 inner_lr: float = 0.01,
                 meta_lr: float = 0.001):
        """
        初始化多环境训练器
        
        Args:
            environments: 环境名称列表，如 ['textworld', 'babyai', 'minigrid']
            use_meta_learning: 是否使用元学习
            inner_lr: 内循环学习率
            meta_lr: 元学习率
        """
        self.environments = environments or ['textworld', 'babyai', 'minigrid']
        self.adapters: Dict[str, any] = {}
        self.env_stats: Dict[str, Dict] = {}
        self.use_meta_learning = use_meta_learning and MOSS_AVAILABLE
        
        # 元学习器
        self.meta_learner = None
        if self.use_meta_learning:
            try:
                from agi.meta_learner import MetaLearner
                self.meta_learner = MetaLearner(inner_lr=inner_lr, meta_lr=meta_lr)
                print(f"Meta-learner initialized (inner_lr={inner_lr}, meta_lr={meta_lr})")
            except ImportError:
                print("Warning: MetaLearner not available")
        
        # 训练统计
        self.global_stats = {
            'total_episodes': 0,
            'total_steps': 0,
            'total_reward': 0.0,
            'start_time': datetime.now().isoformat(),
        }
        
        self._init_adapters()
    
    def _init_adapters(self):
        """初始化环境适配器"""
        for env_name in self.environments:
            if env_name not in self.ENV_CONFIGS:
                print(f"Warning: Unknown environment '{env_name}', skipping")
                continue
            
            config = self.ENV_CONFIGS[env_name]
            adapter_class = config['adapter_class']
            env_config = config['default_config']
            
            try:
                print(f"Initializing {env_name} adapter...")
                if env_name == 'textworld':
                    self.adapters[env_name] = adapter_class(env_config)
                else:
                    self.adapters[env_name] = adapter_class(env_config)
                self.env_stats[env_name] = {
                    'episodes': 0,
                    'total_reward': 0.0,
                    'success_count': 0,
                }
                print(f"  ✓ {env_name} adapter initialized")
            except Exception as e:
                print(f"  ✗ Failed to initialize {env_name}: {e}")
                self.adapters[env_name] = None
    
    def train(self, episodes_per_env: int = 100, max_steps_per_episode: int = 100):
        """
        在多环境上训练
        
        Args:
            episodes_per_env: 每个环境的训练轮数
            max_steps_per_episode: 每轮最大步数
        """
        print(f"\n{'='*60}")
        print(f"Starting Multi-Environment Training")
        print(f"Environments: {list(self.adapters.keys())}")
        print(f"Episodes per environment: {episodes_per_env}")
        print(f"Max steps per episode: {max_steps_per_episode}")
        print(f"Meta-learning: {'enabled' if self.meta_learner else 'disabled'}")
        print(f"{'='*60}\n")
        
        for env_name, adapter in self.adapters.items():
            if adapter is None:
                print(f"Skipping {env_name} (not initialized)")
                continue
            
            print(f"\nTraining on {env_name}...")
            print(f"{'-'*40}")
            
            for episode in range(episodes_per_env):
                episode_reward = self._train_episode(
                    env_name, adapter, max_steps_per_episode
                )
                
                # 更新统计
                self.env_stats[env_name]['episodes'] += 1
                self.env_stats[env_name]['total_reward'] += episode_reward
                self.global_stats['total_episodes'] += 1
                
                # 打印进度
                if (episode + 1) % 10 == 0 or episode == 0:
                    avg_reward = self.env_stats[env_name]['total_reward'] / (episode + 1)
                    print(f"  Episode {episode + 1}/{episodes_per_env}: "
                          f"reward={episode_reward:.2f}, avg={avg_reward:.2f}")
            
            # 打印环境总结
            self._print_env_summary(env_name)
        
        # 打印全局总结
        self._print_global_summary()
    
    def _train_episode(self, env_name: str, adapter, max_steps: int) -> float:
        """
        训练单个回合
        
        Args:
            env_name: 环境名称
            adapter: 环境适配器
            max_steps: 最大步数
            
        Returns:
            回合总奖励
        """
        # 重置环境
        obs = adapter.reset()
        episode_reward = 0.0
        done = False
        step = 0
        
        # 获取可用动作
        available_actions = adapter.get_available_actions()
        
        while not done and step < max_steps:
            # 获取当前状态向量
            state_vector = adapter.get_state_vector()
            
            # 选择动作 (简单策略：随机选择)
            # 在实际应用中，这里应该使用 MOSS Agent 的决策逻辑
            action = self._select_action(env_name, state_vector, available_actions)
            
            # 执行动作
            obs, reward, done, info = adapter.step(action)
            
            episode_reward += reward
            step += 1
            self.global_stats['total_steps'] += 1
            
            # 元学习更新 (如果启用)
            if self.meta_learner and step % 5 == 0:
                self._meta_learning_update(env_name, state_vector, action, reward)
        
        # 更新成功计数
        if episode_reward > 0:
            self.env_stats[env_name]['success_count'] += 1
        
        return episode_reward
    
    def _select_action(self, env_name: str, state_vector: np.ndarray, 
                       available_actions: List[str]) -> str:
        """
        选择动作
        
        这是一个简化的策略，实际应用中应该使用 MOSS Agent
        
        Args:
            env_name: 环境名称
            state_vector: 当前状态向量
            available_actions: 可用动作列表
            
        Returns:
            选择的动作
        """
        # 简单启发式策略
        if len(available_actions) == 0:
            return 'wait'
        
        # 基于状态选择动作
        # 例如：如果携带物品，可能更倾向于移动或放置
        carrying = state_vector[3] > 0.5 if len(state_vector) > 3 else False
        
        # 随机选择，但偏向某些动作
        if carrying and 'drop' in available_actions:
            # 有一定概率放下物品
            if np.random.random() < 0.3:
                return 'drop'
        
        # 默认随机选择
        return np.random.choice(available_actions)
    
    def _meta_learning_update(self, env_name: str, state: np.ndarray, 
                              action: str, reward: float):
        """元学习更新"""
        if self.meta_learner is None:
            return
        
        # 记录适应历史
        self.meta_learner.adaptation_history.append({
            'env': env_name,
            'state': state.copy(),
            'action': action,
            'reward': reward,
            'timestamp': datetime.now().isoformat(),
        })
    
    def _print_env_summary(self, env_name: str):
        """打印环境训练总结"""
        stats = self.env_stats[env_name]
        episodes = stats['episodes']
        if episodes == 0:
            return
        
        avg_reward = stats['total_reward'] / episodes
        success_rate = stats['success_count'] / episodes
        
        print(f"\n{env_name} Summary:")
        print(f"  Episodes: {episodes}")
        print(f"  Total Reward: {stats['total_reward']:.2f}")
        print(f"  Avg Reward: {avg_reward:.2f}")
        print(f"  Success Rate: {success_rate:.1%}")
    
    def _print_global_summary(self):
        """打印全局训练总结"""
        print(f"\n{'='*60}")
        print("Global Training Summary")
        print(f"{'='*60}")
        print(f"Total Episodes: {self.global_stats['total_episodes']}")
        print(f"Total Steps: {self.global_stats['total_steps']}")
        print(f"Environments: {list(self.adapters.keys())}")
        
        # 跨环境泛化评估
        print(f"\nCross-Environment Generalization:")
        success_rates = []
        for env_name, stats in self.env_stats.items():
            if stats['episodes'] > 0:
                sr = stats['success_count'] / stats['episodes']
                success_rates.append(sr)
                print(f"  {env_name}: {sr:.1%}")
        
        if success_rates:
            avg_success_rate = np.mean(success_rates)
            print(f"\nAverage Success Rate: {avg_success_rate:.1%}")
        
        # 元学习统计
        if self.meta_learner and self.meta_learner.adaptation_history:
            print(f"\nMeta-Learning Statistics:")
            print(f"  Adaptation Steps: {len(self.meta_learner.adaptation_history)}")
            recent_rewards = [h['reward'] for h in self.meta_learner.adaptation_history[-100:]]
            if recent_rewards:
                print(f"  Recent Avg Reward: {np.mean(recent_rewards):.2f}")
        
        print(f"\nTraining completed at: {datetime.now().isoformat()}")
        print(f"{'='*60}\n")
    
    def evaluate_generalization(self, test_episodes: int = 10) -> Dict:
        """
        评估跨环境泛化能力
        
        Args:
            test_episodes: 测试回合数
            
        Returns:
            泛化评估结果
        """
        print(f"\nEvaluating Cross-Environment Generalization...")
        print(f"{'-'*40}")
        
        results = {}
        
        for env_name, adapter in self.adapters.items():
            if adapter is None:
                continue
            
            rewards = []
            for _ in range(test_episodes):
                obs = adapter.reset()
                episode_reward = 0.0
                done = False
                step = 0
                
                while not done and step < 50:
                    state_vector = adapter.get_state_vector()
                    available_actions = adapter.get_available_actions()
                    action = self._select_action(env_name, state_vector, available_actions)
                    obs, reward, done, info = adapter.step(action)
                    episode_reward += reward
                    step += 1
                
                rewards.append(episode_reward)
            
            results[env_name] = {
                'mean_reward': np.mean(rewards),
                'std_reward': np.std(rewards),
                'success_rate': sum(1 for r in rewards if r > 0) / len(rewards),
            }
            
            print(f"  {env_name}: mean={results[env_name]['mean_reward']:.2f}, "
                  f"success={results[env_name]['success_rate']:.1%}")
        
        return results
    
    def close(self):
        """关闭所有环境"""
        for env_name, adapter in self.adapters.items():
            if adapter is not None:
                try:
                    adapter.close()
                    print(f"Closed {env_name} adapter")
                except Exception as e:
                    print(f"Error closing {env_name}: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='MOSS v6.2 Multi-Environment Training'
    )
    parser.add_argument(
        '--envs', 
        nargs='+', 
        default=['textworld', 'babyai', 'minigrid'],
        help='Environments to train on (default: textworld babyai minigrid)'
    )
    parser.add_argument(
        '--episodes', 
        type=int, 
        default=100,
        help='Episodes per environment (default: 100)'
    )
    parser.add_argument(
        '--max-steps', 
        type=int, 
        default=100,
        help='Max steps per episode (default: 100)'
    )
    parser.add_argument(
        '--meta-learning', 
        action='store_true',
        help='Enable meta-learning'
    )
    parser.add_argument(
        '--inner-lr', 
        type=float, 
        default=0.01,
        help='Inner loop learning rate for meta-learning (default: 0.01)'
    )
    parser.add_argument(
        '--meta-lr', 
        type=float, 
        default=0.001,
        help='Meta learning rate (default: 0.001)'
    )
    parser.add_argument(
        '--evaluate', 
        action='store_true',
        help='Run evaluation after training'
    )
    
    args = parser.parse_args()
    
    # 创建训练器
    trainer = MultiEnvironmentTrainer(
        environments=args.envs,
        use_meta_learning=args.meta_learning,
        inner_lr=args.inner_lr,
        meta_lr=args.meta_lr,
    )
    
    try:
        # 训练
        trainer.train(
            episodes_per_env=args.episodes,
            max_steps_per_episode=args.max_steps
        )
        
        # 评估
        if args.evaluate:
            results = trainer.evaluate_generalization()
            print("\nGeneralization Results:", results)
    
    finally:
        # 清理
        trainer.close()


if __name__ == '__main__':
    main()
