"""
Tests for Statistical Validator
统计验证框架测试
"""

import numpy as np
import pytest
from pathlib import Path

from moss.core.statistical_validator import (
    ValidationConfig,
    ExperimentData,
    ComparisonResult,
    ValidationReport,
    StatisticalValidator,
    TestType,
    EffectSizeInterpretation,
)


class TestValidationConfig:
    """测试验证配置"""

    def test_default_config(self):
        config = ValidationConfig()
        assert config.n_samples == 30
        assert config.alpha == 0.05
        assert config.test_type == TestType.T_TEST
        assert config.confidence_level == 0.95

    def test_custom_config(self):
        config = ValidationConfig(
            n_samples=50,
            alpha=0.01,
            test_type=TestType.MANN_WHITNEY,
            random_seed=42
        )
        assert config.n_samples == 50
        assert config.alpha == 0.01
        assert config.test_type == TestType.MANN_WHITNEY
        assert config.random_seed == 42

    def test_config_validation_invalid_n(self):
        config = ValidationConfig(n_samples=5)
        errors = config.validate()
        assert len(errors) > 0
        assert "n_samples" in errors[0]

    def test_config_validation_invalid_alpha(self):
        config = ValidationConfig(alpha=1.5)
        errors = config.validate()
        assert len(errors) > 0
        assert "alpha" in errors[0]


class TestExperimentData:
    """测试实验数据类"""

    def test_creation(self):
        data = ExperimentData("test", [1.0, 2.0, 3.0])
        assert data.name == "test"
        assert data.n == 3
        assert data.mean == 2.0

    def test_empty_values_raises(self):
        with pytest.raises(ValueError):
            ExperimentData("test", [])

    def test_statistics(self):
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        data = ExperimentData("test", values)
        assert data.mean == 30.0
        assert data.median == 30.0
        assert data.min == 10.0
        assert data.max == 50.0
        assert data.std > 0

    def test_ci_calculation(self):
        np.random.seed(42)
        values = np.random.normal(100, 10, 30).tolist()
        data = ExperimentData("test", values)
        ci_low, ci_high = data.ci()
        assert ci_low < data.mean < ci_high

    def test_normality_test(self):
        # 正态分布数据
        np.random.seed(42)
        normal_data = ExperimentData("normal", np.random.normal(0, 1, 50).tolist())
        stat, p = normal_data.shapiro_test()
        assert 0 <= stat <= 1
        assert 0 <= p <= 1

    def test_to_dict(self):
        data = ExperimentData("test", [1.0, 2.0, 3.0], unit="points", metadata={"key": "value"})
        d = data.to_dict()
        assert d["name"] == "test"
        assert d["n"] == 3
        assert d["unit"] == "points"
        assert "mean" in d
        assert "ci_95" in d


