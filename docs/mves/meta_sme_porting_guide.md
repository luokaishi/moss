# MVES Phase 1 - Meta-SME 移植指南

**日期**: 2026-04-19  
**版本**: v7.1.0-dev  
**状态**: 🚧 进行中

---

## 概述

本文档描述将 main 分支的 Meta-SME（元自修改引擎）移植到 mves 分支的过程。

### 移植目标

结合 main 分支的代码级自我修改能力与 mves 分支的工程化优势：
- ✅ 代码级自我修改 (AST 级别)
- ✅ 沙箱测试环境
- ✅ 37+ 环境支持
- ✅ 统计验证框架
- ✅ 完整文档

---

## 移植组件

### 1. 核心模块

| 文件 | 描述 | 来源 |
|------|------|------|
| `agi/meta_sme.py` | Meta-SME 核心引擎 | main → mves |
| `agi/meta_sme_integration.py` | 与 mves 驱动系统集成 | 新建 |
| `tests/test_meta_sme.py` | 单元测试 | 新建 |

### 2. 功能映射

#### main 分支 → mves 分支

| main 组件 | mves 对应 | 状态 |
|-----------|-----------|------|
| `core/meta_cognition.py` | `agi/meta_sme.py` | ✅ 已移植 |
| `core/self_awareness.py` | `agi/meta_drive/self_model.py` | ✅ 已存在 |
| `core/self_optimization_v2.py` | `agi/meta_sme.py::MetaSME` | ✅ 已整合 |
| `v2/core/self_modifying_agent.py` | `agi/meta_sme_integration.py` | ✅ 已适配 |

---

## 架构对比

### main 分支架构

```
core/
├── meta_cognition.py          # 元认知
├── self_awareness.py          # 自我意识
├── self_optimization_v2.py    # 自优化
└── self_reflection.py         # 自我反思

v2/core/
└── self_modifying_agent.py    # 自修改 Agent
```

### mves 分支架构 (移植后)

```
agi/
├── meta_sme.py                # Meta-SME 引擎 (NEW)
├── meta_sme_integration.py    # 集成层 (NEW)
├── meta_drive/
│   ├── meta_controller.py     # 元控制器 (已存在)
│   ├── self_model.py          # 自我模型 (已存在)
│   └── ...
└── drive_manager.py           # 驱动管理器 (已存在)
```

---

## 核心功能

### Meta-SME 引擎

```python
from agi.meta_sme import MetaSME, ModificationType

# 创建引擎
meta_sme = MetaSME(
    enable_auto_modify=False,      # 不自动修改
    require_human_approval=True     # 需要人工审核
)

# 生成修改提案
proposal = meta_sme.generate_proposal(
    target_module="agi.drive_manager",
    mod_type=ModificationType.WEIGHT_ADJUSTMENT,
    description="调整好奇心驱动权重",
    ast_patch={'new_code': '...'},
    expected_impact={'min_performance_improvement': 0.01}
)

# 审核提案
meta_sme.review_proposal(proposal.proposal_id, approved=True)
```

### 驱动系统集成

```python
from agi.meta_sme_integration import MetaSMEDriveIntegration

# 创建集成器
integration = MetaSMEDriveIntegration(
    meta_sme=meta_sme,
    drive_manager=drive_manager
)

# 记录驱动性能
integration.record_drive_performance(
    drive_name='curiosity',
    avg_reward=0.6,
    activation_frequency=0.5,
    success_rate=0.8
)

# 提议权重调整
proposals = integration.propose_weight_adjustments()
```

---

## 安全机制

### 修改类型安全级别

| 类型 | 级别 | 自动应用 | 需要审核 |
|------|------|----------|----------|
| WEIGHT_ADJUSTMENT | SAFE | 可选 | 建议 |
| PARAMETER_UPDATE | SAFE | 可选 | 建议 |
| STRATEGY_CHANGE | MODERATE | 否 | 必须 |
| STRUCTURE_MODIFICATION | HIGH | 否 | 必须 |
| SAFETY_RULE_UPDATE | CRITICAL | 否 | 必须 |

### 保护模块

以下模块禁止自动修改：
- `agi.safety.*`
- `agi.security.*`
- `agi.emergency_stop.*`

---

## 环境支持

### 37+ 环境配置

```python
from agi.meta_sme_integration import EnvironmentAwareMetaSME

# 创建环境感知适配器
env_aware = EnvironmentAwareMetaSME(integration)

# 设置环境类型
env_aware.set_environment('textworld')  # 或 'atari', 'procgen'

# 获取环境配置
config = env_aware.get_environment_config()
```

### 环境特定参数

| 环境 | 权重调整阈值 | 性能窗口 | 自动调整 |
|------|-------------|----------|----------|
| textworld | 0.03 | 30 | 否 |
| atari | 0.05 | 100 | 否 |
| procgen | 0.04 | 50 | 否 |
| default | 0.05 | 50 | 否 |

---

## 测试

### 运行单元测试

```bash
cd /home/admin/.openclaw/workspace
python -m pytest tests/test_meta_sme.py -v
```

### 测试覆盖

- ✅ SandboxTester - 沙箱测试
- ✅ PatchVerifier - 补丁验证
- ✅ RollbackManager - 回滚管理
- ✅ MetaSME - 核心引擎
- ✅ MetaSMEDriveIntegration - 驱动集成
- ✅ EnvironmentAwareMetaSME - 环境适配

---

## Phase 1 完成标准

- [x] Meta-SME 核心引擎实现
- [x] 与 mves 驱动系统集成
- [x] 37+ 环境支持
- [x] 单元测试 (12+ 测试)
- [ ] 集成测试
- [ ] 文档完善
- [ ] 代码审查

---

## 下一步

### Phase 2: 统计验证

1. 设计 Meta-SME 验证实验
2. 运行 57K 周期测试
3. 统计分析 (N≥30)
4. 生成验证报告

### Phase 3: 工程化

1. 统一版本号 v7.1.0
2. 清理实验环境
3. 完善 CI/CD
4. 发布 v7.1.0

---

## 参考

- main 分支: `v2/core/self_modifying_agent.py`
- mves 分支: `agi/meta_drive/`
- 评估报告: `docs/mves/BRANCH_ANALYSIS_AND_PLAN.md`

---

**创建日期**: 2026-04-19  
**维护者**: MOSS Team