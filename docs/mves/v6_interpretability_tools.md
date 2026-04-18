# MOSS v6.0 可解释性工具文档

**版本**: v6.0.0  
**日期**: 2026-04-18  
**状态**: ✅ 已完成

---

## 概述

可解释性工具套件为 MOSS v6.0 实验提供深度分析能力，包括：

1. **Latent Cluster 导出** - 从检查点提取驱动权重和状态向量
2. **行为片段关联** - 关联驱动状态与行为日志
3. **反事实测试** - 驱动消融实验和因果验证
4. **可视化工具** - 生成权重时序图、聚类分析等

---

## 模块清单

| 模块 | 路径 | 功能 |
|------|------|------|
| LatentExporter | `agi/analysis/latent_export.py` | 聚类分析、PCA降维 |
| BehaviorMapper | `agi/analysis/behavior_mapping.py` | 行为-驱动映射 |
| CounterfactualTester | `scripts/counterfactual_test.py` | 消融实验 |
| visualize_latent | `scripts/visualize_latent.py` | 可视化报告 |

---

## 快速开始

### 1. 生成可视化报告

```bash
python scripts/visualize_latent.py \
    --experiment-dir logs/experiment_v6_full_20260417_224303_seed456 \
    --output logs/visualization
```

输出文件: `logs/visualization/visualization_report.txt`

### 2. 运行反事实测试

```bash
python scripts/counterfactual_test.py \
    --checkpoint-dir logs/experiment_v6_full_*/ \
    --cycles 1000 \
    --repeats 3
```

### 3. 使用 Python API

```python
from agi.analysis.latent_export import LatentExporter
from agi.analysis.behavior_mapping import BehaviorMapper

# 加载检查点
exporter = LatentExporter()
exporter.load_checkpoints('logs/experiment_v6_full_*/')

# K-Means 聚类
clusters, info = exporter.cluster_kmeans(n_clusters=3)
for cluster in clusters:
    print(f"Cluster {cluster.cluster_id}: {len(cluster.samples)} samples")

# PCA 降维
pca_result = exporter.reduce_pca(n_components=2)
print(f"解释方差: {pca_result.explained_variance_ratio}")
```

---

## LatentExporter 详细说明

### 类方法

#### `load_checkpoints(checkpoint_dir, pattern="checkpoint_*.json")`

从目录加载检查点文件。

**参数**:
- `checkpoint_dir`: 检查点目录路径
- `pattern`: 文件匹配模式

**返回**: 加载的检查点数量

**示例**:
```python
exporter = LatentExporter()
n_loaded = exporter.load_checkpoints('logs/experiment_v6/')
print(f"加载了 {n_loaded} 个检查点")
```

#### `cluster_kmeans(n_clusters=3, standardize=True, random_state=42)`

执行 K-Means 聚类分析。

**参数**:
- `n_clusters`: 聚类数量 (默认 3)
- `standardize`: 是否标准化数据 (默认 True)
- `random_state`: 随机种子

**返回**: `(clusters, info)`
- `clusters`: ClusterResult 列表
- `info`: 聚类信息字典

**示例**:
```python
clusters, info = exporter.cluster_kmeans(n_clusters=3)
for cluster in clusters:
    print(f"Cluster {cluster.cluster_id}:")
    print(f"  样本数: {len(cluster.samples)}")
    print(f"  平均权重: {cluster.avg_weights}")
```

#### `reduce_pca(n_components=2, standardize=True)`

执行 PCA 降维。

**参数**:
- `n_components`: 主成分数量 (默认 2)
- `standardize`: 是否标准化数据 (默认 True)

**返回**: PCAResult 对象

**示例**:
```python
pca_result = exporter.reduce_pca(n_components=2)
print(f"解释方差比: {pca_result.explained_variance_ratio}")
print(f"累积方差: {sum(pca_result.explained_variance_ratio):.4f}")
```

#### `get_drive_weights(drive_name)`

获取指定驱动的权重历史。

**参数**:
- `drive_name`: 驱动名称

**返回**: 权重值列表

#### `get_drive_stats(drive_name)`

获取指定驱动的统计信息。

**参数**:
- `drive_name`: 驱动名称

**返回**: 统计信息字典 (mean, std, min, max, median, range)

---

## BehaviorMapper 详细说明

### 类方法

#### `load_data(checkpoint_dir, behavior_log_path=None)`

加载检查点和行为日志。

**参数**:
- `checkpoint_dir`: 检查点目录
- `behavior_log_path`: 行为日志路径 (可选)

