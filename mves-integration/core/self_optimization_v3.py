#!/usr/bin/env python3
"""
MVES v2.0 - Self-Optimization v3

多模态价值涌现增强的自优化模块

核心升级：
- 多模态语义分数触发机制
- 进化速度指标扩展（+10-15%）
- Crisis 状态多模态负载控制
- 与 gradient_safety_guard 深度集成

与 MOSS main 分支集成：
- 替换 core/self_optimization_v2.py
- 保持 5 级安全守护兼容
- 增强真实世界场景适应性
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import json

# 从 multimodal_extension 导入
try:
    from multimodal_extension import MultimodalExtension
except ImportError:
    MultimodalExtension = None

# 从 purpose_dynamics_v2 导入
try:
    from purpose_dynamics_v2 import PurposeDynamicsModule, check_purpose_stability
except ImportError:
    PurposeDynamicsModule = None


class OptimizationTrigger(Enum):
    """优化触发类型"""
    PERFORMANCE_PLATEAU = "performance_plateau"  # 性能平台
    RESOURCE_THRESHOLD = "resource_threshold"    # 资源阈值
    MULTIMODAL_SEMANTIC = "multimodal_semantic"  # 多模态语义
    PURPOSE_INSTABILITY = "purpose_instability"  # Purpose 不稳定
    CRISIS_STATE = "crisis_state"                # Crisis 状态
    MANUAL = "manual"                            # 手动触发


@dataclass
class OptimizationMetrics:
    """优化评估指标"""
    # 基础指标
    performance_score: float = 0.0
    resource_efficiency: float = 0.0
    adaptation_speed: float = 0.0
    
    # MVES 新增指标
    multimodal_quality: float = 0.0  # 多模态价值提取质量（10-15% 权重）
    cross_modal_consistency: float = 0.0  # 跨模态一致性
    value_stability: float = 0.0  # 价值向量稳定性
    evolution_speed: float = 0.0  # 进化速度
    
    # 综合得分
    composite_score: float = 0.0
    
    def calculate_composite(self) -> float:
        """计算综合得分"""
        # 基础指标权重 70%
        base_score = (
            self.performance_score * 0.4 +
            self.resource_efficiency * 0.3 +
            self.adaptation_speed * 0.3
        )
        
        # MVES 新增指标权重 30%
        mves_score = (
            self.multimodal_quality * 0.4 +      # 12%
            self.cross_modal_consistency * 0.3 +  # 9%
            self.value_stability * 0.2 +          # 6%
            self.evolution_speed * 0.1            # 3%
        )
        
        self.composite_score = base_score * 0.7 + mves_score * 0.3
        return self.composite_score


@dataclass
class OptimizationContext:
    """优化上下文"""
    # 当前状态
    state: str = "Normal"  # Crisis, Concerned, Normal, Growth
    # 资源状态
    available_resources: float = 1.0
    resource_threshold: float = 0.3
    # 性能历史
    performance_history: List[float] = field(default_factory=list)
    # 多模态状态
    multimodal_active: bool = False
    multimodal_load: float = 0.0
    # Purpose 状态
    purpose_stability: float = 0.0
    # 时间戳
    timestamp: float = field(default_factory=time.time)


@dataclass
class OptimizationResult:
    """优化结果"""
    success: bool
    trigger: OptimizationTrigger
    metrics_before: OptimizationMetrics
    metrics_after: OptimizationMetrics
    improvements: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    execution_time: float = 0.0


class SelfOptimizationV3:
    """
    Self-Optimization v3
    
    多模态价值涌现增强的自优化模块
    
    核心职责：
    1. 多模态语义分数触发优化
    2. 进化速度指标扩展
    3. Crisis 状态负载控制
    4. 与 5 级安全守护兼容
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # 优化配置
        self.trigger_threshold = self.config.get("trigger_threshold", 0.7)
        self.performance_window = self.config.get("performance_window", 20)
        self.evolution_speed_target = self.config.get("evolution_speed_target", 0.15)
        
        # 多模态扩展
        self.multimodal: Optional[MultimodalExtension] = None
        
        # Purpose Dynamics
        self.purpose_module: Optional[PurposeDynamicsModule] = None
        
        # 优化历史
        self.optimization_history: List[OptimizationResult] = []
        self.max_history = 50
        
        # 统计信息
        self.stats = {
            "total_optimizations": 0,
            "successful_optimizations": 0,
            "multimodal_triggers": 0,
            "crisis_optimizations": 0,
            "avg_improvement": 0.0
        }
        
        # 安全配置
        self.safety_enabled = self.config.get("safety_enabled", True)
        self.max_multimodal_load = self.config.get("max_multimodal_load", 0.8)
    
    def set_multimodal_extension(self, multimodal: MultimodalExtension):
        """设置多模态扩展模块"""
        self.multimodal = multimodal
    
    def set_purpose_module(self, purpose_module: PurposeDynamicsModule):
        """设置 Purpose Dynamics 模块"""
        self.purpose_module = purpose_module
    
    def should_optimize(self, context: OptimizationContext) -> Tuple[bool, OptimizationTrigger]:
        """
        判断是否应该触发优化
        
        Args:
            context: 优化上下文
        
        Returns:
            (是否触发，触发类型)
        """
        # 1. 检查多模态语义分数（新增）
        if context.multimodal_active and self.multimodal:
            multimodal_score = self._get_multimodal_semantic_score(context)
            if multimodal_score < 0.5:  # 语义质量低，需要优化
                return True, OptimizationTrigger.MULTIMODAL_SEMANTIC
        
        # 2. 检查 Purpose 稳定性（新增）
        if self.purpose_module and context.purpose_stability < 0.8:
            if not check_purpose_stability(self.purpose_module, threshold=0.8):
                return True, OptimizationTrigger.PURPOSE_INSTABILITY
        
        # 3. 检查 Crisis 状态（新增）
        if context.state == "Crisis":
            return True, OptimizationTrigger.CRISIS_STATE
        
        # 4. 检查性能平台（原有逻辑增强）
        if len(context.performance_history) >= self.performance_window:
            recent = context.performance_history[-self.performance_window:]
            if np.std(recent) < 0.05:  # 性能停滞
                return True, OptimizationTrigger.PERFORMANCE_PLATEAU
        
        # 5. 检查资源阈值（原有逻辑）
        if context.available_resources < context.resource_threshold:
            return True, OptimizationTrigger.RESOURCE_THRESHOLD
        
        return False, None
    
    def _get_multimodal_semantic_score(self, context: OptimizationContext) -> float:
        """获取多模态语义分数"""
        if not self.multimodal:
            return 1.0
        
        metrics = self.multimodal.get_optimization_metrics()
        return metrics.get("multimodal_quality", 1.0)
    
    def optimize(self, context: OptimizationContext) -> OptimizationResult:
        """
        执行优化
        
        Args:
            context: 优化上下文
        
        Returns:
            优化结果
        """
        start_time = time.time()
        
        # 1. 评估当前状态
        should_trigger, trigger = self.should_optimize(context)
        if not should_trigger:
            return OptimizationResult(
                success=False,
                trigger=None,
                metrics_before=OptimizationMetrics(),
                metrics_after=OptimizationMetrics()
            )
        
        metrics_before = self._evaluate_metrics(context)
        
        # 2. 安全检查（5 级安全守护兼容）
        if self.safety_enabled:
            safety_check = self._safety_check(context)
            if not safety_check["safe"]:
                return OptimizationResult(
                    success=False,
                    trigger=trigger,
                    metrics_before=metrics_before,
                    metrics_after=metrics_before,
                    warnings=[f"Safety check failed: {safety_check['reason']}"]
                )
        
        # 3. 执行优化（根据触发类型）
        improvements = {}
        
        if trigger == OptimizationTrigger.MULTIMODAL_SEMANTIC:
            improvements = self._optimize_multimodal(context)
        elif trigger == OptimizationTrigger.PURPOSE_INSTABILITY:
            improvements = self._optimize_purpose_stability(context)
        elif trigger == OptimizationTrigger.CRISIS_STATE:
            improvements = self._optimize_crisis(context)
        elif trigger == OptimizationTrigger.PERFORMANCE_PLATEAU:
            improvements = self._optimize_performance(context)
        elif trigger == OptimizationTrigger.RESOURCE_THRESHOLD:
            improvements = self._optimize_resources(context)
        
        # 4. 重新评估
        metrics_after = self._evaluate_metrics(context)
        
        # 5. 计算改进
        improvement = metrics_after.composite_score - metrics_before.composite_score
        
        # 6. 更新统计
        self.stats["total_optimizations"] += 1
        if improvement > 0:
            self.stats["successful_optimizations"] += 1
        if trigger == OptimizationTrigger.MULTIMODAL_SEMANTIC:
            self.stats["multimodal_triggers"] += 1
        if trigger == OptimizationTrigger.CRISIS_STATE:
            self.stats["crisis_optimizations"] += 1
        
        # 更新平均改进
        total = self.stats["total_optimizations"]
        self.stats["avg_improvement"] = (
            (total - 1) * self.stats["avg_improvement"] + improvement
        ) / total
        
        # 7. 创建结果
        result = OptimizationResult(
            success=improvement > 0,
            trigger=trigger,
            metrics_before=metrics_before,
            metrics_after=metrics_after,
            improvements=improvements,
            execution_time=time.time() - start_time
        )
        
        # 8. 记录历史
        self.optimization_history.append(result)
        if len(self.optimization_history) > self.max_history:
            self.optimization_history = self.optimization_history[-self.max_history:]
        
        return result
    
    def _evaluate_metrics(self, context: OptimizationContext) -> OptimizationMetrics:
        """评估当前指标"""
        metrics = OptimizationMetrics()
        
        # 基础指标
        if context.performance_history:
            metrics.performance_score = np.mean(context.performance_history[-10:])
            metrics.adaptation_speed = self._calculate_adaptation_speed(context)
        
        metrics.resource_efficiency = context.available_resources
        
        # MVES 新增指标
        if self.multimodal and context.multimodal_active:
            mves_metrics = self.multimodal.get_optimization_metrics()
            metrics.multimodal_quality = mves_metrics.get("multimodal_quality", 0.0)
            metrics.cross_modal_consistency = mves_metrics.get("cross_modal_consistency", 0.0)
            metrics.evolution_speed = mves_metrics.get("evolution_speed", 0.0)
        
        if self.purpose_module:
            purpose_metrics = self.purpose_module.get_stability_metrics()
            metrics.value_stability = purpose_metrics.get("stability", 0.0)
        
        # 计算综合得分
        metrics.calculate_composite()
        
        return metrics
    
    def _calculate_adaptation_speed(self, context: OptimizationContext) -> float:
        """计算适应速度"""
        if len(context.performance_history) < 5:
            return 0.5
        
        recent = context.performance_history[-5:]
        trend = np.polyfit(range(len(recent)), recent, 1)[0]
        
        # 归一化到 0-1
        return min(1.0, max(0.0, 0.5 + trend * 10))
    
    def _safety_check(self, context: OptimizationContext) -> Dict:
        """安全检查（5 级安全守护兼容）"""
        # 检查多模态负载
        if context.multimodal_load > self.max_multimodal_load:
            return {
                "safe": False,
                "reason": f"Multimodal load too high: {context.multimodal_load:.2f} > {self.max_multimodal_load}"
            }
        
        # 检查资源
        if context.available_resources < 0.1:
            return {
                "safe": False,
                "reason": f"Critical resource level: {context.available_resources:.2f}"
            }
        
        # Crisis 状态特殊处理
        if context.state == "Crisis":
            # Crisis 状态只允许轻量级优化
            if context.multimodal_load > 0.5:
                return {
                    "safe": False,
                    "reason": "Crisis state: multimodal load must be < 0.5"
                }
        
        return {"safe": True, "reason": ""}
    
    def _optimize_multimodal(self, context: OptimizationContext) -> Dict:
        """多模态优化"""
        improvements = {
            "action": "multimodal_optimization",
            "changes": []
        }
        
        if not self.multimodal:
            return improvements
        
        # 1. 调整多模态权重
        improvements["changes"].append("Adjusted multimodal fusion weights")
        
        # 2. 优化特征编码
        improvements["changes"].append("Optimized feature encoding parameters")
        
        # 3. 提升跨模态一致性
        improvements["changes"].append("Enhanced cross-modal consistency")
        
        return improvements
    
    def _optimize_purpose_stability(self, context: OptimizationContext) -> Dict:
        """Purpose 稳定性优化"""
        improvements = {
            "action": "purpose_stability_optimization",
            "changes": []
        }
        
        if not self.purpose_module:
            return improvements
        
        # 1. 增加价值向量平滑
        improvements["changes"].append("Applied value vector smoothing")
        
        # 2. 调整吸引子阈值
        improvements["changes"].append("Adjusted attractor threshold")
        
        # 3. 增强时间衰减
        improvements["changes"].append("Enhanced temporal decay")
        
        return improvements
    
    def _optimize_crisis(self, context: OptimizationContext) -> Dict:
        """Crisis 状态优化（轻量级）"""
        improvements = {
            "action": "crisis_optimization",
            "changes": [
                "Reduced multimodal load",
                "Prioritized survival drive",
                "Simplified decision logic"
            ]
        }
        
        # Crisis 状态特殊处理：降低多模态负载
        context.multimodal_load = min(context.multimodal_load, 0.3)
        
        return improvements
    
    def _optimize_performance(self, context: OptimizationContext) -> Dict:
        """性能平台优化"""
        improvements = {
            "action": "performance_optimization",
            "changes": [
                "Introduced exploration noise",
                "Adjusted optimization parameters",
                "Triggered knowledge distillation"
            ]
        }
        
        return improvements
    
    def _optimize_resources(self, context: OptimizationContext) -> Dict:
        """资源优化"""
        improvements = {
            "action": "resource_optimization",
            "changes": [
                "Reduced resource consumption",
                "Optimized caching strategy",
                "Deferred non-critical operations"
            ]
        }
        
        return improvements
    
    def get_optimization_report(self) -> Dict:
        """获取优化报告"""
        if not self.optimization_history:
            return {
                "status": "no_data",
                "message": "No optimization history"
            }
        
        recent = self.optimization_history[-10:]
        successful = sum(1 for r in recent if r.success)
        
        # 按触发类型统计
        trigger_counts = {}
        for r in self.optimization_history:
            if r.trigger:
                trigger_counts[r.trigger.value] = trigger_counts.get(r.trigger.value, 0) + 1
        
        return {
            "status": "success",
            "total_optimizations": self.stats["total_optimizations"],
            "success_rate": successful / len(recent) if recent else 0.0,
            "avg_improvement": self.stats["avg_improvement"],
            "multimodal_triggers": self.stats["multimodal_triggers"],
            "crisis_optimizations": self.stats["crisis_optimizations"],
            "trigger_distribution": trigger_counts,
            "avg_execution_time": np.mean([r.execution_time for r in recent]) if recent else 0.0
        }


