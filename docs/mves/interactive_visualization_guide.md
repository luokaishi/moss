# MOSS v6.1 交互式可视化指南

**版本**: 6.1.0  
**更新日期**: 2026-04-18  
**文档类型**: 使用指南

---

## 简介

MOSS v6.1 引入了全新的交互式可视化工具，使用 Plotly 和 Dash 技术栈，提供丰富的数据探索和演示功能。

### 功能特性

1. **实时权重监控** - 动态更新的权重时序图
2. **涌现检测动画** - 可视化涌现事件的时间分布
3. **交互式 PCA 可视化** - 鼠标悬停显示详情，探索状态空间
4. **3D 聚类可视化** - 三维聚类分析
5. **时间轴回放** - 带播放控制的历史回放功能

---

## 安装

### 依赖安装

```bash
# 基础依赖（必须）
pip install plotly dash

# 可选依赖（推荐）
pip install scikit-learn pandas

# 完整安装
pip install plotly dash scikit-learn pandas numpy
```

### 验证安装

```bash
python -c "import plotly; import dash; print('✓ 安装成功')"
```

---

## 快速开始

### 1. 启动交互式仪表板

```bash
# 基本用法
python scripts/visualize_interactive.py --experiment-dir logs/experiment_v6_full_seed42

# 指定端口
python scripts/visualize_interactive.py --experiment-dir logs/experiment_v6_full_seed42 --port 8051

# 指定主机（远程访问）
python scripts/visualize_interactive.py --experiment-dir logs/experiment_v6_full_seed42 --host 0.0.0.0 --port 8050
```

### 2. 导出静态 HTML

```bash
# 导出所有可视化为 HTML 文件
python scripts/visualize_interactive.py --experiment-dir logs/experiment_v6_full_seed42 --export-only --output logs/visualization
```

---

## 可视化类型详解

### 1. 权重时序图 (Weight Timeline)

**用途**: 查看各驱动力权重随时间的变化趋势

**交互功能**:
- 鼠标悬停查看具体数值
- 图例点击隐藏/显示特定驱动
- 框选缩放时间范围
- 双击重置视图

**解读指南**:
- 上升曲线 (↑): 该驱动力在增强
- 下降曲线 (↓): 该驱动力在减弱
- 平稳曲线 (→): 该驱动力已稳定

---

### 2. 涌现检测动画 (Emergence Animation)

**用途**: 可视化涌现事件的发生时间和分布

**视图组成**:
- 上半部分: 权重演化曲线
- 下半部分: 涌现事件标记（红星标记）

**交互功能**:
- 悬停查看涌现的驱动名称
- 点击标记查看详情

---

### 3. 交互式 PCA 可视化 (PCA Visualization)

**用途**: 降维探索高维驱动状态空间

**视图组成**:
- 主成分散点图（颜色表示时间）
- 状态轨迹连线
- 起点（绿色星）和终点（红色X）标记

**交互功能**:
- 悬停查看该时刻所有驱动权重
- 缩放和平移探索局部结构
- 颜色条显示时间进度

**解读指南**:
- 点之间的距离: 状态相似度
- 轨迹方向: 系统演化方向
- 聚类分布: 稳定状态区域

---

### 4. 3D 聚类可视化 (3D Clustering)

**用途**: 三维视角观察状态聚类

**技术细节**:
- 使用 PCA 降维到 3D
- K-Means 聚类 (自动确定聚类数)
- 不同颜色表示不同聚类

**交互功能**:
- 旋转、缩放 3D 视图
- 悬停查看所属聚类和权重详情
- 图例切换显示/隐藏聚类

---

### 5. 时间轴回放 (Timeline Replay)

**用途**: 回放实验过程，观察动态变化

**控制按钮**:
- ▶ Play: 播放动画
- ⏸ Pause: 暂停动画
- 滑块: 手动控制进度

**视图组成**:
- 左侧Y轴: 权重时序
- 右侧Y轴: 当前状态柱状图

---

## 仪表板界面

### 布局说明

```
┌─────────────────────────────────────────────────────────┐
│         MOSS v6.1 Interactive Visualization             │
├────────────┬────────────┬───────────────────────────────┤
│ Experiment │ Drive List │ Controls                      │
│ Info       │            │ - Visualization Type Dropdown │
│ - Checkpts │ - Drive 1  │ - Export HTML Button          │
│ - Drives   │ - Drive 2  │                               │
│ - Cycles   │ - ...      │                               │
├────────────┴────────────┴───────────────────────────────┤
│                                                         │
│              Visualization Display Area                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 控制面板

**可视化类型选择**:
- Weight Timeline: 权重时序图
- Emergence Animation: 涌现动画
- PCA Visualization: PCA 可视化
- 3D Clustering: 3D聚类
- Timeline Replay: 时间轴回放

**导出功能**:
- 点击 "Export HTML" 导出当前可视化为 HTML 文件
- 导出文件保存在 `--output` 指定的目录

---

## 高级用法

### 编程接口

```python
from scripts.visualize_interactive import InteractiveVisualizer
from pathlib import Path

