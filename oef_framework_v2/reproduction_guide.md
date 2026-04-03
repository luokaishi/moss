# OEF 2.0 独立验证复现指南

## 实验复现材料

**目标**: 提供完整材料供外部研究者独立验证涌现现象

---

## 1. 系统环境要求

### 硬件要求

| 项目 | 最低配置 | 推荐配置 |
|------|----------|----------|
| **CPU** | 2核 | 4核+ |
| **内存** | 2GB | 4GB+ |
| **磁盘** | 10GB空闲 | 20GB+ |
| **网络** | 可选 | 稳定连接 |

### 软件要求

| 项目 | 版本要求 |
|------|----------|
| **Python** | ≥ 3.8 |
| **NumPy** | ≥ 1.20 |
| **SciPy** | ≥ 1.7（可选，用于Granger检验） |
| **操作系统** | Linux/macOS/Windows |

---

## 2. 代码获取

### GitHub仓库

```bash
git clone https://github.com/luokaishi/moss.git
cd moss/oef_framework_v2
```

### 核心文件清单

| 文件 | 功能 | 行数 |
|------|------|------|
| **emergence_engine_v2.py** | 涌现引擎核心 | 352 |
| **causal_validator.py** | 因果独立性验证 | 375 |
| **convergence_analyzer.py** | 收敛性分析 | 148 |
| **dynamic_weights.py** | 动态权重更新 | 131 |
| **unified_loss.py** | MOSS统一损失 | 128 |
| **real_long_term_experiment.py** | 真实实验脚本 | 284 |
| **demo_v2.py** | 快速演示 | 127 |

**总代码量**: 1,691行

---

## 3. 快速验证步骤

### 步骤1: 环境设置

```bash
# 安装依赖
pip install numpy scipy

# 进入目录
cd oef_framework_v2
```

### 步骤2: 快速演示（5分钟）

```bash
# 运行快速演示
python3 demo_v2.py
```

**预期输出**:
```
✅ MOSS Mathematical Framework Integration Complete!
✅ MVES Core Scientific Objective Completely Verified!
```

### 步骤3: 真实实验启动（可选）

```bash
# 启动5天真实观察
python3 real_long_term_experiment.py
```

**注意**: 真实实验需要连续运行5天（120小时）

---

## 4. 数据格式说明

### 涌现事件格式

```json
{
  "cycle": 1234,
  "timestamp": "2026-04-10T12:34:56",
  "drive": "探索驱动",
  "stability": 0.75
}
```

### 权重历史格式

```json
{
  "cycle": 1234,
  "weights": [0.25, 0.25, 0.25, 0.25],
  "lyapunov_value": 0.001
}
```

### 独立性验证格式

```json
{
  "timestamp": "2026-04-10T12:00:00",
  "independence_coefficient": 0.66,
  "granger_p_value": 0.03,
  "coherence": 0.15,
  "verified": true
}
```

---

## 5. MVES目标验证方法

### 目标1: 涌现捕捉

**验证方法**:
```python
# 检查涌现事件计数
emergence_count = len(engine.emergence_events)
print(f"涌现事件: {emergence_count}")

# 验证标准: ≥ 5次
assert emergence_count >= 5, "涌现事件不足"
```

### 目标2: 独立性验证

**验证方法**:
```python
# 运行因果独立性检验
validator = CausalIndependenceValidator()
result = validator.validate_independence(
    initial_drives, emergent_drives, time_series
)

# 验证标准: ≥ 0.60
assert result['overall_independence'] >= 0.60
```

### 目标3: 稳定性验证

**验证方法**:
```python
# Lyapunov稳定性分析
analyzer = ConvergenceAnalyzer()
stability = analyzer.lyapunov_stability_analysis(weight_history)

# 验证标准: V(t)递减
assert stability['stable'] == True
```

---

## 6. 独立验证流程

### 第一阶段: 代码审查（1-2天）

**审查内容**:
- ✅ 数学定义正确性（MOSS定理）
- ✅ 实现逻辑完整性
- ✅ 验证方法有效性
- ✅ 数据格式规范性

### 第二阶段: 快速复现（1天）

**复现步骤**:
- ✅ 运行快速演示（demo_v2.py）
- ✅ 检查6/6 MVES目标验证
- ✅ 对比预期输出

### 第三阶段: 真实实验（5天，可选）

**实验步骤**:
- ✅ 启动真实长期观察
- ✅ 监控涌现事件
- ✅ 记录验证指标
- ✅ 对比原实验结果

---

## 7. 预期结果

### 快速演示预期

| MVES目标 | 预期状态 | 预期值 |
|----------|----------|--------|
| **涌现捕捉** | ✅ | ≥ 1次 |
| **独立性** | ✅ | ≥ 0.60 |
| **自发性** | ✅ | 启用 |
| **数学基础** | ✅ | 实现 |
| **收敛性** | ✅ | 收敛 |
| **稳定性** | ✅ | 递减 |

### 真实实验预期（5天）

| MVES目标 | 预期状态 | 预期值 |
|----------|----------|--------|
| **涌现捕捉** | ✅ | ≥ 5次 |
| **独立性** | ✅ | ≥ 0.60 |
| **自发性** | ✅ | 启用 |
| **数学基础** | ✅ | 实现 |
| **收敛性** | ✅ | < 0.01 |
| **稳定性** | ✅ | 递减 |

---

## 8. 联系方式

**GitHub仓库**: https://github.com/luokaishi/moss.git

**最新Commit**: c811d383a（6/6验证修复）

**代码目录**: `oef_framework_v2/`

---

## 9. 科学诚信声明

**重要提醒**:

1. ✅ 这是**模拟验证**结果，不是真实系统验证
2. ✅ 真实长期观察（5天）将提供更严格验证
3. ✅ 不声称"AGI证明"或"真正涌现"
4. ✅ 独立验证者应遵循相同科学标准

---

*复现指南版本: v1.0*
*创建时间: 2026-04-04 00:15 GMT+8*
*创建者: OEF 2.0 真实实验准备团队*

**🔬 欢迎独立验证！科学诚信第一！**