#!/usr/bin/env python3
"""
MOSS v9.4 - LLM Cost Controller
LLM 调用成本控制

基于 mves v8.6 经验：每 20 代 1 次 LLM 调用策略

功能：
- Token 使用量追踪
- 每 N 代 1 次策略
- 成本预算管理
- 成本报告生成

Usage:
    from moss.core.llm_cost_controller import LLMCostController, CostBudget

    budget = CostBudget(max_tokens_per_run=10000, call_strategy="every_n", n_generations=20)
    controller = LLMCostController(budget)

    if controller.should_call_llm(current_generation=20):
        result = llm_call()
        controller.record_call(tokens_used=500)

    report = controller.generate_report()
"""

import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from moss.core.exceptions import MossError

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Cost Strategy
# ═══════════════════════════════════════════════════════════

class CallStrategy(Enum):
    """LLM 调用策略"""
    EVERY_GENERATION = "every_gen"  # 每代都调用
    EVERY_N_GENERATIONS = "every_n"  # 每 N 代调用 (mves 推荐)
    ADAPTIVE = "adaptive"  # 自适应 (基于进展)
    ON_DEMAND = "on_demand"  # 按需 (外部触发)


# ═══════════════════════════════════════════════════════════
# Cost Budget
# ═══════════════════════════════════════════════════════════

@dataclass
class CostBudget:
    """
    LLM 成本预算配置

    Attributes:
        max_tokens_per_run: 单次运行最大 token 数
        max_calls_per_run: 单次运行最大调用次数
        call_strategy: 调用策略
        n_generations: 每 N 代调用一次 (for every_n strategy)
        token_cost_per_1k: 每 1000 token 成本 (USD)
        budget_usd: 总预算 (USD)，0 表示无限制
    """
    max_tokens_per_run: int = 10000
    max_calls_per_run: int = 50
    call_strategy: str = "every_n"
    n_generations: int = 20  # mves 经验值
    token_cost_per_1k: float = 0.002  # GPT-3.5 价格
    budget_usd: float = 0.0  # 0 = 无限制

    def validate(self) -> List[str]:
        """验证配置"""
        errors = []
        if self.max_tokens_per_run < 100:
            errors.append("max_tokens_per_run must be >= 100")
        if self.max_calls_per_run < 1:
            errors.append("max_calls_per_run must be >= 1")
        if self.n_generations < 1:
            errors.append("n_generations must be >= 1")
        if self.token_cost_per_1k <= 0:
            errors.append("token_cost_per_1k must be > 0")
        return errors


# ═══════════════════════════════════════════════════════════
# Call Record
# ═══════════════════════════════════════════════════════════

@dataclass
class CallRecord:
    """单次 LLM 调用记录"""
    timestamp: float
    generation: int
    tokens_input: int
    tokens_output: int
    cost_usd: float
    success: bool
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'generation': self.generation,
            'tokens_input': self.tokens_input,
            'tokens_output': self.tokens_output,
            'tokens_total': self.tokens_input + self.tokens_output,
            'cost_usd': round(self.cost_usd, 6),
            'success': self.success,
            'error': self.error,
        }


# ═══════════════════════════════════════════════════════════
# Cost Controller
# ═══════════════════════════════════════════════════════════

