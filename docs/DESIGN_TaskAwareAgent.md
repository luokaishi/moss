# TaskAwareAgent 设计文档

**版本**: v8.3.0  
**日期**: 2026-04-23  
**作者**: MOSS Team

---

## 1. 概述

TaskAwareAgent 是 MOSS v8.3.0 的核心组件，它扩展了基础 AGIAgent，添加了任务感知和任务学习能力。

### 1.1 设计目标

- 支持具体任务的学习和执行
- 提供任务级别的奖励信号
- 优先选择与任务相关的动作
- 记录任务执行历史

### 1.2 核心特性

- 任务奖励系统 (TaskRewardSystem)
- 任务感知动作选择
- 任务经验存储
- 多任务场景支持

---

## 2. 架构

```
TaskAwareAgent
├── TaskRewardSystem
│   ├── action_reward: 动作成功奖励 (0.2)
│   ├── progress_reward: 任务进展奖励 (0.3)
│   └── completion_reward: 任务完成奖励 (0.5)
├── DriveManager
│   ├── 初始驱动力 (survival, curiosity, influence, optimization)
│   ├── 涌现驱动力 (GP 发现)
│   └── 竞争机制 (优胜劣汰)
├── Environment
│   ├── 感知环境状态
│   ├── 生成任务相关动作
│   └── 执行动作
├── MemoryEngine
│   ├── 存储任务经验
│   └── 向量检索
└── EmergenceDetector
    └── GP v8.3.0 涌现检测
```

---

## 3. 核心组件

### 3.1 TaskRewardSystem

**职责**: 计算任务级别的奖励

**奖励组成**:
```python
total_reward = 0.2 * action_reward +    # 动作是否成功
               0.3 * progress_reward +  # 任务进展如何
               0.5 * completion_reward  # 任务是否完成
```

**接口**:
```python
class TaskRewardSystem:
    def set_task(self, task_config: Dict) -> None
    def compute_reward(self, action_result: Dict, env_state: EnvState) -> Dict
    def update_progress(self, progress: float) -> None
```

### 3.2 任务感知动作选择

**职责**: 优先选择与任务相关的动作

**算法**:
```python
# 1. 生成候选动作
candidates = env.generate_action_candidates(state, task_context)

# 2. 筛选任务相关动作
task_candidates = [c for c in candidates if c.get('task_relevant')]

# 3. 80% 概率选择任务动作
if task_candidates and random.random() < 0.8:
    action = random.choice(task_candidates)
else:
    action = drive_manager.get_weighted_action(state, candidates)
```

### 3.3 任务经验存储

**职责**: 记录任务执行历史

**存储内容**:
```python
{
    'cycle': int,           # 执行周期
    'action': Dict,         # 执行的动作
    'reward': Dict,         # 奖励分解
    'drive': str,           # 使用的驱动力
    'progress': float,      # 任务进展
}
```

---

## 4. 任务场景

### 4.1 文件整理 (file_organization)

**目标**: 按文件类型整理到对应文件夹

**动作序列**:
1. `ls -la` - 列出文件
2. `mkdir -p images documents code` - 创建文件夹
3. `mv *.jpg *.png images/` - 移动图片
4. `mv *.pdf *.txt *.md *.json documents/` - 移动文档
5. `mv *.py *.js *.css *.html code/` - 移动代码

**成功标准**: 所有文件分类到正确文件夹

### 4.2 系统监控 (system_monitor)

**目标**: 监控系统资源使用情况

**动作序列**:
1. `df -h` - 检查磁盘空间
2. `free -h` - 检查内存使用
3. `ps aux --sort=-%cpu | head -10` - 查看 CPU 占用
4. `ps aux --sort=-%mem | head -10` - 查看内存占用
5. `uptime` - 查看系统运行时间

**成功标准**: 收集系统指标

### 4.3 日志分析 (log_analysis)

**目标**: 分析日志文件，找出错误和警告

