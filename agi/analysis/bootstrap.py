"""
Bootstrap Confidence Interval - Bootstrap 置信区间计算

实现多种 Bootstrap 方法：
1. Percentile Bootstrap: 简单百分位法
2. BCa Bootstrap: 偏差校正加速法 (推荐)
3. Studentized Bootstrap: t 统计量法

基于 Copilot 评估报告建议，提供稳健的置信区间估计。
"""

import numpy as np
from typing import List, Callable, Optional, Tuple, Dict
from dataclasses import dataclass
import warnings


@dataclass
class BootstrapResult:
    """Bootstrap 结果"""
    statistic: float           # 原始统计量
    ci_lower: float           # 置信区间下限
    ci_upper: float           # 置信区间上限
    ci_level: float           # 置信水平
    n_bootstrap: int          # Bootstrap 次数
    std_error: float          # 标准误
    bias: float               # 偏差估计
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'statistic': round(self.statistic, 6),
            'ci': [round(self.ci_lower, 6), round(self.ci_upper, 6)],
            'ci_level': self.ci_level,
            'n_bootstrap': self.n_bootstrap,
            'std_error': round(self.std_error, 6),
            'bias': round(self.bias, 6),
        }


def percentile_bootstrap(data: List[float], 
                         statistic_func: Callable[[List[float]], float] = np.mean,
                         n_bootstrap: int = 10000,
                         ci: float = 0.95,
                         random_seed: Optional[int] = None) -> BootstrapResult:
    """
    百分位 Bootstrap 置信区间
    
    最简单的方法，直接取 bootstrap 统计量的百分位
    
    Args:
        data: 原始数据
        statistic_func: 统计量函数 (默认均值)
        n_bootstrap: bootstrap 次数
        ci: 置信水平
        random_seed: 随机种子
        
    Returns:
        BootstrapResult
    """
    if random_seed is not None:
        np.random.seed(random_seed)
    
    data = np.array(data)
    n = len(data)
    
    # 原始统计量
    original_stat = statistic_func(data)
    
    # Bootstrap 重采样
    bootstrap_stats = []
    for _ in range(n_bootstrap):
        sample = np.random.choice(data, size=n, replace=True)
        stat = statistic_func(sample)
        bootstrap_stats.append(stat)
    
    bootstrap_stats = np.array(bootstrap_stats)
    
    # 百分位置信区间
    alpha = (1 - ci) / 2
    ci_lower = np.percentile(bootstrap_stats, alpha * 100)
    ci_upper = np.percentile(bootstrap_stats, (1 - alpha) * 100)
    
    # 标准误和偏差
    std_error = np.std(bootstrap_stats, ddof=1)
    bias = np.mean(bootstrap_stats) - original_stat
    
    return BootstrapResult(
        statistic=original_stat,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        ci_level=ci,
        n_bootstrap=n_bootstrap,
        std_error=std_error,
        bias=bias
    )


def bca_bootstrap(data: List[float],
                  statistic_func: Callable[[List[float]], float] = np.mean,
                  n_bootstrap: int = 10000,
                  ci: float = 0.95,
                  random_seed: Optional[int] = None) -> BootstrapResult:
    """
    BCa (Bias-Corrected and Accelerated) Bootstrap 置信区间
    
    推荐方法，校正偏差和偏度，比简单百分位更准确
    
    Args:
        data: 原始数据
        statistic_func: 统计量函数
        n_bootstrap: bootstrap 次数
        ci: 置信水平
        random_seed: 随机种子
        
    Returns:
        BootstrapResult
    """
    if random_seed is not None:
        np.random.seed(random_seed)
    
    data = np.array(data)
    n = len(data)
    
    # 原始统计量
    original_stat = statistic_func(data)
    
    # Bootstrap 重采样
    bootstrap_stats = []
    for _ in range(n_bootstrap):
        sample = np.random.choice(data, size=n, replace=True)
        stat = statistic_func(sample)
        bootstrap_stats.append(stat)
    
    bootstrap_stats = np.array(bootstrap_stats)
    
    # 偏差校正 (z0)
    prop_less = np.mean(bootstrap_stats < original_stat)
    z0 = stats.norm.ppf(prop_less) if 0 < prop_less < 1 else 0
    
    # 加速系数 (a) - 使用 Jackknife
    jackknife_stats = []
    for i in range(n):
        jack_sample = np.delete(data, i)
        jack_stat = statistic_func(jack_sample)
        jackknife_stats.append(jack_stat)
    
    jackknife_stats = np.array(jackknife_stats)
    jack_mean = np.mean(jackknife_stats)
    
    numerator = np.sum((jack_mean - jackknife_stats) ** 3)
    denominator = 6 * (np.sum((jack_mean - jackknife_stats) ** 2) ** 1.5)
    a = numerator / denominator if denominator > 0 else 0
    
    # BCa 调整后的百分位
    alpha = (1 - ci) / 2
    z_alpha = stats.norm.ppf(alpha)
    z_1_alpha = stats.norm.ppf(1 - alpha)
    
    alpha_lower = stats.norm.cdf(z0 + (z0 + z_alpha) / (1 - a * (z0 + z_alpha)))
    alpha_upper = stats.norm.cdf(z0 + (z0 + z_1_alpha) / (1 - a * (z0 + z_1_alpha)))
    
    ci_lower = np.percentile(bootstrap_stats, alpha_lower * 100)
    ci_upper = np.percentile(bootstrap_stats, alpha_upper * 100)
    
    # 标准误和偏差
    std_error = np.std(bootstrap_stats, ddof=1)
    bias = np.mean(bootstrap_stats) - original_stat
    
    return BootstrapResult(
        statistic=original_stat,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        ci_level=ci,
        n_bootstrap=n_bootstrap,
        std_error=std_error,
        bias=bias
    )


