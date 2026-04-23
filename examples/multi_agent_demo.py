#!/usr/bin/env python3
"""
MOSS v9.0 - 多Agent协作演示
展示AgentRegistry + MessageBus + ConflictResolver的协同工作

Author: MOSS v9.0
Date: 2026-04-23
"""

import asyncio
import sys
sys.path.insert(0, '/workspace/moss')

from typing import Dict, List
from dataclasses import dataclass

from moss.core.agent_registry import create_registry, AgentStatus, HealthStatus
from moss.core.message_bus import create_message_bus, Message, MessageType, Priority
from moss.core.conflict_resolver import ConflictResolver, ConflictType


@dataclass
class Task:
    """任务定义"""
    task_id: str
    task_type: str
    priority: int
    requirements: List[str]
    payload: Dict


class FileOrganizerAgent:
    """文件整理Agent"""
    
    def __init__(self, agent_id: str, message_bus):
        self.agent_id = agent_id
        self.message_bus = message_bus
        self.processed_files = 0
        
    async def handle_message(self, message: Message):
        """处理消息"""
        if message.payload.get('task_type') == 'organize_files':
            files = message.payload.get('files', [])
            self.processed_files += len(files)
            print(f"  [{self.agent_id}] 整理了 {len(files)} 个文件")
            
            # 发送结果
            await self.message_bus.send_to_agent(
                target_agent_id=message.source,
                payload={
                    'task_id': message.payload.get('task_id'),
                    'status': 'completed',
                    'processed': len(files),
                    'by': self.agent_id
                },
                source=self.agent_id,
                message_type=MessageType.RESULT
            )


class SystemMonitorAgent:
    """系统监控Agent"""
    
    def __init__(self, agent_id: str, message_bus):
        self.agent_id = agent_id
        self.message_bus = message_bus
        self.alerts_sent = 0
        
    async def monitor(self):
        """监控循环"""
        while True:
            # 模拟监控系统
            cpu_usage = 75  # 模拟CPU使用率
            
            if cpu_usage > 70:
                self.alerts_sent += 1
                print(f"  [{self.agent_id}] 检测到CPU高负载: {cpu_usage}%")
                
                # 广播告警
                await self.message_bus.broadcast(
                    payload={
                        'alert_type': 'high_cpu',
                        'cpu_usage': cpu_usage,
                        'severity': 'warning'
                    },
                    source=self.agent_id
                )
            
            await asyncio.sleep(2)


class TaskCoordinatorAgent:
    """任务协调Agent"""
    
    def __init__(self, agent_id: str, registry, message_bus, conflict_resolver):
        self.agent_id = agent_id
        self.registry = registry
        self.message_bus = message_bus
        self.conflict_resolver = conflict_resolver
        self.task_queue: List[Task] = []
        self.completed_tasks = 0
        
    async def handle_message(self, message: Message):
        """处理消息"""
        if message.message_type == MessageType.RESULT:
            self.completed_tasks += 1
            print(f"  [{self.agent_id}] 收到任务完成通知: {message.payload}")
            
        elif message.payload.get('alert_type') == 'high_cpu':
            print(f"  [{self.agent_id}] 处理系统告警，调整任务分配")
            
    async def assign_task(self, task: Task):
        """分配任务"""
        print(f"\n[{self.agent_id}] 分配任务: {task.task_id} ({task.task_type})")
        
        # 查找有能力的Agent
        agents = await self.registry.find_by_capabilities(
            task.requirements,
            match_all=True
        )
        
        if not agents:
            print(f"  警告: 没有Agent能处理此任务")
            return
        
        # 选择健康的Agent
        healthy_agents = [a for a in agents if a.health == HealthStatus.HEALTHY]
        
        if len(healthy_agents) > 1:
            # 检测冲突
            actions = [
                {'agent_id': a.agent_id, 'resources': [task.task_id]}
                for a in healthy_agents
            ]
            
            conflict = self.conflict_resolver.detect_conflict(actions)
            if conflict:
                agent_info = {
                    a.agent_id: {
                        'priority': a.metadata.get('priority', 1),
                        'performance_score': a.performance_score
                    }
                    for a in healthy_agents
                }
                
                resolution = await self.conflict_resolver.resolve(conflict, agent_info)
                selected_agent = resolution.winner
            else:
                selected_agent = healthy_agents[0].agent_id
        else:
            selected_agent = healthy_agents[0].agent_id if healthy_agents else agents[0].agent_id
        
        print(f"  分配给: {selected_agent}")
        
        # 发送任务
        await self.message_bus.send_to_agent(
            target_agent_id=selected_agent,
            payload={
                'task_id': task.task_id,
                'task_type': task.task_type,
                **task.payload
            },
            source=self.agent_id,
            priority=Priority(task.priority),
            message_type=MessageType.TASK
        )


