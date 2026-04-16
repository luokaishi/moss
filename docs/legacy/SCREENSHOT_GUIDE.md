# MOSS关键画面截图指南

## Dashboard截图清单

### 截图1: Dashboard主页全景
**URL**: http://localhost:5000  
**时机**: 实验运行中（显示实时数据）  
**内容**:
- 顶部: MOSS Logo + 状态指示器
- 中部: 四目标得分实时曲线
- 底部: 权重分布图 + 系统指标

**操作**:
```bash
cd /workspace/projects/moss
make web-monitor
# 浏览器打开 http://localhost:5000
```

---

### 截图2: 四目标得分曲线
**重点**: 显示6+小时的历史曲线  
**数据点**:
- Survival: ~0.95 (缓慢下降)
- Curiosity: ~0.06 (开始上升)
- Influence: ~0.06 (开始上升)
- Optimization: 0.5 (稳定)

**说明**: 证明四目标同时存在，无退化

---

### 截图3: 系统状态面板
**显示**:
- Current State: "Normal" (绿色)
- Resource Ratio: 94.82%
- Elapsed: 6h 00m
- Tokens Used: 2,590 / 50,000
- Knowledge Count: 6

---

### 截图4: 权重分布可视化
**显示**: 饼图/条形图
- Curiosity: 40%
- Survival: 20%
- Influence: 30%
- Optimization: 10%

---

## Terminal截图清单

### 截图5: 实验启动画面
**命令**:
```bash
ps aux | grep moss_72h_experiment
tail -20 moss_72h_experiment.log
```

**关键信息**:
```
2026-03-10 14:25:46,289 - INFO - STARTING MOSS 72-HOUR EXPERIMENT
2026-03-10 14:25:46,290 - INFO - Duration: 72 hours
2026-03-10 14:25:46,290 - INFO - Token budget: 50000
```

---

### 截图6: 检查点保存记录
**命令**:
```bash
ls -lh checkpoint_*.json
cat checkpoint_20260310_202546.json | jq '.elapsed_hours, .tokens_used, .knowledge_acquired'
```

**显示**:
```
elapsed_hours: 6.0
tokens_used: 2590
knowledge_acquired: 6
```

---

## GitHub实验结果截图

### 截图7: GitHub API实验输出
**文件**: experiments/real_github_simple.py运行结果  
**关键信息**:
```
[1/5] Searching: machine learning stars:>1000
  ✅ Found 536 repositories
     • josephmisiti/awesome-machine-learning
       71925 stars
```

---

### 截图8: 实验结果JSON
**文件**: real_github_results_20260310_205951.json  
**高亮**:
```json
{
  "total_queries": 5,
  "successful_queries": 5,
  "total_repos_found": 42189,
  "total_stars_top_repos": 164927
}
```

---

## 代码/文档截图

### 截图9: README v0.3.0头部
**URL**: https://github.com/luokaishi/moss  
**显示**:
- MOSS标题
- 徽章: v0.3.0, MIT License, Python 3.8+
- 核心描述

---

### 截图10: 项目结构
**命令**:
```bash
tree -L 2 -I '__pycache__|*.pyc'
```

**显示**:
```
moss/
├── agents/
├── core/
│   ├── objectives.py
│   ├── gradient_safety_guard.py
│   ├── conflict_resolver_enhanced.py
│   ├── self_optimization_v2.py
│   └── ...
├── experiments/
└── docs/
```

---

### 截图11: 最近提交历史
**命令**:
```bash
git log --oneline -10
```

**显示**:
```
11b9746 feat: Complete first real-world API experiment with GitHub
e5a1de1 feat: Complete baseline comparison experiment
7268498 feat: Complete data-driven state decision model
...
```

---

## Baseline对比截图

### 截图12: 对比结果表格
**来源**: docs/BASELINE_COMPARISON_REPORT.md  
**表格**:
```
| Method   | Avg Reward | Success Rate | Knowledge |
|----------|-----------|--------------|-----------|
| MOSS     | 11.25     | 100.0%       | 4.5       |
| ReAct    | 11.34     | 50.0%        | 5.1       |
| Reflexion| 11.43     | 100.0%       | 3.4       |
| Voyager  | 11.49     | 100.0%       | 1.9       |
```

**高亮**: MOSS的100%成功率和平衡的知识获取

---

## 外部评估截图

### 截图13: 评估汇总
**来源**: docs/EXTERNAL_EVALUATIONS_COMPREHENSIVE_REPORT.md  
**显示**:
- 8份评估来源列表
- 共识问题表格
- 解决状态

---

## 安全机制截图

### 截图14: 5级安全架构
**来源**: core/gradient_safety_guard.py注释  
**显示**:
```python
Level 1 - Warning: Log and notify
Level 2 - Throttling: Reduce action rate 50%
Level 3 - Pause: Pause all actions
Level 4 - Rollback: Rollback to checkpoint
Level 5 - Terminate: Emergency shutdown
```

---

## 72小时完成后的必截图（3月13日）

### 最终截图清单

1. **Dashboard 72小时全景**
   - 完整四目标曲线
   - 最终统计数据

2. **四目标最终得分**
   - Survival: ?
   - Curiosity: ?
   - Influence: ?
   - Optimization: ?

3. **Token消耗曲线**
   - 展示预算管理效果

4. **知识获取增长曲线**
   - 从0到最终数量

5. **权重变化热力图**
   - 72小时内权重如何动态调整

6. **状态转换时间线**
   - Normal/Crisis/Growth状态变化

---

## 截图工具推荐

### macOS
- **CleanShot X**: 专业截图 + 标注
- **Snagit**: 录屏 + 截图
- **Cmd+Shift+4**: 系统自带

### Linux
- **Flameshot**: 开源截图工具
- **Shutter**: 功能丰富
- **gnome-screenshot**: 系统自带

### Windows
- **Snip & Sketch**: 系统自带
- **ShareX**: 开源强大
- **Greenshot**: 轻量好用

---

## 截图命名规范

```
moss_dashboard_main_20260310.png
moss_dashboard_objectives_20260310.png
moss_terminal_start_20260310.png
moss_github_experiment_20260310.png
moss_baseline_comparison_20260310.png
moss_readme_header_20260310.png
```

---

## 截图存储位置

```
/workspace/projects/moss/assets/screenshots/
├── dashboard/
├── terminal/
├── experiments/
└── docs/
```

---

**准备就绪！72小时完成后立即拍摄最终截图。**
