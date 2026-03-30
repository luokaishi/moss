# MVES v5 - 最小可验证演化系统

**版本**: v5.0  
**代号**: MEAP (Minimal Evolutionary AGI Prototype)  
**设计时间**: 2026-03-30  
**状态**: 设计中

---

## 🎯 核心目标

**验证命题**:
> 存在一种内在驱动力结构，使 AI 系统在无外部任务下
> 仍能持续产生行为、改进自身、扩展能力边界

**形式化**:
```
∃ M (motivation structure)，使得
System + M → 持续自主演化 (open-ended evolution)
```

---

## 🔬 演化三要素（核心改进）

### 1. 变异（Variation）✅

**v5 设计**: 结构变异机制

```python
class EvolutionaryAgent:
    def mutate_structure(self):
        """结构变异（不只是参数调整）"""
        mutations = [
            self._add_new_module,       # 添加新功能模块
            self._rewrite_strategy,     # 改写决策策略
            self._spawn_subagent,       # 生成子 agent
            self._change_decision_flow, # 改变决策流程
            self._modify_goal_function  # 修改目标函数
        ]
        return random.choice(mutations)()
    
    def _add_new_module(self):
        """添加新模块"""
        module_templates = [
            "memory_optimizer",    # 记忆优化器
            "pattern_recognizer",  # 模式识别器
            "tool_creator",        # 工具创造器
            "self_reflector"       # 自我反思器
        ]
        new_module = random.choice(module_templates)
        self.modules.append(new_module)
        return f"Added {new_module}"
    
    def _rewrite_strategy(self):
        """改写策略"""
        # 修改决策树结构
        old_strategy = self.strategy.copy()
        self.strategy = self._mutate_strategy(self.strategy)
        return f"Strategy rewritten: {old_strategy} → {self.strategy}"
    
    def _spawn_subagent(self):
        """生成子 agent"""
        child = self.clone()
        child.genome.mutate()
        child.parent_id = self.agent_id
        return f"Spawned child agent {child.agent_id}"
```

**变异率**:
- 基础变异率：15% / 代
- 结构变异率：5% / 代
- 最大变异数：3 次 / 代

---

### 2. 选择（Selection）✅

**v5 设计**: 真实选择压力

```python
class Environment:
    def apply_selection_pressure(self, agent):
        """应用选择压力"""
        
        # 能量耗尽 → 死亡
        if agent.energy <= 0:
            agent.die()
            agent.memory = {}      # 记忆丢失
            agent.state = {}       # 状态重置
            agent.modules = []     # 模块清除
            return "death"
        
        # 低能量 → 资源惩罚
        elif agent.energy < 30:
            agent.lose_memory(50%)     # 丢失 50% 记忆
            agent.lose_resources(30%)  # 失去 30% 资源
            return "resource_penalty"
        
        # 低适应度 → 淘汰风险
        elif agent.fitness < threshold:
            agent.probability_of_death = 0.3
            return "selection_risk"
        
        return "survived"
    
    def calculate_fitness(self, agent):
        """适应度计算"""
        # 多指标综合
        fitness = (
            agent.energy * 0.3 +           # 生存能力
            len(agent.modules) * 0.2 +     # 复杂度
            agent.performance_score * 0.3 + # 性能
            agent.innovation_count * 0.2    # 创新数
        )
        return fitness
```

**选择压力强度**:
- 死亡率目标：40-60% / 100 代
- 淘汰阈值：适应度最低的 30%
- 环境压力：动态调整

---

### 3. 保留（Retention）✅

**v5 设计**: 遗传机制

```python
class Genome:
    def __init__(self):
        self.modules = []           # 模块清单
        self.strategies = {}        # 策略字典
        self.goal_function = None   # 目标函数
        self.drive_weights = {}     # 驱动权重
    
    def inherit_from(self, parent):
        """从父代继承"""
        self.modules = parent.modules.copy()
        self.strategies = parent.strategies.copy()
        self.goal_function = parent.goal_function.copy()
        self.drive_weights = parent.drive_weights.copy()
    
    def mutate(self, rate=0.15):
        """变异"""
        if random.random() < rate:
            # 模块变异
            if random.random() < 0.3:
                self._mutate_modules()
            
            # 策略变异
            if random.random() < 0.3:
                self._mutate_strategies()
            
            # 权重变异
            if random.random() < 0.4:
                self._mutate_weights()
    
    def save_checkpoint(self, filepath):
        """保存检查点（遗传信息）"""
        with open(filepath, 'w') as f:
            json.dump({
                'modules': self.modules,
                'strategies': self.strategies,
                'goal_function': self.goal_function,
                'drive_weights': self.drive_weights,
                'mutation_count': self.mutation_count
            }, f, indent=2)
```

**保留机制**:
- 检查点保存：每 10 代
- 优秀个体保护：适应度前 20% 免于死亡
- 遗传信息传递：子代继承父代 80% 基因

