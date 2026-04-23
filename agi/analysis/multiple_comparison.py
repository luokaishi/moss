"""
Multiple Comparison Correction - 多重比较校正

实现标准多重比较校正方法：
1. Bonferroni: 最保守，控制族错误率
2. Holm-Bonferroni: 逐步校正，比 Bonferroni 更有功效
3. Benjamini-Hochberg (FDR): 控制错误发现率
4. Benjamini-Yekutieli: 处理相关检验的 FDR

基于 Copilot 评估报告建议，防止"试到显著为止"的假阳性。
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from scipy import stats


@dataclass
class CorrectionResult:
    """校正结果"""
    method: str                    # 校正方法
    original_pvalues: List[float]  # 原始 p 值
    adjusted_pvalues: List[float]  # 校正后 p 值
    significant: List[bool]        # 是否显著
    alpha: float                   # 显著性水平
    n_tests: int                   # 检验次数
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'method': self.method,
            'alpha': self.alpha,
            'n_tests': self.n_tests,
            'results': [
                {
                    'original_p': round(p, 6),
                    'adjusted_p': round(ap, 6),
                    'significant': sig
                }
                for p, ap, sig in zip(self.original_pvalues, self.adjusted_pvalues, self.significant)
            ],
            'n_significant': sum(self.significant),
        }


def bonferroni_correction(pvalues: List[float], alpha: float = 0.05) -> CorrectionResult:
    """
    Bonferroni 校正
    
    最保守的方法，将 alpha 除以检验次数
    
    adjusted_p = min(p * m, 1.0)
    
    其中 m 是检验次数
    
    Args:
        pvalues: 原始 p 值列表
        alpha: 显著性水平
        
    Returns:
        CorrectionResult
    """
    m = len(pvalues)
    pvalues = np.array(pvalues)
    
    # Bonferroni 校正
    adjusted = np.minimum(pvalues * m, 1.0)
    
    # 判断是否显著
    significant = adjusted < alpha
    
    return CorrectionResult(
        method="Bonferroni",
        original_pvalues=pvalues.tolist(),
        adjusted_pvalues=adjusted.tolist(),
        significant=significant.tolist(),
        alpha=alpha,
        n_tests=m
    )


def holm_bonferroni_correction(pvalues: List[float], alpha: float = 0.05) -> CorrectionResult:
    """
    Holm-Bonferroni 逐步校正
    
    比 Bonferroni 更有功效，同时控制族错误率
    
    步骤:
    1. 将 p 值排序
    2. 找到最大的 k 使得 p(k) <= alpha / (m - k + 1)
    3. 拒绝所有 p <= p(k) 的假设
    
    Args:
        pvalues: 原始 p 值列表
        alpha: 显著性水平
        
    Returns:
        CorrectionResult
    """
    m = len(pvalues)
    pvalues = np.array(pvalues)
    
    # 排序并记录原始索引
    sorted_indices = np.argsort(pvalues)
    sorted_pvalues = pvalues[sorted_indices]
    
    # Holm 校正
    adjusted = np.zeros(m)
    max_adj = 0
    
    for i in range(m):
        # 从大到小计算
        idx = m - 1 - i
        raw_adjusted = sorted_pvalues[idx] * (i + 1)
        max_adj = max(max_adj, raw_adjusted)
        adjusted[idx] = min(max_adj, 1.0)
    
    # 恢复原始顺序
    adjusted_original = np.zeros(m)
    adjusted_original[sorted_indices] = adjusted
    
    # 判断是否显著 (Holm 方法)
    significant = np.zeros(m, dtype=bool)
    for i in range(m):
        if sorted_pvalues[i] <= alpha / (m - i):
            significant[sorted_indices[i]] = True
        else:
            break
    
    return CorrectionResult(
        method="Holm-Bonferroni",
        original_pvalues=pvalues.tolist(),
        adjusted_pvalues=adjusted_original.tolist(),
        significant=significant.tolist(),
        alpha=alpha,
        n_tests=m
    )


def benjamini_hochberg_correction(pvalues: List[float], alpha: float = 0.05) -> CorrectionResult:
    """
    Benjamini-Hochberg FDR 校正
    
    控制错误发现率 (False Discovery Rate)，比 Bonferroni 更宽松
    
    步骤:
    1. 将 p 值排序
    2. 找到最大的 k 使得 p(k) <= (k / m) * alpha
    3. 拒绝所有 p <= p(k) 的假设
    
    Args:
        pvalues: 原始 p 值列表
        alpha: 显著性水平 (FDR 水平)
        
    Returns:
        CorrectionResult
    """
    m = len(pvalues)
    pvalues = np.array(pvalues)
    
    # 排序并记录原始索引
    sorted_indices = np.argsort(pvalues)
    sorted_pvalues = pvalues[sorted_indices]
    
    # BH 校正
    adjusted = np.zeros(m)
    for i in range(m):
        # 从大到小
        idx = m - 1 - i
        rank = idx + 1
        adjusted[idx] = min(sorted_pvalues[idx] * m / rank, 1.0)
    
    # 单调性约束
    for i in range(1, m):
        adjusted[i] = min(adjusted[i], adjusted[i-1])
    
    # 恢复原始顺序
    adjusted_original = np.zeros(m)
    adjusted_original[sorted_indices] = adjusted
    
    # 判断是否显著 (BH 方法)
    significant = np.zeros(m, dtype=bool)
    max_k = -1
    for i in range(m):
        rank = i + 1
        if sorted_pvalues[i] <= (rank / m) * alpha:
            max_k = i
    
    if max_k >= 0:
        for i in range(max_k + 1):
            significant[sorted_indices[i]] = True
    
    return CorrectionResult(
        method="Benjamini-Hochberg (FDR)",
        original_pvalues=pvalues.tolist(),
        adjusted_pvalues=adjusted_original.tolist(),
        significant=significant.tolist(),
        alpha=alpha,
        n_tests=m
    )


def benjamini_yekutieli_correction(pvalues: List[float], alpha: float = 0.05) -> CorrectionResult:
    """
    Benjamini-Yekutieli FDR 校正
    
    处理相关检验的 FDR 校正，适用于检验间存在相关性的情况
    
    Args:
        pvalues: 原始 p 值列表
        alpha: 显著性水平
        
    Returns:
        CorrectionResult
    """
    m = len(pvalues)
    pvalues = np.array(pvalues)
    
    # 计算调和数
    harmonic_sum = np.sum(1 / np.arange(1, m + 1))
    
    # 排序并记录原始索引
    sorted_indices = np.argsort(pvalues)
    sorted_pvalues = pvalues[sorted_indices]
    
    # BY 校正 (比 BH 更保守)
    adjusted = np.zeros(m)
    for i in range(m):
        idx = m - 1 - i
        rank = idx + 1
        adjusted[idx] = min(sorted_pvalues[idx] * m * harmonic_sum / rank, 1.0)
    
    # 单调性约束
    for i in range(1, m):
        adjusted[i] = min(adjusted[i], adjusted[i-1])
    
    # 恢复原始顺序
    adjusted_original = np.zeros(m)
    adjusted_original[sorted_indices] = adjusted
    
    # 判断是否显著 (BY 方法)
    significant = np.zeros(m, dtype=bool)
    max_k = -1
    for i in range(m):
        rank = i + 1
        if sorted_pvalues[i] <= (rank / m) * alpha / harmonic_sum:
            max_k = i
    
    if max_k >= 0:
        for i in range(max_k + 1):
            significant[sorted_indices[i]] = True
    
    return CorrectionResult(
        method="Benjamini-Yekutieli (FDR, correlated)",
        original_pvalues=pvalues.tolist(),
        adjusted_pvalues=adjusted_original.tolist(),
        significant=significant.tolist(),
        alpha=alpha,
        n_tests=m
    )


def sidak_correction(pvalues: List[float], alpha: float = 0.05) -> CorrectionResult:
    """
    Sidak 校正
    
    假设检验独立时的精确校正
    
    adjusted_p = 1 - (1 - p)^m
    
    Args:
        pvalues: 原始 p 值列表
        alpha: 显著性水平
        
    Returns:
        CorrectionResult
    """
    m = len(pvalues)
    pvalues = np.array(pvalues)
    
    # Sidak 校正
    adjusted = 1 - (1 - pvalues) ** m
    
    # Sidak 显著性阈值
    sidak_alpha = 1 - (1 - alpha) ** (1 / m)
    significant = pvalues < sidak_alpha
    
    return CorrectionResult(
        method="Sidak (independent tests)",
        original_pvalues=pvalues.tolist(),
        adjusted_pvalues=adjusted.tolist(),
        significant=significant.tolist(),
        alpha=alpha,
        n_tests=m
    )


def apply_correction(pvalues: List[float], 
                    method: str = 'bonferroni',
                    alpha: float = 0.05) -> CorrectionResult:
    """
    应用指定的多重比较校正
    
    Args:
        pvalues: 原始 p 值列表
        method: 'bonferroni', 'holm', 'fdr_bh', 'fdr_by', 'sidak'
        alpha: 显著性水平
        
    Returns:
        CorrectionResult
    """
    methods = {
        'bonferroni': bonferroni_correction,
        'holm': holm_bonferroni_correction,
        'fdr_bh': benjamini_hochberg_correction,
        'fdr_by': benjamini_yekutieli_correction,
        'sidak': sidak_correction,
    }
    
    if method not in methods:
        raise ValueError(f"Unknown method: {method}. Available: {list(methods.keys())}")
    
    return methods[method](pvalues, alpha)


def compare_methods(pvalues: List[float], alpha: float = 0.05) -> Dict:
    """
    比较所有校正方法的结果
    
    Returns:
        {
            'bonferroni': CorrectionResult,
            'holm': CorrectionResult,
            'fdr_bh': CorrectionResult,
            ...
        }
    """
    return {
        'bonferroni': bonferroni_correction(pvalues, alpha),
        'holm': holm_bonferroni_correction(pvalues, alpha),
        'fdr_bh': benjamini_hochberg_correction(pvalues, alpha),
        'fdr_by': benjamini_yekutieli_correction(pvalues, alpha),
        'sidak': sidak_correction(pvalues, alpha),
    }


# 便捷函数
def quick_correction(pvalues: List[float], 
                    n_hypotheses: Optional[int] = None,
                    method: str = 'bonferroni',
                    alpha: float = 0.05) -> Dict:
    """
    快速校正 p 值
    
    Args:
        pvalues: p 值列表
        n_hypotheses: 假设总数 (用于预注册校正)
        method: 校正方法
        alpha: 显著性水平
        
    Returns:
        字典格式结果
    """
    if n_hypotheses is not None and n_hypotheses > len(pvalues):
        # 添加未报告的检验 (假设 p=1.0)
        pvalues = pvalues + [1.0] * (n_hypotheses - len(pvalues))
    
    result = apply_correction(pvalues, method, alpha)
    return result.to_dict()


def pre_registration_correction(reported_pvalues: List[float],
                                n_preregistered: int,
                                method: str = 'bonferroni',
                                alpha: float = 0.05) -> CorrectionResult:
    """
    预注册实验的校正
    
    考虑预注册时声明的所有假设，即使部分未报告
    
    Args:
        reported_pvalues: 实际报告的 p 值
        n_preregistered: 预注册时声明的假设数
        method: 校正方法
        alpha: 显著性水平
        
    Returns:
        CorrectionResult
    """
    # 为未报告的假设添加 p=1.0
    all_pvalues = reported_pvalues + [1.0] * (n_preregistered - len(reported_pvalues))
    
    return apply_correction(all_pvalues, method, alpha)