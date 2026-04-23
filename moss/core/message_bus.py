#!/usr/bin/env python3
"""
MOSS v9.0 - Message Bus
消息总线 - Agent间通信基础设施

Author: MOSS v9.0
Date: 2026-04-23
"""

from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
import asyncio
import uuid
import json


class MessageType(Enum):
    """消息类型"""
    TASK = auto()          # 任务分配
    RESULT = auto()        # 任务结果
    QUERY = auto()         # 查询请求
    RESPONSE = auto()      # 查询响应
    BROADCAST = auto()     # 广播消息
    COORDINATION = auto()  # 协调消息
    HEARTBEAT = auto()     # 心跳
    ERROR = auto()         # 错误通知


class Priority(Enum):
    """消息优先级"""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class Message:
    """MOSS标准消息格式"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    source: str = ""                    # 来源Agent ID
    target: Optional[str] = None        # 目标Agent ID (None=广播)
    message_type: MessageType = MessageType.BROADCAST
    payload: Dict = field(default_factory=dict)
    priority: Priority = Priority.NORMAL
    ttl: int = 300                      # 生存时间(秒)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'message_id': self.message_id,
            'timestamp': self.timestamp,
            'source': self.source,
            'target': self.target,
            'message_type': self.message_type.name,
            'payload': self.payload,
            'priority': self.priority.value,
            'ttl': self.ttl,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        """从字典创建"""
        return cls(
            message_id=data.get('message_id', str(uuid.uuid4())),
            timestamp=data.get('timestamp', datetime.now().timestamp()),
            source=data.get('source', ''),
            target=data.get('target'),
            message_type=MessageType[data.get('message_type', 'BROADCAST')],
            payload=data.get('payload', {}),
            priority=Priority(data.get('priority', 2)),
            ttl=data.get('ttl', 300),
        )
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        age = datetime.now().timestamp() - self.timestamp
        return age > self.ttl


@dataclass
class Subscription:
    """订阅信息"""
    subscription_id: str
    topic: str
    handler: Callable
    agent_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


class MessageBus:
    """
    消息总线
    
    核心功能:
    1. 发布-订阅模式
    2. 点对点消息
    3. 广播消息
    4. 消息路由
    5. 消息持久化(可选)
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.subscriptions: Dict[str, List[Subscription]] = {}  # topic -> [subscriptions]
        self.agent_handlers: Dict[str, Callable] = {}  # agent_id -> handler
        self.message_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.message_history: List[Message] = []
        self.max_history = self.config.get('max_history', 10000)
        self._processing_task: Optional[asyncio.Task] = None
        self._running = False
        
        # 统计
        self.stats = {
            'published': 0,
            'delivered': 0,
            'dropped': 0,
            'errors': 0,
        }
    
    async def initialize(self) -> bool:
        """初始化消息总线"""
        try:
            self._running = True
            self._processing_task = asyncio.create_task(
                self._process_message_loop()
            )
            print("[MessageBus] 初始化完成")
            return True
        except Exception as e:
            print(f"[MessageBus] 初始化失败: {e}")
            return False
    
    async def subscribe(
        self,
        topic: str,
        handler: Callable,
        agent_id: Optional[str] = None
    ) -> str:
        """
        订阅主题
        
        Args:
            topic: 主题名称
            handler: 消息处理函数
            agent_id: 关联的Agent ID
            
        Returns:
            subscription_id: 订阅ID
        """
        subscription_id = f"sub_{uuid.uuid4().hex[:8]}"
        
        subscription = Subscription(
            subscription_id=subscription_id,
            topic=topic,
            handler=handler,
            agent_id=agent_id
        )
        
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
        
        self.subscriptions[topic].append(subscription)
        
        # 如果指定了agent_id，注册到agent_handlers
        if agent_id:
            self.agent_handlers[agent_id] = handler
        
        print(f"[MessageBus] 订阅创建: {subscription_id} -> {topic}")
        return subscription_id
    
    async def unsubscribe(self, subscription_id: str) -> bool:
        """取消订阅"""
        for topic, subs in self.subscriptions.items():
            for sub in subs:
                if sub.subscription_id == subscription_id:
                    subs.remove(sub)
                    print(f"[MessageBus] 订阅取消: {subscription_id}")
                    return True
        return False
    
    async def publish(
        self,
        topic: str,
        payload: Dict,
        source: str = "",
        priority: Priority = Priority.NORMAL,
        ttl: int = 300
    ) -> str:
        """
        发布消息到主题
        
        Args:
            topic: 主题名称
            payload: 消息内容
            source: 来源Agent ID
            priority: 优先级
            ttl: 生存时间
            
        Returns:
            message_id: 消息ID
        """
        message = Message(
            source=source,
            target=None,  # 广播
            message_type=MessageType.BROADCAST,
            payload=payload,
            priority=priority,
            ttl=ttl
        )
        
        # 添加到队列 (优先级队列: (priority_value, timestamp, message))
        await self.message_queue.put((
            priority.value,
            message.timestamp,
            message
        ))
        
        self.stats['published'] += 1
        return message.message_id
    
    async def send_to_agent(
        self,
        target_agent_id: str,
        payload: Dict,
        source: str = "",
        message_type: MessageType = MessageType.TASK,
        priority: Priority = Priority.NORMAL,
        ttl: int = 300
    ) -> str:
        """
        点对点发送消息
        
        Args:
            target_agent_id: 目标Agent ID
            payload: 消息内容
            source: 来源Agent ID
            message_type: 消息类型
            priority: 优先级
            ttl: 生存时间
            
        Returns:
            message_id: 消息ID
        """
        message = Message(
            source=source,
            target=target_agent_id,
            message_type=message_type,
            payload=payload,
            priority=priority,
            ttl=ttl
        )
        
        await self.message_queue.put((
            priority.value,
            message.timestamp,
            message
        ))
        
        self.stats['published'] += 1
        return message.message_id
    
    async def broadcast(
        self,
        payload: Dict,
        source: str = "",
        priority: Priority = Priority.NORMAL
    ) -> str:
        """广播消息到所有Agent"""
        return await self.publish(
            topic="broadcast",
            payload=payload,
            source=source,
            priority=priority
        )
    
    async def _process_message_loop(self):
        """消息处理循环"""
        while self._running:
            try:
                # 获取消息 (带超时以便检查_running)
                try:
                    _, _, message = await asyncio.wait_for(
                        self.message_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # 检查过期
                if message.is_expired():
                    self.stats['dropped'] += 1
                    continue
                
                # 记录历史
                self.message_history.append(message)
                if len(self.message_history) > self.max_history:
                    self.message_history.pop(0)
                
                # 路由消息
                await self._route_message(message)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[MessageBus] 消息处理错误: {e}")
                self.stats['errors'] += 1
    
    async def _route_message(self, message: Message):
        """路由消息到目标"""
        try:
            if message.target:
                # 点对点消息
                await self._deliver_to_agent(message.target, message)
            else:
                # 广播消息 - 发送到所有订阅者
                await self._deliver_to_subscribers(message)
                
        except Exception as e:
            print(f"[MessageBus] 路由失败: {e}")
            self.stats['errors'] += 1
    
    async def _deliver_to_agent(self, agent_id: str, message: Message):
        """投递到指定Agent"""
        handler = self.agent_handlers.get(agent_id)
        
        if handler:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
                self.stats['delivered'] += 1
            except Exception as e:
                print(f"[MessageBus] 投递到 {agent_id} 失败: {e}")
                self.stats['errors'] += 1
        else:
            print(f"[MessageBus] Agent {agent_id} 未注册")
            self.stats['dropped'] += 1
    
    async def _deliver_to_subscribers(self, message: Message):
        """投递到所有订阅者"""
        # 这里简化处理，实际应该根据topic路由
        delivered = 0
        
        for agent_id, handler in self.agent_handlers.items():
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
                delivered += 1
            except Exception as e:
                print(f"[MessageBus] 投递到 {agent_id} 失败: {e}")
        
        self.stats['delivered'] += delivered
    
    async def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            'queue_size': self.message_queue.qsize(),
            'subscribers': sum(len(subs) for subs in self.subscriptions.values()),
            'registered_agents': len(self.agent_handlers),
        }
    
    async def shutdown(self) -> bool:
        """关闭消息总线"""
        try:
            self._running = False
            
            if self._processing_task:
                self._processing_task.cancel()
                try:
                    await self._processing_task
                except asyncio.CancelledError:
                    pass
            
            # 清空订阅
            self.subscriptions.clear()
            self.agent_handlers.clear()
            
            print("[MessageBus] 已关闭")
            return True
        except Exception as e:
            print(f"[MessageBus] 关闭失败: {e}")
            return False


# 全局消息总线实例
_bus: Optional[MessageBus] = None


def get_message_bus(config: Dict = None) -> MessageBus:
    """获取全局消息总线实例"""
    global _bus
    if _bus is None:
        _bus = MessageBus(config)
    return _bus


async def create_message_bus(config: Dict = None) -> MessageBus:
    """创建并初始化消息总线"""
    bus = MessageBus(config)
    await bus.initialize()
    return bus


# 测试代码
if __name__ == "__main__":
    async def test():
        # 创建消息总线
        bus = await create_message_bus()
        
        # 消息处理器
        async def handler(message):
            print(f"收到消息: {message.payload}")
        
        # 订阅
        sub_id = await bus.subscribe("test_topic", handler, "agent_1")
        print(f"订阅ID: {sub_id}")
        
        # 发布消息
        msg_id = await bus.publish(
            topic="test_topic",
            payload={"content": "Hello, MOSS!"},
            source="test"
        )
        print(f"消息ID: {msg_id}")
        
        # 等待消息处理
        await asyncio.sleep(0.5)
        
        # 获取统计
        stats = await bus.get_stats()
        print(f"统计: {stats}")
        
        # 关闭
        await bus.shutdown()
    
    asyncio.run(test())