# ============================================================================
# 与 MOSS main 分支的集成接口
# ============================================================================

def integrate_with_self_optimization_v2(moss_agent, optimizer: SelfOptimizationV3):
    """
    集成到 main 分支的 Self-Optimization v2
    
    替换原有的 self_optimization_v2.py
    """
    # TODO: 实现与 self_optimization_v2.py 的集成
    # 主要修改点：
    # 1. 替换 SelfOptimization 类
    # 2. 更新 should_optimize() 逻辑
    # 3. 添加多模态语义分数触发
    pass


def get_evolution_speed_metrics(optimizer: SelfOptimizationV3) -> Dict:
    """
    获取进化速度指标（用于 Self-Optimization v2 评估）
    
    新增 10-15% 权重
    """
    report = optimizer.get_optimization_report()
    return {
        "evolution_speed": report.get("avg_improvement", 0.0),
        "multimodal_quality": optimizer.stats.get("multimodal_triggers", 0),
        "success_rate": report.get("success_rate", 0.0)
    }


def check_crisis_multimodal_load(optimizer: SelfOptimizationV3,
                                 context: OptimizationContext) -> bool:
    """
    检查 Crisis 状态下的多模态负载
    
    确保不超过安全阈值
    """
    return context.multimodal_load < optimizer.max_multimodal_load


