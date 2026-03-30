# MVES v5 实施计划（mves-integration 分支限定）

**编制时间**: 2026-03-30 19:50 GMT+8  
**权限范围**: 仅限 mves-integration 分支  
**目标**: 最小可验证演化系统（MEAP）

---

## 🎯 约束条件

### 权限限制

| 操作 | 主分支 | mves 分支 | 状态 |
|------|--------|----------|------|
| 修改主分支代码 | ❌ 无权限 | - | 不可行 |
| 修改 mves 分支代码 | - | ✅ 有权限 | 可行 |
| 读取主分支代码 | ✅ 只读 | ✅ 只读 | 可参考 |
| 提交到 main | ❌ 无权限 | - | 不可行 |
| 提交到 mves | - | ✅ 有权限 | 可行 |
| 发起 PR | ✅ 可以 | ✅ 可以 | 推荐 |

### 策略

**核心原则**:
1. 所有开发在 mves 分支内完成
2. 参考主分支设计，但不直接修改
3. 成熟后通过 PR 贡献到主分支
4. 保持 mves 分支的独立性和完整性

---

## 📊 当前状态总览

### 已完成（2/6）

| 模块 | 文件 | 状态 | 测试 |
|------|------|------|------|
| **设计文档** | DESIGN.md | ✅ 完成 | - |
| **演化智能体** | agent.py | ✅ 完成 | ✅ 通过 |

### 待实现（4/6）

| 模块 | 文件 | 优先级 | 预计工时 |
|------|------|--------|---------|
| **演化引擎** | evolution.py | 🔴 高 | 4-6h |
| **环境系统** | environment.py | 🔴 高 | 3-4h |
| **指标系统** | metrics.py | 🟡 中 | 2-3h |
| **主程序** | main.py | 🔴 高 | 3-4h |

---

## 🗺️ 实施路线图

### Phase 1: 核心实现（本周，12-17 小时）

**目标**: 完成可运行的最小演化系统

**任务**:
1. 🔴 evolution.py（演化引擎）
   - 种群管理
   - 选择压力实现
   - 繁殖机制
   - 检查点保存

2. 🔴 environment.py（环境系统）
   - 30x30 网格环境
   - 资源再生机制
   - 环境变化阶段
   - 结构建造支持

3. 🔴 metrics.py（指标系统）
   - 演化指标（非行为指标）
   - 多样性计算
   - 复杂度计算
   - 新能力检测

4. 🔴 main.py（主程序）
   - 实验配置
   - 演化循环
   - 日志记录
   - 对照实验支持

**产出**: 可运行的 168h 实验系统

---

### Phase 2: 实验验证（下周，16-24 小时）

**目标**: 运行完整实验并收集数据

**任务**:
1. 🟡 运行 168h 实验
   - A 组（自驱力）
   - B 组（任务驱动）
   - C 组（RL）
   - D 组（Planning）

2. 🟡 数据收集
   - 每 10 代检查点
   - 指标记录
   - 日志保存

3. 🟡 数据分析
   - 演化轨迹
   - 对照组对比
   - 统计显著性

**产出**: 完整实验数据集

---

### Phase 3: 论文准备（本月，40-60 小时）

**目标**: 准备 NeurIPS/ICLR 投稿

**任务**:
1. 🟡 命题重构（存在性而非必要性）
2. 🟡 因果模型补充
3. 🟡 实验数据可视化
4. 🟡 论文撰写
5. ⚪ 投稿准备

**产出**: 完整论文 + 数据集

---

## 📁 文件结构（mves 分支）

