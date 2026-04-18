# v6.0 GP 质量强化 (V3) 实现文档

**日期**: 2026-04-17  
**版本**: V3  
**状态**: ✅ 已完成  
**测试**: 14 个单元测试通过  

---

## 概述

基于 Copilot 评估报告的建议，实现了 GP (遗传编程) 质量强化版本，解决"GP 发现函数过于简单（单终端）"的问题。

**核心改进**:
- 更大种群 (200) 和更多代数 (100)，探索更复杂的函数空间
- 惩罚单终端函数，鼓励复合函数
- 严格的行为增益门槛 (≥0.10)，确保实用性
- 复杂度奖励，鼓励适度复杂的函数

---

## 实现文件

| 文件 | 路径 | 说明 |
|------|------|------|
| GP V3 实现 | `agi/genetic_programmer_v3.py` | 质量强化版 GP |
| 单元测试 | `tests/test_gp_v3.py` | 14 个测试用例 |

---

## 核心改进

### 1. 强化搜索参数

| 参数 | V2 | V3 | 改进 |
|------|-----|-----|------|
| 种群规模 | 100 | **200** | +100% |
| 代数 | 50 | **100** | +100% |

**效果**: 更大的搜索空间，更可能发现复杂函数。

### 2. 单终端惩罚

```python
if tree.node_count() == 1 and tree.is_terminal():
    fitness -= 0.5  # 显著惩罚
```

**目的**: 阻止 GP 只发现简单的单终端函数（如 `entropy`, `file_count`）。

**示例**:
- ❌ `entropy` (单终端，惩罚 -0.5)
- ✅ `sigmoid(mul(entropy, file_count))` (复合函数，无惩罚)

### 3. 最小行为增益过滤

```python
if behavioral_gain < 0.10:
    return -1.0  # 拒绝
```

**目的**: 确保发现的函数具有实际的行为影响，而非仅统计相关。

### 4. 适应度权重调整 (V3 公式)

```python
fitness = (
    0.20 * correlation +      # 相关性 (降低)
    0.10 * (1 - mse) +        # 精度 (降低)
    0.50 * behavioral_gain +  # 行为增益 (最高)
    0.20 * complexity_bonus   # 复杂度奖励 (新增)
)
```

**重点**: behavioral_gain 权重最高 (0.5)，确保实用性优先。

### 5. 复杂度奖励

```python
# 目标复杂度: 8 个节点
# 容差: ±5 个节点

if 3 <= node_count <= 20:
    if abs(node_count - 8) <= 5:
        bonus = 1.0 - (distance / 5)  # 接近目标，高奖励
    else:
        bonus = 0.5  # 在范围内
else:
    bonus = -0.3 if node_count < 3 else -0.2  # 惩罚
```

**目的**: 鼓励复杂度适中的函数，避免过简或过繁。

---

## 使用方式

### 基础用法

```python
from agi.genetic_programmer_v3 import GeneticProgrammerV3

# 创建 GP V3
gp = GeneticProgrammerV3()

# 运行进化
result = gp.evolve(
    behavior_labels=[1, 0, 1, 0, ...],
    env_states=[{'entropy': 0.5, ...}, ...]
)

if result:
    print(f"发现函数: {result.expr_str}")
    print(f"节点数: {result.node_count}")
    print(f"适应度: {result.fitness:.3f}")
```

### 使用预设配置

```python
from agi.genetic_programmer_v3 import get_gp_v3_preset

# 标准配置
config = get_gp_v3_preset('v3_default')
gp = GeneticProgrammerV3(config)

# 严格配置 (更高门槛)
config = get_gp_v3_preset('v3_strict')
gp = GeneticProgrammerV3(config)

# 快速配置 (快速测试)
config = get_gp_v3_preset('v3_fast')
gp = GeneticProgrammerV3(config)
```

### 便捷函数

```python
from agi.genetic_programmer_v3 import evolve_drive_v3

result = evolve_drive_v3(
    behavior_labels=B,
    env_states=X,
    config={'population_size': 200, 'generations': 100}
)
```

---

## 配置预设

### v3_default (标准)

```python
{
    'population_size': 200,
    'generations': 100,
    'terminal_penalty': 0.5,
    'min_behavioral_gain': 0.10,
    'target_complexity': 8,
}
```

### v3_strict (严格)

```python
{
    'population_size': 300,
    'generations': 150,
    'terminal_penalty': 0.8,
    'min_behavioral_gain': 0.15,
    'target_complexity': 10,
}
```

### v3_fast (快速)

```python
{
    'population_size': 100,
    'generations': 50,
    'terminal_penalty': 0.3,
    'min_behavioral_gain': 0.08,
    'target_complexity': 6,
}
```

---

## 预期效果

### 与 V2 对比

| 维度 | V2 | V3 | 改进 |
|------|-----|-----|------|
| 函数复杂度 | 单终端为主 | 复合函数 | ✅ 显著提升 |
| 行为增益 | ~0.08 | ≥0.10 | ✅ 门槛提高 |
| 搜索空间 | 100×50 | 200×100 | ✅ 扩大 4 倍 |
| 实用性 | 中等 | 高 | ✅ 更实用 |

### 示例函数对比

**V2 典型输出**:
```
entropy                    # 单终端，过于简单
file_count                 # 单终端，过于简单
```

**V3 预期输出**:
```
sigmoid(mul(entropy, file_count))           # 复合函数
add(entropy_delta, mul(resource_level, 0.5)) # 复合函数
clip01(div(error_rate, success_rate_recent)) # 复合函数
```

---

## 测试覆盖

### 测试文件: `tests/test_gp_v3.py`

| 测试类 | 测试数 | 覆盖内容 |
|--------|--------|----------|
| TestGPV3Config | 3 | 配置、预设 |
| TestGPV3Fitness | 5 | 适应度函数、惩罚、过滤 |
| TestGPV3Evolution | 3 | 进化过程 |
| TestGPV3Complexity | 3 | 复杂度奖励 |

**运行测试**:
```bash
python tests/test_gp_v3.py
```

---

## 下一步

1. **运行 2,000 周期验证实验** - 验证 V3 实际效果
2. **对比 V2 vs V3** - 量化改进效果
3. **调整参数** - 根据实验结果优化配置

---

## 参考

- Copilot 评估报告: `markDown1776415707546.md`
- GP V2 实现: `agi/genetic_programmer_v2.py`
- GP V1 实现: `agi/genetic_programmer.py`

---

*实现完成: 2026-04-17*  
*测试通过: 14/14*  
*作者: OpenClaw Agent*
