# MOSS 项目文档索引

**版本**: v8.6.0  
**日期**: 2026-04-24  
**状态**: 生产级可用

---

## 📚 快速导航

### 🚀 新用户入门
1. [README.md](README.md) - 项目简介和快速开始
2. [RELEASE_v8.6.0.md](RELEASE_v8.6.0.md) - 最新版本发布说明
3. [ROADMAP_v8.6.0.md](ROADMAP_v8.6.0.md) - 开发路线图

### 📖 核心文档

#### 版本发布
| 版本 | 文档 | 核心特性 |
|------|------|----------|
| v8.6.0 | [RELEASE_v8.6.0.md](RELEASE_v8.6.0.md) | 72小时实验、事件驱动、监控仪表盘、自动恢复 |
| v8.5.0 | [RELEASE_v8.5.0.md](RELEASE_v8.5.0.md) | 真实世界耦合、100gen实验、跨任务泛化、5Agent群体演化 |
| v8.4.0 | [RELEASE_v8.4.0.md](RELEASE_v8.4.0.md) | 自适应任务发现、多Agent协作、GP优化 |
| v8.3.0 | [RELEASE_v8.3.0.md](RELEASE_v8.3.0.md) | Task-Aware Agent、10种任务场景 |

#### 路线图
| 版本 | 文档 | 目标 |
|------|------|------|
| v8.6.0 | [ROADMAP_v8.6.0.md](ROADMAP_v8.6.0.md) | 生产级可用性 |
| v8.5.0 | [ROADMAP_v8.5.0.md](ROADMAP_v8.5.0.md) | 真实世界演化 |
| v8.4.0 | [ROADMAP_v8.4.0.md](ROADMAP_v8.4.0.md) | 多Agent协作 |
| v8.3.0 | [ROADMAP_v8.3.0.md](ROADMAP_v8.3.0.md) | 任务感知Agent |

### 🔬 实验报告

#### 统计验证
| 实验 | 文档 | 样本量 | 关键结果 |
|------|------|--------|----------|
| N=45 Meta-SME | [N45_META_SME_REPORT.md](N45_META_SME_REPORT.md) | N=45 | 统计显著性验证 |
| N=30 百炼真实LLM | [N30_SUCCESS_20260422.md](N30_SUCCESS_20260422.md) | N=30 | p < 0.0001, Cohen's d = 3.112 |
| 100代长期稳定性 | [LONGTERM_100GEN_REPORT_20260422.md](LONGTERM_100GEN_REPORT_20260422.md) | 100 Gen | 长期优势保持 |
| 多模型对比 | [MULTI_MODEL_REPORT_20260422.md](MULTI_MODEL_REPORT_20260422.md) | 2模型 | kimi-k2.5 > qwen3.5-plus |
| GP v8.4.0 | [GP_V840_RESULTS.md](GP_V840_RESULTS.md) | N=20 | 成功率70%, 增益+16% |

#### 专项实验
| 实验 | 文档 | 描述 |
|------|------|------|
| 72小时长期实验 | [experiments/72h_longterm_experiment.py](experiments/72h_longterm_experiment.py) | 生产级稳定性验证 |
| 跨任务泛化 | [experiments/cross_task_experiment.py](experiments/cross_task_experiment.py) | E3-E5实验 |
| 群体演化 | [experiments/population_evolution_experiment.py](experiments/population_evolution_experiment.py) | 5Agent协作 |
| 端到端测试 | [experiments/phase4_end_to_end_test.py](experiments/phase4_end_to_end_test.py) | 任务完成率验证 |

### 🏗️ 架构文档

#### 核心模块
| 模块 | 文件 | 功能 |
|------|------|------|
| Task-Aware Agent | [agi/task_aware_agent.py](agi/task_aware_agent.py) | 任务感知Agent |
| 遗传编程 | [agi/genetic_programmer.py](agi/genetic_programmer.py) | GP优化 |
| 真实世界桥接 | [agi/mves_realworld_bridge.py](agi/mves_realworld_bridge.py) | 环境感知 |
| 任务发现 | [agi/task_discovery.py](agi/task_discovery.py) | 自适应任务发现 |
| 多Agent协调 | [agi/multi_agent_coordinator.py](agi/multi_agent_coordinator.py) | 多Agent协作 |
| 事件驱动Purpose | [agi/event_driven_purpose.py](agi/event_driven_purpose.py) | 事件响应 |
| 监控仪表盘 | [agi/monitoring_dashboard.py](agi/monitoring_dashboard.py) | 实时监控 |
| 自动恢复 | [agi/auto_recovery.py](agi/auto_recovery.py) | 故障自愈 |