```
mves-integration/
├── mves_v5/                    ← 新实验系统
│   ├── DESIGN.md               ✅ 完成
│   ├── README.md               ✅ 完成
│   ├── IMPLEMENTATION_PLAN.md  ✅ 本文件
│   ├── agent.py                ✅ 完成
│   ├── evolution.py            ⏳ 待实现
│   ├── environment.py          ⏳ 待实现
│   ├── metrics.py              ⏳ 待实现
│   └── main.py                 ⏳ 待实现
│
├── mves_v1-v4/                 ← 历史实验
│   └── ...                     ✅ 完成
│
├── experiments/
│   ├── real_world_72h_experiment.py  ← 主分支兼容版
│   └── objective_system_moss_compatible.py  ← 权重系统
│
└── docs/
    ├── CHATGPT_EVALUATION_AND_MVES_PROGRESS.md  ← 评估分析
    ├── RESPONSE_TO_CRITICAL_EVALUATION.md       ← 评估回应
    └── MOSS_MAIN_BRANCH_IMPROVEMENT_PROPOSAL.md ← 主分支改进
```

---

## 🔧 立即行动（Phase 1）

### 任务 1: evolution.py（4-6 小时）

**核心功能**:
```python
class EvolutionEngine:
    def __init__(self, config):
        self.population = []
        self.generation = 0
        self.config = config
    
    def run_generation(self):
        """运行一代演化"""
        # 1. 每个 agent 行动
        for agent in self.population:
            action = agent.decide()
            result = agent.execute(action, self.environment)
            agent.learn(result)
        
        # 2. 应用选择压力
        deaths = 0
        for agent in self.population:
            outcome = self.environment.apply_selection_pressure(agent)
            if outcome == "death":
                deaths += 1
        
        # 3. 繁殖（优秀个体）
        top_agents = self._select_top_agents()
        for parent in top_agents:
            child = parent.clone()
            child.genome.mutate()
            self.population.append(child)
        
        # 4. 记录指标
        self.generation += 1
        return {'deaths': deaths, 'births': len(top_agents)}
```

**优先级**: 🔴 最高

---

### 任务 2: environment.py（3-4 小时）

**核心功能**:
```python
class Environment:
    def __init__(self, size=(30, 30), initial_resources=3000):
        self.size = size
        self.resources = initial_resources
        self.structures = {}
        self.changelog = {}
    
    def apply_selection_pressure(self, agent):
        """应用选择压力"""
        if agent.energy <= 0:
            agent.die()
            return "death"
        elif agent.energy < 30:
            agent.lose_memory(50%)
            agent.lose_resources(30%)
            return "resource_penalty"
        elif agent.fitness < self.threshold:
            agent.probability_of_death = 0.3
            return "selection_risk"
        return "survived"
    
    def add_phase_change(self, hour, phase_config):
        """环境变化阶段"""
        # Phase 1 (0-48h): 稳定
        # Phase 2 (48-96h): 资源减少 50%
        # Phase 3 (96-144h): 新工具可用
        # Phase 4 (144-168h): 环境重构
        pass
```

**优先级**: 🔴 高

---

### 任务 3: metrics.py（2-3 小时）

**核心功能**:
```python
class EvolutionMetrics:
    @staticmethod
    def behavior_diversity(population):
        """行为多样性（熵）"""
        strategies = [agent.strategy for agent in population]
        return entropy(strategies)
    
    @staticmethod
    def strategy_complexity(agent):
        """策略复杂度"""
        depth = agent.strategy.get_depth()
        branches = agent.strategy.count_branches()
        return depth * branches
    
    @staticmethod
    def novel_capabilities(population, baseline):
        """未预设能力"""
        observed = set()
        for agent in population:
            observed.update(agent.get_capabilities())
        return observed - baseline
    
    @staticmethod
    def long_term_improvement(history):
        """长期性能提升"""
        if len(history) < 2:
            return 0.0
        return (history[-1] - history[0]) / history[0]
```

**优先级**: 🟡 中

---

### 任务 4: main.py（3-4 小时）