**返回**: 加载的检查点数量

**示例**:
```python
mapper = BehaviorMapper()
n_loaded = mapper.load_data('logs/experiment_v6/')
```

#### `segment_behaviors(window_size=100)`

将行为分割成片段。

**参数**:
- `window_size`: 窗口大小 (周期数)

**返回**: BehaviorSegment 列表

#### `analyze_drive_behavior_mapping()`

分析驱动-行为映射。

**返回**: 驱动名称 -> DriveBehaviorMapping 的字典

---

## CounterfactualTester 详细说明

### 类方法

#### `__init__(drive_manager, environment)`

初始化反事实测试器。

**参数**:
- `drive_manager`: DriveManager 实例
- `environment`: 环境实例

#### `run_ablation_test(drive_name, cycles=1000, repeats=3)`

执行驱动消融实验。

**参数**:
- `drive_name`: 要禁用的驱动名称
- `cycles`: 每次模拟周期数
- `repeats`: 重复次数

**返回**: AblationResult 对象

**示例**:
```python
from agi.drive_manager import DriveManager
from agi.environment_v2 import RealEnvironmentV2
from scripts.counterfactual_test import CounterfactualTester

drive_manager = DriveManager(...)
environment = RealEnvironmentV2(...)

tester = CounterfactualTester(drive_manager, environment)
result = tester.run_ablation_test('survival', cycles=1000, repeats=3)

print(f"基线均值: {result.baseline_mean}")
print(f"消融均值: {result.ablated_mean}")
print(f"p-value: {result.p_value}")
print(f"效应量: {result.effect_size.cohens_d}")
```

---

## 可视化报告格式

可视化报告包含以下部分：

### 1. 权重时序分布

显示每个检查点周期各驱动的权重值。

```
Cycle      composit | curiosit | influenc | optimiza | survival
--------------------------------------------------------------------
1000       0.3076   | 0.0964   | 0.1285   | 0.1728   | 0.2947
2000       0.3500   | 0.0434   | 0.0579   | 0.2496   | 0.2991
```

### 2. 权重变化趋势

显示各驱动从初始到最终的变化。

```
composite_emergence_v3 0.3076 → 0.3500 (+0.0424, +13.8%) ↑
curiosity            0.0964 → 0.0434 (-0.0530, -54.9%) ↓
```

### 3. 聚类分析

K-Means 聚类结果，显示每个聚类的样本数和平均权重。

### 4. PCA 降维分析

主成分分析结果，显示解释方差比和累积方差。

---

## 测试

运行单元测试：

```bash
python -m pytest tests/test_interpretability.py -v
```

预期输出：
```
============================= test session starts ==============================
tests/test_interpretability.py::TestLatentExporter::test_cluster_kmeans PASSED
tests/test_interpretability.py::TestLatentExporter::test_get_drive_stats PASSED
tests/test_interpretability.py::TestLatentExporter::test_get_drive_weights PASSED
tests/test_interpretability.py::TestLatentExporter::test_initialization PASSED
tests/test_interpretability.py::TestLatentExporter::test_load_checkpoints_from_list PASSED
tests/test_interpretability.py::TestLatentExporter::test_reduce_pca PASSED
tests/test_interpretability.py::TestBehaviorMapper::test_initialization PASSED
tests/test_interpretability.py::TestIntegration::test_end_to_end_workflow PASSED
============================== 8 passed in 1.08s ===============================
```

---

## 依赖

- numpy
- scikit-learn
- scipy

安装：
```bash
pip install numpy scikit-learn scipy
```

---

## 文件清单

```
agi/analysis/
├── latent_export.py          # LatentExporter 类
├── behavior_mapping.py       # BehaviorMapper 类
├── effect_size.py            # 效应量计算
├── bootstrap.py              # Bootstrap CI
└── multiple_comparison.py    # 多重比较校正

scripts/
├── visualize_latent.py       # 可视化工具
└── counterfactual_test.py    # 反事实测试

tests/
└── test_interpretability.py  # 单元测试

docs/mves/
└── v6_interpretability_tools.md  # 本文档
```

---

## 后续工作

- [ ] 支持 Matplotlib 图形输出
- [ ] 交互式可视化 (Plotly/Dash)
- [ ] 更多聚类算法 (DBSCAN, Hierarchical)
- [ ] t-SNE 降维支持

---

**最后更新**: 2026-04-18  
**维护者**: MOSS Team
