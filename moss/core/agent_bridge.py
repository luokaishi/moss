"""
MOSS Agent Bridge
Agent 架构桥接模块

解决核心问题：
- autonomous_loop.py 的 LinearPolicy 与 unified_agent.py 的 9维架构是平行宇宙
- 本模块提供桥接，让两者协同工作

设计：
1. UnifiedAgentEnvironment: 将 UnifiedMOSSAgent 包装为 Environment 接口
2. UnifiedAgentPolicy: 将 UnifiedMOSSAgent 的决策逻辑包装为 Policy 接口
3. DimensionAwareLearningLoop: 在 LearningLoop 中维护 9维权重
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from moss.core.autonomous_loop import (
    Action,
    CodeEnvironment,
    Environment,
    LearningLoop,
    Observation,
    Policy,
    Reward,
)
from moss.core.unified_agent import MOSSConfig, UnifiedMOSSAgent

logger = logging.getLogger(__name__)


class UnifiedAgentEnvironment(Environment):
    """
    UnifiedMOSSAgent 的环境包装器

    将 UnifiedMOSSAgent 包装为 Environment 接口，使其能够：
    - 通过 step() 接收动作
    - 通过 reward 反馈学习信号
    - 与 LearningLoop 协同工作
    """

    def __init__(self, agent: UnifiedMOSSAgent, project_path: str = "."):
        self.agent = agent
        self.project_path = project_path
        self._step_count = 0
        self._max_steps = 100

        # 创建底层代码环境用于真实质量评估
        self._code_env = CodeEnvironment(project_path, max_steps=self._max_steps)

    def reset(self) -> Observation:
        """重置环境和 Agent"""
        self._step_count = 0

        # 重置底层环境
        code_obs = self._code_env.reset()

        # 构建观测
        obs = Observation(
            state={
                "agent_id": self.agent.config.agent_id,
                "project_path": self.project_path,
                "weights": self.agent.weights.tolist(),
                "purpose": self.agent.purpose_vector.tolist() if hasattr(self.agent, 'purpose_vector') else None,
            },
            available_actions=self.get_available_actions(),
            metrics={
                "quality": code_obs.metrics.get("quality", 0.5),
                "test_pass_rate": code_obs.metrics.get("test_pass_rate", 1.0),
            },
            info={
                "agent_state": self.agent.state.value if hasattr(self.agent, 'state') else "unknown",
            },
        )

        return obs

    def step(self, action: Action) -> Tuple[Observation, Reward, bool]:
        """执行动作，更新 Agent 状态"""
        self._step_count += 1

        # 在底层代码环境中执行对应动作
        code_action = Action(name=self._map_action(action.name))
        code_obs, code_reward, code_done = self._code_env.step(code_action)

        # 更新 Agent 的 9维权重 (如果动作是学习相关的)
        if action.name in ["learn", "adapt", "optimize"]:
            self._update_agent_weights(code_reward)

        # 构建观测
        obs = Observation(
            state={
                "agent_id": self.agent.config.agent_id,
                "step": self._step_count,
                "weights": self.agent.weights.tolist() if hasattr(self.agent, 'weights') else None,
            },
            available_actions=self.get_available_actions(),
            metrics=code_obs.metrics,
            info={
                "action_executed": action.name,
                "code_quality": code_obs.metrics.get("quality"),
            },
        )

        # 构建奖励 (结合代码环境奖励和 Agent 内部状态)
        reward = self._compute_reward(code_reward, action)

        done = code_done or self._step_count >= self._max_steps

        return obs, reward, done

    def get_available_actions(self) -> List[str]:
        """获取可用动作"""
        return ["analyze", "refactor", "test", "learn", "observe", "adapt"]

    def _map_action(self, action_name: str) -> str:
        """将 Agent 动作映射到代码环境动作"""
        mapping = {
            "adapt": "observe",
            "optimize": "refactor",
        }
        return mapping.get(action_name, action_name)

    def _update_agent_weights(self, reward: Reward) -> None:
        """根据奖励更新 Agent 权重"""
        if hasattr(self.agent, 'weights') and reward.total > 0:
            # 简单的权重调整：奖励高的维度加强
            weight_delta = np.ones(4) * reward.total * 0.01
            self.agent.weights = np.clip(self.agent.weights + weight_delta, 0.1, 0.9)
            # 重新归一化
            self.agent.weights = self.agent.weights / np.sum(self.agent.weights)

    def _compute_reward(self, code_reward: Reward, action: Action) -> Reward:
        """计算综合奖励"""
        # 基础奖励来自代码环境
        total = code_reward.total

        # 额外奖励：动作与 Agent 当前权重的匹配度
        if hasattr(self.agent, 'weights') and action.name in ["analyze", "refactor", "test", "learn"]:
            action_idx = {"analyze": 1, "refactor": 3, "test": 0, "learn": 1}.get(action.name, 0)
            weight_match = self.agent.weights[action_idx]
            total += weight_match * 0.1  # 小幅度奖励匹配

        components = dict(code_reward.components)
        components["agent_alignment"] = total - code_reward.total

        return Reward(total=total, components=components)


class UnifiedAgentPolicy(Policy):
    """
    UnifiedMOSSAgent 的策略包装器

    将 UnifiedMOSSAgent 的决策逻辑包装为 Policy 接口，使其能够：
    - 通过 select_action() 选择动作
    - 利用 Agent 的 9维权重进行决策
    - 与 LearningLoop 协同工作
    """

    def __init__(self, agent: UnifiedMOSSAgent, epsilon: float = 0.1):
        self.agent = agent
        self.epsilon = epsilon
        self._rng = np.random.RandomState(42)

    def select_action(self, observation: Observation) -> Action:
        """使用 Agent 的权重选择动作"""
        if not observation.available_actions:
            return Action(name="noop", source="policy")

        # ε-贪心探索
        if self._rng.random() < self.epsilon:
            action_name = self._rng.choice(observation.available_actions)
            return Action(name=action_name, source="exploration", confidence=0.0)

        # 利用：使用 Agent 的 9维权重评估动作
        action_scores = {}
        for action_name in observation.available_actions:
            score = self._score_action(action_name)
            action_scores[action_name] = score

        # 选择最高分动作
        best_score = max(action_scores.values())
        best_actions = [a for a, s in action_scores.items() if s == best_score]
        action_name = self._rng.choice(best_actions)

        confidence = best_score / (max(action_scores.values()) + 1e-8)
        return Action(name=action_name, source="policy", confidence=float(confidence))

    def _score_action(self, action_name: str) -> float:
        """根据 Agent 的 9维权重评分动作"""
        if not hasattr(self.agent, 'weights'):
            return 0.5

        weights = self.agent.weights

        # 动作与维度的映射
        action_dims = {
            "analyze": [1, 4],      # curiosity, coherence
            "refactor": [3, 4],     # optimization, coherence
            "test": [0, 7],         # survival, norm
            "commit": [2, 7],       # influence, norm
            "learn": [1, 3],        # curiosity, optimization
            "observe": [1, 4, 5],   # curiosity, coherence, valence
        }

        dims = action_dims.get(action_name, [0])
        score = sum(weights[d % len(weights)] for d in dims) / len(dims)

        return float(score)

    def update(self, transition: Any) -> None:
        """更新策略 (通过更新 Agent 的权重)"""
        reward = transition.reward.total
        action_name = transition.action.name

        if hasattr(self.agent, 'weights') and reward != 0:
            # 根据奖励调整权重
            action_dims = {
                "analyze": [1], "refactor": [3], "test": [0],
                "commit": [2], "learn": [1], "observe": [1],
            }

            dims = action_dims.get(action_name, [])
            for d in dims:
                if d < len(self.agent.weights):
                    # 正奖励增强对应维度，负奖励减弱
                    delta = reward * 0.01
                    self.agent.weights[d] = np.clip(
                        self.agent.weights[d] + delta, 0.05, 0.95
                    )

            # 重新归一化
            self.agent.weights = self.agent.weights / np.sum(self.agent.weights)


class IntegratedMOSSSystem:
    """
    集成 MOSS 系统

    将 UnifiedMOSSAgent + autonomous_loop 整合为统一系统：
    - Agent 使用 9维权重进行决策
    - LearningLoop 提供学习闭环
    - CodeEnvironment 提供真实奖励信号
    """

    def __init__(self, project_path: str = ".", max_steps: int = 100):
        self.project_path = project_path
        self.max_steps = max_steps

        # 创建 Agent
        config = MOSSConfig(
            agent_id="integrated_moss",
            enable_survival=True,
            enable_curiosity=True,
            enable_influence=True,
            enable_optimization=True,
            enable_coherence=True,
            enable_valence=True,
            enable_other=True,
            enable_norm=True,
            enable_purpose=True,
        )
        self.agent = UnifiedMOSSAgent(config)

        # 创建环境 (包装 Agent)
        self.env = UnifiedAgentEnvironment(self.agent, project_path)

        # 创建策略 (包装 Agent)
        self.policy = UnifiedAgentPolicy(self.agent, epsilon=0.2)

        # 创建学习循环
        self.loop = LearningLoop(
            self.env,
            self.policy,
            max_steps=max_steps,
            on_transition=self._on_transition,
        )

    def run(self) -> Dict[str, Any]:
        """运行集成系统"""
        logger.info(f"Starting IntegratedMOSSSystem on {self.project_path}")

        summary = self.loop.run()

        # 添加 Agent 状态信息
        summary["agent_state"] = {
            "agent_id": self.agent.config.agent_id,
            "final_weights": self.agent.weights.tolist() if hasattr(self.agent, 'weights') else None,
            "purpose_vector": self.agent.purpose_vector.tolist() if hasattr(self.agent, 'purpose_vector') else None,
        }

        return summary

    def _on_transition(self, transition: Any) -> None:
        """转移回调"""
        if transition.metadata.get("step", 0) % 20 == 0:
            logger.info(f"Step {transition.metadata['step']}: "
                       f"action={transition.action.name}, "
                       f"reward={transition.reward.total:.3f}")


def demo_integrated_system():
    """演示集成系统"""
    print("=" * 70)
    print("MOSS Integrated System Demo")
    print("=" * 70)
    print()

    # 创建集成系统
    system = IntegratedMOSSSystem(project_path=".", max_steps=50)

    # 运行
    summary = system.run()

    # 打印结果
    print(f"\nTotal Steps: {summary['total_steps']}")
    print(f"Total Reward: {summary['total_reward']:.3f}")
    print(f"Avg Reward: {summary['avg_reward']:.3f}")
    print(f"Action Distribution: {summary['action_distribution']}")

    if summary.get('agent_state', {}).get('final_weights'):
        print(f"\nFinal Agent Weights: {summary['agent_state']['final_weights']}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo_integrated_system()