class TestStatisticalValidator:
    """测试统计验证器"""

    def test_creation(self):
        validator = StatisticalValidator()
        assert validator.config.n_samples == 30

    def test_creation_with_config(self):
        config = ValidationConfig(n_samples=20, random_seed=42)
        validator = StatisticalValidator(config)
        assert validator.config.n_samples == 20

    def test_add_experiment(self):
        validator = StatisticalValidator()
        data = validator.add_experiment("exp1", [1.0, 2.0, 3.0])
        assert data.name == "exp1"
        assert "exp1" in validator._experiments

    def test_compare_t_test(self):
        np.random.seed(42)
        validator = StatisticalValidator()

        # 显著不同的两组数据
        exp_values = np.random.normal(100, 10, 30).tolist()
        ctrl_values = np.random.normal(80, 10, 30).tolist()

        validator.add_experiment("experiment", exp_values)
        validator.add_experiment("control", ctrl_values)

        result = validator.compare("experiment", "control")

        assert isinstance(result, ComparisonResult)
        assert result.experiment_name == "experiment"
        assert result.control_name == "control"
        assert result.p_value < 0.05  # 应该显著
        assert result.significant is True
        assert result.cohens_d > 0.8  # 大效应量

    def test_compare_mann_whitney(self):
        np.random.seed(42)
        validator = StatisticalValidator(config=ValidationConfig(test_type=TestType.MANN_WHITNEY))

        exp_values = np.random.normal(100, 10, 30).tolist()
        ctrl_values = np.random.normal(80, 10, 30).tolist()

        validator.add_experiment("experiment", exp_values)
        validator.add_experiment("control", ctrl_values)

        result = validator.compare("experiment", "control")
        assert result.test_type == TestType.MANN_WHITNEY
        assert result.p_value < 0.05

    def test_compare_missing_experiment(self):
        validator = StatisticalValidator()
        validator.add_experiment("control", [1.0, 2.0, 3.0])

        with pytest.raises(ValueError):
            validator.compare("missing", "control")

    def test_compare_missing_control(self):
        validator = StatisticalValidator()
        validator.add_experiment("experiment", [1.0, 2.0, 3.0])

        with pytest.raises(ValueError):
            validator.compare("experiment", "missing")

    def test_validate_experiment(self):
        np.random.seed(42)
        validator = StatisticalValidator()

        exp_values = np.random.normal(100, 10, 30).tolist()
        ctrl_values = np.random.normal(80, 10, 30).tolist()

        validator.add_experiment("MOSS", exp_values)
        validator.add_experiment("Baseline", ctrl_values)

        report = validator.validate_experiment("MOSS", "Baseline")

        assert isinstance(report, ValidationReport)
        assert report.experiment_name == "MOSS"
        assert report.comparison is not None
        assert len(report.conclusions) >= 4
        assert report.comparison.significant is True

    def test_validate_experiment_no_improvement(self):
        np.random.seed(42)
        validator = StatisticalValidator()

        # 两组相同分布的数据
        exp_values = np.random.normal(80, 10, 30).tolist()
        ctrl_values = np.random.normal(80, 10, 30).tolist()

        validator.add_experiment("exp", exp_values)
        validator.add_experiment("ctrl", ctrl_values)

        report = validator.validate_experiment("exp", "ctrl")

        # 可能不显著 (取决于随机种子)
        assert report.comparison is not None

    def test_run_ab_test(self):
        np.random.seed(42)
        validator = StatisticalValidator(ValidationConfig(n_samples=10))

        def exp_func():
            return np.random.normal(100, 5)

        def ctrl_func():
            return np.random.normal(90, 5)

        report = validator.run_ab_test(
            exp_func, ctrl_func,
            experiment_name="NewFeature",
            control_name="OldFeature"
        )

        assert report.experiment_name == "NewFeature"
        assert report.control_data is not None
        assert report.comparison is not None

    def test_save_report(self, tmp_path):
        np.random.seed(42)
        validator = StatisticalValidator()

        validator.add_experiment("exp", np.random.normal(100, 10, 30).tolist())
        validator.add_experiment("ctrl", np.random.normal(90, 10, 30).tolist())

        report = validator.validate_experiment("exp", "ctrl")

        output_path = tmp_path / "test_report"
        validator.save_report(report, output_path)

        assert (tmp_path / "test_report.json").exists()
        assert (tmp_path / "test_report.md").exists()

    def test_get_summary(self):
        validator = StatisticalValidator()
        validator.add_experiment("exp1", [1.0, 2.0, 3.0])
        validator.add_experiment("exp2", [4.0, 5.0, 6.0])

        summary = validator.get_summary()
        assert "experiments" in summary
        assert "exp1" in summary["experiments"]
        assert "exp2" in summary["experiments"]


class TestEffectSizeInterpretation:
    """测试效应量解释"""

    def test_neglibible(self):
        assert EffectSizeInterpretation.from_cohens_d(0.1) == EffectSizeInterpretation.NEGLIGIBLE
        assert EffectSizeInterpretation.from_cohens_d(-0.1) == EffectSizeInterpretation.NEGLIGIBLE

    def test_small(self):
        assert EffectSizeInterpretation.from_cohens_d(0.3) == EffectSizeInterpretation.SMALL
        assert EffectSizeInterpretation.from_cohens_d(0.4) == EffectSizeInterpretation.SMALL

    def test_medium(self):
        assert EffectSizeInterpretation.from_cohens_d(0.6) == EffectSizeInterpretation.MEDIUM
        assert EffectSizeInterpretation.from_cohens_d(0.7) == EffectSizeInterpretation.MEDIUM

    def test_large(self):
        assert EffectSizeInterpretation.from_cohens_d(0.8) == EffectSizeInterpretation.LARGE
        assert EffectSizeInterpretation.from_cohens_d(1.5) == EffectSizeInterpretation.LARGE


