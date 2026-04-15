# 原始日志: 7layer_v2_5000

## 实验信息
- **实验名称**: 7层AGI涌现架构5000周期
- **导出时间**: 2026-04-15T23:56:22.476934
- **随机种子**: 42
- **Git提交**: cdbe495e2

## 文件说明

### 元数据
- `metadata.json`: 实验配置和环境信息

### 详细日志
- `cycle_logs.csv`: 每周期详细记录 (5000行)
  - 概念系统指标
  - Self-Model指标
  - Goal系统指标
  - Meta-Drive指标
  - 行为记录

### 检查点
- `checkpoints/checkpoint_*.json`: 每100周期检查点
  - 共50个检查点
  - 用于实验恢复和验证

### 随机种子
- `seeds.json`: 完整随机种子记录
  - 确保完全可复现

## 数据格式

### cycle_logs.csv
```
cycle: 周期数 (0-4999)
concept_error: 概念预测误差
concept_stability: 概念稳定性 (0-1)
self_model_accuracy: 自我模型准确率 (0-1)
num_goals: 活跃目标数
goal_stability: 目标稳定性 (0-1)
meta_triggered: Meta-Drive是否触发
behavior_pattern: 行为模式 (explore/exploit)
action_taken: 执行的动作
reward_received: 获得的奖励
```

## 使用示例

```python
import pandas as pd

# 加载日志
df = pd.read_csv('cycle_logs.csv')

# 分析概念稳定性
mean_stability = df['concept_stability'].mean()

# 分析Goal涌现
goal_cycles = df[df['num_goals'] > 0]['cycle']
```

## 复现验证

```bash
# 使用相同种子复现
python experiment_7layer_v2_5000.py --seed 42

# 对比结果
python verify_reproduction.py --original cycle_logs.csv --new new_logs.csv
```

## 引用

```
MOSS 7-Layer AGI Emergence Architecture
Experiment: 7layer_v2_5000
Data: experiments/raw_logs/7layer_v2_5000/
```
