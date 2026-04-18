"""
TextWorld v6.5 Training - 深度优化训练

目标: 成功率 70%+
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import json
import time
from datetime import datetime

from agi.textworld_rl_agent_v65 import TextWorldRLAgentV65


class TextWorldAdapter:
    """
    TextWorld 环境适配器
    
    模拟 TextWorld 环境接口用于测试
    实际使用时可以替换为真正的 TextWorld 环境
    """
    
    def __init__(self, difficulty: str = "easy"):
        self.difficulty = difficulty
        self.current_room = "entrance"
        self.inventory = []
        self.rooms = {}
        self.objects = {}
        self.score = 0.0
        self.moves = 0
        self.max_score = 10.0
        self.won = False
        self.lost = False
        self.task = ""
        
        # 初始化环境
        self._setup_environment()
    
    def _setup_environment(self):
        """设置环境"""
        # 创建房间
        self.rooms = {
            'entrance': {
                'description': 'You are at the entrance hall.',
                'exits': {'north': 'hallway'},
                'objects': ['key'],
            },
            'hallway': {
                'description': 'A long hallway with doors on both sides.',
                'exits': {'south': 'entrance', 'east': 'kitchen', 'west': 'bedroom'},
                'objects': [],
            },
            'kitchen': {
                'description': 'A kitchen with various appliances.',
                'exits': {'west': 'hallway'},
                'objects': ['apple', 'knife'],
            },
            'bedroom': {
                'description': 'A cozy bedroom with a bed.',
                'exits': {'east': 'hallway', 'north': 'bathroom'},
                'objects': ['coin'],
            },
            'bathroom': {
                'description': 'A small bathroom.',
                'exits': {'south': 'bedroom'},
                'objects': ['soap'],
            },
        }
        
        # 设置任务
        self.task = "Find and take the key, then explore the house."
        self.target_object = "key"
    
    def reset(self):
        """重置环境"""
        self.current_room = "entrance"
        self.inventory = []
        self.score = 0.0
        self.moves = 0
        self.won = False
        self.lost = False
        
        # 重置房间物品
        self._setup_environment()
        
        obs = self._get_observation()
        info = self._get_info()
        
        return obs, info
    
    def _get_observation(self) -> str:
        """获取观察文本"""
        room = self.rooms.get(self.current_room, {})
        
        obs = f"-= {self.current_room.capitalize()} =-\n\n"
        obs += room.get('description', '') + "\n\n"
        
        # 添加物品信息
        objects = room.get('objects', [])
        if objects:
            obs += f"You see: {', '.join(objects)}.\n"
        
        # 添加出口信息
        exits = list(room.get('exits', {}).keys())
        if exits:
            obs += f"Exits: {', '.join(exits)}.\n"
        
        # 添加库存信息
        if self.inventory:
            obs += f"\nYou are carrying: {', '.join(self.inventory)}.\n"
        else:
            obs += "\nYou are carrying nothing.\n"
        
        # 添加任务信息
        obs += f"\nYour goal is to: {self.task}\n"
        
        return obs
    
    def _get_info(self) -> dict:
        """获取信息"""
        room = self.rooms.get(self.current_room, {})
        
        # 构建可用命令
        admissible_commands = ['look', 'inventory']
        
        # 添加移动命令
        for exit_dir in room.get('exits', {}).keys():
            admissible_commands.append(f"go {exit_dir}")
        
        # 添加拿取命令
        for obj in room.get('objects', []):
            admissible_commands.append(f"take {obj}")
            admissible_commands.append(f"examine {obj}")
        
        # 添加使用命令
        for obj in self.inventory:
            admissible_commands.append(f"drop {obj}")
        
        return {
            'admissible_commands': admissible_commands,
            'score': self.score,
            'moves': self.moves,
            'max_score': self.max_score,
            'won': self.won,
            'lost': self.lost,
            'inventory': self.inventory,
            'current_room': self.current_room,
        }
    
    def step(self, action: str):
        """执行动作"""
        self.moves += 1
        reward = 0.0
        
        action_lower = action.lower()
        room = self.rooms.get(self.current_room, {})
        
        # 处理移动
        if action_lower.startswith('go '):
            direction = action_lower[3:].strip()
            exits = room.get('exits', {})
            if direction in exits:
                self.current_room = exits[direction]
                reward = 0.1  # 小奖励鼓励探索
            else:
                reward = -0.1  # 惩罚无效动作
        
        # 处理拿取
        elif action_lower.startswith('take '):
            obj = action_lower[5:].strip()
            room_objects = room.get('objects', [])
            if obj in room_objects:
                self.inventory.append(obj)
                room['objects'].remove(obj)
                
                # 任务相关奖励
                if obj == self.target_object:
                    reward = 1.0
                    self.score += 5.0
                else:
                    reward = 0.5
            else:
                reward = -0.1
        
        # 处理丢弃
        elif action_lower.startswith('drop '):
            obj = action_lower[5:].strip()
            if obj in self.inventory:
                self.inventory.remove(obj)
                room['objects'].append(obj)
                reward = -0.1
            else:
                reward = -0.1
        
        # 处理查看
        elif action_lower == 'look' or action_lower.startswith('examine'):
            reward = 0.05
        
        # 处理库存
        elif action_lower == 'inventory':
            reward = 0.0
        
        # 检查胜利条件
        if self.target_object in self.inventory:
            # 额外探索奖励
            unique_rooms = len(set([self.current_room]))
            if unique_rooms >= 3 and self.score >= 5.0:
                self.won = True
                reward += 5.0
                self.score = self.max_score
        
        # 检查失败条件（步数过多）
        if self.moves > 50:
            self.lost = True
            reward = -1.0
        
        obs = self._get_observation()
        info = self._get_info()
        
        return obs, reward, self.won or self.lost, info
    
    def get_available_actions(self):
        """获取可用动作"""
        info = self._get_info()
        return info['admissible_commands']


def train(episodes: int = 2000, eval_interval: int = 100, target_success_rate: float = 0.70):
    """
    训练 Agent
    
    Args:
        episodes: 训练回合数
        eval_interval: 评估间隔
        target_success_rate: 目标成功率
    """
    print("=" * 60)
    print("TextWorld v6.5 Training - Target: 70%+")
    print("=" * 60)
    
    # 创建环境和 Agent
    env = TextWorldAdapter(difficulty="medium")
    agent = TextWorldRLAgentV65(
        state_dim=20,
        action_dim=20,
        hidden_dim=256,
        lr=3e-4,
        device='cpu'
    )
    
    # 训练统计
    best_rate = 0.0
    best_episode = 0
    training_start = time.time()
    
    # 记录训练历史
    history = {
        'episodes': [],
        'success_rates': [],
        'rewards': [],
        'exploration_rates': [],
        'timestamps': []
    }
    
    print(f"\n开始训练...")
    print(f"目标成功率: {target_success_rate:.0%}")
    print(f"评估间隔: 每 {eval_interval} 回合")
    print()
    
    for episode in range(episodes):
        # 训练一个回合
        reward, steps, success, info = agent.train_episode(env, max_steps=100)
        
        # 定期评估
        if (episode + 1) % eval_interval == 0:
            print(f"\n--- Episode {episode + 1} ---")
            
            # 评估
            success_rate = agent.evaluate(env, episodes=50, max_steps=100)
            
            # 获取统计
            stats = agent.get_stats()
            
            print(f"Success Rate: {success_rate:.2%}")
            print(f"Exploration Rate: {stats['exploration_rate']:.3f}")
            print(f"Total Episodes: {stats['episodes']}")
            print(f"Total Steps: {stats['total_steps']}")
            print(f"Policy Loss: {stats['avg_policy_loss']:.4f}")
            print(f"Value Loss: {stats['avg_value_loss']:.4f}")
            
            # 理解模块摘要
            understanding = stats.get('understanding_summary', {})
            print(f"Rooms Discovered: {understanding.get('rooms_discovered', 0)}")
            print(f"Objects Found: {understanding.get('objects_found', 0)}")
            
            # 记录历史
            history['episodes'].append(episode + 1)
            history['success_rates'].append(success_rate)
            history['rewards'].append(reward)
            history['exploration_rates'].append(stats['exploration_rate'])
            history['timestamps'].append(time.time() - training_start)
            
            # 更新最佳
            if success_rate > best_rate:
                best_rate = success_rate
                best_episode = episode + 1
                print(f"*** New Best: {best_rate:.2%} ***")
                
                # 保存最佳模型
                agent.save('models/textworld_v6.5_best.pt')
            
            # 检查是否达到目标
            if success_rate >= target_success_rate:
                print(f"\n{'='*60}")
                print(f"TARGET ACHIEVED! Success Rate: {success_rate:.2%}")
                print(f"{'='*60}")
                break
            
            print()
    
    # 训练完成
    training_time = time.time() - training_start
    
    print("\n" + "=" * 60)
    print("Training Complete")
    print("=" * 60)
    print(f"Best Success Rate: {best_rate:.2%} (Episode {best_episode})")
    print(f"Final Success Rate: {history['success_rates'][-1]:.2%}")
    print(f"Total Training Time: {training_time:.1f}s")
    print(f"Total Episodes: {agent.train_stats['episodes']}")
    print(f"Total Steps: {agent.train_stats['total_steps']}")
    
    # 保存最终模型
    agent.save('models/textworld_v6.5_final.pt')
    
    # 保存训练历史
    with open('logs/textworld_v6.5_history.json', 'w') as f:
        json.dump(history, f, indent=2)
    
    # 生成报告
    generate_report(history, best_rate, best_episode, training_time)
    
    return agent, history, best_rate


def evaluate(agent, env, episodes=100, max_steps=100):
    """评估 Agent"""
    successes = 0
    total_reward = 0.0
    total_steps = 0
    
    for ep in range(episodes):
        obs, info = env.reset()
        
        # 创建新的理解器用于评估
        from agi.textworld_enhanced_understanding import EnhancedTextWorldUnderstanding
        understanding = EnhancedTextWorldUnderstanding()
        
        done = False
        steps = 0
        episode_reward = 0.0
        
        while not done and steps < max_steps:
            available_actions = info.get('admissible_commands', [])
            if not available_actions:
                break
            
            # 解析观察
            parsed = understanding.parse_observation(obs, info)
            
            # 选择动作（评估模式）
            command, _, _ = agent.select_action(obs, available_actions, info, training=False)
            
            # 执行
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


def generate_report(history, best_rate, best_episode, training_time):
    """生成训练报告"""
    report = f"""
