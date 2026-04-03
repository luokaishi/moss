#!/usr/bin/env python3
"""
MOSS v5.4 - Agent Communication Protocol
Agent 间通信协议

核心功能:
- 消息传递
- 通信协议
- 消息路由
- 通信历史

Author: MOSS Project
Date: 2026-04-03
Version: 5.4.0-dev
"""

import json
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MessageType(Enum):
    """消息类型"""
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    KNOWLEDGE_SHARE = "knowledge_share"
    COORDINATION = "coordination"
    STATUS_UPDATE = "status_update"
    EMERGENCY = "emergency"


@dataclass
class Message:
    """通信消息"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = ""
    receiver: str = ""  # "*" 表示广播
    type: MessageType = MessageType.STATUS_UPDATE
    content: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    priority: float = 0.5  # 0-1
    requires_response: bool = False
    response_to: Optional[str] = None  # 回复的消息 ID
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'sender': self.sender,
            'receiver': self.receiver,
            'type': self.type.value,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'priority': self.priority,
            'requires_response': self.requires_response,
            'response_to': self.response_to
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        return cls(
            id=data['id'],
            sender=data['sender'],
            receiver=data['receiver'],
            type=MessageType(data['type']),
            content=data['content'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            priority=data['priority'],
            requires_response=data['requires_response'],
            response_to=data.get('response_to')
        )


class CommunicationChannel:
    """
    通信信道
    
    支持点对点和广播通信
    """
    
    def __init__(self, channel_id: str):
        self.channel_id = channel_id
        self.participants: List[str] = []
        self.message_queue: List[Message] = []
        self.message_history: List[Message] = []
        self.max_history = 1000
    
    def add_participant(self, agent_id: str):
        """添加参与者"""
        if agent_id not in self.participants:
            self.participants.append(agent_id)
    
    def send(self, message: Message):
        """发送消息"""
        self.message_queue.append(message)
        self.message_history.append(message)
        
        # 限制历史记录长度
        if len(self.message_history) > self.max_history:
            self.message_history = self.message_history[-self.max_history:]
    
    def receive(self, agent_id: str) -> List[Message]:
        """接收消息"""
        if agent_id not in self.participants:
            return []
        
        # 返回给该 agent 的消息
        messages = [
            m for m in self.message_queue 
            if m.receiver == agent_id or m.receiver == "*"
        ]
        
        # 从队列中移除已读取的消息
        self.message_queue = [
            m for m in self.message_queue 
            if m not in messages
        ]
        
        return messages
    
    def get_history(self, limit: int = 100) -> List[Message]:
        """获取历史消息"""
        return self.message_history[-limit:]


class CommunicationNetwork:
    """
    通信网络
    
    管理多个通信信道
    """
    
    def __init__(self):
        self.channels: Dict[str, CommunicationChannel] = {}
        self.agent_channels: Dict[str, List[str]] = {}  # agent_id -> [channel_ids]
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'broadcasts': 0
        }
    
    def create_channel(self, channel_id: str, participants: List[str]) -> CommunicationChannel:
        """创建通信信道"""
        channel = CommunicationChannel(channel_id)
        for participant in participants:
            channel.add_participant(participant)
            if participant not in self.agent_channels:
                self.agent_channels[participant] = []
            self.agent_channels[participant].append(channel_id)
        
        self.channels[channel_id] = channel
        return channel
    
    def send_message(self, message: Message, channel_id: Optional[str] = None):
        """发送消息"""
        if channel_id:
            if channel_id in self.channels:
                self.channels[channel_id].send(message)
                self.stats['messages_sent'] += 1
                if message.receiver == "*":
                    self.stats['broadcasts'] += 1
        else:
            # 广播到所有相关信道
            if message.sender in self.agent_channels:
                for channel_id in self.agent_channels[message.sender]:
                    if channel_id in self.channels:
                        self.channels[channel_id].send(message)
                self.stats['messages_sent'] += 1
    
    def receive_messages(self, agent_id: str) -> List[Message]:
        """接收 agent 的所有消息"""
        all_messages = []
        if agent_id in self.agent_channels:
            for channel_id in self.agent_channels[agent_id]:
                if channel_id in self.channels:
                    messages = self.channels[channel_id].receive(agent_id)
                    all_messages.extend(messages)
                    self.stats['messages_received'] += len(messages)
        return all_messages
    
    def get_status(self) -> Dict:
        """获取网络状态"""
        return {
            'channels': len(self.channels),
            'agents': len(self.agent_channels),
            'stats': self.stats
        }


# 便捷消息创建函数
def create_task_request(
    sender: str,
    receiver: str,
    task_description: str,
    required_skills: List[str],
    deadline: Optional[datetime] = None
) -> Message:
    """创建任务请求消息"""
    return Message(
        sender=sender,
        receiver=receiver,
        type=MessageType.TASK_REQUEST,
        content={
            'task_description': task_description,
            'required_skills': required_skills,
            'deadline': deadline.isoformat() if deadline else None
        },
        requires_response=True
    )


def create_knowledge_share(
    sender: str,
    receiver: str,
    knowledge: Dict[str, Any],
    category: str = "general"
) -> Message:
    """创建知识共享消息"""
    return Message(
        sender=sender,
        receiver=receiver,
        type=MessageType.KNOWLEDGE_SHARE,
        content={
            'knowledge': knowledge,
            'category': category
        }
    )


def create_coordination_message(
    sender: str,
    receivers: List[str],
    coordination_type: str,
    parameters: Dict[str, Any]
) -> Message:
    """创建协调消息"""
    return Message(
        sender=sender,
        receiver="*" if len(receivers) > 1 else receivers[0],
        type=MessageType.COORDINATION,
        content={
            'coordination_type': coordination_type,
            'parameters': parameters,
            'target_agents': receivers
        }
    )


# 测试代码
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v5.4 - Communication Protocol Test")
    print("=" * 60)
    
    # 创建网络
    network = CommunicationNetwork()
    
    # 创建信道
    channel1 = network.create_channel("channel_1", ["agent_1", "agent_2", "agent_3"])
    
    # 发送任务请求
    msg1 = create_task_request(
        sender="agent_1",
        receiver="agent_2",
        task_description="Implement feature X",
        required_skills=["coding", "testing"]
    )
    network.send_message(msg1, "channel_1")
    print(f"\n✅ 发送任务请求：{msg1.id}")
    
    # 发送知识共享
    msg2 = create_knowledge_share(
        sender="agent_2",
        receiver="*",
        knowledge={'tip': 'Use caching'},
        category="optimization"
    )
    network.send_message(msg2, "channel_1")
    print(f"✅ 发送知识共享：{msg2.id}")
    
    # 发送协调消息
    msg3 = create_coordination_message(
        sender="agent_1",
        receivers=["agent_2", "agent_3"],
        coordination_type="sync",
        parameters={'sync_point': 'phase_1_complete'}
    )
    network.send_message(msg3, "channel_1")
    print(f"✅ 发送协调消息：{msg3.id}")
    
    # 接收消息
    agent2_messages = network.receive_messages("agent_2")
    print(f"\n📬 Agent 2 收到 {len(agent2_messages)} 条消息:")
    for msg in agent2_messages:
        print(f"  - [{msg.type.value}] {msg.content.get('task_description', msg.content.get('knowledge', 'N/A'))}")
    
    # 获取状态
    status = network.get_status()
    print(f"\n📊 网络状态:")
    print(f"  信道数量：{status['channels']}")
    print(f"  Agent 数量：{status['agents']}")
    print(f"  发送消息：{status['stats']['messages_sent']}")
    print(f"  接收消息：{status['stats']['messages_received']}")
    print(f"  广播次数：{status['stats']['broadcasts']}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)
