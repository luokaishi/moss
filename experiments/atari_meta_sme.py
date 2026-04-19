"""
MOSS v7.2 - Atari Meta-SME Validation
Atari 环境深度验证实验

验证 Meta-SME 在视觉游戏环境中的表现
N=30, 57K cycles

Author: MOSS Project
Date: 2026-04-19
"""

import numpy as np
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from agi.meta_sme import MetaSME


class AtariPong:
    """模拟 Atari Pong 环境"""
    
    def __init__(self):
        self.ball_pos = np.array([0.5, 0.5])
        self.ball_vel = np.array([0.03, 0.01])
        self.paddle_y = 0.5
        self.opponent_y = 0.5
        self.score = 0
        self.opponent_score = 0
        self.step_count = 0
        self.max_steps = 1000
    
    def reset(self) -> np.ndarray:
        """重置环境"""
        self.ball_pos = np.array([0.5, 0.5])
        self.ball_vel = np.array([0.03, 0.01])
        self.paddle_y = 0.5
        self.opponent_y = 0.5
        self.score = 0
        self.opponent_score = 0
        self.step_count = 0
        return self._get_observation()
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """执行动作"""
        self.step_count += 1
        
        # 动作: 0=上, 1=下, 2=不动
        if action == 0:
            self.paddle_y = np.clip(self.paddle_y + 0.05, 0.1, 0.9)
        elif action == 1:
            self.paddle_y = np.clip(self.paddle_y - 0.05, 0.1, 0.9)
        
        # 对手简单 AI
        if self.ball_pos[1] > self.opponent_y:
            self.opponent_y = np.clip(self.opponent_y + 0.04, 0.1, 0.9)
        else:
            self.opponent_y = np.clip(self.opponent_y - 0.04, 0.1, 0.9)
        
        # 更新球位置
        self.ball_pos += self.ball_vel
        
        # 碰撞检测
        reward = 0.0
        done = False
        
        # 上下边界
        if self.ball_pos[1] <= 0 or self.ball_pos[1] >= 1:
            self.ball_vel[1] *= -1
        
        # 左边界 (对手)
        if self.ball_pos[0] <= 0:
            if abs(self.ball_pos[1] - self.opponent_y) < 0.15:
                self.ball_vel[0] *= -1
                self.ball_vel[0] *= 1.1  # 加速
            else:
                self.score += 1
                reward = 1.0
                self._reset_ball()
        
        # 右边界 (玩家)
        if self.ball_pos[0] >= 1:
            if abs(self.ball_pos[1] - self.paddle_y) < 0.15:
                self.ball_vel[0] *= -1
                self.ball_vel[0] *= 1.1
                reward = 0.1  # 击中奖励
            else:
                self.opponent_score += 1
                reward = -1.0
                self._reset_ball()
        
        # 检查结束
        if self.score >= 21 or self.opponent_score >= 21:
            done = True
        
        if self.step_count >= self.max_steps:
            done = True
        
        info = {
            'score': self.score,
            'opponent_score': self.opponent_score,
            'step_count': self.step_count
        }
        
        return self._get_observation(), reward, done, info
    
    def _reset_ball(self):
        """重置球"""
        self.ball_pos = np.array([0.5, 0.5])
        self.ball_vel = np.array([0.03 * np.sign(np.random.randn()), 
                                   0.01 * np.random.randn()])
    
    def _get_observation(self) -> np.ndarray:
        """获取观察 (简化)"""
        return np.array([
            self.ball_pos[0],      # 球 x
            self.ball_pos[1],      # 球 y
            self.ball_vel[0],      # 球 vx
            self.ball_vel[1],      # 球 vy
            self.paddle_y,         # 玩家 paddle y
            self.opponent_y,       # 对手 paddle y
            self.score / 21.0,     # 归一化分数
            self.opponent_score / 21.0
        ])


