"""
Distributed Trainer - MOSS v6.3 分布式训练

支持多机并行训练
"""

import multiprocessing as mp
from typing import Dict, List, Callable, Optional, Any, Tuple
import numpy as np
import time
from dataclasses import dataclass, field
from datetime import datetime
import pickle
import os
from pathlib import Path


@dataclass
class TrainingConfig:
    """训练配置"""
    env_name: str = "default"
    episodes: int = 100
    max_steps: int = 100
    learning_rate: float = 0.001
    gamma: float = 0.99
    seed: int = 42
    
    def to_dict(self) -> Dict:
        return {
            'env_name': self.env_name,
            'episodes': self.episodes,
            'max_steps': self.max_steps,
            'learning_rate': self.learning_rate,
            'gamma': self.gamma,
            'seed': self.seed,
        }


@dataclass
class TrainingResult:
    """训练结果"""
    config: TrainingConfig
    worker_id: int
    total_reward: float
    success_count: int
    episode_rewards: List[float]
    training_time: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            'config': self.config.to_dict(),
            'worker_id': self.worker_id,
            'total_reward': self.total_reward,
            'success_count': self.success_count,
            'episode_rewards': self.episode_rewards,
            'training_time': self.training_time,
            'timestamp': self.timestamp,
        }


class DistributedTrainer:
    """分布式训练器 - 支持单机多进程和多机并行"""
    
    def __init__(self, n_workers: int = 4, use_gpu: bool = False):
        """
        初始化分布式训练器
        
        Args:
            n_workers: 工作进程数
            use_gpu: 是否使用 GPU (当前版本仅支持 CPU)
        """
        self.n_workers = n_workers
        self.use_gpu = use_gpu
        self.pool: Optional[mp.Pool] = None
        self.results: List[TrainingResult] = []
        self.global_model: Optional[Dict] = None
        
        # 训练统计
        self.stats = {
            'total_episodes': 0,
            'total_rewards': 0.0,
            'start_time': None,
            'end_time': None,
        }
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self
    
    def __exit__(self, *args):
        """上下文管理器出口"""
        self.stop()
    
    def start(self):
        """启动进程池"""
        if self.pool is None:
            self.pool = mp.Pool(processes=self.n_workers)
            print(f"DistributedTrainer: Started {self.n_workers} workers")
    
    def stop(self):
        """停止进程池"""
        if self.pool is not None:
            self.pool.close()
            self.pool.join()
            self.pool = None
            print("DistributedTrainer: Stopped all workers")
    
    def train_parallel(
        self, 
        train_fn: Callable[[TrainingConfig], TrainingResult],
        configs: List[TrainingConfig]
    ) -> List[TrainingResult]:
        """
        并行训练多个配置
        
        Args:
            train_fn: 训练函数，接收配置返回结果
            configs: 训练配置列表
            
        Returns:
            训练结果列表
        """
        if self.pool is None:
            self.start()
        
        self.stats['start_time'] = datetime.now().isoformat()
        print(f"Starting parallel training with {len(configs)} configs...")
        
        # 并行执行训练
        results = self.pool.map(train_fn, configs)
        
        self.results = results
        self.stats['end_time'] = datetime.now().isoformat()
        self.stats['total_episodes'] = sum(r.config.episodes for r in results)
        self.stats['total_rewards'] = sum(r.total_reward for r in results)
        
        print(f"Parallel training completed: {len(results)} results")
        return results
    
    def train_map_reduce(
        self,
        map_fn: Callable[[Any], Any],
        reduce_fn: Callable[[List[Any]], Any],
        data: List[Any]
    ) -> Any:
        """
        Map-Reduce 风格的分布式训练
        
        Args:
            map_fn: 映射函数
            reduce_fn: 归约函数
            data: 输入数据列表
            
        Returns:
            归约结果
        """
        if self.pool is None:
            self.start()
        
        # Map 阶段
        mapped_results = self.pool.map(map_fn, data)
        
        # Reduce 阶段 (在主进程执行)
        result = reduce_fn(mapped_results)
        
        return result
    
    def sync_parameters(
        self, 
        local_models: List[Dict[str, np.ndarray]], 
        global_model: Optional[Dict[str, np.ndarray]] = None
    ) -> Dict[str, np.ndarray]:
        """
        同步参数 - 参数平均
        
        Args:
            local_models: 各工作进程的本地模型参数
            global_model: 可选的全局模型 (用于动量更新)
            
        Returns:
            更新后的全局模型参数
        """
        if not local_models:
            return global_model or {}
        
        # 参数平均
        synced_params = {}
        param_keys = local_models[0].keys()
        
        for key in param_keys:
            # 收集所有模型的该参数
            params = [model[key] for model in local_models if key in model]
            
            if params:
                # 计算平均
                synced_params[key] = np.mean(params, axis=0)
        
        # 如果提供了全局模型，使用动量更新
        if global_model is not None:
            momentum = 0.9
            for key in synced_params:
                if key in global_model:
                    synced_params[key] = (
                        momentum * global_model[key] + 
                        (1 - momentum) * synced_params[key]
                    )
        
        self.global_model = synced_params
        return synced_params
    
    def async_update(
        self,
        local_model: Dict[str, np.ndarray],
        global_model: Dict[str, np.ndarray],
        alpha: float = 0.1
    ) -> Dict[str, np.ndarray]:
        """
        异步参数更新
        
        Args:
            local_model: 本地模型参数
            global_model: 全局模型参数
            alpha: 更新系数
            
        Returns:
            更新后的全局模型参数
        """
        updated_model = {}
        
        for key in global_model:
            if key in local_model:
                # 异步更新: global = global + alpha * (local - global)
                updated_model[key] = (
                    global_model[key] + 
                    alpha * (local_model[key] - global_model[key])
                )
            else:
                updated_model[key] = global_model[key]
        
        self.global_model = updated_model
        return updated_model
    
    def save_results(self, output_path: str):
        """保存训练结果"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        results_data = {
            'results': [r.to_dict() for r in self.results],
            'stats': self.stats,
            'n_workers': self.n_workers,
        }
        
        with open(output_path, 'wb') as f:
            pickle.dump(results_data, f)
        
        print(f"Results saved to {output_path}")
    
    def load_results(self, input_path: str) -> List[TrainingResult]:
        """加载训练结果"""
        with open(input_path, 'rb') as f:
            data = pickle.load(f)
        
        # 重建结果对象
        self.results = []
        for r_data in data['results']:
            config = TrainingConfig(**r_data['config'])
            result = TrainingResult(
                config=config,
                worker_id=r_data['worker_id'],
                total_reward=r_data['total_reward'],
                success_count=r_data['success_count'],
                episode_rewards=r_data['episode_rewards'],
                training_time=r_data['training_time'],
                timestamp=r