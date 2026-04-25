"""
MOSS v8.0 - Multi-Agent Coordinator
多智能体协调器

核心功能:
- 多 Agent 通信
- 任务分配
- 协作机制
- 冲突解决

Author: MOSS Project
Date: 2026-04-19
"""

import uuid
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto


class AgentStatus(Enum):
    """Agent 状态"""
    IDLE = auto()
    BUSY = auto()
    OFFLINE = auto()
    ERROR = auto()


class MessageType(Enum):
    """消息类型"""
    TASK = auto()
    RESULT = auto()
    QUERY = auto()
    BROADCAST = auto()
    COORDINATION = auto()


@dataclass
class Agent:
    """Agent 表示"""
    agent_id: str
    name: str
    capabilities: List[str]
    status: AgentStatus = AgentStatus.IDLE
    current_task: Optional[str] = None
    performance_score: float = 0.5
    last_seen: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'capabilities': self.capabilities,
            'status': self.status.name,
            'current_task': self.current_task,
            'performance_score': self.performance_score,
            'last_seen': self.last_seen.isoformat()
        }


@dataclass
class Message:
    """消息"""
    message_id: str
    sender_id: str
    receiver_id: str
    message_type: MessageType
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 1
    
    def to_dict(self) -> Dict:
        return {
            'message_id': self.message_id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'message_type': self.message_type.name,
            'content': self.content,
            'priority': self.priority,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class Task:
    """任务"""
    task_id: str
    description: str
    required_capabilities: List[str]
    assigned_to: Optional[str] = None
    status: str = "pending"
    priority: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'task_id': self.task_id,
            'description': self.description,
            'required_capabilities': self.required_capabilities,
            'assigned_to': self.assigned_to,
            'status': self.status,
            'priority': self.priority,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result': self.result
        }


class MultiAgentCoordinator:
    """
    多智能体协调器
    
    管理多个 Agent 的协作
    """
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.tasks: Dict[str, Task] = {}
        self.messages: List[Message] = []
        
        # 统计
        self.stats = {
            'agents_registered': 0,
            'tasks_assigned': 0,
            'tasks_completed': 0,
            'messages_sent': 0,
            'conflicts_resolved': 0
        }
    
    def register_agent(self, name: str, capabilities: List[str]) -> Agent:
        """注册 Agent"""
        agent_id = f"AGENT_{uuid.uuid4().hex[:8]}"
        
        agent = Agent(
            agent_id=agent_id,
            name=name,
            capabilities=capabilities
        )
        
        self.agents[agent_id] = agent
        self.stats['agents_registered'] += 1
        
        return agent
    
    def create_task(self, description: str, 
                   required_capabilities: List[str],
                   priority: int = 1) -> Task:
        """创建任务"""
        task_id = f"TASK_{uuid.uuid4().hex[:8]}"
        
        task = Task(
            task_id=task_id,
            description=description,
            required_capabilities=required_capabilities,
            priority=priority
        )
        
        self.tasks[task_id] = task
        
        # 自动分配
        self._assign_task(task)
        
        return task
    
    def _assign_task(self, task: Task):
        """分配任务给最合适的 Agent"""
        candidates = []
        
        for agent in self.agents.values():
            if agent.status != AgentStatus.IDLE:
                continue
            
            # 计算能力匹配度
            matching_caps = set(agent.capabilities) & set(task.required_capabilities)
            match_score = len(matching_caps) / len(task.required_capabilities)
            
            if match_score > 0:
                candidates.append((agent, match_score))
        
        if not candidates:
            return
        
        # 选择匹配度最高且性能最好的 Agent
        candidates.sort(key=lambda x: (x[1], x[0].performance_score), reverse=True)
        best_agent = candidates[0][0]
        
        task.assigned_to = best_agent.agent_id
        task.status = "assigned"
        best_agent.status = AgentStatus.BUSY
        best_agent.current_task = task.task_id
        
        self.stats['tasks_assigned'] += 1
        
        # 发送任务消息
        self.send_message(
            sender_id="COORDINATOR",
            receiver_id=best_agent.agent_id,
            message_type=MessageType.TASK,
            content=f"Task assigned: {task.description}"
        )
    
    def send_message(self, sender_id: str, receiver_id: str,
                    message_type: MessageType, content: str,
                    priority: int = 1) -> Message:
        """发送消息"""
        message_id = f"MSG_{uuid.uuid4().hex[:8]}"
        
        message = Message(
            message_id=message_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type=message_type,
            content=content,
            priority=priority
        )
        
        self.messages.append(message)
        self.stats['messages_sent'] += 1
        
        return message
    
    def broadcast(self, sender_id: str, content: str) -> List[Message]:
        """广播消息"""
        messages = []
        
        for agent_id in self.agents:
            if agent_id != sender_id:
                msg = self.send_message(
                    sender_id=sender_id,
                    receiver_id=agent_id,
                    message_type=MessageType.BROADCAST,
                    content=content
                )
                messages.append(msg)
        
        return messages
    
    def complete_task(self, task_id: str, result: str, agent_id: str):
        """完成任务"""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        task.status = "completed"
        task.result = result
        task.completed_at = datetime.now()
        
        # 更新 Agent 状态
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            agent.status = AgentStatus.IDLE
            agent.current_task = None
            
            # 更新性能分数
            agent.performance_score = min(agent.performance_score + 0.05, 1.0)
        
        self.stats['tasks_completed'] += 1
        
        # 发送结果消息
        self.send_message(
            sender_id=agent_id,
            receiver_id="COORDINATOR",
            message_type=MessageType.RESULT,
            content=f"Task {task_id} completed: {result}"
        )
    
    def resolve_conflict(self, task_ids: List[str]) -> str:
        """解决任务冲突 (选择优先级最高的)"""
        if not task_ids:
            return None
        
        tasks = [self.tasks[tid] for tid in task_ids if tid in self.tasks]
        if not tasks:
            return None
        
        # 按优先级排序
        tasks.sort(key=lambda t: t.priority, reverse=True)
        
        winner = tasks[0]
        self.stats['conflicts_resolved'] += 1
        
        return winner.task_id
    
    def get_agent_messages(self, agent_id: str) -> List[Message]:
        """获取 Agent 的消息"""
        return [m for m in self.messages if m.receiver_id == agent_id]
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            **self.stats,
            'active_agents': len([a for a in self.agents.values() if a.status == AgentStatus.IDLE]),
            'busy_agents': len([a for a in self.agents.values() if a.status == AgentStatus.BUSY]),
            'pending_tasks': len([t for t in self.tasks.values() if t.status == "pending"]),
            'completed_tasks': len([t for t in self.tasks.values() if t.status == "completed"]),
            'total_messages': len(self.messages)
        }