# TextWorld v6.5 Training Report

## 训练配置
- **目标成功率**: 70%+
- **实际最佳成功率**: {best_rate:.2%}
- **达到最佳回合**: {best_episode}
- **总训练时间**: {training_time:.1f}s

## 训练结果
- **最终成功率**: {history['success_rates'][-1]:.2%}
- **总训练回合**: {history['episodes'][-1]}
- **探索率衰减**: {history['exploration_rates'][0]:.3f} → {history['exploration_rates'][-1]:.3f}

## 关键优化
1. **增强环境理解模块**: 深度解析观察，构建房间图，跟踪物品位置
2. **泛化优化**: Dropout, LayerNorm, 数据增强
3. **自适应探索**: 动态调整探索率
4. **失败学习**: 记录失败模式，避免重复错误
5. **成功模式记忆**: 学习有效策略

## 性能指标
"""
    
    # 计算指标
    if len(history['success_rates']) >= 5:
        recent_rates = history['success_rates'][-5:]
        avg_recent = sum(recent_rates) / len(recent_rates)
        report += f"- **最近5次评估平均成功率**: {avg_recent:.2%}\n"
    
    report += f"- **成功率提升**: {history['success_rates'][0]:.2%} → {history['success_rates'][-1]:.2%}\n"
    
    # 保存报告
    with open('docs/mves/textworld_optimization_v6.5.md', 'w') as f:
        f.write(report)
    
    print(f"\n报告已保存到: docs/mves/textworld_optimization_v6.5.md")


def run_full_evaluation(model_path: str = None):
    """运行完整评估"""
    print("\n" + "=" * 60)
    print("Running Full Evaluation")
    print("=" * 60)
    
    env = TextWorldAdapter(difficulty="hard")
    agent = TextWorldRLAgentV65()
    
    if model_path:
        agent.load(model_path)
        print(f"Loaded model from: {model_path}")
    
    # 多轮评估
    results = []
    for i in range(5):
        print(f"\nEvaluation Run {i+1}/5...")
        result = evaluate(agent, env, episodes=100, max_steps=100)
        results.append(result)
        print(f"  Success Rate: {result['success_rate']:.2%}")
        print(f"  Avg Reward: {result['avg_reward']:.2f}")
        print(f"  Avg Steps: {result['avg_steps']:.1f}")
    
    # 统计
    avg_success = sum(r['success_rate'] for r in results) / len(results)
    std_success = np.std([r['success_rate'] for r in results])
    
    print("\n" + "=" * 60)
    print("Final Evaluation Results")
    print("=" * 60)
    print(f"Average Success Rate: {avg_success:.2%} ± {std_success:.2%}")
    print(f"Min Success Rate: {min(r['success_rate'] for r in results):.2%}")
    print(f"Max Success Rate: {max(r['success_rate'] for r in results):.2%}")
    
    return results


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='TextWorld v6.5 Training')
    parser.add_argument('--episodes', type=int, default=2000, help='Number of training episodes')
    parser.add_argument('--eval-interval', type=int, default=100, help='Evaluation interval')
    parser.add_argument('--target', type=float, default=0.70, help='Target success rate')
    parser.add_argument('--evaluate-only', action='store_true', help='Run evaluation only')
    parser.add_argument('--model-path', type=str, default=None, help='Model path for evaluation')
    
    args = parser.parse_args()
    
    # 创建必要的目录
    os.makedirs('models', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('docs/mves', exist_ok=True)
    
    if args.evaluate_only:
        run_full_evaluation(args.model_path)
    else:
        agent, history, best_rate = train(
            episodes=args.episodes,
            eval_interval=args.eval_interval,
            target_success_rate=args.target
        )
        
        # 如果达到目标，运行完整评估
        if best_rate >= 0.70:
            print("\n" + "=" * 60)
            print("Target achieved! Running full evaluation...")
            print("=" * 60)
            run_full_evaluation('models/textworld_v6.5_best.pt')
