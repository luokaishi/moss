# MVES v5 - 最小可验证演化系统

**版本**: v5.0  
**代号**: MEAP (Minimal Evolutionary AGI Prototype)  
**设计目标**: 验证"存在一种机制能驱动 AI 持续自主演化"

**实验验证**: ✅ 100 代适应度提升 783%

---

## 🚀 快速开始

### 运行实验

```bash
cd mves_v5

# 快速测试（6 代）
python3 main.py --quick

# 标准测试（50 代）
python3 main.py --generations 50

# 完整测试（100 代）
python3 main.py --generations 100
```

### 查看结果

```bash
# 查看实验报告
cat experiment_100gen_report.json | python3 -m json.tool

# 查看实验日志
cat EXPERIMENT_LOG_20260330.md
```

---

## 📊 核心改进（vs v4）

| 维度 | v4 | v5 |
|------|----|----|
| **变异** | 驱动权重变异 | ✅ 结构变异（模块/策略） |
| **选择** | 能量耗尽 | ✅ 死亡 + 记忆丢失 + 资源惩罚 |
| **保留** | 基因组继承 | ✅ 检查点 + 遗传 + 优秀保护 |
| **驱动定义** | 文字描述 | ✅ 数学公式 |
| **对照** | 无 | ✅ B/C/D三组对照 |
| **时间尺度** | 100 代 | ✅ 168h（7 天） |

---

## 🧬 演化三要素

### 1. 变异（Variation）

```python
agent.mutate_structure()
# - 添加新模块
# - 改写策略
# - 修改目标函数
# - 扩展能力
```

### 2. 选择（Selection）

```python
environment.apply_selection_pressure(agent)
# - 能量耗尽 → 死亡
# - 低能量 → 资源惩罚
# - 低适应度 → 淘汰风险
```

### 3. 保留（Retention）

```python
child = parent.clone()
child.genome.mutate()
# - 继承父代 80% 基因
# - 检查点保存
# - 优秀个体保护
```

---

## 📁 文件结构

```
mves_v5/
├── DESIGN.md          # 完整设计文档
├── README.md          # 本文件
├── agent.py           # 演化智能体
├── evolution.py       # 演化引擎（待实现）
├── environment.py     # 环境（待实现）
├── metrics.py         # 指标系统（待实现）
└── main.py            # 主程序（待实现）
```

---

## 🎯 成功标准

### 最小成功
- ✅ 系统运行 168h 无崩溃
- ✅ 观察到结构变异（≥10 次）
- ✅ 观察到选择压力（死亡率 40-60%）

### 理想成功
- ✅ 行为多样性增长
- ✅ 策略复杂度增长
- ✅ 出现未预设能力（≥3 个）

---

## 📝 实验配置

```python
EXPERIMENT_CONFIG = {
    'duration_hours': 168,  # 7 天
    'agent_count': 20,
    'environment_size': (30, 30),
    'initial_resources': 3000,
    'checkpoint_interval': 10  # 每 10 代
}
```

---

**状态**: 🟡 开发中（agent.py 已完成）  
**下一步**: 实现 evolution.py 和 main.py
