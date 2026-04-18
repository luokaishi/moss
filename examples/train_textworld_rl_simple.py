"""
TextWorld RL Training - 简化版 (模拟环境)

训练 RL + MOSS 混合 Agent，目标成功率 > 50%

使用:
    python examples/train_textworld_rl_simple.py --episodes 1000 --eval-every 100
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import argparse
import json
import numpy as np
import pickle
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional


class MockTextWorldEnv:
    """模拟 TextWorld 环境用于训练演示"""
    
    def __init__(self, seed=42):
        self.seed = seed
        self.np_random = np.random.RandomState(seed)
        self.current_room = 0
        self.inventory = []
        self.target_object = None
        self.steps = 0
        self.max_steps = 50
        self.rooms = ['entrance', 'hallway', 'kitchen', 'bedroom', 'garden']
        self.objects = ['key', 'apple', 'book', 'lamp', 'chest']
        self.room_objects = {
            0: [],  # entrance
            1: ['key'],  # hallway
            2: ['apple'],  # kitchen
            3: ['book', 'lamp'],  # bedroom
            4: ['chest'],  # garden
        }
        self.room_connections = {
            0: [1],  # entrance -> hallway
            1: [0, 2, 3],  # hallway -> entrance, kitchen, bedroom
            2: [1],  # kitchen -> hallway
            3: [1, 4],  # bedroom -> hallway, garden
            4: [3],  # garden -> bedroom
        }
        self.episode_count = 0
        
    def reset(self) -> str:
        """重置环境"""
        self.current_room = 0
        self.inventory = []
        self.steps = 0
        self.episode_count += 1
        
        # 随机选择一个目标物品
        self.target_object = self.np_random.choice(self.objects)
        
        # 重置房间物品
        self.room_objects = {
            0: [],
            1: ['key'],
            2: ['apple'],
            3: ['book', 'lamp'],
            4: ['chest'],
        }
        
        return self._get_observation()
    
    def _get_observation(self) -> str:
        """获取当前观察"""
        room_name = self.rooms[self.current_room]
        objects_here = self.room_objects.get(self.current_room, [])
        exits = [self.rooms[r] for r in self.room_connections.get(self.current_room, [])]
        
        obs = f"You are in the {room_name}. "
        if objects_here:
            obs += f"You see: {', '.join(objects_here)}. "
        obs += f"Exits: {', '.join(exits)}. "
        obs += f"Inventory: {', '.join(self.inventory) if self.inventory else 'empty'}. "
        obs += f"Goal: Find and take the {self.target_object}."
        
        return obs
    
    def get_available_actions(self) -> List[str]:
        """获取可用动作"""
        actions = []
        
        # 导航动作
        for room_id in self.room_connections.get(self.current_room, []):
            actions.append(f"go to {self.rooms[room_id]}")
        
        # 物品动作
        objects_here = self.room_objects.get(self.current_room, [])
        for obj in objects_here:
            actions.append(f"take {obj}")
            actions.append(f"examine {obj}")
        
        # 检查背包
        actions.append("inventory")
        actions.append("look")
        
        return actions
    
    def step(self, action: str) -> Tuple[str, float, bool, Dict]:
        """执行动作"""
        self.steps += 1
        reward = -0.1  # 每步惩罚
        done = False
        won = False
        
        action_lower = action.lower()
        
        # 解析动作
        if action_lower.startswith("go to "):
            target_room = action_lower[6:]
            for room_id, name in enumerate(self.rooms):
                if name == target_room and room_id in self.room_connections.get(self.current_room, []):
                    self.current_room = room_id
                    reward = 0.0
                    break
        
        elif action_lower.startswith("take "):
            obj = action_lower[5:]
            objects_here = self.room_objects.get(self.current_room, [])
            if obj in objects_here:
                self.inventory.append(obj)
                self.room_objects[self.current_room].remove(obj)
                reward = 1.0
                
                # 检查是否获胜
                if obj == self.target_object:
                    reward = 10.0
                    done = True
                    won = True
        
        elif action_lower == "examine":
            reward = 0.0
        
        # 检查是否超过最大步数
        if self.steps >= self.max_steps:
            done = True
        
        obs = self._get_observation()
        info = {'won': won, 'steps': self.steps}
        
        return obs, reward, done, info


class SimpleRLAgent:
    """简单的 RL Agent (使用 Q-Learning)"""
    
    def __init__(self, state_dim=50, action_dim=20, learning_rate=0.001, gamma=0.99):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.lr = learning_rate
        self.gamma = gamma
        self.epsilon = 1.0
        self.epsilon_decay = 0.995
        self.epsilon_min = 0.05
        
        # 简化的 Q-table (使用状态哈希)
        self.q_table = {}
        self.experiences = []
        
    def _get_state_key(self, obs: str) -> str:
        """从观察生成状态键"""
        # 简化：使用观察的哈希
        return hash(obs) % 10000
    
    def select_action(self, obs: str, available_actions: List[str], explore: bool = True) -> str:
        """选择动作"""
        state_key = self._get_state_key(obs)
        
        if explore and np.random.random() < self.epsilon:
            # 随机探索
            return np.random.choice(available_actions)
        
        # 选择 Q 值最高的动作
        if state_key not in self.q_table:
            self.q_table[state_key] = {a: 0.0 for a in available_actions}
        
        # 只考虑可用动作
        q_values = {a: self.q_table[state_key].get(a, 0.0) for a in available_actions}
        
        if not q_values:
            return np.random.choice(available_actions)
        
        max_q = max(q_values.values())
        best_actions = [a for a, q in q_values.items() if q == max_q]
        
        return np.random.choice(best_actions)
    
    def store_experience(self, obs: str, action: str, reward: float, next_obs: str, done: bool):
        """存储经验"""
        self.experiences.append({
            'obs': obs,
            'action': action,
            'reward': reward,
            'next_obs': next_obs,
            'done': done
        })
    
    def update(self):
        """更新 Q 表"""
        if not self.experiences:
            return
        
        for exp in self.experiences:
            state_key = self._get_state_key(exp['obs'])
            next_state_key = self._get_state_key(exp['next_obs'])
            
            if state_key not in self.q_table:
                self.q_table[state_key] = {}
            if exp['action'] not in self.q_table[state_key]:
                self.q_table[state_key][exp['action']] = 0.0
            
            # Q-learning 更新
            current_q = self.q_table[state_key][exp['action']]
            
            if next_state_key in self.q_table and self.q_table[next_state_key]:
                next_max_q = max(self.q_table[next_state_key].values())
            else:
                next_max_q = 0.0
            
            target = exp['reward'] + self.gamma * next_max_q * (not exp['done'])
            self.q_table[state_key][exp['action']] += self.lr * (target - current_q)
        
        # 清空经验
        self.experiences = []
        
        # 衰减 epsilon
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
    
    def save(self, path):
        """保存模型"""
        with open(path, 'wb') as f:
            pickle.dump({
                'q_table': self.q_table,
                'epsilon': self.epsilon
            }, f)


def train(args):
    """训练 RL Agent"""
    print(f"\n{'='*70}")
    print(f"TextWorld RL Training (Simplified)")
    print(f"{'='*70}")
    print(f"Episodes: {args.episodes}")
    print(f"Eval every: {args.eval_every}")
    print(f"Seed: {args.seed}")
    print(f"{'='*70}\n")
    
    np.random.seed(args.seed)
    
    # 创建输出目录
    output_dir = Path('logs/textworld_rl_v6.3')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建环境
    print("Creating environment...")
    env = MockTextWorldEnv(seed=args.seed)
    
    # 创建 Agent
    print("Creating RL Agent...")
    agent = SimpleRLAgent(
        state_dim=50,
        action_dim=20,
        learning_rate=args.lr
    )
    
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
            # 获取可用动作
            available_actions = env.get_available_actions()
            
            # 选择动作
            action = agent.select_action(obs, available_actions)
            
            # 执行动作
            next_obs, reward, done, info = env.step(action)
            
            # 存储经验
            agent.store_experience(obs, action, reward, next_obs, done)
            
            episode_reward += reward
            episode_steps += 1
            obs = next_obs
            
            if done:
                # 记录结果
                success = info.get('won', False)
                training_history['episodes'].append(episode)
                training_history['rewards'].append(episode_reward)
                training_history['successes'].append(success)
        
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
            print(f"Epsilon: {agent.epsilon:.3f}")
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
    parser = argparse.ArgumentParser(description='TextWorld RL Training (Simplified)')
    parser.add_argument('--episodes', type=int, default=1000,
                        help='Training episodes')
    parser.add_argument('--eval-every', type=int, default=100,
                        help='Evaluate every N episodes')
    parser.add_argument('--eval-episodes', type=int, default=20,
                        help='Episodes per evaluation')
    parser.add_argument('--update-every', type=int, default=10,
                        help='Update every N episodes')
    parser.add_argument('--max-steps', type=int, default=50,
                        help='Max steps per episode')
    parser.add_argument('--lr', type=float, default=0.001,
                        help='Learning rate')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed')
    
    args = parser.parse_args()
    
    result = train(args)
    
    if result and result.get('success_rate', 0) > 0.5:
        print(f"\n✓ Training successful! Success rate: {result['success_rate']:.2%}")
    else:
        print(f"\n⚠ Training completed. Success rate: {result.get('success_rate', 0):.2%}")
    
    return result


if __name__ == '__main__':
    main()