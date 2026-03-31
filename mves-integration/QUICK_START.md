# MVES v5 快速开始指南

## 5 分钟快速体验

### 1. 安装依赖 (2 分钟)

```bash
cd /home/admin/.openclaw/workspace/projects/moss/mves-integration

# 安装 Python 依赖
pip install -r requirements.txt
```

### 2. 运行快速测试 (1 分钟)

```bash
# 快速测试模式 (1 小时实验，约 6 代)
python3 mves_v5/main.py --quick
```

**预期输出**:
```
======================================================================
MVES v5 - Minimal Evolutionary AGI Prototype
======================================================================
Mode: Quick Test
Duration: 1 hours
Population: 5 agents
...
✓ Checkpoint saved
```

### 3. 查看结果 (1 分钟)

```bash
# 查看检查点
ls -lh mves_v5/checkpoints/

# 查看最终结果
python3 -c "import json,gzip; d=json.load(gzip.open('mves_v5/checkpoints/final_result.json.gz','rt')); print('最终适应度:', d['history'][-1]['avg_fitness'])"
```

### 4. 分析数据 (1 分钟)

```bash
# 提取数据
python3 scripts/4a_extract_data.py

# 统计分析
python3 scripts/4b_statistical_analysis.py

# 生成可视化
python3 scripts/4c_create_visualizations.py
```

---

## 标准实验流程

### 运行 24 小时实验

```bash
python3 mves_v5/main.py --hours 24
```

**参数说明**:
- `--hours 24`: 运行 24 小时
- `--quick`: 快速测试模式 (1 小时)
- `--population 10`: 自定义种群大小

### 完整分析流程

```bash
# 1. 数据提取
python3 scripts/4a_extract_data.py

# 2. 统计分析
python3 scripts/4b_statistical_analysis.py

# 3. 可视化生成
python3 scripts/4c_create_visualizations.py

# 4. 涌现分析
python3 scripts/4d_emergence_analysis.py
```

### 查看结果

```bash
# 数据文件
cat analysis/dataset_clean.csv | head

# 统计报告
cat analysis/statistical_analysis.md

# 涌现报告
cat analysis/emergence_analysis.md

# 可视化图表
ls -lh plots/
```

---

## 常见问题

### Q: 内存不足怎么办？

A: 减少种群大小：
```bash
python3 mves_v5/main.py --hours 24 --population 5
```

### Q: 如何查看实时进度？

A: 实验日志会实时输出：
```bash
# 查看日志
tail -f mves_v5/../logs/*.log 2>/dev/null

# 或查看最新检查点
ls -lt mves_v5/checkpoints/ | head
```

### Q: 如何复现论文结果？

A: 使用固定随机种子：
```bash
# 修改 main.py，添加 random.seed(42)
python3 mves_v5/main.py --hours 24
```

---

## 下一步

- 📚 阅读 [DESIGN.md](DESIGN.md) 了解系统架构
- 📊 查看 [EXPERIMENT_REPORT.md](EXPERIMENT_REPORT.md) 了解实验结果
- 📄 参考 [papers/MVES_PAPER_DRAFT_v1.md](papers/MVES_PAPER_DRAFT_v1.md) 了解科学背景

---

*快速开始指南 - 2026-03-31*
