"""
MOSS Comprehensive Test Suite
=============================

Tests for the refactored MOSS core package.
Run with: pytest tests/ -v
"""

import sys
import os
import numpy as np
import pytest
from datetime import datetime

# Ensure moss package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestUnifiedAgent:
    """Test UnifiedMOSSAgent and MOSSConfig"""

    def test_config_defaults(self):
        from moss.core.unified_agent import MOSSConfig
        config = MOSSConfig()
        assert config.version == "9.5.0"
        assert config.enable_survival is True
        assert config.enable_purpose is True
        assert config.purpose_interval == 2000

    def test_state_weights_sum_to_one(self):
        """Verify that all state weights sum to 1.0 (regression test for Bug #1)"""
        from moss.core.unified_agent import UnifiedMOSSAgent, MOSSConfig
        config = MOSSConfig()
        agent = UnifiedMOSSAgent(config)

        for state in ['normal', 'crisis', 'concerned', 'growth']:
            agent.current_state = state
            agent._apply_state_weights()
            assert abs(agent.weights.sum() - 1.0) < 1e-9, \
                f"State '{state}' weights sum to {agent.weights.sum()}, expected 1.0"

    def test_concerned_state_executes(self):
        """Verify that 'concerned' state is reachable and applies correct weights (Bug #1)"""
        from moss.core.unified_agent import UnifiedMOSSAgent, MOSSConfig
        config = MOSSConfig()
        agent = UnifiedMOSSAgent(config)

        agent._update_state({'warning': True})
        assert agent.current_state == 'concerned'
        agent._apply_state_weights()
        # Concerned: Survival 35%, Curiosity 35%, Influence 20%, Optimization 10%
        np.testing.assert_allclose(agent.weights, [0.35, 0.35, 0.20, 0.10])

    def test_config_serialization(self):
        from moss.core.unified_agent import MOSSConfig
        config = MOSSConfig(agent_id="test_agent")
        d = config.to_dict()
        assert d['agent_id'] == "test_agent"
        restored = MOSSConfig.from_dict(d)
        assert restored.agent_id == "test_agent"

    def test_agent_state_enum(self):
        from moss.core.unified_agent import AgentState
        assert AgentState.INITIALIZING.value == "initializing"
        assert AgentState.RUNNING.value == "running"
        assert AgentState.TERMINATED.value == "terminated"

    def test_action_result(self):
        from moss.core.unified_agent import ActionResult
        result = ActionResult(
            action_id="test_1",
            action_type="explore",
            success=True,
            reward=0.5,
            state="normal"
        )
        assert result.success is True
        assert result.timestamp is not None
        d = result.to_dict()
        assert d['action_type'] == 'explore'

    def test_base_agent_initialization(self):
        from moss.core.unified_agent import UnifiedMOSSAgent, MOSSConfig
        config = MOSSConfig(agent_id="test_base")
        agent = UnifiedMOSSAgent(config)
        assert agent.agent_id == "test_base"
        assert agent.step_count == 0
        assert len(agent.history) == 0


class TestObjectives:
    """Test objective modules"""

    def test_base_objective_interface(self):
        from moss.core.objectives import BaseObjective, SurvivalObjective
        obj = SurvivalObjective()
        assert obj.name == "survival"
        # Should have calculate_reward and suggest_action
        reward = obj.calculate_reward({'system_health': 0.8, 'resources_available': 0.9}, 'ensure_resource_availability')
        assert isinstance(reward, float)
        action = obj.suggest_action()
        assert isinstance(action, str)

    def test_all_objectives(self):
        from moss.core.objectives import (
            SurvivalObjective, CuriosityObjective,
            InfluenceObjective, OptimizationObjective
        )
        for cls in [SurvivalObjective, CuriosityObjective, InfluenceObjective, OptimizationObjective]:
            obj = cls()
            reward = obj.calculate_reward({}, 'test')
            assert 0 <= reward <= 2.0  # Allow range with bonuses
            action = obj.suggest_action()
            assert isinstance(action, str)

    def test_objective_manager(self):
        from moss.core.objectives import ObjectiveManager
        manager = ObjectiveManager()
        rewards = manager.calculate_all_rewards(
            {'system_health': 0.5}, 'test'
        )
        assert 'survival' in rewards
        assert 'curiosity' in rewards
        assert 'influence' in rewards
        assert 'optimization' in rewards

    def test_curiosity_no_repeat_explore(self):
        from moss.core.objectives import CuriosityObjective
        obj = CuriosityObjective()
        # First visit should give bonus
        r1 = obj.calculate_reward({'pattern_id': 'A', 'new_patterns_discovered': 1, 'information_gain': 0.5}, 'explore')
        # Repeat visit should give penalty
        r2 = obj.calculate_reward({'pattern_id': 'A', 'new_patterns_discovered': 0, 'information_gain': 0.0}, 'explore')
        assert r1 > r2  # Repeat should be penalized


