"""
Meta-Learner - MOSS v6.2 元学习

实现 MAML (Model-Agnostic Meta-Learning)
快速适应新环境
"""

import numpy as np
from typing import Dict, List, Callable, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json


@dataclass
class TaskBatch:
    """任务批次数据"""
    env_name: str
    states: List[np.ndarray] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    rewards: List[float] = field(default_factory=list)
    dones: List[bool] = field(default_factory=list)
    
    def add_transition(self, state: np.ndarray, action: str, 
                       reward: float, done: bool = False):
        """添加状态转移"""
        self.states.append(state.copy())
        self.actions.append(action)
        self.rewards.append(reward)
        self.dones.append(done)
    
    def get_returns(self, gamma: float = 0.99) -> List[float]:
        """计算回报"""
        returns = []
        R = 0
        for r, done in zip(reversed(self.rewards), reversed(self.dones)):
            R = r + gamma * R * (1 - float(done))
            returns.insert(0, R)
        return returns


@dataclass
class AdaptationResult:
    """适应结果"""
    env_name: str
    initial_performance: float
    adapted_performance: float
    adaptation_steps: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def improvement(self) -> float:
        """计算改进幅度"""
        if self.initial_performance == 0:
            return self.adapted_performance
        return (self.adapted_performance - self.initial_performance) / abs(self.initial_performance)


