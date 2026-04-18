"""
Tests for Statistical Analysis Modules - 统计分析模块单元测试

测试内容:
1. Effect Size Calculation (Cohen's d, Hedge's g, etc.)
2. Bootstrap Confidence Intervals
3. Multiple Comparison Correction
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
import numpy as np

from agi.analysis.effect_size import (
    cohens_d, hedges_g, glass_delta, r_from_t,
    compare_to_baseline, effect_size_summary,
    _interpret_cohens_d, _interpret_r
)

from agi.analysis.bootstrap import (
    percentile_bootstrap, bca_bootstrap,
    bootstrap_two_groups, bootstrap_mean_ci,
    quick_bootstrap_ci
)

from agi.analysis.multiple_comparison import (
    bonferroni_correction, holm_bonferroni_correction,
    benjamini_hochberg_correction, benjamini_yekutieli_correction,
    sidak_correction, apply_correction, compare_methods
)


class TestEffectSize(unittest.TestCase):
    """测试效应量计算"""
    
    def setUp(self):
        """设置测试数据"""
        np.random.seed(42)
        self.group1 = np.random.normal(100, 15, 50).tolist()
        self.group2 = np.random.normal(95, 15, 50).tolist()
    
    def test_cohens_d(self):
        """测试 Cohen's d"""
        result = cohens_d(self.group1, self.group2)
        
        self.assertIsNotNone(result.value)
        self.assertGreater(result.value, 0)  # group1 均值更高
        self.assertIsNotNone(result.ci_lower)
        self.assertIsNotNone(result.ci_upper)
        self.assertEqual(result.metric, "Cohen's d")
        self.assertIn('negligible', result.interpretation)
    
    def test_hedges_g(self):
        """测试 Hedge's g"""
        result = hedges_g(self.group1, self.group2)
        
        self.assertIsNotNone(result.value)
        # Hedge's g 应该接近 Cohen's d (小样本校正)
        d_result = cohens_d(self.group1, self.group2)
        self.assertAlmostEqual(result.value, d_result.value, places=1)
    
    def test_glass_delta(self):
        """测试 Glass's delta"""
        result = glass_delta(self.group1, self.group2)
        
        self.assertIsNotNone(result.value)
        self.assertEqual(result.metric, "Glass's delta")
    
    def test_r_from_t(self):
        """测试从 t 统计量计算 r"""
        t = 2.5
        df = 48
        result = r_from_t(t, df)
        
        self.assertIsNotNone(result.value)
        self.assertGreater(abs(result.value), 0)
        self.assertLess(abs(result.value), 1)
    
    def test_compare_to_baseline(self):
        """测试与基线比较"""
        baseline = 100
        result = compare_to_baseline(self.group1, baseline)
        
        self.assertIsNotNone(result.value)
        self.assertEqual(result.metric, "Cohen's d (one-sample)")
    
    def test_effect_size_summary(self):
        """测试效应量摘要"""
        summary = effect_size_summary(self.group1, self.group2)
        
        self.assertIn('cohens_d', summary)
        self.assertIn('hedges_g', summary)
        self.assertIn('glass_delta', summary)
    
    def test_interpret_cohens_d(self):
        """测试 Cohen's d 解释"""
        self.assertIn('可忽略', _interpret_cohens_d(0.1))
        self.assertIn('小', _interpret_cohens_d(0.3))
        self.assertIn('中', _interpret_cohens_d(0.6))
        self.assertIn('大', _interpret_cohens_d(1.0))
    
    def test_interpret_r(self):
        """测试 r 解释"""
        self.assertIn('可忽略', _interpret_r(0.05))
        self.assertIn('小', _interpret_r(0.2))
        self.assertIn('中', _interpret_r(0.4))
        self.assertIn('大', _interpret_r(0.6))


class TestBootstrap(unittest.TestCase):
    """测试 Bootstrap 置信区间"""
    
    def setUp(self):
        """设置测试数据"""
        np.random.seed(42)
        self.data = np.random.normal(100, 15, 100).tolist()
    
    def test_percentile_bootstrap(self):
        """测试百分位 Bootstrap"""
        result = percentile_bootstrap(self.data, np.mean, n_bootstrap=1000, ci=0.95)
        
        self.assertIsNotNone(result.statistic)
        self.assertIsNotNone(result.ci_lower)
        self.assertIsNotNone(result.ci_upper)
        self.assertEqual(result.ci_level, 0.95)
        self.assertEqual(result.n_bootstrap, 1000)
        # CI 应该包含统计量
        self.assertLess(result.ci_lower, result.statistic)
        self.assertGreater(result.ci_upper, result.statistic)
    
    def test_bca_bootstrap(self):
        """测试 BCa Bootstrap"""
        result = bca_bootstrap(self.data, np.mean, n_bootstrap=1000, ci=0.95)
        
        self.assertIsNotNone(result.statistic)
        self.assertIsNotNone(result.ci_lower)
        self.assertIsNotNone(result.ci_upper)
        # CI 应该包含统计量
        self.assertLess(result.ci_lower, result.statistic)
        self.assertGreater(result.ci_upper, result.statistic)
    
    def test_bootstrap_mean_ci(self):
        """测试均值 CI 便捷函数"""
        mean, ci_lower, ci_upper = bootstrap_mean_ci(self.data, ci=0.95, n_bootstrap=1000)
        
        self.assertIsNotNone(mean)
        self.assertIsNotNone(ci_lower)
        self.assertIsNotNone(ci_upper)
        self.assertLess(ci_lower, mean)
        self.assertGreater(ci_upper, mean)
    
    def test_bootstrap_two_groups(self):
        """测试两组比较"""
        group1 = np.random.normal(100, 15, 50).tolist()
        group2 = np.random.normal(95, 15, 50).tolist()
        
        result = bootstrap_two_groups(
            group1, group2,
            lambda x, y: np.mean(x) - np.mean(y),
            n_bootstrap=1000
        )
        
        self.assertIsNotNone(result.statistic)
        self.assertGreater(result.statistic, 0)  # group1 均值更高
    
    def test_quick_bootstrap_ci(self):
        """测试快速 Bootstrap CI"""
        result = quick_bootstrap_ci(self.data, 'mean', ci=0.95, n_bootstrap=1000)
        
        self.assertIn('statistic', result)
        self.assertIn('ci', result)
        self.assertIn('ci_level', result)


