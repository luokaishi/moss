# MOSS v8.6.0 核心组件设计文档

**版本**: v8.6.0 (Production Ready)  
**日期**: 2026-04-23  
**文档类型**: 组件设计规范  

---

## 1. 架构概览

### 1.1 组件层次

```
MOSS v9.0.0-dev (基于v8.6.0)
├── 应用层
│   ├── TaskAwareAgent          # 任务感知Agent (v8.3)
│   ├── MultiAgentCoordinator   # 多Agent协调 (v8.4)
│   └── SevenLayerAgent         # 七层Agent架构 (v8.3)
├── 能力层
│   ├── EventDrivenPurpose      # 事件驱动Purpose (v8.6) ⭐
│   ├── MonitoringDashboard     # 监控仪表盘 (v8.6) ⭐
│   ├── AutoRecovery            # 自动恢复 (v8.6) ⭐
│   ├── MVESRealWorldBridge     # 真实世界桥接 (v8.5) ⭐
│   └── GeneticProgrammer       # GP引擎 (v8.3)
├── 认知层
│   ├── MetaSME                 # 元自修改引擎
│   ├── MetaCognition           # 元认知系统
│   ├── DriveCompetition        # 驱动力竞争
│   └── CausalEngine            # 因果推理
└── 基础层
    ├── moss/core/SME           # main独有SME引擎
    ├── moss/core/LLMBackend    # LLM后端
    └── moss/core/HybridMutation # 混合变异策略
```

### 1.2 组件关系图

```
RealWorldEvent → EventDrivenPurpose → Purpose
                      ↓
               TaskAwareAgent ←→ MultiAgentCoordinator
                      ↓
               MonitoringDashboard (监控)
                      ↓
               AutoRecovery (故障恢复)
```

---

## 2. EventDrivenPurpose (事件驱动Purpose)

### 2.1 设计目标

替代固定步长的Purpose生成，实现**事件驱动**的实时响应。

### 2.2 核心概念

| 概念 | 说明 |
|------|------|
| Event | 真实世界事件 (文件变更/网络错误/资源告警/安全威胁/系统故障) |
| EventHandler | 事件处理器，将事件转换为Purpose |
| PurposeQueue | Purpose优先级队列 |
| EventHistory | 事件历史记录 |

### 2.3 架构设计

```python
class EventDrivenPurpose:
    # 事件处理器映射
    event_handlers: Dict[str, Callable] = {
        'file_change': _handle_file_change,      # 文件整理
        'network_error': _handle_network_error,  # 网络诊断
        'resource_alert': _handle_resource_alert, # 系统监控
        'security_threat': _handle_security_threat, # 安全扫描
        'system_failure': _handle_system_failure, # 紧急恢复
    }
```

### 2.4 事件到Purpose映射

| 事件类型 | 优先级 | 生成Purpose | 动作 |
|----------|--------|-------------|------|
| file_change | medium | organize_files | 文件分类整理 |
| network_error | high | diagnose_network | 网络故障诊断 |
| resource_alert | critical | monitor_resources | 资源监控告警 |
| security_threat | critical | security_scan | 安全威胁扫描 |
| system_failure | critical | emergency_recovery | 紧急系统恢复 |

### 2.5 接口定义

```python
def on_event(self, event: Dict) -> Optional[Dict]:
    """
    处理事件并生成Purpose
    
    Args:
        event: {
            'type': str,      # 事件类型
            'priority': str,  # low/medium/high/critical
            'data': Dict,     # 事件数据
            'source': str,    # 事件来源
        }
    
    Returns:
        Purpose对象或None
    """
```

### 2.6 使用示例

```python
from agi.event_driven_purpose import EventDrivenPurpose

edp = EventDrivenPurpose()

# 处理文件变更事件
purpose = edp.on_event({
    'type': 'file_change',
    'priority': 'medium',
    'data': {'type': 'created', 'added': ['new_file.txt']},
    'source': 'file_monitor',
})
# → 生成Purpose: organize_files
```

---

## 3. MonitoringDashboard (监控仪表盘)

### 3.1 设计目标

实现**企业级监控**，实时可视化Agent状态，支持告警规则。

### 3.2 核心概念

| 概念 | 说明 |
|------|------|
| Metric | 监控指标 (CPU/内存/任务状态等) |
| AlertRule | 告警规则 (阈值/条件) |
| Alert | 告警实例 |
| MetricsBuffer | 指标缓冲区 |

### 3.3 架构设计

```python
class MonitoringDashboard:
    metrics_buffer: List[Metric]     # 指标缓冲
    alert_rules: List[Dict]          # 告警规则
    alert_history: List[Dict]        # 告警历史
```

### 3.4 默认告警规则

