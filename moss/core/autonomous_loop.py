"""
MOSS v9.5.0 - Autonomous Agent Loop
自主 Agent 循环 - 让 MOSS 真正自驱动

核心改进：
1. 真实环境接口 (Environment) - Agent 通过 Environment 获取观测、执行动作、接收奖励
2. 可扩展动作空间 (ActionSpace) - 不再是硬编码的4个动作，而是环境驱动
3. 学习循环 (LearningLoop) - 闭环反馈：观测→决策→执行→奖励→学习→改进
4. 策略接口 (Policy) - 可插拔决策策略 (epsilon-greedy, Thompson sampling, etc.)

设计原则：
- Agent 不直接操作环境，通过 Environment 接口
- 奖励信号由 Environment 提供，不是随机生成
- 策略可替换，支持从简单到复杂的学习算法
- 保持与现有 9 维架构的兼容性
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Core Types
# ═══════════════════════════════════════════════════════════

@dataclass
class Observation:
    """环境观测"""
    state: Dict[str, Any]  # 环境状态
    available_actions: List[str]  # 可用动作
    metrics: Dict[str, float] = field(default_factory=dict)  # 性能指标
    info: Dict[str, Any] = field(default_factory=dict)  # 额外信息
    timestamp: float = field(default_factory=time.time)


@dataclass
class Action:
    """Agent 动作"""
    name: str
    params: Dict[str, Any] = field(default_factory=dict)
    source: str = "policy"  # policy / exploration / override
    confidence: float = 1.0  # 动作置信度 [0, 1]

    def __str__(self) -> str:
        if self.params:
            return f"{self.name}({self.params})"
        return self.name


@dataclass
class Reward:
    """奖励信号"""
    total: float  # 总奖励
    components: Dict[str, float] = field(default_factory=dict)  # 分维度奖励
    sparse: bool = False  # 是否稀疏奖励
    info: Dict[str, Any] = field(default_factory=dict)  # 奖励解释

    @property
    def signed_total(self) -> float:
        return self.total


@dataclass
class Transition:
    """状态转移 (s, a, r, s')"""
    observation: Observation
    action: Action
    reward: Reward
    next_observation: Observation
    done: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentPhase(Enum):
    """Agent 运行阶段"""
    OBSERVE = "observe"     # 观测环境
    DECIDE = "decide"       # 决策
    ACT = "act"             # 执行动作
    LEARN = "learn"         # 学习更新
    REFLECT = "reflect"     # 反思 (D5-D8 维度)


# ═══════════════════════════════════════════════════════════
# Environment Interface
# ═══════════════════════════════════════════════════════════

class Environment(ABC):
    """
    环境接口

    Agent 通过 Environment 与外部世界交互。
    这是 MOSS 从"随机模拟"走向"真实自驱动"的关键抽象。
    """

    @abstractmethod
    def reset(self) -> Observation:
        """重置环境，返回初始观测"""
        ...

    @abstractmethod
    def step(self, action: Action) -> Tuple[Observation, Reward, bool]:
        """
        执行动作，返回 (next_observation, reward, done)

        这是 Agent 与环境交互的核心方法。
        奖励由环境计算，不是随机生成。
        """
        ...

    @abstractmethod
    def get_available_actions(self) -> List[str]:
        """获取当前可用动作列表"""
        ...

    def render(self) -> Optional[str]:
        """渲染当前状态 (可选)"""
        return None

    def close(self) -> None:
        """关闭环境"""
        pass


# ═══════════════════════════════════════════════════════════
# Policy Interface
# ═══════════════════════════════════════════════════════════

class Policy(ABC):
    """
    策略接口

    可插拔的决策策略，支持从简单到复杂：
    - RandomPolicy: 随机探索
    - EpsilonGreedyPolicy: ε-贪心
    - ThompsonSamplingPolicy: Thompson 采样
    - LinearPolicy: 线性权重策略 (与9维架构兼容)
    """

    @abstractmethod
    def select_action(self, observation: Observation) -> Action:
        """根据观测选择动作"""
        ...

    @abstractmethod
    def update(self, transition: Transition) -> None:
        """根据转移更新策略"""
        ...

    def reset(self) -> None:
        """重置策略状态"""
        pass


class RandomPolicy(Policy):
    """随机策略 - 基线对比用"""

    def __init__(self, seed: Optional[int] = None):
        self._rng = np.random.RandomState(seed)

    def select_action(self, observation: Observation) -> Action:
        if not observation.available_actions:
            return Action(name="noop", source="policy")
        action_name = self._rng.choice(observation.available_actions)
        return Action(name=action_name, source="exploration", confidence=0.0)

    def update(self, transition: Transition) -> None:
        pass  # 随机策略不学习


class EpsilonGreedyPolicy(Policy):
    """ε-贪心策略"""

    def __init__(self, epsilon: float = 0.1, decay: float = 0.999,
                 min_epsilon: float = 0.01, seed: Optional[int] = None):
        self.epsilon = epsilon
        self.decay = decay
        self.min_epsilon = min_epsilon
        self._rng = np.random.RandomState(seed)
        self._q_values: Dict[str, float] = {}
        self._action_counts: Dict[str, int] = {}

    def select_action(self, observation: Observation) -> Action:
        if not observation.available_actions:
            return Action(name="noop", source="policy")

        # 探索
        if self._rng.random() < self.epsilon:
            action_name = self._rng.choice(observation.available_actions)
            return Action(name=action_name, source="exploration", confidence=0.0)

        # 利用
        q_vals = {a: self._q_values.get(a, 0.0) for a in observation.available_actions}
        best_value = max(q_vals.values())
        best_actions = [a for a, v in q_vals.items() if v == best_value]
        action_name = self._rng.choice(best_actions)
        confidence = (best_value - min(q_vals.values())) / (max(q_vals.values()) - min(q_vals.values()) + 1e-8)

        return Action(name=action_name, source="policy", confidence=float(confidence))

    def update(self, transition: Transition) -> None:
        action_name = transition.action.name
        reward = transition.reward.total

        # 简单增量更新
        count = self._action_counts.get(action_name, 0) + 1
        old_q = self._q_values.get(action_name, 0.0)
        self._q_values[action_name] = old_q + (reward - old_q) / count
        self._action_counts[action_name] = count

        # 衰减 epsilon
        self.epsilon = max(self.min_epsilon, self.epsilon * self.decay)


class LinearPolicy(Policy):
    """
    线性权重策略 - 与9维架构兼容

    使用9维目标权重向量选择动作：
    - 每个动作有一个9维特征向量
    - 决策时计算加权和
    - 支持状态依赖的权重调整 (crisis/concerned/normal/growth)
    """

    DIMENSION_NAMES = [
        "survival", "curiosity", "influence", "optimization",
        "coherence", "valence", "other_modeling", "norm",
        "purpose"
    ]

    def __init__(self, weights: Optional[np.ndarray] = None,
                 learning_rate: float = 0.01,
                 seed: Optional[int] = None):
        if weights is not None:
            self.weights = np.array(weights, dtype=float)
        else:
            # 默认权重：9维均衡
            self.weights = np.ones(9) / 9.0

        self.learning_rate = learning_rate
        self._rng = np.random.RandomState(seed)
        self._action_features: Dict[str, np.ndarray] = {}
        self._epsilon = 0.1

    def register_action_features(self, action_name: str, features: np.ndarray) -> None:
        """注册动作的9维特征向量"""
        assert len(features) == 9, f"Expected 9-dim features, got {len(features)}"
        self._action_features[action_name] = np.array(features, dtype=float)

    def select_action(self, observation: Observation) -> Action:
        if not observation.available_actions:
            return Action(name="noop", source="policy")

        # 探索
        if self._rng.random() < self._epsilon:
            action_name = self._rng.choice(observation.available_actions)
            return Action(name=action_name, source="exploration", confidence=0.0)

        # 利用：计算加权和
        scores = {}
        for action_name in observation.available_actions:
            features = self._action_features.get(action_name)
            if features is not None:
                scores[action_name] = float(np.dot(self.weights, features))
            else:
                # 未知动作：使用观测指标估计
                if observation.metrics:
                    scores[action_name] = float(np.mean(list(observation.metrics.values())))
                else:
                    scores[action_name] = 0.0

        best_score = max(scores.values())
        best_actions = [a for a, s in scores.items() if s == best_score]
        action_name = self._rng.choice(best_actions)

        confidence = best_score / (abs(best_score) + 1.0)
        return Action(name=action_name, source="policy", confidence=float(confidence))

    def update(self, transition: Transition) -> None:
        """更新权重 - 简单的梯度上升"""
        action_name = transition.action.name
        reward = transition.reward.total
        features = self._action_features.get(action_name)

        if features is not None:
            # 沿奖励方向更新权重
            gradient = features * reward * self.learning_rate
            self.weights = self.weights + gradient
            # 归一化
            weight_sum = np.sum(np.abs(self.weights))
            if weight_sum > 0:
                self.weights = self.weights / weight_sum


# ═══════════════════════════════════════════════════════════
# Code Environment (MOSS 的核心环境)
# ═══════════════════════════════════════════════════════════

class CodeEnvironment(Environment):
    """
    代码环境 - MOSS 的核心交互环境

    Agent 在代码库上执行操作：
    - 分析代码质量
    - 执行重构
    - 运行测试
    - 提交变更

    奖励基于：
    - 代码质量改善 (分析得分变化)
    - 测试通过率
    - 重构安全性
    - 目标达成度
    """

    def __init__(self, project_path: str, max_steps: int = 100):
        self.project_path = project_path
        self.max_steps = max_steps
        self._step_count = 0
        self._initial_quality: Optional[float] = None
        self._current_quality: Optional[float] = None
        self._test_pass_rate: float = 1.0
        self._safety_violations: int = 0

        # 动作定义
        self._action_definitions = {
            "analyze": {
                "description": "分析代码质量",
                "features": np.array([0.1, 0.3, 0.1, 0.4, 0.05, 0.05, 0.0, 0.0, 0.0]),
            },
            "refactor": {
                "description": "执行重构",
                "features": np.array([0.05, 0.2, 0.1, 0.5, 0.05, 0.05, 0.0, 0.0, 0.05]),
            },
            "test": {
                "description": "运行测试",
                "features": np.array([0.4, 0.1, 0.0, 0.3, 0.1, 0.0, 0.0, 0.1, 0.0]),
            },
            "commit": {
                "description": "提交变更",
                "features": np.array([0.2, 0.0, 0.3, 0.1, 0.1, 0.1, 0.0, 0.2, 0.0]),
            },
            "learn": {
                "description": "学习改进策略",
                "features": np.array([0.0, 0.5, 0.0, 0.2, 0.1, 0.1, 0.0, 0.0, 0.1]),
            },
            "observe": {
                "description": "观察环境状态",
                "features": np.array([0.1, 0.4, 0.0, 0.1, 0.2, 0.1, 0.1, 0.0, 0.0]),
            },
        }

    def reset(self) -> Observation:
        """重置环境"""
        self._step_count = 0
        self._initial_quality = self._estimate_quality()
        self._current_quality = self._initial_quality

        return Observation(
            state={
                "project_path": self.project_path,
                "initial_quality": self._initial_quality,
                "step": 0,
            },
            available_actions=self.get_available_actions(),
            metrics={
                "quality": self._current_quality,
                "test_pass_rate": self._test_pass_rate,
                "safety_violations": 0,
            },
        )

    def step(self, action: Action) -> Tuple[Observation, Reward, bool]:
        """执行动作"""
        self._step_count += 1

        # 执行动作并计算奖励
        reward = self._execute_and_reward(action)

        # 更新环境状态
        self._current_quality = self._estimate_quality()
        done = self._step_count >= self.max_steps

        obs = Observation(
            state={
                "project_path": self.project_path,
                "initial_quality": self._initial_quality,
                "current_quality": self._current_quality,
                "quality_delta": (self._current_quality - self._initial_quality)
                    if self._initial_quality else 0,
                "step": self._step_count,
                "last_action": action.name,
            },
            available_actions=self.get_available_actions(),
            metrics={
                "quality": self._current_quality,
                "test_pass_rate": self._test_pass_rate,
                "safety_violations": self._safety_violations,
                "step": self._step_count,
            },
        )

        return obs, reward, done

    def get_available_actions(self) -> List[str]:
        return list(self._action_definitions.keys())

    def _execute_and_reward(self, action: Action) -> Reward:
        """执行动作并计算奖励"""
        components = {}

        if action.name == "analyze":
            components["knowledge_gain"] = 0.1
            components["curiosity"] = 0.2
        elif action.name == "refactor":
            quality_before = self._current_quality or 0.5
            quality_delta = np.random.normal(0.05, 0.1)  # 模拟质量变化
            components["quality_delta"] = quality_delta
            components["optimization"] = max(0, quality_delta)
            if quality_delta < 0:
                components["safety_penalty"] = -0.1
        elif action.name == "test":
            components["survival"] = 0.1
            components["confidence"] = 0.15
        elif action.name == "commit":
            components["influence"] = 0.1
            components["norm"] = 0.1
        elif action.name == "learn":
            components["curiosity"] = 0.3
            components["optimization"] = 0.1
        elif action.name == "observe":
            components["coherence"] = 0.15
            components["curiosity"] = 0.1
        else:
            components["unknown"] = 0.0

        total = sum(components.values())
        return Reward(total=total, components=components)

    def _estimate_quality(self) -> float:
        """估算代码质量 (简化版)"""
        # 实际实现应调用 IncrementalAnalyzer
        return 0.5 + np.random.normal(0, 0.05)


# ═══════════════════════════════════════════════════════════
# Learning Loop
# ═══════════════════════════════════════════════════════════

class LearningLoop:
    """
    自主学习循环

    闭环反馈: 观测 → 决策 → 执行 → 奖励 → 学习 → 改进

    这是 MOSS 从"工具"走向"自驱动系统"的核心引擎。
    """

    def __init__(self,
                 environment: Environment,
                 policy: Policy,
                 max_steps: int = 100,
                 checkpoint_interval: int = 10,
                 on_transition: Optional[Callable[[Transition], None]] = None):
        self.env = environment
        self.policy = policy
        self.max_steps = max_steps
        self.checkpoint_interval = checkpoint_interval
        self.on_transition = on_transition

        self._history: List[Transition] = []
        self._total_reward: float = 0.0
        self._step_count: int = 0
        self._phase: AgentPhase = AgentPhase.OBSERVE
        self._running: bool = False

    @property
    def total_reward(self) -> float:
        return self._total_reward

    @property
    def step_count(self) -> int:
        return self._step_count

    @property
    def history(self) -> List[Transition]:
        return self._history

    @property
    def phase(self) -> AgentPhase:
        return self._phase

    def run(self) -> Dict[str, Any]:
        """运行完整学习循环"""
        self._running = True

        # 重置环境
        obs = self.env.reset()
        done = False

        while not done and self._step_count < self.max_steps:
            # 1. 观测阶段
            self._phase = AgentPhase.OBSERVE

            # 2. 决策阶段
            self._phase = AgentPhase.DECIDE
            action = self.policy.select_action(obs)

            # 3. 执行阶段
            self._phase = AgentPhase.ACT
            next_obs, reward, done = self.env.step(action)

            # 创建转移
            transition = Transition(
                observation=obs,
                action=action,
                reward=reward,
                next_observation=next_obs,
                done=done,
                metadata={
                    "step": self._step_count,
                    "phase": self._phase.value,
                },
            )

            # 回调
            if self.on_transition:
                self.on_transition(transition)

            # 4. 学习阶段
            self._phase = AgentPhase.LEARN
            self.policy.update(transition)

            # 记录
            self._history.append(transition)
            self._total_reward += reward.total
            self._step_count += 1

            # 5. 反思阶段 (每10步)
            if self._step_count % 10 == 0:
                self._phase = AgentPhase.REFLECT
                self._reflect()

            # 进入下一步
            obs = next_obs

        self._running = False

        return self._generate_summary()

    def stop(self) -> None:
        """停止循环"""
        self._running = False

    def _reflect(self) -> None:
        """反思 - 分析历史表现并调整"""
        if len(self._history) < 5:
            return

        # 计算最近5步的平均奖励
        recent = self._history[-5:]
        avg_reward = np.mean([t.reward.total for t in recent])

        # 计算动作分布
        action_counts: Dict[str, int] = {}
        for t in recent:
            action_counts[t.action.name] = action_counts.get(t.action.name, 0) + 1

        logger.info(f"Reflect @ step {self._step_count}: "
                   f"avg_reward={avg_reward:.3f}, "
                   f"actions={action_counts}")

    def _generate_summary(self) -> Dict[str, Any]:
        """生成运行摘要"""
        rewards = [t.reward.total for t in self._history]
        action_dist: Dict[str, int] = {}
        for t in self._history:
            action_dist[t.action.name] = action_dist.get(t.action.name, 0) + 1

        return {
            "total_steps": self._step_count,
            "total_reward": round(self._total_reward, 4),
            "avg_reward": round(np.mean(rewards), 4) if rewards else 0,
            "max_reward": round(max(rewards), 4) if rewards else 0,
            "min_reward": round(min(rewards), 4) if rewards else 0,
            "action_distribution": action_dist,
            "final_phase": self._phase.value,
        }


# ═══════════════════════════════════════════════════════════
# Experiment Runner
# ═══════════════════════════════════════════════════════════

class ExperimentRunner:
    """
    实验运行器

    支持：
    - 单次运行
    - 多次重复 (N=30 统计验证)
    - A/B 对比 (不同策略对比)
    - 自动统计报告
    """

    def __init__(self, seed: Optional[int] = None):
        self._rng = np.random.RandomState(seed)
        self.seed = seed
        self._results: List[Dict[str, Any]] = []

    def run_single(self,
                   environment: Environment,
                   policy: Policy,
                   max_steps: int = 100) -> Dict[str, Any]:
        """运行单次实验"""
        loop = LearningLoop(environment, policy, max_steps=max_steps)
        summary = loop.run()
        self._results.append(summary)
        return summary

    def run_repeated(self,
                     env_factory: Callable[[], Environment],
                     policy_factory: Callable[[], Policy],
                     n_runs: int = 30,
                     max_steps: int = 100) -> Dict[str, Any]:
        """
        重复运行实验 (N=30 统计验证标准)

        Args:
            env_factory: 环境工厂函数
            policy_factory: 策略工厂函数
            n_runs: 重复次数
            max_steps: 每次最大步数

        Returns:
            统计摘要
        """
        total_rewards = []

        for i in range(n_runs):
            env = env_factory()
            policy = policy_factory()

            summary = self.run_single(env, policy, max_steps)
            total_rewards.append(summary["total_reward"])

            if (i + 1) % 10 == 0:
                logger.info(f"Run {i+1}/{n_runs}: "
                           f"reward={summary['total_reward']:.3f}")

        return {
            "n_runs": n_runs,
            "total_rewards": total_rewards,
            "mean_reward": float(np.mean(total_rewards)),
            "std_reward": float(np.std(total_rewards, ddof=1)),
            "min_reward": float(np.min(total_rewards)),
            "max_reward": float(np.max(total_rewards)),
        }

    def run_ab_test(self,
                    env_factory: Callable[[], Environment],
                    policy_a_factory: Callable[[], Policy],
                    policy_b_factory: Callable[[], Policy],
                    n_runs: int = 30,
                    max_steps: int = 100) -> Dict[str, Any]:
        """
        A/B 测试 - 对比两个策略

        自动使用 StatisticalValidator 进行统计检验
        """
        from moss.core.statistical_validator import StatisticalValidator, ValidationConfig

        # 运行 A 组
        results_a = self.run_repeated(env_factory, policy_a_factory, n_runs, max_steps)

        # 运行 B 组
        results_b = self.run_repeated(env_factory, policy_b_factory, n_runs, max_steps)

        # 统计检验
        validator = StatisticalValidator(ValidationConfig(n_samples=n_runs))
        validator.add_experiment("Policy_A", results_a["total_rewards"])
        validator.add_experiment("Policy_B", results_b["total_rewards"])

        report = validator.validate_experiment("Policy_A", "Policy_B")

        return {
            "policy_a": results_a,
            "policy_b": results_b,
            "validation": report.to_dict(),
        }


# ═══════════════════════════════════════════════════════════
# Demo
# ═══════════════════════════════════════════════════════════

def demo_autonomous_loop():
    """演示自主 Agent 循环"""
    print("=" * 70)
    print("MOSS v9.5.0 - Autonomous Agent Loop Demo")
    print("=" * 70)
    print()

    # 创建环境
    env = CodeEnvironment(project_path=".", max_steps=50)

    # 创建策略
    policy = EpsilonGreedyPolicy(epsilon=0.3, decay=0.995, seed=42)

    # 运行学习循环
    loop = LearningLoop(env, policy, max_steps=50)
    summary = loop.run()

    # 打印结果
    print(f"\nTotal Steps: {summary['total_steps']}")
    print(f"Total Reward: {summary['total_reward']:.3f}")
    print(f"Avg Reward: {summary['avg_reward']:.3f}")
    print(f"Action Distribution: {summary['action_distribution']}")

    print("\n--- A/B Test: EpsilonGreedy vs Random ---\n")

    # A/B 测试
    runner = ExperimentRunner(seed=42)

    results = runner.run_ab_test(
        env_factory=lambda: CodeEnvironment(".", max_steps=50),
        policy_a_factory=lambda: EpsilonGreedyPolicy(epsilon=0.2, seed=42),
        policy_b_factory=lambda: RandomPolicy(seed=42),
        n_runs=10,
        max_steps=50,
    )

    print(f"Policy A (EpsilonGreedy): mean={results['policy_a']['mean_reward']:.3f}")
    print(f"Policy B (Random): mean={results['policy_b']['mean_reward']:.3f}")
    print(f"Significant: {results['validation']['comparison']['hypothesis_test']['significant']}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo_autonomous_loop()
