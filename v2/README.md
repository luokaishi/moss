# MOSS 2.0 架构文档

**版本**: 2.0  
**日期**: 2026-03-11  
**作者**: Cash, 伏羲

---

## 架构概述

MOSS 2.0 是 MOSS (Multi-Objective Self-organizing System) 的架构升级版本，保留品牌延续性的同时实现核心能力的重大演进。

### 版本定位

| 版本 | 核心特性 | 状态 |
|------|----------|------|
| **MOSS 1.0 (v1)** | 固定权重多目标优化 | 已完成，作为基线 |
| **MOSS 2.0 (v2)** | 自修改动态权重演化 | 开发中，当前阶段1 |

---

## 设计原则

### 1. 数据连续性
- v2可与v1实验数据对比
- v1作为基线（固定权重最优表现）
- v2验证自驱演化能力

### 2. 工程效率
- 复用已验证的安全和评估组件
- 共享基础设施（检查点、日志、安全）
- 模块化设计便于迭代

### 3. 概念一致
- 仍遵循"多目标自组织系统"核心理念
- 四目标框架不变（生存/好奇/影响/优化）
- 从"静态优化"演进为"动态演化"

---

## 目录结构

```
/workspace/projects/moss/
├── v1/                          # v1 现有实验（保留）
│   ├── core/                    # v1 核心代码
│   ├── experiments/             # 72小时实验等
│   └── ...
├── v2/                          # v2 自驱演化实验（新建）
│   ├── core/                    # v2 核心模块
│   │   ├── self_modifying_agent.py    # 自修改Agent
│   │   ├── objective_evolver.py       # 权重演化策略
│   │   └── persistent_state.py        # 跨会话状态
│   ├── environment/             # 环境模块
│   │   └── continuous_task_stream.py  # 持续任务流
│   ├── utils/                   # 工具模块
│   │   └── checkpoint_manager.py      # 检查点管理
│   └── experiments/             # v2 实验
│       └── phase1_single_agent.py     # 阶段1实验
├── shared/                      # 共享组件
│   ├── safety/                  # 安全组件（从v1复用）
│   │   └── gradient_safety_guard.py
│   ├── evaluation/              # 评估组件（从v1复用）
│   │   └── generalization_test_suite.py
│   └── mating/                  # 繁殖组件（阶段2用）
└── README.md                    # 项目文档
```

---

## 核心模块说明

### 1. SelfModifyingAgent (`v2/core/self_modifying_agent.py`)

**功能**: 可自调整目标权重的Agent核心

**关键特性**:
- 动态权重配置（WeightConfiguration）
- 权重演化策略选择（gradient_ascent / random_search / bayesian）
- 性能驱动的自适应修改
- 修改冷却期控制

**与v1区别**:
- v1: 固定权重 `[0.6, 0.1, 0.2, 0.1]`
- v2: 动态权重，根据表现自我调整

### 2. ObjectiveEvolver (`v2/core/objective_evolver.py`)

**功能**: 管理多种权重演化策略

**策略选项**:
1. **gradient_ascent**: 基于梯度上升微调
2. **random_exploration**: 大力度随机探索
3. **weighted_random**: 偏向主导权重的变异
4. **adaptive_greedy**: 自适应贪心选择
5. **population_inspired**: 种群启发式遗传算法

**自适应选择**: 根据策略历史表现自动选择最优策略

### 3. PersistentState (`v2/core/persistent_state.py`)

**功能**: 跨会话状态持久化管理

**解决v1问题**: 实验中断后状态丢失

**功能**:
- 自动保存Agent状态到磁盘
- 支持从任意检查点恢复
- 多版本状态管理
- 自动备份和清理

### 4. ContinuousTaskStream (`v2/environment/continuous_task_stream.py`)

**功能**: 永不停止的任务流

**与v1区别**:
- v1: 固定任务集，运行完即结束
- v2: 持续生成任务，永不停止

**自适应特性**:
- 根据Agent权重调整任务类型分布
- 根据Agent表现调整任务难度
- 动态奖励潜力计算

### 5. CheckpointManager (`v2/utils/checkpoint_manager.py`)

**功能**: 增强的检查点管理

**特性**:
- 定时自动保存
- 条件触发保存（性能突破、重大事件）
- 检查点分析和比较
- 智能清理策略

---

## 对比实验设计

### 基线数据（v1）
- 固定权重: `[0.6, 0.1, 0.2, 0.1]`
- 72小时实验表现
- 10,000代模拟数据
- 已验证MOSS_Original为最优静态配置

### v2实验目标
- 可变权重在同等时间/任务下的表现
- 与v1数据对比

### 成功标准
| 结果 | 结论 |
|------|------|
| v2显著优于v1 | 自修改机制有效 |
| v2收敛到接近v1 | 原权重接近最优，自修改验证有效性 |
| v2劣于v1 | 需要调整演化策略 |

---

## 阶段规划

### 阶段1：单智能体自修改（当前）
- 目标：验证单个Agent自调整权重能力
- 实验：`phase1_single_agent.py`
- 持续时间：24小时测试 / 72小时完整

### 阶段2：多智能体演化（待开发）
- 目标：验证多Agent间的权重演化竞争
- 组件：`shared/mating/mating_mixin.py`
- 预期：观察涌现的社会结构

### 阶段3：真实环境部署（待规划）
- 目标：在真实API环境中验证
- 涉及：与v1相同的API集成
- 安全：复用`shared/safety/`组件

---

## 使用说明

### 运行阶段1实验

```bash
cd /workspace/projects/moss/v2/experiments

# 测试模式（1小时）
python phase1_single_agent.py --duration 1.0

# 完整实验（24小时）
python phase1_single_agent.py --duration 24.0 --id phase1_full_001
```

### 查看结果

```python
import json

with open('/workspace/projects/moss/v2/experiments/phase1_xxx_results.json') as f:
    results = json.load(f)

print(f"总动作数: {results['summary']['total_actions']}")
print(f"权重修改: {results['summary']['weight_modifications']} 次")
print(f"最终权重: {results['final_weights']}")
```

---

## 与v1组件复用

### 复用组件（位于`shared/`）

| 组件 | 来源 | 用途 |
|------|------|------|
| gradient_safety_guard.py | v1/core/ | 安全机制 |
| generalization_test_suite.py | v1/experiments/ | 评估套件 |

### 扩展计划

- **Safety**: 新增自修改安全约束
- **Evaluation**: 新增v2专用评估指标
- **Mating**: 阶段2多智能体繁殖

---

## 技术债务与TODO

### 高优先级
- [ ] 与v1基线的并行对比实验
- [ ] 真实API集成（从v1迁移）
- [ ] 安全约束增强（防止过度自修改）

### 中优先级
- [ ] 权重演化可视化
- [ ] 性能分析仪表板
- [ ] 自动化对比报告

### 低优先级
- [ ] 支持更多演化策略
- [ ] 分布式多Agent实验
- [ ] 神经网络权重预测器

---

## 参考

- v1文档: `/workspace/projects/moss/README.md`
- v1实验: `/workspace/projects/moss/experiments/`
- 核心论文: `docs/paper_simple.pdf`

---

**最后更新**: 2026-03-11  
**状态**: Phase 1 开发完成，待测试
