# MOSS Experiments Directory Structure

**Last Updated**: 2026-03-24

## 目录结构

```
experiments/
├── run_4_series/              # Run 4.x 系列实验
│   ├── run_4_2/              # 基准实验 (Survival初始, 10%探索)
│   │   ├── run_4_2.py              # 实验脚本
│   │   ├── run_4_2_actions.jsonl   # 行动记录
│   │   ├── run_4_2_status.json     # 状态记录
│   │   ├── run_4_2_final_status.json
│   │   ├── RUN_4_2_ANALYSIS_REPORT.md
│   │   └── checkpoints/            # 检查点文件
│   │       └── checkpoint_*.json
│   ├── run_4_3/              # Curiosity初始变体
│   │   ├── run_4_3_optimized.py    # 原始脚本
│   │   ├── run_4_3_resumed.py      # 恢复脚本
│   │   ├── run_4_3_actions.jsonl   # 行动记录 (运行中)
│   │   ├── run_4_3_status.json     # 状态记录 (运行中)
│   │   └── checkpoints/            # 检查点文件
│   ├── run_4_4/              # 高探索率变体 (20%探索)
│   │   ├── run_4_4_optimized.py    # 原始脚本
│   │   ├── run_4_4_resumed.py      # 恢复脚本
│   │   ├── run_4_4_actions.jsonl   # 行动记录 (运行中)
│   │   ├── run_4_4_status.json     # 状态记录 (运行中)
│   │   └── checkpoints/            # 检查点文件
│   └── README.md             # 本文件
├── analysis/                  # 分析脚本
│   └── analyze_run4_series.py # Run 4.x对比分析工具
├── real_world_*.py           # 真实世界实验脚本
├── real_world_*.jsonl        # 真实世界实验数据
└── ...                       # 其他实验文件
```

## Run 4.x 实验设计

| 实验 | 初始Purpose | 探索率 | 研究问题 |
|------|-------------|--------|----------|
| Run 4.2 | Survival | 10% | 基准行为 |
| Run 4.3 | **Curiosity** | 10% | 初始Purpose是否影响收敛？ |
| Run 4.4 | Survival | **20%** | 探索率是否影响多样性？ |

## 快速分析

```bash
# 分析所有Run 4.x实验
cd experiments/analysis
python3 analyze_run4_series.py

# 查看特定Run的状态
cat experiments/run_4_series/run_4_3/run_4_3_status.json
```

## 数据文件格式

### actions.jsonl
每行一个JSON对象：
```json
{
  "ts": "2026-03-24T08:14:00",
  "step": 924000,
  "action": "explore_new_patterns",
  "success": true,
  "reward": 0.15,
  "purpose": "Surv"
}
```

### status.json
```json
{
  "timestamp": "2026-03-24T08:14:00",
  "step": 924000,
  "progress": 0.321,
  "purpose": {
    "dominant": "Survival",
    "statement": "I exist to persist..."
  },
  "metrics": {
    "exp_rate": 0.1,
    "diversity": 0.16,
    "success_rate": 0.62
  }
}
```

## 检查点格式

### checkpoint_*.json
```json
{
  "step": 700000,
  "timestamp": "2026-03-23T23:15:04",
  "purpose_state": [0.22, 0.22, 0.22, 0.22, 0.97, 0.34, 0.0, 0.0, 0.11],
  "exploration_rate": 0.1
}
```

Purpose state向量顺序:
1. survival
2. curiosity
3. influence
4. optimization
5. coherence
6. valence
7. other_modeling
8. norm_internalization
9. self_generated
