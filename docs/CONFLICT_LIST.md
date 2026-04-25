# MOSS 分支冲突文件清单

**版本**: 1.0  
**日期**: 2026-04-25  
**分析结果**: **无实质性代码冲突**

---

## 执行摘要

| 类别 | 数量 | 处理方式 |
|------|------|----------|
| 内容相同的文件 | 7 | 无需处理，已同步 |
| 命名空间差异 | 55 | 统一导入路径 |
| 实际代码冲突 | **0** | 无 |

**结论**: 两个分支之间**没有代码逻辑冲突**，所有差异都可以通过文件复制和导入路径更新解决。

---

## 文件分类

### 1. 内容相同的文件 (无需处理)

以下文件在 `moss/core/` 和 `agi/` 中内容完全相同，已同步:

| # | 文件名 | Main 路径 | MVES 路径 | 处理方式 |
|---|--------|-----------|-----------|----------|
| 1 | `__init__.py` | ✅ | ✅ | 已同步 |
| 2 | `auto_recovery.py` | ✅ | ✅ | 已同步 |
| 3 | `event_driven_purpose.py` | ✅ | ✅ | 已同步 |
| 4 | `hybrid_mutation.py` | ✅ | ✅ | 相同 |
| 5 | `llm_backend.py` | ✅ | ✅ | 相同 |
| 6 | `llm_mutator.py` | ✅ | ✅ | 相同 |
| 7 | `monitoring_dashboard.py` | ✅ | ✅ | 已同步 |

**处理**: ✅ 已完成，无需进一步操作

---

### 2. Main 特有文件 (需移植到 MVES)

以下文件仅在 `moss/core/` 中存在，建议选择性移植到 MVES:

| # | 文件名 | 优先级 | 说明 | 移植难度 |
|---|--------|--------|------|----------|
| 1 | `agent_bridge.py` | P1 | v9 Agent 桥接 | 低 |
| 2 | `agent_registry.py` | P1 | Agent 注册表 | 低 |
| 3 | `autonomous_loop.py` | P1 | 9维自主循环 | 中 |
| 4 | `causal_purpose.py` | P2 | 因果 Purpose | 中 |
| 5 | `config_manager.py` | P2 | 配置管理 | 低 |
| 6 | `conflict_resolver.py` | P2 | 冲突解决 | 中 |
| 7 | `conflict_resolver_enhanced.py` | P2 | 增强冲突解决 | 中 |
| 8 | `cross_file_refactor.py` | P2 | 跨文件重构 | 中 |
| 9 | `dimensions.py` | P1 | 9维定义 | 低 |
| 10 | `exceptions.py` | P0 | MossError 基类 | 低 |
| 11 | `experiment_statistics.py` | P2 | 实验统计 | 低 |
| 12 | `file_watcher.py` | P2 | 文件监控 | 低 |
| 13 | `gradient_safety_guard.py` | P2 | 梯度安全 | 高 |
| 14 | `incremental_analyzer.py` | P2 | 增量分析 | 中 |
| 15 | `llm_cost_controller.py` | ✅ | Token 预算 | 已完成 |
| 16 | `llm_verification_closed_loop.py` | P2 | LLM 验证闭环 | 高 |
| 17 | `local_llm_backend.py` | P1 | 本地 LLM | 中 |
| 18 | `lsp_server.py` | P3 | LSP 服务器 | 中 |
| 19 | `message_bus.py` | P1 | 消息总线 | 低 |
| 20 | `ml_recommender.py` | P2 | ML 推荐 | 中 |
| 21 | `multimodal_extension.py` | P3 | 多模态扩展 | 高 |
| 22 | `objectives.py` | P2 | 目标定义 | 低 |
| 23 | `parallel_analyzer.py` | P2 | 并行分析 | 中 |
| 24 | `pattern_learner.py` | P2 | 模式学习 | 中 |
| 25 | `performance_engine.py` | P2 | 性能引擎 | 中 |
| 26 | `phase2_components.py` | P2 | Phase 2 组件 | 中 |
| 27 | `plugin_system.py` | P2 | 插件系统 | 中 |
| 28 | `purpose.py` | P1 | Purpose 基类 | 低 |
| 29 | `purpose_dynamics.py` | P2 | Purpose 动态 | 中 |
| 30 | `real_world_bridge.py` | ✅ | 真实世界桥接 | 已合并 |
| 31 | `refactor_engine.py` | P2 | 重构引擎 | 中 |
| 32 | `reproducibility_kit.py` | P2 | 可复现套件 | 低 |
| 33 | `self_improvement.py` | P2 | 自我改进 | 中 |
| 34 | `self_modification_engine.py` | P2 | 自修改引擎 | 高 |
| 35 | `self_optimization_v2.py` | P2 | 自优化 v2 | 中 |
| 36 | `semantic_refactor.py` | P2 | 语义重构 | 中 |
| 37 | `split_operations.py` | P2 | 分割操作 | 低 |
| 38 | `state_decision_model.py` | P2 | 状态决策模型 | 中 |
| 39 | `statistical_validator.py` | ✅ | 统计验证 | 已完成 |
| 40 | `team_collaboration.py` | P2 | 团队协作 | 中 |
| 41 | `unified_agent.py` | P1 | 统一 Agent | 中 |

**总计**: 41 个文件 (2 个已完成)

---

### 3. MVES 特有文件 (需合并到 Main)

以下文件仅在 `agi/` 中存在，需要合并到 `moss/core/`:

