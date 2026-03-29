# MVES 科学评估框架

**从"实验玩具"到"科学研究"的方法论**

---

## 1. 核心科学问题

### 主问题
> 在没有外部任务输入的情况下，系统能否自发产生：
> - 稳定策略
> - 工具使用
> - 环境操控
> - 长期行为模式

### 子问题
1. 演化是否需要外部选择压力？
2. 复杂性能否自发涌现？
3. 目标能否内生形成？
4. "智能"是否需要外部引导？

---

## 2. 可证伪性标准

### 2.1 证伪条件

实验被证伪，如果：

| 条件 | 阈值 | 测量 |
|------|------|------|
| **复杂度不增长** | 100 代后 < 2.0 | 工具 + 结构数量 |
| **行为收敛** | 熵 < 0.5 | 行动分布 |
| **无环境改变** | 结构数 = 0 | 环境 API |
| **群体灭绝** | 存活率 < 10% | 最终/初始 |
| **驱动单一** | 单一驱动 > 90% | 主导驱动分布 |

### 2.2 验证条件

实验成功，如果：

| 条件 | 阈值 | 测量 |
|------|------|------|
| **复杂度增长** | > 3.0 | 工具 + 结构 |
| **行为多样** | 熵 > 1.5 | Shannon 熵 |
| **环境改造** | 结构数 > 10 | 环境 API |
| **群体稳定** | 存活率 > 60% | 最终/初始 |
| **驱动分化** | 3 种驱动均存在 | 分布 |

---

## 3. 量化指标

### 3.1 结构复杂度

```python
complexity_score = (
    avg_tools * 1.0 +           # 工具数量
    avg_structures * 2.0 +      # 建筑数量
    code_depth * 0.5 +          # 代码深度
    memory_layers * 1.5         # 记忆层次
)
```

**阈值：**
- 低：< 2.0
- 中：2.0 - 5.0
- 高：> 5.0

### 3.2 行为熵

```python
def calculate_entropy(actions):
    # actions: 最近 100 次行动列表
    counts = Counter(actions)
    probs = [c / len(actions) for c in counts.values()]
    return -sum(p * log(p) for p in probs)
```

**阈值：**
- 收敛：< 0.5（单一行为）
- 多样：0.5 - 2.0
- 混乱：> 2.0

### 3.3 代际稳定性

```python
stability = (
    strategy_continuity * 0.4 +    # 策略传承
    tool_inheritance * 0.3 +       # 工具继承
    memory_retention * 0.3         # 记忆保留
)
```

### 3.4 环境改变

```python
env_change = (
    len(structures) * 1.0 +        # 建筑数量
    len(rule_changes) * 5.0 +      # 规则修改
    resource_variance * 0.1        # 资源分布变化
)
```

### 3.5 驱动分化

```python
drive_diversity = len(unique_dominant_drives) / 3.0
# 1.0 = 三种驱动均主导过
# 0.33 = 单一驱动主导
```

---

## 4. 实验设计

### 4.1 对照组设计

| 组别 | 驱动权重 | 群体大小 | 预期 |
|------|----------|----------|------|
| A | survival=0.7 | 10 | 高存活 |
| B | curiosity=0.7 | 10 | 高探索 |
| C | control=0.7 | 10 | 高建造 |
| D | 均衡 (0.33) | 10 | 基准 |
| E | 均衡 | 50 | 群体效应 |

### 4.2 变量控制

**固定变量：**
- 环境大小（20x20）
- 初始能量（100）
- 资源再生率（0.1）
- 最大代数（100）

**自变量：**
- 驱动权重
- 群体大小
- 变异率

**因变量：**
- 存活率
- 复杂度
- 行为熵
- 环境改变

### 4.3 统计检验

```python
# t-test 比较两组存活率
from scipy import stats
t_stat, p_val = stats.ttest_ind(group_A, group_B)

# 显著性：p < 0.05
```

---

## 5. 数据收集

### 5.1 检查点数据

```json
{
  "generation": 50,
  "population": [...],
  "environment": {...},
  "metrics": {
    "complexity_score": 2.5,
    "behavior_entropy": 1.2,
    "environment_change": 15
  }
}
```

### 5.2 日志解析

```python
def parse_log(log_file):
    metrics = []
    with open(log_file) as f:
        for line in f:
            if "Gen" in line:
                metrics.append(extract_metrics(line))
    return pd.DataFrame(metrics)
```

### 5.3 时间序列分析

```python
# 趋势检测
from scipy.stats import linregress

slope, intercept, r_value, p_value, std_err = linregress(
    generations, complexity_scores
)

# 显著增长：slope > 0, p < 0.05
```

---

## 6. 结果解释

### 6.1 阳性结果

如果观察到：
- 复杂度显著增长（p < 0.05）
- 行为熵维持 > 1.0
- 环境改变 > 10

**解释：** 系统具备自演化能力

### 6.2 阴性结果

如果观察到：
- 复杂度无增长
- 群体崩溃
- 驱动单一

**解释：** 需要校准参数或修改机制

### 6.3 混淆变量

注意：
- LLM 注入 ≠ 内生演化
- 随机波动 ≠ 趋势
- 过拟合参数 ≠ 普适规律

---

## 7. 可重复性

### 7.1 随机种子

```python
RANDOM_SEED = 42  # 固定种子
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
```

### 7.2 版本控制

- 代码版本：Git commit hash
- 配置版本：JSON 快照
- 数据版本：检查点编号

### 7.3 报告模板

```markdown
## 实验运行

- 日期：YYYY-MM-DD
- 版本：v4.0
- Commit: abc123
- 种子：42
- 配置：{...}

## 结果摘要

- 存活率：XX%
- 复杂度：X.X
- 熵：X.XX
```

---

## 8. 伦理考量

### 8.1 AI 安全

- 代码沙箱：禁止 os/system
- 资源限制：最大内存/CPU
- 终止开关：手动停止

### 8.2 数据透明

- 公开所有数据
- 公开失败实验
- 公开分析方法

### 8.3 结果谨慎

- 避免过度解读
- 区分"复杂"与"智能"
- 承认边界条件

---

## 9. 未来改进

### 9.1 指标优化

- [ ] 加入信息论指标
- [ ] 网络分析（agent 关系）
- [ ] 因果推断

### 9.2 实验规模

- [ ] 千代实验
- [ ] 千 agent 群体
- [ ] 多环境对比

### 9.3 理论整合

- [ ] 连接信息整合理论
- [ ] 自由能原理
- [ ] 主动推理框架

---

## 10. 结论

本框架提供：

✅ **可证伪标准** - 5 项清晰阈值  
✅ **量化指标** - 复杂度/熵/稳定性  
✅ **实验设计** - 对照组 + 变量控制  
✅ **统计方法** - 显著性检验  
✅ **可重复性** - 种子 + 版本 + 报告  

**从"想法"进入"科学"的门槛已跨越。**

---

**科学是允许失败的探索。** 🔬
