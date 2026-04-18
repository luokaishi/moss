"""
Effect Size Calculation - 效应量计算模块

实现标准效应量指标：
1. Cohen's d: 标准均值差异效应量
2. Hedge's g: Cohen's d 的小样本校正版本
3. Glass's delta: 使用对照组标准差
4. r (相关系数): 从 t 统计量转换

基于 Copilot 评估报告建议，提升统计报告严谨性。
"""

import numpy as np
from typing import List, Union, Optional, Dict, Tuple
from dataclasses import dataclass
from scipy import stats


@dataclass
class EffectSizeResult:
    """效应量计算结果"""
    metric: str              # 效应量指标名称
    value: float             # 效应量值
    ci_lower: float          # 置信区间下限
    ci_upper: float          # 置信区间上限
    interpretation: str      # 解释 (小/中/大效应)
    
    # 额外统计
    n1: int                  # 组1样本量
    n2: int                  # 组2样本量
    pooled_sd: Optional[float] = None  # 合并标准差
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'metric': self.metric,
            'value': round(self.value, 4),
            'ci_95': [round(self.ci_lower, 4), round(self.ci_upper, 4)],
            'interpretation': self.interpretation,
            'n1': self.n1,
            'n2': self.n2,
            'pooled_sd': round(self.pooled_sd, 4) if self.pooled_sd else None,
        }


def cohens_d(group1: List[float], group2: List[float], 
             ci: float = 0.95) -> EffectSizeResult:
    """
    计算 Cohen's d 效应量
    
    Cohen's d = (M1 - M2) / Sp
    其中 Sp 是合并标准差
    
    解释标准:
    - |d| < 0.2: 可忽略
    - 0.2 <= |d| < 0.5: 小效应
    - 0.5 <= |d| < 0.8: 中效应
    - |d| >= 0.8: 大效应
    
    Args:
        group1: 组1数据
        group2: 组2数据
        ci: 置信水平 (默认 0.95)
        
    Returns:
        EffectSizeResult
    """
    x1 = np.array(group1)
    x2 = np.array(group2)
    
    n1, n2 = len(x1), len(x2)
    
    # 均值
    m1, m2 = np.mean(x1), np.mean(x2)
    
    # 标准差
    sd1, sd2 = np.std(x1, ddof=1), np.std(x2, ddof=1)
    
    # 合并标准差 (pooled SD)
    pooled_sd = np.sqrt(((n1 - 1) * sd1**2 + (n2 - 1) * sd2**2) / (n1 + n2 - 2))
    
    # Cohen's d
    d = (m1 - m2) / pooled_sd if pooled_sd > 0 else 0.0
    
    # 置信区间 (使用近似公式)
    se = np.sqrt((n1 + n2) / (n1 * n2) + d**2 / (2 * (n1 + n2)))
    z = stats.norm.ppf((1 + ci) / 2)
    ci_lower = d - z * se
    ci_upper = d + z * se
    
    return EffectSizeResult(
        metric="Cohen's d",
        value=d,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        interpretation=_interpret_cohens_d(d),
        n1=n1,
        n2=n2,
        pooled_sd=pooled_sd
    )


def hedges_g(group1: List[float], group2: List[float],
             ci: float = 0.95) -> EffectSizeResult:
    """
    计算 Hedge's g 效应量 (Cohen's d 的小样本校正)
    
    Hedge's g = Cohen's d * (1 - 3 / (4 * (n1 + n2) - 9))
    
    适用于小样本 (n < 20)，提供无偏估计
    
    Args:
        group1: 组1数据
        group2: 组2数据
        ci: 置信水平
        
    Returns:
        EffectSizeResult
    """
    # 先计算 Cohen's d
    d_result = cohens_d(group1, group2, ci)
    d = d_result.value
    n1, n2 = d_result.n1, d_result.n2
    
    # Hedge's g 校正因子
    correction = 1 - 3 / (4 * (n1 + n2) - 9)
    g = d * correction
    
    # 校正置信区间
    ci_lower = d_result.ci_lower * correction
    ci_upper = d_result.ci_upper * correction
    
    return EffectSizeResult(
        metric="Hedge's g",
        value=g,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        interpretation=_interpret_cohens_d(g),  # 使用相同解释标准
        n1=n1,
        n2=n2,
        pooled_sd=d_result.pooled_sd
    )


def glass_delta(group1: List[float], group2: List[float],
                ci: float = 0.95, use_group2_sd: bool = True) -> EffectSizeResult:
    """
    计算 Glass's delta 效应量
    
    Glass's delta = (M1 - M2) / SD_control
    
    使用对照组标准差，适用于实验组和对照组方差不等的情况
    
    Args:
        group1: 组1数据 (实验组)
        group2: 组2数据 (对照组)
        ci: 置信水平
        use_group2_sd: 是否使用组2作为对照组
        
    Returns:
        EffectSizeResult
    """
    x1 = np.array(group1)
    x2 = np.array(group2)
    
    n1, n2 = len(x1), len(x2)
    m1, m2 = np.mean(x1), np.mean(x2)
    
    # 使用对照组标准差
    if use_group2_sd:
        control_sd = np.std(x2, ddof=1)
        delta = (m1 - m2) / control_sd if control_sd > 0 else 0.0
    else:
        control_sd = np.std(x1, ddof=1)
        delta = (m2 - m1) / control_sd if control_sd > 0 else 0.0
    
    # 置信区间 (近似)
    se = delta * np.sqrt(1 / (2 * (n1 if not use_group2_sd else n2)))
    z = stats.norm.ppf((1 + ci) / 2)
    ci_lower = delta - z * se
    ci_upper = delta + z * se
    
    return EffectSizeResult(
        metric="Glass's delta",
        value=delta,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        interpretation=_interpret_cohens_d(delta),  # 使用相同解释标准
        n1=n1,
        n2=n2,
        pooled_sd=control_sd
    )


