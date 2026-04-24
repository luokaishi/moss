#!/usr/bin/env python3
"""
MOSS v9.4 - LLM Cost Controller Tests
"""

import tempfile
from pathlib import Path

import pytest

from moss.core.llm_cost_controller import (
    LLMCostController,
    CostBudget,
    CallRecord,
    CostAwareLLMBackend,
    print_cost_report,
)
from moss.core.exceptions import MossError


class TestCostBudget:
    """Test CostBudget"""

    def test_default_budget(self):
        """测试默认预算"""
        budget = CostBudget()
        assert budget.max_tokens_per_run == 10000
        assert budget.call_strategy == "every_n"
        assert budget.n_generations == 20
        assert budget.token_cost_per_1k == 0.002

    def test_budget_validation_valid(self):
        """测试有效预算"""
        budget = CostBudget()
        errors = budget.validate()
        assert len(errors) == 0

    def test_budget_validation_invalid(self):
        """测试无效预算"""
        budget = CostBudget(max_tokens_per_run=50)
        errors = budget.validate()
        assert len(errors) > 0

        budget = CostBudget(n_generations=0)
        errors = budget.validate()
        assert len(errors) > 0


class TestLLMCostController:
    """Test LLM Cost Controller"""

    def test_controller_creation(self):
        """测试创建控制器"""
        budget = CostBudget()
        controller = LLMCostController(budget)
        assert controller.budget == budget

    def test_should_call_every_n_strategy(self):
        """测试 every_n 策略"""
        budget = CostBudget(call_strategy="every_n", n_generations=20)
        controller = LLMCostController(budget)

        # 应该调用的代数
        assert controller.should_call_llm(0) is True
        assert controller.should_call_llm(20) is True
        assert controller.should_call_llm(40) is True

        # 不应该调用的代数
        assert controller.should_call_llm(1) is False
        assert controller.should_call_llm(19) is False
        assert controller.should_call_llm(21) is False

    def test_should_call_every_gen_strategy(self):
        """测试 every_gen 策略"""
        budget = CostBudget(call_strategy="every_gen")
        controller = LLMCostController(budget)

        assert controller.should_call_llm(0) is True
        assert controller.should_call_llm(1) is True
        assert controller.should_call_llm(100) is True

    def test_should_call_budget_exceeded(self):
        """测试预算超限"""
        budget = CostBudget(budget_usd=0.001)  # 很小的预算
        controller = LLMCostController(budget)

        # 记录一次昂贵的调用
        controller.record_call(0, 1000, 1000)  # 约 $0.004

        # 应该返回 False
        assert controller.should_call_llm(20) is False

    def test_should_call_token_limit(self):
        """测试 token 限制"""
        budget = CostBudget(max_tokens_per_run=100)
        controller = LLMCostController(budget)

        # 记录调用消耗 token
        controller.record_call(0, 50, 50)  # 100 tokens

        # 达到限制
        assert controller.should_call_llm(20) is False

    def test_record_call(self):
        """测试记录调用"""
        budget = CostBudget()
        controller = LLMCostController(budget)

        controller.record_call(
            generation=10,
            tokens_input=100,
            tokens_output=50,
            success=True,
        )

        assert len(controller._call_history) == 1
        assert controller._current_run_tokens == 150
        assert controller._current_run_calls == 1

    def test_get_statistics_empty(self):
        """测试空统计"""
        budget = CostBudget()
        controller = LLMCostController(budget)

        stats = controller.get_statistics()
        assert stats['total_calls'] == 0
        assert stats['total_cost_usd'] == 0.0

    def test_get_statistics_with_data(self):
        """测试有数据的统计"""
        budget = CostBudget()
        controller = LLMCostController(budget)

        controller.record_call(0, 1000, 500, success=True)
        controller.record_call(20, 1000, 500, success=True)
        controller.record_call(40, 1000, 500, success=False)

        stats = controller.get_statistics()
        assert stats['total_calls'] == 3
        assert stats['successful_calls'] == 2
        assert stats['failed_calls'] == 1
        assert stats['success_rate'] == 2/3
        assert stats['total_tokens'] == 4500
        assert stats['total_cost_usd'] > 0

    def test_budget_tracking(self):
        """测试预算跟踪"""
        budget = CostBudget(budget_usd=0.01)
        controller = LLMCostController(budget)

        assert controller.is_budget_exceeded() is False
        assert controller.get_remaining_budget() == 0.01
        assert controller.get_usage_percentage() == 0.0

        # 消耗一些预算
        controller.record_call(0, 2000, 1000)

        assert controller.get_remaining_budget() < 0.01
        assert controller.get_usage_percentage() > 0

    def test_generate_report(self):
        """测试生成报告"""
        budget = CostBudget()
        controller = LLMCostController(budget)

        controller.record_call(0, 1000, 500, success=True)
        controller.record_call(20, 1000, 500, success=True)

        report = controller.generate_report()
        assert 'summary' in report
        assert 'efficiency' in report
        assert 'call_history' in report
        assert 'recommendations' in report
        assert len(report['call_history']) == 2

    def test_save_and_load_history(self):
        """测试保存和加载历史"""
        budget = CostBudget()
        controller = LLMCostController(budget)

        controller.record_call(0, 1000, 500, success=True)
        controller.record_call(20, 1000, 500, success=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "cost_history.json"
            controller.save_history(path)

            # 加载到新控制器
            new_controller = LLMCostController(budget)
            new_controller.load_history(path)

            assert len(new_controller._call_history) == 2

    def test_reset(self):
        """测试重置"""
        budget = CostBudget()
        controller = LLMCostController(budget)

        controller.record_call(0, 1000, 500)
        assert len(controller._call_history) == 1

        controller.reset()
        assert len(controller._call_history) == 0
        assert controller._current_run_tokens == 0
        assert controller._current_run_calls == 0


class TestCostAwareLLMBackend:
    """Test CostAwareLLMBackend wrapper"""

    def test_should_call(self):
        """测试 should_call"""
        mock_backend = object()
        budget = CostBudget(call_strategy="every_n", n_generations=10)
        wrapper = CostAwareLLMBackend(mock_backend, budget)

        assert wrapper.should_call(0) is True
        assert wrapper.should_call(10) is True
        assert wrapper.should_call(5) is False

    def test_call_when_allowed(self):
        """测试允许时调用"""
        class MockBackend:
            def call(self, prompt, **kwargs):
                return f"Response to: {prompt}"

        backend = MockBackend()
        budget = CostBudget(call_strategy="every_n", n_generations=10)
        wrapper = CostAwareLLMBackend(backend, budget)

        # 在允许的代数调用
        response = wrapper.call("Hello", generation=0)
        assert "Response to:" in response

        # 检查记录
        stats = wrapper.get_report()['summary']
        assert stats['total_calls'] == 1

    def test_call_when_skipped(self):
        """测试跳过时调用"""
        class MockBackend:
            pass

        backend = MockBackend()
        budget = CostBudget(call_strategy="every_n", n_generations=10)
        wrapper = CostAwareLLMBackend(backend, budget)

        # 在不允许的代数调用
        with pytest.raises(MossError) as exc_info:
            wrapper.call("Hello", generation=5)

        assert "skipped" in str(exc_info.value).lower()

    def test_call_records_failure(self):
        """测试记录失败调用"""
        class MockBackend:
            def call(self, prompt, **kwargs):
                raise RuntimeError("API Error")

        backend = MockBackend()
        budget = CostBudget(call_strategy="every_n", n_generations=10)
        wrapper = CostAwareLLMBackend(backend, budget)

        with pytest.raises(RuntimeError):
            wrapper.call("Hello", generation=0)

        # 检查失败记录
        stats = wrapper.get_report()['summary']
        assert stats['total_calls'] == 1
        assert stats['failed_calls'] == 1


class TestPrintCostReport:
    """Test print_cost_report"""

    def test_print_report(self, capsys):
        """测试打印报告"""
        budget = CostBudget()
        controller = LLMCostController(budget)
        controller.record_call(0, 1000, 500, success=True)

        report = controller.generate_report()
        print_cost_report(report)

        captured = capsys.readouterr()
        assert "LLM Cost Report" in captured.out
        assert "Total Calls:" in captured.out
        assert "Total Cost:" in captured.out
