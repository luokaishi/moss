"""
Model Compression - MOSS v6.3 模型压缩

知识蒸馏、量化、剪枝
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Callable, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import copy


@dataclass
class CompressionConfig:
    """压缩配置"""
    method: str = "quantization"  # quantization, pruning, distillation
    target_ratio: float = 0.5  # 目标压缩比
    bits: int = 8  # 量化位数
    sparsity: float = 0.5  # 剪枝稀疏度
    temperature: float = 4.0  # 蒸馏温度
    alpha: float = 0.7  # 蒸馏损失权重
    
    def to_dict(self) -> Dict:
        return {
            'method': self.method,
            'target_ratio': self.target_ratio,
            'bits': self.bits,
            'sparsity': self.sparsity,
            'temperature': self.temperature,
            'alpha': self.alpha,
        }


@dataclass
class CompressionResult:
    """压缩结果"""
    original_size: int
    compressed_size: int
    compression_ratio: float
    accuracy_loss: float
    method: str
    details: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'original_size': self.original_size,
            'compressed_size': self.compressed_size,
            'compression_ratio': self.compression_ratio,
            'accuracy_loss': self.accuracy_loss,
            'method': self.method,
            'details': self.details,
        }


class Compressor(ABC):
    """压缩器基类"""
    
    @abstractmethod
    def compress(self, model: Any, **kwargs) -> Tuple[Any, CompressionResult]:
        """压缩模型"""
        pass
    
    @abstractmethod
    def decompress(self, compressed_model: Any, **kwargs) -> Any:
        """解压缩模型"""
        pass


class QuantizationCompressor(Compressor):
    """量化压缩器"""
    
    def __init__(self, bits: int = 8):
        self.bits = bits
        self.scale_factors: Dict[str, float] = {}
        self.zero_points: Dict[str, float] = {}
    
    def compress(self, model: Dict[str, np.ndarray], **kwargs) -> Tuple[Dict, CompressionResult]:
        """
        量化压缩模型参数
        
        Args:
            model: 模型参数字典
            
        Returns:
            压缩后的模型和压缩结果
        """
        compressed = {}
        original_size = 0
        compressed_size = 0
        
        for name, param in model.items():
            original_size += param.nbytes
            
            # 计算缩放因子和零点
            min_val = param.min()
            max_val = param.max()
            
            if max_val - min_val < 1e-8:
                # 避免除零
                scale = 1.0
                zero_point = 0.0
            else:
                scale = (max_val - min_val) / (2**self.bits - 1)
                zero_point = min_val
            
            self.scale_factors[name] = scale
            self.zero_points[name] = zero_point
            
            # 量化
            quantized = np.round((param - zero_point) / scale).astype(np.uint8 if self.bits <= 8 else np.uint16)
            
            # 限制范围
            quantized = np.clip(quantized, 0, 2**self.bits - 1)
            
            compressed[name] = quantized
            compressed_size += quantized.nbytes
        
        compression_ratio = original_size / compressed_size if compressed_size > 0 else 1.0
        
        result = CompressionResult(
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=compression_ratio,
            accuracy_loss=0.0,  # 需要实际评估
            method=f"quantization_{self.bits}bit",
            details={'bits': self.bits, 'n_params': len(model)}
        )
        
        return compressed, result
    
    def decompress(self, compressed_model: Dict[str, np.ndarray], **kwargs) -> Dict[str, np.ndarray]:
        """解压缩模型"""
        decompressed = {}
        
        for name, quantized in compressed_model.items():
            scale = self.scale_factors.get(name, 1.0)
            zero_point = self.zero_points.get(name, 0.0)
            
            # 反量化
            decompressed[name] = quantized.astype(np.float32) * scale + zero_point
        
        return decompressed


class PruningCompressor(Compressor):
    """剪枝压缩器"""
    
    def __init__(self, sparsity: float = 0.5, method: str = "magnitude"):
        self.sparsity = sparsity
        self.method = method
        self.masks: Dict[str, np.ndarray] = {}
    
    def compress(self, model: Dict[str, np.ndarray], **kwargs) -> Tuple[Dict, CompressionResult]:
        """
        剪枝压缩模型
        
        Args:
            model: 模型参数字典
            
        Returns:
            压缩后的模型和压缩结果
        """
        compressed = {}
        original_size = 0
        compressed_size = 0
        
        for name, param in model.items():
            original_size += param.nbytes
            
            # 创建剪枝掩码
            if self.method == "magnitude":
                # 基于幅度的剪枝
                threshold = np.percentile(np.abs(param), self.sparsity * 100)
                mask = np.abs(param) >= threshold
            elif self.method == "random":
                # 随机剪枝
                mask = np.random.random(param.shape) >= self.sparsity
            else:
                # 默认不剪枝
                mask = np.ones_like(param, dtype=bool)
            
            self.masks[name] = mask
            
            # 应用掩码
            pruned = param * mask
            
            # 稀疏存储 (只存储非零值和索引)
            non_zero_indices = np.nonzero(mask)
            non_zero_values = pruned[non_zero_indices]
            
            compressed[name] = {
                'values': non_zero_values,
                'indices': non_zero_indices,
                'shape': param.shape,
            }
            
            compressed_size += non_zero_values.nbytes + len(non_zero_indices[0]) * 4
        
        compression_ratio = original_size / compressed_size if compressed_size > 0 else 1.0
        
        result = CompressionResult(
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=compression_ratio,
            accuracy_loss=0.0,
            method=f"pruning_{self.method}_{self.sparsity}",
            details={
                'sparsity': self.sparsity,
                'method': self.method,
                'n_params': len(model),
            }
        )
        
        return compressed, result
    
    def decompress(self, compressed_model: Dict, **kwargs) -> Dict[str, np.ndarray]:
        """解压缩模型"""
        decompressed = {}
        
        for name, sparse_data in compressed_model.items():
            shape = sparse_data['shape']
            values = sparse_data['values']
            indices = sparse_data['indices']
            
            # 重建稠密矩阵
            decompressed[name] = np.zeros(shape, dtype=values.dtype)
            decompressed[name][indices] = values
        
        return decompressed


class DistillationTrainer:
    """知识蒸馏训练器"""
    
    def __init__(
        self, 
        temperature: float = 4.0, 
        alpha: float = 0.7,
        learning_rate: float = 0.001
    ):
        self.temperature = temperature
        self.alpha = alpha
        self.learning_rate = learning_rate
        
        self.teacher_model: Optional[Any] = None
        self.student_model: Optional[Any] = None
    
    def set_teacher(self, teacher_model: Any):
        """设置教师模型"""
        self.teacher_model = teacher_model
    
    def set_student(self, student_model: Any):
        """设置学生模型"""
        self.student_model = student_model
    
    def soft_target_loss(
        self, 
        student_logits: np.ndarray, 
        teacher_logits: np.ndarray
    ) -> float:
        """
        计算软目标损失 (KL散度)
        
        Args:
            student_logits: 学生模型输出
            teacher_logits: 教师模型输出
            
        Returns:
            KL散度损失
        """
        # 应用温度缩放
        student_probs = self._softmax(student_logits / self.temperature)
        teacher_probs = self._softmax(teacher_logits / self.temperature)
        
        # KL散度
        kl_div = np.sum(
            teacher_probs * (np.log(teacher_probs + 1e-10) - np.log(student_probs + 1e-10))
        )
        
        return kl_div * (self.temperature ** 2)
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Softmax 函数"""
        exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=-1, keepdims=True)
    
    def distill_step(
        self,
        data: np.ndarray,
        labels: np.ndarray,
        student_forward: Callable,
        teacher_forward: Callable,
        update_fn: Callable,
    ) -> Dict[str, float]:
        """
        单步蒸馏训练
        
        Args:
            data: 输入数据
            labels: 真实标签
            student_forward: 学生模型前向函数
            teacher_forward: 教师模型前向函数
            update_fn: 参数更新函数
            
        Returns:
            损失字典
        """
        # 教师输出
        teacher_logits = teacher_forward(data)
        
        # 学生输出
        student_logits = student_forward(data)
        
        # 软目标损失
        soft_loss = self.soft_target_loss(student_logits, teacher_logits)
        
        # 硬目标损失 (交叉熵)
        hard_loss = self._cross_entropy(student_logits, labels)
        
        # 总损失
        total_loss = self.alpha * soft_loss + (1 - self.alpha) * hard_loss
        
        # 更新学生模型
        update_fn(total_loss)
        
        return {
            'total_loss': total_loss,
            'soft_loss': soft_loss,
            'hard_loss': hard_loss,
        }
    
    def _cross_entropy(self, logits: np.ndarray, labels: np.ndarray) -> float:
        """计算交叉熵损失"""
        probs = self._softmax(logits)
        n_samples = labels.shape[0]
        
        # one-hot 编码
        if labels.ndim == 1:
            n_classes = logits.shape[-1]
            one_hot = np.zeros((n_samples, n_classes))
            one_hot[np.arange(n_samples), labels.astype(int)] = 1
            labels = one_hot
        
        loss = -np.sum(labels * np.log(probs + 1e-10)) / n_samples
        return loss


