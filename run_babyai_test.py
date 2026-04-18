#!/usr/bin/env python
"""BabyAI 验证实验脚本"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from moss.benchmarks.babyai_adapter import BabyAIAdapter, BABYAI_AVAILABLE
import numpy as np
from datetime import datetime
import json

def run_babyai_validation(episodes=100, max_steps=50):
    """运行 BabyAI 验证实验"""
    print("="*60)
    print("BabyAI Validation Experiment - MOSS v6.3")
    print("="*60)
    
    if not BABYAI_AVAILABLE:
        print("\nBabyAI not installed. Running simulation mode.")
        print("Install with: pip install babyai")
    
    # 初始化适配器
    adapter = BabyAIAdapter('BabyAI-GoToObj-v0')
    
    stats = {
        'episodes': 0,
        'total_reward': 0.0,
        'success_count': 0,
        'steps_per_episode': [],
        'rewards_per_episode': [],
        'adapter_available': BABYAI_AVAILABLE,
    }
    
    print(f"\nRunning {episodes} episodes...")
    
    for episode in range(episodes):
        obs, mission = adapter.reset()
        episode_reward = 0.0
        done = False
        step = 0
        
        while not done and step < max_steps:
            # 随机策略
            actions = adapter.get_available_actions()
            action = np.random.choice(actions)
            
            obs, reward, done, info = adapter.step(action)
            episode_reward += reward
            step += 1
        
        stats['episodes'] += 1
        stats['total_reward'] += episode_reward
        stats['steps_per_episode'].append(step)
        stats['rewards_per_episode'].append(episode_reward)
        
        if episode_reward > 0:
            stats['success_count'] += 1
        
        if (episode + 1) % 20 == 0:
            print(f"  Episode {episode + 1}/{episodes} completed")
    
    # 计算统计信息
    stats['avg_reward'] = stats['total_reward'] / stats['episodes']
    stats['success_rate'] = stats['success_count'] / stats['episodes']
    stats['avg_steps'] = np.mean(stats['steps_per_episode'])
    
    adapter.close()
    
    print(f"\n{'='*60}")
    print("Results Summary")
    print(f"{'='*60}")
    print(f"Episodes: {stats['episodes']}")
    print(f"Total Reward: {stats['total_reward']:.2f}")
    print(f"Average Reward: {stats['avg_reward']:.2f}")
    print(f"Success Rate: {stats['success_rate']:.1%}")
    print(f"Average Steps: {stats['avg_steps']:.1f}")
    print(f"BabyAI Available: {BABYAI_AVAILABLE}")
    
    # 保存结果
    output_path = Path('logs/babyai_v6.3')
    output_path.mkdir(parents=True, exist_ok=True)
    
    with open(output_path / 'results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'episodes': episodes,
            'max_steps': max_steps,
            'avg_reward': stats['avg_reward'],
            'success_rate': stats['success_rate'],
            'avg_steps': stats['avg_steps'],
            'babyai_available': BABYAI_AVAILABLE,
        }, f, indent=2)
    
    print(f"\nResults saved to {output_path / 'results.json'}")
    
    return stats

if __name__ == '__main__':
    run_babyai_validation(episodes=100, max_steps=50)
