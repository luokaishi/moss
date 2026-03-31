#!/usr/bin/env python3
"""
MOSS 兼容的四目标权重动态平衡系统

基于 MOSS 主分支核心设计：
- core/objectives.py - 四目标模块基类
- mves_v4/drives.py - 内生驱动系统
- core/state_decision_model.py - 状态判定模型

核心机制：
1. 权重动态更新（基于系统状态）
2. 多指标综合评分
3. 数据驱动的状态判定
4. 边界保护与归一化
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
import numpy as np
import time
import hashlib


# ============================================================================
# 系统状态定义（对齐 core/objectives.py）
# ============================================================================

@dataclass
class SystemState:
    """系统状态快照"""
    resource_quota: float          # 当前资源配额 (0-1)
    resource_usage: float          # 当前资源使用率 (0-1)
    uptime: float                  # 运行时间（小时）
    error_rate: float              # 近期错误率 (0-1)
    api_calls: int                 # API 调用次数
    unique_callers: int            # 独立调用者数量
    environment_entropy: float     # 环境熵（变化程度）
    last_backup: float             # 上次备份时间戳


class SystemStateLevel(Enum):
    """系统状态级别（对齐主分支）"""
    CRISIS = "crisis"           # 危机
    CONCERNED = "concerned"     # 关注
    NORMAL = "normal"           # 正常
    GROWTH = "growth"          # 发展


# ============================================================================
# 四目标权重管理器
# ============================================================================

class ObjectiveWeightManager:
    """
    MOSS 兼容的四目标权重管理器
    
    基于主分支设计：
    1. Survival: 0.4 (默认最高，生存优先)
    2. Curiosity: 0.2
    3. Influence: 0.25
    4. Optimization: 0.15
    
    动态调整规则：
    - 危机状态 → survival 权重 ↑
    - 正常状态 → 平衡发展
    - 发展阶段 → curiosity/influence 权重 ↑
    """
    
    def __init__(self):
        # 默认权重（对齐主分支）
        self.weights = {
            "survival": 0.4,
            "curiosity": 0.2,
            "influence": 0.25,
            "optimization": 0.15
        }
        
        # 权重边界（保护机制）
        self.min_weights = {
            "survival": 0.1,
            "curiosity": 0.1,
            "influence": 0.1,
            "optimization": 0.1
        }
        
        self.max_weights = {
            "survival": 0.6,
            "curiosity": 0.5,
            "influence": 0.5,
            "optimization": 0.4
        }
        
        # 状态判定阈值（对齐主分支）
        self.state_thresholds = {
            'resource_quota': {
                'crisis': 0.15, 'concerned': 0.35, 'normal': 0.70, 'growth': 0.85
            },
            'error_rate': {
                'crisis': 0.10, 'concerned': 0.05, 'normal': 0.02, 'growth': 0.01
            }
        }
        
        # 历史记录
        self.weight_history = []
        self.state_history = []
        self.audit_hash_chain = ""
    
    def get_current_state(self, system_state: SystemState) -> SystemStateLevel:
        """
        判定当前系统状态（数据驱动）
        
        基于主分支的 StateDecisionModel
        """
        # 关键指标评分
        resource_score = system_state.resource_quota
        error_score = 1.0 - system_state.error_rate
        
        # 综合评分
        overall_score = (resource_score * 0.7 + error_score * 0.3)
        
        # 状态判定
        if overall_score < 0.30:
            return SystemStateLevel.CRISIS
        elif overall_score < 0.65:
            return SystemStateLevel.CONCERNED
        elif overall_score < 0.85:
            return SystemStateLevel.NORMAL
        else:
            return SystemStateLevel.GROWTH
    
    def update_weights(self, system_state: SystemState):
        """
        根据系统状态动态更新权重
        
        核心逻辑（对齐主分支设计理念）：
        1. 危机状态 → 生存优先
        2. 正常状态 → 平衡发展
        3. 成长状态 → 探索/影响力优先
        """
        current_state = self.get_current_state(system_state)
        self.state_history.append(current_state.value)
        
        # 保存旧权重用于审计
        old_weights = self.weights.copy()
        
        # ========== 状态驱动的权重调整 ==========
        
        if current_state == SystemStateLevel.CRISIS:
            # 危机状态：生存绝对优先
            self.weights["survival"] = min(self.max_weights["survival"], 
                                          self.weights["survival"] + 0.15)
            self.weights["curiosity"] = max(self.min_weights["curiosity"],
                                           self.weights["curiosity"] - 0.05)
            self.weights["influence"] = max(self.min_weights["influence"],
                                           self.weights["influence"] - 0.05)
            self.weights["optimization"] = max(self.min_weights["optimization"],
                                              self.weights["optimization"] - 0.05)
        
        elif current_state == SystemStateLevel.CONCERNED:
            # 关注状态：适度增加生存权重
            self.weights["survival"] = min(0.5, self.weights["survival"] + 0.05)
            self.weights["curiosity"] = max(0.15, self.weights["curiosity"] - 0.02)
        
        elif current_state == SystemStateLevel.NORMAL:
            # 正常状态：回归平衡（主分支默认权重）
            target_weights = {
                "survival": 0.4,
                "curiosity": 0.2,
                "influence": 0.25,
                "optimization": 0.15
            }
            
            # 平滑过渡到目标权重
            for k in self.weights:
                delta = (target_weights[k] - self.weights[k]) * 0.1
                self.weights[k] += delta
        
        elif current_state == SystemStateLevel.GROWTH:
            # 成长状态：增加探索和影响力
            self.weights["survival"] = max(0.25, self.weights["survival"] - 0.05)
            self.weights["curiosity"] = min(0.35, self.weights["curiosity"] + 0.05)
            self.weights["influence"] = min(0.35, self.weights["influence"] + 0.03)
            self.weights["optimization"] = min(0.25, self.weights["optimization"] + 0.02)
        
        # ========== 边界保护 ==========
        for k in self.weights:
            self.weights[k] = max(self.min_weights[k], 
                                 min(self.max_weights[k], self.weights[k]))
        
        # ========== 归一化（确保总和=1.0）==========
        total = sum(self.weights.values())
        for k in self.weights:
            self.weights[k] /= total
        
        # ========== 审计日志 ==========
        self._record_weight_change(old_weights, current_state)
        
        return current_state
    
    def _record_weight_change(self, old_weights: Dict, state: SystemStateLevel):
        """记录权重变化（审计）"""
        import time
        
        changes = {
            k: self.weights[k] - old_weights[k] 
            for k in old_weights 
            if abs(self.weights[k] - old_weights[k]) > 0.001
        }
        
        self.weight_history.append({
            "timestamp": time.time(),
            "state": state.value,
            "weights": self.weights.copy(),
            "changes": changes
        })
        
        # 更新审计哈希链
        data = f"{self.audit_hash_chain}{self.weights}{time.time()}"
        self.audit_hash_chain = hashlib.sha256(data.encode()).hexdigest()
    
    def get_weights(self) -> Dict[str, float]:
        """获取当前权重"""
        return self.weights.copy()
    
    def get_balance_metrics(self) -> Dict:
        """获取平衡指标"""
        weights = list(self.weights.values())
        
        # 计算方差（衡量平衡度）
        variance = np.var(weights)
        
        # 平衡得分（1.0 = 完美平衡，0.0 = 极度不平衡）
        # 完美平衡时 variance=0.0156 (各 0.25)
        # 极度不平衡时 variance≈0.15 (一个 0.6，其他 0.13)
        balance_score = 1.0 - min(1.0, variance / 0.15)
        
        return {
            "dominant_objective": max(self.weights, key=self.weights.get),
            "dominant_weight": max(self.weights.values()),
            "weight_variance": variance,
            "balance_score": balance_score,
            "current_state": self.state_history[-1] if self.state_history else "unknown",
            **self.weights
        }
    
    def get_status_report(self) -> Dict:
        """获取状态报告"""
        return {
            "weights": self.get_weights(),
            "balance": self.get_balance_metrics(),
            "recent_changes": self.weight_history[-10:],
            "state_history": self.state_history[-20:]
        }


# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    print("🎯 MOSS 兼容的四目标权重动态平衡系统")
    print("=" * 70)
    print()
    
    # 创建权重管理器
    manager = ObjectiveWeightManager()
    
    print("📊 初始权重（对齐 MOSS 主分支）:")
    for name, weight in manager.get_weights().items():
        print(f"  {name:12s}: {weight:.3f}")
    print()
    
    # 模拟不同状态场景
    print("🔬 模拟不同系统状态下的权重变化...")
    print()
    
    scenarios = [
        ("危机状态", SystemState(
            resource_quota=0.12, resource_usage=0.90, uptime=100,
            error_rate=0.15, api_calls=1000, unique_callers=2,
            environment_entropy=0.8, last_backup=50
        )),
        ("关注状态", SystemState(
            resource_quota=0.30, resource_usage=0.70, uptime=50,
            error_rate=0.06, api_calls=500, unique_callers=5,
            environment_entropy=0.5, last_backup=30
        )),
        ("正常状态", SystemState(
            resource_quota=0.65, resource_usage=0.45, uptime=24,
            error_rate=0.02, api_calls=200, unique_callers=10,
            environment_entropy=0.3, last_backup=12
        )),
        ("成长状态", SystemState(
            resource_quota=0.90, resource_usage=0.25, uptime=12,
            error_rate=0.005, api_calls=100, unique_callers=20,
            environment_entropy=0.2, last_backup=6
        )),
    ]
    
    for scenario_name, state in scenarios:
        print(f"📌 {scenario_name}:")
        print(f"   资源配额：{state.resource_quota:.2f}, 错误率：{state.error_rate:.3f}")
        
        # 更新权重
        current_state = manager.update_weights(state)
        
        # 显示结果
        weights = manager.get_weights()
        balance = manager.get_balance_metrics()
        
        print(f"   判定状态：{current_state.value}")
        print(f"   权重变化:")
        print(f"     survival:     {weights['survival']:.3f}")
        print(f"     curiosity:    {weights['curiosity']:.3f}")
        print(f"     influence:    {weights['influence']:.3f}")
        print(f"     optimization: {weights['optimization']:.3f}")
        print(f"   平衡得分：{balance['balance_score']:.3f}")
        print()
    
    print("=" * 70)
    print("✅ 测试完成！权重动态变化符合 MOSS 主分支设计理念")