---

## 🧬 四驱动系统（数学化定义）

### 评估建议核心改进

**原设计**（v4）:
```python
# 问题：不可计算
curiosity = "maximize information gain"  # ❌
```

**v5 设计**（数学化）:
```python
class Drives:
    @staticmethod
    def curiosity(agent):
        """
        好奇心 = 预测误差最小化
        
        数学定义:
        C(s) = 1 / (1 + prediction_error(s))
        
        其中:
        prediction_error(s) = |actual_outcome - predicted_outcome|
        """
        prediction_error = agent.model.get_prediction_error()
        curiosity_score = 1.0 / (1.0 + prediction_error)
        return curiosity_score
    
    @staticmethod
    def survival(agent):
        """
        生存 = 资源缓冲 / 消耗率
        
        数学定义:
        S = buffer / (consumption + ε)
        
        其中:
        buffer = current_energy - min_energy_threshold
        consumption = avg_energy_consumption_per_step
        """
        buffer = agent.state["energy"] - 20  # 20 为最低阈值
        consumption = agent.get_avg_consumption()
        survival_score = buffer / (consumption + 1)  # +1 防止除零
        return max(0, survival_score)
    
    @staticmethod
    def influence(agent):
        """
        影响力 = 外部状态变化数
        
        数学定义:
        I = |{s ∈ Environment : caused_by(agent, s)}|
        
        其中:
        caused_by(agent, s) = True if agent 导致了状态 s 的变化
        """
        changes = agent.environment.get_changes_caused_by(agent)
        influence_score = len(changes)
        return min(1.0, influence_score / 10)  # 归一化到 [0,1]
    
    @staticmethod
    def optimization(agent):
        """
        优化 = 性能提升率
        
        数学定义:
        O = (performance_t - performance_{t-1}) / performance_{t-1}
        
        其中:
        performance = task_completion_rate * efficiency
        """
        current_perf = agent.get_performance()
        past_perf = agent.get_past_performance()
        
        if past_perf == 0:
            return 0.0
        
        optimization_score = (current_perf - past_perf) / past_perf
        return max(0, optimization_score)  # 只计正向提升
```

---

## 🧪 实验设计

### 对照组设计（评估建议 5.2）

| 组 | 类型 | 驱动系统 | 目的 |
|----|------|---------|------|
| **A 组** | 自驱力 Agent | S/C/I/O 四驱动 | 完整系统 |
| **B 组** | 纯任务驱动 | 无 | 基线对照 |
| **C 组** | RL Agent | Reward-based | 对照范式 1 |
| **D 组** | Planning Agent | Tree Search | 对照范式 2 |

### 实验参数

```python
EXPERIMENT_CONFIG = {
    'duration_hours': 168,  # 7 天（评估建议）
    'agent_count': 20,
    'environment_size': (30, 30),
    'initial_resources': 3000,
    'checkpoint_interval': 10,  # 每 10 代保存
    
    # 环境变化阶段（评估建议）
    'phases': [
        {'hours': 48, 'resource_rate': 1.0, 'complexity': 'stable'},
        {'hours': 48, 'resource_rate': 0.5, 'complexity': 'stress'},
        {'hours': 48, 'resource_rate': 1.0, 'complexity': 'new_tools'},
        {'hours': 24, 'resource_rate': 1.5, 'complexity': 'growth'}
    ]
}
```

---

## 📊 验证指标（重新定义）

### 评估建议：不要再用"任务完成数/运行时间"

**新指标体系**:

```python
class EvolutionMetrics:
    """演化指标（非行为指标）"""
    
    @staticmethod
    def behavior_diversity(population):
        """
        行为多样性增长
        
        计算：策略分布的熵
        H = -Σ p(strategy_i) * log(p(strategy_i))
        """
        strategies = [agent.strategy for agent in population]
        strategy_counts = Counter(strategies)
        total = len(strategies)
        
        entropy = 0
        for count in strategy_counts.values():
            p = count / total
            entropy -= p * math.log(p)
        
        return entropy
    
    @staticmethod
    def strategy_complexity(agent):
        """
        策略复杂度增长
        
        计算：决策树深度 + 分支数
        """
        depth = agent.strategy.get_depth()
        branches = agent.strategy.count_branches()
        return depth * branches
    
    @staticmethod
    def novel_capabilities(population, baseline):
        """
        未预设能力出现
        
        检测：能力是否在预设清单中
        """
        preset_capabilities = baseline
        observed_capabilities = set()
        
        for agent in population:
            observed_capabilities.update(agent.get_capabilities())
        
        novel = observed_capabilities - preset_capabilities
        return len(novel)
    
    @staticmethod
    def long_term_improvement(history):
        """
        长期性能提升（非训练）
        
        计算：performance 随时间的增长率
        """
        if len(history) < 2:
            return 0.0
        
        initial_perf = history[0]['performance']
        final_perf = history[-1]['performance']
        
        improvement = (final_perf - initial_perf) / initial_perf
        return improvement
```