| 规则 | 条件 | 级别 |
|------|------|------|
| CPU高负载 | CPU > 80% | warning |
| 内存不足 | 内存 < 20% | critical |
| Agent无响应 | 心跳超时 | critical |
| 任务失败率高 | 失败率 > 30% | warning |

### 3.5 接口定义

```python
def collect_metric(self, agent_id: str, metric_type: str, value: float, labels: Dict = None):
    """收集指标"""

def get_agent_status(self, agent_id: str) -> Dict:
    """获取Agent状态"""

def export_to_prometheus(self) -> str:
    """导出Prometheus格式"""
```

### 3.6 使用示例

```python
from agi.monitoring_dashboard import MonitoringDashboard

dashboard = MonitoringDashboard()

# 收集指标
dashboard.collect_metric('agent_1', 'cpu', 75.5)
dashboard.collect_metric('agent_1', 'memory', 82.0)

# 获取状态
status = dashboard.get_agent_status('agent_1')
print(f"健康状态: {status['is_healthy']}")
```

---

## 4. AutoRecovery (自动恢复)

### 4.1 设计目标

实现**故障自愈**，自动检测故障并执行恢复策略。

### 4.2 核心概念

| 概念 | 说明 |
|------|------|
| Failure | 故障信息 |
| RecoveryStrategy | 恢复策略 |
| RecoveryAttempt | 恢复尝试记录 |
| Cooldown | 恢复冷却期 |

### 4.3 恢复策略

| 故障类型 | 恢复策略 | 步骤 |
|----------|----------|------|
| agent_crash | Agent崩溃恢复 | 重启Agent → 加载检查点 → 恢复状态 |
| task_stuck | 任务卡住恢复 | 中断任务 → 重置状态 → 重启Agent |
| resource_exhausted | 资源耗尽恢复 | 清理资源 → 释放内存 → 优化配置 |
| network_timeout | 网络超时恢复 | 检查网络 → 重置连接 → 重试操作 |
| memory_leak | 内存泄漏恢复 | 强制GC → 释放内存 → 重启Agent |

### 4.4 接口定义

```python
def detect_failure(self, agent_status: Dict) -> Optional[Failure]:
    """检测故障"""

def recover(self, failure: Failure) -> bool:
    """执行恢复"""

def get_recovery_stats(self) -> Dict:
    """获取恢复统计"""
```

### 4.5 使用示例

```python
from agi.auto_recovery import AutoRecovery

recovery = AutoRecovery()

# 检测故障
failure = recovery.detect_failure(agent_status)

# 执行恢复
if failure:
    success = recovery.recover(failure)
    print(f"恢复{'成功' if success else '失败'}")
```

---

## 5. MVESRealWorldBridge (真实世界桥接)

### 5.1 设计目标

将mves系统接入**真实世界环境**，实现真实状态感知和安全动作执行。

### 5.2 核心概念

| 概念 | 说明 |
|------|------|
| RealWorldState | 真实世界状态快照 |
| FileSystemMonitor | 文件系统监控 |
| NetworkMonitor | 网络状态监控 |
| SystemMonitor | 系统资源监控 |
| SafeActionExecutor | 安全动作执行器 |

### 5.3 状态感知

```python
@dataclass
class RealWorldState:
    timestamp: float
    files: Dict      # 文件系统状态
    network: Dict    # 网络状态
    system: Dict     # 系统资源
    processes: Dict  # 进程状态
```

### 5.4 安全动作

| 动作类型 | 示例 | 安全检查 |
|----------|------|----------|
| file_read | 读取文件 | 路径白名单 |
| file_write | 写入文件 | 备份+确认 |
| command_exec | 执行命令 | 命令白名单 |
| network_request | 网络请求 | 域名白名单 |

### 5.5 接口定义

```python
def perceive(self) -> RealWorldState:
    """感知真实世界状态"""

def execute_action(self, action: Dict) -> Dict:
    """安全执行动作"""

def save_checkpoint(self, state: Dict) -> str:
    """保存检查点"""

def load_checkpoint(self, checkpoint_id: str) -> Dict:
    """加载检查点"""
```

### 5.6 使用示例

```python
from agi.mves_realworld_bridge import create_bridge

bridge = create_bridge()

# 感知真实世界
state = bridge.perceive()
print(f"文件数: {state.files['total_files']}")

# 执行安全动作
result = bridge.execute_action({'command': 'ls -la'})
```

---

## 6. MultiAgentCoordinator (多Agent协调)

### 6.1 设计目标

实现**多Agent协作**，支持任务分配、消息通信、冲突解决。

### 6.2 核心概念

| 概念 | 说明 |
|------|------|
| Agent | Agent实例 |
| AgentStatus | Agent状态 (IDLE/BUSY/OFFLINE/ERROR) |
| Message | 消息 |
| MessageType | 消息类型 (TASK/RESULT/QUERY/BROADCAST/COORDINATION) |
| TaskAllocation | 任务分配 |

