"""
GPU Trainer - MOSS v6.4 GPU Accelerated Training

使用 PyTorch 实现 GPU 加速训练，支持混合精度 (FP16)

Features:
- PyTorch GPU training
- Mixed precision (FP16)
- Data parallel training
- Automatic mixed precision (AMP)
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import time


class GPUTrainer:
    """GPU 训练器"""
    
    def __init__(self, device='auto', use_amp=True):
        """
        Args:
            device: 'cuda', 'cpu', or 'auto'
            use_amp: 使用自动混合精度
        """
        self.device = self._setup_device(device)
        self.use_amp = use_amp and self.device == 'cuda'
        
        # PyTorch 组件
        self.scaler = None
        if self.use_amp:
            try:
                from torch.cuda.amp import GradScaler
                self.scaler = GradScaler()
            except ImportError:
                print("Warning: AMP not available")
                self.use_amp = False
        
        self.training_stats = {
            'total_steps': 0,
            'gpu_time': 0,
            'data_time': 0,
            'throughput': []
        }
    
    def _setup_device(self, device: str) -> str:
        """设置计算设备"""
        if device == 'auto':
            try:
                import torch
                if torch.cuda.is_available():
                    device = 'cuda'
                    print(f"GPU detected: {torch.cuda.get_device_name(0)}")
                else:
                    device = 'cpu'
                    print("No GPU detected, using CPU")
            except ImportError:
                device = 'cpu'
                print("PyTorch not installed, using CPU")
        return device
    
    def train_epoch(self, model, dataloader, optimizer, loss_fn):
        """训练一个 epoch"""
        try:
            import torch
            import torch.nn as nn
        except ImportError:
            print("PyTorch not installed, using CPU fallback")
            return self._train_epoch_cpu(model, dataloader, optimizer, loss_fn)
        
        model.train()
        model.to(self.device)
        
        total_loss = 0
        correct = 0
        total = 0
        
        epoch_start = time.time()
        
        for batch_idx, (data, target) in enumerate(dataloader):
            data_start = time.time()
            
            # 数据转移到 GPU
            data = data.to(self.device)
            target = target.to(self.device)
            
            data_time = time.time() - data_start
            self.training_stats['data_time'] += data_time
            
            gpu_start = time.time()
            
            # 前向传播
            optimizer.zero_grad()
            
            if self.use_amp:
                # 混合精度训练
                with torch.cuda.amp.autocast():
                    output = model(data)
                    loss = loss_fn(output, target)
                
                # 反向传播
                self.scaler.scale(loss).backward()
                self.scaler.step(optimizer)
                self.scaler.update()
            else:
                # 普通训练
                output = model(data)
                loss = loss_fn(output, target)
                loss.backward()
                optimizer.step()
            
            gpu_time = time.time() - gpu_start
            self.training_stats['gpu_time'] += gpu_time
            
            # 统计
            total_loss += loss.item()
            _, predicted = output.max(1)
            total += target.size(0)
            correct += predicted.eq(target).sum().item()
            
            self.training_stats['total_steps'] += 1
            
            # 计算吞吐量
            throughput = len(data) / (data_time + gpu_time)
            self.training_stats['throughput'].append(throughput)
        
        epoch_time = time.time() - epoch_start
        
        return {
            'loss': total_loss / len(dataloader),
            'accuracy': correct / total,
            'epoch_time': epoch_time,
            'throughput': np.mean(self.training_stats['throughput'][-100:])
        }
    
    def _train_epoch_cpu(self, model, dataloader, optimizer, loss_fn):
        """CPU 训练回退"""
        model.train()
        total_loss = 0
        correct = 0
        total = 0
        
        for data, target in dataloader:
            output = model(data)
            loss = loss_fn(output, target)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            _, predicted = output.max(1)
            total += target.size(0)
            correct += predicted.eq(target).sum().item()
        
        return {
            'loss': total_loss / len(dataloader),
            'accuracy': correct / total,
            'epoch_time': 0,
            'throughput': 0
        }
    
    def evaluate(self, model, dataloader, loss_fn):
        """评估模型"""
        try:
            import torch
        except ImportError:
            return self._evaluate_cpu(model, dataloader, loss_fn)
        
        model.eval()
        model.to(self.device)
        
        total_loss = 0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for data, target in dataloader:
                data = data.to(self.device)
                target = target.to(self.device)
                
                output = model(data)
                loss = loss_fn(output, target)
                
                total_loss += loss.item()
                _, predicted = output.max(1)
                total += target.size(0)
                correct += predicted.eq(target).sum().item()
        
        return {
            'loss': total_loss / len(dataloader),
            'accuracy': correct / total
        }
    
    def _evaluate_cpu(self, model, dataloader, loss_fn):
        """CPU 评估回退"""
        model.eval()
        total_loss = 0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for data, target in dataloader:
                output = model(data)
                loss = loss_fn(output, target)
                
                total_loss += loss.item()
                _, predicted = output.max(1)
                total += target.size(0)
                correct += predicted.eq(target).sum().item()
        
        return {
            'loss': total_loss / len(dataloader),
            'accuracy': correct / total
        }
    
    def get_stats(self) -> Dict:
        """获取训练统计"""
        return {
            'device': self.device,
            'use_amp': self.use_amp,
            'total_steps': self.training_stats['total_steps'],
            'avg_gpu_time': self.training_stats['gpu_time'] / max(1, self.training_stats['total_steps']),
            'avg_data_time': self.training_stats['data_time'] / max(1, self.training_stats['total_steps']),
            'avg_throughput': np.mean(self.training_stats['throughput']) if self.training_stats['throughput'] else 0
        }


class MOSSGPUAgent:
    """MOSS GPU Agent"""
    
    def __init__(self, state_dim=12, action_dim=10, hidden_dim=128):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_dim = hidden_dim
        
        # 创建网络
        self.policy_net = self._create_network()
        self.value_net = self._create_network(output_dim=1)
        
        # GPU 训练器
        self.trainer = GPUTrainer()
        
        # 优化器
        self.policy_optimizer = None
        self.value_optimizer = None
        
        self._setup_optimizers()
    
    def _create_network(self, output_dim=None):
        """创建神经网络"""
        try:
            import torch
            import torch.nn as nn
            
            if output_dim is None:
                output_dim = self.action_dim
            
            class Network(nn.Module):
                def __init__(self, input_dim, hidden_dim, output_dim):
                    super().__init__()
                    self.fc1 = nn.Linear(input_dim, hidden_dim)
                    self.fc2 = nn.Linear(hidden_dim, hidden_dim)
                    self.fc3 = nn.Linear(hidden_dim, output_dim)
                    self.relu = nn.ReLU()
                
                def forward(self, x):
                    x = self.relu(self.fc1(x))
                    x = self.relu(self.fc2(x))
                    x = self.fc3(x)
                    return x
            
            return Network(self.state_dim, self.hidden_dim, output_dim)
        except ImportError:
            return None
    
    def _setup_optimizers(self):
        """设置优化器"""
        try:
            import torch.optim as optim
            
            if self.policy_net:
                self.policy_optimizer = optim.Adam(
                    self.policy_net.parameters(),
                    lr=0.0003
                )
            
            if self.value_net:
                self.value_optimizer = optim.Adam(
                    self.value_net.parameters(),
                    lr=0.0003
                )
        except ImportError:
            pass
    
    def select_action(self, state, explore=True):
        """选择动作"""
        try:
            import torch
            
            if self.policy_net is None:
                return np.random.randint(self.action_dim)
            
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            state_tensor = state_tensor.to(self.trainer.device)
            
            with torch.no_grad():
                logits = self.policy_net(state_tensor)
                probs = torch.softmax(logits, dim=-1)
            
            if explore:
                action = torch.multinomial(probs, 1).item()
            else:
                action = probs.argmax().item()
            
            return action
        except ImportError:
            return np.random.randint(self.action_dim)
    
    def train_step(self, batch):
        """训练一步"""
        if self.policy_net is None or self.policy_optimizer is None:
            return {}
        
        try:
            import torch
            import torch.nn.functional as F
            
            states, actions, rewards, next_states, dones = batch
            
            # 转换为 tensor
            states = torch.FloatTensor(states).to(self.trainer.device)
            actions = torch.LongTensor(actions).to(self.trainer.device)
            rewards = torch.FloatTensor(rewards).to(self.trainer.device)
            
            # 策略损失
            logits = self.policy_net(states)
            log_probs = F.log_softmax(logits, dim=-1)
            selected_log_probs = log_probs.gather(1, actions.unsqueeze(1)).squeeze()
            
            # 简单策略梯度
            loss = -(selected_log_probs * rewards).mean()
            
            # 优化
            self.policy_optimizer.zero_grad()
            
            if self.trainer.use_amp and self.trainer.scaler:
                from torch.cuda.amp import autocast
                with autocast():
                    loss = -(selected_log_probs * rewards).mean()
                self.trainer.scaler.scale(loss).backward()
                self.trainer.scaler.step(self.policy_optimizer)
                self.trainer.scaler.update()
            else:
                loss.backward()
                self.policy_optimizer.step()
            
            return {'policy_loss': loss.item()}
        except ImportError:
            return {}
    
    def save(self, path):
        """保存模型"""
        try:
            import torch
            torch.save({
                'policy_net': self.policy_net.state_dict() if self.policy_net else None,
                'value_net': self.value_net.state_dict() if self.value_net else None
            }, path)
        except ImportError:
            np.save(path, {})
    
    def load(self, path):
        """加载模型"""
        try:
            import torch
            checkpoint = torch.load(path)
            if self.policy_net and checkpoint['policy_net']:
                self.policy_net.load_state_dict(checkpoint['policy_net'])
            if self.value_net and checkpoint['value_net']:
                self.value_net.load_state_dict(checkpoint['value_net'])
        except ImportError:
            pass


def benchmark_gpu_speedup():
    """基准测试 GPU 加速"""
    print("\n" + "="*70)
    print("GPU Speedup Benchmark")
    print("="*70)
    
    try:
        import torch
        
        # 检查 GPU
        if torch.cuda.is_available():
            print(f"GPU: {torch.cuda.get_device_name(0)}")
            print(f"CUDA Version: {torch.version.cuda}")
        else:
            print("No GPU available")
            return
        
        # 创建测试数据
        batch_size = 256
        input_dim = 128
        hidden_dim = 256
        output_dim = 10
        
        # 创建模型
        model = torch.nn.Sequential(
            torch.nn.Linear(input_dim, hidden_dim),
            torch.nn.ReLU(),
            torch.nn.Linear(hidden_dim, hidden_dim),
            torch.nn.ReLU(),
            torch.nn.Linear(hidden_dim, output_dim)
        )
        
        data = torch.randn(batch_size, input_dim)
        target = torch.randint(0, output_dim, (batch_size,))
        
        # CPU 测试
        print("\nCPU Training:")
        model_cpu = model.cpu()
        optimizer_cpu = torch.optim.Adam(model_cpu.parameters())
        loss_fn = torch.nn.CrossEntropyLoss()
        
        start = time.time()
        for _ in range(100):
            optimizer_cpu.zero_grad()
            output = model_cpu(data)
            loss = loss_fn(output, target)
            loss.backward()
            optimizer_cpu.step()
        cpu_time = time.time() - start
        print(f"  Time: {cpu_time:.3f}s")
        
        # GPU 测试
        print("\nGPU Training:")
        model_gpu = model.cuda()
        optimizer_gpu = torch.optim.Adam(model_gpu.parameters())
        data_gpu = data.cuda()
        target_gpu = target.cuda()
        
        # Warmup
        for _ in range(10):
            output = model_gpu(data_gpu)
            loss = loss_fn(output, target_gpu)
        
        torch.cuda.synchronize()
        start = time.time()
        for _ in range(100):
            optimizer_gpu.zero_grad()
            output = model_gpu(data_gpu)
            loss = loss_fn(output, target_gpu)
            loss.backward()
            optimizer_gpu.step()
        torch.cuda.synchronize()
        gpu_time = time.time() - start
        print(f"  Time: {gpu_time:.3f}s")
        
        # 加速比
        speedup = cpu_time / gpu_time
        print(f"\nSpeedup: {speedup:.2f}x")
        print("="*70)
        
    except ImportError:
        print("PyTorch not installed")


if __name__ == '__main__':
    # 运行基准测试
    benchmark_gpu_speedup()
