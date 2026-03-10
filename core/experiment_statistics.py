"""
MOSS Experiment Statistics
实验统计分析 - 回应Copilot评估

实现: 多次重复、置信区间、显著性检验
"""

import numpy as np
from typing import Dict, List, Tuple
from scipy import stats
import json
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ExperimentResult:
    """实验结果数据类"""
    name: str
    values: List[float]
    unit: str = ""
    
    def mean(self) -> float:
        return np.mean(self.values)
    
    def std(self) -> float:
        return np.std(self.values, ddof=1)
    
    def ci_95(self) -> Tuple[float, float]:
        """95%置信区间"""
        mean = self.mean()
        sem = stats.sem(self.values)
        ci = stats.t.interval(0.95, len(self.values)-1, loc=mean, scale=sem)
        return ci
    
    def min(self) -> float:
        return np.min(self.values)
    
    def max(self) -> float:
        return np.max(self.values)


class ExperimentStatistics:
    """实验统计分析器"""
    
    def __init__(self):
        self.results = {}
    
    def add_result(self, name: str, values: List[float], unit: str = ""):
        """添加实验结果"""
        self.results[name] = ExperimentResult(name, values, unit)
    
    def compare_with_baseline(self, experiment_name: str, baseline_name: str) -> Dict:
        """
        与基线对比
        
        Returns:
            对比统计结果
        """
        if experiment_name not in self.results or baseline_name not in self.results:
            return {'error': 'Missing data for comparison'}
        
        exp = self.results[experiment_name]
        baseline = self.results[baseline_name]
        
        # t检验
        t_stat, p_value = stats.ttest_ind(exp.values, baseline.values)
        
        # 效应量 (Cohen's d)
        pooled_std = np.sqrt((np.var(exp.values, ddof=1) + np.var(baseline.values, ddof=1)) / 2)
        cohens_d = (exp.mean() - baseline.mean()) / pooled_std if pooled_std > 0 else 0
        
        # 相对改进
        relative_improvement = (exp.mean() - baseline.mean()) / baseline.mean() * 100
        
        return {
            'experiment': experiment_name,
            'baseline': baseline_name,
            'experiment_mean': exp.mean(),
            'baseline_mean': baseline.mean(),
            'relative_improvement': relative_improvement,
            't_statistic': t_stat,
            'p_value': p_value,
            'cohens_d': cohens_d,
            'significant': p_value < 0.05,
            'effect_size': 'large' if abs(cohens_d) > 0.8 else 'medium' if abs(cohens_d) > 0.5 else 'small'
        }
    
    def generate_report(self) -> Dict:
        """生成完整统计报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'experiments': {},
            'comparisons': {}
        }
        
        # 每个实验的统计
        for name, result in self.results.items():
            ci_low, ci_high = result.ci_95()
            
            report['experiments'][name] = {
                'n': len(result.values),
                'mean': result.mean(),
                'std': result.std(),
                'min': result.min(),
                'max': result.max(),
                'ci_95_low': ci_low,
                'ci_95_high': ci_high,
                'unit': result.unit,
                'raw_values': result.values
            }
        
        return report
    
    def calculate_survival_rate(self, survival_times: List[int], max_steps: int) -> Dict:
        """
        计算生存率
        
        Args:
            survival_times: 每次实验的生存步数
            max_steps: 最大步数
        
        Returns:
            生存率统计
        """
        survived = [t for t in survival_times if t >= max_steps]
        survival_rate = len(survived) / len(survival_times)
        
        # 置信区间
        ci = stats.binom.interval(0.95, len(survival_times), survival_rate)
        
        return {
            'max_steps': max_steps,
            'total_runs': len(survival_times),
            'survived_count': len(survived),
            'survival_rate': survival_rate,
            'ci_95_low': ci[0] / len(survival_times),
            'ci_95_high': ci[1] / len(survival_times),
            'mean_survival_time': np.mean(survival_times),
            'median_survival_time': np.median(survival_times)
        }


def demo_experiment_statistics():
    """演示实验统计"""
    print("="*70)
    print("MOSS EXPERIMENT STATISTICS DEMO")
    print("="*70)
    print()
    
    stats_analyzer = ExperimentStatistics()
    
    # 模拟MOSS实验结果 (10次重复)
    moss_rewards = [11.2, 11.5, 11.0, 11.8, 11.3, 11.6, 11.1, 11.4, 11.7, 11.2]
    stats_analyzer.add_result('MOSS', moss_rewards, 'reward')
    
    # 模拟ReAct基线结果
    react_rewards = [10.8, 9.5, 11.2, 8.9, 10.5, 9.8, 11.0, 9.2, 10.6, 9.9]
    stats_analyzer.add_result('ReAct', react_rewards, 'reward')
    
    # 模拟生存时间
    moss_survival = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100]  # 全部存活
    react_survival = [85, 92, 100, 78, 95, 88, 100, 82, 94, 90]  # 部分存活
    
    print("1. REWARD STATISTICS")
    print("-"*70)
    
    for name in ['MOSS', 'ReAct']:
        result = stats_analyzer.results[name]
        ci_low, ci_high = result.ci_95()
        
        print(f"\n{name}:")
        print(f"  Mean: {result.mean():.3f} ± {result.std():.3f}")
        print(f"  95% CI: [{ci_low:.3f}, {ci_high:.3f}]")
        print(f"  Range: [{result.min():.3f}, {result.max():.3f}]")
        print(f"  N: {len(result.values)}")
    
    print("\n2. COMPARISON WITH BASELINE")
    print("-"*70)
    
    comparison = stats_analyzer.compare_with_baseline('MOSS', 'ReAct')
    
    print(f"\nMOSS vs ReAct:")
    print(f"  Relative improvement: {comparison['relative_improvement']:+.1f}%")
    print(f"  t-statistic: {comparison['t_statistic']:.3f}")
    print(f"  p-value: {comparison['p_value']:.4f}")
    print(f"  Significant: {'Yes' if comparison['significant'] else 'No'} (α=0.05)")
    print(f"  Effect size (Cohen's d): {comparison['cohens_d']:.3f} ({comparison['effect_size']})")
    
    print("\n3. SURVIVAL RATE ANALYSIS")
    print("-"*70)
    
    moss_survival_stats = stats_analyzer.calculate_survival_rate(moss_survival, 100)
    react_survival_stats = stats_analyzer.calculate_survival_rate(react_survival, 100)
    
    print(f"\nMOSS (100 steps max):")
    print(f"  Survival rate: {moss_survival_stats['survival_rate']:.1%}")
    print(f"  95% CI: [{moss_survival_stats['ci_95_low']:.1%}, {moss_survival_stats['ci_95_high']:.1%}]")
    
    print(f"\nReAct (100 steps max):")
    print(f"  Survival rate: {react_survival_stats['survival_rate']:.1%}")
    print(f"  95% CI: [{react_survival_stats['ci_95_low']:.1%}, {react_survival_stats['ci_95_high']:.1%}]")
    
    print("\n4. FULL REPORT")
    print("-"*70)
    
    report = stats_analyzer.generate_report()
    report['comparisons'] = {'MOSS_vs_ReAct': comparison}
    report['survival_analysis'] = {
        'MOSS': moss_survival_stats,
        'ReAct': react_survival_stats
    }
    
    print(json.dumps(report, indent=2, default=str))
    
    # 保存报告
    filename = f"experiment_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n✅ Report saved to: {filename}")


if __name__ == '__main__':
    demo_experiment_statistics()