class TestCausalPurpose:
    """Test Causal Purpose Generator (v5.1)"""

    def test_purpose_state(self):
        from moss.core.causal_purpose import PurposeState, CausalPurposeConfig
        state = PurposeState(
            latent_vector=np.random.randn(64),
            explicit_purpose="Test purpose",
            strength=0.5,
            evolution_history=[]
        )
        d = state.to_dict()
        assert d['strength'] == 0.5
        restored = PurposeState.from_dict(d)
        assert restored.explicit_purpose == "Test purpose"

    def test_causal_purpose_generator_init(self):
        from moss.core.causal_purpose import CausalPurposeGenerator
        gen = CausalPurposeGenerator(agent_id="test_causal")
        assert gen.purpose_state.strength == 0.5
        assert gen.purpose_state.latent_vector.shape == (64,)

    def test_purpose_evolution(self):
        from moss.core.causal_purpose import CausalPurposeGenerator, CausalPurposeConfig
        config = CausalPurposeConfig(evolution_interval=10, latent_dim=64)
        gen = CausalPurposeGenerator(agent_id="test_evo", config=config)

        initial_purpose = gen.purpose_state.explicit_purpose
        initial_latent = gen.purpose_state.latent_vector.copy()

        # Run 15 steps (should trigger 1 evolution at step 10)
        for step in range(15):
            observation = {'phase': 'normal'}
            gen.step(observation, step)
            # Record feedback
            gen.record_feedback({
                'success': True,
                'reward': 0.5,
                'expected_reward': 0.3,
                'is_novel': False
            })

        assert len(gen.purpose_state.evolution_history) >= 1
        # Latent should have changed
        assert not np.allclose(initial_latent, gen.purpose_state.latent_vector)

    def test_purpose_9d_vector(self):
        from moss.core.causal_purpose import CausalPurposeGenerator
        gen = CausalPurposeGenerator(agent_id="test_9d")
        vec = gen.get_purpose_vector_9d()
        assert vec.shape == (9,)
        assert np.allclose(vec[:8].sum(), 1.0, atol=0.01)

    def test_purpose_save_load(self, tmp_path):
        from moss.core.causal_purpose import CausalPurposeGenerator
        gen = CausalPurposeGenerator(agent_id="test_save")
        save_file = str(tmp_path / "purpose_test.json")
        gen.save(save_file)
        assert os.path.exists(save_file)
        loaded = CausalPurposeGenerator.load(save_file)
        assert loaded.agent_id == "test_save"
        assert loaded.purpose_state.explicit_purpose == gen.purpose_state.explicit_purpose


class TestPurposeDynamics:
    """Test Purpose Dynamics mathematical module"""

    def test_purpose_state_dynamics(self):
        from moss.core.purpose_dynamics import PurposeState as PDState
        state = PDState(survival=0.5, curiosity=0.3, influence=0.1, optimization=0.1)
        vec = state.to_vector()
        assert vec.shape == (4,)
        # Should be normalized
        assert abs(vec.sum() - 1.0) < 0.01

    def test_dynamics_step(self):
        from moss.core.purpose_dynamics import PurposeDynamics
        dynamics = PurposeDynamics(alpha=0.01, beta=0.005, gamma=0.001, delta=0.001)
        state = {'task_completion_rate': 0.8}
        observation = {'novelty': 0.5}
        interaction = {'count': 30}
        new_state = dynamics.step(state, observation, interaction)
        assert new_state is not None

    def test_attractor_tracking(self):
        from moss.core.purpose_dynamics import PurposeDynamics
        dynamics = PurposeDynamics(alpha=0.01, beta=0.005, gamma=0.001, delta=0.001)
        # Run 100 steps
        for step in range(100):
            dynamics.step(
                {'task_completion_rate': 0.5 + 0.3 * np.sin(step / 20)},
                {'novelty': 0.5},
                {'count': 50}
            )
        basin, dist = dynamics.get_attractor_basin()
        assert basin in ['Survival', 'Curiosity', 'Balanced']
        report = dynamics.get_basin_of_attraction_report()
        assert 'attractor_stability' in report

    def test_purpose_transition_detection(self):
        from moss.core.purpose_dynamics import PurposeDynamicsTracker
        tracker = PurposeDynamicsTracker()
        stats = []
        for step in range(200):
            report = tracker.update(
                {'task_completion_rate': 0.5 + 0.4 * np.sin(step / 30)},
                {'novelty': 0.5 + 0.5 * np.cos(step / 15)},
                {'count': int(50 + 50 * np.sin(step / 10))}
            )
            stats.append(report)
        full_stats = tracker.get_statistics()
        assert 'total_transitions' in full_stats
        assert full_stats['trajectory_length'] == 201