class LLMCostController:
    """
    LLM 成本控制器

    管理 LLM 调用的成本、频率和预算。

    Example:
        controller = LLMCostController(CostBudget(n_generations=20))

        for gen in range(100):
            if controller.should_call_llm(gen):
                response = llm_api.call(prompt)
                controller.record_call(
                    generation=gen,
                    tokens_input=len(prompt),
                    tokens_output=len(response),
                )

            if controller.is_budget_exceeded():
                logger.warning("Budget exceeded, stopping")
                break

        report = controller.generate_report()
        print(f"Total cost: ${report['total_cost_usd']:.4f}")
    """

    def __init__(self, budget: Optional[CostBudget] = None):
        self.budget = budget or CostBudget()
        self._call_history: List[CallRecord] = []
        self._current_run_tokens = 0
        self._current_run_calls = 0
        self._start_time = time.time()

        # 验证预算
        errors = self.budget.validate()
        if errors:
            raise MossError(f"Invalid cost budget: {errors}")

    # ── Decision Making ──

    def should_call_llm(self, current_generation: int) -> bool:
        """
        决定是否应该调用 LLM

        Args:
            current_generation: 当前代数

        Returns:
            True 如果应该调用 LLM
        """
        # 检查预算
        if self.is_budget_exceeded():
            logger.warning("Budget exceeded, skipping LLM call")
            return False

        # 检查 token 限制
        if self._current_run_tokens >= self.budget.max_tokens_per_run:
            logger.warning("Token limit reached, skipping LLM call")
            return False

        # 检查调用次数限制
        if self._current_run_calls >= self.budget.max_calls_per_run:
            logger.warning("Call limit reached, skipping LLM call")
            return False

        # 根据策略决定
        strategy = self.budget.call_strategy

        if strategy == CallStrategy.EVERY_GENERATION.value:
            return True

        elif strategy == CallStrategy.EVERY_N_GENERATIONS.value:
            # 每 N 代调用一次 (mves 推荐策略)
            should_call = current_generation % self.budget.n_generations == 0
            if should_call:
                logger.debug(f"Generation {current_generation}: scheduled LLM call (every {self.budget.n_generations})")
            return should_call

        elif strategy == CallStrategy.ADAPTIVE.value:
            # 自适应策略：基于进展决定
            return self._adaptive_decision(current_generation)

        elif strategy == CallStrategy.ON_DEMAND.value:
            # 按需策略：外部决定
            return False

        else:
            logger.warning(f"Unknown strategy: {strategy}, defaulting to every_n")
            return current_generation % 20 == 0

    def _adaptive_decision(self, current_generation: int) -> bool:
        """
        自适应决策

        基于历史表现决定是否需要 LLM 调用。
        """
        if not self._call_history:
            return True  # 第一次总是调用

        # 获取最近几次调用的成功率
        recent_calls = self._call_history[-5:]
        if not recent_calls:
            return True

        success_rate = sum(1 for c in recent_calls if c.success) / len(recent_calls)

        # 如果成功率低，增加调用频率
        if success_rate < 0.5:
            return current_generation % 10 == 0  # 更频繁
        else:
            return current_generation % 30 == 0  # 更稀疏

    # ── Recording ──

    def record_call(
        self,
        generation: int,
        tokens_input: int,
        tokens_output: int,
        success: bool = True,
        error: Optional[str] = None,
    ) -> None:
        """
        记录一次 LLM 调用

        Args:
            generation: 当前代数
            tokens_input: 输入 token 数
            tokens_output: 输出 token 数
            success: 是否成功
            error: 错误信息 (如果失败)
        """
        tokens_total = tokens_input + tokens_output
        cost = (tokens_total / 1000) * self.budget.token_cost_per_1k

        record = CallRecord(
            timestamp=time.time(),
            generation=generation,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            cost_usd=cost,
            success=success,
            error=error,
        )

        self._call_history.append(record)
        self._current_run_tokens += tokens_total
        self._current_run_calls += 1

        logger.debug(
            f"Recorded LLM call: gen={generation}, "
            f"tokens={tokens_total}, cost=${cost:.6f}"
        )

    # ── Budget Checking ──

    def is_budget_exceeded(self) -> bool:
        """检查是否超出预算"""
        if self.budget.budget_usd <= 0:
            return False  # 无预算限制

        total_cost = sum(r.cost_usd for r in self._call_history)
        return total_cost >= self.budget.budget_usd

    def get_remaining_budget(self) -> float:
        """获取剩余预算"""
        if self.budget.budget_usd <= 0:
            return float('inf')

        total_cost = sum(r.cost_usd for r in self._call_history)
        return max(0, self.budget.budget_usd - total_cost)

    def get_usage_percentage(self) -> float:
        """获取预算使用百分比"""
        if self.budget.budget_usd <= 0:
            return 0.0

        total_cost = sum(r.cost_usd for r in self._call_history)
        return (total_cost / self.budget.budget_usd) * 100

    # ── Statistics ──

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self._call_history:
            return {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'total_tokens': 0,
                'total_tokens_input': 0,
                'total_tokens_output': 0,
                'total_cost_usd': 0.0,
                'success_rate': 0.0,
                'avg_tokens_per_call': 0.0,
                'avg_cost_per_call': 0.0,
                'budget_usd': self.budget.budget_usd,
                'remaining_budget_usd': self.budget.budget_usd,
                'budget_usage_percent': 0.0,
            }

        total_calls = len(self._call_history)
        successful_calls = sum(1 for r in self._call_history if r.success)
        total_tokens = sum(r.tokens_input + r.tokens_output for r in self._call_history)
        total_cost = sum(r.cost_usd for r in self._call_history)

        return {
            'total_calls': total_calls,
            'successful_calls': successful_calls,
            'failed_calls': total_calls - successful_calls,
            'success_rate': successful_calls / total_calls,
            'total_tokens': total_tokens,
            'total_tokens_input': sum(r.tokens_input for r in self._call_history),
            'total_tokens_output': sum(r.tokens_output for r in self._call_history),
            'total_cost_usd': round(total_cost, 6),
            'avg_tokens_per_call': total_tokens / total_calls,
            'avg_cost_per_call': round(total_cost / total_calls, 6),
            'budget_usd': self.budget.budget_usd,
            'remaining_budget_usd': round(self.get_remaining_budget(), 6),
            'budget_usage_percent': round(self.get_usage_percentage(), 2),
        }

    def generate_report(self) -> Dict[str, Any]:
        """
        生成成本报告

        Returns:
            详细的成本报告字典
        """
        stats = self.get_statistics()
        duration = time.time() - self._start_time

        # 按代数分组
        calls_by_generation: Dict[int, List[CallRecord]] = {}
        for record in self._call_history:
            gen = record.generation
            if gen not in calls_by_generation:
                calls_by_generation[gen] = []
            calls_by_generation[gen].append(record)

        # 计算效率指标
        efficiency = {
            'tokens_per_dollar': stats['total_tokens'] / stats['total_cost_usd'] if stats['total_cost_usd'] > 0 else 0,
            'calls_per_hour': stats['total_calls'] / (duration / 3600) if duration > 0 else 0,
            'cost_per_generation': stats['total_cost_usd'] / len(calls_by_generation) if calls_by_generation else 0,
        }

        return {
            'summary': stats,
            'duration_seconds': round(duration, 2),
            'efficiency': {k: round(v, 4) for k, v in efficiency.items()},
            'call_history': [r.to_dict() for r in self._call_history],
            'generations_with_calls': sorted(calls_by_generation.keys()),
            'recommendations': self._generate_recommendations(stats),
        }

    def _generate_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """生成优化建议"""
        recommendations = []

        if stats['success_rate'] < 0.7:
            recommendations.append("Success rate is low (<70%), consider adjusting prompts or model")

        if stats['budget_usage_percent'] > 90:
            recommendations.append("Budget nearly exhausted (>90%), consider increasing budget or reducing calls")

        if stats['avg_tokens_per_call'] > 4000:
            recommendations.append("High token usage per call, consider optimizing prompts")

        if stats['total_calls'] > 0 and stats['total_calls'] < 5:
            recommendations.append("Very few calls, consider using more aggressive strategy")

        if not recommendations:
            recommendations.append("Cost efficiency is good, no immediate action needed")

        return recommendations

    # ── Persistence ──

    def save_history(self, path: Path) -> None:
        """保存调用历史到文件"""
        data = {
            'budget': {
                'max_tokens_per_run': self.budget.max_tokens_per_run,
                'max_calls_per_run': self.budget.max_calls_per_run,
                'call_strategy': self.budget.call_strategy,
                'n_generations': self.budget.n_generations,
                'token_cost_per_1k': self.budget.token_cost_per_1k,
                'budget_usd': self.budget.budget_usd,
            },
            'statistics': self.get_statistics(),
            'call_history': [r.to_dict() for r in self._call_history],
        }

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Cost history saved to {path}")

    def load_history(self, path: Path) -> None:
        """从文件加载调用历史"""
        if not path.exists():
            logger.warning(f"No history file found at {path}")
            return

        with open(path) as f:
            data = json.load(f)

        # 恢复历史记录
        for record_data in data.get('call_history', []):
            record = CallRecord(
                timestamp=record_data['timestamp'],
                generation=record_data['generation'],
                tokens_input=record_data['tokens_input'],
                tokens_output=record_data['tokens_output'],
                cost_usd=record_data['cost_usd'],
                success=record_data['success'],
                error=record_data.get('error'),
            )
            self._call_history.append(record)

        logger.info(f"Loaded {len(self._call_history)} records from {path}")

    # ── Reset ──

    def reset(self) -> None:
        """重置控制器状态"""
        self._call_history.clear()
        self._current_run_tokens = 0
        self._current_run_calls = 0
        self._start_time = time.time()
        logger.info("Cost controller reset")