#### 任务场景
| 场景 | 文件 | 描述 |
|------|------|------|
| 任务定义 | [agi/task_scenarios.py](agi/task_scenarios.py) | 10种任务场景定义 |
| 文件整理 | `task_type='file_organization'` | 自动文件分类 |
| 系统监控 | `task_type='system_monitor'` | 资源监控 |
| 日志分析 | `task_type='log_analysis'` | 日志处理 |
| 代码审查 | `task_type='code_review'` | 代码检查 |
| 备份清理 | `task_type='backup_cleanup'` | 备份管理 |
| 网络诊断 | `task_type='network_diagnosis'` | 网络检测 |
| 依赖分析 | `task_type='dependency_analysis'` | 依赖检查 |
| 安全扫描 | `task_type='security_scan'` | 安全检查 |
| 性能测试 | `task_type='performance_test'` | 性能评估 |
| 文档生成 | `task_type='documentation_gen'` | 文档创建 |

### 📊 测试结果

#### 性能指标
| 指标 | 值 | 文档 |
|------|-----|------|
| 任务完成率 | 100% | [PHASE4_COMPLETE.md](PHASE4_COMPLETE.md) |
| GP成功率 | 70% | [GP_V840_RESULTS.md](GP_V840_RESULTS.md) |
| 平均增益 | 0.583 | [GP_V840_RESULTS.md](GP_V840_RESULTS.md) |
| 72小时运行 | 进行中 | [experiments/72h_longterm_experiment.py](experiments/72h_longterm_experiment.py) |

### 🔧 配置和工具

| 文件 | 用途 |
|------|------|
| [config/agent_config.yaml](config/agent_config.yaml) | Agent配置 |
| [check_72h_status.sh](check_72h_status.sh) | 实验状态检查 |
| [monitor_72h_experiment.py](monitor_72h_experiment.py) | 实验监控 |
| [alert_config.yaml](alert_config.yaml) | 告警配置 |

### 📈 项目总结

| 文档 | 描述 |
|------|------|
| [FINAL_v830.md](FINAL_v830.md) | v8.3.0最终成果 |
| [FINAL_SUMMARY.md](FINAL_SUMMARY.md) | v8.0.0项目总结 |
| [MOSS_v830_UNIFIED.md](MOSS_v830_UNIFIED.md) | v8.3.0统一文档 |
| [SUCCESS_v830.md](SUCCESS_v830.md) | v8.3.0成功报告 |
| [TEST_RESULTS.md](TEST_RESULTS.md) | 测试结果汇总 |

---

## 🎯 使用场景

### 场景1: 快速体验MOSS
```bash
# 1. 查看README
 cat README.md

# 2. 运行演示
 python3 demo_v830.py
```

### 场景2: 使用Task-Aware Agent
```python
from agi.task_aware_agent import TaskAwareAgent

agent = TaskAwareAgent('config.yaml')
agent.set_task({
    'type': 'file_organization',
    'description': '整理下载文件夹'
})
```

### 场景3: 运行72小时实验
```bash
# 启动实验
 nohup python3 experiments/72h_longterm_experiment.py --full &

# 检查状态
 ./check_72h_status.sh
```

### 场景4: 多Agent协作
```python
from agi.multi_agent_coordinator import MultiAgentCoordinator

coordinator = MultiAgentCoordinator()
coordinator.register_agent(agent_id, capabilities)
coordinator.submit_task(task_type, priority)
```

---

## 📞 获取帮助

- **GitHub**: https://github.com/luokaishi/moss
- **Issues**: https://github.com/luokaishi/moss/issues
- **Discussions**: https://github.com/luokaishi/moss/discussions

---

*最后更新: 2026-04-24*
