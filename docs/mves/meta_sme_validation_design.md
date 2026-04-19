# Phase 2 - Meta-SME 统计验证设计

**日期**: 2026-04-19  
**版本**: v7.1.0-dev  
**目标**: 验证 Meta-SME 的有效性 (N≥30, p<0.05)

---

## 实验目标

验证 Meta-SME 的自我修改能力是否显著提升系统性能。

### 假设

- **H1 (主假设)**: 启用 Meta-SME 的系统性能显著优于禁用组
- **H2 (涌现假设)**: Meta-SME 能够产生涌现的自我改进行为
- **H3 (安全假设)**: Meta-SME 的安全机制能有效防止危险修改

---

## 实验设计

### 对照组设置

| 组别 | 描述 | 样本量 |
|------|------|--------|
| **实验组 (E)** | 启用 Meta-SME | n=15 |
| **对照组1 (C1)** | 禁用 Meta-SME (固定权重) | n=10 |
| **对照组2 (C2)** | 随机权重调整 | n=10 |
| **对照组3 (C3)** | GP-only (无代码修改) | n=10 |
| **总计** | | **N=45** |

### 实验参数

```python
EXPERIMENT_CONFIG = {
    'num_cycles': 50000,           # 50K 周期
    'checkpoint_interval': 500,    # 每 500 周期检查点
    'num_seeds': 45,               # 45 个独立运行
    'environments': [
        'textworld',               # 文本环境
        'atari_pong',             # Atari
        'procgen_coinrun',        # Procgen
        'moss_custom'             # 自定义环境
    ],
    'metrics': {
        'primary': 'cumulative_reward',
        'secondary': [
            'emergence_score',
            'self_modification_count',
            'successful_modifications',
            'weight_evolution_stability'
        ]
    }
}
```

---

## 统计方法

### 主要分析

1. **组间比较**: Mann-Whitney U 检验 (非参数)
2. **效应量**: Cohen's d
3. **置信区间**: 95% CI
4. **显著性水平**: α = 0.05

### 次要分析

1. **时间序列分析**: 性能趋势对比
2. **生存分析**: 涌现事件时间
3. **相关性分析**: 修改频率 vs 性能提升

### 样本量计算

```python
# 基于先验效应量 d=0.8 (大效应)
# Power = 0.80, α = 0.05
# 每组最少需要 n=21
# 我们使用 n=15-10，总计 N=45，提供足够统计力
```

---

## 验证指标

### 主要指标

| 指标 | 描述 | 测量方式 |
|------|------|----------|
| 累积奖励 | 总奖励积累 | sum(rewards) |
| 涌现分数 | 内在动机涌现程度 | emergence_detector |
| 性能提升率 | (后期-前期)/前期 | % improvement |

### 次要指标

| 指标 | 描述 |
|------|------|
| 修改提案数 | Meta-SME 生成的提案数量 |
| 成功修改率 | 通过验证的修改比例 |
| 回滚次数 | 失败的修改回滚次数 |
| 权重稳定性 | 权重变化的方差 |

---

## 实验流程

### Phase 2.1: 基线测试 (Week 1)

```
Day 1-2: 环境准备
  - 配置 4 种环境
  - 验证实验脚本
  
Day 3-5: 小规模预实验
  - 每组 3 个 seed
  - 5K 周期
  - 验证实验流程
```

### Phase 2.2: 全规模实验 (Week 1-2)

```
Week 1:
  - 实验组 (E): 15 runs × 50K cycles
  - 对照组1 (C1): 10 runs × 50K cycles
  
Week 2:
  - 对照组2 (C2): 10 runs × 50K cycles
  - 对照组3 (C3): 10 runs × 50K cycles
```

### Phase 2.3: 数据分析 (Week 2)

```
Day 1-2: 数据收集与清洗
Day 3-4: 统计分析
Day 5: 报告生成
```

---

## 成功标准

### 统计标准

- [ ] 实验组 vs 对照组1: p < 0.05
- [ ] 效应量 Cohen's d > 0.5 (中等效应)
- [ ] 95% CI 不包含 0

### 实用标准

- [ ] 性能提升 ≥ 10%
- [ ] 涌现检出率 ≥ 70%
- [ ] 成功修改率 ≥ 60%

---

## 风险缓解

| 风险 | 缓解措施 |
|------|----------|
| 实验时间过长 | 并行运行，GPU 加速 |
| 环境不稳定 | 断点续跑机制 |
| 结果不显著 | 增加样本量至 N=60 |
| 计算资源不足 | 优先运行关键对比 |

---

## 预期输出

### 报告文档

1. `docs/mves/meta_sme_validation_report.md`
2. `docs/mves/meta_sme_statistical_analysis.md`
3. 可视化图表 (性能曲线、分布图等)

### 数据文件

1. `experiments/meta_sme_validation/results.json`
2. `experiments/meta_sme_validation/statistics.json`
3. `experiments/meta_sme_validation/checkpoints/`

---

## 下一步行动

1. **立即开始**: 创建实验脚本
2. **今天完成**: 基线测试配置
3. **本周运行**: 小规模预实验
4. **下周开始**: 全规模 50K 周期实验

---

**创建日期**: 2026-04-19  
**计划完成**: 2026-05-03 (2周)