# ═══════════════════════════════════════════════════════════
# Cost-Aware LLM Backend Wrapper
# ═══════════════════════════════════════════════════════════

class CostAwareLLMBackend:
    """
    成本感知的 LLM Backend 包装器

    包装现有的 LLM Backend，添加成本控制。

    Example:
        from moss.core.llm_backend import LLMBackend
        from moss.core.llm_cost_controller import CostAwareLLMBackend, CostBudget

        base_backend = LLMBackend(config)
        budget = CostBudget(n_generations=20)
        cost_backend = CostAwareLLMBackend(base_backend, budget)

        for gen in range(100):
            if cost_backend.should_call(gen):
                response = cost_backend.call(prompt, generation=gen)
    """

    def __init__(self, backend: Any, budget: Optional[CostBudget] = None):
        self.backend = backend
        self.controller = LLMCostController(budget)

    def should_call(self, generation: int) -> bool:
        """检查是否应该调用"""
        return self.controller.should_call_llm(generation)

    def call(self, prompt: str, generation: int, **kwargs) -> Any:
        """
        调用 LLM (带成本控制)

        Args:
            prompt: 提示词
            generation: 当前代数
            **kwargs: 传递给 backend 的参数

        Returns:
            Backend 的响应
        """
        if not self.should_call(generation):
            raise MossError(
                f"LLM call skipped for generation {generation} due to cost control",
                suggestion=f"Next call at generation {(generation // self.controller.budget.n_generations + 1) * self.controller.budget.n_generations}"
            )

        try:
            # 估算输入 token (简化估算：1 token ≈ 4 chars)
            tokens_input = len(prompt) // 4

            # 调用 backend
            response = self.backend.call(prompt, **kwargs)

            # 估算输出 token
            if isinstance(response, str):
                tokens_output = len(response) // 4
            else:
                tokens_output = tokens_input  # 默认假设

            # 记录调用
            self.controller.record_call(
                generation=generation,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                success=True,
            )

            return response

        except Exception as e:
            # 记录失败
            self.controller.record_call(
                generation=generation,
                tokens_input=len(prompt) // 4,
                tokens_output=0,
                success=False,
                error=str(e),
            )
            raise

    def get_report(self) -> Dict[str, Any]:
        """获取成本报告"""
        return self.controller.generate_report()


