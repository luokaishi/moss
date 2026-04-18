#!/usr/bin/env python3
"""Run TextWorld v6.5 Training"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import json
import time
from datetime import datetime

from agi.textworld_rl_agent_v65 import TextWorldRLAgentV65
import importlib.util

# Load TextWorldAdapter from examples
train_path = os.path.join(os.path.dirname(__file__), 'examples', 'train_textworld_v6.5.py')
spec = importlib.util.spec_from_file_location("train_module", train_path)
train_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(train_module)
TextWorldAdapter = train_module.TextWorldAdapter


def train(episodes=500, eval_interval=50, target_success_rate=0.70):
    """Train Agent"""
    print("=" * 60)
    print("TextWorld v6.5 Training - Target: 70%+")
    print("=" * 60)
    
    # Create environment and agent
    env = TextWorldAdapter(difficulty="medium")
    agent = TextWorldRLAgentV65(
        state_dim=20,
        action_dim=20,
        hidden_dim=256,
        lr=3e-4,
        device='cpu'
    )
    
    # Training stats
    best_rate = 0.0
    best_episode = 0
    training_start = time.time()
    
    # Training history
    history = {
        'episodes': [],
        'success_rates': [],
        'rewards': [],
        'exploration_rates': [],
        'timestamps': []
    }
    
    print(f"\nStarting training...")
    print(f"Target success rate: {target_success_rate:.0%}")
    print(f"Evaluation interval: every {eval_interval} episodes")
    print()
    
    for episode in range(episodes):
        # Train one episode
        reward, steps, success, info = agent.train_episode(env, max_steps=100)
        
        # Periodic evaluation
        if (episode + 1) % eval_interval == 0:
            print(f"\n--- Episode {episode + 1} ---")
            
            # Evaluate
            eval_results = evaluate_agent(agent, env, episodes=30)
            success_rate = eval_results['success_rate']
            
            # Get stats
            stats = agent.get_stats()
            
            print(f"Success Rate: {success_rate:.2%}")
            print(f"Exploration Rate: {stats['exploration_rate']:.3f}")
            print(f"Total Episodes: {stats['episodes']}")
            print(f"Total Steps: {stats['total_steps']}")
            print(f"Avg Reward: {eval_results['avg_reward']:.2f}")
            print(f"Avg Steps: {eval_results['avg_steps']:.1f}")
            
            # Understanding summary
            understanding = stats.get('understanding_summary', {})
            print(f"Rooms Discovered: {understanding.get('rooms_discovered', 0)}")
            print(f"Objects Found: {understanding.get('objects_found', 0)}")
            
            # Record history
            history['episodes'].append(episode + 1)
            history['success_rates'].append(success_rate)
            history['rewards'].append(reward)
            history['exploration_rates'].append(stats['exploration_rate'])
            history['timestamps'].append(time.time() - training_start)
            
            # Update best
            if success_rate > best_rate:
                best_rate = success_rate
                best_episode = episode + 1
                print(f"*** New Best: {best_rate:.2%} ***")
            
            # Check if target reached
            if success_rate >= target_success_rate:
                print(f"\n{'='*60}")
                print(f"TARGET ACHIEVED! Success Rate: {success_rate:.2%}")
                print(f"{'='*60}")
                break
            
            print()
    
    # Training complete
    training_time = time.time() - training_start
    
    print("\n" + "=" * 60)
    print("Training Complete")
    print("=" * 60)
    print(f"Best Success Rate: {best_rate:.2%} (Episode {best_episode})")
    if history['success_rates']:
        print(f"Final Success Rate: {history['success_rates'][-1]:.2%}")
    print(f"Total Training Time: {training_time:.1f}s")
    print(f"Total Episodes: {agent.train_stats['episodes']}")
    print(f"Total Steps: {agent.train_stats['total_steps']}")
    
    # Create directories
    os.makedirs('models', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Save model
    agent.save('models/textworld_v6.5_final.pt')
    
    # Save history
    with open('logs/textworld_v6.5_history.json', 'w') as f:
        json.dump(history, f, indent=2)
    
    return agent, history, best_rate


def evaluate_agent(agent, env, episodes=50, max_steps=100):
    """Evaluate Agent"""
    from agi.textworld_enhanced_understanding import EnhancedTextWorldUnderstanding
    
    successes = 0
    total_reward = 0.0
    total_steps = 0
    
    for ep in range(episodes):
        obs, info = env.reset()
        understanding = EnhancedTextWorldUnderstanding()
        
        done = False
        steps = 0
        episode_reward = 0.0
        
        while not done and steps < max_steps:
            available_actions = info.get('admissible_commands', [])
            if not available_actions:
                break
            
            # Parse observation
            parsed = understanding.parse_observation(obs, info)
            
            # Select action (eval mode)
            command, _, _ = agent.select_action(obs, available_actions, info, training=False)
            
            # Execute
            obs, reward, done, info = env.step(command)
            
            episode_reward += reward
            steps += 1
            
            if info.get('won', False):
                successes += 1
                break
        
        total_reward += episode_reward
        total_steps += steps
    
    success_rate = successes / episodes
    avg_reward = total_reward / episodes
    avg_steps = total_steps / episodes
    
    return {
        'success_rate': success_rate,
        'avg_reward': avg_reward,
        'avg_steps': avg_steps,
        'successes': successes,
        'total_episodes': episodes
    }


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='TextWorld v6.5 Training')
    parser.add_argument('--episodes', type=int, default=500, help='Number of training episodes')
    parser.add_argument('--eval-interval', type=int, default=50, help='Evaluation interval')
    parser.add_argument('--target', type=float, default=0.70, help='Target success rate')
    
    args = parser.parse_args()
    
    agent, history, best_rate = train(
        episodes=args.episodes,
        eval_interval=args.eval_interval,
        target_success_rate=args.target
    )
    
    print(f"\n{'='*60}")
    print(f"Final Results:")
    print(f"  Best Success Rate: {best_rate:.2%}")
    print(f"  Target: {args.target:.0%}")
    print(f"  {'PASSED' if best_rate >= args.target else 'NEED MORE TRAINING'}")
    print(f"{'='*60}")
