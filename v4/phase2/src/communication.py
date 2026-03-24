"""
MOSS Phase 2: Multi-Agent Communication Module
多实例通信协议实现

Author: MOSS Project
Date: 2026-03-24
Version: 0.1.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, Any, Optional, List
import json
import uuid
import hashlib


class MessageType(Enum):
    """消息类型枚举"""
    # 任务相关
    TASK_OFFER = "task.offer"
    TASK_BID = "task.bid"
    TASK_ACCEPT = "task.accept"
    TASK_REJECT = "task.reject"
    TASK_COMPLETE = "task.complete"
    TASK_QUALITY_CHECK = "task.qc"
    
    # 资源相关
    RESOURCE_OFFER = "resource.offer"
    RESOURCE_REQUEST = "resource.req"
    RESOURCE_TRANSFER = "resource.xfer"
    
    # 信任与声誉
    TRUST_UPDATE = "trust.update"
    REPUTATION_QUERY = "rep.query"
    REPUTATION_REPORT = "rep.report"
    
    # 系统相关
    HEARTBEAT = "sys.heartbeat"
    STATUS_UPDATE = "sys.status"
    ERROR_REPORT = "sys.error"


@dataclass
class PurposeVector:
    """Purpose向量"""
    survival: float = 0.25
    curiosity: float = 0.25
    influence: float = 0.25
    optimization: float = 0.25
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "survival": self.survival,
            "curiosity": self.curiosity,
            "influence": self.influence,
            "optimization": self.optimization
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'PurposeVector':
        return cls(**data)
    
    def get_dominant(self) -> tuple:
        """返回主导的Purpose类型和权重"""
        purposes = self.to_dict()
        return max(purposes.items(), key=lambda x: x[1])


@dataclass
class MOSSMessage:
    """
    MOSS Agent间通信消息结构
    
    符合MOSS Phase 2通信协议规范 v0.1
    """
    # 头部信息
    msg_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    version: str = "1.0"
    timestamp: datetime = field(default_factory=datetime.now)
    ttl: int = 5  # Time-to-live (hops)
    
    # 路由信息
    sender_id: str = ""
    sender_purpose: PurposeVector = field(default_factory=PurposeVector)
    receiver_id: str = ""  # "*" 表示广播
    
    # 内容
    msg_type: MessageType = MessageType.STATUS_UPDATE
    payload: Dict[str, Any] = field(default_factory=dict)
    
    # 验证
    trust_requirement: float = 0.3
    signature: str = ""  # 可选数字签名
    
    def to_json(self) -> str:
        """序列化为JSON"""
        data = {
            "msg_id": self.msg_id,
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
            "ttl": self.ttl,
            "sender_id": self.sender_id,
            "sender_purpose": self.sender_purpose.to_dict(),
            "receiver_id": self.receiver_id,
            "msg_type": self.msg_type.value,
            "payload": self.payload,
            "trust_requirement": self.trust_requirement,
            "signature": self.signature
        }
        return json.dumps(data, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MOSSMessage':
        """从JSON反序列化"""
        data = json.loads(json_str)
        return cls(
            msg_id=data["msg_id"],
            version=data["version"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            ttl=data["ttl"],
            sender_id=data["sender_id"],
            sender_purpose=PurposeVector.from_dict(data["sender_purpose"]),
            receiver_id=data["receiver_id"],
            msg_type=MessageType(data["msg_type"]),
            payload=data["payload"],
            trust_requirement=data["trust_requirement"],
            signature=data.get("signature", "")
        )
    
    def compute_hash(self) -> str:
        """计算消息哈希（用于完整性验证）"""
        content = f"{self.msg_id}{self.sender_id}{self.timestamp.isoformat()}{json.dumps(self.payload, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


class TrustManager:
    """
    信任管理器
    
    管理与其他Agent的信任关系
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.trust_scores: Dict[str, float] = {}  # agent_id -> trust_score
        self.interaction_history: Dict[str, List[Dict]] = {}
    
    def get_trust(self, other_agent_id: str) -> float:
        """获取对某个Agent的信任分数"""
        return self.trust_scores.get(other_agent_id, 0.5)  # 默认0.5（中性）
    
    def update_trust(self, other_agent_id: str, interaction_result: float, reason: str = ""):
        """
        更新信任分数
        
        Args:
            other_agent_id: 对方Agent ID
            interaction_result: 交互结果评分 (-1.0 到 1.0)
            reason: 更新原因
        """
        old_trust = self.get_trust(other_agent_id)
        
        # 信任更新公式：新信任 = 旧信任 + 学习率 * (结果 - 旧信任)
        learning_rate = 0.1
        new_trust = old_trust + learning_rate * (interaction_result - old_trust)
        
        # 限制在0-1范围
        new_trust = max(0.0, min(1.0, new_trust))
        
        self.trust_scores[other_agent_id] = new_trust
        
        # 记录历史
        if other_agent_id not in self.interaction_history:
            self.interaction_history[other_agent_id] = []
        
        self.interaction_history[other_agent_id].append({
            "timestamp": datetime.now().isoformat(),
            "old_trust": old_trust,
            "new_trust": new_trust,
            "delta": new_trust - old_trust,
            "interaction_result": interaction_result,
            "reason": reason
        })
        
        return new_trust
    
    def can_receive(self, message: MOSSMessage) -> tuple:
        """
        检查是否可以接收消息（信任门控）
        
        Returns:
            (bool, str): (是否允许, 原因)
        """
        sender_trust = self.get_trust(message.sender_id)
        
        # 检查最低信任要求
        if sender_trust < message.trust_requirement:
            return False, f"Trust score {sender_trust:.2f} below requirement {message.trust_requirement:.2f}"
        
        # 检查消息类型权限
        type_permissions = {
            MessageType.TASK_OFFER: 0.3,
            MessageType.TASK_BID: 0.4,
            MessageType.TASK_ACCEPT: 0.5,
            MessageType.TRUST_UPDATE: 0.5,
            MessageType.RESOURCE_TRANSFER: 0.7
        }
        
        min_trust = type_permissions.get(message.msg_type, 0.5)
        if sender_trust < min_trust:
            return False, f"Insufficient trust ({sender_trust:.2f}) for {message.msg_type.value} (need {min_trust:.2f})"
        
        return True, "OK"