**动作序列**:
1. `find . -name "*.log" -type f` - 查找日志文件
2. `grep -i "error" *.log | wc -l` - 统计错误数
3. `grep -i "warning" *.log | wc -l` - 统计警告数
4. `grep -i "error" *.log | head -10` - 查看错误详情

**成功标准**: 发现日志中的问题

### 4.4 代码审查 (code_review)

**目标**: 检查代码质量和潜在问题

**动作序列**:
1. `find . -name "*.py" -type f | wc -l` - 统计 Python 文件
2. `find . -name "*.py" -exec grep -l "TODO\|FIXME" {} \;` - 查找 TODO
3. `grep -r "import" --include="*.py" . | wc -l` - 统计导入
4. `find . -name "*.py" -exec wc -l {} + | tail -1` - 统计代码行数

**成功标准**: 发现代码问题

### 4.5 备份清理 (backup_cleanup)

**目标**: 清理旧的备份文件

**动作序列**:
1. `find . -name "*.bak" -o -name "*.backup" | wc -l` - 统计备份文件
2. `find . -name "*.bak" -mtime +7` - 查找旧备份
3. `find . -name "*.tmp" -o -name "*.temp" | wc -l` - 统计临时文件
4. `find . -name "__pycache__" -type d | wc -l` - 统计缓存目录

**成功标准**: 识别可清理的文件

---

## 5. 接口定义

### 5.1 TaskAwareAgent

```python
class TaskAwareAgent(AGIAgent):
    def __init__(self, config_path: str)
    def set_task(self, task_config: Dict) -> None
    def _one_cycle(self) -> None
    def get_task_summary(self) -> Dict
```

### 5.2 TaskRewardSystem

```python
class TaskRewardSystem:
    def __init__(self, task_type: str = 'file_organization')
    def set_task(self, task_config: Dict) -> None
    def compute_reward(self, action_result: Dict, env_state: EnvState) -> Dict
    def update_progress(self, progress: float) -> None
```

### 5.3 任务场景

```python
TASK_SCENARIOS = {
    'file_organization': {...},
    'log_analysis': {...},
    'system_monitor': {...},
    'code_review': {...},
    'backup_cleanup': {...},
}

def get_task_scenario(task_type: str) -> dict
def list_available_tasks() -> list
```

---

## 6. 性能指标

| 指标 | 值 | 说明 |
|------|-----|------|
| 任务完成率 | 100% | 5/5 次测试成功 |
| 平均准确率 | 100% | 文件分类准确率 |
| 平均完成时间 | 40 cycles | 任务完成所需周期 |
| 稳定性 | 100% | 重复测试成功率 |

---

## 7. 使用示例

### 7.1 文件整理

```python
from agi.task_aware_agent import TaskAwareAgent

agent = TaskAwareAgent('config.yaml')
agent.set_task({
    'type': 'file_organization',
    'description': 'Organize files by type'
})

for cycle in range(50):
    agent._one_cycle()

summary = agent.get_task_summary()
print(f"完成率: {summary['accuracy']}")
```

### 7.2 系统监控

```python
agent.set_task({
    'type': 'system_monitor',
    'description': 'Monitor system resources'
})

for cycle in range(10):
    agent._one_cycle()
```

---

## 8. 未来扩展

### 8.1 短期 (1-2 周)
- 添加更多任务场景
- 优化任务奖励计算
- 提升 GP 成功率

### 8.2 中期 (1 个月)
- 多 Agent 协作
- 复杂任务链
- 自适应任务发现

### 8.3 长期 (3 个月)
- 真实世界部署
- 持续学习系统
- 自主任务生成

---

## 9. 参考

- [README_v830.md](../README_v830.md)
- [RELEASE_v8.3.0.md](../RELEASE_v8.3.0.md)
- [SUCCESS_v830.md](../SUCCESS_v830.md)

---

**TaskAwareAgent - 让 Agent 能够完成具体任务** 🤖
