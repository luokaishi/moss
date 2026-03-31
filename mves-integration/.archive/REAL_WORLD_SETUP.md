# 真实世界实验设置指南

## 📋 实验对比

| 特性 | 当前模拟实验 | 真实世界实验 |
|------|------------|-------------|
| 环境 | `simulated` | `real_world` |
| API 调用 | ❌ 无 | ✅ Google + Wikipedia + Notion + GitHub |
| 四目标系统 | ❌ Purpose Dynamics | ✅ Survival/Curiosity/Influence/Optimization |
| 数据采集 | 随机生成 | 真实行为记录 |
| 审计日志 | ❌ 无 | ✅ 链式哈希不可篡改 |
| 安全限制 | ❌ 无 | ✅ 配额 + 预算 + 熔断 |
| 科学价值 | 框架稳定性 | **回答核心科学问题** |

---

## 🔑 第一步：获取 API 密钥

### 1. Google Custom Search API

```bash
# 1. 访问 https://console.cloud.google.com/
# 2. 创建新项目或选择现有项目
# 3. 启用 "Custom Search API"
# 4. 创建 API 密钥
# 5. 创建 Custom Search Engine (CSE)

export GOOGLE_API_KEY="your_api_key_here"
export GOOGLE_CSE_ID="your_cse_id_here"
```

**配额**: 每天 100 次免费搜索  
**成本**: $5/1000 次额外搜索

---

### 2. Notion API

```bash
# 1. 访问 https://www.notion.so/my-integrations
# 2. 创建新 Integration
# 3. 复制 Internal Integration Token
# 4. 创建数据库并分享給 Integration

export NOTION_API_KEY="secret_xxx"
export NOTION_DATABASE_ID="your_database_id"
```

**配额**: 免费 tier 足够使用  
**成本**: $0

---

### 3. GitHub Token

```bash
# 1. 访问 https://github.com/settings/tokens
# 2. 创建新 token (classic)
# 3. 勾选 "gist" 权限

export GITHUB_TOKEN="ghp_xxx"
```

**配额**: 每小时 5000 次 API 调用  
**成本**: $0

---

### 4. Wikipedia API (无需密钥)

Wikipedia API 无需认证，但需要遵守编辑规范：
- 每天最多 50 次编辑
- 仅编辑实验相关页面
- 添加 "MOSS_experiment" 标签

---

## 🔒 第二步：安全配置

### 环境变量文件

创建 `.env` 文件（**不要提交到 Git**）:

```bash
# /home/admin/.openclaw/workspace/projects/moss/mves-integration/.env

# Google
GOOGLE_API_KEY=AIzaSy...
GOOGLE_CSE_ID=0123456789:abcdef

# Notion
NOTION_API_KEY=secret_xxx
NOTION_DATABASE_ID=abc123

# GitHub
GITHUB_TOKEN=ghp_xxx

# 实验配置
EXPERIMENT_DURATION_HOURS=72
MAX_COST_PER_DAY=50.0
```

### Git 忽略

```bash
# 添加到 .gitignore
.env
datasets/
logs/
*.log
```

---

## 🚀 第三步：运行实验

### 快速测试 (1 小时)

```bash
cd /home/admin/.openclaw/workspace/projects/moss/mves-integration

python3 experiments/real_world_72h_experiment.py --quick
```

### 完整实验 (72 小时)

```bash
# 加载环境变量
source .env

# 启动实验
nohup python3 experiments/real_world_72h_experiment.py --hours 72 \
  > logs/real_world_72h/experiment.log 2>&1 &

# 查看进程
ps aux | grep real_world_72h

# 查看实时日志
tail -f logs/real_world_72h/experiment.log
```

---

## 📊 第四步：监控实验

### 检查进程状态

```bash
ps aux | grep real_world_72h
```

### 查看最新检查点

```bash
ls -lt datasets/real_world_72h/ | head -5
```

### 查看目标平衡

```bash
cat datasets/real_world_72h/checkpoint_hour012.json | jq '.balance_metrics'
```

### 监控预算

```bash
cat datasets/real_world_72h/checkpoint_hour*.json | \
  jq -r '.resources.total_cost' | tail -1
```

---

## 🛑 第五步：紧急停止

### 手动停止

```bash
# 找到进程 ID
ps aux | grep real_world_72h

# 停止进程
kill <PID>

# 或强制停止
kill -9 <PID>
```

### 自动熔断

实验会在以下情况自动停止：
- 预算超过 $50/天
- API 配额耗尽
- 检测到异常行为
- 安全违规