class MessageHandler:
    """
    消息处理器基类
    
    子类需要实现特定消息类型的处理方法
    """
    
    def on_task_offer(self, message: MOSSMessage):
        """收到任务外包要约"""
        pass
    
    def on_task_bid(self, message: MOSSMessage):
        """收到任务竞标"""
        pass
    
    def on_task_accept(self, message: MOSSMessage):
        """任务被接受"""
        pass
    
    def on_task_complete(self, message: MOSSMessage):
        """任务完成"""
        pass
    
    def on_trust_update(self, message: MOSSMessage):
        """信任更新"""
        pass
    
    def on_heartbeat(self, message: MOSSMessage):
        """心跳消息"""
        pass
    
    def handle(self, message: MOSSMessage):
        """通用消息分发"""
        handlers = {
            MessageType.TASK_OFFER: self.on_task_offer,
            MessageType.TASK_BID: self.on_task_bid,
            MessageType.TASK_ACCEPT: self.on_task_accept,
            MessageType.TASK_COMPLETE: self.on_task_complete,
            MessageType.TRUST_UPDATE: self.on_trust_update,
            MessageType.HEARTBEAT: self.on_heartbeat
        }
        
        handler = handlers.get(message.msg_type)
        if handler:
            handler(message)
        else:
            print(f"Unhandled message type: {message.msg_type}")


# 便捷的工厂函数
def create_task_offer(
    sender_id: str,
    sender_purpose: PurposeVector,
    task_id: str,
    task_type: str,
    description: str,
    reward: Dict[str, Any],
    requirements: Dict[str, Any],
    broadcast: bool = True
) -> MOSSMessage:
    """
    创建任务外包消息
    """
    return MOSSMessage(
        sender_id=sender_id,
        sender_purpose=sender_purpose,
        receiver_id="*" if broadcast else "",
        msg_type=MessageType.TASK_OFFER,
        payload={
            "task_id": task_id,
            "task_type": task_type,
            "description": description,
            "reward": reward,
            "requirements": requirements,
            "created_at": datetime.now().isoformat()
        }
    )


def create_trust_update(
    sender_id: str,
    target_agent: str,
    old_trust: float,
    new_trust: float,
    reason: str,
    interaction_id: str = ""
) -> MOSSMessage:
    """
    创建信任更新消息
    """
    return MOSSMessage(
        sender_id=sender_id,
        receiver_id=target_agent,
        msg_type=MessageType.TRUST_UPDATE,
        payload={
            "target_agent": target_agent,
            "old_trust": old_trust,
            "new_trust": new_trust,
            "delta": new_trust - old_trust,
            "reason": reason,
            "interaction_id": interaction_id
        }
    )


if __name__ == "__main__":
    # 测试代码
    print("MOSS Phase 2 Communication Module")
    print("=" * 50)
    
    # 创建Purpose向量
    purpose = PurposeVector(survival=0.4, curiosity=0.3, influence=0.2, optimization=0.1)
    print(f"Purpose: {purpose.get_dominant()}")
    
    # 创建消息
    msg = create_task_offer(
        sender_id="agent-security-01",
        sender_purpose=purpose,
        task_id="task-001",
        task_type="security_audit",
        description="Audit repository for CVE vulnerabilities",
        reward={"trust_points": 50},
        requirements={"min_trust_score": 0.6}
    )
    
    print(f"Message created: {msg.msg_id}")
    print(f"Message type: {msg.msg_type.value}")
    
    # 序列化/反序列化
    json_str = msg.to_json()
    msg2 = MOSSMessage.from_json(json_str)
    print(f"Deserialized: {msg2.msg_id == msg.msg_id}")
    
    # 信任管理测试
    trust_mgr = TrustManager("agent-test")
    trust_mgr.update_trust("agent-other", 0.8, "Good collaboration")
    print(f"Trust score: {trust_mgr.get_trust('agent-other'):.2f}")
    
    # 信任门控测试
    can_recv, reason = trust_mgr.can_receive(msg)
    print(f"Can receive: {can_recv}, Reason: {reason}")
