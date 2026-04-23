"""
干预式驱动力验证代理 (Interventional Validation Agent)

核心能力：
1. 执行干预实验：强制启用/禁用特定驱动力
2. 收集行为数据：记录干预条件下的行为指标
3. 计算因果效应：Δbehavior = E[behavior | do(f=high)] - E[behavior | do(f=low)]

使用方式：
    validator = InterventionValidator(config)
    result = validator.validate_drive(candidate_drive, agent_config, existing_drives)
    if result.significant and result.delta_behavior > 0:
        # 接受候选驱动力
"""

import numpy as np
from typing import Dict, List
from dataclasses import dataclass
import logging
import tempfile
import yaml

logger = logging.getLogger(__name__)


@dataclass
class InterventionResult:
    """干预实验结果"""
    delta_behavior: float
    treatment_metrics: Dict
    control_metrics: Dict
    significant: bool
    p_value: float
    confidence_interval: tuple = (0.0, 0.0)


class InterventionValidator:
    """
    干预式验证代理

    实验设计：
    1. Treatment 组：强制启用候选驱动力，运行 N 周期
    2. Control 组：禁用候选驱动力，运行 N 周期
    3. 计算 Δbehavior = E[treatment] - E[control]
    4. 统计显著性检验
    """

    def __init__(self, config: Dict):
        self.cycles_per_condition = config.get('cycles_per_condition', 50)
        self.warmup_cycles = config.get('warmup_cycles', 10)
        self.significance_threshold = config.get('significance_threshold', 0.05)
        self.bootstrap_samples = config.get('bootstrap_samples', 100)

        # 行为指标权重
        self.metric_weights = {
            'success_rate': 0.3,
            'reward_avg': 0.3,
            'behavior_diversity': 0.2,
            'novel_action_ratio': 0.2
        }

    def validate_drive(self, candidate_drive, agent_config: Dict,
                       existing_drives: List[str]) -> InterventionResult:
        """
        执行完整的干预式验证

        Args:
            candidate_drive: EvolvedDrive 候选驱动力
            agent_config: Agent 配置字典
            existing_drives: 现有驱动力名称列表

        Returns:
            InterventionResult 包含因果效应和显著性
        """
        logger.info(f"开始干预式验证: {candidate_drive.name}")

        # 1. 运行 Treatment 组（强制启用候选驱动力）
        treatment_metrics = self._run_treatment(
            candidate_drive, agent_config, existing_drives
        )

        # 2. 运行 Control 组（正常状态，不添加候选驱动力）
        control_metrics = self._run_control(
            candidate_drive, agent_config, existing_drives
        )

        # 3. 计算因果效应
        delta_behavior = self._compute_delta(treatment_metrics, control_metrics)

        # 4. 统计显著性检验
        p_value = self._significance_test(treatment_metrics, control_metrics)

        # 5. 置信区间
        ci = self._compute_ci(delta_behavior, treatment_metrics, control_metrics)

        logger.info(f"验证完成: Δ={delta_behavior:.4f}, p={p_value:.4f}, 显著={p_value < self.significance_threshold}")

        return InterventionResult(
            delta_behavior=delta_behavior,
            treatment_metrics=treatment_metrics,
            control_metrics=control_metrics,
            significant=p_value < self.significance_threshold,
            p_value=p_value,
            confidence_interval=ci
        )

    def _run_treatment(self, candidate_drive, agent_config: Dict,
                       existing_drives: List[str]) -> Dict:
        """运行 Treatment 组：强制启用候选驱动力"""
        # 创建临时 Agent
        agent = self._create_test_agent(agent_config)

        # 添加候选驱动力
        eval_fn = getattr(candidate_drive, 'eval_fn', None) or getattr(candidate_drive, 'evolved_fn', None)
        agent.drive_manager.add_emergent_drive(
            name=candidate_drive.name,
            weight=0.25,
            description=getattr(candidate_drive, 'description', 'emerged'),
            source_behaviors=getattr(candidate_drive, 'source_behaviors', []),
            novelty_score=getattr(candidate_drive, 'novelty_score', 0.5),
            causal_independence=getattr(candidate_drive, 'causal_independence', 0.5),
            eval_fn=eval_fn
        )

        # 设置干预模式：强制使用该驱动力
        agent.set_intervention_mode(forced_drive=candidate_drive.name)

        # Warmup（不计入指标）
        for _ in range(self.warmup_cycles):
            agent._one_cycle()

        # 收集数据
        metrics = agent.run_intervention_cycles(self.cycles_per_condition)

        return metrics

    def _run_control(self, candidate_drive, agent_config: Dict,
                     existing_drives: List[str]) -> Dict:
        """运行 Control 组：正常状态（不添加候选驱动力）"""
        # 创建临时 Agent（不添加候选驱动力）
        agent = self._create_test_agent(agent_config)

        # Warmup
        for _ in range(self.warmup_cycles):
            agent._one_cycle()

        # 收集数据
        metrics = agent.run_intervention_cycles(self.cycles_per_condition)

        return metrics

    def _create_test_agent(self, agent_config: Dict):
        """创建测试用的临时 Agent"""
        from .agent import AGIAgent

        # 写入临时配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(agent_config, f)
            config_path = f.name

        return AGIAgent(config_path)

    def _compute_delta(self, treatment: Dict, control: Dict) -> float:
        """计算因果效应大小（综合指标）"""
        delta = 0.0
        for metric, w in self.metric_weights.items():
            t_val = treatment.get(metric, 0.0)
            c_val = control.get(metric, 0.0)
            delta += w * (t_val - c_val)
        return delta

    def _significance_test(self, treatment: Dict, control: Dict) -> float:
        """统计显著性检验（正态近似）"""
        t_success = treatment.get('success_rate', 0.5)
        c_success = control.get('success_rate', 0.5)

        n = self.cycles_per_condition
        se = np.sqrt(t_success * (1 - t_success) / n + c_success * (1 - c_success) / n + 1e-8)
        z = (t_success - c_success) / se

        # 双尾检验 p-value（使用正态CDF近似）
        p_value = self._norm_cdf_approx(abs(z))
        p_value = 2 * (1 - p_value)

        return float(p_value)

    def _norm_cdf_approx(self, x: float) -> float:
        """标准正态分布CDF的Hastings近似（避免scipy依赖）"""
        if x < 0:
            return 1 - self._norm_cdf_approx(-x)
        # 常数
        a1, a2, a3, a4, a5 = 0.254829592, -0.284496736, 1.421413741, -1.453152027, 1.061405429
        p = 0.3275911
        # 计算
        sign = 1 if x >= 0 else -1
        x = abs(x) / (2 ** 0.5)
        t = 1.0 / (1.0 + p * x)
        y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * np.exp(-x * x)
        return 0.5 * (1.0 + sign * y)

    def _compute_ci(self, delta: float, treatment: Dict, control: Dict) -> tuple:
        """计算置信区间"""
        n = self.cycles_per_condition

        t_var = treatment.get('success_rate', 0.5) * (1 - treatment.get('success_rate', 0.5))
        c_var = control.get('success_rate', 0.5) * (1 - control.get('success_rate', 0.5))

        se = np.sqrt(t_var / n + c_var / n + 1e-8)

        return (delta - 1.96 * se, delta + 1.96 * se)
