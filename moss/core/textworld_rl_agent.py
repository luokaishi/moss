"""
TextWorld RL Agent - 深度强化学习优化

结合 PPO + MOSS 驱动的混合架构，实现任务导向的智能体
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass, field
from collections import deque
import random
from datetime import datetime

# MOSS imports
from moss.core.drive_manager import DriveManager
from moss.core.environment_v2 import EnvState


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


class PolicyNetwork(nn.Module):
    """策略网络 - PPO Actor"""
    
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 128):
        super().__init__()
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, action_dim)
        
        # 初始化
        nn.init.orthogonal_(self.fc1.weight, gain=np.sqrt(2))
        nn.init.orthogonal_(self.fc2.weight, gain=np.sqrt(2))
        nn.init.orthogonal_(self.fc3.weight, gain=0.01)
        
    def forward(self, state: torch.Tensor) -> torch.Tensor:
        x = torch.relu(self.fc1(state))
        x = torch.relu(self.fc2(x))
        logits = self.fc3(x)
        return torch.softmax(logits, dim=-1)
    
    def get_action(self, state: torch.Tensor, available_mask: Optional[torch.Tensor] = None):
        """采样动作"""
        probs = self.forward(state)
        
        # 应用可用动作掩码
        if available_mask is not None:
            probs = probs * available_mask
            probs = probs / (probs.sum() + 1e-8)
        
        dist = torch.distributions.Categorical(probs)
        action = dist.sample()
        log_prob = dist.log_prob(action)
        
        return action, log_prob, probs


class ValueNetwork(nn.Module):
    """价值网络 - PPO Critic"""
    
    def __init__(self, state_dim: int, hidden_dim: int = 128):
        super().__init__()
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, 1)
        
        nn.init.orthogonal_(self.fc1.weight, gain=np.sqrt(2))
        nn.init.orthogonal_(self.fc2.weight, gain=np.sqrt(2))
        nn.init.orthogonal_(self.fc3.weight, gain=1.0)
        
    def forward(self, state: torch.Tensor) -> torch.Tensor:
        x = torch.relu(self.fc1(state))
        x = torch.relu(self.fc2(x))
        return self.fc3(x)


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


class TextWorldRLAgent:
    """
    TextWorld 强化学习 Agent
    
    结合 PPO + MOSS 驱动的混合架构
    """
    
    def __init__(self, 
                 state_dim: int = 12,
                 action_dim: int = 20,
                 hidden_dim: int = 128,
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
        
        # MOSS 驱动管理器
        self.drive_manager = DriveManager(
            drives_config=[
                {'name': 'survival', 'weight': 0.20, 'evaluator': 'survival'},
                {'name': 'optimization', 'weight': 0.25, 'evaluator': 'optimization'},
                {'name': 'curiosity', 'weight': 0.20, 'evaluator': 'curiosity'},
                {'name': 'influence', 'weight': 0.20, 'evaluator': 'influence'},
                {'name': 'efficiency', 'weight': 0.15},
            ],
            weight_cap_config='v6_default'
        )
        
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
        }
        
        # 动作映射
        self.action_to_command: Dict[int, str] = {}
        self.command_to_action: Dict[str, int] = {}
        
        # RL 和驱动的权重
        self.rl_weight = 0.7
        self.drive_weight = 0.3
        
    def register_actions(self, commands: List[str]):
        """注册可用动作"""
        for i, cmd in enumerate(commands):
            self.action_to_command[i] = cmd
            self.command_to_action[cmd] = i
        
        # 更新动作维度
        self.action_dim = len(commands)
        
        # 重新初始化网络输出层
        if self.policy_net.fc3.out_features != self.action_dim:
            self.policy_net.fc3 = nn.Linear(self.policy_net.fc3.in_features, self.action_dim).to(self.device)
            nn.init.orthogonal_(self.policy_net.fc3.weight, gain=0.01)
    
    def state_to_vector(self, state_info: Dict[str, Any]) -> np.ndarray:
        """将状态信息转换为向量"""
        vector = np.zeros(self.state_dim, dtype=np.float32)
        
        # 0: 归一化分数
        score = state_info.get('score', 0.0)
        max_score = state_info.get('max_score', 10.0)
        vector[0] = np.clip(score / max_score, 0, 1)
        
        # 1: 库存占用率
        inventory = state_info.get('inventory', [])
        vector[1] = np.clip(len(inventory) / 5.0, 0, 1)
        
        # 2: 房间探索进度
        visited_rooms = state_info.get('visited_rooms', [])
        vector[2] = np.clip(len(visited_rooms) / 10.0, 0, 1)
        
        # 3: 可见物品数
        visible_objects = state_info.get('objects_visible', [])
        vector[3] = np.clip(len(visible_objects) / 5.0, 0, 1)
        
        # 4: 可用出口数
        exits = state_info.get('exits', [])
        vector[4] = np.clip(len(exits) / 4.0, 0, 1)
        
        # 5: 房间类型编码
        room_type = state_info.get('room_type', 'generic')
        room_type_encoding = {
            'kitchen': 0.1, 'bedroom': 0.2, 'living': 0.3,
            'bathroom': 0.4, 'hallway': 0.5, 'garden': 0.6,
            'office': 0.7, 'dungeon': 0.8, 'generic': 0.9,
        }
        vector[5] = room_type_encoding.get(room_type, 0.0)
        
        # 6: 步数效率
        moves = state_info.get('moves', 0)
        vector[6] = np.clip(1.0 - (moves / 100.0), 0, 1)
        
        # 7: 交互多样性
        unique_interactions = state_info.get('unique_interactions', 0)
        vector[7] = np.clip(unique_interactions / 20.0, 0, 1)
        
        # 8: 任务进度
        task_progress = state_info.get('task_progress', 0.0)
        vector[8] = task_progress
        
        # 9: 胜利状态
        won = state_info.get('won', False)
        vector[9] = 1.0 if won else 0.0
        
        # 10: 失败状态
        lost = state_info.get('lost', False)
        vector[10] = 1.0 if lost else 0.0
        
        # 11: 环境熵
        entropy = state_info.get('environment_entropy', 0.5)
        vector[11] = entropy
        
        return vector
    
    def select_action(self, state_vector: np.ndarray, available_commands: List[str]) -> Tuple[str, int, float]:
        """
        选择动作 (PPO + 驱动混合)
        
        Returns:
            (command, action_idx, log_prob)
        """
        state_tensor = torch.FloatTensor(state_vector).unsqueeze(0).to(self.device)
        
        # PPO 策略输出
        with torch.no_grad():
            probs = self.policy_net(state_tensor).cpu().numpy()[0]
        
        # MOSS 驱动评分
        drive_scores = self._evaluate_drives(state_vector, available_commands)
        
        # 结合 RL 和驱动
        combined_probs = self._combine_probs(probs, drive_scores, available_commands)
        
        # 采样动作
        action_idx = np.random.choice(len(available_commands), p=combined_probs)
        command = available_commands[action_idx]
        log_prob = np.log(combined_probs[action_idx] + 1e-8)
        
        return command, action_idx, log_prob
    
    def _evaluate_drives(self, state_vector: np.ndarray, available_commands: List[str]) -> np.ndarray:
        """基于 MOSS 驱动评估动作"""
        # 创建 EnvState
        state = EnvState(
            resource_level=1.0 - state_vector[1],  # 库存越少资源越充足
            error_rate=state_vector[10],  # 失败状态
            uptime_hours=state_vector[6] * 100 / 3600,  # 步数转换
            environment_entropy=state_vector[11],
            visited_paths=int(state_vector[2] * 10),
            total_paths=20,
            interactions_count=int(state_vector[7] * 20),
            task_completion_rate=state_vector[8],
        )
        
        # 评估所有驱动
        drive_scores = self.drive_manager.evaluate_all(state)
        
        # 为每个动作计算驱动分数
        action_scores = np.zeros(len(available_commands))
        
        for i, cmd in enumerate(available_commands):
            cmd_lower = cmd.lower()
            
            # 基础分数
            score = 0.5
            
            # 根据命令类型调整
            if 'take' in cmd_lower or 'pick' in cmd_lower:
                score += drive_scores.get('optimization', 0) * 0.3
                score += drive_scores.get('influence', 0) * 0.2
            elif 'go' in cmd_lower or 'move' in cmd_lower:
                score += drive_scores.get('curiosity', 0) * 0.4
                score += drive_scores.get('efficiency', 0) * 0.2
            elif 'examine' in cmd_lower or 'look' in cmd_lower:
                score += drive_scores.get('curiosity', 0) * 0.5
            elif 'open' in cmd_lower or 'unlock' in cmd_lower:
                score += drive_scores.get('optimization', 0) * 0.4
            elif 'inventory' in cmd_lower:
                score += drive_scores.get('survival', 0) * 0.3
            
            # 关键词奖励
            if any(kw in cmd_lower for kw in ['key', 'door', 'chest']):
                score += 0.2
            
            action_scores[i] = score
        
        # 归一化为概率
        if action_scores.sum() > 0:
            action_scores = action_scores / action_scores.sum()
        else:
            action_scores = np.ones(len(available_commands)) / len(available_commands)
        
        return action_scores
    
    def _combine_probs(self, rl_probs: np.ndarray, drive_scores: np.ndarray, 
                       available_commands: List[str]) -> np.ndarray:
        """结合 RL 和驱动概率"""
        # 将 RL 概率映射到可用动作
        rl_mapped = np.zeros(len(available_commands))
        
        # 如果维度匹配直接使用
        if len(rl_probs) == len(available_commands):
            rl_mapped = rl_probs
        else:
            # 否则均匀分布
            rl_mapped = np.ones(len(available_commands)) / len(available_commands)
        
        # 加权结合
        combined = self.rl_weight * rl_mapped + self.drive_weight * drive_scores
        
        # 归一化
        combined = combined / (combined.sum() + 1e-8)
        
        return combined
    
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
        
        # 添加到经验缓冲区
        for i, exp in enumerate(self.episode_buffer):
            exp_with_return = Experience(
                state=exp.state,
                action=exp.action,
                reward=exp.reward,
                next_state=exp.next_state,
                done=exp.done,
                value=returns[i],
                log_prob=exp.log_prob
            )
            self.memory.add(exp_with_return)
        
        # 清空回合缓冲区
        self.episode_buffer.clear()
        self.train_stats['episodes'] += 1
    
    def train(self, batch_size: int = 32, epochs: int = 4) -> Dict[str, float]:
        """训练 PPO"""
        if len(self.memory) < batch_size:
            return {'policy_loss': 0.0, 'value_loss': 0.0, 'entropy_loss': 0.0}
        
        experiences = self.memory.get_all()
        
        # 准备数据
        states = torch.FloatTensor([e.state for e in experiences]).to(self.device)
        actions = torch.LongTensor([e.action for e in experiences]).to(self.device)
        old_log_probs = torch.FloatTensor([e.log_prob for e in experiences]).to(self.device)
        returns = torch.FloatTensor([e.value for e in experiences]).to(self.device)  # value 字段存储 return
        
        # 计算当前价值
        with torch.no_grad():
            values = self.value_net(states).squeeze()
            advantages = returns - values
            advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        # 多 epoch 训练
        policy_losses = []
        value_losses = []
        entropy_losses = []
        
        for _ in range(epochs):
            # 策略更新
            probs = self.policy_net(states)
            dist = torch.distributions.Categorical(probs)
            new_log_probs = dist.log_prob(actions)
            entropy = dist.entropy()
            
            # PPO 损失
            ratio = torch.exp(new_log_probs - old_log_probs)
            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 1 - self.clip_epsilon, 1 + self.clip_epsilon) * advantages
            policy_loss = -torch.min(surr1, surr2).mean()
            
            # 价值损失
            new_values = self.value_net(states).squeeze()
            value_loss = nn.MSELoss()(new_values, returns)
            
            # 熵正则化
            entropy_loss = -entropy.mean()
            
            # 总损失
            total_loss = policy_loss + self.value_coef * value_loss + self.entropy_coef * entropy_loss
            
            # 反向传播
            self.policy_optimizer.zero_grad()
            self.value_optimizer.zero_grad()
            total_loss.backward()
            
            # 梯度裁剪
            nn.utils.clip_grad_norm_(self.policy_net.parameters(), self.max_grad_norm)
            nn.utils.clip_grad_norm_(self.value_net.parameters(), self.max_grad_norm)
            
            self.policy_optimizer.step()
            self.value_optimizer.step()
            
            policy_losses.append(policy_loss.item())
            value_losses.append(value_loss.item())
            entropy_losses.append(entropy_loss.item())
        
        # 清空缓冲区
        self.memory.clear()
        
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
    
    def update_drive_weights(self, reward: float, drive_name: str = 'optimization'):
        """根据奖励更新驱动权重"""
        self.drive_manager.update_weight_from_feedback(drive_name, reward)
    
    def save(self, path: str):
        """保存模型"""
        torch.save({
            'policy_net': self.policy_net.state_dict(),
            'value_net': self.value_net.state_dict(),
            'policy_optimizer': self.policy_optimizer.state_dict(),
            'value_optimizer': self.value_optimizer.state_dict(),
            'train_stats': self.train_stats,
            'action_to_command': self.action_to_command,
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
    
    def get_stats(self) -> Dict[str, Any]:
        """获取训练统计"""
        return {
            'episodes': self.train_stats['episodes'],
            'total_steps': self.train_stats['total_steps'],
            'successes': self.train_stats['successes'],
            'success_rate': self.train_stats['successes'] / max(self.train_stats['episodes'], 1),
            'avg_policy_loss': np.mean(self.train_stats['policy_losses'][-100:]) if self.train_stats['policy_losses'] else 0.0,
            'avg_value_loss': np.mean(self.train_stats['value_losses'][-100:]) if self.train_stats['value_losses'] else 0.0,
            'drive_summary': self.drive_manager.get_drive_summary(),
        }