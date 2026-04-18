"""
Generalization Optimizer - MOSS v6.4

泛化优化模块，提供以下功能：
- 数据增强
- Dropout 正则化
- 早停机制
- 集成学习
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional, Callable, Any
from dataclasses import dataclass, field
from collections import deque
import copy
import random


@dataclass
class OptimizationConfig:
    """优化配置"""
    # 数据增强
    augmentation_enabled: bool = True
    noise_std: float = 0.1
    dropout_rate: float = 0.2
    
    # 早停
    early_stopping_enabled: bool = True
    patience: int = 10
    min_delta: float = 0.001
    
    # 集成学习
    ensemble_enabled: bool = True
    ensemble_size: int = 5
    
    # 训练
    batch_size: int = 32
    learning_rate: float = 0.001
    max_epochs: int = 100


class DataAugmenter:
    """数据增强器"""
    
    def __init__(self, config: OptimizationConfig):
        self.config = config
    
    def add_noise(self, data: np.ndarray, noise_std: float = None) -> np.ndarray:
        """添加高斯噪声"""
        if noise_std is None:
            noise_std = self.config.noise_std
        noise = np.random.normal(0, noise_std, data.shape)
        return data + noise
    
    def random_scale(self, data: np.ndarray, scale_range: Tuple[float, float] = (0.9, 1.1)) -> np.ndarray:
        """随机缩放"""
        scale = np.random.uniform(*scale_range)
        return data * scale
    
    def random_shift(self, data: np.ndarray, shift_range: float = 0.1) -> np.ndarray:
        """随机平移"""
        shift = np.random.uniform(-shift_range, shift_range, data.shape)
        return data + shift
    
    def mixup(self, data1: np.ndarray, data2: np.ndarray, alpha: float = 0.2) -> np.ndarray:
        """Mixup 数据增强"""
        lam = np.random.beta(alpha, alpha)
        return lam * data1 + (1 - lam) * data2
    
    def augment_batch(self, batch: np.ndarray) -> np.ndarray:
        """对整个批次进行增强"""
        if not self.config.augmentation_enabled:
            return batch
        
        augmented = []
        for sample in batch:
            # 随机选择增强方法
            aug_type = random.choice(['noise', 'scale', 'shift', 'none'])
            
            if aug_type == 'noise':
                sample = self.add_noise(sample)
            elif aug_type == 'scale':
                sample = self.random_scale(sample)
            elif aug_type == 'shift':
                sample = self.random_shift(sample)
            
            augmented.append(sample)
        
        return np.array(augmented)


class RegularizedNetwork(nn.Module):
    """带正则化的神经网络"""
    
    def __init__(self, input_dim: int, hidden_dims: List[int], output_dim: int,
                 dropout_rate: float = 0.2, use_batch_norm: bool = True):
        super().__init__()
        
        self.layers = nn.ModuleList()
        self.batch_norms = nn.ModuleList() if use_batch_norm else None
        self.dropouts = nn.ModuleList()
        
        prev_dim = input_dim
        for hidden_dim in hidden_dims:
            self.layers.append(nn.Linear(prev_dim, hidden_dim))
            if use_batch_norm:
                self.batch_norms.append(nn.BatchNorm1d(hidden_dim))
            self.dropouts.append(nn.Dropout(dropout_rate))
            prev_dim = hidden_dim
        
        self.output_layer = nn.Linear(prev_dim, output_dim)
        self.dropout_rate = dropout_rate
        self.use_batch_norm = use_batch_norm
    
    def forward(self, x: torch.Tensor, training: bool = True) -> torch.Tensor:
        for i, layer in enumerate(self.layers):
            x = layer(x)
            if self.use_batch_norm:
                x = self.batch_norms[i](x)
            x = F.relu(x)
            if training:
                x = self.dropouts[i](x)
        
        x = self.output_layer(x)
        return x
    
    def get_l2_regularization(self) -> torch.Tensor:
        """获取 L2 正则化损失"""
        l2_loss = 0.0
        for param in self.parameters():
            l2_loss += torch.sum(param ** 2)
        return l2_loss


class EarlyStopping:
    """早停机制"""
    
    def __init__(self, patience: int = 10, min_delta: float = 0.001,
                 restore_best_weights: bool = True):
        self.patience = patience
        self.min_delta = min_delta
        self.restore_best_weights = restore_best_weights
        
        self.best_loss = float('inf')
        self.best_weights = None
        self.counter = 0
        self.early_stop = False
    
    def __call__(self, val_loss: float, model: nn.Module = None) -> bool:
        """
        检查是否应该早停
        
        Returns:
            True 如果应该停止训练
        """
        if val_loss < self.best_loss - self.min_delta:
            self.best_loss = val_loss
            self.counter = 0
            if self.restore_best_weights and model is not None:
                self.best_weights = copy.deepcopy(model.state_dict())
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
                if self.restore_best_weights and self.best_weights is not None:
                    model.load_state_dict(self.best_weights)
                return True
        
        return False
    
    def reset(self):
        """重置状态"""
        self.best_loss = float('inf')
        self.best_weights = None
        self.counter = 0
        self.early_stop = False


class EnsembleModel:
    """集成学习模型"""
    
    def __init__(self, base_model_class: type, model_params: Dict,
                 ensemble_size: int = 5, device: str = 'cpu'):
        self.ensemble_size = ensemble_size
        self.device = device
        self.models = []
        
        # 创建多个模型实例
        for i in range(ensemble_size):
            model = base_model_class(**model_params).to(device)
            self.models.append(model)
    
    def fit(self, X_train: np.ndarray, y_train: np.ndarray,
            X_val: Optional[np.ndarray] = None,
            y_val: Optional[np.ndarray] = None,
            epochs: int = 100, batch_size: int = 32,
            learning_rate: float = 0.001) -> Dict:
        """
        训练集成模型
        
        Returns:
            训练历史
        """
        histories = []
        
        for i, model in enumerate(self.models):
            print(f"Training ensemble model {i+1}/{self.ensemble_size}")
            
            # 使用不同的数据子集 (Bootstrap)
            indices = np.random.choice(len(X_train), size=len(X_train), replace=True)
            X_subset = X_train[indices]
            y_subset = y_train[indices]
            
            history = self._train_single_model(
                model, X_subset, y_subset, X_val, y_val,
                epochs, batch_size, learning_rate
            )
            histories.append(history)
        
        return {'ensemble_histories': histories}
    
    def _train_single_model(self, model: nn.Module, X_train: np.ndarray, y_train: np.ndarray,
                           X_val: np.ndarray, y_val: np.ndarray,
                           epochs: int, batch_size: int, learning_rate: float) -> Dict:
        """训练单个模型"""
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        
        history = {'train_loss': [], 'val_loss': []}
        
        X_train_t = torch.FloatTensor(X_train).to(self.device)
        y_train_t = torch.FloatTensor(y_train).to(self.device)
        
        if X_val is not None:
            X_val_t = torch.FloatTensor(X_val).to(self.device)
            y_val_t = torch.FloatTensor(y_val).to(self.device)
        
        for epoch in range(epochs):
            model.train()
            optimizer.zero_grad()
            
            outputs = model(X_train_t, training=True)
            loss = criterion(outputs.squeeze(), y_train_t)
            loss.backward()
            optimizer.step()
            
            history['train_loss'].append(loss.item())
            
            if X_val is not None:
                model.eval()
                with torch.no_grad():
                    val_outputs = model(X_val_t, training=False)
                    val_loss = criterion(val_outputs.squeeze(), y_val_t)
                    history['val_loss'].append(val_loss.item())
        
        return history
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        集成预测
        
        Returns:
            平均预测结果
        """
        X_t = torch.FloatTensor(X).to(self.device)
        predictions = []
        
        for model in self.models:
            model.eval()
            with torch.no_grad():
                pred = model(X_t, training=False).cpu().numpy()
                predictions.append(pred)
        
        # 平均所有模型的预测
        return np.mean(predictions, axis=0)
    
    def predict_with_uncertainty(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        带不确定性的预测
        
        Returns:
            (mean_prediction, uncertainty)
        """
        X_t = torch.FloatTensor(X).to(self.device)
        predictions = []
        
        for model in self.models:
            model.eval()
            with torch.no_grad():
                pred = model(X_t, training=False).cpu().numpy()
                predictions.append(pred)
        
        predictions = np.array(predictions)
        mean_pred = np.mean(predictions, axis=0)
        uncertainty = np.std(predictions, axis=0)
        
        return mean_pred, uncertainty


class GeneralizationOptimizer:
    """
    泛化优化器主类
    
    整合数据增强、正则化、早停和集成学习
    """
    
    def __init__(self, config: Optional[OptimizationConfig] = None):
        self.config = config or OptimizationConfig()
        self.augmenter = DataAugmenter(self.config)
        self.early_stopping = EarlyStopping(
            patience=self.config.patience,
            min_delta=self.config.min_delta
        ) if self.config.early_stopping_enabled else None
    
    def optimize(self, model: nn.Module, X_train: np.ndarray, y_train: np.ndarray,
                 X_val: np.ndarray, y_val: np.ndarray,
                 epochs: int = 100, l2_lambda: float = 0.01) -> Dict:
        """
        执行完整的优化流程
        
        Args:
            model: 要优化的模型
            X_train, y_train: 训练数据
            X_val, y_val: 验证数据
            epochs: 训练轮数
            l2_lambda: L2 正则化系数
        
        Returns:
            训练历史
        """
        device = next(model.parameters()).device
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=self.config.learning_rate)
        
        history = {
            'train_loss': [],
            'val_loss': [],
            'train_acc': [],
            'val_acc': []
        }
        
        X_train_t = torch.FloatTensor(X_train).to(device)
        y_train_t = torch.FloatTensor(y_train).to(device)
        X_val_t = torch.FloatTensor(X_val).to(device)
        y_val_t = torch.FloatTensor(y_val).to(device)
        
        for epoch in range(epochs):
            model.train()
            optimizer.zero_grad()
            
            # 数据增强
            if self.config.augmentation_enabled:
                X_aug = self.augmenter.augment_batch(X_train)
                X_batch = torch.FloatTensor(X_aug).to(device)
            else:
                X_batch = X_train_t
            
            # 前向传播
            outputs = model(X_batch, training=True)
            loss = criterion(outputs.squeeze(), y_train_t)
            
            # L2 正则化
            if hasattr(model, 'get_l2_regularization'):
                l2_loss = model.get_l2_regularization()
                loss = loss + l2_lambda * l2_loss
            
            # 反向传播
            loss.backward()
            optimizer.step()
            
            # 验证
            model.eval()
            with torch.no_grad():
                train_outputs = model(X_train_t, training=False)
                train_loss = criterion(train_outputs.squeeze(), y_train_t)
                
                val_outputs = model(X_val_t, training=False)
                val_loss = criterion(val_outputs.squeeze(), y_val_t)
            
            history['train_loss'].append(train_loss.item())
            history['val_loss'].append(val_loss.item())
            
            # 早停检查
            if self.early_stopping is not None:
                if self.early_stopping(val_loss.item(), model):
                    print(f"Early stopping at epoch {epoch+1}")
                    break
            
            if (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch+1}/{epochs}: train_loss={train_loss:.4f}, val_loss={val_loss:.4f}")
        
        return history
    
    def create_ensemble(self, input_dim: int, hidden_dims: List[int],
                       output_dim: int) -> EnsembleModel:
        """
        创建集成模型
        
        Args:
            input_dim: 输入维度
            hidden_dims: 隐藏层维度列表
            output_dim: 输出维度
        
        Returns:
            集成模型
        """
        model_params = {
            'input_dim': input_dim,
            'hidden_dims': hidden_dims,
            'output_dim': output_dim,
            'dropout_rate': self.config.dropout_rate,
            'use_batch_norm': True
        }
        
        return EnsembleModel(
            RegularizedNetwork,
            model_params,
            ensemble_size=self.config.ensemble_size
        )
    
    def evaluate_generalization(self, model: nn.Module, X_test: np.ndarray,
                               y_test: np.ndarray) -> Dict:
        """
        评估泛化性能
        
        Returns:
            评估指标
        """
        device = next(model.parameters()).device
        X_test_t = torch.FloatTensor(X_test).to(device)
        y_test_t = torch.FloatTensor(y_test).to(device)
        
        model.eval()
        with torch.no_grad():
            predictions = model(X_test_t, training=False).cpu().numpy()
        
        # 计算指标
        mse = np.mean((predictions.squeeze() - y_test) ** 2)
        mae = np.mean(np.abs(predictions.squeeze() - y_test))
        
        return {
            'mse': mse,
            'mae': mae,
            'rmse': np.sqrt(mse),
            'predictions': predictions
        }


def compare_optimization_strategies(X_train: np.ndarray, y_train: np.ndarray,
                                    X_val: np.ndarray, y_val: np.ndarray,
                                    X_test: np.ndarray, y_test: np.ndarray,
                                    input_dim: int, hidden_dims: List[int],
                                    output_dim: int = 1) -> Dict:
    """
    对比不同优化策略的效果
    
    Returns:
        对比结果
    """
    results = {}
    
    # 1. 基准模型 (无优化)
    print("="*50)
    print("Training Baseline Model (No Optimization)")
    print("="*50)
    
    baseline_config = OptimizationConfig(
        augmentation_enabled=False,
        early_stopping_enabled=False,
        ensemble_enabled=False,
        dropout_rate=0.0
    )
    baseline_optimizer = GeneralizationOptimizer(baseline_config)
    baseline_model = RegularizedNetwork(input_dim, hidden_dims, output_dim, dropout_rate=0.0).to('cpu')
    
    baseline_history = baseline_optimizer.optimize(
        baseline_model, X_train, y_train, X_val, y_val, epochs=50, l2_lambda=0.0
    )
    baseline_eval = baseline_optimizer.evaluate_generalization(baseline_model, X_test, y_test)
    
    results['baseline'] = {
        'history': baseline_history,
        'test_mse': baseline_eval['mse'],
        'test_mae': baseline_eval['mae']
    }
    
    # 2. 带正则化的模型
    print("\n" + "="*50)
    print("Training Regularized Model")
    print("="*50)
    
    reg_config = OptimizationConfig(
        augmentation_enabled=False,
        early_stopping_enabled=True,
        ensemble_enabled=False,
        dropout_rate=0.2
    )
    reg_optimizer = GeneralizationOptimizer(reg_config)
    reg_model = RegularizedNetwork(input_dim, hidden_dims, output_dim, dropout_rate=0.2).to('cpu')
    
    reg_history = reg_optimizer.optimize(
        reg_model, X_train, y_train, X_val, y_val, epochs=50, l2_lambda=0.01
    )
    reg_eval = reg_optimizer.evaluate_generalization(reg_model, X_test, y_test)
    
    results['regularized'] = {
        'history': reg_history,
        'test_mse': reg_eval['mse'],
        'test_mae': reg_eval['mae']
    }
    
    # 3. 带数据增强的模型
    print("\n" + "="*50)
    print("Training with Data Augmentation")
    print("="*50)
    
    aug_config = OptimizationConfig(
        augmentation_enabled=True,
        early_stopping_enabled=True,
        ensemble_enabled=False,
        dropout_rate=0.2
    )
    aug_optimizer = GeneralizationOptimizer(aug_config)
    aug_model = RegularizedNetwork(input_dim, hidden_dims, output_dim, dropout_rate=0.2).to('cpu')
    
    aug_history = aug_optimizer.optimize(
        aug_model, X_train, y_train, X_val, y_val, epochs=50, l2_lambda=0.01
    )
    aug_eval = aug_optimizer.evaluate_generalization(aug_model, X_test, y_test)
    
    results['augmented'] = {
        'history': aug_history,
        'test_mse': aug_eval['mse'],
        'test_mae': aug_eval['mae']
    }
    
    # 4. 集成模型
    print("\n" + "="*50)
    print("Training Ensemble Model")
    print("="*50)
    
    ensemble_config = OptimizationConfig(
        ensemble_enabled=True,
        ensemble_size=5
    )
    ensemble_optimizer = GeneralizationOptimizer(ensemble_config)
    ensemble_model = ensemble_optimizer.create_ensemble(input_dim, hidden_dims, output_dim)
    
    ensemble_model.fit(X_train, y_train, X_val, y_val, epochs=50)
    
    # 评估集成模型
    predictions = ensemble_model.predict(X_test)
    ensemble_mse = np.mean((predictions.squeeze() - y_test) ** 2)
    ensemble_mae = np.mean(np.abs(predictions.squeeze() - y_test))
    
    results['ensemble'] = {
        'test_mse': ensemble_mse,
        'test_mae': ensemble_mae
    }
    
    # 打印对比结果
    print("\n" + "="*50)
    print("Comparison Results")
    print("="*50)
    print(f"{'Method':<20} {'Test MSE':<15} {'Test MAE':<15}")
    print("-"*50)
    for method, result in results.items():
        print(f"{method:<20} {result['test_mse']:<15.4f} {result['test_mae']:<15.4f}")
    
    return results


# 便捷函数
def create_optimizer(config: Optional[Dict] = None) -> GeneralizationOptimizer:
    """创建优化器"""
    if config is None:
        opt_config = OptimizationConfig()
    else:
        opt_config = OptimizationConfig(**config)
    return GeneralizationOptimizer(opt_config)


def get_default_config() -> OptimizationConfig:
    """获取默认配置"""
    return OptimizationConfig()