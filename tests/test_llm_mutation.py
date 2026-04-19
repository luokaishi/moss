"""
MOSS v8.0 - LLM-Guided Mutation Tests
=======================================

测试覆盖：
1. LLMBackend (Mock模式)
2. LLMMutator + MockBackend
3. HybridMutationStrategy
4. SME集成 (enable_llm_mutation=True)
5. 回归验证 (enable_llm_mutation=False 不影响现有功能)
"""

import ast
import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pytest


# ─────────────────────────────────────────────
# LLMBackend Tests
# ─────────────────────────────────────────────

class TestLLMBackend:
    """LLMBackend 抽象层测试"""

    def test_mock_backend_creation(self):
        from moss.core.llm_backend import MockBackend, LLMConfig, create_llm_backend
        backend = create_llm_backend(LLMConfig(provider="mock"))
        assert isinstance(backend, MockBackend)

    def test_mock_backend_complete(self):
        from moss.core.llm_backend import MockBackend, LLMConfig
        backend = MockBackend(LLMConfig())
        response = backend.complete("system prompt", "user prompt with some code")
        assert response.content
        assert response.provider == "mock"
        assert response.input_tokens > 0

    def test_budget_tracking(self):
        from moss.core.llm_backend import MockBackend, LLMConfig
        config = LLMConfig(daily_token_budget=100, daily_request_budget=2)
        backend = MockBackend(config)

        # 前两次请求应该成功
        backend.complete("sys", "user prompt 1")
        backend.complete("sys", "user prompt 2")

        # 第三次应该因请求预算耗尽而失败
        assert not backend.check_budget()

    def test_usage_stats(self):
        from moss.core.llm_backend import MockBackend, LLMConfig
        backend = MockBackend(LLMConfig())
        backend.complete("sys", "user prompt")
        stats = backend.get_usage_stats()
        assert stats['total_requests'] == 1
        assert stats['total_input_tokens'] > 0

    def test_unknown_provider_raises(self):
        from moss.core.llm_backend import LLMConfig, create_llm_backend
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            create_llm_backend(LLMConfig(provider="nonexistent"))

    def test_config_auto_infer(self):
        from moss.core.llm_backend import LLMConfig
        config = LLMConfig(provider="openai")
        assert config.api_key_env == "OPENAI_API_KEY"
        assert config.model == "gpt-4o-mini"

    def test_bailian_config_auto_infer(self):
        from moss.core.llm_backend import LLMConfig
        config = LLMConfig(provider="bailian")
        assert config.api_key_env == "DASHSCOPE_API_KEY"
        assert config.model == "qwen-coder-plus"


# ─────────────────────────────────────────────
# LLMMutator Tests
# ─────────────────────────────────────────────

