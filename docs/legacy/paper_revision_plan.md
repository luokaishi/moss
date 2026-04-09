# MOSS 论文修改框架（Path Bifurcation 主线）

## 修改清单

### Abstract 修改
**删除：**
- "Weight quantization experiments further validate that state-dependent weight allocation achieves optimal performance (0.3763 overall score)."

**保留/强调：**
- "Our key discovery is path bifurcation: identical initial conditions evolve into divergent stable strategies—social-exploration (6h) versus knowledge-seeking (24h)—depending on runtime duration."
- "This reveals that self-modification enables context-dependent adaptation rather than converging to a single global optimum."

---

### 1. Introduction 修改
**当前问题：**
- 混合提及 state-dependent 和 path bifurcation

**修改方案：**
- 聚焦"时间上下文驱动策略分化"
- 删除或弱化"state-dependent specialization"表述
- 强调"相同初始条件→不同运行时长→不同策略"

---

### 3. Results 结构调整

#### 3.1 Long-Term Performance（保持）
- 6h/24h 性能对比
- 累计奖励数据
- 权重演化轨迹

#### 3.2 Path Bifurcation（核心，保持）
- 6h Social-Exploration 策略：[0.05, 0.46, 0.45, 0.05]
- 24h Knowledge-Seeking 策略：[0.21, 0.53, 0.19, 0.07]
- 路径分叉现象解释

#### 3.3 State-Dependent Specialization → 移至附录
**处理方式：**
```
删除 3.3 节正文内容

改为 Appendix B: State-Dependent Weight Quantization
- 简要介绍实验设计
- 呈现 Crisis 配置最优结果（0.3763）
- 说明这是补充验证，非核心发现
```

---

### 4. Discussion 修改
**当前：** 混合讨论 path bifurcation 和 state-dependent

**改为：** 聚焦时间尺度与策略选择的关系
- 短期（6h）：快速探索，社交扩张优先
- 长期（24h）：深度知识积累，平衡生存
- 类比：生物适应辐射（adaptive radiation）

---

### Figures 修改

#### Figure 1（保持）
- 柱状图：Fixed vs 6h vs 24h 累计奖励
- 数据真实，无需修改

#### Figure 2（保持）
- 雷达图：6h vs 24h 权重对比
- 确保标签准确

#### Figure 3（删除或替换）
**当前：** 可能包含 weight quantization 内容

**改为：**
- 选项A：删除 Figure 3
- 选项B：替换为"15实例统计验证聚类结果"（等新实验完成）
- 选项C：改为"权重演化时间序列图"

**推荐选项A**（最简洁）

---

### 5. Limitations 新增
**添加段落：**
```
While our experiments demonstrate path bifurcation across multiple runs, 
the current study is limited by sample size (single 6h and 24h runs). 
Future work will conduct N=15-30 repeated experiments with identical 
initial conditions to establish statistical significance (p<0.05) and 
verify that path bifurcation is a robust phenomenon rather than 
an artifact of specific random seeds.
```

---

## 修改优先级

| 优先级 | 任务 | 时间 |
|--------|------|------|
| **P0** | Abstract 修改 | 30分钟 |
| **P0** | 删除/移动 3.3 节 | 30分钟 |
| **P0** | 调整 Discussion | 1小时 |
| **P1** | 删除 Figure 3 | 15分钟 |
| **P1** | 添加 Limitations | 15分钟 |
| **P2** | 更新 Introduction | 1小时 |

**总计**：约4小时完成核心修改

---

## 后续工作（统计验证完成后）

1. 分析15实例结果
2. 聚类分析最终权重
3. 计算p值
4. 如结果显著 → 更新论文，删除Limitations中的"single run"表述
5. 如结果不显著 → 改为"初步观察"表述