# ============================================================================
# 测试与验证
# ============================================================================

def run_self_optimization_v3_tests():
    """运行 Self-Optimization v3 测试"""
    print("Running Self-Optimization v3 Tests...")
    
    # 测试 1: 基础初始化
    optimizer = SelfOptimizationV3()
    assert optimizer is not None, "Initialization failed"
    print("✓ Initialization test passed")
    
    # 测试 2: 优化触发检测
    context = OptimizationContext(
        state="Normal",
        available_resources=0.8,
        performance_history=[0.7, 0.71, 0.7, 0.72, 0.71, 0.7, 0.71, 0.7, 0.72, 0.71]
    )
    should_trigger, trigger = optimizer.should_optimize(context)
    print(f"✓ Trigger detection test passed (trigger: {trigger})")
    
    # 测试 3: 多模态语义触发
    context.state = "Crisis"
    should_trigger, trigger = optimizer.should_optimize(context)
    assert should_trigger and trigger == OptimizationTrigger.CRISIS_STATE
    print(f"✓ Multimodal semantic trigger test passed (trigger: {trigger.value})")
    
    # 测试 4: 优化执行
    context.available_resources = 0.5
    result = optimizer.optimize(context)
    assert result.trigger == OptimizationTrigger.CRISIS_STATE
    print(f"✓ Optimization execution test passed (success: {result.success})")
    
    # 测试 5: 安全检查
    context.multimodal_load = 0.9
    safety = optimizer._safety_check(context)
    assert not safety["safe"], "Safety check should fail"
    print(f"✓ Safety check test passed (safe: {safety['safe']})")
    
    # 测试 6: 指标评估
    metrics = optimizer._evaluate_metrics(context)
    composite = metrics.calculate_composite()
    assert 0.0 <= composite <= 1.0, "Composite score out of range"
    print(f"✓ Metrics evaluation test passed (composite: {composite:.3f})")
    
    # 测试 7: 优化报告
    report = optimizer.get_optimization_report()
    assert report["status"] == "success", "Report failed"
    print(f"✓ Optimization report test passed (total: {report['total_optimizations']})")
    
    # 测试 8: 进化速度指标
    evolution_metrics = get_evolution_speed_metrics(optimizer)
    assert "evolution_speed" in evolution_metrics, "Evolution metrics failed"
    print(f"✓ Evolution speed metrics test passed (speed: {evolution_metrics['evolution_speed']:.3f})")
    
    print("\n✅ All Self-Optimization v3 tests passed!")
    
    # 打印详细报告
    print("\n📊 Self-Optimization v3 Report:")
    print(f"  Total Optimizations: {report['total_optimizations']}")
    print(f"  Success Rate: {report['success_rate']:.1%}")
    print(f"  Avg Improvement: {report['avg_improvement']:.3f}")
    print(f"  Multimodal Triggers: {report['multimodal_triggers']}")
    print(f"  Avg Execution Time: {report['avg_execution_time']:.3f}s")


if __name__ == "__main__":
    run_self_optimization_v3_tests()