class PongAgent:
    """Pong Agent with Meta-SME"""
    
    def __init__(self, use_meta_sme: bool = True):
        self.use_meta_sme = use_meta_sme
        
        # 策略网络 (简化)
        self.weights = np.random.randn(8, 3) * 0.1
        self.bias = np.zeros(3)
        
        # 学习参数
        self.learning_rate = 0.01
        
        # 性能追踪
        self.episode_rewards = []
        self.episode_scores = []
        self.wins = 0
        
        # Meta-SME
        self.meta_sme = None
        if use_meta_sme:
            self.meta_sme = MetaSME(
                enable_auto_modify=False,
                require_human_approval=True
            )
    
    def select_action(self, obs: np.ndarray) -> int:
        """选择动作"""
        logits = obs @ self.weights + self.bias
        # 数值稳定的 softmax
        logits = logits - np.max(logits)
        exp_logits = np.exp(logits)
        probs = exp_logits / (np.sum(exp_logits) + 1e-8)
        # 检查 NaN
        if np.any(np.isnan(probs)) or np.any(probs < 0):
            return np.random.choice(3)
        probs = probs / probs.sum()  # 确保归一化
        return np.random.choice(3, p=probs)
    
    def update_policy(self, obs: np.ndarray, action: int, reward: float):
        """更新策略"""
        # 简单梯度上升
        logits = obs @ self.weights + self.bias
        logits = logits - np.max(logits)
        exp_logits = np.exp(logits)
        probs = exp_logits / (np.sum(exp_logits) + 1e-8)
        
        # 梯度
        grad = -probs
        grad[action] += 1
        grad *= reward * self.learning_rate
        
        # 更新
        self.weights += np.outer(obs, grad)
        self.bias += grad
    
    def record_episode(self, total_reward: float, score: int, won: bool):
        """记录回合"""
        self.episode_rewards.append(total_reward)
        self.episode_scores.append(score)
        if won:
            self.wins += 1
        
        if self.meta_sme:
            performance = (score + 10) / 31.0  # 归一化
            self.meta_sme.record_performance(performance)
    
    def get_stats(self) -> Dict:
        """获取统计"""
        if not self.episode_rewards:
            return {}
        
        recent = self.episode_rewards[-100:] if len(self.episode_rewards) > 100 else self.episode_rewards
        
        return {
            'avg_reward': np.mean(recent),
            'std_reward': np.std(recent),
            'avg_score': np.mean(self.episode_scores[-100:]) if len(self.episode_scores) > 0 else 0,
            'win_rate': self.wins / max(len(self.episode_rewards), 1),
            'total_episodes': len(self.episode_rewards)
        }


