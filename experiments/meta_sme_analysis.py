"""
MOSS v7.1 - Meta-SME Statistical Analysis
Meta-SME 统计分析

统计验证 Meta-SME 的有效性
"""

import numpy as np
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from scipy import stats
import warnings
warnings.filterwarnings('ignore')


class StatisticalAnalyzer:
    """统计分析器"""
    
    def __init__(self, results_dir: str):
        self.results_dir = Path(results_dir)
        self.data = {}
        self.analysis_results = {}
    
    def load_data(self) -> Dict:
        """加载实验数据"""
        print("Loading experiment data...")
        
        # 加载汇总文件
        summary_path = self.results_dir / 'summary.json'
        if summary_path.exists():
            with open(summary_path, 'r') as f:
                self.summary = json.load(f)
        
        # 加载各组数据
        for group in ['E', 'C1', 'C2', 'C3']:
            group_files = list(self.results_dir.glob(f"{group}_*.json"))
            if group_files:
                self.data[group] = []
                for file_path in group_files:
                    with open(file_path, 'r') as f:
                        self.data[group].append(json.load(f))
                print(f"  Loaded {len(group_files)} runs for group {group}")
        
        return self.data
    
    def extract_metrics(self, group: str) -> Dict:
        """提取指标"""
        if group not in self.data:
            return {}
        
        metrics = {
            'avg_reward': [],
            'cumulative_reward': [],
            'runtime': []
        }
        
        for run in self.data[group]:
            final = run.get('final_metrics', {})
            metrics['avg_reward'].append(final.get('avg_reward', 0))
            metrics['cumulative_reward'].append(final.get('cumulative_reward', 0))
            metrics['runtime'].append(final.get('runtime_seconds', 0))
        
        return metrics
    
    def descriptive_statistics(self) -> Dict:
        """描述性统计"""
        print("\n" + "=" * 60)
        print("Descriptive Statistics")
        print("=" * 60)
        
        desc_stats = {}
        
        for group in ['E', 'C1', 'C2', 'C3']:
            if group not in self.data:
                continue
            
            metrics = self.extract_metrics(group)
            
            desc_stats[group] = {}
            for metric_name, values in metrics.items():
                if not values:
                    continue
                
                values = np.array(values)
                desc_stats[group][metric_name] = {
                    'n': len(values),
                    'mean': float(np.mean(values)),
                    'std': float(np.std(values, ddof=1)),
                    'sem': float(stats.sem(values)),
                    'median': float(np.median(values)),
                    'min': float(np.min(values)),
                    'max': float(np.max(values)),
                    'q25': float(np.percentile(values, 25)),
                    'q75': float(np.percentile(values, 75))
                }
            
            # 打印
            print(f"\nGroup {group} (n={desc_stats[group]['avg_reward']['n']}):")
            print(f"  Avg Reward: {desc_stats[group]['avg_reward']['mean']:.4f} ± "
                  f"{desc_stats[group]['avg_reward']['std']:.4f}")
            print(f"  Median: {desc_stats[group]['avg_reward']['median']:.4f}")
            print(f"  Range: [{desc_stats[group]['avg_reward']['min']:.4f}, "
                  f"{desc_stats[group]['avg_reward']['max']:.4f}]")
        
        return desc_stats
    
    def normality_test(self, group: str, metric: str = 'avg_reward') -> Dict:
        """正态性检验"""
        metrics = self.extract_metrics(group)
        values = metrics.get(metric, [])
        
        if len(values) < 3:
            return {'error': 'Insufficient data'}
        
        # Shapiro-Wilk 检验
        statistic, p_value = stats.shapiro(values)
        
        return {
            'test': 'Shapiro-Wilk',
            'statistic': float(statistic),
            'p_value': float(p_value),
            'is_normal': p_value > 0.05
        }
    
    def mann_whitney_test(self, group1: str, group2: str, 
                         metric: str = 'avg_reward') -> Dict:
        """
        Mann-Whitney U 检验 (非参数)
        
        用于比较两组独立样本
        """
        metrics1 = self.extract_metrics(group1)
        metrics2 = self.extract_metrics(group2)
        
        values1 = metrics1.get(metric, [])
        values2 = metrics2.get(metric, [])
        
        if not values1 or not values2:
            return {'error': 'Insufficient data'}
        
        # Mann-Whitney U 检验
        statistic, p_value = stats.mannwhitneyu(
            values1, values2, alternative='two-sided'
        )
        
        # 效应量 (r = Z / sqrt(N))
        n1, n2 = len(values1), len(values2)
        z_score = (statistic - n1 * n2 / 2) / np.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
        effect_size = abs(z_score) / np.sqrt(n1 + n2)
        
        # 解释效应量
        if effect_size < 0.3:
            effect_interpretation = 'small'
        elif effect_size < 0.5:
            effect_interpretation = 'medium'
        else:
            effect_interpretation = 'large'
        
        return {
            'test': 'Mann-Whitney U',
            'group1': group1,
            'group2': group2,
            'statistic': float(statistic),
            'p_value': float(p_value),
            'significant': p_value < 0.05,
            'effect_size': float(effect_size),
            'effect_interpretation': effect_interpretation,
            'n1': n1,
            'n2': n2
        }
    
    def cohens_d(self, group1: str, group2: str, 
                metric: str = 'avg_reward') -> Dict:
        """
        计算 Cohen's d 效应量
        """
        metrics1 = self.extract_metrics(group1)
        metrics2 = self.extract_metrics(group2)
        
        values1 = np.array(metrics1.get(metric, []))
        values2 = np.array(metrics2.get(metric, []))
        
        if len(values1) < 2 or len(values2) < 2:
            return {'error': 'Insufficient data'}
        
        # 合并标准差
        n1, n2 = len(values1), len(values2)
        var1 = np.var(values1, ddof=1)
        var2 = np.var(values2, ddof=1)
        
        pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
        
        # Cohen's d
        d = (np.mean(values1) - np.mean(values2)) / pooled_std if pooled_std > 0 else 0
        
        # 解释
        abs_d = abs(d)
        if abs_d < 0.2:
            interpretation = 'negligible'
        elif abs_d < 0.5:
            interpretation = 'small'
        elif abs_d < 0.8:
            interpretation = 'medium'
        else:
            interpretation = 'large'
        
        # 置信区间 (近似)
        se = np.sqrt((n1 + n2) / (n1 * n2) + d**2 / (2 * (n1 + n2)))
        ci_lower = d - 1.96 * se
        ci_upper = d + 1.96 * se
        
        return {
            'cohens_d': float(d),
            'interpretation': interpretation,
            'ci_95': [float(ci_lower), float(ci_upper)],
            'pooled_std': float(pooled_std)
        }
    
    def run_all_comparisons(self) -> Dict:
        """运行所有组间比较"""
        print("\n" + "=" * 60)
        print("Group Comparisons")
        print("=" * 60)
        
        comparisons = {}
        
        # 主要比较: E vs C1
        print("\n1. Experimental (E) vs Control 1 (C1)")
        comp = self.mann_whitney_test('E', 'C1')
        comp['cohens_d'] = self.cohens_d('E', 'C1')
        comparisons['E_vs_C1'] = comp
        
        self._print_comparison(comp)
        
        # 其他比较
        for control in ['C2', 'C3']:
            print(f"\n2. Experimental (E) vs {control}")
            comp = self.mann_whitney_test('E', control)
            comp['cohens_d'] = self.cohens_d('E', control)
            comparisons[f'E_vs_{control}'] = comp
            
            self._print_comparison(comp)
        
        return comparisons
    
    def _print_comparison(self, comp: Dict):
        """打印比较结果"""
        if 'error' in comp:
            print(f"  Error: {comp['error']}")
            return
        
        print(f"  Mann-Whitney U: {comp['statistic']:.2f}")
        print(f"  p-value: {comp['p_value']:.4f} {'***' if comp['significant'] else 'ns'}")
        print(f"  Effect size (r): {comp['effect_size']:.3f} ({comp['effect_interpretation']})")
        
        if 'cohens_d' in comp and 'error' not in comp['cohens_d']:
            d = comp['cohens_d']
            print(f"  Cohen's d: {d['cohens_d']:.3f} ({d['interpretation']})")
            print(f"  95% CI: [{d['ci_95'][0]:.3f}, {d['ci_95'][1]:.3f}]")
    
    def check_success_criteria(self, comparisons: Dict) -> Dict:
        """检查成功标准"""
        print("\n" + "=" * 60)
        print("Success Criteria Check")
        print("=" * 60)
        
        criteria = {
            'statistical_significance': False,
            'effect_size': False,
            'confidence_interval': False,
            'performance_improvement': False
        }
        
        # 主要比较 E vs C1
        if 'E_vs_C1' in comparisons and 'error' not in comparisons['E_vs_C1']:
            comp = comparisons['E_vs_C1']
            
            # 1. 统计显著性 p < 0.05
            criteria['statistical_significance'] = comp['p_value'] < 0.05
            print(f"\n1. Statistical Significance (p < 0.05):")
            print(f"   p = {comp['p_value']:.4f} {'✅ PASS' if criteria['statistical_significance'] else '❌ FAIL'}")
            
            # 2. 效应量 Cohen's d > 0.5
            if 'cohens_d' in comp and 'error' not in comp['cohens_d']:
                d = abs(comp['cohens_d']['cohens_d'])
                criteria['effect_size'] = d > 0.5
                print(f"\n2. Effect Size (Cohen's d > 0.5):")
                print(f"   d = {d:.3f} {'✅ PASS' if criteria['effect_size'] else '❌ FAIL'}")
                
                # 3. 置信区间不包含 0
                ci = comp['cohens_d']['ci_95']
                criteria['confidence_interval'] = not (ci[0] <= 0 <= ci[1])
                print(f"\n3. 95% CI excludes 0:")
                print(f"   CI = [{ci[0]:.3f}, {ci[1]:.3f}] {'✅ PASS' if criteria['confidence_interval'] else '❌ FAIL'}")
        
        # 4. 性能提升 >= 10%
        if 'E' in self.data and 'C1' in self.data:
            e_metrics = self.extract_metrics('E')
            c1_metrics = self.extract_metrics('C1')
            
            if e_metrics['avg_reward'] and c1_metrics['avg_reward']:
                e_mean = np.mean(e_metrics['avg_reward'])
                c1_mean = np.mean(c1_metrics['avg_reward'])
                
                if c1_mean > 0:
                    improvement = (e_mean - c1_mean) / c1_mean * 100
                    criteria['performance_improvement'] = improvement >= 10
                    print(f"\n4. Performance Improvement (>= 10%):")
                    print(f"   Improvement = {improvement:.1f}% {'✅ PASS' if criteria['performance_improvement'] else '❌ FAIL'}")
        
        # 总体评估
        all_passed = all(criteria.values())
        print(f"\n{'=' * 60}")
        print(f"Overall: {'✅ ALL CRITERIA PASSED' if all_passed else '❌ SOME CRITERIA FAILED'}")
        print(f"{'=' * 60}")
        
        return criteria
    
    def generate_report(self, output_path: str):
        """生成完整报告"""
        print("\nGenerating report...")
        
        # 运行所有分析
        self.load_data()
        desc_stats = self.descriptive_statistics()
        
        # 正态性检验
        normality = {}
        for group in ['E', 'C1', 'C2', 'C3']:
            if group in self.data:
                normality[group] = self.normality_test(group)
        
        # 组间比较
        comparisons = self.run_all_comparisons()
        
        # 成功标准
        criteria = self.check_success_criteria(comparisons)
        
        # 汇总报告
        report = {
            'analysis_date': str(Path(output_path).stat().st_mtime if Path(output_path).exists() else ''),
            'descriptive_statistics': desc_stats,
            'normality_tests': normality,
            'comparisons': comparisons,
            'success_criteria': {k: bool(v) for k, v in criteria.items()},
            'conclusion': {
                'all_criteria_passed': bool(all(criteria.values())),
                'meta_sme_effective': bool(comparisons.get('E_vs_C1', {}).get('significant', False))
            }
        }
        
        # 保存报告
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=lambda x: x.item() if hasattr(x, 'item') else str(x))
        
        print(f"Report saved to {output_path}")
        
        return report


def main():
    """主函数"""
    print("=" * 60)
    print("MOSS v7.1 - Meta-SME Statistical Analysis")
    print("=" * 60)
    
    # 分析结果
    results_dir = 'experiments/meta_sme_validation/results'
    output_path = 'experiments/meta_sme_validation/analysis_report.json'
    
    analyzer = StatisticalAnalyzer(results_dir)
    report = analyzer.generate_report(output_path)
    
    print("\n" + "=" * 60)
    print("Analysis Complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()