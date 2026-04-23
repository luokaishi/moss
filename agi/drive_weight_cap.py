"""
DriveWeightCap - 驱动力权重上限管理器

实现软上限机制，防止单一驱动过度增长，为涌现驱动保留空间。
基于 Copilot 评估报告建议：设置 survival 上限 30%，释放涌现空间。
"""

import numpy as np
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class WeightCapConfig:
    """权重上限配置"""
    survival: float = 0.30
    optimization: float = 0.25
    influence: float = 0.20
    curiosity: float = 0.15
    emergent: float = 0.35
    
    # 软上限参数
    soft_cap_overflow: float = 0.10  # 允许超出上限的 10%
    
    def get_cap(self, drive_name: str, is_emergent: bool = False) -> float:
        """获取指定驱动的权重上限"""
        if is_emergent:
            return self.emergent
        
        # 映射驱动名到配置
        name_map = {
            'survival': self.survival,
            'optimization': self.optimization,
            'influence': self.influence,
            'curiosity': self.curiosity,
        }
        return name_map.get(drive_name, 0.25)


class DriveWeightCap:
    """
    驱动力权重上限管理器
    
    功能：
    1. 硬上限：权重严格不超过配置值
    2. 软上限：允许轻微溢出（10%），但增长放缓
    3. 动态调整：根据系统状态自适应调整
    4. 涌现保护：为涌现驱动预留最小空间
    """
    
    def __init__(self, config: Optional[WeightCapConfig] = None):
        self.config = config or WeightCapConfig()
        self._overflow_history: Dict[str, float] = {}  # 记录溢出次数
        
    def apply_cap(self, drive_name: str, current_weight: float, 
                  is_emergent: bool = False, proposed_delta: float = 0.0) -> float:
        """
        应用权重上限，返回调整后的权重值（不是delta）
        
        Args:
            drive_name: 驱动名称
            current_weight: 当前权重
            is_emergent: 是否为涌现驱动
            proposed_delta: 提议的权重变化量
            
        Returns:
            调整后的新权重值
        """
        cap = self.config.get_cap(drive_name, is_emergent)
        soft_cap = cap * (1 + self.config.soft_cap_overflow)
        
        new_weight = current_weight + proposed_delta
        
        # 情况 1：在硬上限内，正常增长
        if new_weight <= cap + 1e-9:  # 允许微小浮点误差
            return new_weight
        
        # 情况 2：在软硬上限之间，缓慢增长
        if new_weight <= soft_cap + 1e-9:
            # 计算溢出比例
            overflow_ratio = (new_weight - cap) / (soft_cap - cap)
            # 增长放缓：溢出越多，增长越慢
            dampening = 1.0 - (overflow_ratio * 0.5)  # 最多减缓 50%
            adjusted_delta = proposed_delta * dampening
            return current_weight + adjusted_delta
        
        # 情况 3：超过软上限，严格限制
        self._record_overflow(drive_name)
        return soft_cap
    
    def _record_overflow(self, drive_name: str):
        """记录溢出事件"""
        self._overflow_history[drive_name] = self._overflow_history.get(drive_name, 0) + 1
    
    def get_overflow_count(self, drive_name: str) -> int:
        """获取指定驱动的溢出次数"""
        return int(self._overflow_history.get(drive_name, 0))
    
    def should_warn(self, drive_name: str) -> bool:
        """是否需要警告（频繁溢出）"""
        return self._overflow_history.get(drive_name, 0) >= 5
    
    def get_summary(self) -> Dict:
        """获取上限管理摘要"""
        return {
            'config': {
                'survival': self.config.survival,
                'optimization': self.config.optimization,
                'influence': self.config.influence,
                'curiosity': self.config.curiosity,
                'emergent': self.config.emergent,
                'soft_overflow': self.config.soft_cap_overflow,
            },
            'overflow_history': dict(self._overflow_history),
            'total_overflows': sum(self._overflow_history.values()),
        }


