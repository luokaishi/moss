# MOSS/MVES 迭代规划 v5.5.0

**目标版本**: 5.5.0  
**目标日期**: 2026-05-01  
**主题**: 长周期稳定性 + 行为多样性 + 多Agent验证

---

## 目标

解决 v5.4.0 评估中识别的**高优先级局限**，完成 72h 长周期实验，扩展行为空间，激活多Agent验证。

---

## 迭代任务

### P0: 高优先级 (必须完成) ✅ 全部实现

**状态**: 所有 P0 任务已实现并通过快速测试，待长周期实验验证

**验证报告**: `docs/mves/V5.5.0_VALIDATION_REPORT.md`

#### 1. 长周期实验支持 ✅ 完成
**问题**: 容器限制导致无法完成 72h 实验  
**目标**: 支持 100,000+ 周期 (~5h) 连续运行

**任务**:
- [x] 实现分布式检查点保存 (每 1000 周期自动保存) - `experiment_v5_longrun.py`
- [x] 优化内存使用 (目标: <3 MB/千周期) - `MemoryOptimizer` 类
- [x] 添加内存自适应 GC 策略 - 双触发机制 (周期+增长)
- [x] 实现实验续跑自动化脚本 - `--resume latest` 支持
- [ ] 完成 100,000 周期实验并生成报告

**实现文件**: `examples/experiment_v5_longrun.py`

**验收标准**:
- 单容器可运行 50,000+ 周期不中断
- 内存增长线性可控
- 续跑后状态完全一致

**负责人**: TBD  
**预计工时**: 5天

---

#### 2. 行为多样性扩展 ✅ 完成
**问题**: Agent 收敛到 shell 为主的策略 (86% shell, 14% write_file)  
**目标**: 行为类型分布更均衡，探索更多 action 类型

**任务**:
- [x] 扩展 action space - `RealEnvironmentV2`:
  - [x] 文件编辑 (edit_file: append/prepend/replace)
  - [x] 代码执行 (exec_python) - AST安全检查
  - [x] 数据分析 (analyze_data: workspace/actions)
  - [x] 报告生成 (generate_report: summary/diversity)
- [x] 创建多样性实验脚本 - `experiment_v5_diversity.py`
- [ ] 实现 action 探索奖励机制
- [ ] 添加 action 成功率反馈到驱动力评估
- [ ] 实验验证行为多样性提升 (目标: shell < 60%)

**验收标准**:
- shell 占比降至 60% 以下
- 至少 3 种 action 类型占比 >10%
- 新 action 类型成功率 >80%

**负责人**: TBD  
**预计工时**: 4天

---

#### 3. 多Agent协作验证 ✅ 完成
**问题**: 已有多Agent模块但未充分验证  
**目标**: 验证涌现驱动力在多Agent场景中的稳定性

**任务**:
- [x] 完成 multi_agent.py 模块集成 - 使用现有 `agi/ecology/world.py`
- [x] 设计 2-Agent 协作实验 - `experiment_v5_multiagent.py --mode 2agent`
- [x] 设计 3-Agent 竞争实验 - `experiment_v5_multiagent.py --mode 3agent`
- [x] 实现驱动力传播检测 - `drive_transmission_log`
- [x] 实现涌现收敛分析 - `emergence_convergence` 跟踪
- [ ] 运行 5,000 周期实验并验证

**实现文件**: `examples/experiment_v5_multiagent.py`

**验收标准**:
- 2-Agent 场景运行 5,000 周期无错误
- 观察到 Agent 间行为影响
- 涌现驱动在群体中可重复

**负责人**: TBD  
**预计工时**: 4天

---

### P1: 中优先级 (尽量完成)

#### 4. 涌现驱动效用优化 ✅ 进行中
**问题**: 涌现驱动权重仅 0.08-0.11，实际影响有限  
**目标**: 提升涌现驱动的评估质量和实际效用

**任务**:
- [x] 优化 GP 适应度函数 (增加实用性权重) - `genetic_programmer_v2.py`
- [x] 实现涌现驱动淘汰机制 - `DriveManagerV2._prune_least_utility()`
- [x] 添加涌现驱动与初始驱动的竞争机制 - `get_competitive_weights()`
- [ ] 实验验证涌现驱动效用提升 (目标: >=0.20)