# ═══════════════════════════════════════════════════════════
# CLI Helper
# ═══════════════════════════════════════════════════════════

def print_cost_report(report: Dict[str, Any]) -> None:
    """打印成本报告"""
    stats = report['summary']

    print("\n" + "="*60)
    print("LLM Cost Report")
    print("="*60)
    print(f"Total Calls: {stats['total_calls']}")
    print(f"Successful: {stats['successful_calls']}")
    print(f"Failed: {stats['failed_calls']}")
    print(f"Success Rate: {stats['success_rate']*100:.1f}%")
    print("-"*60)
    print(f"Total Tokens: {stats['total_tokens']:,}")
    print(f"  Input: {stats['total_tokens_input']:,}")
    print(f"  Output: {stats['total_tokens_output']:,}")
    print("-"*60)
    print(f"Total Cost: ${stats['total_cost_usd']:.4f} USD")
    print(f"Avg Cost/Call: ${stats['avg_cost_per_call']:.6f}")
    print("-"*60)
    if stats['budget_usd'] > 0:
        print(f"Budget: ${stats['budget_usd']:.2f}")
        print(f"Remaining: ${stats['remaining_budget_usd']:.4f}")
        print(f"Usage: {stats['budget_usage_percent']:.1f}%")
    print("="*60)
    print("\nRecommendations:")
    for rec in report['recommendations']:
        print(f"  • {rec}")
    print()