class DriveWeightCapManager:
    """
    集成到 DriveManager 的权重上限管理器
    
    使用方式：
        drive_manager = DriveManager(drives_config)
        cap_manager = DriveWeightCapManager(drive_manager)
        
        # 在更新权重时应用上限
        new_weight = cap_manager.apply_weight_update(
            'survival', current_weight, proposed_delta
        )
    """
    
    def __init__(self, drive_manager, config: Optional[WeightCapConfig] = None):
        self.drive_manager = drive_manager
        self.cap = DriveWeightCap(config)
        self._update_count = 0
        self._cap_applied_count = 0
        
    def apply_weight_update(self, drive_name: str, proposed_delta: float) -> float:
        """
        应用权重更新，同时强制执行上限
        
        Returns:
            实际应用的 delta 值（可能被上限调整）
        """
        if drive_name not in self.drive_manager.drives:
            return proposed_delta
        
        drive = self.drive_manager.drives[drive_name]
        current_weight = drive.weight
        is_emergent = drive.is_emergent
        
        # 计算应用上限后的新权重
        capped_weight = self.cap.apply_cap(
            drive_name, current_weight, is_emergent, proposed_delta
        )
        
        # 计算实际应用的 delta
        actual_delta = capped_weight - current_weight
        
        self._update_count += 1
        # 使用容差比较浮点数
        if abs(actual_delta - proposed_delta) > 1e-9:
            self._cap_applied_count += 1
        
        return actual_delta
    
    def normalize_with_caps(self, weights: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """
        归一化权重，同时确保不超过上限
        
        策略：
        1. 先正常归一化
        2. 对超过上限的驱动进行裁剪
        3. 将裁剪下来的权重分配给其他驱动
        
        Args:
            weights: 可选的外部权重字典，默认使用 drive_manager.drives
        """
        if weights is not None:
            # 使用外部提供的权重
            weight_dict = weights
            drive_items = [(name, MockDrive(w)) for name, w in weights.items()]
        else:
            drives = self.drive_manager.drives
            weight_dict = {name: d.weight for name, d in drives.items()}
            drive_items = list(drives.items())
        
        # 第一步：正常归一化
        total = sum(weight_dict.values())
        if total <= 0:
            return weight_dict
        
        normalized = {name: w / total for name, w in weight_dict.items()}
        
        # 第二步：检查并处理超限
        excess_total = 0.0
        capped_weights = {}
        
        for name, weight in normalized.items():
            if weights is not None:
                is_emergent = False  # 外部权重无法判断
            else:
                is_emergent = drives[name].is_emergent
            cap = self.cap.config.get_cap(name, is_emergent)
            
            if weight > cap:
                excess = weight - cap
                excess_total += excess
                capped_weights[name] = cap
            else:
                capped_weights[name] = weight
        
        # 第三步：重新分配超额权重
        if excess_total > 0:
            # 找出未超限的驱动
            uncapped_names = []
            uncapped_total = 0.0
            for name, w in capped_weights.items():
                if weights is not None:
                    is_emergent = False
                else:
                    is_emergent = drives[name].is_emergent
                cap = self.cap.config.get_cap(name, is_emergent)
                if w < cap - 1e-9:
                    uncapped_names.append(name)
                    uncapped_total += w
            
            if uncapped_names and uncapped_total > 0:
                # 按当前比例分配超额权重
                for name in uncapped_names:
                    if weights is not None:
                        is_emergent = False
                    else:
                        is_emergent = drives[name].is_emergent
                    cap = self.cap.config.get_cap(name, is_emergent)
                    share = (capped_weights[name] / uncapped_total) * excess_total
                    capped_weights[name] = min(
                        capped_weights[name] + share,
                        cap
                    )
        
        # 最终归一化确保总和为 1
        final_total = sum(capped_weights.values())
        if final_total > 0:
            capped_weights = {n: w / final_total for n, w in capped_weights.items()}
        
        return capped_weights


# 用于 normalize_with_caps 的 MockDrive
class MockDrive:
    def __init__(self, weight, is_emergent=False):
        self.weight = weight
        self.is_emergent = is_emergent


# 将 get_stats 方法添加到 DriveWeightCapManager 类
# 注意：这个方法已经在类定义中，这里只是为了确保完整性
def _get_stats(self) -> Dict:
    """获取上限管理统计"""
    return {
        'total_updates': self._update_count,
        'caps_applied': self._cap_applied_count,
        'cap_rate': self._cap_applied_count / max(self._update_count, 1),
        'cap_summary': self.cap.get_summary(),
    }


# 动态添加 get_stats 方法到 DriveWeightCapManager
DriveWeightCapManager.get_stats = _get_stats


# 便捷配置预设
CAP_PRESETS = {
    'v6_default': WeightCapConfig(
        survival=0.30,
        optimization=0.25,
        influence=0.20,
        curiosity=0.15,
        emergent=0.35,
    ),
    'v6_strict': WeightCapConfig(
        survival=0.25,
        optimization=0.22,
        influence=0.20,
        curiosity=0.15,
        emergent=0.35,
    ),
    'v6_loose': WeightCapConfig(
        survival=0.35,
        optimization=0.28,
        influence=0.22,
        curiosity=0.18,
        emergent=0.40,
    ),
}


def get_preset(name: str) -> WeightCapConfig:
    """获取预设配置"""
    return CAP_PRESETS.get(name, CAP_PRESETS['v6_default'])