# mves 分支 LLM 集成计划

**日期**: 2026-04-22  
**目标**: 将 main 分支 (v8.1.1) 的 LLM 引导变异能力集成到 mves AGI 架构  
**优先级**: P0

---

## 一、main 分支 LLM 能力清单

### 核心模块

| 文件 | 功能 | 行数 | 依赖 |
|------|------|------|------|
| `moss/core/llm_backend.py` | LLM 后端抽象层 | ~300 | ast, json |
| `moss/core/llm_mutator.py` | LLM 引导变异 | ~200 | llm_backend |
| `moss/core/hybrid_mutation.py` | Hybrid 策略 | ~150 | llm_mutator |
| `moss/core/self_modification_engine.py` | v8.1 引擎 | ~400 | 以上全部 |

### 关键特性

1. **多后端支持**: OpenAI, Anthropic, ARK (百炼), Local, Mock
2. **Token 预算管理**: 500K/天 (支持 30 代)
3. **精英保留**: 防止 fitness 退化
4. **动态阈值**: 早期探索，晚期精细
5. **7 层预验证**: AST 解析→沙盒执行→fitness 评估

---

## 二、mves 分支集成点分析

### 当前架构

```
agi/
├── genetic_programmer.py       # GP 核心 (eval 函数发现)
├── genetic_programmer_v2.py    # v2 改进
├── genetic_programmer_v3.py    # v3 改进
├── meta_sme.py                 # Meta-SME 引擎
├── meta_sme_v2.py              # v2 版本
├── meta_sme_optimizer.py       # 优化器
├── drive_competition.py        # 驱动竞争
└── self_modifying_agent.py     # 自修改 Agent
```

### 集成策略

#### 方案 A: 轻量集成 (推荐) ⭐
**目标**: 最小改动，快速验证

**行动**:
1. 复制 `moss/core/llm_backend.py` → `agi/llm_backend.py`
2. 在 `genetic_programmer_v3.py` 中添加 LLM 变异选项
3. 配置 Token 预算：500K/天

**代码改动**:
```python
# agi/genetic_programmer_v3.py (新增)
from agi.llm_backend import LLMConfig, LLMBackend

class GeneticProgrammerV3:
    def __init__(self, enable_llm=False, llm_config=None):
        self.enable_llm = enable_llm
        if enable_llm and llm_config:
            self.llm = LLMBackend(llm_config)
    
    def generate_mutation(self, current_code, fitness_history):
        if self.enable_llm and random() < self.llm_mutation_rate:
            return self.llm_guided_mutation(current_code, fitness_history)
        else:
            return self.ast_mutation(current_code)
```

**预计工作量**: 4-6 小时

---

#### 方案 B: 深度集成
**目标**: 完整 v8.1 能力

**行动**:
1. 完整复制 `moss/core/` 到 `agi/mutation/`
2. 重构 `self_modifying_agent.py` 使用新引擎
3. 集成精英保留和动态阈值

**预计工作量**: 2-3 天

---

## 三、Token 预算配置

基于 main 分支经验 (V81_EXPERIMENT_ANALYSIS.md):

```python
# 推荐配置
LLM_CONFIG = {
    'provider': 'bailian',          # 阿里云百炼
    'model': 'qwen3-coder-plus',    # 最强代码能力
    'api_key_env': 'DASHSCOPE_API_KEY',
    
    # Token 预算 (关键！)
    'llm_daily_token_budget': 500000,    # 500K/天 (支持 30 代)
    'llm_daily_request_budget': 500,     # 请求次数限制
    
    # 变异策略
    'llm_mutation_rate': 0.50,           # 50% LLM 变异
    'llm_budget_fraction': 0.50,         # 50% 预算用于 LLM
    
    # v8.1 特性
    'enable_elitism': True,              # 精英保留
    'enable_adaptive_threshold': True,   # 动态阈值
    'elite_protection_threshold': 0.95,  # 精英阈值
}
```

**成本估算**:
- 30 代实验：~500K tokens
- 成本：~$0.55 (约¥4)
- 每日预算：¥10 可支持 2-3 次实验

---

## 四、实验设计

### 验证实验 (N=5)

| 组别 | 配置 | N | 预期 |
|------|------|---|------|
| **E1** | GP-only (基线) | 5 | 负提升 (参考 main AST-only) |
| **E2** | GP + LLM (33%) | 5 | +0.5% 提升 |
| **E3** | GP + LLM (50%) + Elite | 5 | **+1.0% 提升** |

### 统计验证 (N=10)

基于 E3 最优配置，进行 N=10 重复验证：
- 每实验 30 代
- 总周期：300 代
- 预计时间：1-2 天

---

## 五、执行计划

### Day 1: 代码集成
- [ ] 复制 `llm_backend.py` → `agi/`
- [ ] 修改 `genetic_programmer_v3.py` 添加 LLM 选项
- [ ] 添加配置文件 `agi/config/llm_config.py`
- [ ] 单元测试

### Day 2: 初步验证
- [ ] 运行 E1 (基线) - 30 代
- [ ] 运行 E2 (LLM 33%) - 30 代
- [ ] 分析结果

### Day 3-4: 优化与重复
- [ ] 运行 E3 (LLM 50% + Elite) - 30 代
- [ ] 启动 N=5 重复实验
- [ ] 统计分析

### Day 5-7: 扩展验证
- [ ] N=10 完整验证
- [ ] 撰写实验报告
- [ ] 同步到 main 分支

---

## 六、风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| Token 预算不足 | 中 | 高 | 设置 500K/天，监控使用 |
| LLM 变异质量差 | 中 | 中 | 7 层预验证过滤 |
| 成本超预算 | 低 | 低 | 每日上限¥10 |
| 代码冲突 | 高 | 中 | 小步提交，频繁测试 |

---

## 七、成功标准

1. ✅ LLM 变异占比达到 50%+
2. ✅ Fitness 提升 > 0.5% (vs 基线)
3. ✅ Token 预算控制在 500K/天内
4. ✅ 无灾难性退化 (elite protection 生效)
5. ✅ N=5 统计显著 (p < 0.05)

---

## 八、下一步决策

**请确认**:
- [ ] **A**: 执行方案 A (轻量集成，4-6 小时) ⭐推荐
- [ ] **B**: 执行方案 B (深度集成，2-3 天)
- [ ] **C**: 先运行 mves 现有实验 (无 LLM)
- [ ] **D**: 其他建议

**推荐**: A → 验证 → B (如需要)

---

**参考文档**:
- `FINAL_SUMMARY.md` (main 分支)
- `V81_EXPERIMENT_ANALYSIS.md` (main 分支)
- `MANUS_EVAL_RESPONSE_ACTION_PLAN.md` (mves 分支)
