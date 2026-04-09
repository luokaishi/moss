# Multi-Agent Communication Protocol Specification
## MOSS Phase 2: 实例间通信协议详细规范

**版本**: v0.1  
**状态**: Draft  
**目标**: 定义10-20个MOSS Agent实例间的标准通信格式与交互流程

---

## 一、协议概述

### 1.1 设计原则

1. **异步通信**: Agent无需实时响应，适应不同处理速度
2. **信任优先**: 通信权限基于历史信任分数
3. **价值导向**: 所有交互都涉及价值交换（任务、资源、信任）
4. **容错设计**: 网络分区、Agent故障不影响整体系统

### 1.2 通信层级

```
┌─────────────────────────────────────────┐
│  Layer 4: Application (Purpose Exchange)│
│  - Task negotiation                     │
│  - Resource trading                     │
│  - Reputation updates                   │
├─────────────────────────────────────────┤
│  Layer 3: Session (Trust Management)    │
│  - Authentication                       │
│  - Trust score verification             │
│  - Session establishment                │
├─────────────────────────────────────────┤
│  Layer 2: Transport (Message Routing)   │
│  - Message queuing                      │
│  - Broadcast/Multicast                  │
│  - Priority handling                    │
├─────────────────────────────────────────┤
│  Layer 1: Network (Connectivity)        │
│  - WebSocket / HTTP                     │
│  - Message persistence                  │
│  - Retry mechanism                      │
└─────────────────────────────────────────┘
```

---

## 二、消息格式规范

### 2.1 基础消息结构

```python
@dataclass
class MOSSMessage:
    # 头部信息
    msg_id: str                    # UUID v4
    version: str                   # 协议版本 "1.0"
    timestamp: datetime            # ISO 8601 format
    ttl: int                       # Time-to-live (hops)
    
    # 路由信息
    sender_id: str                 # 发送者唯一ID
    sender_purpose: PurposeVector  # 发送者当前Purpose
    receiver_id: str               # 接收者ID ("*" for broadcast)
    
    # 内容
    msg_type: MessageType          # 消息类型枚举
    payload: Dict[str, Any]        # 消息体
    
    # 验证
    signature: str                 # 数字签名 (可选)
    trust_requirement: float       # 接收者需要的最低信任度
```

### 2.2 消息类型定义

```python
from enum import Enum, auto

class MessageType(Enum):
    # 任务相关
    TASK_OFFER = "task.offer"           # 任务外包要约
    TASK_BID = "task.bid"               # 任务竞标
    TASK_ACCEPT = "task.accept"         # 接受任务
    TASK_REJECT = "task.reject"         # 拒绝任务
    TASK_COMPLETE = "task.complete"     # 任务完成报告
    TASK_QUALITY_CHECK = "task.qc"      # 质量检查结果
    
    # 资源相关
    RESOURCE_OFFER = "resource.offer"   # 资源提供
    RESOURCE_REQUEST = "resource.req"   # 资源请求
    RESOURCE_TRANSFER = "resource.xfer" # 资源转移确认
    
    # 信任与声誉
    TRUST_UPDATE = "trust.update"       # 信任分数更新
    REPUTATION_QUERY = "rep.query"      # 声誉查询
    REPUTATION_REPORT = "rep.report"    # 声誉报告
    
    # 系统相关
    HEARTBEAT = "sys.heartbeat"         # 心跳检测
    STATUS_UPDATE = "sys.status"        # 状态更新
    ERROR_REPORT = "sys.error"          # 错误报告
```

### 2.3 具体消息示例

#### TASK_OFFER (任务外包)

```json
{
  "msg_id": "uuid-1234",
  "version": "1.0",
  "timestamp": "2026-03-27T10:00:00Z",
  "ttl": 5,
  "sender_id": "agent-security-01",
  "sender_purpose": {
    "survival": 0.45,
    "curiosity": 0.15,
    "influence": 0.25,
    "optimization": 0.15
  },
  "receiver_id": "*",
  "msg_type": "task.offer",
  "payload": {
    "task_id": "task-5678",
    "task_type": "security_audit",
    "description": "Audit repository for CVE vulnerabilities",
    "repository": "github.com/example/project",
    "estimated_effort": 2.5,
    "reward": {
      "trust_points": 50,
      "priority_boost": 10
    },
    "deadline": "2026-03-27T14:00:00Z",
    "requirements": {
      "min_trust_score": 0.6,
      "required_purpose": ["survival", "curiosity"],
      "skills": ["security", "python"]
    }
  },
  "trust_requirement": 0.3
}
```

#### TASK_BID (任务竞标)

```json
{
  "msg_id": "uuid-5678",
  "version": "1.0",
  "timestamp": "2026-03-27T10:05:00Z",
  "sender_id": "agent-security-02",
  "receiver_id": "agent-security-01",
  "msg_type": "task.bid",
  "payload": {
    "task_id": "task-5678",
    "bid_id": "bid-9999",
    "bid_amount": 45,
    "estimated_completion": "2026-03-27T12:00:00Z",
    "confidence": 0.85,
    "similar_tasks_completed": 12,
    "avg_quality_score": 0.92
  }
}
```

#### TRUST_UPDATE (信任更新)

```json
{
  "msg_id": "uuid-9999",
  "version": "1.0",
  "timestamp": "2026-03-27T14:30:00Z",
  "sender_id": "agent-security-01",
  "receiver_id": "agent-security-02",
  "msg_type": "trust.update",
  "payload": {
    "target_agent": "agent-security-02",
    "interaction_type": "task_completion",
    "old_trust": 0.65,
    "new_trust": 0.72,
    "delta": 0.07,
    "reason": "Task completed on time with quality score 0.95",
    "interaction_id": "task-5678"
  }
}
```

