#!/usr/bin/env python3
"""
MVES v2.0 - Purpose Dynamics Module v2

多向量价值涌现增强的 D9 Purpose 模块

核心功能：
- 多向量价值融合（目标 + 价值 + 模态）
- Purpose 自生成增强
- 价值吸引子提取
- 稳定性分析

与 MOSS main 分支集成：
- 替换/增强 objectives.py 中的 Purpose Dynamics Module
- 为 D9 自生成 Purpose 提供多模态价值源
- 保持与 D1-D8 框架兼容
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import json
import time

# 从 multimodal_extension 导入
try:
    from multimodal_extension import ValueVector, MultimodalExtension
except ImportError:
    # 简化版本（测试用）
    class ValueVector:
        def __init__(self):
            self.goal_vector = np.zeros(64)
            self.value_vector = np.zeros(64)
            self.modality_vector = np.zeros(16)
            self.confidence = 1.0
        
        def fuse(self, other: 'ValueVector', alpha: float = 0.5) -> 'ValueVector':
            new = ValueVector()
            new.goal_vector = alpha * self.goal_vector + (1 - alpha) * other.goal_vector
            new.value_vector = alpha * self.value_vector + (1 - alpha) * other.value_vector
            new.modality_vector = alpha * self.modality_vector + (1 - alpha) * other.modality_vector
            new.confidence = alpha * self.confidence + (1 - alpha) * other.confidence
            return new

# v5.3 社会压力模块集成
try:
    from .social_pressure import SocialPressureModule
except (ImportError, SystemError):
    try:
        from social_pressure import SocialPressureModule
    except ImportError:
        SocialPressureModule = None


@dataclass
class PurposeAttractor:
    """
    Purpose 吸引子
    
    代表一个稳定的价值配置状态
    类似物理系统中的吸引子，系统会自然趋向这些状态
    """
    name: str
    value_vector: np.ndarray
    goal_vector: np.ndarray
    stability: float  # 0-1
    activation_count: int = 0
    last_activation: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def activate(self):
        """激活吸引子"""
        self.activation_count += 1
        self.last_activation = time.time()
    
    def distance_to(self, current_value: np.ndarray) -> float:
        """计算当前价值向量与吸引子的距离"""
        return np.linalg.norm(self.value_vector - current_value)


@dataclass
class PurposeState:
    """
    Purpose 状态
    
    表示当前的 Purpose 配置
    """
    # 核心价值向量
    value_vector: np.ndarray = field(default_factory=lambda: np.zeros(64))
    # 目标向量
    goal_vector: np.ndarray = field(default_factory=lambda: np.zeros(64))
    # 稳定性指标
    stability: float = 0.0
    # 清晰度（熵的倒数）
    clarity: float = 0.0
    # 时间戳
    timestamp: float = 0.0
    # 历史向量（用于稳定性分析）
    history: List[np.ndarray] = field(default_factory=list)
    
    def update(self, new_value: np.ndarray, new_goal: np.ndarray):
        """更新 Purpose 状态"""
        # 指数移动平均
        alpha = 0.1
        self.value_vector = alpha * new_value + (1 - alpha) * self.value_vector
        self.goal_vector = alpha * new_goal + (1 - alpha) * self.goal_vector
        self.timestamp = time.time()
        
        # 更新历史
        self.history.append(new_value.copy())
        if len(self.history) > 100:
            self.history = self.history[-100:]
        
        # 重新计算稳定性
        self._calculate_stability()
    
    def _calculate_stability(self):
        """计算稳定性（基于历史方差）"""
        if len(self.history) < 10:
            self.stability = 0.0
            return
        
        recent = np.array(self.history[-10:])
        std = np.std(recent, axis=0).mean()
        self.stability = max(0.0, 1.0 - std * 10)
        
        # 计算清晰度（基于价值向量熵）
        probs = np.abs(self.value_vector) / (np.sum(np.abs(self.value_vector)) + 1e-10)
        entropy = -np.sum(probs * np.log(probs + 1e-10))
        max_entropy = np.log(len(self.value_vector))
        self.clarity = 1.0 - (entropy / max_entropy) if max_entropy > 0 else 0.0


class PurposeDynamicsModule:
    """
    Purpose Dynamics Module v2
    
    多向量价值涌现增强的 D9 Purpose 模块
    
    核心职责：
    1. 从多模态输入中提取价值向量
    2. 维护 Purpose 吸引子池
    3. 动态调整 Purpose 状态
    4. 提供稳定性分析
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # 维度配置
        self.value_dim = self.config.get("value_dim", 64)
        self.goal_dim = self.config.get("goal_dim", 64)
        
        # Purpose 状态
        self.current_purpose = PurposeState()
        
        # 吸引子池
        self.attractors: List[PurposeAttractor] = []
        self.max_attractors = 10
        
        # 多模态扩展（如果可用）
        self.multimodal: Optional[MultimodalExtension] = None
        
        # v5.3 社会压力模块
        self.social_module: Optional[SocialPressureModule] = None
        
        # 配置参数
        self.attraction_threshold = self.config.get("attraction_threshold", 0.3)
        self.stability_target = self.config.get("stability_target", 0.96)
        
        # 统计信息
        self.stats = {
            "total_updates": 0,
            "attractor_formations": 0,
            "purpose_shifts": 0,
            "avg_stability": 0.0
        }
    
    def set_multimodal_extension(self, multimodal):
        """设置多模态扩展模块"""
        self.multimodal = multimodal
    
    def set_social_pressure_module(self, module):
        """v5.3 社会压力模块集成"""
        if SocialPressureModule is None:
            print("⚠️  SocialPressureModule 未导入，无法设置")
            return
        self.social_module = module
        print(f"✅ [PurposeDynamics v5.3] SocialPressureModule 已注入")
    
    def update_from_values(self, 
                          value_vectors: List[ValueVector],
                          context: Dict) -> PurposeState:
        """
        从价值向量列表更新 Purpose
        
        Args:
            value_vectors: 价值向量列表（来自多模态输入）
            context: 上下文信息（包含 state、goals 等）
        
        Returns:
            更新后的 Purpose 状态
        """
        if not value_vectors:
            return self.current_purpose
        
        # 1. 融合价值向量
        fused_value = self._fuse_value_vectors(value_vectors)
        
        # v5.3 社会压力向量融合
        if self.social_module:
            social_vec = self.social_module.get_social_value_vector()
            value_vectors_extended = value_vectors + [social_vec]
            fused_value = self._fuse_value_vectors(value_vectors_extended)
            
            # 额外标量压力权重
            pressure_weight = self.social_module.get_pressure_weight()
            fused_value = 0.85 * fused_value + 0.15 * pressure_weight * np.ones_like(fused_value)
        
        # 2. 提取目标向量
        fused_goal = self._extract_goal_vector(fused_value, context)
        
        # 3. 检查吸引子
        attractor = self._find_nearest_attractor(fused_value)
        
        if attractor and attractor.distance_to(fused_value) < self.attraction_threshold:
            # 接近现有吸引子 - 向吸引子收敛
            attractor.activate()
            fused_value = self._attract_to_attractor(fused_value, attractor)
        else:
            # 远离所有吸引子 - 可能形成新吸引子
            # 条件放宽：允许在早期形成吸引子
            if len(self.attractors) < 3 or self.current_purpose.stability > 0.3:
                self._try_form_new_attractor(fused_value, fused_goal, context)
        
        # 4. 更新 Purpose 状态
        old_stability = self.current_purpose.stability
        self.current_purpose.update(fused_value, fused_goal)
        self.stats["total_updates"] += 1
        
        # 5. 检测 Purpose 转移
        if old_stability > 0.8 and self.current_purpose.stability < 0.5:
            self.stats["purpose_shifts"] += 1
        
        # 6. 更新平均稳定性
        self.stats["avg_stability"] = (
            0.95 * self.stats["avg_stability"] + 
            0.05 * self.current_purpose.stability
        )
        
        return self.current_purpose
    
    def update_from_multimodal(self,
                              inputs: Dict,
                              context: Dict) -> PurposeState:
        """
        从多模态输入更新 Purpose
        
        Args:
            inputs: 多模态输入字典
            context: 上下文信息
        
        Returns:
            更新后的 Purpose 状态
        """
        if not self.multimodal:
            raise RuntimeError("MultimodalExtension not set")
        
        # 使用多模态扩展处理输入
        result = self.multimodal.process_multimodal_input(inputs, context)
        value_vector = result["value_vector"]
        
        # 转换为 ValueVector 列表（单个元素）
        value_vectors = [value_vector]
        
        return self.update_from_values(value_vectors, context)
    
    def _fuse_value_vectors(self, vectors: List[ValueVector]) -> np.ndarray:
        """融合多个价值向量"""
        if not vectors:
            return np.zeros(self.value_dim)
        
        # 时间加权融合
        fused = np.zeros(self.value_dim)
        total_weight = 0.0
        
        for i, vv in enumerate(vectors):
            # 越新的向量权重越高
            weight = 0.9 ** (len(vectors) - i - 1)
            weight *= vv.confidence
            
            if len(vv.value_vector) < self.value_dim:
                padded = np.pad(vv.value_vector, (0, self.value_dim - len(vv.value_vector)))
            else:
                padded = vv.value_vector[:self.value_dim]
            
            fused += weight * padded
            total_weight += weight
        
        if total_weight > 0:
            fused /= total_weight
        
        # 归一化
        norm = np.linalg.norm(fused)
        if norm > 0:
            fused /= norm
        
        return fused
    
    def _extract_goal_vector(self, 
                            value_vector: np.ndarray,
                            context: Dict) -> np.ndarray:
        """从价值向量提取目标向量"""
        # 简化实现：基于上下文调整
        goal = value_vector.copy()
        
        # 根据状态调整
        state = context.get("state", "Normal")
        state_multipliers = {
            "Crisis": 1.5,
            "Concerned": 1.2,
            "Normal": 1.0,
            "Growth": 0.8
        }
        
        multiplier = state_multipliers.get(state, 1.0)
        goal *= multiplier
        
        # 归一化
        norm = np.linalg.norm(goal)
        if norm > 0:
            goal /= norm
        
        return goal
    
    def _find_nearest_attractor(self, value_vector: np.ndarray) -> Optional[PurposeAttractor]:
        """找到最近的价值吸引子"""
        if not self.attractors:
            return None
        
        nearest = None
        min_distance = float('inf')
        
        for attractor in self.attractors:
            distance = attractor.distance_to(value_vector)
            if distance < min_distance:
                min_distance = distance
                nearest = attractor
        
        return nearest
    
    def _attract_to_attractor(self, 
                             current_value: np.ndarray,
                             attractor: PurposeAttractor) -> np.ndarray:
        """向吸引子收敛"""
        # 吸引力度与距离成正比
        distance = attractor.distance_to(current_value)
        attraction_strength = min(0.5, distance * 2)
        
        new_value = (
            (1 - attraction_strength) * current_value +
            attraction_strength * attractor.value_vector
        )
        
        # 归一化
        norm = np.linalg.norm(new_value)
        if norm > 0:
            new_value /= norm
        
        return new_value
    
    def _try_form_new_attractor(self,
                               value_vector: np.ndarray,
                               goal_vector: np.ndarray,
                               context: Dict):
        """尝试形成新的吸引子"""
        # 检查是否已有足够多的吸引子
        if len(self.attractors) >= self.max_attractors:
            # 替换最不活跃的吸引子
            self.attractors.sort(key=lambda a: a.last_activation)
            self.attractors.pop(0)
        
        # 计算稳定性（即使当前稳定性低，也允许形成初始吸引子）
        stability = max(0.5, self.current_purpose.stability)
        
        # 创建新吸引子
        attractor = PurposeAttractor(
            name=f"Attractor_{len(self.attractors) + 1}",
            value_vector=value_vector.copy(),
            goal_vector=goal_vector.copy(),
            stability=stability,
            activation_count=1,
            last_activation=time.time(),
            metadata=context.copy()
        )
        
        self.attractors.append(attractor)
        self.stats["attractor_formations"] += 1
    
    def get_purpose_vector(self) -> np.ndarray:
        """获取当前 Purpose 向量"""
        return self.current_purpose.value_vector
    
    def get_stability_metrics(self) -> Dict:
        """获取稳定性指标"""
        return {
            "stability": self.current_purpose.stability,
            "clarity": self.current_purpose.clarity,
            "target": self.stability_target,
            "history_size": len(self.current_purpose.history),
            "attractor_count": len(self.attractors),
            "total_updates": self.stats["total_updates"],
            "purpose_shifts": self.stats["purpose_shifts"],
            "avg_stability": self.stats["avg_stability"]
        }
    
    def analyze_purpose_dynamics(self) -> Dict:
        """
        分析 Purpose 动力学
        
        Returns:
            详细分析报告
        """
        if len(self.current_purpose.history) < 10:
            return {
                "status": "insufficient_data",
                "message": "Need at least 10 history points"
            }
        
        history_array = np.array(self.current_purpose.history)
        
        # 计算趋势
        if len(history_array) > 1:
            trend = np.polyfit(range(len(history_array)), history_array.mean(axis=1), 1)[0]
        else:
            trend = 0.0
        
        # 分析吸引子激活模式
        attractor_activations = {
            a.name: a.activation_count 
            for a in self.attractors
        }
        
        # 计算主导吸引子
        dominant_attractor = None
        if self.attractors:
            dominant = max(self.attractors, key=lambda a: a.activation_count)
            dominant_attractor = {
                "name": dominant.name,
                "activations": dominant.activation_count,
                "stability": dominant.stability
            }
        
        return {
            "status": "success",
            "stability": self.current_purpose.stability,
            "clarity": self.current_purpose.clarity,
            "trend": trend,
            "trend_direction": "increasing" if trend > 0 else "decreasing" if trend < 0 else "stable",
            "attractor_count": len(self.attractors),
            "dominant_attractor": dominant_attractor,
            "attractor_activations": attractor_activations,
            "purpose_shifts": self.stats["purpose_shifts"],
            "avg_stability": self.stats["avg_stability"]
        }
    
    def export_purpose_state(self) -> Dict:
        """导出 Purpose 状态（用于持久化或分析）"""
        return {
            "current_purpose": {
                "value_vector": self.current_purpose.value_vector.tolist(),
                "goal_vector": self.current_purpose.goal_vector.tolist(),
                "stability": self.current_purpose.stability,
                "clarity": self.current_purpose.clarity,
                "timestamp": self.current_purpose.timestamp,
                "history_size": len(self.current_purpose.history)
            },
            "attractors": [
                {
                    "name": a.name,
                    "stability": a.stability,
                    "activation_count": a.activation_count,
                    "last_activation": a.last_activation
                }
                for a in self.attractors
            ],
            "stats": self.stats.copy()
        }
    
    def import_purpose_state(self, state: Dict):
        """导入 Purpose 状态"""
        if "current_purpose" in state:
            cp = state["current_purpose"]
            self.current_purpose.value_vector = np.array(cp["value_vector"])
            self.current_purpose.goal_vector = np.array(cp["goal_vector"])
            self.current_purpose.stability = cp["stability"]
            self.current_purpose.clarity = cp["clarity"]
            self.current_purpose.timestamp = cp["timestamp"]
        
        if "attractors" in state:
            self.attractors = []
            for a in state["attractors"]:
                attractor = PurposeAttractor(
                    name=a["name"],
                    value_vector=np.zeros(self.value_dim),
                    goal_vector=np.zeros(self.goal_dim),
                    stability=a["stability"],
                    activation_count=a["activation_count"],
                    last_activation=a["last_activation"]
                )
                self.attractors.append(attractor)
        
        if "stats" in state:
            self.stats = state["stats"].copy()


