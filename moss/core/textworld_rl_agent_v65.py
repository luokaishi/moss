"""
TextWorld RL Agent v6.5 - 改进版

结合增强理解 + 泛化优化，目标成功率 70%+
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass
from collections import deque
import random

from moss.core.textworld_enhanced_understanding import EnhancedTextWorldUnderstanding
from moss.core.generalization_optimizer import GeneralizationOptimizer, OptimizationConfig


@dataclass
class Experience:
    """经验元组"""
    state: np.ndarray
    action: int
    reward: float
    next_state: np.ndarray
    done: bool
    value: float
    log_prob: float
    advantage: float = 0.0


class PolicyNetwork(nn.Module):
    """策略网络 - PPO Actor with 泛化优化"""
    
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 256):
        super().__init__()
        
        # 更深的网络结构
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, hidden_dim // 2)
        self.fc4 = nn.Linear(hidden_dim // 2, action_dim)
        
        # Dropout 用于泛化
        self.dropout = nn.Dropout(0.2)
        self.layer_norm1 = nn.LayerNorm(hidden_dim)
        self.layer_norm2 = nn.LayerNorm(hidden_dim)
        self.layer_norm3 = nn.LayerNorm(hidden_dim // 2)
        
        # 初始化
        nn.init.orthogonal_(self.fc1.weight, gain=np.sqrt(2))
        nn.init.orthogonal_(self.fc2.weight, gain=np.sqrt(2))
        nn.init.orthogonal_(self.fc3.weight, gain=np.sqrt(2))
        nn.init.orthogonal_(self.fc4.weight, gain=0.01)
        
    def forward(self, state: torch.Tensor, training: bool = True) -> torch.Tensor:
        x = torch.relu(self.fc1(state))
        x = self.layer_norm1(x)
        if training:
            x = self.dropout(x)
        
        x = torch.relu(self.fc2(x))
        x = self.layer_norm2(x)
        if training:
            x = self.dropout(x)
        
        x = torch.relu(self.fc3(x))
        x = self.layer_norm3(x)
        
        logits = self.fc4(x)
        return torch.softmax(logits, dim=-1)
    
    def get_action(self, state: torch.Tensor, available_mask: Optional[torch.Tensor] = None):
        """采样动作"""
        probs = self.forward(state, training=False)
        
        # 应用可用动作掩码
        if available_mask is not None:
            probs = probs * available_mask
            probs = probs / (probs.sum() + 1e-8)
        
        dist = torch.distributions.Categorical(probs)
        action = dist.sample()
        log_prob = dist.log_prob(action)
        entropy = dist.entropy()
        
        return action, log_prob, probs, entropy


class ValueNetwork(nn.Module):
    """价值网络 - PPO Critic with 泛化优化"""
    
    def __init__(self, state_dim: int, hidden_dim: int = 256):
        super().__init__()
        
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, hidden_dim // 2)
        self.fc4 = nn.Linear(hidden_dim // 2, 1)
        
        self.dropout = nn.Dropout(0.2)
        self.layer_norm1 = nn.LayerNorm(hidden_dim)
        self.layer_norm2 = nn.LayerNorm(hidden_dim)
        self.layer_norm3 = nn.LayerNorm(hidden_dim // 2)
        
        nn.init.orthogonal_(self.fc1.weight, gain=np.sqrt(2))
        nn.init.orthogonal_(self.fc2.weight, gain=np.sqrt(2))
        nn.init.orthogonal_(self.fc3.weight, gain=np.sqrt(2))
        nn.init.orthogonal_(self.fc4.weight, gain=1.0)
        
    def forward(self, state: torch.Tensor, training: bool = True) -> torch.Tensor:
        x = torch.relu(self.fc1(state))
        x = self.layer_norm1(x)
        if training:
            x = self.dropout(x)
        
        x = torch.relu(self.fc2(x))
        x = self.layer_norm2(x)
        if training:
            x = self.dropout(x)
        
        x = torch.relu(self.fc3(x))
        x = self.layer_norm3(x)
        
        return self.fc4(x)


class PPOMemory:
    """PPO 经验缓冲区"""
    
    def __init__(self, capacity: int = 10000):
        self.capacity = capacity
        self.buffer: deque = deque(maxlen=capacity)
        
    def add(self, experience: Experience):
        self.buffer.append(experience)
        
    def clear(self):
        self.buffer.clear()
        
    def get_all(self) -> List[Experience]:
        return list(self.buffer)
    
    def __len__(self):
        return len(self.buffer)


class TextWorldRLAgentV65:
    """
    TextWorld RL Agent v6.5
    
    改进点：
    1. 增强的环境理解模块
    2. 泛化优化（Dropout, LayerNorm, 数据增强）
    3. 自适应探索-利用平衡
    4. 失败学习和成功模式记忆
    5. 多环境训练支持
    """
    
    def __init__(self, 
                 state_dim: int = 20,  # 增强理解模块的状态维度
                 action_dim: int = 20,
                 hidden_dim: int = 256,
                 lr: float = 3e-4,
                 gamma: float = 0.99,
                 gae_lambda: float = 0.95,
                 clip_epsilon: float = 0.2,
                 value_coef: float = 0.5,
                 entropy_coef: float = 0.01,
                 max_grad_norm: float = 0.5,
                 device: str = 'cpu'):
        
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.device = torch.device(device)
        
        # PPO 超参数
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.clip_epsilon = clip_epsilon
        self.value_coef = value_coef
        self.entropy_coef = entropy_coef
        self.max_grad_norm = max_grad_norm
        
        # 网络
        self.policy_net = PolicyNetwork(state_dim, action_dim, hidden_dim).to(self.device)
        self.value_net = ValueNetwork(state_dim, hidden_dim).to(self.device)
        
        # 优化器
        self.policy_optimizer = optim.Adam(self.policy_net.parameters(), lr=lr)
        self.value_optimizer = optim.Adam(self.value_net.parameters(), lr=lr)
        
        # 学习率调度器
        self.policy_scheduler = optim.lr_scheduler.StepLR(self.policy_optimizer, step_size=500, gamma=0.9)
        self.value_scheduler = optim.lr_scheduler.StepLR(self.value_optimizer, step_size=500, gamma=0.9)
        
        # 增强理解模块
        self.understanding = EnhancedTextWorldUnderstanding()
        
        # 泛化优化器
        opt_config = OptimizationConfig(
            augmentation_enabled=True,
            noise_std=0.05,
            dropout_rate=0.2,
            early_stopping_enabled=False,
            ensemble_enabled=False,
        )
        self.gen_optimizer = GeneralizationOptimizer(opt_config)
        
        # 经验缓冲区
        self.memory = PPOMemory(capacity=10000)
        self.episode_buffer: List[Experience] = []
        
        # 训练统计
        self.train_stats = {
            'episodes': 0,
            'total_steps': 0,
            'policy_losses': [],
            'value_losses': [],
            'entropy_losses': [],
            'successes': 0,
            'eval_success_rates': [],
        }
        
        # 动作映射
        self.action_to_command: Dict[int, str] = {}
        self.command_to_action: Dict[str, int] = {}
        
        # 探索-利用平衡
        self.exploration_rate = 0.4
        self.min_exploration = 0.05
        self.exploration_decay = 0.995
        
        # 理解模块和RL的权重
        self.understanding_weight = 0.6
        self.rl_weight = 0.4
        
        # 失败学习
        self.consecutive_failures = 0
        self.max_consecutive_failures = 5
        
    def register_actions(self, commands: List[str]):
        """注册可用动作"""
        self.action_to_command.clear()
        self.command_to_action.clear()
        
        for i, cmd in enumerate(commands):
            self.action_to_command[i] = cmd
            self.command_to_action[cmd] = i
        
        # 更新动作维度
        self.action_dim = len(commands)
        
        # 重新初始化网络输出层
        if self.policy_net.fc4.out_features != self.action_dim:
            self.policy_net.fc4 = nn.Linear(self.policy_net.fc4.in_features, self.action_dim).to(self.device)
            nn.init.orthogonal_(self.policy_net.fc4.weight, gain=0.01)
    
    def select_action(self, obs: str, available_commands: List[str], 
                      info: Optional[Dict] = None, training: bool = True) -> Tuple[str, int, float]:
        """
        选择动作（理解模块 + RL 混合）
        
        Returns:
            (command, action_idx, log_prob)
        """
        # 解析观察
        parsed = self.understanding.parse_observation(obs, info)
        
        # 获取状态向量
        state_vector = self.understanding.get_state_vector()
        state_tensor = torch.FloatTensor(state_vector).unsqueeze(0).to(self.device)
        
        # 使用理解模块规划
        planned_action = self.understanding.plan_next_action(parsed, available_commands)
        
        # 获取 RL 策略输出
        with torch.no_grad():
            rl_probs = self.policy_net(state_tensor, training=False).cpu().numpy()[0]
        
        # 创建可用动作掩码
        available_mask = torch.zeros(self.action_dim).to(self.device)
        command_to_idx = {cmd: idx for idx, cmd in self.action_to_command.items()}
        
        valid_indices = []
        for cmd in available_commands:
            if cmd in command_to_idx:
                idx = command_to_idx[cmd]
                available_mask[idx] = 1.0
                valid_indices.append(idx)
        
        # 结合理解模块和 RL
        if planned_action and planned_action in self.command_to_action:
            # 如果规划的动作可用
            planned_idx = self.command_to_action[planned_action]
            
            # 以 exploration_rate 的概率使用规划的动作
            if training and random.random() > self.exploration_rate:
                action_idx = planned_idx
                # 计算 log_prob
                with torch.no_grad():
                    _, log_prob, _, _ = self.policy_net.get_action(state_tensor, available_mask)
                    log_prob = log_prob.cpu().item()
                return planned_action, action_idx, log_prob
        
        # 使用 RL 策略
        with torch.no_grad():
            action_tensor, log_prob, probs, _ = self.policy_net.get_action(state_tensor, available_mask)
            action_idx = action_tensor.cpu().item()
            log_prob = log_prob.cpu().item()
        
        # 获取命令
        if action_idx in self.action_to_command:
            command = self.action_to_command[action_idx]
        else:
            # 回退到随机选择
            command = random.choice(available_commands)
            action_idx = self.command_to_action.get(command, 0)
        
        return command, action_idx, log_prob
    
    def store_experience(self, state: np.ndarray, action: int, reward: float,
                         next_state: np.ndarray, done: bool, value: float, log_prob: float):
        """存储经验"""
        exp = Experience(
            state=state,
            action=action,
            reward=reward,
            next_state=next_state,
            done=done,
            value=value,
            log_prob=log_prob
        )
        self.episode_buffer.append(exp)
    
    def end_episode(self, final_value: float = 0.0):
        """结束回合，处理经验"""
        if not self.episode_buffer:
            return
        
        # 计算回报和优势
        returns = []
        advantages = []
        
        gae = 0.0
        next_value = final_value
        
        for exp in reversed(self.episode_buffer):
            if exp.done:
                next_value = 0.0
                gae = 0.0
            
            delta = exp.reward + self.gamma * next_value - exp.value
            gae = delta + self.gamma * self.gae_lambda * gae
            
            returns.insert(0, gae + exp.value)
            advantages.insert(0, gae)
            
            next_value = exp.value
        
        # 归一化优势
        advantages = np.array(advantages)
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        # 添加到经验缓冲区
        for i, exp in enumerate(self.episode_buffer):
            exp_with_return = Experience(
                state=exp.state,
                action=exp.action,
                reward=exp.reward,
                next_state=exp.next_state,
                done=exp.done,
                value=returns[i],
                log_prob=exp.log_prob,
                advantage=advantages[i]
            )
            self.memory.add(exp_with_return)
        
        # 清空回合缓冲区
        self.episode_buffer.clear()
        self.train_stats['episodes'] += 1
    
    def train(self, batch_size: int = 64, epochs: int = 4) -> Dict[str, float]:
        """训练 PPO"""
        if len(self.memory) < batch_size:
            return {'policy_loss': 0.0, 'value_loss': 0.0, 'entropy_loss': 0.0}
        
        experiences = self.memory.get_all()
        
        # 准备数据
        states = torch.FloatTensor([e.state for e in experiences]).to(self.device)
        actions = torch.LongTensor([e.action for e in experiences]).to(self.device)
        old_log_probs = torch.FloatTensor([e.log_prob for e in experiences]).to(self.device)
        returns = torch.FloatTensor([e.value for e in experiences]).to(self.device)
        advantages = torch.FloatTensor([e.advantage for e in experiences]).to(self.device)
        
        policy_losses = []
        value_losses = []
        entropy_losses = []
        
        for _ in range(epochs):
            # 数据增强：添加噪声
            if self.gen_optimizer.config.augmentation_enabled:
                noise = torch.randn_like(states) * self.gen_optimizer.config.noise_std
                states_aug = states + noise
            else:
                states_aug = states
            
            # 策略更新
            probs = self.policy_net(states_aug, training=True)
            dist = torch.distributions.Categorical(probs)
            new_log_probs = dist.log_prob(actions)
            entropy = dist.entropy()
            
            # PPO 损失
            ratio = torch.exp(new_log_probs - old_log_probs)
            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 1 - self.clip_epsilon, 1 + self.clip_epsilon) * advantages
            policy_loss = -torch.min(surr1, surr2).mean()
            
            # 价值损失
            new_values = self.value_net(states_aug, training=True).squeeze()
            value_loss = nn.MSELoss()(new_values, returns)
            
            # 熵正则化
            entropy_loss = -entropy.mean()
            
            # 总损失
            total_policy_loss = policy_loss + self.entropy_coef * entropy_loss
            
            # 反向传播 - 策略
            self.policy_optimizer.zero_grad()
            total_policy_loss.backward()
            nn.utils.clip_grad_norm_(self.policy_net.parameters(), self.max_grad_norm)
            self.policy_optimizer.step()
            
            # 反向传播 - 价值
            self.value_optimizer.zero_grad()
            value_loss.backward()
            nn.utils.clip_grad_norm_(self.value_net.parameters(), self.max_grad_norm)
            self.value_optimizer.step()
            
            policy_losses.append(policy_loss.item())
            value_losses.append(value_loss.item())
            entropy_losses.append(entropy_loss.item())
        
        # 清空缓冲区
        self.memory.clear()
        
        # 更新学习率
        self.policy_scheduler.step()
        self.value_scheduler.step()
        
        # 更新统计
        avg_policy_loss = np.mean(policy_losses)
        avg_value_loss = np.mean(value_losses)
        avg_entropy_loss = np.mean(entropy_losses)
        
        self.train_stats['policy_losses'].append(avg_policy_loss)
        self.train_stats['value_losses'].append(avg_value_loss)
        self.train_stats['entropy_losses'].append(avg_entropy_loss)
        
        return {
            'policy_loss': avg_policy_loss,
            'value_loss': avg_value_loss,
            'entropy_loss': avg_entropy_loss,
        }
    
    def train_episode(self, env, max_steps: int = 100) -> Tuple[float, int, bool, Dict]:
        """
        训练一个 episode
        
        Returns:
            (total_reward, steps, success, info)
        """
        obs, info = env.reset()
        self.understanding.reset()  # 重置理解模块
        
        done = False
        steps = 0
        total_reward = 0.0
        
        while not done and steps < max_steps:
            # 获取可用动作
            available_actions = info.get('admissible_commands', [])
            if not available_actions:
                available_actions = ['look', 'inventory']
            
            # 注册动作
            self.register_actions(available_actions)
            
            # 获取当前状态
            state_vector = self.understanding.get_state_vector()
            
            # 选择动作
            command, action_idx, log_prob = self.select_action(
                obs, available_actions, info, training=True
            )
            
            # 获取价值估计
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state_vector).unsqueeze(0).to(self.device)
                value = self.value_net(state_tensor, training=False).cpu().item()
            
            # 执行动作
            next_obs, reward, done, next_info = env.step(command)
            
            # 更新理解模块
            self.understanding.learn_from_outcome(command, next_obs, reward, next_info.get('won', False))
            
            # 获取下一状态
            next_state_vector = self.understanding.get_state_vector()
            
            # 存储经验
            self.store_experience(state_vector, action_idx, reward, 
                                  next_state_vector, done, value, log_prob)
            
            total_reward += reward
            steps += 1
            obs = next_obs
            info = next_info
        
        # 结束回合
        final_value = 0.0
        if not done:
            with torch.no_grad():
                state_tensor = torch.FloatTensor(self.understanding.get_state_vector()).unsqueeze(0).to(self.device)
                final_value = self.value_net(state_tensor, training=False).cpu().item()
        
        self.end_episode(final_value)
        
        # 更新统计
        won = info.get('won', False)
        if won:
            self.train_stats['successes'] += 1
            self.consecutive_failures = 0
        else:
            self.consecutive_failures += 1
        
        self.train_stats['total_steps'] += steps
        
        # 衰减探索率
        self.exploration_rate = max(
            self.min_exploration,
            self.exploration_rate * self.exploration_decay
        )
        
        return total_reward, steps, won, info
    
    def evaluate(self, env, episodes: int = 50, max_steps: int = 100) -> float:
        """评估 Agent"""
        successes = 0
        
        for _ in range(episodes):
            obs, info = env.reset()
            understanding = EnhancedTextWorldUnderstanding()  # 新的理解器
            
            done = False
            steps = 0
            
            while not done and steps < max_steps:
                available_actions = info.get('admissible_commands', [])
                if not available_actions:
                    break
                
                self.register_actions(available_actions)
                
                # 解析观察
                parsed = understanding.parse_observation(obs, info)
                state_vector = understanding.get_state_vector()
                
                # 选择动作（评估时不使用探索）
                command, _, _ = self.select_action(obs, available_actions, info, training=False)
                
                # 执行
                obs, _, done, info = env.step(command)
                steps += 1
                
                if info.get('won', False):
                    successes += 1
                    break
        
        success_rate = successes / episodes
        self.train_stats['eval_success_rates'].append(success_rate)
        return success_rate
    
    def save(self, path: str):
        """保存模型"""
        torch.save({
            'policy_net': self.policy_net.state_dict(),
            'value_net': self.value_net.state_dict(),
            'policy_optimizer': self.policy_optimizer.state_dict(),
            'value_optimizer': self.value_optimizer.state_dict(),
            'train_stats': self.train_stats,
            'action_to_command': self.action_to_command,
            'exploration_rate': self.exploration_rate,
        }, path)
    
    def load(self, path: str):
        """加载模型"""
        checkpoint = torch.load(path, map_location=self.device)
        self.policy_net.load_state_dict(checkpoint['policy_net'])
        self.value_net.load_state_dict(checkpoint['value_net'])
        self.policy_optimizer.load_state_dict(checkpoint['policy_optimizer'])
        self.value_optimizer.load_state_dict(checkpoint['value_optimizer'])
        self.train_stats = checkpoint.get('train_stats', self.train_stats)
        self.action_to_command = checkpoint.get('action_to_command', self.action_to_command)
        self.exploration_rate = checkpoint.get('exploration_rate', self.exploration_rate)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取训练统计"""
        episodes = max(self.train_stats['episodes'], 1)
        return {
            'episodes': self.train_stats['episodes'],
            'total_steps': self.train_stats['total_steps'],
            'successes': self.train_stats['successes'],
            'success_rate': self.train_stats['successes'] / episodes,
            'avg_policy_loss': np.mean(self.train_stats['policy_losses'][-100:]) if self.train_stats['policy_losses'] else 0.0,
            'avg_value_loss': np.mean(self.train_stats['value_losses'][-100:]) if self.train_stats['value_losses'] else 0.0,
            'exploration_rate': self.exploration_rate,
            'understanding_summary': self.understanding.get_summary(),
        }
