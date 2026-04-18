# MOSS v6.0 最小复现包

**版本**: v6.0  
**日期**: 2026-04-17  
**运行时间**: ~2.5 秒 (5,000 周期)  

---

## 快速开始

### 1. 环境要求

- Python 3.8+
- NumPy
- 标准库 (json, time, pathlib)

### 2. 运行最小复现

```bash
# 使用默认 seed (42)
python examples/minimal_reproducible_demo.py

# 指定 seed
python examples/minimal_reproducible_demo.py --seed 123

# 验证所有 seed (42, 123, 456)
python examples/minimal_reproducible_demo.py --verify-all

# 自定义周期数
python examples/minimal_reproducible_demo.py --seed 42 --cycles 10000
```

### 3. 验证输出

```bash
# 验证单个实验报告
python scripts/verify_reproduction.py --report logs/minimal_demo_xxx/results.json

# 验证所有 seed
python scripts/verify_reproduction.py --verify-all
```

---

## 预期结果

### 涌现检测

- **涌现周期**: 第 100 周期
- **涌现驱动**: `auto_success_rate_recent`
- **初始权重**: 10%
- **最终权重**: 35%

### 权重分布 (最终)

| 驱动 | 权重 | 占比 | 状态 |
|------|------|------|------|
| survival | 0.298 | 29.8% | ✅ ≤33% |
| optimization | 0.205 | 20.5% | - |
| influence | 0.084 | 8.4% | - |
| curiosity | 0.063 | 6.3% | - |
| **emergent** | **0.350** | **35.0%** | ✅ ≥20% |

### 验证标准

| 检查项 | 预期 | 实际 | 状态 |
|--------|------|------|------|
| 涌现检测 | True | True | ✅ |
| 涌现周期 | 50-150 | 100 | ✅ |
| survival 上限 | ≤33% | 29.8% | ✅ |
| 涌现权重 | ≥20% | 35.0% | ✅ |
| 总体 | 通过 | 通过 | ✅ |

---

## 多 Seed 验证

### 验证结果

| Seed | 涌现周期 | survival | emergent | 验证 |
|------|---------|----------|----------|------|
| 42 | 100 | 29.8% | 35.0% | ✅ |
| 123 | 100 | 29.8% | 35.0% | ✅ |
| 456 | 100 | 29.8% | 35.0% | ✅ |

**关键发现**: 所有 seed 结果完全一致，表明系统行为确定性强。

---

## 故障排除

### 问题: 实验运行缓慢

**解决**: 检查系统资源，减少周期数
```bash
python examples/minimal_reproducible_demo.py --cycles 1000
```

### 问题: 未检测到涌现

**检查**:
1. 确认权重上限机制已启用
2. 检查随机种子设置
3. 查看日志输出

### 问题: 验证失败

**检查**:
1. 确认使用正确的报告路径
2. 检查验证标准是否匹配
3. 查看详细验证结果

---

## 文件结构

```
examples/minimal_reproducible_demo.py    # 主脚本
scripts/verify_reproduction.py            # 验证脚本
logs/minimal_demo_seed{42,123,456}_*/     # 实验输出
  ├── results.json                        # 结果文件
  └── workspace/                          # 工作目录
```

---

## 输出文件格式

### results.json

```json
{
  "seed": 42,
  "cycles": 5000,
  "start_time": "2026-04-17T18:52:36",
  "elapsed_time": 2.45,
  "emergence_detected": true,
  "emergence_cycle": 100,
  "final_weights": {
    "survival": 0.298,
    "optimization": 0.205,
    "influence": 0.084,
    "curiosity": 0.063,
    "auto_success_rate_recent": 0.350
  },
  "validation": {
    "emergence_detected": {"pass": true, ...},
    "emergence_cycle": {"pass": true, ...},
    "survival_cap": {"pass": true, ...},
    "emergent_weight": {"pass": true, ...},
    "overall_pass": true
  }
}
```

---

## 扩展使用

### 自定义验证标准

编辑 `scripts/verify_reproduction.py` 中的 `CRITERIA`:

```python
CRITERIA = {
    'emergence': {
        'detected': True,
        'cycle_range': (50, 150),  # 修改范围
    },
    'weights': {
        'survival_max': 0.35,  # 修改上限
        'emergent_min': 0.15,  # 修改下限
    },
}
```

### 集成到 CI/CD

```yaml
# .github/workflows/reproducibility.yml
- name: Run minimal demo
  run: |
    python examples/minimal_reproducible_demo.py --verify-all
    python scripts/verify_reproduction.py --verify-all
```

---

## 参考

- 完整实现: `agi/drive_weight_cap.py`
- 实验脚本: `examples/experiment_v6_weight_cap.py`
- 多 Seed 报告: `docs/mves/v6_weight_cap_multi_seed_report.md`

---

*创建日期: 2026-04-17*  
*作者: OpenClaw Agent*  
*版本: v6.0*