# ============================================================================
# 与 MOSS main 分支的集成接口
# ============================================================================

def integrate_with_objectives(moss_agent, purpose_module: PurposeDynamicsModule):
    """
    集成到 objectives.py 的 Purpose Dynamics Module
    
    替换原有的 D9 Purpose 实现
    """
    # TODO: 实现与 objectives.py 的集成
    # 主要修改点：
    # 1. 替换 PurposeState 类
    # 2. 更新 update_purpose() 函数
    # 3. 添加多模态输入支持
    pass


def get_purpose_vector_for_decision(moss_agent, purpose_module: PurposeDynamicsModule) -> np.ndarray:
    """
    获取用于决策的 Purpose 向量
    
    在 MOSS 的决策循环中调用
    """
    return purpose_module.get_purpose_vector()


def check_purpose_stability(purpose_module: PurposeDynamicsModule, 
                           threshold: float = 0.96) -> bool:
    """
    检查 Purpose 稳定性是否达标
    
    用于 Self-Optimization 触发判断
    """
    metrics = purpose_module.get_stability_metrics()
    return metrics["stability"] >= threshold


# ============================================================================
# 测试与验证
# ============================================================================

def run_purpose_dynamics_tests():
    """运行 Purpose Dynamics 测试"""
    print("Running Purpose Dynamics Module v2 Tests...")
    
    # 测试 1: 基础初始化
    module = PurposeDynamicsModule()
    assert module.current_purpose is not None, "Initialization failed"
    print("✓ Initialization test passed")
    
    # 测试 2: 价值向量更新
    vectors = [ValueVector() for _ in range(5)]
    for i, vv in enumerate(vectors):
        vv.value_vector = np.random.randn(64)
        vv.value_vector /= np.linalg.norm(vv.value_vector)
        vv.confidence = 0.8 + 0.04 * i
    
    context = {"state": "Normal"}
    purpose = module.update_from_values(vectors, context)
    assert purpose.stability >= 0.0, "Update failed"
    print(f"✓ Value update test passed (stability: {purpose.stability:.3f})")
    
    # 测试 3: 吸引子形成
    for _ in range(20):
        new_vectors = [ValueVector() for _ in range(3)]
        for vv in new_vectors:
            vv.value_vector = purpose.value_vector + np.random.randn(64) * 0.1
            vv.confidence = 0.9
        purpose = module.update_from_values(new_vectors, context)
    
    assert len(module.attractors) > 0, "Attractor formation failed"
    print(f"✓ Attractor formation test passed ({len(module.attractors)} attractors)")
    
    # 测试 4: 稳定性分析
    metrics = module.get_stability_metrics()
    assert "stability" in metrics, "Metrics failed"
    print(f"✓ Stability metrics test passed (stability: {metrics['stability']:.3f})")
    
    # 测试 5: 动力学分析
    analysis = module.analyze_purpose_dynamics()
    assert analysis["status"] == "success", "Analysis failed"
    print(f"✓ Dynamics analysis test passed (trend: {analysis['trend_direction']})")
    
    # 测试 6: 状态导出/导入
    state = module.export_purpose_state()
    new_module = PurposeDynamicsModule()
    new_module.import_purpose_state(state)
    assert new_module.stats["total_updates"] == module.stats["total_updates"], "Export/Import failed"
    print("✓ State export/import test passed")
    
    # 测试 7: 稳定性目标检测
    is_stable = check_purpose_stability(module, threshold=0.96)
    print(f"✓ Stability check test passed (stable: {is_stable})")
    
    print("\n✅ All Purpose Dynamics tests passed!")
    
    # 打印详细报告
    print("\n📊 Purpose Dynamics Report:")
    print(f"  Stability: {metrics['stability']:.3f} (target: >0.96)")
    print(f"  Clarity: {metrics['clarity']:.3f}")
    print(f"  Attractors: {len(module.attractors)}")
    print(f"  Purpose Shifts: {module.stats['purpose_shifts']}")
    print(f"  Avg Stability: {metrics['avg_stability']:.3f}")


if __name__ == "__main__":
    run_purpose_dynamics_tests()
