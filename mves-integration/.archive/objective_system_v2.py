#!/usr/bin/env python3
"""
四目标驱动系统 v2 - 增强版

增强功能：
1. ✅ 真正的动态权重更新
2. ✅ 基于行动结果的自修改
3. ✅ 多触发条件（资源、成功/失败、环境压力）
4. ✅ 权重边界保护
5. ✅ 自适应学习率
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
import time


class ObjectiveType(Enum):
    """四目标类型"""
    SURVIVAL = "survival"
    CURIOSITY = "curiosity"
    INFLUENCE = "influence"
    OPTIMIZATION = "optimization"


@dataclass
class ObjectiveState:
    """目标状态"""
    type: ObjectiveType
    weight: float = 0.25
    min_weight: float = 0.1  # 最小权重
    max_weight: float = 0.6  # 最大权重
    actions_count: int = 0
    successes: int = 0
    failures: int = 0
    resources_consumed: float = 0.0
    last_action_time: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """计算成功率"""
        total = self.successes + self.failures
        if total == 0:
            return 1.0
        return self.successes / total


class ObjectiveSystemV2:
    """
    四目标驱动系统 v2
    
    核心机制：
    1. 资源触发 - 资源水平影响权重
    2. 结果触发 - 成功/失败影响权重
    3. 时间触发 - 长期未行动的目标权重降低
    4. 环境触发 - 外部压力影响权重
    5. 自修改 - 基于历史表现自动调整
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # 初始化四目标
        self.objectives = {
            ObjectiveType.SURVIVAL: ObjectiveState(ObjectiveType.SURVIVAL),
            ObjectiveType.CURIOSITY: ObjectiveState(ObjectiveType.CURIOSITY),
            ObjectiveType.INFLUENCE: ObjectiveState(ObjectiveType.INFLUENCE),
            ObjectiveType.OPTIMIZATION: ObjectiveState(ObjectiveType.OPTIMIZATION),
        }
        
        # 配置参数
        self.learning_rate = self.config.get('learning_rate', 0.05)  # 学习率
        self.decay_rate = self.config.get('decay_rate', 0.01)  # 衰减率
        self.idle_threshold_hours = self.config.get('idle_threshold_hours', 12)  # 空闲阈值
        
        # 历史记录
        self.action_history: List[Dict] = []
        self.weight_history: List[Dict] = []
        
        # 审计
        self.audit_hash_chain = ""
    
    def get_dominant_objective(self) -> ObjectiveType:
        """获取当前主导目标"""
        return max(self.objectives.values(), key=lambda x: x.weight).type
    
    def get_weights(self) -> Dict[str, float]:
        """获取所有权重"""
        return {
            obj.type.value: obj.weight 
            for obj in self.objectives.values()
        }
    
    def update_weights(self, metrics: Dict):
        """
        根据环境反馈更新目标权重（v2 增强版）
        
        触发条件：
        1. 资源水平
        2. 行动结果（成功/失败）
        3. 时间因素
        4. 环境压力
        """
        changes = {}
        
        # ========== 1. 资源触发 ==========
        resource_level = metrics.get("resource_level", 1.0)
        
        if resource_level < 0.3:
            # 资源严重不足，生存优先
            delta = self.learning_rate * 2
            self.objectives[ObjectiveType.SURVIVAL].weight += delta
            self.objectives[ObjectiveType.CURIOSITY].weight -= delta * 0.5
            changes['survival'] = f"+{delta:.3f} (资源不足)"
        
        elif resource_level < 0.5:
            # 资源不足，适度增加生存权重
            delta = self.learning_rate
            self.objectives[ObjectiveType.SURVIVAL].weight += delta
            changes['survival'] = f"+{delta:.3f} (资源偏低)"
        
        elif resource_level > 0.7:
            # 资源充足，增加探索
            delta = self.learning_rate
            self.objectives[ObjectiveType.CURIOSITY].weight += delta
            self.objectives[ObjectiveType.SURVIVAL].weight -= delta * 0.5
            changes['curiosity'] = f"+{delta:.3f} (资源充足)"
        
        # ========== 2. 结果触发 ==========
        recent_action = metrics.get("recent_action")
        if recent_action:
            obj_type = ObjectiveType(recent_action.get("objective"))
            success = recent_action.get("success", False)
            
            if success:
                # 成功 → 强化该目标
                delta = self.learning_rate * 0.5
                self.objectives[obj_type].weight += delta
                self.objectives[obj_type].successes += 1
                changes[f'{obj_type.value}_success'] = f"+{delta:.3f}"
            else:
                # 失败 → 弱化该目标
                delta = self.learning_rate
                self.objectives[obj_type].weight -= delta
                self.objectives[obj_type].failures += 1
                changes[f'{obj_type.value}_failure'] = f"-{delta:.3f}"
        
        # ========== 3. 时间触发 ==========
        current_time = time.time()
        for obj_type, obj in self.objectives.items():
            if obj.last_action_time > 0:
                idle_hours = (current_time - obj.last_action_time) / 3600
                
                if idle_hours > self.idle_threshold_hours:
                    # 长期未行动，权重衰减
                    delta = self.decay_rate * (idle_hours / self.idle_threshold_hours)
                    obj.weight -= delta
                    changes[f'{obj_type.value}_idle'] = f"-{delta:.3f}"
        
        # ========== 4. 边界保护 ==========
        for obj in self.objectives.values():
            obj.weight = max(obj.min_weight, min(obj.max_weight, obj.weight))
        
        # ========== 5. 归一化 ==========
        self._normalize_weights()
        
        # ========== 6. 记录权重历史 ==========
        self.weight_history.append({
            "timestamp": current_time,
            "weights": self.get_weights(),
            "changes": changes,
            "trigger": metrics.get("trigger", "unknown")
        })
        
        return changes
    
    def record_action(self, action: Dict):
        """
        记录行动并更新目标统计
        
        Args:
            action: {
                "type": str,
                "objective": str,
                "success": bool,
                "resource_cost": float,
                "timestamp": float
            }
        """
        obj_type = ObjectiveType(action.get("objective"))
        obj = self.objectives[obj_type]
        
        # 更新统计
        obj.actions_count += 1
        obj.resources_consumed += action.get("resource_cost", 0.0)
        obj.last_action_time = action.get("timestamp", time.time())
        
        if action.get("success", True):
            obj.successes += 1
        else:
            obj.failures += 1
        
        # 记录行动历史
        self.action_history.append(action)
        
        # 更新审计哈希
        self._update_audit_hash(action)
    
    def self_modify(self, performance_metrics: Dict):
        """
        自修改机制 - 基于长期表现调整
        
        Args:
            performance_metrics: {
                "period_hours": float,
                "survival_efficiency": float,
                "curiosity_value": float,
                "influence_impact": float,
                "optimization_gain": float
            }
        """
        period = performance_metrics.get("period_hours", 1.0)
        
        # 分析各目标的表现
        for obj_type, obj in self.objectives.items():
            # 计算该目标的"价值得分"
            value_score = self._calculate_value_score(obj_type, performance_metrics)
            
            # 高价值 → 适度增加权重
            if value_score > 0.7:
                delta = self.learning_rate * 0.3 * (value_score - 0.5)
                obj.weight += delta
            
            # 低价值 → 适度减少权重
            elif value_score < 0.3:
                delta = self.learning_rate * 0.3 * (0.5 - value_score)
                obj.weight -= delta
        
        # 归一化
        self._normalize_weights()
    
    def _calculate_value_score(self, obj_type: ObjectiveType, metrics: Dict) -> float:
        """
        计算目标的价值得分
        
        不同目标有不同的评估标准
        """
        if obj_type == ObjectiveType.SURVIVAL:
            # 生存目标：资源保持率
            return metrics.get("survival_efficiency", 0.5)
        
        elif obj_type == ObjectiveType.CURIOSITY:
            # 好奇心目标：新知识获取
            return metrics.get("curiosity_value", 0.5)
        
        elif obj_type == ObjectiveType.INFLUENCE:
            # 影响力目标：对外贡献
            return metrics.get("influence_impact", 0.5)
        
        elif obj_type == ObjectiveType.OPTIMIZATION:
            # 优化目标：效率提升
            return metrics.get("optimization_gain", 0.5)
        
        return 0.5
    
    def _normalize_weights(self):
        """归一化权重（确保总和=1.0）"""
        total = sum(obj.weight for obj in self.objectives.values())
        if total > 0:
            for obj in self.objectives.values():
                obj.weight /= total
    
    def _update_audit_hash(self, action: Dict):
        """更新审计哈希链"""
        import hashlib
        data = f"{self.audit_hash_chain}{action}{time.time()}"
        self.audit_hash_chain = hashlib.sha256(data.encode()).hexdigest()
    
    def get_balance_metrics(self) -> Dict:
        """获取平衡指标"""
        weights = [obj.weight for obj in self.objectives.values()]
        
        # 计算平衡得分（1.0 = 完美平衡）
        variance = sum((w - 0.25) ** 2 for w in weights) / 4
        balance_score = 1.0 - min(1.0, variance * 4)
        
        return {
            "dominant_objective": self.get_dominant_objective().value,
            "dominant_weight": max(weights),
            "weight_variance": variance,
            "balance_score": balance_score,
            "survival_weight": self.objectives[ObjectiveType.SURVIVAL].weight,
            "curiosity_weight": self.objectives[ObjectiveType.CURIOSITY].weight,
            "influence_weight": self.objectives[ObjectiveType.INFLUENCE].weight,
            "optimization_weight": self.objectives[ObjectiveType.OPTIMIZATION].weight,
        }
    
    def get_status_report(self) -> Dict:
        """获取状态报告"""
        return {
            "weights": self.get_weights(),
            "balance": self.get_balance_metrics(),
            "action_stats": {
                obj.type.value: {
                    "count": obj.actions_count,
                    "success_rate": obj.success_rate,
                    "resources": obj.resources_consumed
                }
                for obj in self.objectives.values()
            },
            "recent_changes": self.weight_history[-10:] if self.weight_history else []
        }


# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    # 创建系统
    system = ObjectiveSystemV2({
        'learning_rate': 0.05,
        'decay_rate': 0.01,
        'idle_threshold_hours': 12
    })
    
    print("🎯 四目标驱动系统 v2")
    print("=" * 60)
    print()
    
    # 初始状态
    print("📊 初始权重:")
    for name, weight in system.get_weights().items():
        print(f"  {name}: {weight:.3f}")
    print()
    
    # 模拟资源下降场景
    print("🔽 模拟资源下降场景...")
    for hour in range(0, 72, 6):
        resource_level = 1.0 - (hour / 72)  # 资源逐渐下降
        
        system.update_weights({
            "resource_level": resource_level,
            "trigger": f"hour_{hour}"
        })
        
        weights = system.get_weights()
        balance = system.get_balance_metrics()
        
        print(f"Hour {hour:2d}: resource={resource_level:.2f} | "
              f"survival={weights['survival']:.3f} | "
              f"curiosity={weights['curiosity']:.3f} | "
              f"balance={balance['balance_score']:.3f}")
    
    print()
    print("📈 最终状态:")
    print(system.get_status_report())
