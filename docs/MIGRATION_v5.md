# MOSS v5.0 统一架构迁移指南

**日期**: 2026-03-25
**版本**: 5.0.0-dev

---

## 🎯 迁移目标

将分散的 v2/v3/v4 代码整合为统一架构：
- `moss/core/` - 核心模块（统一接口）
- `moss/experiments/` - 实验框架（标准化）

---

## 📁 新架构结构

```
moss/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── unified_agent.py    # 统一Agent基类
│   ├── objectives.py        # 标准化目标模块
│   └── purpose.py           # Purpose Generator (待迁移)
├── experiments/
│   ├── __init__.py
│   └── base.py              # 标准实验框架
└── agents/
    └── (原有v1/v2 agent)
```

---

## 🔄 迁移映射

| 旧代码 | 新代码 | 状态 |
|--------|--------|------|
| `v3/core/agent_9d.py` | `moss/core/unified_agent.py` | ✅ 已整合 |
| `v3/core/agent_8d.py` | `moss/core/unified_agent.py` | ✅ 已整合 |
| `v3/core/purpose.py` | `moss/core/purpose.py` | ⏳ 待迁移 |
| `v4/integration/agent_v4*.py` | `moss/core/unified_agent.py` | ✅ 已整合 |
| `core/objectives.py` | `moss/core/objectives.py` | ✅ 已标准化 |
| 各版本实验脚本 | `moss/experiments/base.py` | ✅ 已标准化 |

---

## 💻 使用示例

### 旧方式 (v3)
```python
from v3.core.agent_9d import MOSSv3Agent9D

agent = MOSSv3Agent9D(
    agent_id="test",
    enable_purpose=True,
    purpose_interval=2000
)
```

### 新方式 (v5)
```python
from moss.core import UnifiedMOSSAgent, MOSSConfig

config = MOSSConfig(
    agent_id="test",
    enable_purpose=True,
    purpose_interval=2000
)
agent = UnifiedMOSSAgent(config)
```

---

## 🧪 实验框架示例

### 旧方式
```python
# 各版本实验各自实现循环、日志、报告
```

### 新方式
```python
from moss.experiments import ExperimentConfig, SimpleMOSSExperiment

config = ExperimentConfig(
    experiment_id="my_exp",
    duration_steps=10000,
    output_dir="experiments/results"
)

exp = SimpleMOSSExperiment(config)
result = exp.run()
```

---

## ⚠️ 已知限制

1. **Purpose Generator** 尚未完全迁移（当前为新框架预留接口）
2. **真实世界桥接** 需要适配新接口
3. **v2/v3/v4历史实验** 保持兼容，建议新实验使用v5框架

---

## 📋 下一步迁移任务

- [ ] 完整迁移 Purpose Generator
- [ ] 迁移 RealWorldBridge 到统一接口
- [ ] 创建 v5 使用教程
- [ ] 将 Run 4.x 实验重构为新框架
- [ ] 将 72h 实验重构为新框架

---

## ✅ 已完成

- [x] 统一 Agent 基类
- [x] 标准化目标模块
- [x] 标准实验框架
- [x] 配置管理系统