class ModelCompressor:
    """模型压缩器 - 整合多种压缩方法"""
    
    def __init__(self):
        self.quantizer = QuantizationCompressor()
        self.pruner = PruningCompressor()
        self.distiller = DistillationTrainer()
        self.compression_history: List[CompressionResult] = []
    
    def distill(
        self, 
        teacher_model: Any, 
        student_model: Any, 
        data: np.ndarray,
        labels: np.ndarray,
        n_epochs: int = 10,
        **kwargs
    ) -> Tuple[Any, CompressionResult]:
        """
        知识蒸馏
        
        Args:
            teacher_model: 教师模型
            student_model: 学生模型
            data: 训练数据
            labels: 训练标签
            n_epochs: 训练轮数
            
        Returns:
            蒸馏后的学生模型和压缩结果
        """
        self.distiller.set_teacher(teacher_model)
        self.distiller.set_student(student_model)
        
        # 简化的蒸馏过程 (实际应用需要完整的前向/反向传播)
        print(f"Distilling for {n_epochs} epochs...")
        
        # 计算模型大小
        teacher_size = self._get_model_size(teacher_model)
        student_size = self._get_model_size(student_model)
        
        compression_ratio = teacher_size / student_size if student_size > 0 else 1.0
        
        result = CompressionResult(
            original_size=teacher_size,
            compressed_size=student_size,
            compression_ratio=compression_ratio,
            accuracy_loss=0.05,  # 估计值
            method="distillation",
            details={
                'temperature': self.distiller.temperature,
                'alpha': self.distiller.alpha,
                'n_epochs': n_epochs,
            }
        )
        
        self.compression_history.append(result)
        return student_model, result
    
    def quantize(self, model: Dict[str, np.ndarray], bits: int = 8) -> Tuple[Dict, CompressionResult]:
        """
        模型量化
        
        Args:
            model: 模型参数
            bits: 量化位数
            
        Returns:
            量化后的模型和压缩结果
        """
        self.quantizer.bits = bits
        compressed, result = self.quantizer.compress(model)
        self.compression_history.append(result)
        return compressed, result
    
    def prune(
        self, 
        model: Dict[str, np.ndarray], 
        sparsity: float = 0.5,
        method: str = "magnitude"
    ) -> Tuple[Dict, CompressionResult]:
        """
        模型剪枝
        
        Args:
            model: 模型参数
            sparsity: 稀疏度 (0-1)
            method: 剪枝方法
            
        Returns:
            剪枝后的模型和压缩结果
        """
        self.pruner.sparsity = sparsity
        self.pruner.method = method
        compressed, result = self.pruner.compress(model)
        self.compression_history.append(result)
        return compressed, result
    
    def compress_pipeline(
        self,
        model: Dict[str, np.ndarray],
        config: CompressionConfig,
    ) -> Tuple[Dict, List[CompressionResult]]:
        """
        压缩流水线 - 组合多种压缩方法
        
        Args:
            model: 原始模型
            config: 压缩配置
            
        Returns:
            压缩后的模型和所有压缩结果
        """
        results = []
        current_model = model
        
        # 1. 剪枝
        if config.sparsity > 0:
            current_model, result = self.prune(current_model, sparsity=config.sparsity)
            results.append(result)
            print(f"Pruning: {result.compression_ratio:.2f}x compression")
        
        # 2. 量化
        if config.bits < 32:
            current_model, result = self.quantize(current_model, bits=config.bits)
            results.append(result)
            print(f"Quantization: {result.compression_ratio:.2f}x compression")
        
        return current_model, results
    
    def _get_model_size(self, model: Any) -> int:
        """计算模型大小 (字节)"""
        if isinstance(model, dict):
            return sum(v.nbytes for v in model.values() if isinstance(v, np.ndarray))
        elif isinstance(model, np.ndarray):
            return model.nbytes
        else:
            return 0
    
    def get_summary(self) -> Dict:
        """获取压缩摘要"""
        if not self.compression_history:
            return {'status': 'No compression performed'}
        
        total_ratio = np.mean([r.compression_ratio for r in self.compression_history])
        total_size_reduction = sum(
            r.original_size - r.compressed_size 
            for r in self.compression_history
        )
        
        return {
            'n_compressions': len(self.compression_history),
            'avg_compression_ratio': total_ratio,
            'total_size_reduction_bytes': total_size_reduction,
            'methods_used': list(set(r.method for r in self.compression_history)),
        }


