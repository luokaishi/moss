#!/usr/bin/env python3
"""
Statistical Significance Analysis
统计显著性分析

为 MVES 实验数据提供统计显著性检验
"""

import numpy as np
from scipy import stats
import json
from pathlib import Path
from datetime import datetime


class StatisticalAnalysis:
    """统计分析器"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': []
        }
    
    def t_test(self, sample1: list, sample2: list, 
               alternative: str = 'two-sided') -> dict:
        """独立样本 t 检验"""
        t_stat, p_value = stats.ttest_ind(sample1, sample2, alternative=alternative)
        
        # 计算效应量 (Cohen's d)
        pooled_std = np.sqrt((np.std(sample1)**2 + np.std(sample2)**2) / 2)
        cohens_d = (np.mean(sample1) - np.mean(sample2)) / pooled_std
        
        # 95% 置信区间
        mean_diff = np.mean(sample1) - np.mean(sample2)
        ci_low = mean_diff - 1.96 * pooled_std
        ci_high = mean_diff + 1.96 * pooled_std
        
        result = {
            'test': 'independent_t_test',
            't_statistic': float(t_stat),
            'p_value': float(p_value),
            'significant': bool(p_value < 0.05),
            'effect_size_cohens_d': float(cohens_d),
            'mean_difference': float(mean_diff),
            'confidence_interval_95': [float(ci_low), float(ci_high)],
            'interpretation': self._interpret_p_value(p_value, cohens_d)
        }
        
        self.results['tests'].append(result)
        return result
    
    def anova_test(self, *samples) -> dict:
        """单因素方差分析 (ANOVA)"""
        f_stat, p_value = stats.f_oneway(*samples)
        
        result = {
            'test': 'one_way_anova',
            'f_statistic': f_stat,
            'p_value': p_value,
            'significant': p_value < 0.05,
            'interpretation': self._interpret_p_value(p_value)
        }
        
        self.results['tests'].append(result)
        return result
    
    def correlation_test(self, x: list, y: list) -> dict:
        """皮尔逊相关系数检验"""
        corr, p_value = stats.pearsonr(x, y)
        
        result = {
            'test': 'pearson_correlation',
            'correlation_coefficient': corr,
            'p_value': p_value,
            'significant': p_value < 0.05,
            'strength': self._interpret_correlation(corr),
            'interpretation': self._interpret_p_value(p_value)
        }
        
        self.results['tests'].append(result)
        return result
    
    def chi_square_test(self, observed: list, expected: list = None) -> dict:
        """卡方检验"""
        if expected is None:
            # 拟合优度检验
            chi2, p_value = stats.chisquare(observed)
        else:
            # 独立性检验
            chi2, p_value, dof, expected = stats.chi2_contingency([observed, expected])
        
        result = {
            'test': 'chi_square',
            'chi2_statistic': chi2,
            'p_value': p_value,
            'significant': p_value < 0.05,
            'interpretation': self._interpret_p_value(p_value)
        }
        
        self.results['tests'].append(result)
        return result
    
    def _interpret_p_value(self, p_value: float, effect_size: float = None) -> str:
        """解释 p 值"""
        if p_value < 0.001:
            significance = "极显著 (p < 0.001)"
        elif p_value < 0.01:
            significance = "非常显著 (p < 0.01)"
        elif p_value < 0.05:
            significance = "显著 (p < 0.05)"
        else:
            significance = "不显著 (p >= 0.05)"
        
        if effect_size is not None:
            if abs(effect_size) < 0.2:
                effect = "效应量很小"
            elif abs(effect_size) < 0.5:
                effect = "效应量小到中等"
            elif abs(effect_size) < 0.8:
                effect = "效应量中等到大"
            else:
                effect = "效应量很大"
            return f"{significance}, {effect}"
        
        return significance
    
    def _interpret_correlation(self, corr: float) -> str:
        """解释相关系数"""
        if abs(corr) < 0.3:
            return "弱相关"
        elif abs(corr) < 0.7:
            return "中等相关"
        else:
            return "强相关"
    
    def save_results(self, output_dir: str = 'experiments/benchmarks/results'):
        """保存结果"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'statistical_analysis_{timestamp}.json'
        filepath = output_path / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        return filepath


def main():
    print("=" * 60)
    print("统计显著性分析")
    print("=" * 60)
    
    analyzer = StatisticalAnalysis()
    
    # 示例：100 Agent vs 1000 Agent 协作效率对比
    print("\n1. 独立样本 t 检验 (100 Agent vs 1000 Agent)...")
    sample_100 = np.random.normal(0.85, 0.05, 100)  # 100 Agent 效率
    sample_1000 = np.random.normal(0.87, 0.03, 100)  # 1000 Agent 效率
    
    t_result = analyzer.t_test(sample_100, sample_1000)
    print(f"   t 统计量：{t_result['t_statistic']:.3f}")
    print(f"   p 值：{t_result['p_value']:.4f}")
    print(f"   效应量 (Cohen's d): {t_result['effect_size_cohens_d']:.3f}")
    print(f"   95% CI: [{t_result['confidence_interval_95'][0]:.3f}, {t_result['confidence_interval_95'][1]:.3f}]")
    print(f"   解释：{t_result['interpretation']}")
    
    # 示例：多组协作效率对比 (ANOVA)
    print("\n2. 单因素方差分析 (多组对比)...")
    group_10 = np.random.normal(0.75, 0.08, 50)
    group_100 = np.random.normal(0.85, 0.05, 50)
    group_1000 = np.random.normal(0.87, 0.03, 50)
    
    anova_result = analyzer.anova_test(group_10, group_100, group_1000)
    print(f"   F 统计量：{anova_result['f_statistic']:.3f}")
    print(f"   p 值：{anova_result['p_value']:.4f}")
    print(f"   解释：{anova_result['interpretation']}")
    
    # 示例：任务完成率与协作效率相关性
    print("\n3. 皮尔逊相关系数检验...")
    completion_rate = np.random.uniform(0.8, 1.0, 100)
    efficiency = 0.5 + 0.5 * completion_rate + np.random.normal(0, 0.1, 100)
    
    corr_result = analyzer.correlation_test(completion_rate, efficiency)
    print(f"   相关系数：{corr_result['correlation_coefficient']:.3f}")
    print(f"   p 值：{corr_result['p_value']:.4f}")
    print(f"   强度：{corr_result['strength']}")
    print(f"   解释：{corr_result['interpretation']}")
    
    # 保存结果
    filepath = analyzer.save_results()
    print(f"\n💾 结果已保存：{filepath}")
    
    print("\n" + "=" * 60)
    print("✅ 统计显著性分析完成!")
    print("=" * 60)


if __name__ == '__main__':
    main()
