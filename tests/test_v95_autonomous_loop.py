"""
Tests for Autonomous Agent Loop
自主 Agent 循环测试
"""

import numpy as np
import pytest
from unittest.mock import Mock

from moss.core.autonomous_loop import (
    Observation,
    Action,
    Reward,
    Transition,
    AgentPhase,
    Environment,
    Policy,
    RandomPolicy,
    EpsilonGreedyPolicy,
    LinearPolicy,
    CodeEnvironment,
    LearningLoop,
    ExperimentRunner,
)


# ═══════════════════════════════════════════════════════════
# Test Core Types
# ═══════════════════════════════════════════════════════════

class TestObservation:
    def test_creation(self):
        obs = Observation(
            state={"x": 1},
            available_actions=["a", "b"],
            metrics={"quality": 0.8},
        )
        assert obs.state["x"] == 1
        assert len(obs.available_actions) == 2
        assert obs.metrics["quality"] == 0.8

    def test_default_fields(self):
        obs = Observation(state={}, available_actions=[])
        assert obs.metrics == {}
        assert obs.info == {}
        assert obs.timestamp > 0


class TestAction:
    def test_creation(self):
        action = Action(name="test", params={"key": "val"})
        assert action.name == "test"
        assert action.params["key"] == "val"
        assert action.source == "policy"
        assert action.confidence == 1.0

    def test_str(self):
        action = Action(name="refactor")
        assert str(action) == "refactor"

    def test_str_with_params(self):
        action = Action(name="refactor", params={"file": "test.py"})
        assert "refactor" in str(action)
        assert "test.py" in str(action)


class TestReward:
    def test_total(self):
        reward = Reward(total=1.5, components={"a": 0.5, "b": 1.0})
        assert reward.total == 1.5
        assert reward.signed_total == 1.5

    def test_negative_reward(self):
        reward = Reward(total=-0.5, components={"penalty": -0.5})
        assert reward.signed_total == -0.5

    def test_default_fields(self):
        reward = Reward(total=0.0)
        assert reward.components == {}
        assert reward.sparse is False


class TestTransition:
    def test_creation(self):
        obs = Observation(state={}, available_actions=["a"])
        action = Action(name="a")
        reward = Reward(total=1.0)
        next_obs = Observation(state={}, available_actions=["b"])

        t = Transition(observation=obs, action=action, reward=reward,
                      next_observation=next_obs)
        assert t.done is False
        assert t.metadata == {}


# ═══════════════════════════════════════════════════════════
# Test Policies
# ═══════════════════════════════════════════════════════════

class TestRandomPolicy:
    def test_select_action(self):
        policy = RandomPolicy(seed=42)
        obs = Observation(state={}, available_actions=["a", "b", "c"])
        action = policy.select_action(obs)
        assert action.name in ["a", "b", "c"]
        assert action.source == "exploration"

    def test_empty_actions(self):
        policy = RandomPolicy()
        obs = Observation(state={}, available_actions=[])
        action = policy.select_action(obs)
        assert action.name == "noop"

    def test_no_learning(self):
        policy = RandomPolicy()
        obs = Observation(state={}, available_actions=["a"])
        action = Action(name="a")
        reward = Reward(total=1.0)
        next_obs = Observation(state={}, available_actions=["a"])

        policy.update(Transition(obs, action, reward, next_obs))
        # RandomPolicy should not change


