# MOSS v6.0 实验预注册指南

**版本**: v6.0.0  
**日期**: 2026-04-17  
**状态**: ✅ 已锁定  

---

## 什么是预注册？

预注册 (Pre-registration) 是在实验开始前明确记录研究假设、方法和分析计划的做法。

**目的**:
- 防止"试到显著为止" (p-hacking)
- 提高研究透明度和可复现性
- 区分验证性研究和探索性研究

---

## v6.0 预注册内容

### 假设 (Hypotheses)

#### H1: 权重上限机制有效性
- **零假设 (H0)**: 设置 survival 权重上限 (30%) 不会提升涌现驱动权重
- **备择假设 (H1)**: 设置 survival 权重上限 (30%) 将使涌现驱动权重提升至 ≥0.20
- **判定标准**: 涌现权重 ≥ 0.20

#### H2: 驱动竞争机制有效性
- **零假设 (H0)**: 引入驱动竞争机制不会提升涌现驱动稳定性
- **备择假设 (H2)**: 驱动竞争机制将使涌现驱动稳定性保持 ≥95%，方差降低 ≥20%
- **判定标准**: 稳定性 ≥ 95% 且方差降低 ≥ 20%

#### H3: GP 质量强化效果
- **零假设 (H0)**: GP 质量强化不会提升涌现函数的行为增益
- **备择假设 (H3)**: GP 质量强化将使行为增益提升至 ≥0.15
- **判定标准**: 行为增益 ≥ 0.15

### 主要指标 (Primary Metrics)

| 指标 | 定义 | 测量方法 | 目标值 |
|------|------|----------|--------|
| emergent_drive_weight | 涌现驱动权重占比 | 最终 checkpoint | ≥ 0.20 |
| emergent_drive_stability | 涌现驱动稳定性 | 存在周期/总周期 | ≥ 0.95 |
| behavioral_gain | 行为增益 | (新行为-基线)/基线 | ≥ 0.15 |

### 对照条件 (Control Conditions)

1. **baseline**: v5.5.2 默认参数 (比较基准)
2. **ablation_weight_cap**: 移除权重上限 (验证必要性)
3. **ablation_competition**: 移除竞争机制 (验证必要性)

### 统计方法 (Statistical Methods)

- **效应量**: Cohen's d
- **置信区间**: BCa Bootstrap (10,000 次)
- **多重比较校正**: Bonferroni (α=0.0167，3 个假设)
- **显著性水平**: α = 0.05

### 实验设计

- **样本量**: 3 个独立 seed
- **随机种子**: [42, 123, 456]
- **总周期**: 10,000
- **检查点间隔**: 1,000 周期

---

## 使用预注册系统

### 1. 生成预注册文档

```bash
python scripts/generate_preregistration.py --template v6.0
```

输出: `docs/mves/pre_registration/v6_20260417.yaml`

### 2. 锁定预注册 (实验开始前)

```bash
python scripts/generate_preregistration.py --lock docs/mves/pre_registration/v6_20260417.yaml
```

锁定后文档不可修改，生成锁定哈希。

### 3. 验证预注册完整性

```bash
python scripts/generate_preregistration.py --verify docs/mves/pre_registration/v6_20260417.yaml
```

验证文档是否被篡改。

---

## 预注册文件

### 文件位置

```
docs/mves/pre_registration/
└── v6_20260417.yaml          # 预注册文档 (已锁定)
```

### 文件内容示例

```yaml
version: v6.0.0
date: '2026-04-17T21:16:27'
status: locked
locked_at: '2026-04-17T21:17:16'
lock_hash: 38dea8ef20273c23

hypotheses:
  - id: H1
    name: 权重上限机制有效性
    null_hypothesis: ...
    alternative_hypothesis: ...

primary_metrics:
  - name: emergent_drive_weight
    target_value: 0.2
    ...

sample_size: 3
random_seeds: [42, 123, 456]
total_cycles: 10000
```

---

## 实验后报告

实验完成后，需要生成报告对比预注册内容：

```python
from scripts.generate_preregistration import PreRegistrationGenerator

generator = PreRegistrationGenerator()
pre_reg = generator.load('docs/mves/pre_registration/v6_20260417.yaml')

# 对比实验结果
for hypothesis in pre_reg.hypotheses:
    result = experiment_results[hypothesis.id]
    print(f"{hypothesis.id}: {'支持' if result.supported else '不支持'}")
```

---

## 最佳实践

1. **实验开始前锁定** - 一旦开始收集数据，预注册不可修改
2. **透明报告** - 即使结果不支持假设，也要完整报告
3. **区分探索性分析** - 预注册外的分析应明确标注为探索性
4. **公开预注册** - 考虑将预注册文档公开到 OSF 等平台

---

## 参考

- Copilot 评估报告: `markDown1776415707546.md`
- 预注册文档: `docs/mves/pre_registration/v6_20260417.yaml`
- 生成脚本: `scripts/generate_preregistration.py`

---

*创建日期: 2026-04-17*  
*锁定时间: 2026-04-17T21:17:16*  
*锁定哈希: 38dea8ef20273c23*