### 6.3 架构设计

```python
class MultiAgentCoordinator:
    agents: Dict[str, Agent]           # Agent注册表
    message_queue: List[Message]       # 消息队列
    task_allocations: Dict[str, str]   # 任务分配映射
```

### 6.4 协调机制

| 机制 | 说明 |
|------|------|
| 注册发现 | Agent向协调器注册，声明能力 |
| 任务分配 | 基于能力匹配和负载均衡分配任务 |
| 消息路由 | 根据消息类型和目标路由消息 |
| 冲突检测 | 检测Agent间冲突，触发协调 |

### 6.5 接口定义

```python
def register_agent(self, agent: Agent) -> bool:
    """注册Agent"""

def allocate_task(self, task: Dict) -> Optional[str]:
    """分配任务给合适Agent"""

def send_message(self, message: Message) -> bool:
    """发送消息"""

def resolve_conflict(self, conflict: Dict) -> Dict:
    """解决冲突"""
```

### 6.6 使用示例

```python
from agi.multi_agent.coordinator import MultiAgentCoordinator

coordinator = MultiAgentCoordinator()

# 注册Agent
coordinator.register_agent(Agent(
    agent_id='agent_1',
    name='FileOrganizer',
    capabilities=['file_management', 'classification']
))

# 分配任务
agent_id = coordinator.allocate_task({
    'type': 'file_organization',
    'priority': 'high'
})
```

---

## 7. 组件交互

### 7.1 典型场景：文件整理任务

```
1. FileSystemMonitor检测到文件变更
   ↓
2. EventDrivenPurpose生成organize_files Purpose
   ↓
3. TaskAwareAgent接收任务
   ↓
4. MultiAgentCoordinator分配任务给FileOrganizer Agent
   ↓
5. Agent通过MVESRealWorldBridge执行文件操作
   ↓
6. MonitoringDashboard监控执行过程
   ↓
7. 如遇故障，AutoRecovery执行恢复
```

### 7.2 数据流

```
RealWorldState → Event → Purpose → Task → Action → Result → Metric → Alert
```

---

## 8. 配置指南

### 8.1 最小配置

```python
# EventDrivenPurpose
edp_config = {
    'max_history': 1000,
}

# MonitoringDashboard
dashboard_config = {
    'max_buffer_size': 10000,
    'data_dir': '/tmp/moss_dashboard',
}

# AutoRecovery
recovery_config = {
    'max_recovery_attempts': 3,
    'recovery_cooldown': 60,
}
```

### 8.2 生产配置

```python
# 完整配置示例见各组件__init__参数
```

---

## 9. 性能指标

| 组件 | 延迟 | 吞吐量 | 可靠性 |
|------|------|--------|--------|
| EventDrivenPurpose | <10ms | 1000 events/s | 99.9% |
| MonitoringDashboard | <50ms | 10000 metrics/s | 99.99% |
| AutoRecovery | <5s | - | 95%+ |
| MVESRealWorldBridge | <100ms | 100 actions/s | 99.9% |
| MultiAgentCoordinator | <20ms | 1000 msgs/s | 99.9% |

---

## 10. 扩展指南

### 10.1 添加新事件类型

```python
# 在EventDrivenPurpose中添加处理器
def _handle_custom_event(self, event: Event) -> Dict:
    return {
        'name': 'custom_purpose',
        'priority': event.priority,
        'actions': [...]
    }

# 注册到event_handlers
self.event_handlers['custom_event'] = self._handle_custom_event
```

### 10.2 添加新恢复策略

```python
# 在AutoRecovery中添加策略
def _recover_custom_failure(self, failure: Failure) -> bool:
    # 实现恢复逻辑
    return success

# 注册到recovery_strategies
self.recovery_strategies['custom_failure'] = self._recover_custom_failure
```

---

## 附录

### A. 版本演进

| 版本 | 新增组件 | 状态 |
|------|----------|------|
| v8.3.0 | TaskAwareAgent, GeneticProgrammer | ✅ 已合并 |
| v8.4.0 | MultiAgentCoordinator | ✅ 已合并 |
| v8.5.0 | MVESRealWorldBridge | ✅ 已合并 |
| v8.6.0 | EventDrivenPurpose, MonitoringDashboard, AutoRecovery | ✅ 已合并 |
| v9.0.0 | 统一架构 (规划中) | ⏳ 待开发 |

### B. 相关文档

- [UNIFIED_VALIDATION_REPORT.md](./UNIFIED_VALIDATION_REPORT.md) - 统一验证报告
- [MERGE_STRATEGY_v860.md](./MERGE_STRATEGY_v860.md) - 合并策略
- [RFC_v9.md](./RFC_v9.md) - v9.0架构设计 (待创建)

---

*文档版本: v1.0*  
*最后更新: 2026-04-23*
