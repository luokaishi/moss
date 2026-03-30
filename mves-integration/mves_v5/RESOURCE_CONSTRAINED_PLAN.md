# MVES v5 资源受限实施计划

**编制时间**: 2026-03-30 19:55 GMT+8  
**资源限制**: 内存 734MB 可用 / 磁盘 12GB 可用 / CPU 2 核  
**策略**: 小步快跑，渐进实现

---

## 📊 系统资源现状

| 资源 | 总量 | 已用 | 可用 | 限制 |
|------|------|------|------|------|
| **内存** | 1.8 GB | 845 MB | 734 MB | 🟡 中等 |
| **磁盘** | 40 GB | 26 GB | 12 GB | 🟡 中等 |
| **CPU** | 2 核 | - | - | 🔴 紧张 |
| **Gateway** | - | 436 MB | - | 🟡 占用 23% |

---

## 🎯 资源优化策略

### 1. 控制实验规模

**原计划** vs **优化后**:

| 参数 | 原计划 | 优化后 | 节省 |
|------|--------|--------|------|
| Agent 数量 | 20 | **10** | 50% |
| 环境大小 | 30x30 | **20x20** | 56% |
| 初始资源 | 3000 | **1500** | 50% |
| 实验时长 | 168h | **24h (先快速验证)** | 86% |
| 检查点间隔 | 10 代 | **20 代** | 50% |

### 2. 分阶段实现

**Phase 1a: 最小可运行版**（今天，4-6 小时）
- ✅ agent.py（已完成）
- 🔴 evolution.py（简化版）
- 🔴 main.py（快速测试版）
- ⏸️ environment.py（简化为内存版）
- ⏸️ metrics.py（基础指标）

**目标**: 运行 1h 快速测试，验证核心逻辑

**Phase 1b: 完整功能版**（本周，8-10 小时）
- 🔴 environment.py（完整版）
- 🔴 metrics.py（完整指标）
- 🔴 main.py（168h 版）
- 🔴 对照实验支持

**目标**: 运行 24h 实验

**Phase 2: 扩展验证**（下周，视资源而定）
- 🟡 运行 168h 实验
- 🟡 4 组对照实验
- 🟡 数据分析

### 3. 内存管理

**优化措施**:
```python
# 1. 使用生成器而非列表
def population_generator():
    for agent in population:
        yield agent
        # 及时释放

# 2. 定期垃圾回收
import gc
if generation % 10 == 0:
    gc.collect()

# 3. 限制记忆大小
MAX_MEMORY_SIZE = 100
if len(agent.memory["episodic"]) > MAX_MEMORY_SIZE:
    agent.memory["episodic"] = agent.memory["episodic"][-MAX_MEMORY_SIZE:]

# 4. 检查点压缩
import gzip
with gzip.open(checkpoint_file, 'wt') as f:
    json.dump(data, f)
```

### 4. 磁盘管理

**优化措施**:
```python
# 1. 检查点只保存必要数据
checkpoint = {
    'generation': generation,
    'population_size': len(population),
    'metrics': metrics,
    # 不保存完整 agent 数据
    'top_agents_genomes': [a.genome for a in top_3]
}

# 2. 定期清理旧检查点
if len(checkpoints) > 10:
    oldest = checkpoints.pop(0)
    os.remove(oldest)

# 3. 日志分级
# INFO: 每代记录
# DEBUG: 每 10 代记录（可关闭）
# WARNING/ERROR: 实时记录
```

---

## 📋 立即实施计划（Phase 1a）

### 任务 1: evolution.py 简化版（2-3 小时）

