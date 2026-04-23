# RFC: MOSS v9.0 统一架构设计

**状态**: Draft  
**版本**: v0.1  
**日期**: 2026-04-23  
**作者**: MOSS AI Agent  

---

## 1. 背景与动机

### 1.1 当前问题

MOSS项目经过v8.1.1到v8.6.0的快速演进，积累了大量组件：

- **moss/core/**: 24个模块 (main分支，SME引擎)
- **agi/**: 80个模块 (mves合并，AGI组件)
- **架构分散**: 两套并行架构未完全统一

### 1.2 设计目标

v9.0旨在：
1. **统一架构**: 整合moss/core/和agi/为统一框架
2. **清晰分层**: 明确各层职责边界
3. **可扩展性**: 支持未来10-20 Agent扩展
4. **生产就绪**: 企业级可用性

---

## 2. 架构设计

### 2.1 总体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    MOSS v9.0 统一架构                        │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: 应用层 (Application)                               │
│  ├── AgentApp                                                │
│  ├── TaskOrchestrator                                        │
│  └── MultiAgentApp                                           │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: 能力层 (Capability)                                │
│  ├── SelfModificationEngine (原moss/core/)                   │
│  ├── TaskAwareAgent (原agi/)                                 │
│  ├── EventDrivenPurpose                                      │
│  ├── RealWorldBridge                                         │
│  └── MonitoringDashboard                                     │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: 协调层 (Coordination)                              │
│  ├── AgentRegistry (统一注册中心)                             │
│  ├── MessageBus (统一消息总线)                                │
│  ├── ConflictResolver (统一冲突解决)                          │
│  └── ResourceScheduler (资源调度)                             │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: 基础层 (Foundation)                                │
│  ├── LLMBackend (统一LLM后端)                                │
│  ├── MutationEngine (统一变异引擎)                            │
│  ├── PurposeEngine (统一Purpose引擎)                          │
│  └── SafetyGuard (统一安全层)                                 │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件

#### 2.2.1 AgentRegistry (Agent注册中心)

**职责**: 统一管理所有Agent的生命周期

```python
class AgentRegistry:
    """Agent注册中心 - 统一管理Agent"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}           # Agent实例
        self.capabilities: Dict[str, List[str]] = {} # 能力索引
        self.health_status: Dict[str, HealthStatus] = {} # 健康状态
    
    def register(self, agent: Agent) -> str:
        """注册Agent，返回agent_id"""
        pass
    
    def unregister(self, agent_id: str) -> bool:
        """注销Agent"""
        pass
    
    def find_by_capability(self, capability: str) -> List[Agent]:
        """按能力查找Agent"""
        pass
    
    def get_healthy_agents(self) -> List[Agent]:
        """获取健康Agent列表"""
        pass
```

#### 2.2.2 MessageBus (消息总线)

**职责**: 统一Agent间通信

```python
class MessageBus:
    """消息总线 - Agent间通信基础设施"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}  # 订阅者
        self.message_queue: asyncio.Queue = asyncio.Queue()  # 消息队列
        self.routing_table: Dict[str, str] = {}  # 路由表
    
    async def publish(self, topic: str, message: Message) -> bool:
        """发布消息到主题"""
        pass
    
    async def subscribe(self, topic: str, handler: Callable) -> str:
        """订阅主题"""
        pass
    
    async def send_to_agent(self, agent_id: str, message: Message) -> bool:
        """点对点发送消息"""
        pass
    
    async def broadcast(self, message: Message) -> int:
        """广播消息到所有Agent"""
        pass
```

#### 2.2.3 ConflictResolver (冲突解决器)

**职责**: 解决Agent间冲突

```python
class ConflictResolver:
    """冲突解决器 - 解决Agent间冲突"""
    
    def __init__(self):
        self.resolution_strategies: Dict[str, ResolutionStrategy] = {}
        self.conflict_history: List[Conflict] = []
    
    def detect_conflict(self, actions: List[Action]) -> Optional[Conflict]:
        """检测冲突"""
        pass
    
    def resolve(self, conflict: Conflict) -> Resolution:
        """解决冲突"""
        pass
    
    def register_strategy(self, conflict_type: str, strategy: ResolutionStrategy):
        """注册解决策略"""
        pass
```

### 2.3 统一接口

所有Layer 3+组件实现统一接口：

```python
class MOSSComponent(ABC):
    """MOSS组件统一接口"""
    
    @abstractmethod
    def initialize(self, config: Dict) -> bool:
        """初始化组件"""
        pass
    
    @abstractmethod
    def health_check(self) -> HealthStatus:
        """健康检查"""
        pass
    
    @abstractmethod
    def get_metrics(self) -> Dict:
        """获取指标"""
        pass
    
    @abstractmethod
    def shutdown(self) -> bool:
        """优雅关闭"""
        pass
```

---

## 3. 数据流设计

### 3.1 典型场景：多Agent协作任务

```
1. 外部事件触发
   ↓
2. EventDrivenPurpose生成Purpose
   ↓
3. AgentRegistry查找合适Agent
   ↓
4. MessageBus分配任务消息
   ↓
5. Agent执行任务
   ↓
6. RealWorldBridge执行真实动作
   ↓
7. MonitoringDashboard监控过程
   ↓
8. 如遇冲突，ConflictResolver介入
   ↓
9. 结果通过MessageBus返回
   ↓
10. SelfModificationEngine评估并进化
```

### 3.2 消息格式

```python
@dataclass
class MOSSMessage:
    """MOSS标准消息格式"""
    message_id: str           # 消息ID
    timestamp: float          # 时间戳
    source: str               # 来源Agent ID
    target: Optional[str]     # 目标Agent ID (None表示广播)
    message_type: MessageType # 消息类型
    payload: Dict             # 消息内容
    priority: int             # 优先级 (0-10)
    ttl: int                  # 生存时间 (秒)
```

---

## 4. 迁移路径

### 4.1 从v8.6.0到v9.0

| v8.6.0组件 | v9.0位置 | 迁移策略 |
|------------|----------|----------|
| moss/core/SME | Layer 3 | 保留，实现统一接口 |
| agi/TaskAwareAgent | Layer 3 | 保留，实现统一接口 |
| agi/EventDrivenPurpose | Layer 3 | 保留，实现统一接口 |
| agi/MultiAgentCoordinator | Layer 2 | 重构为AgentRegistry+MessageBus |
| agi/MonitoringDashboard | Layer 3 | 保留，实现统一接口 |
| agi/AutoRecovery | Layer 3 | 保留，实现统一接口 |
| agi/MVESRealWorldBridge | Layer 3 | 保留，实现统一接口 |

### 4.2 分阶段实施

**Phase 1 (Week 1)**: 基础设施
- 实现AgentRegistry
- 实现MessageBus
- 实现基础接口

**Phase 2 (Week 2)**: 组件迁移
- 迁移moss/core/SME
- 迁移agi/TaskAwareAgent
- 迁移agi/EventDrivenPurpose

**Phase 3 (Week 3)**: 协调层
- 实现ConflictResolver
- 重构MultiAgentCoordinator
- 集成测试

**Phase 4 (Week 4)**: 优化发布
- 性能优化
- 文档完善
- v9.0-alpha发布

---

## 5. 接口规范

### 5.1 Agent接口

```python
class MOSSAgent(ABC):
    """MOSS Agent统一接口"""
    
    @property
    @abstractmethod
    def agent_id(self) -> str:
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> List[str]:
        pass
    
    @abstractmethod
    async def handle_message(self, message: MOSSMessage) -> MOSSMessage:
        """处理消息"""
        pass
    
    @abstractmethod
    async def execute_task(self, task: Task) -> TaskResult:
        """执行任务"""
        pass
```

### 5.2 配置规范

```python
@dataclass
class MOSSConfig:
    """MOSS统一配置"""
    # 系统配置
    system_name: str = "MOSS"
    version: str = "9.0.0"
    
    # Agent配置
    max_agents: int = 20
    agent_timeout: float = 30.0
    
    # 消息配置
    message_ttl: int = 300
    max_queue_size: int = 10000
    
    # 监控配置
    metrics_interval: float = 5.0
    alert_threshold: Dict = field(default_factory=dict)
```

---

## 6. 性能目标

| 指标 | 目标 | 说明 |
|------|------|------|
| Agent注册延迟 | <10ms | 从注册到可用 |
| 消息传递延迟 | <5ms | 点对点消息 |
| 广播延迟 | <20ms | 广播到20个Agent |
| 冲突检测延迟 | <50ms | 检测并识别冲突 |
| 系统吞吐量 | 1000 msg/s | 总消息处理能力 |
| 最大Agent数 | 20 | 单节点支持 |
| 可用性 | 99.9% | 年度可用性 |

---

## 7. 安全考虑

### 7.1 安全层设计

```
Layer 1: 输入验证
- 消息格式验证
- 参数范围检查
- 权限验证

Layer 2: 沙箱执行
- Agent隔离
- 资源限制
- 超时控制

Layer 3: 审计日志
- 操作记录
- 变更追踪
- 异常告警
```

### 7.2 安全接口

```python
class SafetyGuard:
    """安全守卫"""
    
    def validate_message(self, message: MOSSMessage) -> bool:
        """验证消息安全性"""
        pass
    
    def check_permission(self, agent_id: str, action: str) -> bool:
        """检查权限"""
        pass
    
    def audit_log(self, event: SecurityEvent):
        """记录审计日志"""
        pass
```

---

## 8. 测试策略

### 8.1 测试金字塔

```
    /\
   /  \  E2E测试 (5%)
  /____\
 /      \  集成测试 (20%)
/________\
/          \  单元测试 (75%)
```

### 8.2 关键测试场景

1. **单Agent生命周期**: 注册→运行→注销
2. **多Agent通信**: 点对点+广播
3. **冲突检测解决**: 资源冲突+任务冲突
4. **故障恢复**: Agent崩溃+网络分区
5. **性能基准**: 20 Agent并发

---

## 9. 实现计划

### 9.1 任务分解

| 任务 | 负责人 | 工期 | 依赖 |
|------|--------|------|------|
| T1: AgentRegistry | AI | 2天 | - |
| T2: MessageBus | AI | 2天 | - |
| T3: ConflictResolver | AI | 2天 | T1,T2 |
| T4: 组件接口适配 | AI | 3天 | T1,T2 |
| T5: 集成测试 | AI | 2天 | T3,T4 |
| T6: 性能优化 | AI | 2天 | T5 |
| T7: 文档完善 | AI | 1天 | T6 |

**总计**: 14天 (2周)

### 9.2 里程碑

- **M1 (Day 7)**: 基础设施完成 (AgentRegistry+MessageBus)
- **M2 (Day 10)**: 组件迁移完成
- **M3 (Day 14)**: v9.0-alpha发布

---

## 10. 开放问题

1. **分布式支持**: 是否需要支持多节点部署？
2. **持久化**: Agent状态是否需要持久化存储？
3. **热更新**: 是否支持运行时组件更新？
4. **外部集成**: 与Kubernetes等编排系统集成？

---

## 附录

### A. 术语表

| 术语 | 定义 |
|------|------|
| Agent | 自主智能体，具有感知、决策、执行能力 |
| Purpose | 目的，Agent行为的内在驱动力 |
| Message | 消息，Agent间通信的基本单元 |
| Registry | 注册中心，管理Agent元数据 |
| Bus | 总线，消息路由基础设施 |

### B. 参考文档

- [DESIGN_v860_Components.md](./DESIGN_v860_Components.md)
- [UNIFIED_VALIDATION_REPORT.md](./UNIFIED_VALIDATION_REPORT.md)
- [MERGE_STRATEGY_v860.md](./MERGE_STRATEGY_v860.md)

---

*RFC状态: Draft*  
*最后更新: 2026-04-23*  
*讨论请提交Issue*
