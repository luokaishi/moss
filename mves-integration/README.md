# MVES - 最小可行演化系统

**Minimal Viable Evolutionary System**

一个自驱力→持续演化→AGI 路径的实验平台

---

## 🎯 项目目标

验证核心假设：

> 在没有外部任务输入的情况下，系统能否通过内部机制（资源约束 + 变异 + 选择）产生持续行为变化和结构演化？

---

## 📊 实验版本总览

| 版本 | 核心机制 | 关键发现 | 状态 |
|------|----------|----------|------|
| **v1** | 硬编码策略演化 | 策略可跃迁 (random→explore) | ✅ 完成 |
| **v2** | 认知结构演化 | 反思驱动 meta-evolution | ✅ 完成 |
| **v3** | Code as Genome | 42 次自修改，代码退化现象 | ✅ 完成 |
| **v4** | 驱动系统 + 开放环境 | 驱动失衡→群体崩溃 | ✅ 完成 |

---

## 🚀 快速开始

### 运行实验

```bash
# v1 - 基础演化
cd mves_v1
python3 main.py

# v2 - 认知演化
cd mves_v2
python3 main.py

# v3 - 代码即基因
cd mves_v3
python3 main.py

# v4 - 开放环境
cd mves_v4
python3 main.py
```

### 查看结果

```bash
# 查看检查点
ls checkpoints/

# 查看日志
tail -f logs/evolution_v*.log

# 分析数据
python3 analyze.py
```

---

## 📁 项目结构

```
MVES/
├── README.md                 # 项目总览
├── EXPERIMENT_REPORT.md      # 实验报告
├── SCIENTIFIC_FRAMEWORK.md   # 科学评估框架
├── mves_v1/                  # v1: 基础演化
├── mves_v2/                  # v2: 认知演化
├── mves_v3/                  # v3: Code as Genome
├── mves_v4/                  # v4: 开放环境
└── analysis/                 # 分析工具
```

---

## 🔬 核心发现

### v1 发现
- ✅ 策略可演化（random → explore）
- ⚠️ 死亡机制未触发（fitness 公式问题）

### v2 发现
- ✅ 反思驱动认知更新（4 次）
- ✅ 决策规则动态调整

### v3 发现
- ✅ 42 次代码自修改
- ⚠️ 代码退化（`random` 未定义）
- ✅ 回退机制有效

### v4 发现
- ❌ 驱动失衡（100% curiosity）
- ❌ 群体崩溃（80% 死亡率）
- ✅ 科学评估框架建立

---

## 📈 关键指标

| 指标 | v1 | v2 | v3 | v4 |
|------|----|----|----|----|
| **存活率** | 100% | 100% | 100% | 20% |
| **变异数** | 3 | 6 | 42 | 0 |
| **复杂度** | 低 | 中 | 中高 | 低 |
| **科学价值** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🧠 理论框架

### 演化三要素

1. **Variation（变异）** - 基因组变化
2. **Selection（选择）** - 环境压力
3. **Retention（保留）** - 遗传机制

### 驱动系统

```python
drives = {
    "survival": keep_energy_positive,
    "curiosity": maximize_state_novelty,
    "control": increase_env_influence
}
```

### 科学评估

- 结构复杂度增长
- 行为多样性（熵）
- 代际稳定性
- 环境改变幅度
- 驱动分化

---

## 📚 文档索引

- [实验报告](EXPERIMENT_REPORT.md) - 详细结果
- [科学框架](SCIENTIFIC_FRAMEWORK.md) - 评估标准
- [v1 文档](mves_v1/README.md)
- [v2 文档](mves_v2/README.md)
- [v3 文档](mves_v3/README.md)
- [v4 文档](mves_v4/README.md)

---

## 🔮 未来方向

### 短期
- [ ] 修复 v4 驱动权重
- [ ] 增加群体大小（10→50）
- [ ] 工具学习机制

### 中期
- [ ] v5: 多 agent 协作
- [ ] LLM 驱动代码演化
- [ ] 真实环境交互

### 长期
- [ ] 开放目标涌现
- [ ] 文化传递机制
- [ ] AGI 评估标准

---

## 📊 实验数据

所有实验数据保存在各版本 `checkpoints/` 和 `logs/` 目录。

### 统计分析

```bash
cd analysis
python3 compare_versions.py
python3 plot_evolution.py
```

---

## 🤝 贡献

这是一个研究项目，欢迎：
- 实验建议
- 理论讨论
- 代码改进

---

## 📝 许可证

Research Project - Open Source

---

**从"程序"到"数字生命"的探索之旅** 🧬