| # | 文件名 | 优先级 | 说明 | 合并难度 |
|---|--------|--------|------|----------|
| 1 | `adaptive_action_selector.py` | P1 | 自适应动作选择 | 低 |
| 2 | `agent.py` | P1 | AGI Agent 基类 | 中 |
| 3 | `behavior_tracker.py` | P2 | 行为追踪 | 低 |
| 4 | `distributed_trainer.py` | P2 | 分布式训练 | 中 |
| 5 | `drive_competition.py` | P1 | 驱动力竞争 | 中 |
| 6 | `drive_manager.py` | P1 | 驱动力管理 | 中 |
| 7 | `drive_weight_cap.py` | P1 | 驱动力权重上限 | 低 |
| 8 | `emergence_detector.py` | P2 | 涌现检测 | 中 |
| 9 | `environment.py` | P1 | 环境系统 | 中 |
| 10 | `environment_v2.py` | P1 | 环境系统 v2 | 中 |
| 11 | `generalization_optimizer.py` | P2 | 泛化优化 | 高 |
| 12 | `genetic_programmer.py` | P0 | GP 系统 | 低 |
| 13 | `genetic_programmer_v2.py` | P0 | GP v2 | 低 |
| 14 | `genetic_programmer_v3.py` | P0 | GP v3 | 低 |
| 15 | `gpu_trainer.py` | P2 | GPU 训练 | 中 |
| 16 | `intervention_validator.py` | P2 | 干预验证 | 中 |
| 17 | `llm_integration.py` | P1 | LLM 集成 | 中 |
| 18 | `memory_engine.py` | P1 | 记忆引擎 | 低 |
| 19 | `meta_cognition/` | P2 | 元认知模块 | 中 |
| 20 | `meta_drive/` | P2 | 元驱动力 | 中 |
| 21 | `meta_learner.py` | P2 | 元学习 | 高 |
| 22 | `meta_sme.py` | P2 | Meta-SME | 高 |
| 23 | `meta_sme_integration.py` | P2 | Meta-SME 集成 | 高 |
| 24 | `meta_sme_optimizer.py` | P2 | Meta-SME 优化 | 高 |
| 25 | `meta_sme_v2.py` | P2 | Meta-SME v2 | 高 |
| 26 | `model_compression.py` | P2 | 模型压缩 | 高 |
| 27 | `multi_agent/` | P1 | 多 Agent 目录 | 中 |
| 28 | `multi_agent_coordinator.py` | P1 | 多 Agent 协调 | 中 |
| 29 | `mves_realworld_bridge.py` | ✅ | 真实世界桥接 | 已合并 |
| 30 | `performance_optimizer.py` | P2 | 性能优化 | 中 |
| 31 | `reward_aligner.py` | P2 | 奖励对齐 | 中 |
| 32 | `seven_layer_agent.py` | P2 | 7层 Agent | 中 |
| 33 | `task_aware_agent.py` | P1 | 任务感知 Agent | 中 |
| 34 | `task_discovery.py` | P2 | 任务发现 | 中 |
| 35 | `task_scenarios.py` | P2 | 任务场景 | 低 |
| 36 | `textworld_*.py` | P3 | TextWorld 相关 (6个) | 中 |

**总计**: 36 个文件 (1 个已合并)

---

## 合并行动计划

### Phase 1: P0 核心组件 (立即执行)

```bash
# GP 系统 (MVES 领先)
cp agi/genetic_programmer.py moss/core/
cp agi/genetic_programmer_v2.py moss/core/
cp agi/genetic_programmer_v3.py moss/core/

# 驱动力系统 (MVES 领先)
cp agi/drive_manager.py moss/core/
cp agi/drive_competition.py moss/core/
cp agi/drive_weight_cap.py moss/core/

# 环境系统 (MVES 领先)
cp agi/environment.py moss/core/
cp agi/environment_v2.py moss/core/
```

### Phase 2: P1 重要组件 (本周完成)

```bash
# Agent 系统整合
# - 需要合并 agent.py 和 agent_bridge.py 的功能
# - 保留统一的 Agent 抽象

# 多 Agent 系统
cp agi/multi_agent_coordinator.py moss/core/
cp -r agi/multi_agent/ moss/core/multi_agent/

# 任务感知
cp agi/task_aware_agent.py moss/core/
```

### Phase 3: P2 辅助组件 (下周完成)

```bash
# 元学习系统
cp agi/meta_learner.py moss/core/
cp agi/meta_sme*.py moss/core/

# 其他辅助组件...
```

---

## 导入路径更新清单

合并后需要更新的导入语句:

| 原导入 | 新导入 | 文件数 |
|--------|--------|--------|
| `from agi import X` | `from moss.core import X` | ~50 |
| `from agi.agent import Y` | `from moss.core.agent import Y` | ~20 |
| `from agi.drive_manager import Z` | `from moss.core.drive_manager import Z` | ~15 |

**建议**: 使用 IDE 批量重构功能或 `sed` 命令批量替换。

---

## 结论

1. **无冲突**: 两个分支之间没有代码逻辑冲突
2. **仅路径**: 所有差异都是命名空间和文件位置
3. **可合并**: 通过文件复制和导入更新即可完成合并
4. **分阶段**: 建议按 P0/P1/P2 优先级分阶段执行

---

*清单版本: 1.0*  
*基于: ARCHITECTURE_DIFFERENCE_REPORT.md*