async def main():
    """主函数 - 多Agent协作演示"""
    print("=" * 70)
    print("MOSS v9.0 - 多Agent协作演示")
    print("=" * 70)
    
    # 初始化基础设施
    print("\n[1] 初始化基础设施...")
    registry = await create_registry()
    message_bus = await create_message_bus()
    conflict_resolver = ConflictResolver()
    print("   ✅ AgentRegistry + MessageBus + ConflictResolver 就绪")
    
    # 注册Agent并获取ID
    print("\n[2] 注册Agent到Registry...")
    
    file_agent_id_1 = await registry.register(
        name="FileOrganizer-1",
        capabilities=["file_management", "organization"],
        metadata={"priority": 2, "specialization": "documents"}
    )
    await registry.update_status(file_agent_id_1, AgentStatus.IDLE)
    await registry.update_health(file_agent_id_1, HealthStatus.HEALTHY)
    print(f"   ✅ FileOrganizer-1 注册完成: {file_agent_id_1}")
    
    file_agent_id_2 = await registry.register(
        name="FileOrganizer-2",
        capabilities=["file_management", "organization"],
        metadata={"priority": 1, "specialization": "images"}
    )
    await registry.update_status(file_agent_id_2, AgentStatus.IDLE)
    await registry.update_health(file_agent_id_2, HealthStatus.HEALTHY)
    print(f"   ✅ FileOrganizer-2 注册完成: {file_agent_id_2}")
    
    monitor_agent_id = await registry.register(
        name="SystemMonitor",
        capabilities=["monitoring", "alerting"],
        metadata={"priority": 3}
    )
    await registry.update_status(monitor_agent_id, AgentStatus.BUSY)
    await registry.update_health(monitor_agent_id, HealthStatus.HEALTHY)
    print(f"   ✅ SystemMonitor 注册完成: {monitor_agent_id}")
    
    coordinator_id = await registry.register(
        name="TaskCoordinator",
        capabilities=["coordination", "task_assignment"],
        metadata={"priority": 5}
    )
    await registry.update_status(coordinator_id, AgentStatus.BUSY)
    await registry.update_health(coordinator_id, HealthStatus.HEALTHY)
    print(f"   ✅ TaskCoordinator 注册完成: {coordinator_id}")
    
    # 创建Agent实例（使用注册返回的ID）
    print("\n[3] 创建Agent实例...")
    
    # 文件整理Agent
    file_agent_1 = FileOrganizerAgent(file_agent_id_1, message_bus)
    file_agent_2 = FileOrganizerAgent(file_agent_id_2, message_bus)
    
    # 系统监控Agent
    monitor_agent = SystemMonitorAgent(monitor_agent_id, message_bus)
    
    # 任务协调Agent
    coordinator_agent = TaskCoordinatorAgent(
        coordinator_id, registry, message_bus, conflict_resolver
    )
    
    # 订阅消息
    await message_bus.subscribe(file_agent_id_1, file_agent_1.handle_message, file_agent_id_1)
    await message_bus.subscribe(file_agent_id_2, file_agent_2.handle_message, file_agent_id_2)
    await message_bus.subscribe(coordinator_id, coordinator_agent.handle_message, coordinator_id)
    print("   ✅ 所有Agent消息订阅完成")
    
    # 显示统计
    stats = await registry.get_statistics()
    print(f"\n   当前系统: {stats['total_agents']} 个Agent, {stats['total_capabilities']} 种能力")
    
    # 演示场景1: 任务分配
    print("\n" + "=" * 70)
    print("【场景1】任务分配与执行")
    print("=" * 70)
    
    task1 = Task(
        task_id="task_001",
        task_type="organize_files",
        priority=2,
        requirements=["file_management", "organization"],
        payload={"files": ["doc1.pdf", "doc2.pdf", "doc3.pdf"]}
    )
    
    await coordinator_agent.assign_task(task1)
    await asyncio.sleep(1)
    
    task2 = Task(
        task_id="task_002",
        task_type="organize_files",
        priority=1,
        requirements=["file_management", "organization"],
        payload={"files": ["img1.jpg", "img2.jpg"]}
    )
    
    await coordinator_agent.assign_task(task2)
    await asyncio.sleep(1)
    
    # 演示场景2: 系统监控
    print("\n" + "=" * 70)
    print("【场景2】系统监控与告警")
    print("=" * 70)
    
    # 启动监控
    monitor_task = asyncio.create_task(monitor_agent.monitor())
    
    # 让监控运行一会儿
    await asyncio.sleep(3)
    monitor_task.cancel()
    
    try:
        await monitor_task
    except asyncio.CancelledError:
        pass
    
    print(f"\n   监控Agent发送了 {monitor_agent.alerts_sent} 次告警")
    
    # 演示场景3: 冲突解决
    print("\n" + "=" * 70)
    print("【场景3】资源冲突解决")
    print("=" * 70)
    
    # 模拟两个Agent竞争同一资源
    actions = [
        {'agent_id': file_agent_id_1, 'resources': ['storage_disk_1']},
        {'agent_id': file_agent_id_2, 'resources': ['storage_disk_1']},
    ]
    
    conflict = conflict_resolver.detect_conflict(actions)
    if conflict:
        print(f"   检测到冲突: {conflict.description}")
        
        agent_info = {
            file_agent_id_1: {'priority': 2, 'performance_score': 0.8},
            file_agent_id_2: {'priority': 1, 'performance_score': 0.7},
        }
        
        resolution = await conflict_resolver.resolve(conflict, agent_info)
        print(f"   解决结果: {resolution.explanation}")
        print(f"   获胜者: {resolution.winner}")
    
    # 总结
    print("\n" + "=" * 70)
    print("演示总结")
    print("=" * 70)
    
    print(f"✅ 文件整理Agent-1 处理了 {file_agent_1.processed_files} 个文件")
    print(f"✅ 文件整理Agent-2 处理了 {file_agent_2.processed_files} 个文件")
    print(f"✅ 系统监控Agent 发送了 {monitor_agent.alerts_sent} 次告警")
    print(f"✅ 任务协调Agent 完成了 {coordinator_agent.completed_tasks} 个任务")
    
    # 清理
    print("\n[4] 清理资源...")
    await registry.shutdown()
    await message_bus.shutdown()
    print("   ✅ 所有资源已释放")
    
    print("\n🎉 多Agent协作演示完成！")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n演示被用户中断")