class TestGradientSafetyGuard:
    """Test Gradient Safety Mechanism"""

    def test_normal_state(self):
        from moss.core.gradient_safety_guard import GradientSafetyGuard, SafetyLevel
        guard = GradientSafetyGuard()
        level = guard.check_metrics({'cpu_percent': 50, 'memory_percent': 40, 'error_rate': 0.01})
        assert level == SafetyLevel.NORMAL

    def test_warning_state(self):
        from moss.core.gradient_safety_guard import GradientSafetyGuard, SafetyLevel
        guard = GradientSafetyGuard()
        level = guard.check_metrics({'cpu_percent': 75, 'memory_percent': 65, 'error_rate': 0.06})
        assert level == SafetyLevel.WARNING

    def test_throttling_state(self):
        from moss.core.gradient_safety_guard import GradientSafetyGuard, SafetyLevel
        guard = GradientSafetyGuard()
        level = guard.check_metrics({'cpu_percent': 85, 'memory_percent': 75, 'error_rate': 0.12})
        assert level == SafetyLevel.THROTTLING

    def test_pause_state(self):
        from moss.core.gradient_safety_guard import GradientSafetyGuard, SafetyLevel
        guard = GradientSafetyGuard()
        level = guard.check_metrics({'cpu_percent': 95, 'memory_percent': 90, 'error_rate': 0.25})
        assert level in (SafetyLevel.PAUSE, SafetyLevel.TERMINATE)

    def test_consecutive_escalation(self):
        from moss.core.gradient_safety_guard import GradientSafetyGuard, SafetyLevel
        guard = GradientSafetyGuard()
        metrics = {'cpu_percent': 75, 'memory_percent': 65, 'error_rate': 0.06}
        for _ in range(5):
            guard.check_metrics(metrics)
        level = guard.check_metrics(metrics)
        # After consecutive violations, should escalate
        assert guard.consecutive_violations >= 3

    def test_status_report(self):
        from moss.core.gradient_safety_guard import GradientSafetyGuard
        guard = GradientSafetyGuard()
        guard.check_metrics({'cpu_percent': 75, 'memory_percent': 65, 'error_rate': 0.06})
        report = guard.get_status_report()
        assert 'current_level' in report
        assert 'total_violations_by_type' in report

    def test_terminate_raises_runtime_error(self):
        from moss.core.gradient_safety_guard import GradientSafetyGuard
        guard = GradientSafetyGuard()
        with pytest.raises(RuntimeError):
            guard.check_metrics({
                'cpu_percent': 99, 'memory_percent': 99,
                'error_rate': 0.6, 'consecutive_failures': 25
            })


class TestMathematicalFramework:
    """Test MOSS Mathematical Framework"""

    def test_unified_loss_function(self):
        from moss.core.moss_mathematical_framework import MOSSMultiObjectiveFramework
        fw = MOSSMultiObjectiveFramework()
        state = np.array([0.7, 0.02, 100])
        action = np.array([0.5, 0.3, 0.2])
        weights = np.array([0.2, 0.4, 0.3, 0.1])
        objectives = [
            lambda s, a: s[0] * (1 - s[1]),
            lambda s, a: 0.6,
            lambda s, a: 0.4,
            lambda s, a: 0.5,
        ]
        loss = fw.unified_loss_function(state, action, weights, objectives)
        assert isinstance(loss, float)
        assert loss > 0

    def test_weight_update(self):
        from moss.core.moss_mathematical_framework import MOSSMultiObjectiveFramework
        fw = MOSSMultiObjectiveFramework()
        w = np.array([0.25, 0.25, 0.25, 0.25])
        new_w = fw.dynamic_weight_update(w, np.array([0.7]))
        assert new_w.shape == (4,)
        assert np.allclose(new_w.sum(), 1.0, atol=0.01)

    def test_pareto_front(self):
        from moss.core.moss_mathematical_framework import MOSSMultiObjectiveFramework
        fw = MOSSMultiObjectiveFramework()
        pop = [np.array([0.9, 0.1]), np.array([0.8, 0.2]), np.array([0.7, 0.3])]
        front = fw.find_pareto_front(pop)
        assert len(front) >= 1
        assert len(front) <= len(pop)

    def test_convergence_analysis(self):
        from moss.core.moss_mathematical_framework import MOSSMultiObjectiveFramework
        fw = MOSSMultiObjectiveFramework()
        w = np.array([0.6, 0.1, 0.2, 0.1])
        history = [w.copy()]
        for _ in range(50):
            w = fw.dynamic_weight_update(w, np.array([0.7]), 0.05)
            history.append(w.copy())
        result = fw.analyze_convergence(history)
        assert 'converged' in result

    def test_lyapunov_stability(self):
        from moss.core.moss_mathematical_framework import MOSSMultiObjectiveFramework
        fw = MOSSMultiObjectiveFramework()
        w = np.array([0.6, 0.1, 0.2, 0.1])
        trajectory = [w.copy()]
        for _ in range(50):
            w = fw.dynamic_weight_update(w, np.array([0.7]), 0.05)
            trajectory.append(w.copy())
        result = fw.lyapunov_stability_analysis(trajectory)
        assert 'stable' in result