**核心功能**（只实现必要的）:
```python
class EvolutionEngine:
    def __init__(self, config):
        self.population_size = config.get('population_size', 10)
        self.population = self._init_population()
        self.generation = 0
    
    def _init_population(self):
        """初始化种群（10 个 agent）"""
        return [EvolutionaryAgent(i) for i in range(self.population_size)]
    
    def run_generation(self, environment):
        """运行一代"""
        # 1. 行动
        for agent in self.population:
            action = agent.decide()
            result = agent.execute(action, environment)
            agent.learn(result)
        
        # 2. 选择（简化版）
        deaths = 0
        for agent in self.population:
            if agent.energy <= 0:
                agent.die()
                deaths += 1
        
        # 3. 繁殖（前 3 名）
        survivors = [a for a in self.population if a.state]
        top_agents = sorted(survivors, key=lambda a: a.get_fitness())[:3]
        
        births = 0
        for parent in top_agents:
            child = parent.clone()
            child.genome.mutate()
            self.population.append(child)
            births += 1
        
        self.generation += 1
        return {'deaths': deaths, 'births': births, 'population': len(self.population)}
```

**预计内存**: <100 MB  
**预计磁盘**: <10 MB/检查点

---

### 任务 2: environment.py 简化版（1-2 小时）

**核心功能**（内存版，不持久化）:
```python
class SimpleEnvironment:
    def __init__(self, size=(20, 20), initial_resources=1500):
        self.size = size
        self.resources = initial_resources
        self.structures = {}  # 内存字典
    
    def apply_selection_pressure(self, agent):
        """简化版选择压力"""
        if agent.energy <= 0:
            return "death"
        elif agent.energy < 30:
            return "resource_penalty"
        return "survived"
    
    def get_prediction_error(self, position):
        """简化版预测误差"""
        # 随机值（模拟）
        return random.uniform(0, 1)
    
    def get_changes_caused_by(self, agent_id):
        """简化版影响力计算"""
        return self.structures.get(agent_id, [])
    
    def add_structure(self, x, y, agent_id):
        """添加结构"""
        if agent_id not in self.structures:
            self.structures[agent_id] = []
        self.structures[agent_id].append((x, y))
```

**预计内存**: <50 MB  
**预计磁盘**: 0（不持久化）

---

### 任务 3: metrics.py 简化版（0.5-1 小时）

**核心功能**（只实现关键指标）:
```python
class SimpleMetrics:
    @staticmethod
    def diversity(population):
        """策略多样性（简化熵）"""
        strategies = [str(a.genome["strategies"]) for a in population]
        unique = len(set(strategies))
        return unique / len(population)
    
    @staticmethod
    def complexity(agent):
        """策略复杂度（简化）"""
        return len(agent.genome["modules"])
    
    @staticmethod
    def novelty(population, baseline):
        """新能力（简化）"""
        current = set()
        for agent in population:
            current.update(agent.get_capabilities())
        return len(current - baseline)
```

**预计内存**: <10 MB  
**预计磁盘**: <1 MB/代

---

### 任务 4: main.py 快速测试版（1-2 小时）

**核心功能**（1h 快速测试）:
```python
def quick_test():
    """快速测试（1 小时）"""
    config = {
        'population_size': 10,
        'duration_hours': 1,  # 1 小时快速测试
        'environment_size': (20, 20),
        'initial_resources': 1500
    }
    
    engine = EvolutionEngine(config)
    env = SimpleEnvironment()
    
    print(f"Starting quick test ({config['duration_hours']}h)...")
    
    for hour in range(config['duration_hours']):
        # 运行 6 代（每代~10 分钟）
        for _ in range(6):
            result = engine.run_generation(env)
            
            # 记录指标
            metrics = {
                'generation': engine.generation,
                'population': result['population'],
                'deaths': result['deaths'],
                'births': result['births'],
                'diversity': SimpleMetrics.diversity(engine.population)
            }
            print(f"Gen {engine.generation}: {metrics}")
        
        # 保存检查点（每 10 代）
        if engine.generation % 10 == 0:
            save_checkpoint(engine, f"checkpoint_gen{engine.generation}.json.gz")
    
    print("Quick test complete!")
    return engine
```

**预计内存**: <200 MB（总计）  
**预计磁盘**: <50 MB（总计）