def r_from_t(t: float, df: int, ci: float = 0.95) -> EffectSizeResult:
    """
    从 t 统计量计算效应量 r
    
    r = sqrt(t^2 / (t^2 + df))
    
    解释标准:
    - |r| < 0.1: 可忽略
    - 0.1 <= |r| < 0.3: 小效应
    - 0.3 <= |r| < 0.5: 中效应
    - |r| >= 0.5: 大效应
    
    Args:
        t: t 统计量
        df: 自由度
        ci: 置信水平
        
    Returns:
        EffectSizeResult
    """
    r = np.sqrt(t**2 / (t**2 + df))
    if t < 0:
        r = -r
    
    # 置信区间 (使用 Fisher z 转换)
    z_r = np.arctanh(r)
    se_z = 1 / np.sqrt(df - 1)
    z_crit = stats.norm.ppf((1 + ci) / 2)
    
    ci_lower_z = z_r - z_crit * se_z
    ci_upper_z = z_r + z_crit * se_z
    
    ci_lower = np.tanh(ci_lower_z)
    ci_upper = np.tanh(ci_upper_z)
    
    return EffectSizeResult(
        metric="r (correlation)",
        value=r,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        interpretation=_interpret_r(r),
        n1=df + 2,  # 近似
        n2=0,
        pooled_sd=None
    )


def _interpret_cohens_d(d: float) -> str:
    """解释 Cohen's d 效应量"""
    abs_d = abs(d)
    if abs_d < 0.2:
        return "可忽略 (negligible)"
    elif abs_d < 0.5:
        return "小效应 (small)"
    elif abs_d < 0.8:
        return "中效应 (medium)"
    else:
        return "大效应 (large)"


def _interpret_r(r: float) -> str:
    """解释相关系数 r"""
    abs_r = abs(r)
    if abs_r < 0.1:
        return "可忽略 (negligible)"
    elif abs_r < 0.3:
        return "小效应 (small)"
    elif abs_r < 0.5:
        return "中效应 (medium)"
    else:
        return "大效应 (large)"


def compare_to_baseline(values: List[float], baseline: float,
                       ci: float = 0.95) -> EffectSizeResult:
    """
    与基线值比较的单样本效应量
    
    Cohen's d = (M - baseline) / SD
    
    Args:
        values: 样本数据
        baseline: 基线值
        ci: 置信水平
        
    Returns:
        EffectSizeResult
    """
    x = np.array(values)
    n = len(x)
    
    m = np.mean(x)
    sd = np.std(x, ddof=1)
    
    d = (m - baseline) / sd if sd > 0 else 0.0
    
    # 置信区间
    se = np.sqrt(1 / n + d**2 / (2 * n))
    z = stats.norm.ppf((1 + ci) / 2)
    ci_lower = d - z * se
    ci_upper = d + z * se
    
    return EffectSizeResult(
        metric="Cohen's d (one-sample)",
        value=d,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        interpretation=_interpret_cohens_d(d),
        n1=n,
        n2=0,
        pooled_sd=sd
    )


def pooled_standard_deviation(group1: List[float], group2: List[float]) -> float:
    """
    计算合并标准差
    
    Sp = sqrt(((n1-1)*SD1^2 + (n2-1)*SD2^2) / (n1+n2-2))
    """
    x1 = np.array(group1)
    x2 = np.array(group2)
    
    n1, n2 = len(x1), len(x2)
    var1 = np.var(x1, ddof=1)
    var2 = np.var(x2, ddof=1)
    
    pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
    return np.sqrt(pooled_var)


def effect_size_summary(group1: List[float], group2: List[float],
                       ci: float = 0.95) -> Dict:
    """
    计算所有效应量指标的摘要
    
    Returns:
        {
            'cohens_d': EffectSizeResult,
            'hedges_g': EffectSizeResult,
            'glass_delta': EffectSizeResult,
        }
    """
    return {
        'cohens_d': cohens_d(group1, group2, ci),
        'hedges_g': hedges_g(group1, group2, ci),
        'glass_delta': glass_delta(group1, group2, ci),
    }


# 便捷函数: 快速计算并返回字典格式
def quick_effect_size(group1: List[float], group2: List[float],
                     metric: str = 'cohens_d') -> Dict:
    """
    快速计算效应量
    
    Args:
        group1: 组1数据
        group2: 组2数据
        metric: 'cohens_d', 'hedges_g', 'glass_delta'
        
    Returns:
        字典格式的结果
    """
    if metric == 'cohens_d':
        result = cohens_d(group1, group2)
    elif metric == 'hedges_g':
        result = hedges_g(group1, group2)
    elif metric == 'glass_delta':
        result = glass_delta(group1, group2)
    else:
        raise ValueError(f"Unknown metric: {metric}")
    
    return result.to_dict()