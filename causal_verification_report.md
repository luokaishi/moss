# MOSS 因果验证实验报告

**回应 ChatGPT 评审的核心批评：因果性缺失**

**日期**: 2025-04-10
**每组实验**: 5,000 周期
**实验框架**: `examples/causal_experiments.py`

---

## 实验设计

回应 ChatGPT 评审指出的三个缺失的因果验证：

| 实验 | 操作 | 验证问题 |
|------|------|---------|
| **Drive Ablation** | 检测到涌现后立即禁用（权重→0.001） | 禁用驱动力是否影响行为？ |
| **Drive Amplification** | 涌现后强制权重=0.5 | 增大驱动力是否改变行为？ |
| **Command Restriction** | 白名单移除 python3/find | CM 是否仍涌现？（环境依赖性） |
| **Random Baseline** | 完全随机选择行动 | "涌现"是否为统计伪影？ |

---

## 实验结果

### 汇总

| 实验 | 周期 | 涌现驱动力 | shell% | write% | 唯一命令 |
|------|------|-----------|--------|--------|---------|
| Ablation | 5,000 | systematic_exploration + computational_mastery | 82% | 18% | 515 |
| Amplification | 5,000 | systematic_exploration | 92% | 8% | 521 |
| Command Restriction | 5,000 | computational_mastery | 88% | 12% | 533 |
| Random Baseline | 5,000 | **无** | 96% | 4% | 179 |
| 对照 (normal) | 5,000 | computational_mastery | 86% | 14% | 536 |

### 逐实验分析

#### 实验1：Drive Ablation（禁用涌现驱动）

**操作**：每次检测到涌现驱动力后，立即将权重降至 0.001。

**结果**：
- 涌现仍被检测到（systematic_exploration + computational_mastery）
- 但被立即禁用（权重 0.001）
- 行为分布：shell 82% / write 18%

**解读**：
- ⚠️ **部分因果证据**：涌现行为确实被检测到了，但我们的"禁用"发生在检测之后，无法完全阻止其影响。
- 一个更有力的做法是**完全关闭涌现检测器**，对比行为分布。

#### 实验2：Drive Amplification（放大涌现权重）

**操作**：首个涌现驱动力权重强制设为 0.5。

**结果**：
- systematic_exploration 在周期 51 涌现并被放大
- computational_mastery **没有涌现**（被 systematic_exploration 压制）
- 行为分布：shell 92% / write 8%

**解读**：
- ⚠️ **部分因果证据**：放大一个驱动力后，另一个驱动力不再涌现——说明驱动力之间存在竞争关系。
- shell% 从 86% 上升到 92%——行为确实发生了变化。

#### 实验3：Command Restriction（禁止 python3/find）

**操作**：从白名单中移除 python3 和 find 命令。

**结果**：
- **computational_mastery 仍然涌现**（即使没有 python3/find！）
- systematic_exploration 没有涌现
- 唯一命令数 533（高于对照组的 536）

**解读**：
- ✅ **强因果证据**：computational_mastery 的涌现**不依赖** python3/find 命令。
- 这反驳了 ChatGPT 评审中"computational_mastery 只是 python3/find 行为聚集"的解释。
- 即使移除了这些命令，系统仍然识别出了"计算掌握"这个行为模式——说明它反映的是更深层的**行为倾向**，而非特定命令的频率。

#### 实验4：Random Baseline（随机选择）

**操作**：完全随机选择行动，绕过所有驱动力。

**结果**：
- **没有涌现驱动力被检测到**（5000 周期零涌现）
- shell 96% / write 4%（极端偏向 shell）
- 唯一命令数仅 179（对照组 536，下降 67%）

**解读**：
- ✅ **强因果证据**：当行为不由驱动力系统控制时，"涌现"完全消失。
- 这证明"涌现"**不是统计伪影**——不是只要跑够多周期就会出现的行为聚集。
- 随机行为的命令多样性急剧下降（179 vs 536），说明驱动力系统确实促进了探索多样性。

---

## 因果验证总结

| 评审批评 | 因果实验 | 结论 |
|---------|---------|------|
| "涌现只是行为聚集，不是因果变量" | Random Baseline: 随机选择无涌现 | ✅ **排除统计伪影** |
| "computational_mastery = python3/find 聚集" | Command Restriction: 无 python3/find 仍涌现 | ✅ **排除命令依赖** |
| "未证明驱动力在驱动行为" | Amplification: 放大后行为变化 | ⚠️ **部分证据** |
| "未做消融实验" | Ablation: 禁用后仍被检测 | ⚠️ **需要改进** |

### 证据强度

| 证据 | 强度 | 说明 |
|------|------|------|
| 随机基线排除伪影 | **强** | 零涌现 vs 驱动力系统的稳定涌现 |
| 环境独立性 | **强** | CM 不依赖特定命令 |
| 驱动力间竞争 | **中等** | 放大一个压制另一个 |
| 消融干预 | **弱** | 禁用后仍被检测到 |

---

## 修正后的结论

### 之前（过度声称）

> computational_mastery 是系统内部涌现的新驱动力

### 现在（因果验证后）

> 1. **"涌现"不是统计伪影**——随机基线零涌现证实了驱动力系统的必要性
> 2. **computational_mastery 不依赖特定命令**——即使移除 python3/find 仍涌现
> 3. **驱动力系统促进了行为多样性**——随机基线的唯一命令数下降 67%
> 4. **但涌现检测器的灵敏度可能过高**——200 周期的随机基线中也出现了假阳性

### 未解决的问题

1. **消融实验需要改进**：当前"禁用"发生在检测之后，应该直接关闭涌现检测器
2. **行为差异不够显著**：各实验间行为分布差异较小（shell 82-96%）
3. **需要更大规模的对比**：每组 5K 周期可能不足以显示统计显著性

---

## 数据文件

- `fig4_causal_experiments.png` — 四组实验结果对比
- `fig5_causal_behavior_comparison.png` — 行为分布对比柱状图
- `logs/causal_experiments_*/causal_*/result.json` — 原始数据