# 创建可视化器
viz = InteractiveVisualizer(Path('logs/experiment_v6_full_seed42'))

# 生成特定图表
fig = viz.create_weight_timeline()
fig.write_html('weight_timeline.html')

fig = viz.create_pca_visualization()
fig.show()

# 创建 Dash 仪表板
app = viz.create_dashboard()
app.run_server(port=8050)
```

### 自定义样式

```python
import plotly.graph_objects as go

# 获取基础图表
fig = viz.create_weight_timeline()

# 自定义样式
fig.update_layout(
    title=dict(text='Custom Title', font=dict(size=24, color='blue')),
    plot_bgcolor='rgba(240, 240, 240, 0.5)',
    paper_bgcolor='white',
    font=dict(family='Arial', size=12)
)

# 保存
fig.write_html('custom_visualization.html')
```

---

## 故障排除

### 常见问题

#### 1. 依赖缺失

**症状**: `ImportError: No module named 'plotly'`

**解决**:
```bash
pip install plotly dash scikit-learn
```

#### 2. 端口被占用

**症状**: `Address already in use`

**解决**:
```bash
# 使用其他端口
python scripts/visualize_interactive.py --port 8051
```

#### 3. 数据加载失败

**症状**: `未找到检查点`

**解决**:
- 确认实验目录路径正确
- 检查目录中是否包含 `checkpoint_*.json` 文件

#### 4. 浏览器无法访问

**症状**: 页面无法加载

**解决**:
- 确认防火墙允许端口访问
- 使用 `--host 0.0.0.0` 允许外部访问
- 检查控制台输出中的 URL

---

## 性能优化

### 大数据集处理

对于包含大量检查点的实验（>1000个）:

1. **采样显示**:
```python
# 在代码中修改采样间隔
self.checkpoints = self.checkpoints[::10]  # 每10个取1个
```

2. **静态导出**:
```bash
# 使用导出模式，避免服务器内存占用
python scripts/visualize_interactive.py --export-only
```

3. **禁用3D可视化**:
```python
# 如果不需要3D，可以跳过相关计算
# 修改 create_3d_clustering 中的 n_components=2
```

---

## 最佳实践

### 实验分析流程

1. **概览检查**: 使用 Weight Timeline 查看整体趋势
2. **涌现分析**: 使用 Emergence Animation 定位关键事件
3. **状态探索**: 使用 PCA Visualization 理解状态空间
4. **聚类验证**: 使用 3D Clustering 验证稳定性
5. **细节回放**: 使用 Timeline Replay 观察关键时刻

### 报告生成

```bash
# 1. 导出所有可视化
python scripts/visualize_interactive.py \
    --experiment-dir logs/experiment_v6_full_seed42 \
    --export-only \
    --output reports/visualization

# 2. 查看生成的 HTML 文件
ls reports/visualization/
# timeline.html, emergence.html, pca.html, cluster3d.html, replay.html
```

---

## 技术细节

### 技术栈

| 组件 | 用途 | 版本要求 |
|------|------|----------|
| Plotly | 交互式图表 | >=5.0 |
| Dash | Web 仪表板 | >=2.0 |
| scikit-learn | PCA/聚类 | >=1.0 |
| NumPy | 数值计算 | >=1.20 |

### 算法说明

**PCA 降维**:
- 输入: 标准化后的权重矩阵
- 输出: 2D/3D 坐标
- 解释方差比显示在图表标题

**K-Means 聚类**:
- 自动确定聚类数: `min(4, n_samples // 5 + 1)`
- 使用标准化特征
- 随机种子: 42

---

## 参考

### 相关文档

- [MOSS v6.1 发布说明](v6.1_RELEASE_NOTES.md)
- [可视化工具 API](../api/visualization.rst)
- [实验分析指南](experiment_analysis_guide.md)

### 示例数据

```bash
# 使用示例实验数据测试
python scripts/visualize_interactive.py \
    --experiment-dir logs/experiment_v6_full_seed42 \
    --port 8050
```

---

## 更新日志

### v6.1.0 (2026-04-18)

- ✨ 初始发布
- ✨ 支持 5 种可视化类型
- ✨ Dash 交互式仪表板
- ✨ HTML 导出功能

---

**维护者**: MOSS Team  
**问题反馈**: https://github.com/luokaishi/moss/issues
