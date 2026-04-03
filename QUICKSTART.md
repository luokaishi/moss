# MVES 快速开始指南

**版本**: v6.2.0  
**更新时间**: 2026-04-03

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 克隆仓库
git clone https://github.com/luokaishi/moss.git
cd moss

# 安装依赖
pip install -r requirements.txt
```

### 2. 基本使用

```python
from core.collaboration import CollaborationCoordinator

# 创建协作协调器
coordinator = CollaborationCoordinator()

# 注册 Agent
coordinator.register_agent("agent_1", {"coding": 0.9, "analysis": 0.8})

# 添加任务
from core.collaboration import Task
task = Task(
    id="task_1",
    description="Implement feature",
    difficulty=0.5,
    priority=0.8,
    required_skills=["coding"]
)
coordinator.add_task(task)

# 分配任务
assignments = coordinator.assign_tasks()
```

### 3. 运行实验

```bash
# 100 Agent 协作实验
python experiments/collab_100agents.py --agents 100 --iterations 100

# 性能基准测试
python experiments/benchmark_v6.1.py

# 168h 压力测试 (模拟)
python experiments/stress_test_168h.py --iterations 100
```

---

## 📚 核心模块

### 协作模块

- `core/collaboration.py` - 协作协调器
- `core/communication.py` - 通信协议
- `core/open_environment.py` - 开放环境

### 性能模块

- `core/performance_optimizer.py` - 性能优化器
- `core/concurrent_executor.py` - 并发执行器
- `core/memory_manager.py` - 内存管理器

### 意识模块

- `core/self_awareness.py` - 自我意识
- `core/meta_cognition.py` - 元认知
- `core/self_reflection.py` - 自我反思

---

## 🧪 实验脚本

| 实验 | 命令 | 说明 |
|------|------|------|
| 100 Agent 协作 | `python experiments/collab_100agents.py` | 多 Agent 协作 |
| 1000 Agent 协作 | `python experiments/collab_1000agents.py` | 大规模协作 |
| 168h 压力测试 | `python experiments/stress_test_168h.py` | 稳定性测试 |
| 性能基准 | `python experiments/benchmark_v6.1.py` | 性能测试 |

---

## 📖 文档

- [API 参考](docs/api_reference.md)
- [使用教程](docs/tutorials/)
- [FAQ](docs/faq.md)
- [贡献指南](CONTRIBUTING.md)

---

## 🔗 相关链接

- **GitHub**: https://github.com/luokaishi/moss
- **Releases**: https://github.com/luokaishi/moss/releases
- **Issues**: https://github.com/luokaishi/moss/issues

---

*最后更新：2026-04-03*
