# MVES 快速开始指南

**5 分钟运行第一个实验**

---

## 🚀 前置要求

- Python 3.8+
- 无外部依赖（v1-v3）
- 可选：matplotlib（分析用）

---

## 📦 安装

```bash
# 克隆或进入项目
cd /home/admin/.openclaw/workspace/MVES

# 查看结构
tree -L 2
```

---

## 🧪 运行实验

### v1 - 基础演化（推荐入门）

```bash
cd mves_v1
python3 main.py
```

**预期输出：**
```
Gen   1 | Energy:   98.0 | Steps:    1 | Fitness:   99.0
Gen   2 | Energy:   96.0 | Steps:    2 | Fitness:   98.0
...
📊 最终状态报告:
  最终策略：explore
  总步数：100
```

### v2 - 认知演化

```bash
cd mves_v2
python3 main.py
```

### v3 - 代码演化

```bash
cd mves_v3
python3 main.py
```

### v4 - 开放环境

```bash
cd mves_v4
python3 main.py
```

**预期输出：**
```
Gen   1 | Pop: 10 | Energy:  99.2 | Complexity: 1.0
...
💀 Agent 8 死亡
🔬 科学评估:
  ❌ 结构复杂度增长
  ✅ 行为多样性
```

---

## 📊 查看结果

### 检查点

```bash
ls checkpoints/
cat checkpoints/checkpoint_gen0010.json
```

### 日志

```bash
tail -f logs/evolution.log
```

### 分析

```bash
cd analysis
python3 compare_versions.py
```

---

## 📚 阅读文档

### 入门顺序

1. [项目总览](README.md) - 了解全貌
2. [实验报告](EXPERIMENT_REPORT.md) - 详细结果
3. [版本文档](mves_v1/README.md) - 深入细节
4. [科学框架](SCIENTIFIC_FRAMEWORK.md) - 方法论

---

## 🔧 常见问题

### Q: 为什么 v4 都死了？

A: 驱动失衡（curiosity 始终主导），这是预期内的"失败"，证明了驱动系统需要校准。

### Q: 如何修改参数？

A: 编辑 `main.py` 中的初始化参数，如：
```python
agents = init_population(size=20)  # 改群体大小
```

### Q: 如何保存数据？

A: 检查点自动保存在 `checkpoints/`，每 10 代保存一次。

---

## 🎯 下一步

### 初学者路径

1. ✅ 运行 v1，观察策略跃迁
2. ✅ 运行 v2，看反思机制
3. ✅ 运行 v3，看代码演化
4. ✅ 阅读科学框架
5. 🔬 设计自己的实验

### 进阶路径

1. 修复 v4 驱动权重
2. 添加新工具类型
3. 增加群体大小
4. 运行对照实验
5. 统计分析

---

## 📞 需要帮助？

- 查看 [EXPERIMENT_REPORT.md](EXPERIMENT_REPORT.md)
- 检查日志文件
- 阅读版本文档

---

**祝实验顺利！🧬**
