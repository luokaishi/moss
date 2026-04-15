"""
Meta Controller - 元控制器

元驱动 = 作用在"驱动生成与进化过程本身"的驱动力

三类元驱动：
1. Exploration-over-Drives: 驱动空间探索
2. Selection Pressure Modulation: 选择压力调节
3. Self-Modification: 自修改
"""

import numpy as np
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from .self_model import SelfModel


@dataclass
class MetaDrive:
    """元驱动"""
    name: str
    description: str
    evaluate_fn: Callable[['MetaController', np.ndarray], float]
    apply_fn: Callable[['MetaController', np.ndarray], None]
    weight: float = 0.5
    activation_history: List[float] = None
    
    def __post_init__(self):
        if self.activation_history is None:
            self.activation_history = []
    
    def evaluate(self, controller: 'MetaController', state: np.ndarray) -> float:
        """评估元驱动在当前状态下的激活程度"""
        score = self.evaluate_fn(controller, state)
        self.activation_history.append(score)
        if len(self.activation_history) > 100:
            self.activation_history = self.activation_history[-100:]
        return score
    
    def apply(self, controller: 'MetaController', state: np.ndarray):
        """应用元驱动的效果"""
        self.apply_fn(controller, state)


class MetaController:
    """
    元控制器
    
    管理元驱动，实现对驱动系统的自我修改
    
    核心功能：
    1. 监控当前驱动系统的性能
    2. 评估元驱动的激活程度
    3. 根据元驱动修改驱动系统
    """
    
    def __init__(self, self_model: SelfModel, drive_manager=None):
        """
        Args:
            self_model: 自我模型
            drive_manager: 驱动管理器（用于修改驱动）
        """
        self.self_model = self_model
        self.drive_manager = drive_manager
        
        # 元驱动集合
        self.meta_drives: List[MetaDrive] = []
        self._register_default_meta_drives()
        
        # 性能监控
        self.performance_history: List[float] = []
        self.drive_diversity_history: List[float] = []
        
        # 修改历史（用于追踪自我修改）
        self.modification_history: List[Dict] = []
        
    def _register_default_meta_drives(self):
        """注册默认元驱动"""
        
        # 元驱动1: 驱动空间探索
        # 当驱动多样性低时，探索新的驱动
        explore_drive = MetaDrive(
            name="exploration_over_drives",
            description="Explore new drive space when diversity is low",
            evaluate_fn=self._eval_exploration_need,
            apply_fn=self._apply_exploration
        )
        self.meta_drives.append(explore_drive)
        
        # 元驱动2: 选择压力调节
        # 根据性能调整选择压力
        selection_pressure = MetaDrive(
            name="selection_pressure_modulation",
            description="Adjust selection pressure based on performance",
            evaluate_fn=self._eval_selection_pressure_need,
            apply_fn=self._apply_selection_pressure
        )
        self.meta_drives.append(selection_pressure)
        
        # 元驱动3: 自修改
        # 当自我模型准确率高时，进行更深度的自我修改
        self_modification = MetaDrive(
            name="self_modification",
            description="Modify own structure when self-awareness is high",
            evaluate_fn=self._eval_self_modification_need,
            apply_fn=self._apply_self_modification
        )
        self.meta_drives.append(self_modification)
    
    def step(self, state: np.ndarray, current_performance: float):
        """
        元控制器的主循环步骤
        
        Args:
            state: 当前状态
            current_performance: 当前性能指标
        """
        # 记录性能
        self.performance_history.append(current_performance)
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
        
        # 计算驱动多样性
        if self.drive_manager:
            diversity = self._compute_drive_diversity()
            self.drive_diversity_history.append(diversity)
            if len(self.drive_diversity_history) > 100:
                self.drive_diversity_history = self.drive_diversity_history[-100:]
        
        # 评估并应用元驱动
        for meta_drive in self.meta_drives:
            activation = meta_drive.evaluate(self, state)
            
            # 如果激活度高，应用该元驱动
            if activation > 0.6:
                meta_drive.apply(self, state)
    
    def _compute_drive_diversity(self) -> float:
        """计算驱动多样性"""
        if not self.drive_manager or not self.drive_manager.drives:
            return 0.0
        
        # 基于驱动权重的熵计算多样性
        weights = [d.weight for d in self.drive_manager.drives.values()]
        weights = np.array(weights)
        weights = weights / (np.sum(weights) + 1e-8)
        
        entropy = -np.sum(weights * np.log(weights + 1e-8))
        max_entropy = np.log(len(weights))
        
        return float(entropy / max_entropy) if max_entropy > 0 else 0.0
    
    # ========== 元驱动评估函数 ==========
    
    def _eval_exploration_need(self, controller: 'MetaController', 
                               state: np.ndarray) -> float:
        """评估是否需要探索新的驱动空间"""
        if len(controller.drive_diversity_history) < 10:
            return 0.3
        
        # 如果多样性持续低，需要探索
        recent_diversity = np.mean(controller.drive_diversity_history[-10:])
        
        # 多样性越低，探索需求越高
        exploration_need = 1.0 - recent_diversity
        
        # 如果性能也在下降，更需要探索
        if len(controller.performance_history) >= 20:
            early_perf = np.mean(controller.performance_history[-20:-10])
            late_perf = np.mean(controller.performance_history[-10:])
            if late_perf < early_perf:
                exploration_need += 0.2
        
        return float(np.clip(exploration_need, 0, 1))
    
    def _eval_selection_pressure_need(self, controller: 'MetaController',
                                      state: np.ndarray) -> float:
        """评估是否需要调节选择压力"""
        if len(controller.performance_history) < 20:
            return 0.5
        
        # 计算性能趋势
        recent_perf = np.mean(controller.performance_history[-10:])
        older_perf = np.mean(controller.performance_history[-20:-10])
        
        # 如果性能停滞，增加选择压力
        if abs(recent_perf - older_perf) < 0.05:
            return 0.8  # 高激活，需要改变
        
        # 如果性能下降，减少选择压力（给系统恢复时间）
        if recent_perf < older_perf - 0.1:
            return 0.3
        
        return 0.5
    
    def _eval_self_modification_need(self, controller: 'MetaController',
                                     state: np.ndarray) -> float:
        """评估是否需要进行自我修改"""
        # 基于自我模型的准确率
        awareness = controller.self_model.get_self_awareness_score()
        
        # 自我认知越高，越可以进行自我修改
        base_need = awareness
        
        # 如果性能良好，可以进行实验性修改
        if len(controller.performance_history) >= 10:
            recent_perf = np.mean(controller.performance_history[-10:])
            if recent_perf > 0.7:
                base_need += 0.1
        
        return float(np.clip(base_need, 0, 1))
    
    # ========== 元驱动应用函数 ==========
    
    def _apply_exploration(self, controller: 'MetaController', state: np.ndarray):
        """应用驱动空间探索"""
        if not controller.drive_manager:
            return
        
        # 降低现有驱动的权重，给新驱动空间
        for drive in controller.drive_manager.drives.values():
            drive.weight *= 0.95
        
        # 记录修改
        controller.modification_history.append({
            'type': 'exploration',
            'description': 'Reduced drive weights to explore new space',
            'timestamp': len(controller.performance_history)
        })
    
    def _apply_selection_pressure(self, controller: 'MetaController', state: np.ndarray):
        """应用选择压力调节"""
        if not controller.drive_manager:
            return
        
        # 根据性能调整选择压力
        if len(controller.performance_history) >= 10:
            recent_perf = np.mean(controller.performance_history[-10:])
            
            # 性能停滞：增加选择压力（淘汰低效驱动）
            if len(controller.performance_history) >= 20:
                older_perf = np.mean(controller.performance_history[-20:-10])
                if abs(recent_perf - older_perf) < 0.05:
                    # 淘汰权重最低的驱动
                    drives = list(controller.drive_manager.drives.items())
                    if len(drives) > 2:
                        drives.sort(key=lambda x: x[1].weight)
                        weakest_drive_name = drives[0][0]
                        if drives[0][1].weight < 0.1:
                            del controller.drive_manager.drives[weakest_drive_name]
                            
                            controller.modification_history.append({
                                'type': 'selection_pressure',
                                'description': f'Pruned weak drive: {weakest_drive_name}',
                                'timestamp': len(controller.performance_history)
                            })
    
    def _apply_self_modification(self, controller: 'MetaController', state: np.ndarray):
        """应用自我修改"""
        # 修改自我模型的学习率
        old_lr = controller.self_model.lr
        
        # 如果自我认知高，可以降低学习率（更稳定）
        if controller.self_model.get_self_awareness_score() > 0.8:
            controller.self_model.lr = max(0.001, old_lr * 0.95)
        else:
            # 否则增加学习率（更快适应）
            controller.self_model.lr = min(0.1, old_lr * 1.05)
        
        controller.modification_history.append({
            'type': 'self_modification',
            'description': f'Adjusted learning rate: {old_lr:.4f} -> {controller.self_model.lr:.4f}',
            'timestamp': len(controller.performance_history)
        })
    
    def get_meta_drive_influence(self) -> float:
        """获取元驱动的总影响"""
        if not self.meta_drives:
            return 0.0
        
        total_activation = sum(
            np.mean(md.activation_history[-10:]) if md.activation_history else 0
            for md in self.meta_drives
        )
        return total_activation / len(self.meta_drives)
    
    def get_stats(self) -> dict:
        """获取元控制器统计"""
        return {
            'num_meta_drives': len(self.meta_drives),
            'meta_drive_influence': self.get_meta_drive_influence(),
            'num_modifications': len(self.modification_history),
            'recent_modifications': self.modification_history[-5:] if self.modification_history else [],
            'drive_diversity': np.mean(self.drive_diversity_history[-10:]) if self.drive_diversity_history else 0.0,
            'meta_drives': [{
                'name': md.name,
                'weight': md.weight,
                'recent_activation': np.mean(md.activation_history[-10:]) if md.activation_history else 0
            } for md in self.meta_drives]
        }