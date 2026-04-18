"""
TextWorld RL Training - 深度强化学习训练

训练 RL + MOSS 混合 Agent，目标成功率 > 50%

使用:
    python examples/train_textworld_rl.py --episodes 5000 --eval-every 100
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import argparse
import json
import numpy as np
from datetime import datetime
from pathlib import Path

# 尝试导入组件
try:
    from agi.textworld_rl_agent import TextWorldRLAgent
    from moss.benchmarks.textworld_adapter import TextWorldAdapter
    from agi.textworld_understanding import TextWorldUnderstanding
    from agi.textworld_memory import TextWorldMemory
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Components not available: {e}")
    COMPONENTS_AVAILABLE = False


def train(args):
    """训练 RL Agent"""
    if not COMPONENTS_AVAILABLE:
        print("Error: Required components not available")
        return
    
    print(f"\n{'='*70}")
    print(f"TextWorld RL Training")
    print(f"{'='*70}")
    print(f"Episodes: {args.episodes}")
    print(f"Eval every: {args.eval_every}")
    print(f"Seed: {args.seed}")
    print(f"{'='*70}\n")
    
    np.random.seed(args.seed)
    
    # 创建输出目录
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path(f'logs/textworld_rl_training_{timestamp}')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建环境
    print("Creating environment...")
    try:
        # 使用预设游戏或创建简单游戏
        import textworld
        from textworld.generator import compile_game
        from textworld import GameOptions
        
        # 创建一个简单的 TextWorld 游戏
        game_options = GameOptions()
        game_options.nb_rooms = 3
        game_options.nb_objects = 5
        game_options.quest_length = 3
        
        # 生成游戏
        game_file = textworld.generator.make_game(game_options)
        env = TextWorldAdapter(game_file, mode="tw")
    except Exception as e:
        print(f"Error creating environment: {e}")
        print("Make sure TextWorld is installed: pip install textworld")
        import traceback
        traceback.print_exc()
        return
    
    # 创建 Agent
    print("Creating RL Agent...")
    agent = TextWorldRLAgent(
        state_dim=50,
        action_dim=20,
        learning_rate=args.lr
    )
    
    # 创建理解模块
    understanding = TextWorldUnderstanding()
    
    # 创建记忆系统
    memory = TextWorldMemory(capacity=10000)
    
    # 训练历史
    training_history = {
        'episodes': [],
        'rewards': [],
        'successes': [],
        'eval_results': []
    }
    
    best_success_rate = 0.0
    
    # 训练循环
    print(f"\nStarting training...")
    for episode in range(args.episodes):
        # 收集经验
        obs = env.reset()
        done = False
        episode_reward = 0
        episode_steps = 0
        
        while not done and episode_steps < args.max_steps:
            # 解析观察
            parsed_state = understanding.parse_observation(obs)
            
            # 获取可用动作
            available_actions = env.get_available_actions()
            
            # 选择动作
            action = agent.select_action(obs, available_actions)
            
            # 执行动作
            next_obs, reward, done, info = env.step(action)
            
            # 存储经验
            agent.store_experience(obs, action, reward, next_obs, done)
            
            # 更新理解
            understanding.update_room_graph(
                parsed_state['current_room'],
                parsed_state['exits']
            )
            
            episode_reward += reward
            episode_steps += 1
            obs = next_obs
            
            if done:
                # 记录结果
                success = info.get('won', False)
                training_history['episodes'].append(episode)
                training_history['rewards'].append(episode_reward)
                training_history['successes'].append(success)
                
                if success:
                    memory.remember_success({
                        'episode': episode,
                        'steps': episode_steps,
                        'reward': episode_reward,
                        'state': obs
                    })
                else:
                    memory.remember_failure({
                        'episode': episode,
                        'steps': episode_steps,
                        'reward': episode_reward
                    })
        
        # 更新 Agent
        if episode % args.update_every == 0:
            agent.update()
        
        # 评估
        if episode % args.eval_every == 0 and episode > 0:
            print(f"\n{'-'*70}")
            print(f"Episode {episode}/{args.episodes}")
            
            # 运行评估
            eval_result = evaluate(agent, env, args.eval_episodes)
            training_history['eval_results'].append({
                'episode': episode,
                'success_rate': eval_result['success_rate'],
                'avg_reward': eval_result['avg_reward'],
                'avg_steps': eval_result['avg_steps']
            })
            
            print(f"Success Rate: {eval_result['success_rate']:.2%}")
            print(f"Avg Reward: {eval_result['avg_reward']:.2f}")
            print(f"Avg Steps: {eval_result['avg_steps']:.2f}")
            print(f"{'-'*70}")
            
            # 保存最佳模型
            if eval_result['success_rate'] > best_success_rate:
                best_success_rate = eval_result['success_rate']
                agent.save(output_dir / 'best_model.pkl')
                print(f"New best model saved! Success rate: {best_success_rate:.2%}")
    
    # 保存训练历史
    with open(output_dir / 'training_history.json', 'w') as f:
        json.dump(training_history, f, indent=2)
    
    # 最终评估
    print(f"\n{'='*70}")
    print(f"Final Evaluation")
    print(f"{'='*70}")
    final_result = evaluate(agent, env, 100)
    print(f"Success Rate: {final_result['success_rate']:.2%}")
    print(f"Avg Reward: {final_result['avg_reward']:.2f}")
    print(f"Avg Steps: {final_result['avg_steps']:.2f}")
    print(f"{'='*70}")
    
    # 保存最终模型
    agent.save(output_dir / 'final_model.pkl')
    
    print(f"\nTraining complete!")
    print(f"Output: {output_dir}")
    
    return final_result


def evaluate(agent, env, episodes=100):
    """评估 Agent"""
    successes = 0
    total_reward = 0
    total_steps = 0
    
    for _ in range(episodes):
        obs = env.reset()
        done = False
        episode_reward = 0
        episode_steps = 0
        
        while not done and episode_steps < 100:
            available_actions = env.get_available_actions()
            action = agent.select_action(obs, available_actions, explore=False)
            obs, reward, done, info = env.step(action)
            
            episode_reward += reward
            episode_steps += 1
            
            if done and info.get('won', False):
                successes += 1
                break
        
        total_reward += episode_reward
        total_steps += episode_steps
    
    return {
        'success_rate': successes / episodes,
        'avg_reward': total_reward / episodes,
        'avg_steps': total_steps / episodes
    }


def main():
    parser = argparse.ArgumentParser(description='TextWorld RL Training')
    parser.add_argument('--episodes', type=int, default=5000,
                        help='Training episodes')
    parser.add_argument('--eval-every', type=int, default=100,
                        help='Evaluate every N episodes')
    parser.add_argument('--eval-episodes', type=int, default=20,
                        help='Episodes per evaluation')
    parser.add_argument('--update-every', type=int, default=10,
                        help='Update every N episodes')
    parser.add_argument('--max-steps', type=int, default=50,
                        help='Max steps per episode')
    parser.add_argument('--lr', type=float, default=0.0003,
                        help='Learning rate')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed')
    
    args = parser.parse_args()
    
    result = train(args)
    
    if result and result.get('success_rate', 0) > 0.5:
        print(f"\n✓ Training successful! Success rate: {result['success_rate']:.2%}")
    
    return result


if __name__ == '__main__':
    main()