class TestMultipleComparison(unittest.TestCase):
    """测试多重比较校正"""
    
    def test_bonferroni_correction(self):
        """测试 Bonferroni 校正"""
        pvalues = [0.01, 0.02, 0.03, 0.1, 0.5]
        result = bonferroni_correction(pvalues, alpha=0.05)
        
        self.assertEqual(result.method, "Bonferroni")
        self.assertEqual(result.n_tests, 5)
        # 校正后 p 值应该更大
        for orig, adj in zip(pvalues, result.adjusted_pvalues):
            self.assertGreaterEqual(adj, orig)
    
    def test_holm_bonferroni_correction(self):
        """测试 Holm-Bonferroni 校正"""
        pvalues = [0.01, 0.02, 0.03, 0.1, 0.5]
        result = holm_bonferroni_correction(pvalues, alpha=0.05)
        
        self.assertEqual(result.method, "Holm-Bonferroni")
        # Holm 应该比 Bonferroni 更有功效
        bonferroni = bonferroni_correction(pvalues, alpha=0.05)
        self.assertGreaterEqual(
            sum(result.significant),
            sum(bonferroni.significant)
        )
    
    def test_benjamini_hochberg_correction(self):
        """测试 Benjamini-Hochberg FDR 校正"""
        pvalues = [0.01, 0.02, 0.03, 0.1, 0.5]
        result = benjamini_hochberg_correction(pvalues, alpha=0.05)
        
        self.assertEqual(result.method, "Benjamini-Hochberg (FDR)")
        # FDR 应该比 Bonferroni 更宽松
        bonferroni = bonferroni_correction(pvalues, alpha=0.05)
        self.assertGreaterEqual(
            sum(result.significant),
            sum(bonferroni.significant)
        )
    
    def test_sidak_correction(self):
        """测试 Sidak 校正"""
        pvalues = [0.01, 0.02, 0.03]
        result = sidak_correction(pvalues, alpha=0.05)
        
        self.assertEqual(result.method, "Sidak (independent tests)")
    
    def test_apply_correction(self):
        """测试通用校正函数"""
        pvalues = [0.01, 0.02, 0.03]
        
        # 测试各种方法
        for method in ['bonferroni', 'holm', 'fdr_bh', 'fdr_by', 'sidak']:
            result = apply_correction(pvalues, method, alpha=0.05)
            self.assertEqual(result.n_tests, 3)
    
    def test_compare_methods(self):
        """测试比较所有方法"""
        pvalues = [0.01, 0.02, 0.03, 0.1]
        results = compare_methods(pvalues, alpha=0.05)
        
        self.assertIn('bonferroni', results)
        self.assertIn('holm', results)
        self.assertIn('fdr_bh', results)
    
    def test_family_wise_error_rate(self):
        """测试族错误率控制"""
        # 模拟所有原假设为真的情况
        np.random.seed(42)
        n_simulations = 100
        n_tests = 10
        
        false_positives_bonferroni = 0
        false_positives_raw = 0
        
        for _ in range(n_simulations):
            # 生成随机 p 值 (原假设为真)
            pvalues = np.random.uniform(0, 1, n_tests).tolist()
            
            # Bonferroni 校正
            result = bonferroni_correction(pvalues, alpha=0.05)
            if any(result.significant):
                false_positives_bonferroni += 1
            
            # 未校正
            if any(p < 0.05 for p in pvalues):
                false_positives_raw += 1
        
        # Bonferroni 应该控制 FWER <= 5%
        fwer_bonferroni = false_positives_bonferroni / n_simulations
        self.assertLessEqual(fwer_bonferroni, 0.1)  # 允许一定波动
        
        # 未校正应该更高
        fwer_raw = false_positives_raw / n_simulations
        self.assertGreater(fwer_raw, fwer_bonferroni)


if __name__ == '__main__':
    unittest.main()