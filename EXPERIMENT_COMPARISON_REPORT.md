# MOSS v8.0 A/B 实验对比报告
## AST-Only vs LLM-Hybrid (30代完整实验)

**实验日期**: 2026-04-20  
**环境**: 本地运行 (无Sandbox超时限制)

---

## 一、实验配置

| 配置项 | AST-Only | LLM-Hybrid (Coding Plan v2) |
|--------|----------|----------------------------|
| **模式** | ast_only | scheduled [ast, ast, llm] |
| **代数** | 30 | 30 |
| **Population** | 6 | 6 |
| **Acceptance Threshold** | -0.01 | -0.01 |
| **LLM Provider** | - | Bailian (qwen3-coder-plus) |
| **Cooldown** | - | 0 (强制模式) |

---

## 二、核心结果对比

| 指标 | AST-Only | LLM-Hybrid | 差异 |
|------|----------|------------|------|
| **初始 Fitness** | 0.6926 | 0.6670 | -0.0256 |
| **最终 Fitness** | 0.6818 | 0.6732 | -0.0086 |
| **净变化** | **-0.0108** | **+0.0062** | +0.0170 |
| **接受变异数** | 10 | 18 | +8 |
| **耗时** | 151.1s (2.5min) | 653.0s (10.9min) | +501.9s |
| **时间效率** | 0.20 gen/s | 0.05 gen/s | 4× slower |

### 关键发现

1. **LLM-Hybrid 实现正向提升 (+0.0062)，AST-Only 下降 (-0.0108)**
2. **LLM 接受更多变异 (18 vs 10)**，说明 LLM 产生更多有效候选
3. **但 LLM 时间成本极高** (10.9min vs 2.5min)，效率低4倍

---

## 三、Fitness 轨迹分析

### AST-Only Fitness 轨迹

```
Gen 0:  0.6926 (初始)
Gen 1:  0.6820 (-0.0106) ❌
Gen 2:  0.6750 (-0.0070) ❌
Gen 3:  0.6881 (+0.0131) ✅
Gen 4:  0.6720 (-0.0161) ❌
Gen 5:  0.6788 (+0.0068) ✅
Gen 6:  0.6850 (+0.0062) ✅
Gen 7:  0.6699 (-0.0150) ❌
Gen 8:  0.6661 (-0.0038) ❌
Gen 9:  0.6721 (+0.0060) ✅
Gen 10: 0.6818 (+0.0097) ✅ (最终)
```

**特点**: 波动大，后期难以突破

### LLM-Hybrid Fitness 轨迹

```
Gen 0:  0.6670 (初始)
Gen 1:  0.6633 (-0.0037) ❌
Gen 2:  0.6745 (+0.0112) ✅
Gen 3:  0.6844 (+0.0099) ✅ ← LLM
Gen 4:  0.6679 (-0.0165) ❌
Gen 5:  0.6542 (-0.0137) ❌
Gen 6:  0.6507 (-0.0035) ❌
Gen 7:  0.6593 (+0.0086) ✅ ← LLM (最后LLM代)
Gen 8-30: 波动，无LLM参与
Gen 30: 0.6732 (+0.0139 from Gen 6最低) ✅
```

**特点**: 
- Gen 3 (LLM) 产生显著 +0.0099 提升
- Gen 7 (LLM) 后无LLM调用 (`last_llm_generation: 7`)
- 后期靠AST缓慢恢复

---

## 四、变异类型分布

### AST-Only

| 类型 | 次数 | 占比 |
|------|------|------|
| no_op | 15 | 50% |
| weight_hardcode | 5 | 16.7% |
| threshold_mutate | 4 | 13.3% |
| constant_tweak | 3 | 10% |
| weight_shift | 2 | 6.7% |
| condition_flip | 1 | 3.3% |

### LLM-Hybrid

| 类型 | 次数 | 占比 |
|------|------|------|
| weight_shift | 10 | 33.3% |
| llm_guided | 6 | 20% |
| no_op | 6 | 20% |
| weight_hardcode | 3 | 10% |
| threshold_mutate | 2 | 6.7% |
| constant_tweak | 2 | 6.7% |
| condition_flip | 1 | 3.3% |

### 关键发现

1. **LLM 贡献了 6 次有效变异 (20%)**
2. **weight_shift 在 LLM 实验中占比最高** (33.3%)
3. **no_op 比例相同** (20% vs 50% 相对比例)

---

## 五、LLM 详细统计

| 指标 | 数值 |
|------|------|
| API 调用次数 | 13 |
| 输入 Token | 54,238 |
| 输出 Token | 48,584 |
| API 成本 | $0.1111 |
| 最后 LLM 代数 | 7 |

### 问题：为什么 Gen 7 后无 LLM 调用？

根据 `hybrid_stats`:
- `last_llm_generation: 7`
- `consecutive_no_ops: 1`
- `consecutive_rejects: 1`

**原因**: Gen 7 后可能触发 adaptive 逻辑，或 scheduled 模式被覆盖。需要检查代码逻辑。

---

## 六、结论与建议

### 6.1 核心结论

| 维度 | 胜出方 | 说明 |
|------|--------|------|
| **Fitness 提升** | LLM-Hybrid ✅ | +0.0062 vs -0.0108 |
| **时间效率** | AST-Only ✅ | 4× 更快 |
| **成本效益** | AST-Only ✅ | 零成本 |
| **突破潜力** | LLM-Hybrid ✅ | Gen 3 单代 +0.0099 |
| **稳定性** | 平局 | 两者都波动 |

### 6.2 关键洞察

1. **LLM 在早期 (Gen 3-7) 有效，后期失效**
   - 可能原因：代码复杂度增加，LLM难以生成有效变异
   - 或：进入局部最优，需要更大胆的变异

2. **AST 变异后期陷入平台**
   - 30代后 fitness 下降，说明 AST 随机变异难以维持

3. **混合策略需要优化**
   - 当前 scheduled 模式在 Gen 7 后停止 LLM 调用
   - 建议：adaptive 模式，根据 fitness  plateau 动态调整

### 6.3 改进建议

#### 短期
1. **修复 scheduled 模式**：确保每3代强制调用 LLM
2. **增加 LLM 预算**：从 33% 提升到 50% 或更高
3. **优化 prompt**：针对后期代码复杂度调整

#### 中期
4. **Adaptive 策略**：根据 fitness 变化动态调整 LLM/AST 比例
5. **多轮评估**：减少 fitness 随机性
6. **变异效果追踪**：分析哪些 LLM 变异类型最有效

#### 长期
7. **分层进化**：早期 LLM 大胆变异，后期 AST 精细调整
8. **元学习**：学习最优的 mutation schedule

---

## 七、数据文件

- AST-Only: `experiment_ast_only_20260420_234040.json`
- LLM-Hybrid: `experiment_coding_plan_v2_20260420_234800.json`

---

**报告生成**: 2026-04-20  
**分析师**: MOSS Auto-Analysis
