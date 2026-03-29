# MVES v2 - LLM 驱动的自演化系统

**Minimal Viable Evolutionary System v2**

Proto-AGI 阶段：系统能思考，能修改自己的认知结构

---

## 🎯 核心跃迁（相比 v1）

| 维度 | v1 | v2 |
|------|----|----|
| **决策** | 硬编码策略 | LLM 生成 |
| **Genome** | 参数 (strategy) | 认知结构 (prompt) |
| **变异** | 策略切换 | 思维模式修改 |
| **Meta** | ❌ 无 | ✅ 反思驱动更新 |

---

## 🧠 认知结构（Genome）

```json
{
  "system_prompt": "身份认知",
  "decision_rule": "决策规则",
  "tool_policy": "工具策略",
  "reflection_rule": "反思规则",
  "memory_size": "记忆容量"
}
```

---

## 🚀 运行方法

```bash
cd mves_v2
python3 main.py
```

---

## 📊 观察指标

### 阶段 1（随机期）
- 行为混乱
- 快速死亡

### 阶段 2（策略形成）
- energy-aware 行为
- 减少无效操作

### 阶段 3（关键）
- 避免重复错误
- 主动试探新行为
- **修改自己的决策规则** ← Meta-evolution

### 阶段 4（突破）
- 改写 prompt
- 优化工具使用
- 形成稳定策略体系

---

## 🔥 关键特性

### 1. LLM 驱动决策
```python
prompt = build_prompt(state, genome, memory)
action = LLM(prompt)  # 不再是硬编码
```

### 2. 反思机制
```python
reflection = agent.reflect()  # LLM 分析自己
genome = apply_reflection(genome, reflection)  # 更新认知
```

### 3. 稀疏奖励
- 5% 概率发现资源 (+5~15 energy)
- 10% 概率 write 创造价值 (+3 energy)
- 鼓励探索行为

### 4. 真实选择压力
- 能量 <= 0 → 死亡 → 重置
- 适应度 = 能量 + 效率 + 多样性

---

## 📁 输出

```
mves_v2/
├── checkpoints/       # 检查点
├── logs/
│   └── evolution_v2.log
├── genome.json        # 当前认知结构
└── main.py
```

---

## ⚠️ 风险

1. **LLM 假装聪明** - 输出合理但无实际改进
2. **变异无效** - prompt 变化不影响行为
3. **收敛过早** - 卡在局部最优

---

## 🎯 成功标准

系统开始：
- [ ] 改写自己的 prompt
- [ ] 优化工具使用策略
- [ ] 形成稳定的认知结构
- [ ] 延长存活时间

---

**v1: 系统能活 → v2: 系统能思考 → v3: 系统能改变"自己是什么"**
