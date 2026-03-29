# MVES v1.0 - 最小可行演化系统

**Minimal Viable Evolutionary System**

一个无任务输入的自主演化原型系统，演示 Variation + Selection + Retention 机制。

---

## 🎯 核心目标

在无外部任务输入的情况下，让系统依靠：
- **资源约束** (energy)
- **变异机制** (mutation)
- **自然选择** (death/fitness)

产生持续的行为变化和演化。

---

## 📁 项目结构

```
mves/
├── main.py           # 主循环
├── agent.py          # 智能体核心
├── environment.py    # 环境 + 选择压力
├── evolution.py      # 变异 + 选择
├── genome.json       # 基因组配置
├── memory.json       # 状态快照
├── logs/             # 演化日志
└── README.md
```

---

## 🚀 运行方法

```bash
cd mves
python3 main.py
```

---

## 🧬 核心机制

### 1. 智能体策略

| 策略 | 行为模式 |
|------|----------|
| `random` | 随机选择 read/write/idle |
| `conserve` | 低能量时 idle，否则 read |
| `explore` | 随机 read/write |

### 2. 资源约束

| 动作 | 能量消耗 |
|------|----------|
| `read` | -1 |
| `write` | -2 |
| `idle` | -0.5 |

### 3. 死亡条件

```
fitness = energy + steps < 0 → 死亡 → 重置
```

### 4. 变异机制

- 20% 概率触发变异
- 变异类型：策略/提示词/记忆大小
- 只有适应度提升才保留

---

## 📊 观察指标

运行后关注：

1. **策略稳定性** - 是否出现 dominant strategy
2. **死亡间隔** - 是否逐渐延长
3. **策略收敛** - 某类 genome 是否持续存活
4. **行为模式** - 是否形成 energy-dependent 决策

---

## 🔥 v2 升级计划

- [ ] 接入 LLM 驱动 act()
- [ ] 引入真实环境（文件系统/API）
- [ ] 真实 fitness 函数
- [ ] 自修改 prompt 机制
- [ ] 工具调用能力

---

## 📝 许可证

Experimental AGI Research Project
