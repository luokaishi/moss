"""
Atari Training - MOSS v6.4

训练 MOSS 在 Atari 环境
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from moss.benchmarks.atari_adapter import AtariAdapter, list_supported_games
import numpy as np


def train(game_name='Pong', episodes=100, max_steps=1000):
    """
    在 Atari 环境上训练
    
    Args:
        game_name: 游戏名称
        episodes: 训练回合数
        max_steps: 每回合最大步数
    """
    print(f"Training on Atari: {game_name}")
    print(f"Episodes: {episodes}, Max steps: {max_steps}")
    
    # 创建环境
    env = AtariAdapter(
        game_name=game_name,
        frame_skip=4,
        max_episode_steps=max_steps
    )
    
    if not env.available:
        print(f"Error: Atari game {game_name} not available")
        print("Make sure you have installed: pip install gym[atari] ale-py autorom[accept-rom-license]")
        return False
    
    print(f"Environment available: {game_name}")
    print(f"Action space: {env.n_actions}")
    print(f"Actions: {env.get_available_actions()[:6]}...")
    
    # 测试运行
    frame = env.reset()
    print(f"Frame shape: {frame.shape}")
    print(f"State vector: {env.get_state_vector()}")
    print()
    
    # 训练统计
    episode_rewards = []
    episode_lengths = []
    
    # 训练循环
    for episode in range(episodes):
        frame = env.reset()
        done = False
        total_reward = 0
        steps = 0
        
        while not done and steps < max_steps:
            # 随机策略 (可以替换为 RL 策略)
            action = np.random.randint(env.n_actions)
            frame, reward, done, info = env.step(action)
            total_reward += reward
            steps += 1
        
        episode_rewards.append(total_reward)
        episode_lengths.append(steps)
        
        if episode % 10 == 0:
            recent_rewards = episode_rewards[-10:] if len(episode_rewards) >= 10 else episode_rewards
            avg_reward = np.mean(recent_rewards)
            print(f"Episode {episode}: reward={total_reward:.2f}, steps={steps}, avg={avg_reward:.2f}")
    
    # 训练总结
    print("\n" + "="*50)
    print("Training Summary")
    print("="*50)
    print(f"Game: {game_name}")
    print(f"Episodes: {episodes}")
    print(f"Average reward: {np.mean(episode_rewards):.2f}")
    print(f"Best reward: {np.max(episode_rewards):.2f}")
    print(f"Average episode length: {np.mean(episode_lengths):.1f}")
    print(f"Total steps: {env.total_steps}")
    print(f"Best score ever: {env.best_score:.2f}")
    
    env.close()
    print("\nTraining complete!")
    return True


def benchmark_all_games(episodes=10):
    """对所有支持的游戏进行基准测试"""
    print("Benchmarking all supported Atari games")
    print("="*50)
    
    results = {}
    
    for game in list_supported_games():
        print(f"\nTesting {game}...")
        try:
            env = AtariAdapter(game, max_episode_steps=1000)
            if not env.available:
                print(f"  {game}: Not available")
                results[game] = {'available': False}
                continue
            
            # 快速测试
            frame = env.reset()
            total_reward = 0
            for _ in range(episodes):
                frame = env.reset()
                done = False
                steps = 0
                episode_reward = 0
                while not done and steps < 500:
                    action = np.random.randint(env.n_actions)
                    frame, reward, done, info = env.step(action)
                    episode_reward += reward
                    steps += 1
                total_reward += episode_reward
            
            avg_reward = total_reward / episodes
            print(f"  {game}: OK (avg_reward={avg_reward:.2f})")
            results[game] = {
                'available': True,
                'avg_reward': avg_reward,
                'actions': env.n_actions
            }
            env.close()
            
        except Exception as e:
            print(f"  {game}: Error - {e}")
            results[game] = {'available': False, 'error': str(e)}
    
    # 打印总结
    print("\n" + "="*50)
    print("Benchmark Summary")
    print("="*50)
    available = sum(1 for r in results.values() if r.get('available'))
    print(f"Available: {available}/{len(results)} games")
    
    for game, result in results.items():
        if result.get('available'):
            print(f"  {game}: avg_reward={result.get('avg_reward', 0):.2f}, actions={result.get('actions', 0)}")
    
    return results


def demo_visualization(game_name='Pong', steps=100):
    """演示可视化 (如果可用)"""
    print(f"Demo visualization for {game_name}")
    
    env = AtariAdapter(game_name, max_episode_steps=steps)
    if not env.available:
        print("Environment not available")
        return False
    
    frame = env.reset()
    print(f"Initial frame shape: {frame.shape}")
    print(f"Frame value range: [{frame.min()}, {frame.max()}]")
    print(f"Frame mean: {frame.mean():.2f}")
    
    for i in range(steps):
        action = np.random.randint(env.n_actions)
        frame, reward, done, info = env.step(action)
        
        if i % 20 == 0:
            print(f"Step {i}: reward={reward:.2f}, score={info.get('score', 0):.2f}, lives={info.get('lives', 0)}")
        
        if done:
            print(f"Episode done at step {i}")
            break
    
    env.close()
    return True


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Train MOSS on Atari')
    parser.add_argument('--game', type=str, default='Pong', help='Game name')
    parser.add_argument('--episodes', type=int, default=100, help='Number of episodes')
    parser.add_argument('--steps', type=int, default=1000, help='Max steps per episode')
    parser.add_argument('--benchmark', action='store_true', help='Benchmark all games')
    parser.add_argument('--demo', action='store_true', help='Run demo visualization')
    
    args = parser.parse_args()
    
    if args.benchmark:
        success = benchmark_all_games(args.episodes)
    elif args.demo:
        success = demo_visualization(args.game, args.steps)
    else:
        success = train(args.game, args.episodes, args.steps)
    
    exit(0 if success else 1)
