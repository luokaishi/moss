"""
MOSS Statistical Validator
统计验证框架 - 基于 mves v8.6.0 实验方法论

提供学术级统计验证：
- N=30 样本量统计验证
- 独立 t-test / Mann-Whitney U 测试
- Cohen's d 效应量计算
- 置信区间估计
- A/B 对比实验框架
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


class TestType(Enum):
    """统计测试类型"""
    T_TEST = "t_test"  # 独立样本 t 检验 (正态分布)
    MANN_WHITNEY = "mann_whitney"  # Mann-Whitney U (非参数)
    WILCOXON = "wilcoxon"  # Wilcoxon 符号秩 (配对样本)


class EffectSizeInterpretation(Enum):
    """效应量解释"""
    NEGLIGIBLE = "negligible"  # |d| < 0.2
    SMALL = "small"  # 0.2 <= |d| < 0.5
    MEDIUM = "medium"  # 0.5 <= |d| < 0.8
    LARGE = "large"  # |d| >= 0.8

    @classmethod
    def from_cohens_d(cls, d: float) -> "EffectSizeInterpretation":
        """根据 Cohen's d 值返回效应量解释"""
        abs_d = abs(d)
        if abs_d < 0.2:
            return cls.NEGLIGIBLE
        elif abs_d < 0.5:
            return cls.SMALL
        elif abs_d < 0.8:
            return cls.MEDIUM
        else:
            return cls.LARGE


@dataclass
class ValidationConfig:
    """验证配置"""
    n_samples: int = 30  # 默认样本量 (mves 标准)
    alpha: float = 0.05  # 显著性水平
    test_type: TestType = TestType.T_TEST
    min_effect_size: float = 0.5  # 最小可接受效应量 (medium)
    confidence_level: float = 0.95  # 置信水平
    random_seed: Optional[int] = None  # 可重复性

    def validate(self) -> List[str]:
        """验证配置有效性"""
        errors = []
        if self.n_samples < 10:
            errors.append(f"n_samples must be >= 10, got {self.n_samples}")
        if not 0 < self.alpha < 1:
            errors.append(f"alpha must be in (0, 1), got {self.alpha}")
        if not 0 < self.confidence_level < 1:
            errors.append(f"confidence_level must be in (0, 1), got {self.confidence_level}")
        return errors


@dataclass
class ExperimentData:
    """实验数据"""
    name: str
    values: List[float]
    unit: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.values:
            raise ValueError("values cannot be empty")

    @property
    def n(self) -> int:
        return len(self.values)

    @property
    def mean(self) -> float:
        return float(np.mean(self.values))

    @property
    def std(self) -> float:
        return float(np.std(self.values, ddof=1))

    @property
    def median(self) -> float:
        return float(np.median(self.values))

    @property
    def min(self) -> float:
        return float(np.min(self.values))

    @property
    def max(self) -> float:
        return float(np.max(self.values))

    def ci(self, confidence: float = 0.95) -> Tuple[float, float]:
        """计算置信区间"""
        if self.n < 2:
            return (self.mean, self.mean)
        sem = stats.sem(self.values)
        ci = stats.t.interval(confidence, self.n - 1, loc=self.mean, scale=sem)
        return (float(ci[0]), float(ci[1]))

    def shapiro_test(self) -> Tuple[float, float]:
        """Shapiro-Wilk 正态性检验"""
        if self.n < 3:
            return (0.0, 1.0)  # 无法检验
        stat, p = stats.shapiro(self.values)
        return (float(stat), float(p))

    def is_normal(self, alpha: float = 0.05) -> bool:
        """检查是否正态分布"""
        _, p = self.shapiro_test()
        return p > alpha

    def to_dict(self) -> Dict[str, Any]:
        ci_low, ci_high = self.ci()
        return {
            "name": self.name,
            "n": self.n,
            "mean": round(self.mean, 4),
            "std": round(self.std, 4),
            "median": round(self.median, 4),
            "min": round(self.min, 4),
            "max": round(self.max, 4),
            "ci_95": [round(ci_low, 4), round(ci_high, 4)],
            "unit": self.unit,
            "is_normal": self.is_normal(),
            "metadata": self.metadata,
        }


