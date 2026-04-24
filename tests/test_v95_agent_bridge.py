"""
Tests for Agent Bridge
Agent 架构桥接测试
"""

import numpy as np
import pytest

from moss.core.agent_bridge import (
    UnifiedAgentEnvironment,
    UnifiedAgentPolicy,
    IntegratedMOSSSystem,
)
from moss.core.autonomous_loop import Action, Observation, Reward
from moss.core.unified_agent import MOSSConfig, UnifiedMOSSAgent


class TestUnifiedAgentEnvironment:
    """测试 UnifiedAgentEnvironment"""

    def test_creation(self):
        config = MOSSConfig()
        agent = UnifiedMOSSAgent(config)
        env = UnifiedAgentEnvironment(agent, project_path=".")

        assert env.agent == agent
        assert env.project_path == "."

    def test_reset(self):
        config = MOSSConfig()
        agent = UnifiedMOSSAgent(config)
        env = UnifiedAgentEnvironment(agent, project_path=".")

        obs = env.reset()

        assert isinstance(obs, Observation)
        assert obs.state["agent_id"] == config.agent_id
        assert len(obs.available_actions) > 0
        assert "quality" in obs.metrics

    def test_step(self):
        config = MOSSConfig()
        agent = UnifiedMOSSAgent(config)
        env = UnifiedAgentEnvironment(agent, project_path=".")

        env.reset()
        action = Action(name="analyze")
        obs, reward, done = env.step(action)

        assert isinstance(obs, Observation)
        assert isinstance(reward, Reward)
        assert isinstance(done, bool)
        assert obs.state["step"] == 1

    def test_action_mapping(self):
        config = MOSSConfig()
        agent = UnifiedMOSSAgent(config)
        env = UnifiedAgentEnvironment(agent, project_path=".")

        # 测试动作映射
        assert env._map_action("adapt") == "observe"
        assert env._map_action("optimize") == "refactor"
        assert env._map_action("analyze") == "analyze"

    def test_reward_computation(self):
        config = MOSSConfig()
        agent = UnifiedMOSSAgent(config)
        env = UnifiedAgentEnvironment(agent, project_path=".")

        code_reward = Reward(total=0.5, components={"quality": 0.5})
        action = Action(name="analyze")

        reward = env._compute_reward(code_reward, action)

        assert reward.total >= code_reward.total  # 可能有额外奖励
        assert "agent_alignment" in reward.components


class TestUnifiedAgentPolicy:
    """测试 UnifiedAgentPolicy"""

    def test_creation(self):
        config = MOSSConfig()
        agent = UnifiedMOSSAgent(config)
        policy = UnifiedAgentPolicy(agent, epsilon=0.1)

        assert policy.agent == agent
        assert policy.epsilon == 0.1

    def test_select_action(self):
        config = MOSSConfig()
        agent = UnifiedMOSSAgent(config)
        policy = UnifiedAgentPolicy(agent, epsilon=0.0)  # 无探索

        obs = Observation(
            state={},
            available_actions=["analyze", "refactor", "test"],
        )

        action = policy.select_action(obs)

        assert action.name in ["analyze", "refactor", "test"]
        assert action.source == "policy"

    def test_action_scoring(self):
        config = MOSSConfig()
        agent = UnifiedMOSSAgent(config)
        policy = UnifiedAgentPolicy(agent)

        # 测试动作评分
        score_analyze = policy._score_action("analyze")
        score_refactor = policy._score_action("refactor")
        score_test = policy._score_action("test")

        assert 0 <= score_analyze <= 1
        assert 0 <= score_refactor <= 1
        assert 0 <= score_test <= 1

    def test_update(self):
        config = MOSSConfig()
        agent = UnifiedMOSSAgent(config)
        policy = UnifiedAgentPolicy(agent)

        # 记录初始权重
        initial_weights = agent.weights.copy()

        # 创建转移
        obs = Observation(state={}, available_actions=["analyze"])
        action = Action(name="analyze")
        reward = Reward(total=1.0)
        next_obs = Observation(state={}, available_actions=["analyze"])

        from moss.core.autonomous_loop import Transition
        transition = Transition(obs, action, reward, next_obs)

        # 更新策略
        policy.update(transition)

        # 权重应该有所变化
        assert not np.allclose(agent.weights, initial_weights)


class TestIntegratedMOSSSystem:
    """测试集成系统"""

    def test_creation(self):
        system = IntegratedMOSSSystem(project_path=".", max_steps=10)

        assert system.project_path == "."
        assert system.max_steps == 10
        assert system.agent is not None
        assert system.env is not None
        assert system.policy is not None
        assert system.loop is not None

    def test_run(self):
        system = IntegratedMOSSSystem(project_path=".", max_steps=5)

        summary = system.run()

        assert summary["total_steps"] == 5
        assert "total_reward" in summary
        assert "action_distribution" in summary
        assert "agent_state" in summary

    def test_agent_state_in_summary(self):
        system = IntegratedMOSSSystem(project_path=".", max_steps=3)

        summary = system.run()

        agent_state = summary.get("agent_state", {})
        assert "agent_id" in agent_state
        assert "final_weights" in agent_state


class TestNineDimensionIntegration:
    """测试9维集成"""

    def test_nine_dim_weights_shape(self):
        config = MOSSConfig()
        agent = UnifiedMOSSAgent(config)

        # 初始化扩展维度
        agent.dimensions['coherence'] = type('obj', (object,), {'current_weight': 0.1})()
        agent.dimensions['valence'] = type('obj', (object,), {'current_weight': 0.1})()
        agent.dimensions['other'] = type('obj', (object,), {'current_weight': 0.1})()
        agent.dimensions['norm'] = type('obj', (object,), {'current_weight': 0.1})()

        weights = agent._get_nine_dim_weights()

        assert len(weights) == 9
        assert abs(np.sum(weights) - 1.0) < 0.01  # 归一化

    def test_extended_dimensions_update(self):
        config = MOSSConfig()
        agent = UnifiedMOSSAgent(config)
        agent.action_history = ['analyze', 'refactor', 'analyze', 'test']

        # 创建模拟维度
        class MockDim:
            def __init__(self):
                self.state = {}
            def update_state(self, state):
                self.state.update(state)

        agent.dimensions['coherence'] = MockDim()
        agent.dimensions['valence'] = MockDim()
        agent.dimensions['other'] = MockDim()
        agent.dimensions['norm'] = MockDim()

        agent._update_extended_dimensions({})

        # 验证维度被更新
        assert 'consistency' in agent.dimensions['coherence'].state

    def test_select_action_uses_nine_dim(self):
        config = MOSSConfig()
        agent = UnifiedMOSSAgent(config)

        # 创建模拟维度
        class MockDim:
            def suggest_action(self):
                return 'test_action'
            def update_state(self, state):
                pass

        for dim_name in ['survival', 'curiosity', 'influence', 'optimization',
                        'coherence', 'valence', 'other', 'norm', 'purpose']:
            agent.dimensions[dim_name] = MockDim()

        observation = {'metrics': {'quality': 0.8}}
        action = agent.select_action(observation)

        assert action is not None
