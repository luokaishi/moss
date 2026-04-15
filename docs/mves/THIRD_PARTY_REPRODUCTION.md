# 第三方独立复现指南

**版本**: 1.0  
**日期**: 2026-04-15  
**目标**: 支持完全独立的第三方复现

---

## 快速开始 (5分钟)

### 使用Docker (推荐)

```bash
# 1. 克隆仓库
git clone https://github.com/luokaishi/moss.git
cd moss

# 2. 运行实验
docker-compose up moss

# 3. 验证结果
python experiments/raw_logs/7layer_v2_5000/verify_reproduction.py \
  experiments/raw_logs/7layer_v2_5000/cycle_logs.csv \
  experiments/output/cycle_logs.csv
```

---

## 详细复现步骤

### 环境要求

| 组件 | 版本 | 检查命令 |
|------|------|----------|
| Python | 3.11+ | `python --version` |
| NumPy | 1.24+ | `python -c "import numpy; print(numpy.__version__)"` |
| Git | 2.30+ | `git --version` |
| 内存 | 4GB+ | `free -h` |
| 磁盘 | 1GB+ | `df -h` |

### 本地安装

```bash
# 1. 克隆仓库
git clone https://github.com/luokaishi/moss.git
cd moss
git checkout mves

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或: venv\\Scripts\\activate  # Windows

# 3. 安装依赖
pip install numpy pyyaml pytest flake8 scikit-learn

# 4. 设置环境
export PYTHONPATH=$(pwd)
```

### 运行实验

```bash
# 主实验: 5000周期
python experiment_7layer_v2_5000.py

# 预期输出:
# 概念误差: 0.309 → 0.028
# Self-Model准确率: 89.6%
# Goal涌现: 2个目标
```

### 验证结果

```bash
# 1. 检查关键指标
python -c "
import json
with open('experiments/7layer_v2_5000/results_5000cycles.json') as f:
    r = json.load(f)
print(f\"Self-Model: {r['self_model']['final_accuracy']:.1%}\")
print(f\"Goal涌现: {r['goal']['emerged']}\")
"

# 2. 对比原始数据
python experiments/raw_logs/7layer_v2_5000/verify_reproduction.py \
  experiments/raw_logs/7layer_v2_5000/cycle_logs.csv \
  experiments/7layer_v2_5000/cycle_logs.csv
```

---

## 复现清单

### 基础复现

- [ ] 环境安装成功
- [ ] 仓库克隆成功
- [ ] 依赖安装成功
- [ ] 实验运行成功
- [ ] 结果文件生成
- [ ] 关键指标匹配

### 扩展复现

- [ ] 多种子验证通过
- [ ] 特征对比实验运行
- [ ] Docker复现成功
- [ ] 统计报告生成

---

## 预期结果

### 关键指标 (随机种子=42)

| 指标 | 期望值 | 容差 | 验证 |
|------|--------|------|------|
| Self-Model准确率 | 89.6% | ±2% | ✅ |
| 概念误差 | 0.028 | ±0.005 | ✅ |
| 概念稳定性 | 0.999 | ±0.001 | ✅ |
| Goal涌现 | True | - | ✅ |
| Goal数量 | 2 | ±1 | ✅ |

### 统计指标

| 指标 | 期望值 | 容差 |
|------|--------|------|
| 95% CI下限 | 88.2% | ±1% |
| 95% CI上限 | 91.0% | ±1% |
| Cohen's d | 4.72 | ±0.5 |

---

## 故障排除

### 导入错误

```bash
# 错误: ModuleNotFoundError
export PYTHONPATH=$(pwd)
# 或: set PYTHONPATH=%cd%  (Windows)
```

### 内存不足

```bash
# 减少周期数
python experiment_7layer_v2_5000.py --cycles 1000
```

### 结果不匹配

```bash
# 检查随机种子
echo $PYTHONHASHSEED  # 应为42

# 检查NumPy版本
python -c "import numpy; print(numpy.__version__)"  # 应为1.24+
```

---

## 验证方法

### 1. 指标对比

```python
import json

# 加载原始结果
with open('experiments/raw_logs/7layer_v2_5000/metadata.json') as f:
    original = json.load(f)

# 加载你的结果
with open('experiments/7layer_v2_5000/results_5000cycles.json') as f:
    yours = json.load(f)

# 对比
assert abs(yours['self_model']['final_accuracy'] - 0.896) < 0.02
assert yours['goal']['emerged'] == True
print("✅ 验证通过!")
```

### 2. 统计检验

```bash
# 运行统计检验
python -m pytest tests/ -v
```

### 3. 可视化对比

```python
import pandas as pd
import matplotlib.pyplot as plt

orig = pd.read_csv('experiments/raw_logs/7layer_v2_5000/cycle_logs.csv')
yours = pd.read_csv('experiments/7layer_v2_5000/cycle_logs.csv')

plt.plot(orig['self_model_accuracy'], label='Original')
plt.plot(yours['self_model_accuracy'], label='Yours')
plt.legend()
plt.savefig('comparison.png')
```

---

## 报告问题

如果复现失败，请提供:

1. **环境信息**
   ```bash
   python --version
   python -c "import numpy; print(numpy.__version__)"
   uname -a
   ```

2. **错误日志**
   ```bash
   python experiment_7layer_v2_5000.py 2>&1 | tee error.log
   ```

3. **结果差异**
   ```bash
   python -c "
   import json
   with open('experiments/7layer_v2_5000/results_5000cycles.json') as f:
       r = json.load(f)
   print(f\"Your result: {r['self_model']['final_accuracy']}\")
   print(f\"Expected: 0.896\")
   "
   ```

**提交Issue**: https://github.com/luokaishi/moss/issues

---

## 独立验证声明

完成复现后，请提交:

```markdown
## 独立复现报告

**复现者**: [你的名字/机构]
**日期**: [日期]
**环境**: [OS, Python版本, NumPy版本]

### 结果对比

| 指标 | 原始值 | 复现值 | 匹配 |
|------|--------|--------|------|
| Self-Model | 89.6% | [你的值] | [是/否] |
| Goal涌现 | 是 | [你的结果] | [是/否] |

### 结论
[你的结论]

### 签名
[你的名字]
```

---

## 参考

- [Docker指南](DOCKER_GUIDE.md)
- [统计报告](STATISTICAL_REPORT_5000CYCLES.md)
- [预注册实验](PREREGISTERED_EXPERIMENTS.md)