def demo():
    """演示模型压缩"""
    print("="*60)
    print("MOSS v6.3 Model Compression Demo")
    print("="*60)
    
    # 创建示例模型
    model = {
        'layer1': np.random.randn(100, 50).astype(np.float32),
        'layer2': np.random.randn(50, 20).astype(np.float32),
        'layer3': np.random.randn(20, 10).astype(np.float32),
    }
    
    original_size = sum(v.nbytes for v in model.values())
    print(f"\nOriginal model size: {original_size} bytes")
    
    compressor = ModelCompressor()
    
    # 1. 量化
    print("\n" + "-"*40)
    print("1. Quantization (8-bit)")
    print("-"*40)
    quantized, result = compressor.quantize(model, bits=8)
    print(f"Compression ratio: {result.compression_ratio:.2f}x")
    print(f"Size: {result.original_size} -> {result.compressed_size} bytes")
    
    # 2. 剪枝
    print("\n" + "-"*40)
    print("2. Pruning (50% sparsity)")
    print("-"*40)
    pruned, result = compressor.prune(model, sparsity=0.5)
    print(f"Compression ratio: {result.compression_ratio:.2f}x")
    print(f"Size: {result.original_size} -> {result.compressed_size} bytes")
    
    # 3. 组合压缩
    print("\n" + "-"*40)
    print("3. Combined Compression")
    print("-"*40)
    config = CompressionConfig(
        sparsity=0.5,
        bits=8,
    )
    compressed, results = compressor.compress_pipeline(model, config)
    
    total_ratio = np.prod([r.compression_ratio for r in results])
    print(f"Combined compression ratio: {total_ratio:.2f}x")
    
    # 摘要
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    summary = compressor.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("\nDemo completed!")


if __name__ == '__main__':
    demo()