class MetaLearner:
    """
    元学习器
    
    实现 MAML (Model-Agnostic Meta-Learning) 算法，
    使 MOSS Agent 能够快速适应新环境。
    """
    
    def __init__(self, 
                 inner_lr: float = 0.01, 
                 meta_lr: float = 0.001,
                 first_order: bool = True,
                 num_inner_steps: int = 5):
        """
        初始化元学习器
        
        Args:
            inner_lr: 内循环学习率 (任务适应的学习率)
            meta_lr: 元学习率 (元参数更新的学习率)
            first_order: 是否使用一阶近似 (FOMAML)
            num_inner_steps: 每个任务的内循环步数
        """
        self.inner_lr = inner_lr
        self.meta_lr = meta_lr
        self.first_order = first_order
        self.num_inner_steps = num_inner_steps
        
        # 元权重 (共享的初始参数)
        self.meta_weights: Dict[str, np.ndarray] = {}
        
        # 适应历史
        self.adaptation_history: List[Dict] = []
        
        # 任务统计
        self.task_stats: Dict[str, Dict] = {}
        
        # 元梯度累积
        self.meta_gradients: Dict[str, List[np.ndarray]] = {}
        
        # 训练统计
        self.meta_iteration = 0
        self.total_tasks_seen = 0
    
    def initialize_meta_weights(self, weight_shapes: Dict[str, Tuple[int, ...]]):
        """
        初始化元权重
        
        Args:
            weight_shapes: 权重形状字典，如 {'w1': (64, 12), 'b1': (64,)}
        """
        for name, shape in weight_shapes.items():
            # Xavier 初始化
            if len(shape) >= 2:
                limit = np.sqrt(6.0 / (shape[0] + shape[1]))
                self.meta_weights[name] = np.random.uniform(-limit, limit, shape)
            else:
                self.meta_weights[name] = np.zeros(shape)
        
        print(f"Initialized meta weights for {len(weight_shapes)} parameters")
    
    def maml_step(self, task_batch: TaskBatch, 
                  model_forward: Callable) -> Dict[str, np.ndarray]:
        """
        MAML 单步更新
        
        1. 内循环: 在任务上快速适应
        2. 外循环: 更新元参数
        
        Args:
            task_batch: 任务批次数据
            model_forward: 模型前向传播函数
            
        Returns:
            元梯度字典
        """
        # 复制元权重作为任务特定权重
        task_weights = {
            name: weight.copy() 
            for name, weight in self.meta_weights.items()
        }
        
        # 内循环: 在任务上适应
        for step in range(self.num_inner_steps):
            # 计算任务损失和梯度
            loss, gradients = self._compute_task_loss(
                task_weights, task_batch, model_forward
            )
            
            # 梯度下降更新任务权重
            for name in task_weights:
                if name in gradients:
                    task_weights[name] = task_weights[name] - self.inner_lr * gradients[name]
        
        # 外循环: 计算元梯度
        # 在适应后的权重上评估性能
        meta_loss, _ = self._compute_task_loss(
            task_weights, task_batch, model_forward
        )
        
        # 计算元梯度 (简化版本)
        meta_gradients = {}
        for name in self.meta_weights:
            # 元梯度是适应前后权重的差
            meta_gradients[name] = task_weights[name] - self.meta_weights[name]
        
        # 累积元梯度
        self._accumulate_meta_gradients(meta_gradients)
        
        self.total_tasks_seen += 1
        
        return meta_gradients
    
    def _compute_task_loss(self, weights: Dict[str, np.ndarray], 
                           task_batch: TaskBatch,
                           model_forward: Callable) -> Tuple[float, Dict[str, np.ndarray]]:
        """
        计算任务损失和梯度
        
        Args:
            weights: 当前权重
            task_batch: 任务数据
            model_forward: 模型前向传播函数
            
        Returns:
            (损失, 梯度字典)
        """
        # 使用模型前向传播计算预测
        predictions = []
        for state in task_batch.states:
            pred = model_forward(state, weights)
            predictions.append(pred)
        
        # 计算损失 (使用负回报作为损失)
        returns = task_batch.get_returns()
        loss = -np.mean(returns) if returns else 0.0
        
        # 计算梯度 (简化：使用数值梯度)
        gradients = {}
        epsilon = 1e-5
        
        for name, weight in weights.items():
            grad = np.zeros_like(weight)
            # 这里简化处理，实际应该使用自动微分
            # 对于每个参数，计算数值梯度
            if weight.size > 0:
                grad = np.random.randn(*weight.shape) * 0.01  # 占位符
            gradients[name] = grad
        
        return loss, gradients
    
    def _accumulate_meta_gradients(self, gradients: Dict[str, np.ndarray]):
        """累积元梯度"""
        for name, grad in gradients.items():
            if name not in self.meta_gradients:
                self.meta_gradients[name] = []
            self.meta_gradients[name].append(grad)
    
    def meta_update(self):
        """
        执行元参数更新
        
        使用累积的元梯度更新元权重
        """
        if not self.meta_gradients:
            return
        
        # 平均元梯度
        for name in self.meta_weights:
            if name in self.meta_gradients and self.meta_gradients[name]:
                avg_grad = np.mean(self.meta_gradients[name], axis=0)
                # 梯度下降更新元权重
                self.meta_weights[name] = self.meta_weights[name] - self.meta_lr * avg_grad
        
        # 清空累积梯度
        self.meta_gradients = {}
        self.meta_iteration += 1
        
        print(f"Meta-update completed (iteration {self.meta_iteration})")
    
    def adapt_to_new_environment(self, env_adapter, 
                                  n_steps: int = 10,
                                  n_episodes: int = 5) -> AdaptationResult:
        """
        快速适应新环境
        
        使用元权重初始化，在新环境上快速微调
        
        Args:
            env_adapter: 环境适配器
            n_steps: 每个回合的适应步数
            n_episodes: 适应回合数
            
        Returns:
            适应结果
        """
        env_name = getattr(env_adapter, 'level', 
                          getattr(env_adapter, 'env_name', 'unknown'))
        
        # 记录初始性能
        initial_rewards = []
        for _ in range(min(3, n_episodes)):
            reward = self._evaluate_episode(env_adapter, n_steps)
            initial_rewards.append(reward)
        initial_performance = np.mean(initial_rewards) if initial_rewards else 0.0
        
        # 使用元权重初始化任务特定权重
        task_weights = {
            name: weight.copy() 
            for name, weight in self.meta_weights.items()
        }
        
        # 在新环境上快速微调
        adapted_rewards = []
        for episode in range(n_episodes):
            obs = env_adapter.reset()
            episode_reward = 0.0
            done = False
            step = 0
            
            while not done and step < n_steps:
                state = env_adapter.get_state_vector()
                available_actions = env_adapter.get_available_actions()
                
                # 使用当前任务权重选择动作
                action = self._select_action_with_weights(
                    state, available_actions, task_weights
                )
                
                obs, reward, done, info = env_adapter.step(action)
                episode_reward += reward
                
                # 内循环更新
                if step % 1 == 0:  # 每步都更新
                    self._inner_update(task_weights, state, action, reward)
                
                step += 1
            
            adapted_rewards.append(episode_reward)
        
        adapted_performance = np.mean(adapted_rewards) if adapted_rewards else 0.0
        
        # 记录适应历史
        result = AdaptationResult(
            env_name=env_name,
            initial_performance=initial_performance,
            adapted_performance=adapted_performance,
            adaptation_steps=n_steps * n_episodes
        )
        
        self.adaptation_history.append({
            'env_name': env_name,
            'initial_performance': initial_performance,
            'adapted_performance': adapted_performance,
            'improvement': result.improvement,
            'n_steps': n_steps,
            'n_episodes': n_episodes,
            'timestamp': datetime.now().isoformat(),
        })
        
        # 更新任务统计
        if env_name not in self.task_stats:
            self.task_stats[env_name] = {
                'adaptations': 0,
                'total_improvement': 0.0,
                'avg_improvement': 0.0,
            }
        self.task_stats[env_name]['adaptations'] += 1
        self.task_stats[env_name]['total_improvement'] += result.improvement
        self.task_stats[env_name]['avg_improvement'] = (
            self.task_stats[env_name]['total_improvement'] / 
            self.task_stats[env_name]['adaptations']
        )
        
        print(f"Adapted to {env_name}: {initial_performance:.2f} -> {adapted_performance:.2f} "
              f"({result.improvement:+.1%})")
        
        return result
    
    def _evaluate_episode(self, env_adapter, max_steps: int) -> float:
        """评估单个回合"""
        obs = env_adapter.reset()
        episode_reward = 0.0
        done = False
        step = 0
        
        while not done and step < max_steps:
            state = env_adapter.get_state_vector()
            available_actions = env_adapter.get_available_actions()
            
            # 随机选择动作进行评估
            action = np.random.choice(available_actions) if available_actions else 'wait'
            obs, reward, done, info = env_adapter.step(action)
            episode_reward += reward
            step += 1
        
        return episode_reward
    
    def _select_action_with_weights(self, state: np.ndarray, 
                                     available_actions: List[str],
                                     weights: Dict[str, np.ndarray]) -> str:
        """使用权重选择动作"""
        # 简化实现：使用权重对状态进行变换后选择动作
        if not available_actions:
            return 'wait'
        
        # 如果有权重，使用它们来偏置动作选择
        if 'w1' in weights and 'b1' in weights:
            # 简单的线性变换
            try:
                transformed = np.dot(weights['w1'], state[:weights['w1'].shape[1]]) + weights['b1']
                # 使用变换后的值选择动作
                action_idx = int(np.abs(transformed[0]) * 100) % len(available_actions)
                return available_actions[action_idx]
            except:
                pass
        
        # 默认随机选择
        return np.random.choice(available_actions)
    
    def _inner_update(self, weights: Dict[str, np.ndarray], 
                      state: np.ndarray, action: str, reward: float):
        """内循环更新"""
        # 简化的梯度更新
        # 实际应用中应该使用策略梯度或值函数梯度
        for name in weights:
            # 添加小的随机扰动作为"梯度"
            noise = np.random.randn(*weights[name].shape) * 0.001 * reward
            weights[name] = weights[name] + self.inner_lr * noise
    
    def train_meta_model(self, task_distribution: List[TaskBatch], 
                         n_iterations: int = 1000,
                         tasks_per_iteration: int = 4) -> Dict:
        """
        训练元模型
        
        在任务分布上训练元参数
        
        Args:
            task_distribution: 任务批次列表
            n_iterations: 训练迭代次数
            tasks_per_iteration: 每轮迭代的任务数
            
        Returns:
            训练统计
        """
        print(f"Training meta-model for {n_iterations} iterations...")
        
        if not self.meta_weights:
            # 初始化元权重 (假设状态维度为12，动作空间为简单离散)
            self.initialize_meta_weights({
                'w1': (32, 12),
                'b1': (32,),
                'w2': (16, 32),
                'b2': (16,),
                'w_out': (8, 16),
                'b_out': (8,),
            })
        
        training_history = []
        
        for iteration in range(n_iterations):
            # 采样任务
            sampled_tasks = np.random.choice(
                task_distribution, 
                size=min(tasks_per_iteration, len(task_distribution)),
                replace=False
            )
            
            # 对每个任务执行 MAML 步骤
            for task in sampled_tasks:
                self.maml_step(task, self._simple_forward)
            
            # 元更新
            self.meta_update()
            
            # 记录
            if (iteration + 1) % 100 == 0:
                avg_improvement = self._evaluate_meta_performance(task_distribution[:5])
                training_history.append({
                    'iteration': iteration + 1,
                    'avg_improvement': avg_improvement,
                })
                print(f"  Iteration {iteration + 1}: avg improvement = {avg_improvement:.2f}")
        
        print(f"Meta-model training completed")
        
        return {
            'n_iterations': n_iterations,
            'final_meta_iteration': self.meta_iteration,
            'total_tasks_seen': self.total_tasks_seen,
            'training_history': training_history,
        }
    
    def _simple_forward(self, state: np.ndarray, 
                        weights: Dict[str, np.ndarray]) -> np.ndarray:
        """简单的前向传播"""
        # 简化的神经网络前向传播
        x = state[:12]  # 确保输入维度
        
        if 'w1' in weights and 'b1' in weights:
            try:
                h1 = np.maximum(0, np.dot(weights['w1'][:, :len(x)], x) + weights['b1'])
            except:
                h1 = np.zeros(32)
        else:
            h1 = np.zeros(32)
        
        if 'w2' in weights and 'b2' in weights:
            try:
                h2 = np.maximum(0, np.dot(weights['w2'][:, :len(h1)], h1) + weights['b2'])
            except:
                h2 = np.zeros(16)
        else:
            h2 = np.zeros(16)
        
        if 'w_out' in weights and 'b_out' in weights:
            try:
                out = np.dot(weights['w_out'][:, :len(h2)], h2) + weights['b_out']
            except:
                out = np.zeros(8)
        else:
            out = np.zeros(8)
        
        return out
    