---

## ⏱️ 时间安排（今天）

| 时间 | 任务 | 产出 | 资源占用 |
|------|------|------|---------|
| **现在 - 2h** | evolution.py 简化版 | 可运行引擎 | <100 MB |
| **2h - 3h** | environment.py 简化版 | 简化环境 | <50 MB |
| **3h - 4h** | metrics.py 简化版 | 基础指标 | <10 MB |
| **4h - 6h** | main.py 快速测试版 | 可运行实验 | <200 MB |
| **6h** | 运行快速测试 | 1h 实验数据 | <50 MB 磁盘 |

**总工时**: 4-6 小时  
**总内存**: <200 MB  
**总磁盘**: <50 MB

---

## 🎯 成功标准（Phase 1a）

### 最小成功
- ✅ evolution.py 实现完成
- ✅ environment.py 实现完成
- ✅ main.py 实现完成
- ✅ 快速测试运行 1h 无崩溃
- ✅ 观察到至少 1 次变异
- ✅ 观察到至少 1 次死亡

### 理想成功
- ✅ 运行 6 代以上
- ✅ 观察到策略多样性变化
- ✅ 数据完整记录
- ✅ 内存占用 <200 MB
- ✅ 磁盘占用 <50 MB

---

## 📊 资源监控

### 运行时监控

```python
import psutil
import os

def check_resources():
    """检查资源使用"""
    process = psutil.Process(os.getpid())
    memory = process.memory_info().rss / 1024 / 1024  # MB
    disk = psutil.disk_usage('.').percent
    
    print(f"Memory: {memory:.1f} MB")
    print(f"Disk: {disk:.1f}%")
    
    # 警告阈值
    if memory > 500:
        print("⚠️  内存占用过高！")
    if disk > 80:
        print("⚠️  磁盘占用过高！")
    
    return memory, disk
```

### 自动优化

```python
# 如果内存超过阈值
if memory > 400:
    # 减少种群大小
    config['population_size'] = 5
    # 减少检查点保存
    config['checkpoint_interval'] = 50
    # 触发垃圾回收
    import gc
    gc.collect()
```

---

## 🔄 后续阶段（资源允许时）

### Phase 1b（本周，资源允许时）

- 🟡 environment.py 完整版（持久化）
- 🟡 metrics.py 完整指标
- 🟡 main.py 24h 版
- 🟡 对照实验支持

**资源需求**:
- 内存：<500 MB
- 磁盘：<200 MB
- 时间：8-10 小时

### Phase 2（下周，资源允许时）

- 🟡 运行 168h 实验
- 🟡 4 组对照实验
- 🟡 数据分析

**资源需求**:
- 内存：<1 GB
- 磁盘：<1 GB
- 时间：16-24 小时

---

## ⚠️ 风险与应对

### 风险 1: 内存不足

**症状**: 系统变慢，OOM
**应对**:
1. 减少种群大小（10→5）
2. 减少检查点频率（20 代→50 代）
3. 关闭 DEBUG 日志
4. 定期 gc.collect()

### 风险 2: 磁盘不足

**症状**: 无法保存检查点
**应对**:
1. 清理旧检查点（保留最近 5 个）
2. 使用 gzip 压缩
3. 减少检查点数据量
4. 清理临时文件

### 风险 3: CPU 过载

**症状**: Gateway 响应慢
**应对**:
1. 降低实验优先级（nice）
2. 减少并发
3. 暂停实验，让位 Gateway

---

## 📝 立即行动

**现在开始**: evolution.py 简化版实现

**预计完成时间**: 2-3 小时

**资源预算**:
- 内存：<100 MB
- 磁盘：<10 MB
- CPU: <50%

---

**计划编制完成**: 2026-03-30 19:55 GMT+8  
**下一步**: 实现 evolution.py（简化版）  
**资源限制**: 内存 200MB / 磁盘 50MB / CPU 50%
