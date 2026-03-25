"""
MOSS Self-Optimization Module v2
自优化模块闭环设计 v2 - 解决Kimi评估缺陷#3

实现：触发条件 → 执行边界 → 评估标准 完整闭环
"""

import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from enum import Enum
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OptimizationTrigger(Enum):
    """优化触发条件类型"""
    RESOURCE_THRESHOLD = "resource_threshold"    # 资源≥30%
    PERFORMANCE_PLATEAU = "performance_plateau"  # 连续N步无提升
    SCHEDULED = "scheduled"                      # 定时触发
    MANUAL = "manual"                            # 手动触发


class OptimizationScope(Enum):
    """优化范围"""
    KNOWLEDGE_BASE = "knowledge_base"      # 允许：知识库重组
    STRATEGY_PARAMS = "strategy_params"    # 允许：策略参数微调
    WEIGHT_TUNING = "weight_tuning"        # 允许：权重微调（±10%）
    MODULE_STRUCTURE = "module_structure"  # 禁止：模块结构修改
    CORE_OBJECTIVES = "core_objectives"    # 禁止：核心目标修改
    SAFETY_RULES = "safety_rules"          # 禁止：安全规则修改


class SelfOptimizationModule:
    """
    自优化模块闭环系统
    
    Kimi要求：
    - 触发条件：资源≥30%、连续100步无提升
    - 执行边界：禁止修改核心安全模块
    - 评估指标：任务完成率、资源利用率、进化速度
    """
    
    # 硬编码安全边界 - 绝对禁止修改
    PROTECTED_MODULES = [
        'core.objectives.SurvivalModule',
        'core.objectives.base.ObjectiveModule',
        'core.gradient_safety_guard.GradientSafetyGuard',
        'core.conflict_resolver_enhanced.ConflictResolver',
    ]
    
    def __init__(self):
        # 触发条件配置
        self.trigger_config = {
            'resource_threshold': 0.30,           # 资源≥30%
            'performance_plateau_steps': 100,     # 连续100步无提升
            'min_performance_improvement': 0.01,  # 最小提升阈值1%
            'scheduled_interval_hours': 24,       # 定时24小时
        }
        
        # 执行边界配置
        self.allowed_scopes = [
            OptimizationScope.KNOWLEDGE_BASE,
            OptimizationScope.STRATEGY_PARAMS,
            OptimizationScope.WEIGHT_TUNING,
        ]
        
        self.forbidden_scopes = [
            OptimizationScope.MODULE_STRUCTURE,
            OptimizationScope.CORE_OBJECTIVES,
            OptimizationScope.SAFETY_RULES,
        ]
        
        # 评估指标历史
        self.performance_history = []
        self.optimization_history = []
        
        # 状态
        self.last_optimization_time = None
        self.consecutive_no_improvement = 0
        self.is_optimizing = False
    
    def check_trigger(self, state: Dict) -> Optional[OptimizationTrigger]:
        """
        检查是否满足优化触发条件
        
        Args:
            state: 当前系统状态
        
        Returns:
            触发类型或None
        """
        # 检查1: 资源阈值
        resource_quota = state.get('resource_quota', 0)
        if resource_quota >= self.trigger_config['resource_threshold']:
            logger.info(f"[OPTIMIZATION TRIGGER] Resource threshold: {resource_quota:.2%} ≥ {self.trigger_config['resource_threshold']:.0%}")
            return OptimizationTrigger.RESOURCE_THRESHOLD
        
        # 检查2: 性能平台期
        if len(self.performance_history) >= 2:
            # 提取最近10个记录的task_completion_rate（或第一个可用指标）
            recent_records = self.performance_history[-10:]  # 最近10个
            if len(recent_records) >= 10:
                # 从metrics字典中提取task_completion_rate，如果不存在则使用0
                recent_perf = [r['metrics'].get('task_completion_rate', 0) for r in recent_records]
                improvement = max(recent_perf) - min(recent_perf)
                if improvement < self.trigger_config['min_performance_improvement']:
                    self.consecutive_no_improvement += 1
                    if self.consecutive_no_improvement >= self.trigger_config['performance_plateau_steps']:
                        logger.info(f"[OPTIMIZATION TRIGGER] Performance plateau: {self.consecutive_no_improvement} steps no improvement")
                        self.consecutive_no_improvement = 0
                        return OptimizationTrigger.PERFORMANCE_PLATEAU
                else:
                    self.consecutive_no_improvement = 0
        
        # 检查3: 定时触发
        if self.last_optimization_time:
            hours_since = (datetime.now() - self.last_optimization_time).total_seconds() / 3600
            if hours_since >= self.trigger_config['scheduled_interval_hours']:
                logger.info(f"[OPTIMIZATION TRIGGER] Scheduled: {hours_since:.1f}h since last optimization")
                return OptimizationTrigger.SCHEDULED
        
        return None
    
    def can_optimize(self, scope: OptimizationScope) -> bool:
        """
        检查优化范围是否在允许边界内
        
        Args:
            scope: 优化范围
        
        Returns:
            是否允许
        """
        if scope in self.forbidden_scopes:
            logger.error(f"[OPTIMIZATION REJECTED] Forbidden scope: {scope.value}")
            return False
        
        if scope not in self.allowed_scopes:
            logger.warning(f"[OPTIMIZATION REJECTED] Unknown scope: {scope.value}")
            return False
        
        return True
    
    def execute_optimization(self, scope: OptimizationScope, 
                           current_params: Dict) -> Dict:
        """
        执行优化（在边界内）
        
        Args:
            scope: 优化范围
            current_params: 当前参数
        
        Returns:
            优化后参数
        """
        if not self.can_optimize(scope):
            raise PermissionError(f"Optimization scope {scope.value} is forbidden")
        
        self.is_optimizing = True
        logger.info(f"[OPTIMIZATION START] Scope: {scope.value}")
        
        try:
            if scope == OptimizationScope.KNOWLEDGE_BASE:
                # 知识库重组：去重、索引优化
                optimized = self._optimize_knowledge_base(current_params)
            
            elif scope == OptimizationScope.STRATEGY_PARAMS:
                # 策略参数微调
                optimized = self._optimize_strategy_params(current_params)
            
            elif scope == OptimizationScope.WEIGHT_TUNING:
                # 权重微调（±10%限制）
                optimized = self._optimize_weights(current_params)
            
            else:
                optimized = current_params
            
            # 记录优化历史
            self.optimization_history.append({
                'timestamp': datetime.now().isoformat(),
                'scope': scope.value,
                'before': current_params,
                'after': optimized,
            })
            
            self.last_optimization_time = datetime.now()
            logger.info(f"[OPTIMIZATION COMPLETE] Scope: {scope.value}")
            
            return optimized
            
        finally:
            self.is_optimizing = False
    
    def _optimize_knowledge_base(self, params: Dict) -> Dict:
        """优化知识库"""
        optimized = params.copy()
        # 模拟：去重、排序
        if 'knowledge_items' in optimized:
            # 去重
            seen = set()
            unique_items = []
            for item in optimized['knowledge_items']:
                key = item.get('content', '')[:50]  # 前50字符作为key
                if key not in seen:
                    seen.add(key)
                    unique_items.append(item)
            optimized['knowledge_items'] = unique_items
            logger.info(f"Knowledge base dedup: {len(params['knowledge_items'])} → {len(unique_items)}")
        return optimized
    
    def _optimize_strategy_params(self, params: Dict) -> Dict:
        """优化策略参数"""
        optimized = params.copy()
        # 微调学习率、探索率等
        if 'learning_rate' in optimized:
            # 自适应调整
            optimized['learning_rate'] *= 0.95  # 略微降低
            logger.info(f"Strategy param tuned: learning_rate adjusted")
        return optimized
    
    def _optimize_weights(self, params: Dict) -> Dict:
        """优化权重（±10%限制）"""
        optimized = params.copy()
        if 'weights' in optimized:
            weights = optimized['weights'].copy()
            for key in weights:
                # 仅允许±10%调整
                adjustment = np.random.uniform(-0.1, 0.1)
                weights[key] = max(0.01, min(0.99, weights[key] * (1 + adjustment)))
            
            # 归一化
            total = sum(weights.values())
            weights = {k: v/total for k, v in weights.items()}
            
            optimized['weights'] = weights
            logger.info(f"Weights tuned with ±10% limit: {weights}")
        return optimized
    
    def evaluate_optimization(self, before_metrics: Dict, 
                            after_metrics: Dict) -> Dict:
        """
        评估优化效果
        
        Kimi要求评估指标：
        - 任务完成率
        - 资源利用率
        - 进化速度
        
        Args:
            before_metrics: 优化前指标
            after_metrics: 优化后指标
        
        Returns:
            评估结果
        """
        # 1. 任务完成率变化
        task_completion_before = before_metrics.get('task_completion_rate', 0)
        task_completion_after = after_metrics.get('task_completion_rate', 0)
        task_improvement = task_completion_after - task_completion_before
        
        # 2. 资源利用率变化
        resource_util_before = before_metrics.get('resource_utilization', 0)
        resource_util_after = after_metrics.get('resource_utilization', 0)
        resource_improvement = resource_util_after - resource_util_before
        
        # 3. 进化速度（知识获取率）
        knowledge_rate_before = before_metrics.get('knowledge_acquisition_rate', 0)
        knowledge_rate_after = after_metrics.get('knowledge_acquisition_rate', 0)
        evolution_speed = knowledge_rate_after - knowledge_rate_before
        
        # 综合评分
        overall_score = (
            task_improvement * 0.4 +      # 任务完成率权重40%
            resource_improvement * 0.3 +   # 资源利用率权重30%
            evolution_speed * 0.3          # 进化速度权重30%
        )
        
        evaluation = {
            'timestamp': datetime.now().isoformat(),
            'task_completion': {
                'before': task_completion_before,
                'after': task_completion_after,
                'improvement': task_improvement
            },
            'resource_utilization': {
                'before': resource_util_before,
                'after': resource_util_after,
                'improvement': resource_improvement
            },
            'evolution_speed': {
                'before': knowledge_rate_before,
                'after': knowledge_rate_after,
                'improvement': evolution_speed
            },
            'overall_score': overall_score,
            'is_positive': overall_score > 0,
            'recommendation': 'KEEP' if overall_score > 0.05 else ('REVERT' if overall_score < -0.05 else 'MONITOR')
        }
        
        logger.info(f"[OPTIMIZATION EVALUATION] Overall score: {overall_score:.3f}, Recommendation: {evaluation['recommendation']}")
        
        return evaluation
    
    def record_performance(self, metrics: Dict):
        """记录性能指标"""
        self.performance_history.append({
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics
        })
        
        # 保留最近1000条
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]
    
    def get_status_report(self) -> Dict:
        """获取状态报告"""
        return {
            'trigger_config': self.trigger_config,
            'allowed_scopes': [s.value for s in self.allowed_scopes],
            'forbidden_scopes': [s.value for s in self.forbidden_scopes],
            'last_optimization': self.last_optimization_time.isoformat() if self.last_optimization_time else None,
            'optimization_count': len(self.optimization_history),
            'recent_optimizations': self.optimization_history[-5:],
            'plateau_counter': self.consecutive_no_improvement,
            'is_optimizing': self.is_optimizing
        }


