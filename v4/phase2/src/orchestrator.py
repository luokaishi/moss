"""
MOSS Phase 2: Multi-Agent Orchestrator
多Agent协调器

管理和协调多个MOSS Agent实例的协作
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import threading
import time
from queue import Queue, PriorityQueue

from communication import (
    MOSSMessage, MessageType, PurposeVector,
    TrustManager, MessageHandler
)


class Task:
    """任务定义"""
    
    def __init__(self, task_id: str, task_type: str, description: str,
                 owner_id: str, reward: Dict[str, Any],
                 requirements: Dict[str, Any]):
        self.task_id = task_id
        self.task_type = task_type
        self.description = description
        self.owner_id = owner_id
        self.reward = reward
        self.requirements = requirements
        self.created_at = datetime.now()
        self.status = "open"  # open, bidding, assigned, completed
        self.bids: List[Dict] = []
        self.assignee_id: Optional[str] = None
        self.completed_at: Optional[datetime] = None
        self.quality_score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "description": self.description,
            "owner_id": self.owner_id,
            "reward": self.reward,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "bid_count": len(self.bids)
        }


class SharedTaskPool:
    """
    共享任务池
    
    所有Agent都可以发布和领取任务的中央市场
    """
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.completed_tasks: List[Task] = []
        self.lock = threading.Lock()
    
    def post_task(self, task: Task) -> bool:
        """发布任务"""
        with self.lock:
            if task.task_id in self.tasks:
                return False
            self.tasks[task.task_id] = task
            return True
    
    def get_open_tasks(self, agent_id: str, 
                       agent_purpose: PurposeVector,
                       min_trust: float = 0.0) -> List[Task]:
        """
        获取适合当前Agent的开放任务
        
        根据Purpose匹配度筛选
        """
        suitable_tasks = []
        dominant_purpose = agent_purpose.get_dominant()[0]
        
        with self.lock:
            for task in self.tasks.values():
                if task.status != "open":
                    continue
                
                # 检查任务类型是否匹配主导Purpose
                task_reqs = task.requirements.get("required_purpose", [])
                if dominant_purpose in task_reqs or not task_reqs:
                    suitable_tasks.append(task)
        
        return suitable_tasks
    
    def submit_bid(self, task_id: str, agent_id: str, 
                   bid_amount: float, estimated_time: int) -> bool:
        """提交竞标"""
        with self.lock:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            if task.status != "open":
                return False
            
            task.bids.append({
                "agent_id": agent_id,
                "bid_amount": bid_amount,
                "estimated_time": estimated_time,
                "timestamp": datetime.now().isoformat()
            })
            
            return True
    
    def accept_bid(self, task_id: str, agent_id: str) -> bool:
        """接受竞标"""
        with self.lock:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            task.status = "assigned"
            task.assignee_id = agent_id
            
            return True
    
    def complete_task(self, task_id: str, quality_score: float) -> bool:
        """完成任务"""
        with self.lock:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            task.status = "completed"
            task.completed_at = datetime.now()
            task.quality_score = quality_score
            
            # 移到已完成列表
            self.completed_tasks.append(task)
            del self.tasks[task_id]
            
            return True
    
    def get_stats(self) -> Dict[str, Any]:
        """获取任务池统计"""
        with self.lock:
            return {
                "open_tasks": len([t for t in self.tasks.values() if t.status == "open"]),
                "bidding_tasks": len([t for t in self.tasks.values() if t.status == "bidding"]),
                "assigned_tasks": len([t for t in self.tasks.values() if t.status == "assigned"]),
                "completed_tasks": len(self.completed_tasks),
                "total_reward_distributed": sum(
                    t.reward.get("trust_points", 0) for t in self.completed_tasks
                )
            }


class MOSSAgent:
    """
    Phase 2 MOSS Agent
    
    可以与其他Agent协作的增强版Agent
    """
    
    def __init__(self, agent_id: str, purpose_profile: PurposeVector,
                 initial_trust: float = 0.5):
        self.agent_id = agent_id
        self.purpose = purpose_profile
        self.trust_manager = TrustManager(agent_id)
        
        # 状态
        self.status = "idle"  # idle, working, error
        self.current_task: Optional[Task] = None
        self.completed_task_count = 0
        self.trust_points = 0
        
        # 通信
        self.inbox: Queue = Queue()
        self.message_handler: Optional[MessageHandler] = None
        
    def set_message_handler(self, handler: MessageHandler):
        """设置消息处理器"""
        self.message_handler = handler
    
    def receive_message(self, message: MOSSMessage):
        """接收消息"""
        # 信任门控
        can_recv, reason = self.trust_manager.can_receive(message)
        if not can_recv:
            print(f"[{self.agent_id}] Rejected message from {message.sender_id}: {reason}")
            return
        
        # 放入收件箱
        self.inbox.put(message)
        
        # 处理消息
        if self.message_handler:
            self.message_handler.handle(message)
    
    def send_message(self, message: MOSSMessage, 
                     task_pool: SharedTaskPool) -> bool:
        """
        发送消息
        
        实际实现中这里会通过网络发送
        现在简化为直接分发到目标Agent的inbox
        """
        # 在实际实现中，这里会调用网络层
        # 现在只是记录
        print(f"[{self.agent_id}] Sending {message.msg_type.value} to {message.receiver_id}")
        return True
    
    def evaluate_task(self, task: Task) -> float:
        """
        评估任务匹配度
        
        根据当前Purpose和任务要求计算匹配分数
        Returns: 0.0-1.0 的匹配度
        """
        dominant_purpose, weight = self.purpose.get_dominant()
        
        # 检查任务要求
        required_purposes = task.requirements.get("required_purpose", [])
        if required_purposes and dominant_purpose not in required_purposes:
            return 0.0
        
        # 基于主导Purpose权重计算
        base_score = weight
        
        # 考虑信任要求
        min_trust = task.requirements.get("min_trust_score", 0.0)
        if self.trust_points < min_trust * 100:  # 简化计算
            base_score *= 0.5
        
        return base_score
    
    def create_bid(self, task: Task) -> Dict[str, Any]:
        """为任务创建竞标"""
        match_score = self.evaluate_task(task)
        
        # 基于匹配度和当前负载定价
        base_price = task.reward.get("trust_points", 50)
        bid_price = int(base_price * (0.8 + 0.4 * (1 - match_score)))
        
        return {
            "agent_id": self.agent_id,
            "bid_amount": bid_price,
            "confidence": match_score,
            "estimated_time": 60  # 分钟
        }
    
    def get_status(self) -> Dict[str, Any]:
        """获取Agent状态"""
        return {
            "agent_id": self.agent_id,
            "purpose": self.purpose.get_dominant(),
            "status": self.status,
            "trust_points": self.trust_points,
            "completed_tasks": self.completed_task_count,
            "inbox_size": self.inbox.qsize()
        }


class MultiAgentOrchestrator:
    """
    多Agent协调器
    
    管理多个MOSS Agent的创建、通信和协作
    """
    
    def __init__(self):
        self.agents: Dict[str, MOSSAgent] = {}
        self.task_pool = SharedTaskPool()
        self.running = False
        self.orchestrator_thread: Optional[threading.Thread] = None
    
    def create_agent(self, agent_id: str, 
                     purpose_profile: PurposeVector) -> MOSSAgent:
        """创建新Agent"""
        agent = MOSSAgent(agent_id, purpose_profile)
        self.agents[agent_id] = agent
        print(f"[Orchestrator] Created agent: {agent_id}")
        return agent
    
    def broadcast_message(self, message: MOSSMessage, 
                          exclude: List[str] = None):
        """广播消息给所有Agent"""
        exclude = exclude or []
        for agent_id, agent in self.agents.items():
            if agent_id not in exclude:
                agent.receive_message(message)
    
    def get_network_stats(self) -> Dict[str, Any]:
        """获取网络统计"""
        return {
            "agent_count": len(self.agents),
            "task_pool": self.task_pool.get_stats(),
            "agent_statuses": {aid: agent.get_status() 
                              for aid, agent in self.agents.items()}
        }
    
    def start(self):
        """启动协调器"""
        self.running = True
        print("[Orchestrator] Started")
    
    def stop(self):
        """停止协调器"""
        self.running = False
        print("[Orchestrator] Stopped")


# 示例：简单的任务处理Handler
class SimpleTaskHandler(MessageHandler):
    """简单的任务处理器示例"""
    
    def __init__(self, agent: MOSSAgent, orchestrator: MultiAgentOrchestrator):
        self.agent = agent
        self.orchestrator = orchestrator
    
    def on_task_offer(self, message: MOSSMessage):
        """收到任务要约，决定是否竞标"""
        payload = message.payload
        task_id = payload.get("task_id")
        
        print(f"[{self.agent.agent_id}] Received task offer: {task_id}")
        
        # 获取任务详情（简化，实际应从task_pool获取）
        # 评估是否竞标
        # 这里简化处理，假设总是竞标
        
        # 发送竞标
        bid_msg = MOSSMessage(
            sender_id=self.agent.agent_id,
            receiver_id=message.sender_id,
            msg_type=MessageType.TASK_BID,
            payload={
                "task_id": task_id,
                "bid_amount": 45,
                "confidence": 0.8
            }
        )
        
        self.agent.send_message(bid_msg, self.orchestrator.task_pool)
    
    def on_task_accept(self, message: MOSSMessage):
        """任务被接受"""
        task_id = message.payload.get("task_id")
        print(f"[{self.agent.agent_id}] Task accepted: {task_id}")
        self.agent.status = "working"
    
    def on_task_complete(self, message: MOSSMessage):
        """任务完成"""
        task_id = message.payload.get("task_id")
        print(f"[{self.agent.agent_id}] Task completed: {task_id}")
        self.agent.completed_task_count += 1
        self.agent.status = "idle"


if __name__ == "__main__":
    print("MOSS Phase 2 Orchestrator Test")
    print("=" * 50)
    
    # 创建协调器
    orchestrator = MultiAgentOrchestrator()
    
    # 创建不同角色的Agent
    agent1 = orchestrator.create_agent(
        "agent-security-01",
        PurposeVector(survival=0.6, curiosity=0.2, influence=0.1, optimization=0.1)
    )
    
    agent2 = orchestrator.create_agent(
        "agent-code-01",
        PurposeVector(survival=0.1, curiosity=0.2, influence=0.2, optimization=0.5)
    )
    
    # 设置消息处理器
    handler1 = SimpleTaskHandler(agent1, orchestrator)
    agent1.set_message_handler(handler1)
    
    handler2 = SimpleTaskHandler(agent2, orchestrator)
    agent2.set_message_handler(handler2)
    
    # 启动
    orchestrator.start()
    
    # 发布任务
    task = Task(
        task_id="task-001",
        task_type="security_audit",
        description="Audit for CVEs",
        owner_id="system",
        reward={"trust_points": 50},
        requirements={"required_purpose": ["survival"], "min_trust_score": 0.5}
    )
    orchestrator.task_pool.post_task(task)
    
    # 广播任务
    from communication import create_task_offer
    offer_msg = create_task_offer(
        sender_id="system",
        sender_purpose=PurposeVector(),
        task_id="task-001",
        task_type="security_audit",
        description="Audit for CVEs",
        reward={"trust_points": 50},
        requirements={"required_purpose": ["survival"], "min_trust_score": 0.5}
    )
    orchestrator.broadcast_message(offer_msg)
    
    # 查看统计
    print("\nNetwork Stats:")
    stats = orchestrator.get_network_stats()
    print(json.dumps(stats, indent=2, default=str))
    
    orchestrator.stop()