class TestComparisonResult:
    """测试对比结果"""

    def test_to_dict(self):
        result = ComparisonResult(
            experiment_name="exp",
            control_name="ctrl",
            test_type=TestType.T_TEST,
            experiment_mean=100.0,
            control_mean=90.0,
            mean_diff=10.0,
            relative_improvement=11.11,
            test_statistic=3.5,
            p_value=0.001,
            significant=True,
            alpha=0.05,
            cohens_d=1.2,
            effect_size="large",
            effect_interpretation=EffectSizeInterpretation.LARGE,
            ci_diff_low=5.0,
            ci_diff_high=15.0,
        )

        d = result.to_dict()
        assert d["experiment"] == "exp"
        assert d["control"] == "ctrl"
        assert d["hypothesis_test"]["significant"] is True
        assert d["effect_size"]["cohens_d"] == 1.2


class TestValidationReport:
    """测试验证报告"""

    def test_to_markdown(self):
        config = ValidationConfig()
        exp_data = ExperimentData("exp", [90.0, 95.0, 100.0])

        report = ValidationReport(
            experiment_name="Test",
            timestamp="2024-01-01T00:00:00",
            config=config,
            experiment_data=exp_data,
            conclusions=["Test conclusion"]
        )

        md = report.to_markdown()
        assert "# Statistical Validation Report" in md
        assert "Mean" in md
        # Note: conclusions only shown when comparison exists

    def test_to_dict_with_comparison(self):
        config = ValidationConfig()
        exp_data = ExperimentData("exp", [100.0, 101.0, 102.0])
        ctrl_data = ExperimentData("ctrl", [90.0, 91.0, 92.0])

        comparison = ComparisonResult(
            experiment_name="exp",
            control_name="ctrl",
            test_type=TestType.T_TEST,
            experiment_mean=101.0,
            control_mean=91.0,
            mean_diff=10.0,
            relative_improvement=10.99,
            test_statistic=10.0,
            p_value=0.0001,
            significant=True,
            alpha=0.05,
            cohens_d=3.0,
            effect_size="large",
            effect_interpretation=EffectSizeInterpretation.LARGE,
            ci_diff_low=8.0,
            ci_diff_high=12.0,
        )

        report = ValidationReport(
            experiment_name="Test",
            timestamp="2024-01-01T00:00:00",
            config=config,
            experiment_data=exp_data,
            control_data=ctrl_data,
            comparison=comparison,
            conclusions=["Passed"]
        )

        d = report.to_dict()
        assert d["comparison"] is not None
        assert d["comparison"]["hypothesis_test"]["significant"] is True


class TestMvesReplication:
    """
    测试是否能复现 mves v8.6.0 的结果

    mves v8.6.0 统计结果：
    - N=30
    - p < 0.0001
    - Cohen's d = 3.112 (large effect)
    - 100% task completion
    """

    def test_replicate_mves_results(self):
        """模拟 mves 实验条件"""
        np.random.seed(42)
        validator = StatisticalValidator(ValidationConfig(n_samples=30))

        # 模拟 mves 数据 (高表现，低方差)
        mves_values = np.random.normal(100, 2, 30).tolist()

        # 模拟基线 (低表现，高方差)
        baseline_values = np.random.normal(60, 10, 30).tolist()

        validator.add_experiment("mves", mves_values)
        validator.add_experiment("baseline", baseline_values)

        report = validator.validate_experiment("mves", "baseline")

        # 验证统计显著性
        assert report.comparison.significant is True
        assert report.comparison.p_value < 0.001

        # 验证大效应量
        assert abs(report.comparison.cohens_d) > 2.0

        # 验证结论包含通过
        assert any("PASSED" in c for c in report.conclusions)