class TestStateDecisionModel:
    """Test State Decision Model"""

    def test_state_determination(self):
        from moss.core.state_decision_model import StateDecisionModel
        model = StateDecisionModel()

        # Crisis state - low resource, high error
        crisis_metrics = {
            'resource_quota': 0.12,
            'resource_usage': 0.88,
            'error_rate': 0.12,
            'system_uptime': 5,
            'api_call_success_rate': 0.65,
            'knowledge_growth_rate': 0.0
        }
        state, details = model.determine_state(crisis_metrics)
        assert state.value in ['crisis', 'concerned']

        # Growth state - high resource, low error
        growth_metrics = {
            'resource_quota': 0.90,
            'resource_usage': 0.25,
            'error_rate': 0.005,
            'system_uptime': 600,
            'api_call_success_rate': 0.99,
            'knowledge_growth_rate': 0.15
        }
        state, details = model.determine_state(growth_metrics)
        assert state.value in ['growth', 'normal']

    def test_weight_mapping(self):
        from moss.core.state_decision_model import StateDecisionModel
        model = StateDecisionModel()
        metrics = {
            'resource_quota': 0.5,
            'resource_usage': 0.5,
            'error_rate': 0.02,
            'system_uptime': 100,
            'api_call_success_rate': 0.96,
            'knowledge_growth_rate': 0.05
        }
        scores = model.calculate_state_score(metrics)
        assert 'crisis' in scores
        assert 'normal' in scores
        assert 'growth' in scores

    def test_validation_report(self):
        from moss.core.state_decision_model import StateDecisionModel
        model = StateDecisionModel()
        model.determine_state({
            'resource_quota': 0.5, 'resource_usage': 0.5,
            'error_rate': 0.02, 'system_uptime': 100,
            'api_call_success_rate': 0.96, 'knowledge_growth_rate': 0.05
        })
        report = model.generate_validation_report()
        assert 'total_records' in report
        assert report['total_records'] == 1


class TestDimensions:
    """Test social dimension modules (D5-D8)"""

    def test_coherence_module(self):
        from moss.core.dimensions import CoherenceModule
        mod = CoherenceModule()
        assert mod.get_score() == 1.0
        mod.update({'test': True})
        assert isinstance(mod.get_score(), float)

    def test_valence_module(self):
        from moss.core.dimensions import ValenceModule
        mod = ValenceModule()
        profile = mod.get_profile()
        assert 'beta_distribution' in profile
        assert len(profile['beta_distribution']) == 4

    def test_other_modeling(self):
        from moss.core.dimensions import OtherModelingModule
        mod = OtherModelingModule()
        mod.update_trust('agent_1', 0.8)
        assert mod.get_trust('agent_1') == 0.8
        assert mod.get_trust('unknown') == 0.5  # Default

    def test_norm_internalization(self):
        from moss.core.dimensions import NormInternalizationModule
        mod = NormInternalizationModule()
        mod.add_norm('honesty', 0.9)
        assert mod.get_norm_strength('honesty') == 0.9
        assert mod.get_norm_strength('unknown') == 0.0


