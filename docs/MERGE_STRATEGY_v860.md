# mves v8.6.0 → main 合并策略

**日期**: 2026-04-23  
**目标**: 将mves v8.6.0的核心组件合并到main，统一为v9.0

---

## 1. 架构差异分析

### 1.1 目录结构对比

| 目录 | main (v8.3.0) | mves (v8.6.0) | 差异 |
|------|--------------|--------------|------|
| `moss/core/` | 24个核心模块 | 不存在 | main独有 |
| `agi/` | 2个文件 | **78个文件** | mves远大 |
| `experiments/` | ~10个文件 | ~15个文件 | 部分重叠 |
| `docs/` | 大量 | 大量 | 结构不同 |
| 根目录散落文件 | ~30个 | **~300+** | mves臃肿 |

### 1.2 核心模块对应关系

| 功能 | main | mves | 合并策略 |
|------|------|------|----------|
| SME自改写引擎 | `moss/core/self_modification_engine.py` | `agi/meta_sme.py` | 保留main |
| LLM Backend | `moss/core/llm_backend.py` | `agi/llm_backend.py` | 保留main(更完善) |
| LLM Mutator | `moss/core/llm_mutator.py` | `agi/llm_mutator.py` | 保留main |
| Hybrid Strategy | `moss/core/hybrid_mutation.py` | `agi/hybrid_mutation.py` | 保留main |
| Task Agent | `agi/task_aware_agent.py` | `agi/task_aware_agent.py` | ⚠️ 冲突-取mves |
| Task Scenarios | `agi/task_scenarios.py` | `agi/task_scenarios.py` | ⚠️ 冲突-取mves |
| GP引擎 | 无 | `agi/genetic_programmer*.py` | 新增mves |
| 多Agent | 无 | `agi/multi_agent/` | 新增mves |
| 真实世界桥接 | `moss/core/real_world_bridge.py` | `agi/mves_realworld_bridge.py` | 两者都保留 |
| 事件驱动 | 无 | `agi/event_driven_purpose.py` | 新增mves |
| 监控仪表盘 | 无 | `agi/monitoring_dashboard.py` | 新增mves |
| 自动恢复 | 无 | `agi/auto_recovery.py` | 新增mves |

### 1.3 冲突文件清单

仅2个冲突：
1. `agi/task_aware_agent.py` → 采用mves版本（更完整）
2. `agi/task_scenarios.py` → 采用mves版本（更多场景）

---

## 2. 合并策略

### 2.1 选择性合并（非直接merge）

**原因**: mves根目录有300+散落文件(report_*.json, test_*.py等)，直接merge会严重污染main。

**策略**: 只挑选核心组件文件合并，跳过历史实验数据。

### 2.2 合并清单

#### 新增到main（来自mves的核心组件）

```
agi/
├── agent.py                          # 基础Agent
├── adaptive_action_selector.py       # 自适应动作选择
├── auto_recovery.py                  # 自动恢复 ⭐ v8.6
├── behavior_tracker.py               # 行为追踪
├── drive_competition.py              # 驱动力竞争
├── drive_manager.py                  # 驱动力管理
├── drive_weight_cap.py              # 驱动力权重限制
├── emergence_detector.py             # 涌现检测
├── environment.py                    # 环境
├── environment_v2.py                 # 环境v2
├── event_driven_purpose.py           # 事件驱动Purpose ⭐ v8.6
├── genetic_programmer.py             # GP引擎
├── genetic_programmer_v2.py          # GP引擎v2
├── genetic_programmer_v3.py          # GP引擎v3
├── memory_engine.py                  # 记忆引擎
├── meta_learner.py                   # 元学习
├── meta_sme.py                       # Meta-SME
├── meta_sme_v2.py                    # Meta-SME v2
├── monitoring_dashboard.py           # 监控仪表盘 ⭐ v8.6
├── multi_agent/                      # 多Agent目录
│   ├── __init__.py
│   └── coordinator.py
├── multi_agent_coordinator.py        # 多Agent协调
├── mves_realworld_bridge.py          # 真实世界桥接 ⭐ v8.5
├── self_modifying_agent.py           # 自修改Agent
├── seven_layer_agent.py              # 七层Agent
├── task_discovery.py                 # 任务发现
├── analysis/                         # 分析模块
├── causal/                           # 因果推理
├── concept/                          # 概念系统
├── config/                           # 配置
├── ecology/                          # 生态
├── goal/                             # 目标
├── learning/                         # 学习
├── meta_cognition/                   # 元认知
├── meta_drive/                       # 元驱动
├── representation/                   # 表征
├── safety/                           # 安全
└── ...
```

#### 更新到main（覆盖冲突文件）
```
agi/task_aware_agent.py  → mves版本
agi/task_scenarios.py    → mves版本
```

#### 跳过（mves历史数据，不合并）
```
report_diversity_*.json     (317个实验报告)
report_summary_*.json      (317个摘要报告)
*.md 散落报告文件           (已提取关键数据到data/mves_validation/)
test_*.py 根目录测试文件
experiment_*.py 根目录实验
```

#### 保留main独有（不覆盖）
```
moss/core/                  # main的核心SME引擎（完整保留）
moss/core/self_modification_engine.py  # v8.1.1增强版
moss/core/llm_backend.py    # 含BailianBackend
moss/core/llm_mutator.py    # 函数级提取优化
moss/core/hybrid_mutation.py # 调度模式修复
moss/core/local_llm_backend.py # 本地模型支持
```

---

## 3. 执行计划

### Phase 1: 创建合并分支
```bash
git checkout -b merge-mves-v860 main
```

### Phase 2: 选择性文件拷贝
```bash
# 从mves提取核心agi文件
git checkout origin/mves -- agi/  # 整个agi目录
# 恢复main独有的moss/core/（不会被覆盖因为mves没有此目录）
```

### Phase 3: 解决冲突
- `agi/task_aware_agent.py`: 采用mves版本
- `agi/task_scenarios.py`: 采用mves版本

### Phase 4: 版本统一
- 更新版本号到v9.0.0-dev
- 更新README/CHANGELOG
- 清理mves散落文件

### Phase 5: 测试验证
- 运行demo.py
- 运行核心模块导入测试
- 验证SME引擎功能

---

## 4. 风险评估

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| agi/目录冲突 | 高 | 低 | 仅2个文件，取mves版 |
| import路径问题 | 中 | 中 | 需要修复agi/内部引用 |
| moss/core与agi功能重叠 | 低 | 中 | 两者互补，不冲突 |
| mves散落文件污染 | 高 | 中 | 选择性合并，跳过历史数据 |

---

*策略版本: v1.0*  
*生成时间: 2026-04-23*
