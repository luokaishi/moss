"""
State AutoEncoder - 状态自编码器

无监督学习状态表征，替代手工特征
"""

import numpy as np
from typing import List, Tuple


class StateAutoEncoder:
    """
    状态自编码器
    
    学习从原始观测到低维潜在表征的映射
    """
    
    def __init__(self, input_dim: int = 64, latent_dim: int = 16, lr: float = 0.01):
        """
        Args:
            input_dim: 原始观测维度
            latent_dim: 潜在表征维度
            lr: 学习率
        """
        self.input_dim = input_dim
        self.latent_dim = latent_dim
        self.lr = lr
        
        # 编码器: input -> latent
        self.W_encoder = np.random.randn(input_dim, latent_dim) * 0.1
        self.b_encoder = np.zeros(latent_dim)
        
        # 解码器: latent -> input
        self.W_decoder = np.random.randn(latent_dim, input_dim) * 0.1
        self.b_decoder = np.zeros(input_dim)
        
        # 训练历史
        self.loss_history: List[float] = []
        
    def encode(self, x: np.ndarray) -> np.ndarray:
        """
        编码: input -> latent
        
        Args:
            x: 原始观测 (input_dim,)
            
        Returns:
            潜在表征 (latent_dim,)
        """
        x = self._normalize(x)
        z = np.tanh(x @ self.W_encoder + self.b_encoder)
        return z
    
    def decode(self, z: np.ndarray) -> np.ndarray:
        """
        解码: latent -> input
        
        Args:
            z: 潜在表征 (latent_dim,)
            
        Returns:
            重构观测 (input_dim,)
        """
        x_recon = np.tanh(z @ self.W_decoder + self.b_decoder)
        return x_recon
    
    def forward(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        前向传播
        
        Returns:
            (latent, reconstruction)
        """
        z = self.encode(x)
        x_recon = self.decode(z)
        return z, x_recon
    
    def train_step(self, x: np.ndarray) -> float:
        """
        单步训练
        
        Args:
            x: 原始观测
            
        Returns:
            重构损失 (MSE)
        """
        x = self._normalize(x)
        
        # 前向
        z, x_recon = self.forward(x)
        
        # 计算损失
        loss = np.mean((x - x_recon) ** 2)
        
        # 反向传播 (简化版梯度下降)
        # 解码器梯度
        d_recon = 2 * (x_recon - x)
        d_decoder = np.outer(z, d_recon * (1 - x_recon ** 2))
        
        # 编码器梯度
        d_encoder = np.outer(x, (d_recon @ self.W_decoder.T) * (1 - z ** 2))
        
        # 更新
        self.W_decoder -= self.lr * d_decoder
        self.b_decoder -= self.lr * np.mean(d_recon * (1 - x_recon ** 2), axis=0)
        self.W_encoder -= self.lr * d_encoder
        self.b_encoder -= self.lr * np.mean((d_recon @ self.W_decoder.T) * (1 - z ** 2), axis=0)
        
        self.loss_history.append(loss)
        if len(self.loss_history) > 1000:
            self.loss_history = self.loss_history[-1000:]
        
        return loss
    
    def train(self, observations: List[np.ndarray], epochs: int = 10):
        """
        训练自编码器
        
        Args:
            observations: 观测列表
            epochs: 训练轮数
        """
        for epoch in range(epochs):
            epoch_loss = 0.0
            for obs in observations:
                loss = self.train_step(obs)
                epoch_loss += loss
            
            avg_loss = epoch_loss / len(observations)
            if (epoch + 1) % 2 == 0:
                print(f"  Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")
    
    def get_representation(self, x: np.ndarray) -> np.ndarray:
        """
        获取表征 (用于下游任务)
        """
        return self.encode(x)
    
    def _normalize(self, x: np.ndarray) -> np.ndarray:
        """归一化输入"""
        if len(x) < self.input_dim:
            x = np.pad(x, (0, self.input_dim - len(x)))
        elif len(x) > self.input_dim:
            x = x[:self.input_dim]
        
        # L2归一化
        norm = np.linalg.norm(x)
        if norm > 0:
            x = x / norm
        return x
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            'input_dim': self.input_dim,
            'latent_dim': self.latent_dim,
            'final_loss': float(np.mean(self.loss_history[-100:])) if self.loss_history else 0.0,
            'loss_trend': 'decreasing' if len(self.loss_history) > 200 and 
                          np.mean(self.loss_history[-100:]) < np.mean(self.loss_history[-200:-100])
                          else 'stable'
        }
