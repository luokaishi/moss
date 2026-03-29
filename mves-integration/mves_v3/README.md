# MVES v3 - 数字生命系统

**Minimal Viable Evolutionary System v3**

自修改代码 + 多体繁殖的演化系统

---

## 🧬 核心跃迁（相比 v2）

| 维度 | v2 | v3 |
|------|----|----|
| **演化单位** | 个体认知结构 | 群体代码库 |
| **Genome** | JSON 配置 | brain.py 代码 |
| **变异** | 文本替换 | 代码自修改 |
| **选择** | 个体适应度 | 群体竞争 |
| **繁殖** | ❌ 无 | ✅ 复制 + 变异 |

---

## 🎯 核心机制

### 1. Code as Genome

```
agents/
├── agent_1/
│   ├── brain.py      # 可演化代码
│   ├── genome.json   # 谱系信息
│   ├── state.json    # 状态
│   └── memory.json   # 记忆
├── agent_2/
│   └── ...
```

### 2. 自修改代码

```python
def self_modify(agent):
    code = open(agent.brain_path).read()
    new_code = LLM_modify(code)  # 或规则修改
    if safe_check(new_code):
        write(agent.brain_path, new_code)
```

### 3. 繁殖机制

```python
if agent.energy > 150:
    child = agent.reproduce()  # 复制 + 变异
    agents.append(child)
```

### 4. 群体选择

```python
# 资源竞争
competition = 1 - (population / carrying_capacity)

# 自然淘汰
if agent.energy <= 0:
    agents.remove(agent)
```

---

## 🚀 运行方法

```bash
cd mves_v3
python3 main.py
```

---

## 📊 观察指标

### 演化信号

| 信号 | 说明 | 意义 |
|------|------|------|
| **策略稳定传承** | 某策略多代持续 | 适应性优势 |
| **自发分化** | 不同 agent 不同策略 | 生态位分化 |
| **代码结构变化** | brain.py 越来越复杂 | 复杂性增长 |
| **非预设行为** | 出现未设计的行为 | 涌现 |

### 群体统计

- 种群大小动态
- 平均适应度变化
- 变异积累速率
- 出生/死亡率

---

## ⚠️ 安全机制

### 代码安全检查

禁止的操作：
- `import os/sys/subprocess`
- `delete/remove`
- `socket/urllib/requests`
- `eval/exec`
- `__class__/__bases__`

### 群体控制

- 环境承载力：50
- 过度拥挤时施加压力
- 淘汰最弱个体

---

## 🎯 成功标准

系统产生：
- [ ] 可继承的结构变化
- [ ] 持续行为改进
- [ ] 策略分化
- [ ] 非预设行为模式

---

## 📁 输出

```
mves_v3/
├── agents/          # 活着的 agent
├── checkpoints/     # 群体快照
├── logs/
│   └── evolution_v3.log
└── main.py
```

---

## 🔮 预期现象

### 阶段 1：初始混乱
- 随机行为
- 快速死亡/繁殖

### 阶段 2：策略形成
- 某些策略存活更久
- 开始积累变异

### 阶段 3：分化
- 不同谱系出现
- 生态位分化

### 阶段 4（理想）：复杂性增长
- 代码结构变复杂
- 出现涌现行为

---

**v1: 能活 → v2: 能思考 → v3: 能改变自己是什么**