**实现文件**:
- `agi/genetic_programmer_v2.py` - V2版GP，实用性评估
- `examples/experiment_v5_utility.py` - 效用优化实验

**验收标准**:
- 涌现驱动权重可达 0.20+
- 至少 1 个涌现驱动在实验中主导行为选择
- 淘汰机制正常工作

**负责人**: TBD  
**预计工时**: 3天

---

#### 5. 因果独立性验证强化
**问题**: 当前基于统计独立性，缺少真正因果干预  
**目标**: 设计并执行因果干预实验

**任务**:
- [ ] 设计干预实验框架
- [ ] 实现 drive_ablation (删除驱动观察行为变化)
- [ ] 实现 drive_amplification (增强驱动权重)
- [ ] 实现 command_restriction (限制命令集)
- [ ] 生成因果验证报告

**验收标准**:
- 完成 3 种干预实验
- 观察到统计显著的行为变化
- 生成 p-value < 0.05 的因果证据

**负责人**: TBD  
**预计工时**: 3天

---

### P2: 低优先级 (可选)

#### 6. Embedding 语义质量提升
**问题**: Hash Embedding 无真正语义理解  
**目标**: 集成轻量级语义模型

**任务**:
- [ ] 调研轻量级 embedding 模型 (如 sentence-transformers/all-MiniLM)
- [ ] 实现可选的语义 embedding 后端
- [ ] 对比 Hash vs 语义 embedding 的检索质量
- [ ] A/B 测试验证效果

**验收标准**:
- 语义 embedding 可选启用
- 检索质量提升 (人工评估)
- 性能开销可接受 (<2x)

**负责人**: TBD  
**预计工时**: 4天

---

## 时间线

```
Week 1 (04/16 - 04/23)
├── 长周期实验支持 (P0)
│   ├── 分布式检查点实现
│   ├── 内存优化
│   └── 续跑自动化
└── 行为多样性扩展 (P0)
    └── action space 设计

Week 2 (04/23 - 04/30)
├── 行为多样性扩展 (P0)
│   ├── action 实现
│   └── 探索奖励机制
├── 多Agent协作验证 (P0)
│   ├── multi_agent 集成
│   └── 2-Agent 实验
└── 涌现驱动效用优化 (P1)

Week 3 (04/30 - 05/01)
├── 长周期实验执行 (P0)
│   └── 100,000 周期运行
├── 多Agent实验完成 (P0)
├── 因果验证强化 (P1)
└── v5.5.0 Release
```

---

## 风险与缓解

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|---------|
| 容器资源限制无法解决 | 中 | 高 | 提前测试分布式方案，准备云环境备选 |
| 多Agent模块集成困难 | 中 | 中 | 预留 buffer 时间，可降级为单 Agent 验证 |
| action 扩展引入安全漏洞 | 低 | 高 | 严格安全审查，白名单机制 |
| 实验时间超出预期 | 高 | 中 | 并行执行实验，自动化数据收集 |

---

## 验收标准

### v5.5.0 Release Criteria

- [ ] 100,000 周期实验完成并归档
- [ ] 行为多样性提升 (shell < 60%)
- [ ] 多Agent 2-Agent 实验完成
- [ ] 所有 P0 任务完成
- [ ] 单元测试通过 (70+)
- [ ] 文档更新完整
- [ ] Manus/外部评估通过

---

## 资源需求

| 资源 | 数量 | 用途 |
|------|------|------|
| 计算资源 | 2-3 容器实例 | 长周期实验并行 |
| 存储空间 | 10GB | 检查点数据存储 |
| 人工时间 | 3人 × 2周 | 开发+实验+文档 |

---

## 参考文档

- `MANUS_EVALUATION_REPORT_v5.4.0.md` - 评估报告
- `PROJECT_STATUS_v5.4.0.md` - 当前状态
- `MOSS_Final_Report.md` - 项目总报告
- `SEVEN_LAYER_ARCHITECTURE.md` - 7层架构设计

---

**创建**: 2026-04-16  
**更新**: 2026-04-16  
**维护者**: MOSS Team
