# MOSS v7.1 整合计划

**日期**: 2026-04-19  
**目标**: 合并 main 的 Meta-SME 和 mves 的统计验证/工程化  
**策略**: 基于 Manus 评估报告建议

---

## 评估报告关键结论

### main 分支 (v7.0.0)

**优势**:
- ✅ Meta-SME 代码自修改实现
- ✅ 4层自我修改架构
- ✅ 9种 AST 变异类型
- ✅ 双沙箱 + 回滚保护
- ✅ Meta-fitness +26.3%

**问题**:
- ❌ 统计显著性不足 (N=1)
- ❌ 实验环境混乱
- ❌ 版本号不一致
- ❌ 可复现性差

### mves 分支 (v5.4.0 → v6.6)

**优势**:
- ✅ 57K 周期统计验证
- ✅ 86% 检出率
- ✅ 37+ 环境适配
- ✅ 完整工程化
- ✅ 生产就绪 (K8s)

**问题**:
- ❌ 无代码自修改能力
- ❌ 停留在 GP 进化 eval

---

## Manus 建议

1. **优先完善 main 的统计验证和工程化**
2. **将 mves 的验证成果整合到 main**
3. **积极探索 LLM 引导的变异生成**

---

## 整合策略

### 方案: mves 为基础，移植 Meta-SME

**理由**:
- mves 工程化完整，统计验证扎实
- main 的 Meta-SME 是核心创新
- 合并后既保留工程化，又获得自修改能力

**步骤**:

1. **以 mves 为基线** (v6.6)
   - 保持 37+ 环境
   - 保持统计验证框架
   - 保持工程化

2. **移植 Meta-SME** (从 main)
   - 提取 `self_modification_engine.py`
   - 适配 mves 模块化架构
   - 集成到 `agi/` 目录

3. **补强统计验证**
   - 使用 mves 的 57K 框架
   - 对 Meta-SME 进行 N≥30 测试
   - 生成验证报告

4. **工程化整理**
   - 统一版本号 v7.1.0
   - 清理实验环境
   - 完善文档

---

## 实施计划

### Phase 1: Meta-SME 移植 (1 周)

**任务**:
- [ ] 分析 main 的 `self_modification_engine.py`
- [ ] 创建 `agi/meta_sme/` 模块
- [ ] 适配 mves 的 Agent 架构
- [ ] 集成 37+ 环境支持
- [ ] 单元测试

**交付物**:
- `agi/meta_sme/engine.py`
- `agi/meta_sme/sandbox.py`
- `agi/meta_sme/mutators.py`
- 移植文档

### Phase 2: 统计验证 (2 周)

**任务**:
- [ ] 设计 Meta-SME 验证实验
- [ ] 运行 57K 周期测试
- [ ] N≥30 种子测试
- [ ] 统计分析 (p<0.05)
- [ ] 生成验证报告

**交付物**:
- `docs/mves/meta_sme_validation_report.md`
- 统计数据
- 可视化图表

### Phase 3: 工程化 (1 周)

**任务**:
- [ ] 统一版本号 v7.1.0
- [ ] 清理实验环境
- [ ] 更新 README
- [ ] 完善 CI/CD
- [ ] 生成 Release Notes

**交付物**:
- v7.1.0 Release
- 更新文档
- 清理后的代码库

---

## 技术细节

### Meta-SME 架构 (移植到 mves)

```
agi/meta_sme/
├── __init__.py
├── engine.py          # 核心引擎
├── sandbox.py         # 沙箱测试
├── mutators.py        # AST 变异
├── fitness.py         # 适应度评估
├── safety.py          # 安全机制
└── rollback.py        # 回滚机制
```

### 与 mves 集成

```python
# agi/agent.py (mves 风格)
from agi.meta_sme.engine import MetaSME

class Agent:
    def __init__(self):
        # mves 原有组件
        self.drive_manager = DriveManager()
        self.emergence_detector = EmergenceDetector()
        
        # 新增 Meta-SME
        self.meta_sme = MetaSME(
            sandbox=Sandbox(),
            mutators=Mutators(),
            safety=SafetyChecker()
        )
    
    def self_modify(self):
        """自我修改"""
        return self.meta_sme.modify(self)
```

### 统计验证 (使用 mves 框架)

```python
# 使用 mves 的验证框架
from agi.validation import StatisticalValidator

validator = StatisticalValidator(
    n_seeds=30,
    n_cycles=57000,
    significance_level=0.05
)

results = validator.validate_meta_sme(
    agent_class=Agent,
    metric='meta_fitness'
)

# 输出: p-value, effect_size, confidence_interval
```

---

## 预期成果

### v7.1.0 特性

| 特性 | 来源 | 说明 |
|------|------|------|
| Meta-SME | main | 代码自修改 |
| 37+ 环境 | mves | 多环境支持 |
| 57K 验证 | mves | 统计显著性 |
| K8s 部署 | mves | 生产就绪 |
| 工程化 | mves | 完整文档 |

### 目标

- **代码自修改**: ✅ Meta-SME
- **统计显著性**: ✅ N≥30, p<0.05
- **多环境**: ✅ 37+
- **生产就绪**: ✅ K8s

---

## 风险评估

| 风险 | 可能性 | 影响 | 缓解 |
|------|--------|------|------|
| Meta-SME 移植复杂 | 中 | 高 | 分模块移植，充分测试 |
| 统计验证耗时 | 中 | 中 | 并行运行，使用 GPU |
| 环境兼容问题 | 低 | 中 | 37 环境已验证 |
| 版本冲突 | 低 | 高 | 以 mves 为基线 |

---

## 时间线

```
Week 1: Meta-SME 移植
  - 分析 main 代码
  - 创建模块
  - 适配集成
  - 单元测试

Week 2-3: 统计验证
  - 设计实验
  - 运行 57K 测试
  - N≥30 种子
  - 生成报告

Week 4: 工程化
  - 统一版本
  - 清理环境
  - 更新文档
  - v7.1 Release
```

---

## 参考

- Manus 评估报告
- main: `self_modification_engine.py`
- mves: `agi/` 模块化架构
- mves: `docs/mves/` 验证框架

---

**决策**: 采用 mves 为基线，移植 Meta-SME，补强统计验证，创建 v7.1