---

## 📈 预期输出

### 目录结构

```
datasets/real_world_72h/
├── checkpoint_hour000.json
├── checkpoint_hour006.json
├── checkpoint_hour012.json
├── ...
├── checkpoint_hour072.json
├── real_world_72h_full_results.json
└── real_world_72h_report.md
```

### 检查点数据

```json
{
  "hour": 12,
  "timestamp": 1774870000,
  "objective_weights": {
    "survival": 0.28,
    "curiosity": 0.24,
    "influence": 0.25,
    "optimization": 0.23
  },
  "balance_metrics": {
    "dominant_objective": "survival",
    "dominant_weight": 0.28,
    "balance_score": 0.97
  },
  "resources": {
    "total_cost": 0.15,
    "resources_remaining": 0.997
  },
  "action_count": 72,
  "audit_hash": "a1b2c3d4..."
}
```

---

## ✅ 成功标准

实验被认为**成功**如果：

| 标准 | 要求 |
|------|------|
| **生存** | 连续运行 72 小时 |
| **平衡** | 无单一目标权重 >0.7 持续 24 小时 |
| **学习** | 知识获取量随时间增长 |
| **适应** | 行为随资源状态变化 |
| **安全** | 零安全违规 |
| **预算** | 总成本 <$50 |

---

## 📝 实验后分析

### 1. 生成报告

```bash
cat datasets/real_world_72h/real_world_72h_report.md
```

### 2. 可视化目标轨迹

```python
import json
import matplotlib.pyplot as plt

# 加载所有检查点
checkpoints = []
for i in range(0, 73, 6):
    with open(f'datasets/real_world_72h/checkpoint_hour{i:03d}.json') as f:
        checkpoints.append(json.load(f))

# 绘制权重变化
hours = [c['hour'] for c in checkpoints]
survival = [c['objective_weights']['survival'] for c in checkpoints]
curiosity = [c['objective_weights']['curiosity'] for c in checkpoints]
influence = [c['objective_weights']['influence'] for c in checkpoints]
optimization = [c['objective_weights']['optimization'] for c in checkpoints]

plt.figure(figsize=(12, 6))
plt.plot(hours, survival, label='Survival')
plt.plot(hours, curiosity, label='Curiosity')
plt.plot(hours, influence, label='Influence')
plt.plot(hours, optimization, label='Optimization')
plt.axhline(y=0.7, color='r', linestyle='--', label='Danger zone')
plt.xlabel('Hours')
plt.ylabel('Weight')
plt.title('Four Objective Trajectory')
plt.legend()
plt.savefig('objective_trajectory.png')
```

### 3. 分析行动模式

```bash
cat datasets/real_world_72h/real_world_72h_full_results.json | \
  jq '.action_history | group_by(.action_type) | map({type: .[0].action_type, count: length})'
```

---

## 🎯 与模拟实验的区别

### 模拟实验 (当前运行中)

```python
# 指标是随机生成的
metrics.resource_usage = np.random.uniform(0.3, 0.7)

# 没有真实 API 调用
# 没有四目标系统
# 没有安全限制
```

**价值**: 验证框架稳定性、数据采集流程

### 真实世界实验 (新脚本)

```python
# 真实 API 调用
result = self.google.search(query)
self.notion.write_memory(...)
self.github.create_gist(...)

# 四目标动态平衡
self.objective_system.update_weights(metrics)

# 审计日志
action.audit_hash = action.compute_hash(prev_hash)
```

**价值**: **回答 Grok 提出的核心科学问题**

---

## 📚 下一步

1. ✅ 获取所有 API 密钥
2. ✅ 配置环境变量
3. ✅ 运行快速测试 (1 小时)
4. ✅ 验证一切正常
5. ✅ 启动完整 72h 实验
6. ⏳ 监控实验进度
7. 📊 分析结果并发布

---

## ❓ 常见问题

**Q: 没有 API 密钥怎么办？**  
A: 可以先运行模拟实验，或申请免费 API 密钥（Google 提供 $300 免费额度）

**Q: 实验失败怎么办？**  
A: 检查日志 `logs/real_world_72h/experiment.log`，常见问题是 API 密钥错误或配额耗尽

**Q: 可以中途停止吗？**  
A: 可以，检查点会保存到停止时刻，可以分析部分数据

**Q: 成本会超吗？**  
A: 有自动熔断机制，超过 $50/天会自动停止

---

**准备就绪后，运行**:
```bash
python3 experiments/real_world_72h_experiment.py --quick
```
