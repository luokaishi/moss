# MOSS 实验指南

**日期**: 2026-04-22  
**版本**: v8.2.0-dev

---

## 快速开始

### 1. 运行 N=10 LLM 验证实验

```bash
# 方式 1: 使用脚本 (推荐)
./run_n10_experiment.sh mock    # Mock 模式 (零成本)
./run_n10_experiment.sh real    # 真实 LLM (需 API Key)

# 方式 2: 直接运行
python3 experiments/n10_llm_validation.py
```

### 2. 检查实验状态

```bash
python3 check_experiment_status.py
```

### 3. 查看结果

```bash
# 汇总统计
cat experiments/n10_llm_validation/results/summary.json

# 统计报告
cat experiments/n10_llm_validation/results/statistical_report.md

# 详细数据
cat experiments/n10_llm_validation/results/results.json
```

---

## 实验列表

| 实验 | 脚本 | 时间 | 成本 | 状态 |
|------|------|------|------|------|
| N=10 LLM 验证 | `n10_llm_validation.py` | 30-60 min | ¥40 | ⏳ 待运行 |
| 100 代长期 | `longterm_100gen.py` | 10 days | ¥100 | 📅 计划中 |
| 成本优化 | `cost_optimization.py` | 1-2 days | ¥50 | 📅 计划中 |
| 消融实验 | `ablation_study.py` | 3-5 days | ¥200 | 📅 计划中 |

---

## 配置说明

### Mock 模式 (测试)

- 零成本
- 快速验证代码逻辑
- 模拟 LLM 响应

### 真实 LLM 模式

```bash
# 设置 API Key
export DASHSCOPE_API_KEY="your-api-key"

# 或使用 .env 文件
echo "DASHSCOPE_API_KEY=your-key" > .env
```

**成本估算**:
- N=10 实验: ~¥40
- 100 代长期: ~¥100
- 消融实验: ~¥200

---

## 实验设计

### N=10 LLM 验证

**目标**: 验证 LLM 引导变异有效性

**设计**:
- E 组: GP + LLM (50%) + Elite (N=5)
- C 组: GP-only 基线 (N=5)
- 每实验: 30 代

**指标**:
- Fitness 提升 (主要)
- LLM 调用次数
- Token 使用量
- 统计显著性 (p < 0.05)

---

## 故障排除

### 问题: Python 依赖缺失

```bash
pip3 install numpy
```

### 问题: API Key 无效

```bash
# 检查是否设置
echo $DASHSCOPE_API_KEY

# 重新设置
export DASHSCOPE_API_KEY="your-key"
```

### 问题: 实验中断

```bash
# 重新运行会自动从检查点恢复
python3 experiments/n10_llm_validation.py
```

---

## 结果提交

实验完成后提交到 GitHub:

```bash
git add experiments/n10_llm_validation/results/
git commit -m "experiments: N=10 LLM 验证结果"
git push origin mves
```

---

**技术支持**: MOSS 开发团队  
**最后更新**: 2026-04-22