@dataclass
class ComparisonResult:
    """对比结果"""
    experiment_name: str
    control_name: str
    test_type: TestType

    # 基本统计
    experiment_mean: float
    control_mean: float
    mean_diff: float
    relative_improvement: float  # 百分比

    # 假设检验
    test_statistic: float
    p_value: float
    significant: bool
    alpha: float

    # 效应量
    cohens_d: float
    effect_size: str
    effect_interpretation: EffectSizeInterpretation

    # 置信区间
    ci_diff_low: float
    ci_diff_high: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment": self.experiment_name,
            "control": self.control_name,
            "test_type": self.test_type.value,
            "statistics": {
                "experiment_mean": round(self.experiment_mean, 4),
                "control_mean": round(self.control_mean, 4),
                "mean_diff": round(self.mean_diff, 4),
                "relative_improvement": round(self.relative_improvement, 2),
            },
            "hypothesis_test": {
                "statistic": round(self.test_statistic, 4),
                "p_value": f"{self.p_value:.2e}" if self.p_value < 0.001 else round(self.p_value, 4),
                "significant": self.significant,
                "alpha": self.alpha,
            },
            "effect_size": {
                "cohens_d": round(self.cohens_d, 3),
                "magnitude": self.effect_size,
                "interpretation": self.effect_interpretation.value,
            },
            "confidence_interval": {
                "diff_95": [round(self.ci_diff_low, 4), round(self.ci_diff_high, 4)],
                "includes_zero": self.ci_diff_low <= 0 <= self.ci_diff_high,
            },
        }


@dataclass
class ValidationReport:
    """验证报告"""
    experiment_name: str
    timestamp: str
    config: ValidationConfig
    experiment_data: ExperimentData
    control_data: Optional[ExperimentData] = None
    comparison: Optional[ComparisonResult] = None
    conclusions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_name": self.experiment_name,
            "timestamp": self.timestamp,
            "config": {
                "n_samples": self.config.n_samples,
                "alpha": self.config.alpha,
                "test_type": self.config.test_type.value,
                "confidence_level": self.config.confidence_level,
            },
            "experiment": self.experiment_data.to_dict(),
            "control": self.control_data.to_dict() if self.control_data else None,
            "comparison": self.comparison.to_dict() if self.comparison else None,
            "conclusions": self.conclusions,
        }

    def to_markdown(self) -> str:
        """生成 Markdown 报告"""
        lines = [
            f"# Statistical Validation Report: {self.experiment_name}",
            "",
            f"**Timestamp:** {self.timestamp}",
            f"**Sample Size:** N={self.config.n_samples}",
            f"**Significance Level:** α={self.config.alpha}",
            "",
            "## Experiment Results",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Mean | {self.experiment_data.mean:.4f} ± {self.experiment_data.std:.4f} |",
            f"| Median | {self.experiment_data.median:.4f} |",
            f"| Range | [{self.experiment_data.min:.4f}, {self.experiment_data.max:.4f}] |",
            f"| 95% CI | [{self.experiment_data.ci()[0]:.4f}, {self.experiment_data.ci()[1]:.4f}] |",
            "",
        ]

        if self.comparison:
            comp = self.comparison
            lines.extend([
                "## Comparison with Control",
                "",
                f"| Metric | Value |",
                f"|--------|-------|",
                f"| Mean Difference | {comp.mean_diff:+.4f} |",
                f"| Relative Improvement | {comp.relative_improvement:+.2f}% |",
                f"| Test Statistic | {comp.test_statistic:.4f} |",
                f"| P-value | {comp.p_value:.2e} |",
                f"| Significant | {'✅ Yes' if comp.significant else '❌ No'} |",
                f"| Cohen's d | {comp.cohens_d:.3f} ({comp.effect_size}) |",
                "",
                "## Conclusions",
                "",
            ])
            for conclusion in self.conclusions:
                lines.append(f"- {conclusion}")
            lines.append("")

        return "\n".join(lines)