class TestEpsilonGreedyPolicy:
    def test_select_action_explore(self):
        # High epsilon = mostly explore
        policy = EpsilonGreedyPolicy(epsilon=1.0, seed=42)
        obs = Observation(state={}, available_actions=["a", "b"])
        action = policy.select_action(obs)
        assert action.name in ["a", "b"]

    def test_select_action_exploit(self):
        # Zero epsilon = always exploit
        policy = EpsilonGreedyPolicy(epsilon=0.0, seed=42)
        obs = Observation(state={}, available_actions=["a", "b"])

        # Pre-populate Q-values
        policy._q_values = {"a": 1.0, "b": 0.5}

        action = policy.select_action(obs)
        assert action.name == "a"

    def test_update_q_values(self):
        policy = EpsilonGreedyPolicy(epsilon=0.0)
        obs = Observation(state={}, available_actions=["a"])
        action = Action(name="a")
        reward = Reward(total=1.0)
        next_obs = Observation(state={}, available_actions=["a"])

        policy.update(Transition(obs, action, reward, next_obs))
        assert policy._q_values["a"] == 1.0
        assert policy._action_counts["a"] == 1

    def test_epsilon_decay(self):
        policy = EpsilonGreedyPolicy(epsilon=0.5, decay=0.9, min_epsilon=0.01)
        obs = Observation(state={}, available_actions=["a"])
        action = Action(name="a")
        reward = Reward(total=1.0)
        next_obs = Observation(state={}, available_actions=["a"])

        initial_epsilon = policy.epsilon
        policy.update(Transition(obs, action, reward, next_obs))
        assert policy.epsilon < initial_epsilon

    def test_epsilon_min(self):
        policy = EpsilonGreedyPolicy(epsilon=0.5, decay=0.5, min_epsilon=0.1)
        obs = Observation(state={}, available_actions=["a"])
        action = Action(name="a")
        reward = Reward(total=1.0)
        next_obs = Observation(state={}, available_actions=["a"])

        for _ in range(20):
            policy.update(Transition(obs, action, reward, next_obs))

        assert policy.epsilon >= 0.1


class TestLinearPolicy:
    def test_default_weights(self):
        policy = LinearPolicy()
        assert len(policy.weights) == 9
        assert abs(np.sum(policy.weights) - 1.0) < 0.01

    def test_register_action_features(self):
        policy = LinearPolicy()
        features = np.array([0.1, 0.2, 0.1, 0.3, 0.1, 0.05, 0.05, 0.05, 0.05])
        policy.register_action_features("test_action", features)
        assert "test_action" in policy._action_features

    def test_select_with_features(self):
        policy = LinearPolicy(seed=42)
        policy._epsilon = 0.0
        # Weight curiosity and optimization high
        policy.weights = np.array([0.05, 0.3, 0.05, 0.3, 0.05, 0.05, 0.05, 0.05, 0.1])

        policy.register_action_features("analyze", np.array([0.1, 0.3, 0.1, 0.4, 0.05, 0.05, 0.0, 0.0, 0.0]))
        policy.register_action_features("observe", np.array([0.1, 0.4, 0.0, 0.1, 0.2, 0.1, 0.1, 0.0, 0.0]))

        obs = Observation(state={}, available_actions=["analyze", "observe"])
        action = policy.select_action(obs)
        assert action.name in ["analyze", "observe"]

    def test_update_weights(self):
        policy = LinearPolicy(learning_rate=0.01)
        policy.register_action_features("test", np.array([0.1, 0.2, 0.1, 0.3, 0.1, 0.05, 0.05, 0.05, 0.05]))

        obs = Observation(state={}, available_actions=["test"])
        action = Action(name="test")
        reward = Reward(total=1.0)
        next_obs = Observation(state={}, available_actions=["test"])

        old_weights = policy.weights.copy()
        policy.update(Transition(obs, action, reward, next_obs))
        # Weights should have changed
        assert not np.allclose(old_weights, policy.weights)

    def test_invalid_feature_dim(self):
        policy = LinearPolicy()
        with pytest.raises(AssertionError):
            policy.register_action_features("bad", np.array([0.1, 0.2]))


# ═══════════════════════════════════════════════════════════
# Test Code Environment
# ═══════════════════════════════════════════════════════════