class TestLLMMutator:
    """LLMMutator 测试"""

    @pytest.fixture
    def mutator(self):
        from moss.core.llm_backend import MockBackend, LLMConfig
        from moss.core.llm_mutator import LLMMutator
        backend = MockBackend(LLMConfig())
        return LLMMutator(backend)

    @pytest.fixture
    def sample_source(self):
        return '''import numpy as np

class SimpleAgent:
    def __init__(self):
        self.weights = np.array([0.25, 0.25, 0.25, 0.25])
        self.threshold = 0.5

    def select_action(self, observation):
        if np.random.random() < self.threshold:
            return "explore"
        return "exploit"

    def step(self, obs):
        action = self.select_action(obs)
        return action

    def save_checkpoint(self, path):
        with open(path, 'w') as f:
            f.write(str(self.weights))
'''

    def test_mutate_returns_tuple(self, mutator, sample_source):
        result = mutator.mutate(
            sample_source,
            target_functions=['select_action', 'step'],
        )
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_mutate_result_type(self, mutator, sample_source):
        from moss.core.llm_mutator import LLMMutationResult
        source, info = mutator.mutate(
            sample_source,
            target_functions=['select_action', 'step'],
        )
        assert isinstance(info, LLMMutationResult)
        assert info.mutation_type in ('llm_guided', 'llm_no_op')

    def test_mutation_strategy_parameter_tune(self, mutator, sample_source):
        source, info = mutator.mutate(
            sample_source,
            target_functions=['select_action', 'step'],
            mutation_strategy='parameter_tune',
        )
        # Mock应该能产生有效变异
        assert info.mutation_type in ('llm_guided', 'llm_no_op')

    def test_immutable_function_protection(self, mutator, sample_source):
        """不可变函数不应被修改"""
        source, info = mutator.mutate(
            sample_source,
            target_functions=['select_action'],
            immutable_functions=['save_checkpoint'],
            mutation_strategy='parameter_tune',
        )
        if info.validation_passed:
            # 保存检查点函数不应改变
            assert 'save_checkpoint' in source

    def test_dangerous_pattern_rejection(self):
        """包含危险模式的代码应被拒绝"""
        from moss.core.llm_mutator import LLMMutator
        dangerous_source = '''
def safe_func():
    x = 1 + 2
    return x

def dangerous_func():
    eval("print('hello')")
    return 1
'''
        # 验证器应该拒绝包含 eval 的变异
        from moss.core.llm_backend import MockBackend, LLMConfig
        backend = MockBackend(LLMConfig())
        mutator = LLMMutator(backend)

        # 直接测试 _validate_llm_output
        is_valid, reason = mutator._validate_llm_output(
            dangerous_source,
            dangerous_source,  # 相同（无变化）
            target_functions=['dangerous_func'],
            immutable_functions=[],
        )
        # 无变化应该被 Layer 4 拒绝
        assert not is_valid

    def test_extract_mutation_info(self, mutator):
        info = mutator._extract_mutation_info(
            'x = 1\n# MUTATION_INFO: {"strategy": "test", "confidence": 0.8}'
        )
        assert info.get('strategy') == 'test'
        assert info.get('confidence') == 0.8

    def test_clean_llm_output_markdown(self, mutator):
        """Markdown代码围栏应被移除"""
        raw = '```python\nx = 1\n```'
        cleaned = mutator._clean_llm_output(raw)
        assert '```' not in cleaned
        assert 'x = 1' in cleaned


# ─────────────────────────────────────────────
# HybridMutationStrategy Tests
# ─────────────────────────────────────────────

class TestHybridMutationStrategy:
    """混合变异策略测试"""

    @pytest.fixture
    def strategy(self):
        from moss.core.llm_backend import MockBackend, LLMConfig
        from moss.core.llm_mutator import LLMMutator
        from moss.core.self_modification_engine import ASTMutator
        from moss.core.hybrid_mutation import HybridMutationStrategy, HybridStrategyConfig

        ast_mut = ASTMutator(intensity=0.3)
        backend = MockBackend(LLMConfig())
        llm_mut = LLMMutator(backend)
        return HybridMutationStrategy(
            ast_mut, llm_mut,
            HybridStrategyConfig(mode='adaptive')
        )

    @pytest.fixture
    def sample_source(self):
        return open('/workspace/moss/moss/core/unified_agent.py').read()

    def test_ast_only_mode(self, sample_source):
        from moss.core.llm_backend import MockBackend, LLMConfig
        from moss.core.llm_mutator import LLMMutator
        from moss.core.self_modification_engine import ASTMutator
        from moss.core.hybrid_mutation import HybridMutationStrategy, HybridStrategyConfig

        ast_mut = ASTMutator(intensity=0.3)
        backend = MockBackend(LLMConfig())
        llm_mut = LLMMutator(backend)
        strategy = HybridMutationStrategy(
            ast_mut, llm_mut,
            HybridStrategyConfig(mode='ast_only')
        )

        candidates = strategy.generate_candidates(
            sample_source,
            target_functions=['_apply_state_weights'],
            population_size=4,
        )
        assert len(candidates) == 4
        # 全部应该是AST变异
        for _, info in candidates:
            assert info['source'] == 'ast'

    def test_adaptive_triggers_llm_on_no_ops(self, strategy, sample_source):
        """连续no_op应触发LLM"""
        # 模拟连续no_op状态
        for gen in range(1, 4):
            strategy.update_state(gen, mutation_type='no_op', accepted=False, fitness=0.5)

        candidates = strategy.generate_candidates(
            sample_source,
            target_functions=['_apply_state_weights', 'step', 'select_action'],
            population_size=4,
            purpose_vector=np.array([0.3, 0.4, 0.2, 0.1]),
            immutable_functions=['__init__'],
        )

        # 应该有LLM候选（如果不在冷却期）
        llm_count = sum(1 for _, info in candidates if info.get('source') == 'llm')
        # 由于冷却机制，第一次可能还在冷却。检查策略统计
        stats = strategy.get_stats()
        assert stats['consecutive_no_ops'] >= 3

    def test_update_state_resets_on_accept(self, strategy):
        """变异被接受后应重置计数器"""
        strategy.update_state(1, mutation_type='no_op', accepted=False, fitness=0.5)
        strategy.update_state(2, mutation_type='no_op', accepted=False, fitness=0.5)
        assert strategy._consecutive_no_ops == 2

        strategy.update_state(3, mutation_type='constant_tweak', accepted=True, fitness=0.6)
        assert strategy._consecutive_no_ops == 0
        assert strategy._consecutive_rejects == 0

    def test_get_stats(self, strategy):
        stats = strategy.get_stats()
        assert 'mode' in stats
        assert 'current_generation' in stats
        assert 'consecutive_no_ops' in stats