class TestConflictResolver:
    """Test Conflict Resolution System"""

    def test_no_conflict(self):
        from moss.core.conflict_resolver_enhanced import (
            ConflictResolver, ObjectiveDemand, PriorityLevel
        )
        resolver = ConflictResolver()
        demands = [
            ObjectiveDemand('survival', PriorityLevel.CRITICAL, {'cpu': 0.2}, 'conserve', 0.5),
            ObjectiveDemand('curiosity', PriorityLevel.MEDIUM, {'cpu': 0.1}, 'explore', 0.3),
        ]
        conflicts = resolver.detect_conflicts({'resource_quota': 0.8}, demands)
        assert len(conflicts) == 0

    def test_resource_conflict(self):
        from moss.core.conflict_resolver_enhanced import (
            ConflictResolver, ObjectiveDemand, PriorityLevel
        )
        resolver = ConflictResolver()
        demands = [
            ObjectiveDemand('curiosity', PriorityLevel.MEDIUM, {'cpu': 0.5}, 'explore', 0.6),
            ObjectiveDemand('influence', PriorityLevel.MEDIUM, {'cpu': 0.5}, 'expand', 0.4),
        ]
        conflicts = resolver.detect_conflicts({'resource_quota': 0.3}, demands)
        assert len(conflicts) > 0

    def test_priority_resolution(self):
        from moss.core.conflict_resolver_enhanced import (
            ConflictResolver, ObjectiveDemand, PriorityLevel
        )
        resolver = ConflictResolver()
        demands = [
            ObjectiveDemand('survival', PriorityLevel.CRITICAL, {'cpu': 0.3}, 'conserve', 0.8),
            ObjectiveDemand('curiosity', PriorityLevel.MEDIUM, {'cpu': 0.4}, 'explore', 0.6),
        ]
        conflicts = resolver.detect_conflicts({'resource_quota': 0.3}, demands)
        allocations = resolver.resolve_conflicts(conflicts, demands)
        # Survival (CRITICAL) should get full allocation
        assert allocations['survival'] == 1.0

    def test_fuse_mechanism(self):
        from moss.core.conflict_resolver_enhanced import ConflictResolver
        resolver = ConflictResolver()
        resolver.blow_fuse('curiosity', cooldown_minutes=30)
        assert resolver.fuse_status['curiosity']['blown'] is True


class TestSelfOptimization:
    """Test Self-Optimization Module"""

    def test_trigger_check(self):
        from moss.core.self_optimization_v2 import SelfOptimizationModule, OptimizationTrigger
        module = SelfOptimizationModule()
        trigger = module.check_trigger({'resource_quota': 0.5})
        assert trigger == OptimizationTrigger.RESOURCE_THRESHOLD

    def test_scope_boundary(self):
        from moss.core.self_optimization_v2 import (
            SelfOptimizationModule, OptimizationScope
        )
        module = SelfOptimizationModule()
        assert module.can_optimize(OptimizationScope.WEIGHT_TUNING) is True
        assert module.can_optimize(OptimizationScope.CORE_OBJECTIVES) is False
        assert module.can_optimize(OptimizationScope.SAFETY_RULES) is False

    def test_weight_optimization(self):
        from moss.core.self_optimization_v2 import (
            SelfOptimizationModule, OptimizationScope
        )
        module = SelfOptimizationModule()
        params = {'weights': {'survival': 0.6, 'curiosity': 0.1, 'influence': 0.2, 'optimization': 0.1}}
        result = module.execute_optimization(OptimizationScope.WEIGHT_TUNING, params)
        # Weights should still sum to ~1
        total = sum(result['weights'].values())
        assert abs(total - 1.0) < 0.01

    def test_evaluation(self):
        from moss.core.self_optimization_v2 import SelfOptimizationModule
        module = SelfOptimizationModule()
        before = {'task_completion_rate': 0.7, 'resource_utilization': 0.6, 'knowledge_acquisition_rate': 0.5}
        after = {'task_completion_rate': 0.75, 'resource_utilization': 0.65, 'knowledge_acquisition_rate': 0.55}
        result = module.evaluate_optimization(before, after)
        assert result['is_positive'] is True
        assert result['recommendation'] == 'KEEP'


class TestPackageImports:
    """Test that the package can be imported correctly"""

    def test_root_import(self):
        import moss
        assert hasattr(moss, '__version__')
        assert moss.__version__ == "9.5.0"

    def test_core_import(self):
        from moss.core import UnifiedMOSSAgent, MOSSConfig
        assert UnifiedMOSSAgent is not None
        assert MOSSConfig is not None

    def test_core_exports(self):
        from moss.core import (
            GradientSafetyGuard, SafetyLevel,
            MOSSMultiObjectiveFramework,
            StateDecisionModel,
            PurposeDynamics,
            CausalPurposeGenerator,
        )
        assert all(v is not None for v in [
            GradientSafetyGuard, SafetyLevel,
            MOSSMultiObjectiveFramework,
            StateDecisionModel,
            PurposeDynamics,
            CausalPurposeGenerator,
        ])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