class TestCodeEnvironment:
    def test_reset(self):
        env = CodeEnvironment(project_path=".", max_steps=10)
        obs = env.reset()
        assert obs.state["step"] == 0
        assert len(obs.available_actions) > 0
        assert "quality" in obs.metrics

    def test_step(self):
        env = CodeEnvironment(project_path=".", max_steps=10)
        env.reset()

        action = Action(name="analyze")
        obs, reward, done = env.step(action)

        assert reward.total != 0 or len(reward.components) > 0
        assert obs.state["step"] == 1

    def test_max_steps(self):
        env = CodeEnvironment(project_path=".", max_steps=3)
        env.reset()

        for _ in range(3):
            _, _, done = env.step(Action(name="observe"))

        assert done is True

    def test_all_actions(self):
        env = CodeEnvironment(project_path=".", max_steps=20)
        env.reset()

        for action_name in env.get_available_actions():
            action = Action(name=action_name)
            obs, reward, done = env.step(action)
            assert isinstance(reward, Reward)

    def test_reward_components(self):
        env = CodeEnvironment(project_path=".", max_steps=10)
        env.reset()

        action = Action(name="analyze")
        _, reward, _ = env.step(action)
        assert "knowledge_gain" in reward.components or "curiosity" in reward.components

    def test_get_available_actions(self):
        env = CodeEnvironment(project_path=".")
        actions = env.get_available_actions()
        assert "analyze" in actions
        assert "refactor" in actions
        assert "test" in actions


# ═══════════════════════════════════════════════════════════
# Test Learning Loop
# ═══════════════════════════════════════════════════════════

class TestLearningLoop:
    def test_run(self):
        env = CodeEnvironment(project_path=".", max_steps=10)
        policy = EpsilonGreedyPolicy(epsilon=0.2, seed=42)
        loop = LearningLoop(env, policy, max_steps=10)

        summary = loop.run()
        assert summary["total_steps"] == 10
        assert summary["total_reward"] != 0
        assert len(summary["action_distribution"]) > 0

    def test_callback(self):
        transitions = []
        def on_transition(t):
            transitions.append(t)

        env = CodeEnvironment(project_path=".", max_steps=5)
        policy = RandomPolicy(seed=42)
        loop = LearningLoop(env, policy, max_steps=5, on_transition=on_transition)

        loop.run()
        assert len(transitions) == 5

    def test_stop(self):
        env = CodeEnvironment(project_path=".", max_steps=100)
        policy = RandomPolicy(seed=42)
        loop = LearningLoop(env, policy, max_steps=100)

        # Run and verify it completes
        summary = loop.run()
        assert summary["total_steps"] == 100

    def test_reflect(self):
        env = CodeEnvironment(project_path=".", max_steps=25)
        policy = EpsilonGreedyPolicy(epsilon=0.2, seed=42)
        loop = LearningLoop(env, policy, max_steps=25)

        summary = loop.run()
        # Should have reflected at steps 10 and 20
        assert summary["total_steps"] == 25


# ═══════════════════════════════════════════════════════════
# Test Experiment Runner
# ═══════════════════════════════════════════════════════════

class TestExperimentRunner:
    def test_run_single(self):
        runner = ExperimentRunner(seed=42)
        env = CodeEnvironment(project_path=".", max_steps=10)
        policy = RandomPolicy(seed=42)

        summary = runner.run_single(env, policy, max_steps=10)
        assert summary["total_steps"] == 10
        assert "total_reward" in summary

    def test_run_repeated(self):
        runner = ExperimentRunner(seed=42)

        results = runner.run_repeated(
            env_factory=lambda: CodeEnvironment(".", max_steps=10),
            policy_factory=lambda: RandomPolicy(seed=42),
            n_runs=5,
            max_steps=10,
        )

        assert results["n_runs"] == 5
        assert len(results["total_rewards"]) == 5
        assert results["mean_reward"] != 0

    def test_run_ab_test(self):
        runner = ExperimentRunner(seed=42)

        results = runner.run_ab_test(
            env_factory=lambda: CodeEnvironment(".", max_steps=10),
            policy_a_factory=lambda: EpsilonGreedyPolicy(epsilon=0.2, seed=42),
            policy_b_factory=lambda: RandomPolicy(seed=42),
            n_runs=10,
            max_steps=10,
        )

        assert "policy_a" in results
        assert "policy_b" in results
        assert "validation" in results
        assert "comparison" in results["validation"]


# ═══════════════════════════════════════════════════════════
# Test Agent Phase
# ═══════════════════════════════════════════════════════════

class TestAgentPhase:
    def test_phases(self):
        assert AgentPhase.OBSERVE.value == "observe"
        assert AgentPhase.DECIDE.value == "decide"
        assert AgentPhase.ACT.value == "act"
        assert AgentPhase.LEARN.value == "learn"
        assert AgentPhase.REFLECT.value == "reflect"
