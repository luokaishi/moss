#!/usr/bin/env python3
"""Simple TextWorld v6.5 Training Demo"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import json
import time
import random

from agi.textworld_rl_agent_v65 import TextWorldRLAgentV65
from agi.textworld_enhanced_understanding import EnhancedTextWorldUnderstanding


class SimpleTextWorldEnv:
    """Simplified TextWorld-like environment for testing"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset environment"""
        self.current_room = 0
        self.inventory = []
        self.steps = 0
        self.max_steps = 50
        self.goal_room = 3
        self.goal_object = "key"
        
        # Simple 4-room layout: 0 - 1 - 2 - 3
        self.rooms = {
            0: {"name": "entrance", "objects": [], "exits": ["east"]},
            1: {"name": "hallway", "objects": ["key"], "exits": ["west", "east"]},
            2: {"name": "corridor", "objects": [], "exits": ["west", "east"]},
            3: {"name": "treasure_room", "objects": [], "exits": ["west"]},
        }
        
        self.has_key = False
        self.done = False
        self.won = False
        
        return self._get_obs(), self._get_info()
    
    def _get_obs(self):
        """Get observation"""
        room = self.rooms[self.current_room]
        obs = f"-= {room['name'].capitalize()} =-\n\n"
        
        if room["objects"]:
            obs += f"You see: {', '.join(room['objects'])}.\n"
        
        obs += f"Exits: {', '.join(room['exits'])}.\n\n"
        
        if self.inventory:
            obs += f"You are carrying: {', '.join(self.inventory)}.\n"
        else:
            obs += "You are carrying nothing.\n"
        
        obs += f"\nYour goal is to: Find the {self.goal_object} and reach the treasure room.\n"
        
        return obs
    
    def _get_info(self):
        """Get info"""
        room = self.rooms[self.current_room]
        commands = ['look', 'inventory']
        
        # Add movement commands
        for exit_dir in room['exits']:
            commands.append(f"go {exit_dir}")
        
        # Add take commands
        for obj in room['objects']:
            commands.append(f"take {obj}")
        
        # Add drop commands
        for obj in self.inventory:
            commands.append(f"drop {obj}")
        
        return {
            'admissible_commands': commands,
            'score': 1.0 if self.has_key else 0.0,
            'moves': self.steps,
            'max_score': 10.0,
            'won': self.won,
            'lost': self.done and not self.won,
            'inventory': self.inventory,
            'current_room': self.current_room,
        }
    
    def step(self, action):
        """Execute action"""
        self.steps += 1
        reward = 0.0
        
        action_lower = action.lower()
        room = self.rooms[self.current_room]
        
        # Movement
        if action_lower.startswith("go "):
            direction = action_lower[3:].strip()
            
            # Simple navigation
            if direction == "east" and self.current_room < 3:
                self.current_room += 1
                reward = 0.1
            elif direction == "west" and self.current_room > 0:
                self.current_room -= 1
                reward = 0.1
            else:
                reward = -0.1
        
        # Take action
        elif action_lower.startswith("take "):
            obj = action_lower[5:].strip()
            if obj in room["objects"]:
                self.inventory.append(obj)
                room["objects"].remove(obj)
                reward = 1.0
                if obj == self.goal_object:
                    self.has_key = True
            else:
                reward = -0.1
        
        # Drop action
        elif action_lower.startswith("drop "):
            obj = action_lower[5:].strip()
            if obj in self.inventory:
                self.inventory.remove(obj)
                room["objects"].append(obj)
                if obj == self.goal_object:
                    self.has_key = False
                reward = -0.1
            else:
                reward = -0.1
        
        # Look
        elif action_lower == "look":
            reward = 0.01
        
        # Inventory
        elif action_lower == "inventory":
            reward = 0.0
        
        # Check win condition
        if self.has_key and self.current_room == self.goal_room:
            self.won = True
            self.done = True
            reward += 10.0
        
        # Check lose condition
        if self.steps >= self.max_steps:
            self.done = True
            reward = -1.0
        
        return self._get_obs(), reward, self.done, self._get_info()


def train(episodes=500, eval_interval=50, target_success_rate=0.70):
    """Train Agent"""
    print("=" * 60)
    print("TextWorld v6.5 Training - Simple Environment")
    print("=" * 60)
    
    env = SimpleTextWorldEnv()
    agent = TextWorldRLAgentV65(
        state_dim=20,
        action_dim=20,
        hidden_dim=128,
        lr=1e-3,
        device='cpu'
    )
    
    best_rate = 0.0
    best_episode = 0
    training_start = time.time()
    
    history = {
        'episodes': [],
        'success_rates': [],
        'rewards': [],
        'exploration_rates': [],
    }
    
    print(f"\nStarting training...")
    print(f"Target success rate: {target_success_rate:.0%}")
    print(f"Evaluation interval: every {eval_interval} episodes")
    print()
    
    for episode in range(episodes):
        reward, steps, success, info = agent.train_episode(env, max_steps=50)
        
        if (episode + 1) % eval_interval == 0:
            print(f"\n--- Episode {episode + 1} ---")
            
            # Evaluate
            success_rate, avg_reward, avg_steps = evaluate(agent, env, episodes=50)
            
            stats = agent.get_stats()
            
            print(f"Success Rate: {success_rate:.2%}")
            print(f"Exploration Rate: {stats['exploration_rate']:.3f}")
            print(f"Avg Reward: {avg_reward:.2f}")
            print(f"Avg Steps: {avg_steps:.1f}")
            
            history['episodes'].append(episode + 1)
            history['success_rates'].append(success_rate)
            history['rewards'].append(avg_reward)
            history['exploration_rates'].append(stats['exploration_rate'])
            
            if success_rate > best_rate:
                best_rate = success_rate
                best_episode = episode + 1
                print(f"*** New Best: {best_rate:.2%} ***")
            
            if success_rate >= target_success_rate:
                print(f"\n{'='*60}")
                print(f"TARGET ACHIEVED! Success Rate: {success_rate:.2%}")
                print(f"{'='*60}")
                break
    
    training_time = time.time() - training_start
    
    print("\n" + "=" * 60)
    print("Training Complete")
    print("=" * 60)
    print(f"Best Success Rate: {best_rate:.2%} (Episode {best_episode})")
    if history['success_rates']:
        print(f"Final Success Rate: {history['success_rates'][-1]:.2%}")
    print(f"Total Training Time: {training_time:.1f}s")
    
    return agent, history, best_rate


def evaluate(agent, env, episodes=50):
    """Evaluate Agent"""
    successes = 0
    total_reward = 0.0
    total_steps = 0
    
    for _ in range(episodes):
        obs, info = env.reset()
        understanding = EnhancedTextWorldUnderstanding()
        
        done = False
        steps = 0
        episode_reward = 0.0
        
        while not done and steps < 50:
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
    
    return success_rate, avg_reward, avg_steps


if __name__ == '__main__':
    agent, history, best_rate = train(episodes=500, eval_interval=50, target_success_rate=0.70)
    
    print(f"\n{'='*60}")
    print(f"Final Results:")
    print(f"  Best Success Rate: {best_rate:.2%}")
    print(f"  Target: 70%")
    print(f"  {'PASSED' if best_rate >= 0.70 else 'NEED MORE TRAINING'}")
    print(f"{'='*60}")