**核心功能**:
```python
def main():
    # 配置
    config = {
        'duration_hours': 168,
        'agent_count': 20,
        'environment_size': (30, 30),
        'checkpoint_interval': 10
    }
    
    # 初始化
    engine = EvolutionEngine(config)
    environment = Environment()
    
    # 运行实验
    for hour in range(config['duration_hours']):
        # 应用环境变化阶段
        environment.apply_phase_change(hour)
        
        # 运行一代
        result = engine.run_generation()
        
        # 记录指标
        metrics = record_metrics(engine.population)
        log(metrics)
        
        # 保存检查点
        if engine.generation % config['checkpoint_interval'] == 0:
            save_checkpoint(engine.population, engine.generation)
    
    # 生成报告
    generate_report(engine.history)
```

**优先级**: 🔴 高

---

## 📊 时间估算

| 阶段 | 任务 | 预计工时 | 累计 |
|------|------|---------|------|
| **Phase 1** | evolution.py | 4-6h | 4-6h |
| | environment.py | 3-4h | 7-10h |
| | metrics.py | 2-3h | 9-13h |
| | main.py | 3-4h | 12-17h |
| **Phase 2** | 实验运行 | 8h | 20-25h |
| | 数据分析 | 8-16h | 28-41h |
| **Phase 3** | 论文准备 | 40-60h | 68-101h |

---

## 🎯 成功标准

### Phase 1 成功
- ✅ evolution.py 实现完成
- ✅ environment.py 实现完成
- ✅ metrics.py 实现完成
- ✅ main.py 实现完成
- ✅ 快速测试通过（1h）

### Phase 2 成功
- ✅ 168h 实验完成
- ✅ 4 组对照实验完成
- ✅ 数据完整收集
- ✅ 初步分析报告

### Phase 3 成功
- ✅ 论文完成
- ✅ 数据可视化完成
- ✅ 投稿准备完成
- ✅ 提交到 arXiv/会议

---

## 🔄 与主分支的协作

### 当前策略

1. **独立开发**（mves 分支内）
   - 所有代码在 mves 分支
   - 不修改主分支代码
   - 保持独立性

2. **参考设计**（只读主分支）
   - 参考主分支架构
   - 学习主分支经验
   - 不直接复制

3. **贡献回主分支**（通过 PR）
   - 成熟后发起 PR
   - 附带完整测试
   - 附带实验数据

### 未来整合点

| mves 成果 | 主分支整合点 | 方式 |
|----------|-------------|------|
|演化智能体 | experiments/ | PR 添加 |
|演化引擎 | experiments/ | PR 添加 |
|指标系统 | core/ | PR 添加 |
|实验数据 | experiments/integrated_data/ | PR 添加 |
|论文 | docs/papers/ | PR 添加 |

---

## ⚠️ 风险管理

### 技术风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 演化系统不稳定 | 中 | 高 | 优秀个体保护机制 |
| 种群过早收敛 | 中 | 高 | 维持变异率 15% |
| 实验运行崩溃 | 低 | 高 | 检查点频繁保存 |
| 数据丢失 | 低 | 高 | 多重备份 |

### 时间风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| Phase 1 超时 | 中 | 中 | 优先核心功能 |
| Phase 2 数据不足 | 低 | 高 | 延长实验时间 |
| Phase 3 论文质量 | 中 | 高 | 提前准备草稿 |

---

## 📝 下一步行动

### 立即行动（今天）

1. 🔴 实现 evolution.py（演化引擎）
2. 🔴 实现 environment.py（环境系统）
3. 🟡 实现 metrics.py（指标系统）
4. 🟡 实现 main.py（主程序）

### 本周目标

- ✅ 完成 Phase 1（12-17 小时）
- ✅ 运行快速测试（1h）
- ✅ 验证核心功能

### 下周目标

- ✅ 运行 168h 完整实验
- ✅ 收集完整数据
- ✅ 初步分析

---

**计划编制完成时间**: 2026-03-30 19:50 GMT+8  
**下一步**: 开始实现 evolution.py  
**预计完成**: 本周内（Phase 1）