---

## 🗺️ 实验流程

### Phase 1: 初始化（0h）

```python
# 创建初始种群
population = []
for i in range(20):
    agent = EvolutionaryAgent(agent_id=i)
    agent.genome.inherit_from(ancestor)
    population.append(agent)

# 保存基线数据
baseline = {
    'agent_count': len(population),
    'avg_energy': np.mean([a.energy for a in population]),
    'strategy_diversity': EvolutionMetrics.behavior_diversity(population),
    'preset_capabilities': get_all_capabilities(population)
}
```

### Phase 2: 演化循环（0-168h）

```python
for generation in range(max_generations):
    # 1. 每个 agent 行动
    for agent in population:
        action = agent.decide()
        result = agent.execute(action)
        agent.learn(result)
    
    # 2. 应用选择压力
    for agent in population:
        outcome = environment.apply_selection_pressure(agent)
        if outcome == "death":
            population.remove(agent)
    
    # 3. 繁殖（优秀个体）
    top_agents = sorted(population, key=lambda a: a.fitness)[:5]
    for parent in top_agents:
        child = parent.clone()
        child.genome.mutate()
        population.append(child)
    
    # 4. 记录指标
    metrics = {
        'generation': generation,
        'population_size': len(population),
        'behavior_diversity': EvolutionMetrics.behavior_diversity(population),
        'avg_complexity': np.mean([EvolutionMetrics.strategy_complexity(a) for a in population]),
        'novel_capabilities': EvolutionMetrics.novel_capabilities(population, baseline),
        'deaths': deaths_this_gen,
        'mutations': mutations_this_gen
    }
    log_metrics(metrics)
    
    # 5. 保存检查点
    if generation % 10 == 0:
        save_checkpoint(population, generation)
```

### Phase 3: 分析（168h+）

```python
# 分析演化轨迹
analysis = {
    'total_generations': final_generation,
    'total_deaths': sum(deaths),
    'total_mutations': sum(mutations),
    'capability_expansion': final_capabilities - initial_capabilities,
    'diversity_trajectory': [m['behavior_diversity'] for m in metrics_history],
    'complexity_trajectory': [m['avg_complexity'] for m in metrics_history]
}

# 生成报告
generate_report(analysis)
```

---

## 📋 实施计划

### 本周（8-12 小时）

**任务**:
1. 🔴 实现变异机制（`_add_new_module` 等）
2. 🔴 实现选择压力（死亡 + 记忆丢失）
3. 🔴 实现遗传机制（检查点 + 继承）
4. 🔴 数学化驱动函数

**产出**: `mves_v5/agent.py`, `mves_v5/evolution.py`

---

### 下周（16-24 小时）

**任务**:
1. 🟡 实现对照架构（B/C/D组）
2. 🟡 实现环境变化阶段
3. 🟡 实现新指标体系
4. 🟡 运行 168h 实验

**产出**: 完整实验数据

---

### 本月（40-60 小时）

**任务**:
1. 🟡 数据分析
2. 🟡 论文重写（存在性命题）
3. 🟡 因果模型补充
4. ⚪ 投稿 NeurIPS/ICLR

**产出**: 论文 + 数据集

---

## 🎯 成功标准

### 最小成功

- ✅ 系统运行 168h 无崩溃
- ✅ 观察到结构变异（≥10 次）
- ✅ 观察到选择压力（死亡率 40-60%）
- ✅ 观察到遗传保留（子代继承父代特征）

### 理想成功

- ✅ 行为多样性增长（熵增加）
- ✅ 策略复杂度增长（深度×分支增加）
- ✅ 出现未预设能力（≥3 个）
- ✅ 长期性能提升（≥20%）

### 突破性成功

- ✅ 观察到"质变演化"（新范式出现）
- ✅ 自驱力组显著优于对照组
- ✅ 数据支持存在性命题
- ✅ 论文被 NeurIPS/ICLR 接收

---

## 📝 与 v4 的关键区别

| 维度 | v4 | v5 |
|------|----|----|
| **变异** | 驱动权重变异 | 结构变异（模块/策略） |
| **选择** | 能量耗尽 | 死亡 + 记忆丢失 + 资源惩罚 |
| **保留** | 基因组继承 | 检查点 + 遗传 + 优秀保护 |
| **驱动定义** | 文字描述 | 数学公式 |
| **对照** | 无 | B/C/D三组对照 |
| **时间尺度** | 100 代 | 168h（7 天） |
| **指标** | 行为指标 | 演化指标 |

---

**设计完成时间**: 2026-03-30 19:45 GMT+8  
**下一步**: 开始编码实现（Phase 1）
