# v6.0 统计报告升级实现文档

**日期**: 2026-04-17  
**状态**: ✅ 已完成  
**测试**: 20 个单元测试全部通过  

---

## 概述

基于 Copilot 评估报告的建议，实现了完整的统计报告升级，包括效应量计算、Bootstrap 置信区间和多重比较校正。

**核心目标**:
- 从"工程报告"升级到"科学论文"级别的统计严谨性
- 提供效应量 (Cohen's d) 而非仅 p 值
- 使用 Bootstrap 计算稳健的置信区间
- 实施多重比较校正防止假阳性

---

## 实现文件

| 模块 | 路径 | 功能 |
|------|------|------|
| 效应量计算 | `agi/analysis/effect_size.py` | Cohen's d, Hedge's g, Glass's delta |
| Bootstrap CI | `agi/analysis/bootstrap.py` | Percentile, BCa 置信区间 |
| 多重比较校正 | `agi/analysis/multiple_comparison.py` | Bonferroni, FDR, Holm |
| 单元测试 | `tests/test_analysis.py` | 20 个测试用例 |

---

## 核心组件

### 1. 效应量计算 (effect_size.py)

#### Cohen's d
```python
from agi.analysis.effect_size import cohens_d

result = cohens_d(group1, group2, ci=0.95)
print(f"Cohen's d: {result.value:.3f}")
print(f"95% CI: [{result.ci_lower:.3f}, {result.ci_upper:.3f}]")
print(f"解释: {result.interpretation}")  # 小/中/大效应
```

**解释标准**:
- |d| < 0.2: 可忽略
- 0.2 ≤ |d| < 0.5: 小效应
- 0.5 ≤ |d| < 0.8: 中效应
- |d| ≥ 0.8: 大效应

#### Hedge's g (小样本校正)
```python
from agi.analysis.effect_size import hedges_g

# 适用于小样本 (n < 20)
result = hedges_g(group1, group2)
```

#### 快速效应量
```python
from agi.analysis.effect_size import quick_effect_size

result = quick_effect_size(group1, group2, metric='cohens_d')
# 返回: {'metric': "Cohen's d", 'value': 0.85, 'ci_95': [0.45, 1.25], ...}
```

### 2. Bootstrap 置信区间 (bootstrap.py)

#### BCa Bootstrap (推荐)
```python
from agi.analysis.bootstrap import bca_bootstrap

result = bca_bootstrap(
    data, 
    statistic_func=np.mean,
    n_bootstrap=10000,
    ci=0.95
)
print(f"均值: {result.statistic:.3f}")
print(f"95% CI: [{result.ci_lower:.3f}, {result.ci_upper:.3f}]")
print(f"标准误: {result.std_error:.3f}")
print(f"偏差: {result.bias:.3f}")
```

#### 快速 Bootstrap CI
```python
from agi.analysis.bootstrap import quick_bootstrap_ci

result = quick_bootstrap_ci(data, statistic='mean', ci=0.95)
# 返回: {'statistic': 100.5, 'ci': [95.2, 105.8], ...}
```

#### 两组比较
```python
from agi.analysis.bootstrap import bootstrap_two_groups

result = bootstrap_two_groups(
    group1, group2,
    statistic_func=lambda x, y: np.mean(x) - np.mean(y),
    method='bca'
)
```

### 3. 多重比较校正 (multiple_comparison.py)

#### Bonferroni 校正
```python
from agi.analysis.multiple_comparison import bonferroni_correction

pvalues = [0.01, 0.02, 0.03, 0.1]
result = bonferroni_correction(pvalues, alpha=0.05)

for i, (p, adj, sig) in enumerate(zip(
    result.original_pvalues,
    result.adjusted_pvalues,
    result.significant
)):
    print(f"H{i+1}: p={p:.3f}, adjusted={adj:.3f}, significant={sig}")
```

#### FDR 校正 (Benjamini-Hochberg)
```python
from agi.analysis.multiple_comparison import benjamini_hochberg_correction

# 控制错误发现率，比 Bonferroni 更宽松
result = benjamini_hochberg_correction(pvalues, alpha=0.05)
```

#### 比较所有方法
```python
from agi.analysis.multiple_comparison import compare_methods

results = compare_methods(pvalues, alpha=0.05)
# 返回所有方法的校正结果
```

#### 预注册实验校正
```python
from agi.analysis.multiple_comparison import pre_registration_correction

# 考虑预注册时声明的所有假设
result = pre_registration_correction(
    reported_pvalues=[0.01, 0.03],  # 实际报告的
    n_preregistered=5,               # 预注册时声明的
    method='bonferroni'
)
```

---

## 使用示例

### 完整实验报告

```python
import numpy as np
from agi.analysis.effect_size import cohens_d, effect_size_summary
from agi.analysis.bootstrap import bca_bootstrap, bootstrap_mean_ci
from agi.analysis.multiple_comparison import bonferroni_correction

# 实验数据
control_group = np.random.normal(100, 15, 50)
treatment_group = np.random.normal(110, 15, 50)

# 1. 效应量计算
d_result = cohens_d(treatment_group, control_group)
print(f"效应量: Cohen's d = {d_result.value:.3f} ({d_result.interpretation})")
print(f"95% CI: [{d_result.ci_lower:.3f}, {d_result.ci_upper:.3f}]")

# 2. Bootstrap 置信区间
mean, ci_lower, ci_upper = bootstrap_mean_ci(treatment_group)
print(f"处理组均值: {mean:.2f} [{ci_lower:.2f}, {ci_upper:.2f}]")

# 3. 多重比较校正 (如果有多个假设)
pvalues = [0.01, 0.03, 0.15]  # 多个检验的 p 值
correction = bonferroni_correction(pvalues, alpha=0.05)
print(f"校正后显著检验数: {sum(correction.significant)}")
```

### 集成到实验报告

```python
def generate_experiment_report_v2(experiment_data):
    """生成 v2 格式实验报告 (含统计升级)"""
    
    report = {
        'experiment': experiment_data['name'],
        'statistics': {
            'effect_sizes': {},
            'bootstrap_ci': {},
            'corrections': {},
        }
    }
    
    # 效应量
    if 'control' in experiment_data and 'treatment' in experiment_data:
        d_result = cohens_d(
            experiment_data['treatment'],
            experiment_data['control']
        )
        report['statistics']['effect_sizes']['cohens_d'] = d_result.to_dict()
    
    # Bootstrap CI
    for metric_name, values in experiment_data['metrics'].items():
        ci_result = bca_bootstrap(values, ci=0.95)
        report['statistics']['bootstrap_ci'][metric_name] = ci_result.to_dict()
    
    # 多重比较校正
    if 'pvalues' in experiment_data:
        correction = bonferroni_correction(
            experiment_data['pvalues'],
            alpha=0.05
        )
        report['statistics']['corrections']['bonferroni'] = correction.to_dict()
    
    return report
```

---

## 方法对比

### 效应量指标选择

| 指标 | 适用场景 | 优点 | 缺点 |
|------|----------|------|------|
| Cohen's d | 大样本，方差相等 | 最常用，易解释 | 小样本有偏 |
| Hedge's g | 小样本 (n<20) | 无偏估计 | 计算稍复杂 |
| Glass's delta | 方差不等 | 使用对照组 SD | 检验力较低 |
| r | t 检验结果 | 直观相关 | 范围受限 |

### Bootstrap 方法选择

| 方法 | 准确度 | 计算成本 | 适用场景 |
|------|--------|----------|----------|
| Percentile | 中 | 低 | 快速估计 |
| BCa | 高 | 中 | **推荐**，校正偏差 |
| Studentized | 高 | 高 | 复杂统计量 |

### 多重比较校正选择

| 方法 | 保守程度 | 控制目标 | 适用场景 |
|------|----------|----------|----------|
| Bonferroni | 最保守 | 族错误率 (FWER) | 检验数少 (<10) |
| Holm | 保守 | FWER | 检验数中等 |
| FDR (BH) | 适中 | 错误发现率 | **推荐**，检验数多 |
| FDR (BY) | 较保守 | FDR (相关检验) | 检验间相关 |

---

## 测试覆盖

### 测试文件: `tests/test_analysis.py`

| 测试类 | 测试数 | 覆盖内容 |
|--------|--------|----------|
| TestEffectSize | 8 | Cohen's d, Hedge's g, Glass's delta, 解释 |
| TestBootstrap | 5 | Percentile, BCa, 两组比较 |
| TestMultipleComparison | 7 | Bonferroni, Holm, FDR, FWER 控制 |

**运行测试**:
```bash
python tests/test_analysis.py
```

---

## 预期效果

### 报告质量提升

| 维度 | 升级前 | 升级后 |
|------|--------|--------|
| 效应量 | 无 | Cohen's d + CI |
| 置信区间 | 无/近似 | Bootstrap 10,000 次 |
| 多重比较 | 无 | Bonferroni/FDR |
| 可解释性 | 低 | 小/中/大效应标签 |

### 对 v6.0 的贡献

1. **预注册支持**: 多重比较校正支持预注册假设数
2. **结果可靠性**: Bootstrap CI 提供稳健的区间估计
3. **效应量化**: 从"显著"到"有意义"的转变
4. **学术标准**: 符合顶级期刊的统计报告要求

---

## 下一步

1. **更新实验报告格式** - 创建 `experiment_report_v2.json` 模板
2. **集成到实验流程** - 在 `experiment_v6.py` 中自动计算统计量
3. **可视化工具** - 添加效应量森林图、CI 可视化

---

## 参考

- Copilot 评估报告: `markDown1776415707546.md`
- v6 预注册草案: `docs/mves/v6_preregistration_draft.md`
- 统计最佳实践: Cumming (2012), "Understanding The New Statistics"

---

*实现完成: 2026-04-17*  
*测试通过: 20/20*  
*作者: OpenClaw Agent*