---

## 三、通信流程

### 3.1 任务外包完整流程

```
Agent A (Task Owner)          Shared Market           Agent B (Executor)
      │                              │                      │
      │  1. TASK_OFFER               │                      │
      │─────────────────────────────>│                      │
      │                              │  2. Broadcast        │
      │                              │─────────────────────>│
      │                              │                      │
      │                              │  3. TASK_BID         │
      │                              │<─────────────────────│
      │  4. (other bids...)          │                      │
      │                              │                      │
      │  5. Evaluation Period        │                      │
      │  (10 minutes)                │                      │
      │                              │                      │
      │  6. TASK_ACCEPT              │                      │
      │─────────────────────────────>│                      │
      │                              │  7. Notify winner    │
      │                              │─────────────────────>│
      │                              │                      │
      │                              │                      │  (execution)
      │                              │                      │
      │                              │  8. TASK_COMPLETE    │
      │                              │<─────────────────────│
      │  9. Quality Check            │                      │
      │  (automated)                 │                      │
      │                              │                      │
      │  10. TRUST_UPDATE            │                      │
      │─────────────────────────────>│                      │
      │                              │  11. Update ledger   │
      │                              │                      │
```

### 3.2 信任建立流程

```python
class TrustEstablishment:
    """新Agent加入网络时的信任建立流程"""
    
    def bootstrap_trust(self, new_agent_id):
        # 1. 初始信任 = 网络平均信任 × 0.5 (保守起点)
        initial_trust = self.network_avg_trust() * 0.5
        
        # 2. 分配"试用期任务"(低风险)
        trial_task = self.create_trial_task(new_agent_id)
        
        # 3. 根据完成质量调整信任
        result = self.wait_for_completion(trial_task)
        if result.quality > 0.8:
            trust_delta = +0.1
        elif result.quality > 0.5:
            trust_delta = +0.05
        else:
            trust_delta = -0.05
        
        # 4. 广播新Agent信任分数
        self.broadcast_trust_update(new_agent_id, initial_trust + trust_delta)
```

---

## 四、安全与隐私

### 4.1 信任门控

```python
class TrustGate:
    """基于信任分数的消息过滤"""
    
    def can_receive(self, message, my_trust_for_sender):
        # 检查最低信任要求
        if my_trust_for_sender < message.trust_requirement:
            return False, "Trust score too low"
        
        # 检查消息类型权限
        type_permissions = {
            MessageType.TASK_OFFER: 0.3,
            MessageType.TASK_BID: 0.4,
            MessageType.TRUST_UPDATE: 0.5,
            MessageType.RESOURCE_TRANSFER: 0.7
        }
        
        min_trust = type_permissions.get(message.msg_type, 0.5)
        if my_trust_for_sender < min_trust:
            return False, f"Insufficient trust for {message.msg_type}"
        
        return True, "OK"
```

### 4.2 消息完整性

- **签名**: 关键消息(Task Accept, Resource Transfer)需要数字签名
- **重放防护**: 消息包含时间戳和nonce，有效期5分钟
- **篡改检测**: 消息体Hash验证

---

## 五、实现接口

### 5.1 Python SDK

```python
from moss.comm import MOSSCommunicator, MessageHandler

class MyAgentHandler(MessageHandler):
    def on_task_offer(self, message):
        # 评估是否竞标
        if self.can_handle(message.payload):
            bid = self.create_bid(message)
            self.comm.send(bid)
    
    def on_task_complete(self, message):
        # 验证质量并支付
        quality = self.verify_quality(message)
        self.update_trust(message.sender_id, quality)
        self.send_payment(message.sender_id, quality)

# 初始化通信器
comm = MOSSCommunicator(
    agent_id="agent-code-01",
    purpose_profile=my_purpose,
    message_handler=MyAgentHandler(),
    bootstrap_peers=["agent-hub:8080"]
)

comm.start()
```

### 5.2 配置文件

```yaml
# comm_config.yaml
communication:
  protocol_version: "1.0"
  transport: "websocket"
  
  network:
    listen_port: 8080
    heartbeat_interval: 30  # seconds
    connection_timeout: 300  # seconds
  
  security:
    enable_signature: true
    signature_algorithm: "ed25519"
    min_trust_default: 0.3
  
  message_queue:
    max_queue_size: 1000
    priority_levels: 3
    
  market:
    task_bid_timeout: 600  # 10 minutes
    reputation_update_interval: 3600  # 1 hour
```

---

## 六、测试规范

### 6.1 单元测试

```python
def test_task_offer_flow():
    # 模拟Agent A发布任务
    agent_a = MockAgent("A")
    agent_b = MockAgent("B")
    
    # B收到offer并竞标
    offer = create_sample_offer()
    agent_a.send(offer)
    
    # 验证B收到并响应
    assert agent_b.received_messages[0].msg_type == MessageType.TASK_OFFER
    
    bid = agent_b.create_bid(offer)
    assert bid.payload["bid_amount"] > 0
    
    # A接受bid
    agent_a.accept_bid(bid)
    assert agent_b.received_messages[-1].msg_type == MessageType.TASK_ACCEPT
```

### 6.2 集成测试

- **网络分区测试**: 部分Agent离线时系统继续运行
- **拜占庭容错测试**: 恶意Agent发送错误信息
- **负载测试**: 100消息/秒的吞吐量验证

---

## 七、版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 0.1 | 2026-03-24 | 初始草案 |

---

**下一步**: 实现消息序列化器 + 基础通信类
