"""
Train All Procgen Environments - v6.6

批量训练全部 16 个 Procgen 环境
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from moss.benchmarks.procgen_adapter import ProcgenFullAdapter
import json
import time
from datetime import datetime
from typing import Dict, List, Optional


class SimpleAgent:
    """简化版 Agent 用于训练演示"""
    
    def __init__(self, state_dim=12, action_dim=15):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.episode_count = 0
        
    def select_action(self, obs):
        """选择动作 - 随机策略作为基线"""
        import random
        return random.randint(0, self.action_dim - 1)
    
    def learn(self, state, action, reward, next_state, done):
        """学习 - 简化版本"""
        pass


def train_single_env(agent, env: ProcgenFullAdapter, episodes: int = 1000) -> Dict:
    """训练单个环境
    
    Args:
        agent: Agent 实例
        env: Procgen 环境适配器
        episodes: 训练回合数
        
    Returns:
        训练结果字典
    """
    successes = 0
    total_reward = 0.0
    episode_rewards = []
    episode_lengths = []
    
    env_info = env.get_env_info()
    print(f"  Environment: {env_info['name']}")
    print(f"  Type: {env_info['type']}, Difficulty: {env_info['difficulty']}")
    print(f"  Action space: {env_info['action_space']}")
    
    start_time = time.time()
    
    for episode in range(episodes):
        obs = env.reset()
        done = False
        episode_reward = 0.0
        steps = 0
        max_steps = 1000
        
        while not done and steps < max_steps:
            # 获取状态向量
            state = env.get_state_vector(obs)
            
            # 选择动作
            action = agent.select_action(state)
            
            # 执行动作
            obs, reward, done, info = env.step(action)
            
            episode_reward += reward
            steps += 1
            
            # 学习
            if steps < max_steps:
                next_state = env.get_state_vector(obs)
                agent.learn(state, action, reward, next_state, done)
        
        # 记录结果
        episode_rewards.append(episode_reward)
        episode_lengths.append(steps)
        total_reward += episode_reward
        
        # 检查是否成功 (reward > 0 通常表示成功)
        if episode_reward > 0:
            successes += 1
        
        # 进度报告
        if (episode + 1) % 100 == 0:
            recent_reward = sum(episode_rewards[-100:]) / 100
            print(f"    Episode {episode + 1}/{episodes}, "
                  f"Avg Reward: {recent_reward:.2f}, "
                  f"Success Rate: {successes/(episode+1):.2%}")
    
    elapsed_time = time.time() - start_time
    
    return {
        'success_rate': successes / episodes,
        'avg_reward': total_reward / episodes,
        'total_reward': total_reward,
        'episodes': episodes,
        'successes': successes,
        'avg_episode_length': sum(episode_lengths) / len(episode_lengths),
        'time_seconds': elapsed_time,
        'env_info': env_info
    }


def train_all_environments(episodes: int = 1000, 
                           env_filter: Optional[List[str]] = None) -> Dict:
    """训练所有环境
    
    Args:
        episodes: 每个环境的训练回合数
        env_filter: 可选的环境过滤列表
        
    Returns:
        所有环境的训练结果
    """
    results = {}
    all_envs = ProcgenFullAdapter.list_environments()
    
    # 应用过滤
    if env_filter:
        envs_to_train = [e for e in all_envs if e in env_filter]
    else:
        envs_to_train = all_envs
    
    print("=" * 70)
    print("MOSS v6.6 - Procgen Full Training")
    print("=" * 70)
    print(f"Total environments: {len(envs_to_train)}")
    print(f"Episodes per environment: {episodes}")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    overall_start = time.time()
    
    for idx, env_name in enumerate(envs_to_train, 1):
        print(f"\n[{idx}/{len(envs_to_train)}] {'=' * 60}")
        print(f"Training: {env_name.upper()}")
        print("=" * 60)
        
        # 创建环境
        env = ProcgenFullAdapter(env_name, num_levels=0)
        
        if not env.available:
            print(f"  SKIPPED - Environment not available (procgen not installed)")
            results[env_name] = {
                'skipped': True,
                'reason': 'procgen not installed'
            }
            continue
        
        # 创建 Agent
        agent = SimpleAgent(
            state_dim=12,
            action_dim=env.get_action_space()
        )
        
        # 训练
        try:
            env_results = train_single_env(agent, env, episodes)
            results[env_name] = env_results
            
            print(f"\n  Results:")
            print(f"    Success Rate: {env_results['success_rate']:.2%}")
            print(f"    Avg Reward: {env_results['avg_reward']:.2f}")
            print(f"    Time: {env_results['time_seconds']:.1f}s")
            
        except Exception as e:
            print(f"  ERROR: {e}")
            results[env_name] = {
                'error': True,
                'message': str(e)
            }
        
        finally:
            env.close()
    
    overall_time = time.time() - overall_start
    
    # 保存结果
    os.makedirs('logs', exist_ok=True)
    results_file = f'logs/procgen_all_results_{datetime.now():%Y%m%d_%H%M%S}.json'
    
    output = {
        'timestamp': datetime.now().isoformat(),
        'episodes_per_env': episodes,
        'total_environments': len(envs_to_train),
        'overall_time_seconds': overall_time,
        'results': results
    }
    
    with open(results_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    # 最终报告
    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    print(f"Total time: {overall_time:.1f}s ({overall_time/60:.1f} minutes)")
    print(f"Results saved to: {results_file}")
    print("\nEnvironment Performance:")
    print("-" * 70)
    print(f"{'Environment':<15} {'Success Rate':<12} {'Avg Reward':<12} {'Status':<10}")
    print("-" * 70)
    
    for env_name in sorted(results.keys()):
        result = results[env_name]
        if result.get('skipped'):
            status = 'SKIPPED'
            print(f"{env_name:<15} {'N/A':<12} {'N/A':<12} {status:<10}")
        elif result.get('error'):
            status = 'ERROR'
            print(f"{env_name:<15} {'N/A':<12} {'N/A':<12} {status:<10}")
        else:
            status = 'OK'
            success_rate = result['success_rate']
            avg_reward = result['avg_reward']
            print(f"{env_name:<15} {success_rate:>10.2%}   {avg_reward:>10.2f}   {status:<10}")
    
    print("-" * 70)
    
    # 统计
    successful = sum(1 for r in results.values() if not r.get('skipped') and not r.get('error'))
    avg_success_rate = sum(
        r['success_rate'] for r in results.values() 
        if not r.get('skipped') and not r.get('error')
    ) / successful if successful > 0 else 0
    
    print(f"\nSummary:")
    print(f"  Environments trained: {successful}/{len(envs_to_train)}")
    print(f"  Average success rate: {avg_success_rate:.2%}")
    
    return results


def quick_test():
    """快速测试 - 每个环境 10 回合"""
    print("Running quick test (10 episodes per environment)...")
    return train_all_environments(episodes=10)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Train all Procgen environments'
    )
    parser.add_argument(
        '--episodes', 
        type=int, 
        default=1000,
        help='Number of episodes per environment (default: 1000)'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick test mode (10 episodes)'
    )
    parser.add_argument(
        '--envs',
        nargs='+',
        help='Specific environments to train (default: all)'
    )
    
    args = parser.parse_args()
    
    if args.quick:
        quick_test()
    else:
        train_all_environments(
            episodes=args.episodes,
            env_filter=args.envs
        )


if __name__ == '__main__':
    main()
