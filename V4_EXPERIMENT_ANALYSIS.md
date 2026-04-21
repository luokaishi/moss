# MOSS v8.0 v4 实验结果分析
## 关键问题：Token预算耗尽导致LLM提前停止

**实验时间**: 2026-04-21 09:26:06  
**实验配置**: v4 (50%预算 + 精英保留 + 动态阈值)

---

## 一、核心问题

### 现象

| 指标 | 预期 | 实际 | 问题 |
|------|------|------|------|
| LLM调用次数 | ~30次 (每3代) | 13次 | ❌ 提前停止 |
| 最后LLM代数 | 30 | 7 | ❌ Gen 7后无LLM |
| Token使用 | <100k | 106,288 | ❌ 超预算 |
| LLM变异数 | ~15 | 5 | ❌ 严重不足 |

### 根本原因

```python
# 默认配置
llm_daily_token_budget: int = 100000  # 10万token

# v4实际使用
total_input_tokens: 55870
total_output_tokens: 50418
-----------------------------------
Total: 106,288 tokens > 100,000 budget ❌
```

**Gen 7后**: `budget_remaining_tokens: 0` → LLM调用被拒绝 → 退化回AST-only

---

## 二、实验结果

### Fitness轨迹

```
Gen 0:  0.6677 (初始)
Gen 1:  0.6713 (+0.0036) ✅ LLM
Gen 2:  0.6620 (-0.0093) ❌
Gen 3:  0.6667 (+0.0047) ✅ LLM
Gen 4:  0.6482 (-0.0185) ❌ 大幅下降
Gen 5:  0.6529 (+0.0047) ✅ LLM
Gen 6:  0.6507 (-0.0022) ❌
Gen 7:  0.6601 (+0.0094) ✅ LLM (最后)
Gen 8-30: 纯AST，波动在 0.65-0.67
Gen 30: 0.6652 (-0.0025 vs 初始)
```

### 与v3对比

| 指标 | v3 | v4 | 说明 |
|------|-----|-----|------|
| 初始Fitness | 0.6651 | 0.6677 | 相近 |
| 最终Fitness | 0.6737 | 0.6652 | v4更差 |
| **最高Fitness** | **0.6954** | **0.6760** | v4低很多 |
| 提升 | +0.86% | -0.37% | v4失败 |
| LLM调用 | 59 | 13 | v4严重不足 |
| 耗时 | 2623s | 617s | v4快但无效 |

---

## 三、为什么v4比v3差？

### v3成功因素
- **59次LLM调用** - 持续参与全部30代
- **Gen 14达到0.6934** - LLM突破
- **Gen 21达到0.6954** - 次高峰

### v4失败因素
1. **Token预算不足** - 10万预算只够7代
2. **Gen 8后无LLM** - 退化回纯AST
3. **精英保留未发挥作用** - 没有高峰可保护
4. **AST-only效果差** - 最终fitness下降

---

## 四、修复方案

### 立即修复

```python
# experiment_coding_plan_v4.py
config = SMEConfig(
    # ...其他配置...
    llm_daily_token_budget=500000,   # 从10万提升到50万
    llm_daily_request_budget=500,     # 从200提升到500
)
```

### 长期改进

1. **预算预估** - 根据历史使用预测所需预算
2. **动态调整** - 预算不足时降低LLM比例
3. **警告机制** - 预算耗尽前提前通知

---

## 五、重新运行v4

### 修复后配置

```python
hybrid_config = HybridStrategyConfig(
    mode="scheduled",
    schedule_pattern=["ast", "ast", "llm"],
    llm_budget_fraction=0.50,
    llm_cooldown_generations=0,
)

config = SMEConfig(
    enable_llm_mutation=True,
    llm_provider='bailian',
    llm_model='qwen3-coder-plus',
    llm_daily_token_budget=500000,  # 关键修复
    llm_daily_request_budget=500,    # 关键修复
    # ...其他配置...
)
```

### 预期结果

- LLM调用: ~30次 (完整30代)
- 最高Fitness: >0.70 (超越v3的0.6954)
- 最终提升: >1.0% (超越v3的0.86%)

---

## 六、教训

1. **预算配置必须足够** - 10万token只够7代，需要50万+
2. **监控budget_remaining** - 及时发现预算耗尽
3. **v3的成功不可复制** - 除非解决预算问题

---

**结论**: v4实验因token预算不足失败，修复后需重新运行。