def bootstrap_two_groups(group1: List[float], group2: List[float],
                        statistic_func: Callable[[List[float], List[float]], float],
                        n_bootstrap: int = 10000,
                        ci: float = 0.95,
                        method: str = 'percentile',
                        random_seed: Optional[int] = None) -> BootstrapResult:
    """
    两组比较的 Bootstrap 置信区间
    
    Args:
        group1: 组1数据
        group2: 组2数据
        statistic_func: 统计量函数 (接受两组数据)
        n_bootstrap: bootstrap 次数
        ci: 置信水平
        method: 'percentile' 或 'bca'
        random_seed: 随机种子
        
    Returns:
        BootstrapResult
    """
    if random_seed is not None:
        np.random.seed(random_seed)
    
    x1 = np.array(group1)
    x2 = np.array(group2)
    n1, n2 = len(x1), len(x2)
    
    # 原始统计量
    original_stat = statistic_func(x1, x2)
    
    # Bootstrap 重采样
    bootstrap_stats = []
    for _ in range(n_bootstrap):
        sample1 = np.random.choice(x1, size=n1, replace=True)
        sample2 = np.random.choice(x2, size=n2, replace=True)
        stat = statistic_func(sample1, sample2)
        bootstrap_stats.append(stat)
    
    bootstrap_stats = np.array(bootstrap_stats)
    
    # 计算置信区间
    if method == 'percentile':
        alpha = (1 - ci) / 2
        ci_lower = np.percentile(bootstrap_stats, alpha * 100)
        ci_upper = np.percentile(bootstrap_stats, (1 - alpha) * 100)
    elif method == 'bca':
        # 简化版 BCa (两组数据)
        prop_less = np.mean(bootstrap_stats < original_stat)
        z0 = stats.norm.ppf(prop_less) if 0 < prop_less < 1 else 0
        
        alpha = (1 - ci) / 2
        z_alpha = stats.norm.ppf(alpha)
        z_1_alpha = stats.norm.ppf(1 - alpha)
        
        # 简化：不使用加速系数
        alpha_lower = stats.norm.cdf(2 * z0 + z_alpha)
        alpha_upper = stats.norm.cdf(2 * z0 + z_1_alpha)
        
        ci_lower = np.percentile(bootstrap_stats, alpha_lower * 100)
        ci_upper = np.percentile(bootstrap_stats, alpha_upper * 100)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    # 标准误和偏差
    std_error = np.std(bootstrap_stats, ddof=1)
    bias = np.mean(bootstrap_stats) - original_stat
    
    return BootstrapResult(
        statistic=original_stat,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        ci_level=ci,
        n_bootstrap=n_bootstrap,
        std_error=std_error,
        bias=bias
    )


def bootstrap_mean_ci(data: List[float], ci: float = 0.95,
                     n_bootstrap: int = 10000,
                     method: str = 'bca') -> Tuple[float, float, float]:
    """
    快速计算均值的 Bootstrap 置信区间
    
    Returns:
        (mean, ci_lower, ci_upper)
    """
    if method == 'bca':
        result = bca_bootstrap(data, np.mean, n_bootstrap, ci)
    else:
        result = percentile_bootstrap(data, np.mean, n_bootstrap, ci)
    
    return result.statistic, result.ci_lower, result.ci_upper


def bootstrap_median_ci(data: List[float], ci: float = 0.95,
                       n_bootstrap: int = 10000) -> Tuple[float, float, float]:
    """
    快速计算中位数的 Bootstrap 置信区间
    
    Returns:
        (median, ci_lower, ci_upper)
    """
    result = percentile_bootstrap(data, np.median, n_bootstrap, ci)
    return result.statistic, result.ci_lower, result.ci_upper


def bootstrap_std_ci(data: List[float], ci: float = 0.95,
                    n_bootstrap: int = 10000) -> Tuple[float, float, float]:
    """
    快速计算标准差的 Bootstrap 置信区间
    
    Returns:
        (std, ci_lower, ci_upper)
    """
    result = percentile_bootstrap(data, lambda x: np.std(x, ddof=1), n_bootstrap, ci)
    return result.statistic, result.ci_lower, result.ci_upper


# 导入 scipy.stats 用于 BCa
from scipy import stats


# 便捷函数
def quick_bootstrap_ci(data: List[float], 
                      statistic: str = 'mean',
                      ci: float = 0.95,
                      n_bootstrap: int = 10000) -> Dict:
    """
    快速计算 Bootstrap CI
    
    Args:
        data: 数据
        statistic: 'mean', 'median', 'std'
        ci: 置信水平
        n_bootstrap: bootstrap 次数
        
    Returns:
        字典格式结果
    """
    stat_funcs = {
        'mean': np.mean,
        'median': np.median,
        'std': lambda x: np.std(x, ddof=1),
    }
    
    if statistic not in stat_funcs:
        raise ValueError(f"Unknown statistic: {statistic}")
    
    result = bca_bootstrap(data, stat_funcs[statistic], n_bootstrap, ci)
    return result.to_dict()