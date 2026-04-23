"""
Meta Controller V2 - 停滞触发机制

关键改进：
- 由"好"触发 → 由"停滞"触发
- 监测变化率而非绝对值
- 预期：每200~500 steps触发一次
"""

import numpy as np
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass


@dataclass
class MetaDrive:
    """元驱动"""
    name: str
    description: str
    evaluate_fn: Callable[['MetaControllerV2', np.ndarray], float]
    apply_fn: Callable[['MetaControllerV2', np.ndarray], None]
    weight: float = 0.5
    activation_history: List[float] = None
    
    def __post_init__(self):
        if self.activation_history is None:
            self.activation_history = []
    
    def evaluate(self, controller: 'MetaControllerV2', state: np.ndarray) -> float:
        score = self.evaluate_fn(controller, state)
        self.activation_history.append(score)
        if len(self.activation_history) > 100:
            self.activation_history = self.activation_history[-100:]
        return score
    
    def apply(self, controller: 'MetaControllerV2', state: np.ndarray):
        self.apply_fn(controller, state)


class MetaControllerV2:
    """
    元控制器 V2 - 停滞触发机制
    
    核心思想：
    > Meta-drive 不应该由"好"触发，而应该由"停滞"触发
    
    当系统：
    - 行为收敛
    - 多样性下降
    - 性能停滞
    
    时自动触发元驱动。
    """
    
    def __init__(self, self_model=None, drive_manager=None):
        self.self_model = self_model
        self.drive_manager = drive_manager
        
        # 历史记录
        self.metric_history: List[float] = []
        self.diversity_history: List[float] = []
        self.window = 50
        
        # 元驱动
        self.meta_drives: List[MetaDrive] = []
        self._register_default_meta_drives()
        
        # 修改历史
        self.modification_history: List[Dict] = []
        self.trigger_count = 0
    
    def _register_default_meta_drives(self):
        """注册默认元驱动"""
        
        # 元驱动1: 探索新驱动空间
        explore_drive = MetaDrive(
            name="exploration_over_drives",
            description="Explore new drive space when stagnated",
            evaluate_fn=self._eval_stagnation,
            apply_fn=self._apply_exploration
        )
        self.meta_drives.append(explore_drive)
        
        # 元驱动2: 增加选择压力
        selection_pressure = MetaDrive(
            name="increase_selection_pressure",
            description="Increase pressure when diversity drops",
            evaluate_fn=self._eval_diversity_drop,
            apply_fn=self._apply_selection_pressure
        )
        self.meta_drives.append(selection_pressure)
    
    def update(self, metric: float) -> bool:
        """
        更新并检查是否触发元驱动
        
        Args:
            metric: 性能指标（如多样性、成功率等）
            
        Returns:
            是否触发了元驱动
        """
        self.metric_history.append(metric)
        
        if len(self.metric_history) < self.window:
            return False
        
        # 计算变化率
        recent = self.metric_history[-self.window:]
        delta = np.mean(recent[-10:]) - np.mean(recent[:10])
        
        # 🔥 关键：如果几乎没变化 → 停滞
        is_stagnant = abs(delta) < 0.01
        
        if is_stagnant:
            self.trigger_count += 1
            return True
        
        return False
    
    def step(self, state: np.ndarray, metric: float):
        """
        元控制器主步骤
        
        Args:
            state: 当前状态
            metric: 性能指标（如行为多样性）
        """
        # 检查是否停滞
        should_trigger = self.update(metric)
        
        if should_trigger:
            # 触发元驱动
            for meta_drive in self.meta_drives:
                activation = meta_drive.evaluate(self, state)
                if activation > 0.5:
                    meta_drive.apply(self, state)
                    
                    self.modification_history.append({
                        'cycle': len(self.metric_history),
                        'type': meta_drive.name,
                        'metric': metric,
                        'description': f"Triggered by stagnation (delta={abs(self._get_delta()):.4f})"
                    })
    
    def _get_delta(self) -> float:
        """获取最近的变化率"""
        if len(self.metric_history) < self.window:
            return 0.0
        recent = self.metric_history[-self.window:]
        return np.mean(recent[-10:]) - np.mean(recent[:10])
    
    def _eval_stagnation(self, controller: 'MetaControllerV2', 
                         state: np.ndarray) -> float:
        """评估停滞程度"""
        if len(controller.metric_history) < controller.window:
            return 0.0
        
        delta = abs(controller._get_delta())
        # 变化越小，停滞程度越高
        stagnation = 1.0 - min(1.0, delta * 100)
        return stagnation
    
    def _eval_diversity_drop(self, controller: 'MetaControllerV2',
                             state: np.ndarray) -> float:
        """评估多样性下降"""
        if len(controller.metric_history) < 20:
            return 0.0
        
        early = np.mean(controller.metric_history[:10])
        late = np.mean(controller.metric_history[-10:])
        
        if late < early * 0.8:  # 多样性下降20%以上
            return 0.8
        return 0.0
    
    def _apply_exploration(self, controller: 'MetaControllerV2', 
                           state: np.ndarray):
        """应用驱动空间探索"""
        if not controller.drive_manager:
            return
        
        # 降低现有驱动权重，给新驱动空间
        for drive in controller.drive_manager.drives.values():
            if hasattr(drive, 'weight'):
                drive.weight *= 0.9
        
        print(f"[Meta-Drive] Exploration triggered at cycle {len(controller.metric_history)}")
    
    def _apply_selection_pressure(self, controller: 'MetaControllerV2', 
                                  state: np.ndarray):
        """应用选择压力"""
        if not controller.drive_manager:
            return
        
        # 淘汰低权重驱动
        drives = list(controller.drive_manager.drives.items())
        if len(drives) > 2:
            drives.sort(key=lambda x: getattr(x[1], 'weight', 0))
            weakest_name = drives[0][0]
            if getattr(drives[0][1], 'weight', 1) < 0.1:
                del controller.drive_manager.drives[weakest_name]
                print(f"[Meta-Drive] Pruned weak drive: {weakest_name}")
    
    def get_stats(self) -> dict:
        """获取统计"""
        return {
            'trigger_count': self.trigger_count,
            'modification_count': len(self.modification_history),
            'metric_history_length': len(self.metric_history),
            'recent_modifications': self.modification_history[-3:] if self.modification_history else [],
            'is_stagnant_now': abs(self._get_delta()) < 0.01 if len(self.metric_history) >= self.window else False
        }