# 测试
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v8.0 - Multi-Agent Coordinator Test")
    print("=" * 60)
    
    # 创建协调器
    coordinator = MultiAgentCoordinator()
    
    # 注册 Agent
    print("\n1. Registering agents...")
    agent1 = coordinator.register_agent("Agent-A", ['planning', 'reasoning'])
    agent2 = coordinator.register_agent("Agent-B", ['learning', 'optimization'])
    agent3 = coordinator.register_agent("Agent-C", ['planning', 'learning'])
    print(f"   Registered: {agent1.name} ({agent1.agent_id})")
    print(f"   Registered: {agent2.name} ({agent2.agent_id})")
    print(f"   Registered: {agent3.name} ({agent3.agent_id})")
    
    # 创建任务
    print("\n2. Creating tasks...")
    task1 = coordinator.create_task(
        "Optimize neural network",
        ['optimization', 'learning'],
        priority=2
    )
    task2 = coordinator.create_task(
        "Plan project roadmap",
        ['planning', 'reasoning'],
        priority=1
    )
    task3 = coordinator.create_task(
        "Learn new patterns",
        ['learning'],
        priority=3
    )
    print(f"   Task 1: {task1.description} -> {task1.assigned_to}")
    print(f"   Task 2: {task2.description} -> {task2.assigned_to}")
    print(f"   Task 3: {task3.description} -> {task3.assigned_to}")
    
    # 发送消息
    print("\n3. Sending messages...")
    msg = coordinator.send_message(
        sender_id=agent1.agent_id,
        receiver_id=agent2.agent_id,
        message_type=MessageType.QUERY,
        content="Can you help with optimization?"
    )
    print(f"   Sent: {msg.content}")
    
    # 广播
    print("\n4. Broadcasting...")
    broadcasts = coordinator.broadcast(agent1.agent_id, "System update available")
    print(f"   Broadcast to {len(broadcasts)} agents")
    
    # 完成任务
    print("\n5. Completing tasks...")
    coordinator.complete_task(task1.task_id, "Optimized successfully", task1.assigned_to)
    coordinator.complete_task(task2.task_id, "Roadmap created", task2.assigned_to)
    print(f"   Completed: {task1.task_id}")
    print(f"   Completed: {task2.task_id}")
    
    # 冲突解决
    print("\n6. Resolving conflicts...")
    winner = coordinator.resolve_conflict([task1.task_id, task2.task_id, task3.task_id])
    print(f"   Winner: {winner}")
    
    # 统计
    print("\n7. Coordinator stats:")
    stats = coordinator.get_stats()
    print(f"   Agents registered: {stats['agents_registered']}")
    print(f"   Active agents: {stats['active_agents']}")
    print(f"   Busy agents: {stats['busy_agents']}")
    print(f"   Tasks assigned: {stats['tasks_assigned']}")
    print(f"   Tasks completed: {stats['tasks_completed']}")
    print(f"   Messages sent: {stats['messages_sent']}")
    print(f"   Conflicts resolved: {stats['conflicts_resolved']}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)