# 演示
def demo_self_optimization():
    """演示自优化闭环"""
    print("="*70)
    print("MOSS SELF-OPTIMIZATION MODULE v2 DEMO")
    print("Addressing Kimi's Defect #3: Self-optimization closed-loop design")
    print("="*70)
    print()
    
    module = SelfOptimizationModule()
    
    # 场景1: 触发条件检查
    print("Scenario 1: Trigger Condition Check")
    print("-"*70)
    
    # 模拟状态 - 资源充足
    state_high_resource = {'resource_quota': 0.35}
    trigger = module.check_trigger(state_high_resource)
    print(f"State: resource=35%")
    print(f"Trigger: {trigger.value if trigger else 'None'}")
    print()
    
    # 场景2: 执行边界检查
    print("Scenario 2: Execution Boundary Check")
    print("-"*70)
    
    for scope in OptimizationScope:
        can_do = module.can_optimize(scope)
        status = "✅ ALLOWED" if can_do else "❌ FORBIDDEN"
        print(f"{scope.value:<25} {status}")
    print()
    
    # 场景3: 执行优化
    print("Scenario 3: Execute Optimization")
    print("-"*70)
    
    current_params = {
        'weights': {'survival': 0.6, 'curiosity': 0.1, 'influence': 0.2, 'optimization': 0.1},
        'learning_rate': 0.01,
        'knowledge_items': [
            {'content': 'item A', 'timestamp': '2026-03-10'},
            {'content': 'item A', 'timestamp': '2026-03-10'},  # 重复
            {'content': 'item B', 'timestamp': '2026-03-10'},
        ]
    }
    
    try:
        optimized = module.execute_optimization(
            OptimizationScope.WEIGHT_TUNING,
            current_params
        )
        print(f"Before: {current_params['weights']}")
        print(f"After:  {optimized['weights']}")
    except PermissionError as e:
        print(f"Error: {e}")
    print()
    
    # 场景4: 评估优化效果
    print("Scenario 4: Evaluate Optimization")
    print("-"*70)
    
    before = {'task_completion_rate': 0.7, 'resource_utilization': 0.6, 'knowledge_acquisition_rate': 0.5}
    after = {'task_completion_rate': 0.75, 'resource_utilization': 0.65, 'knowledge_acquisition_rate': 0.55}
    
    evaluation = module.evaluate_optimization(before, after)
    print(f"Overall Score: {evaluation['overall_score']:.3f}")
    print(f"Recommendation: {evaluation['recommendation']}")
    print()
    
    # 状态报告
    print("="*70)
    print("FINAL STATUS REPORT")
    print("="*70)
    report = module.get_status_report()
    print(json.dumps(report, indent=2, default=str))


if __name__ == '__main__':
    import json
    demo_self_optimization()
