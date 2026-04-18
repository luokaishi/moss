"""
Procgen Training - MOSS v6.4

训练 MOSS 在 Procgen 环境
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from moss.benchmarks.procgen_adapter import ProcgenAdapter
import numpy as np


def train(env_name='coinrun', episodes=100):
    """训练"""
    print(f"Training on Procgen: {env_name}")
    
    # 创建环境
    env = ProcgenAdapter(env_name)
    
    if not env.available:
        print("Error: Procgen not available")
        return False
    
    print(f"Environment available: {env_name}")
    print(f"Action space: {env.get_action_space()}")
    
    # 测试运行
    obs = env.reset()
    print(f"Observation shape: {obs.shape}")
    print(f"State vector: {env.get_state_vector(obs)}")
    
    # 训练循环
    for episode in range(episodes):
        obs = env.reset()
        done = False
        total_reward = 0
        steps = 0
        
        while not done and steps < 100:
            # 随机策略
            action = np.random.randint(env.get_action_space())
            obs, reward, done, info = env.step(action)
            total_reward += reward
            steps += 1
        
        if episode % 20 == 0:
            print(f"Episode {episode}: reward={total_reward:.2f}, steps={steps}")
    
    env.close()
    print("Training complete!")
    return True


if __name__ == '__main__':
    success = train()
    exit(0 if success else 1)