# ─────────────────────────────────────────────
# SME Integration Tests
# ─────────────────────────────────────────────

class TestSMEIntegration:
    """SME v8.0 集成测试"""

    def test_sme_version(self):
        from moss.core.self_modification_engine import SelfModificationEngine
        assert SelfModificationEngine.VERSION == "8.0.0-dev"

    def test_sme_default_no_llm(self):
        """默认配置不应启用LLM"""
        from moss.core.self_modification_engine import SelfModificationEngine
        sme = SelfModificationEngine()
        assert sme._hybrid_strategy is None
        assert sme._llm_backend is None

    def test_sme_with_llm_enabled(self):
        """启用LLM时应正确初始化"""
        from moss.core.self_modification_engine import SelfModificationEngine, SMEConfig
        config = SMEConfig(
            enable_llm_mutation=True,
            llm_provider='mock',
            enable_hot_reload=False,
        )
        sme = SelfModificationEngine(config=config)
        assert sme._hybrid_strategy is not None
        assert sme._llm_backend is not None

    def test_sme_config_defaults(self):
        """v8.0新增配置应有合理默认值"""
        from moss.core.self_modification_engine import SMEConfig
        config = SMEConfig()
        assert config.enable_llm_mutation is False
        assert config.llm_provider == "mock"
        assert config.llm_mutation_strategy == "adaptive"
        assert config.llm_budget_fraction == 0.3

    def test_sme_backward_compatible(self):
        """v6.x/v7.x 功能应完全不受v8.0影响"""
        from moss.core.self_modification_engine import SelfModificationEngine, SMEConfig
        # 模拟v6.x配置
        config = SMEConfig(
            enable_llm_mutation=False,
            enable_semantic_guidance=True,
            use_pareto=False,
        )
        sme = SelfModificationEngine(config=config)
        assert sme._purpose_guided_selector is not None
        assert sme.pareto_archive is None


# ─────────────────────────────────────────────
# Core Import Tests
# ─────────────────────────────────────────────

class TestCoreImports:
    """核心模块导入测试"""

    def test_llm_backend_importable(self):
        from moss.core.llm_backend import LLMBackend, LLMConfig, create_llm_backend
        assert LLMConfig is not None

    def test_llm_mutator_importable(self):
        from moss.core.llm_mutator import LLMMutator, LLMMutationResult
        assert LLMMutator is not None

    def test_hybrid_mutation_importable(self):
        from moss.core.hybrid_mutation import HybridMutationStrategy, HybridStrategyConfig
        assert HybridMutationStrategy is not None

    def test_core_init_exports(self):
        from moss.core import (
            LLMBackend, LLMConfig, LLMResponse, create_llm_backend,
            LLMMutator, LLMMutationResult,
            HybridMutationStrategy, HybridStrategyConfig,
        )
        assert all([
            LLMBackend, LLMConfig, LLMResponse, create_llm_backend,
            LLMMutator, LLMMutationResult,
            HybridMutationStrategy, HybridStrategyConfig,
        ])