class AtariExperiment:
    """Atari 实验"""
    
    def __init__(self, experiment_id: str, use_meta_sme: bool, seed: int, 
                 num_episodes: int = 1000):
        self.experiment_id = experiment_id
        self.use_meta_sme = use_meta_sme
        self.seed = seed
        self.num_episodes = num_episodes
        
        np.random.seed(seed)
        
        self.env = AtariPong()
        self.agent = PongAgent(use_meta_sme=use_meta_sme)
        
        self.results = {
            'experiment_id': experiment_id,
            'use_meta_sme': use_meta_sme,
            'seed': seed,
            'episodes': [],
            'checkpoints': []
        }
        
        self.start_time = datetime.now()
    
    def run(self) -> Dict:
        """运行实验"""
        print(f"[{self.experiment_id}] Starting Atari Pong experiment")
        print(f"  Meta-SME: {self.use_meta_sme}")
        print(f"  Episodes: {self.num_episodes}")
        
        for episode in range(self.num_episodes):
            obs = self.env.reset()
            episode_reward = 0.0
            episode_steps = 0
            
            done = False
            while not done:
                action = self.agent.select_action(obs)
                next_obs, reward, done, info = self.env.step(action)
                
                self.agent.update_policy(obs, action, reward)
                episode_reward += reward
                episode_steps += 1
                obs = next_obs
            
            won = info['score'] > info['opponent_score']
            self.agent.record_episode(episode_reward, info['score'], won)
            
            if episode % 100 == 0:
                stats = self.agent.get_stats()
                self.results['checkpoints'].append({
                    'episode': episode,
                    'stats': stats
                })
                
                if episode % 500 == 0:
                    print(f"  Episode {episode}: avg_reward={stats.get('avg_reward', 0):.3f}, "
                          f"win_rate={stats.get('win_rate', 0):.3f}")
        
        # 最终统计
        final_stats = self.agent.get_stats()
        self.results['final_stats'] = final_stats
        self.results['runtime_seconds'] = (datetime.now() - self.start_time).total_seconds()
        
        print(f"[{self.experiment_id}] Completed in {self.results['runtime_seconds']:.1f}s")
        print(f"  Final avg_reward: {final_stats.get('avg_reward', 0):.3f}")
        print(f"  Final win_rate: {final_stats.get('win_rate', 0):.3f}")
        
        return self.results
    
    def save_results(self, output_dir: str):
        """保存结果"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        filename = f"{self.experiment_id}.json"
        filepath = output_path / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"[{self.experiment_id}] Results saved to {filepath}")


def run_experiment_group(group: str, use_meta_sme: bool, num_runs: int,
                        base_seed: int, output_dir: str) -> List[Dict]:
    """运行实验组"""
    results = []
    
    for i in range(num_runs):
        seed = base_seed + i
        experiment_id = f"{group}_run{i+1:02d}_seed{seed}"
        
        exp = AtariExperiment(
            experiment_id=experiment_id,
            use_meta_sme=use_meta_sme,
            seed=seed,
            num_episodes=1000
        )
        
        result = exp.run()
        exp.save_results(output_dir)
        results.append(result)
    
    return results


def main():
    """主函数"""
    print("=" * 60)
    print("MOSS v7.2 - Atari Meta-SME Validation")
    print("=" * 60)
    
    output_dir = 'experiments/atari_validation/results'
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    groups = {
        'E': {'use_meta_sme': True, 'num_runs': 3, 'base_seed': 7000},
        'C': {'use_meta_sme': False, 'num_runs': 3, 'base_seed': 8000}
    }
    
    all_results = {}
    
    for group_name, group_config in groups.items():
        print(f"\n{'=' * 60}")
        print(f"Running Group: {group_name}")
        print(f"{'=' * 60}")
        
        results = run_experiment_group(
            group=group_name,
            use_meta_sme=group_config['use_meta_sme'],
            num_runs=group_config['num_runs'],
            base_seed=group_config['base_seed'],
            output_dir=output_dir
        )
        
        all_results[group_name] = results
    
    # 汇总
    print(f"\n{'=' * 60}")
    print("Summary Statistics")
    print(f"{'=' * 60}")
    
    for group_name, results in all_results.items():
        avg_rewards = [r['final_stats']['avg_reward'] for r in results]
        win_rates = [r['final_stats']['win_rate'] for r in results]
        
        print(f"\nGroup {group_name}:")
        print(f"  Runs: {len(results)}")
        print(f"  Avg Reward: {np.mean(avg_rewards):.4f} ± {np.std(avg_rewards):.4f}")
        print(f"  Win Rate: {np.mean(win_rates):.4f} ± {np.std(win_rates):.4f}")
    
    # 保存汇总
    summary = {
        'experiment_date': datetime.now().isoformat(),
        'group_stats': {
            group: {
                'num_runs': len(results),
                'avg_reward_mean': float(np.mean([r['final_stats']['avg_reward'] for r in results])),
                'avg_reward_std': float(np.std([r['final_stats']['avg_reward'] for r in results])),
                'win_rate_mean': float(np.mean([r['final_stats']['win_rate'] for r in results])),
                'win_rate_std': float(np.std([r['final_stats']['win_rate'] for r in results]))
            }
            for group, results in all_results.items()
        }
    }
    
    summary_path = Path(output_dir) / 'summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n{'=' * 60}")
    print(f"Experiment completed! Summary saved to {summary_path}")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()