class StatisticalValidator:
    """
    统计验证器

    基于 mves v8.6.0 方法论：
    - N=30 样本量验证
    - 双尾独立 t 检验
    - Cohen's d 效应量
    - p < 0.05 显著性
    """

    def __init__(self, config: Optional[ValidationConfig] = None):
        self.config = config or ValidationConfig()
        errors = self.config.validate()
        if errors:
            raise ValueError(f"Invalid config: {', '.join(errors)}")

        if self.config.random_seed:
            np.random.seed(self.config.random_seed)

        self._experiments: Dict[str, ExperimentData] = {}
        self._comparisons: Dict[str, ComparisonResult] = {}

    def add_experiment(self, name: str, values: List[float],
                       unit: str = "", metadata: Optional[Dict] = None) -> ExperimentData:
        """添加实验数据"""
        data = ExperimentData(
            name=name,
            values=values,
            unit=unit,
            metadata=metadata or {}
        )
        self._experiments[name] = data
        logger.info(f"Added experiment '{name}': N={data.n}, mean={data.mean:.4f}")
        return data

    def compare(self, experiment_name: str, control_name: str,
                auto_select_test: bool = True) -> ComparisonResult:
        """
        对比实验组与对照组

        Args:
            experiment_name: 实验组名称
            control_name: 对照组名称
            auto_select_test: 自动选择测试类型 (基于正态性检验)

        Returns:
            ComparisonResult 对比结果
        """
        if experiment_name not in self._experiments:
            raise ValueError(f"Experiment '{experiment_name}' not found")
        if control_name not in self._experiments:
            raise ValueError(f"Control '{control_name}' not found")

        exp = self._experiments[experiment_name]
        ctrl = self._experiments[control_name]

        # 自动选择测试类型
        test_type = self.config.test_type
        if auto_select_test and test_type != TestType.MANN_WHITNEY:
            if exp.is_normal() and ctrl.is_normal():
                test_type = TestType.T_TEST
            else:
                test_type = TestType.MANN_WHITNEY

        # 执行统计测试
        if test_type == TestType.T_TEST:
            test_stat, p_value = stats.ttest_ind(exp.values, ctrl.values)
        elif test_type == TestType.MANN_WHITNEY:
            test_stat, p_value = stats.mannwhitneyu(
                exp.values, ctrl.values, alternative='two-sided'
            )
        else:  # WILCOXON
            test_stat, p_value = stats.wilcoxon(exp.values, ctrl.values)

        # 计算效应量 (Cohen's d)
        pooled_std = np.sqrt((np.var(exp.values, ddof=1) + np.var(ctrl.values, ddof=1)) / 2)
        cohens_d = (exp.mean - ctrl.mean) / pooled_std if pooled_std > 0 else 0.0

        # 解释效应量
        abs_d = abs(cohens_d)
        if abs_d < 0.2:
            effect_interp = EffectSizeInterpretation.NEGLIGIBLE
        elif abs_d < 0.5:
            effect_interp = EffectSizeInterpretation.SMALL
        elif abs_d < 0.8:
            effect_interp = EffectSizeInterpretation.MEDIUM
        else:
            effect_interp = EffectSizeInterpretation.LARGE

        # 置信区间 (均值差的 CI)
        diff_mean = exp.mean - ctrl.mean
        diff_std = np.sqrt(exp.std**2 / exp.n + ctrl.std**2 / ctrl.n)
        ci_margin = stats.t.ppf(0.975, exp.n + ctrl.n - 2) * diff_std
        ci_low = diff_mean - ci_margin
        ci_high = diff_mean + ci_margin

        # 相对改进
        relative_imp = ((exp.mean - ctrl.mean) / abs(ctrl.mean) * 100) if ctrl.mean != 0 else 0

        result = ComparisonResult(
            experiment_name=experiment_name,
            control_name=control_name,
            test_type=test_type,
            experiment_mean=exp.mean,
            control_mean=ctrl.mean,
            mean_diff=diff_mean,
            relative_improvement=relative_imp,
            test_statistic=float(test_stat),
            p_value=float(p_value),
            significant=bool(p_value < self.config.alpha),
            alpha=self.config.alpha,
            cohens_d=float(cohens_d),
            effect_size=effect_interp.value,
            effect_interpretation=effect_interp,
            ci_diff_low=float(ci_low),
            ci_diff_high=float(ci_high),
        )

        key = f"{experiment_name}_vs_{control_name}"
        self._comparisons[key] = result

        logger.info(f"Comparison '{key}': p={p_value:.4f}, d={cohens_d:.3f}, "
                   f"significant={result.significant}")

        return result

    def validate_experiment(self, experiment_name: str, control_name: str,
                           min_effect_size: Optional[float] = None) -> ValidationReport:
        """
        完整验证实验

        生成结论：
        - 统计显著性
        - 实际意义 (效应量)
        - 置信区间是否包含零
        """
        min_effect = min_effect_size or self.config.min_effect_size

        comparison = self.compare(experiment_name, control_name)
        exp_data = self._experiments[experiment_name]
        ctrl_data = self._experiments[control_name]

        conclusions = []

        # 显著性结论
        if comparison.significant:
            conclusions.append(
                f"✅ **Statistically significant**: p={comparison.p_value:.4f} < α={comparison.alpha}"
            )
        else:
            conclusions.append(
                f"❌ **Not statistically significant**: p={comparison.p_value:.4f} >= α={comparison.alpha}"
            )

        # 效应量结论
        if abs(comparison.cohens_d) >= min_effect:
            conclusions.append(
                f"✅ **Practically significant**: Cohen's d={comparison.cohens_d:.3f} "
                f"(>= {min_effect} threshold)"
            )
        else:
            conclusions.append(
                f"⚠️ **Small effect size**: Cohen's d={comparison.cohens_d:.3f} "
                f"(< {min_effect} threshold)"
            )

        # CI 结论
        if comparison.ci_diff_low > 0:
            conclusions.append(
                f"✅ **Positive effect**: 95% CI [{comparison.ci_diff_low:.4f}, "
                f"{comparison.ci_diff_high:.4f}] excludes zero"
            )
        elif comparison.ci_diff_high < 0:
            conclusions.append(
                f"⚠️ **Negative effect**: 95% CI [{comparison.ci_diff_low:.4f}, "
                f"{comparison.ci_diff_high:.4f}] excludes zero (below control)"
            )
        else:
            conclusions.append(
                f"❌ **Uncertain effect**: 95% CI [{comparison.ci_diff_low:.4f}, "
                f"{comparison.ci_diff_high:.4f}] includes zero"
            )

        # 综合结论
        if comparison.significant and abs(comparison.cohens_d) >= min_effect:
            conclusions.append(
                f"🎉 **VALIDATION PASSED**: '{experiment_name}' significantly outperforms "
                f"'{control_name}' with {comparison.effect_size} effect"
            )
        else:
            conclusions.append(
                f"❌ **VALIDATION FAILED**: '{experiment_name}' does not show "
                f"significant improvement over '{control_name}'"
            )

        return ValidationReport(
            experiment_name=experiment_name,
            timestamp=datetime.now().isoformat(),
            config=self.config,
            experiment_data=exp_data,
            control_data=ctrl_data,
            comparison=comparison,
            conclusions=conclusions,
        )

    def run_ab_test(self, experiment_func: Callable[[], float],
                   control_func: Callable[[], float],
                   n: Optional[int] = None,
                   experiment_name: str = "Experiment",
                   control_name: str = "Control") -> ValidationReport:
        """
        运行 A/B 测试

        自动运行实验收集数据并验证

        Args:
            experiment_func: 实验组函数，返回指标值
            control_func: 对照组函数，返回指标值
            n: 样本量 (默认使用 config.n_samples)
            experiment_name: 实验组名称
            control_name: 对照组名称

        Returns:
            ValidationReport 完整验证报告
        """
        n_samples = n or self.config.n_samples
        logger.info(f"Running A/B test: {n_samples} samples per group")

        # 收集实验数据
        exp_values = []
        for i in range(n_samples):
            value = experiment_func()
            exp_values.append(value)
            if (i + 1) % 10 == 0:
                logger.info(f"  {experiment_name}: {i + 1}/{n_samples}")

        # 收集对照数据
        ctrl_values = []
        for i in range(n_samples):
            value = control_func()
            ctrl_values.append(value)
            if (i + 1) % 10 == 0:
                logger.info(f"  {control_name}: {i + 1}/{n_samples}")

        # 添加数据
        self.add_experiment(experiment_name, exp_values)
        self.add_experiment(control_name, ctrl_values)

        # 验证
        return self.validate_experiment(experiment_name, control_name)

    def save_report(self, report: ValidationReport, path: Path) -> None:
        """保存报告到文件"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # JSON 格式
        json_path = path.with_suffix('.json')
        with open(json_path, 'w') as f:
            json.dump(report.to_dict(), f, indent=2, default=str)

        # Markdown 格式
        md_path = path.with_suffix('.md')
        with open(md_path, 'w') as f:
            f.write(report.to_markdown())

        logger.info(f"Reports saved: {json_path}, {md_path}")

    def get_summary(self) -> Dict[str, Any]:
        """获取所有实验的摘要"""
        return {
            "experiments": {name: data.to_dict() for name, data in self._experiments.items()},
            "comparisons": {key: comp.to_dict() for key, comp in self._comparisons.items()},
        }


def demo_statistical_validator():
    """演示统计验证器"""
    print("=" * 70)
    print("MOSS Statistical Validator Demo")
    print("=" * 70)
    print()

    # 创建验证器 (N=30, mves 标准)
    validator = StatisticalValidator(
        ValidationConfig(n_samples=30, alpha=0.05, random_seed=42)
    )

    # 模拟 MOSS (新系统) 结果 - 高表现
    np.random.seed(42)
    moss_values = np.random.normal(95, 5, 30).tolist()

    # 模拟基线结果 - 较低表现
    baseline_values = np.random.normal(85, 8, 30).tolist()

    # 添加数据
    validator.add_experiment("MOSS_v9.4", moss_values, unit="score")
    validator.add_experiment("Baseline", baseline_values, unit="score")

    # 验证
    report = validator.validate_experiment("MOSS_v9.4", "Baseline")

    # 打印结果
    print(report.to_markdown())

    # 保存报告
    output_dir = Path("validation_reports")
    output_dir.mkdir(exist_ok=True)
    validator.save_report(report, output_dir / "moss_v94_validation")

    return report


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo_statistical_validator()
