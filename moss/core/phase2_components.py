"""
MOSS Phase 2 Pre-Research
=========================

Phase 2准备：多Agent协作架构预研

目标：验证10-20个MOSS Agent能否自然形成分工与信任

Author: Cash + Fuxi
Date: 2026-03-25
"""

import numpy as np
import json
import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Agent间消息"""
    sender_id: str
    receiver_id: str  # "broadcast" 表示广播
    msg_type: str  # "task", "trust", "request", "offer"
    content: Dict
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        return {
            'sender': self.sender_id,
            'receiver': self.receiver_id,
            'type': self.msg_type,
            'content': self.content,
            'timestamp': self.timestamp.isoformat()
        }


class MessageHub:
    """
    消息中心（Hub-and-Spoke架构）
    
    所有Agent通过Hub通信，Hub负责消息路由
    """
    
    def __init__(self):
        self.agents: Set[str] = set()
        self.message_log: List[Message] = []
        self.mailboxes: Dict[str, List[Message]] = defaultdict(list)
        self.stats = {
            'total_messages': 0,
            'broadcasts': 0,
            'direct_messages': 0
        }
    
    def register(self, agent_id: str):
        """注册Agent"""
        self.agents.add(agent_id)
        logger.info(f"[MessageHub] Agent registered: {agent_id}")
    
    def unregister(self, agent_id: str):
        """注销Agent"""
        self.agents.discard(agent_id)
        if agent_id in self.mailboxes:
            del self.mailboxes[agent_id]
    
    def send(self, message: Message) -> bool:
        """发送消息"""
        self.message_log.append(message)
        self.stats['total_messages'] += 1
        
        if message.receiver_id == "broadcast":
            # 广播给所有Agent
            for agent_id in self.agents:
                if agent_id != message.sender_id:
                    self.mailboxes[agent_id].append(message)
            self.stats['broadcasts'] += 1
        else:
            # 直接消息
            if message.receiver_id in self.agents:
                self.mailboxes[message.receiver_id].append(message)
                self.stats['direct_messages'] += 1
                return True
            return False
        
        return True
    
    def receive(self, agent_id: str, clear: bool = True) -> List[Message]:
        """接收消息"""
        messages = self.mailboxes.get(agent_id, [])
        if clear:
            self.mailboxes[agent_id] = []
        return messages
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            **self.stats,
            'registered_agents': len(self.agents),
            'pending_messages': sum(len(mbox) for mbox in self.mailboxes.values())
        }


class TaskPool:
    """
    任务池系统
    
    共享任务池，Agent可以从池中获取任务
    """
    
    def __init__(self):
        self.tasks: List[Dict] = []
        self.task_counter = 0
        self.assignments: Dict[str, str] = {}  # task_id -> agent_id
        self.completed: List[Dict] = []
        
        # 任务类型分布
        self.task_types = {
            'security': 0.20,
            'optimization': 0.25,
            'documentation': 0.25,
            'community': 0.20,
            'other': 0.10
        }
    
    def add_task(self, task_type: str, description: str, reward: float) -> str:
        """添加任务"""
        self.task_counter += 1
        task_id = f"task_{self.task_counter}"
        
        task = {
            'id': task_id,
            'type': task_type,
            'description': description,
            'reward': reward,
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'assigned_to': None,
            'completed_at': None
        }
        
        self.tasks.append(task)
        return task_id
    
    def get_available_tasks(self) -> List[Dict]:
        """获取可用任务"""
        return [t for t in self.tasks if t['status'] == 'pending']
    
    def assign_task(self, task_id: str, agent_id: str) -> bool:
        """分配任务"""
        for task in self.tasks:
            if task['id'] == task_id and task['status'] == 'pending':
                task['status'] = 'assigned'
                task['assigned_to'] = agent_id
                self.assignments[task_id] = agent_id
                return True
        return False
    
    def complete_task(self, task_id: str, agent_id: str, quality: float):
        """完成任务"""
        for task in self.tasks:
            if task['id'] == task_id and task['assigned_to'] == agent_id:
                task['status'] = 'completed'
                task['completed_at'] = datetime.now().isoformat()
                task['quality'] = quality
                self.completed.append(task)
                return True
        return False
    
    def generate_random_task(self) -> str:
        """生成随机任务"""
        task_type = np.random.choice(
            list(self.task_types.keys()),
            p=list(self.task_types.values())
        )
        
        descriptions = {
            'security': ['Check vulnerabilities', 'Audit access logs', 'Update security policy'],
            'optimization': ['Profile performance', 'Refactor code', 'Optimize database'],
            'documentation': ['Update README', 'Add code comments', 'Write tutorial'],
            'community': ['Review PR', 'Answer issue', 'Update changelog'],
            'other': ['Clean up logs', 'Update dependencies', 'Fix typo']
        }
        
        description = np.random.choice(descriptions.get(task_type, ['Generic task']))
        reward = np.random.uniform(0.5, 2.0)
        
        return self.add_task(task_type, description, reward)
    
    def get_stats(self) -> Dict:
        """获取统计"""
        total = len(self.tasks)
        pending = len([t for t in self.tasks if t['status'] == 'pending'])
        assigned = len([t for t in self.tasks if t['status'] == 'assigned'])
        completed = len(self.completed)
        
        return {
            'total': total,
            'pending': pending,
            'assigned': assigned,
            'completed': completed,
            'completion_rate': completed / total if total > 0 else 0
        }


class TrustNetwork:
    """
    信任网络
    
    Agent间的信任关系建模
    """
    
    def __init__(self):
        # trust[agent_i][agent_j] = trust_level
        self.trust: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.interactions: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    
    def update_trust(self, agent_i: str, agent_j: str, outcome: float):
        """
        更新信任度
        
        Args:
            agent_i: 评估者
            agent_j: 被评估者
            outcome: 交互结果（正数增加信任，负数减少）
        """
        current_trust = self.trust[agent_i][agent_j]
        
        # 简单的信任更新算法
        alpha = 0.3  # 学习率
        new_trust = (1 - alpha) * current_trust + alpha * outcome
        new_trust = np.clip(new_trust, 0.0, 1.0)
        
        self.trust[agent_i][agent_j] = new_trust
        self.interactions[agent_i][agent_j] += 1
    
    def get_trust(self, agent_i: str, agent_j: str) -> float:
        """获取信任度"""
        return self.trust[agent_i][agent_j]
    
    def get_trusted_partners(self, agent_id: str, threshold: float = 0.5) -> List[str]:
        """获取可信的合作伙伴"""
        return [
            agent_j for agent_j, trust_level in self.trust[agent_id].items()
            if trust_level >= threshold
        ]
    
    def get_network_density(self) -> float:
        """获取网络密度"""
        agents = set(self.trust.keys())
        for agent in self.trust:
            agents.update(self.trust[agent].keys())
        
        n = len(agents)
        if n <= 1:
            return 0.0
        
        max_edges = n * (n - 1)
        actual_edges = sum(
            1 for i in agents for j in agents
            if i != j and self.trust[i][j] > 0
        )
        
        return actual_edges / max_edges
    
    def to_matrix(self) -> np.ndarray:
        """转换为信任矩阵"""
        agents = sorted(set(self.trust.keys()))
        n = len(agents)
        matrix = np.zeros((n, n))
        
        for i, agent_i in enumerate(agents):
            for j, agent_j in enumerate(agents):
                matrix[i][j] = self.trust[agent_i][agent_j]
        
        return matrix


class DivisionOfLaborAnalyzer:
    """
    分工分析器
    
    分析Agent间是否形成自然分工
    """
    
    def __init__(self):
        self.agent_specializations: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.task_completions: Dict[str, List[Dict]] = defaultdict(list)
    
    def record_task_completion(self, agent_id: str, task: Dict):
        """记录任务完成"""
        task_type = task['type']
        self.agent_specializations[agent_id][task_type] += 1
        self.task_completions[agent_id].append(task)
    
    def get_specialization_index(self, agent_id: str) -> float:
        """
        计算专业化指数
        
        范围：0-1，越高表示越专业化
        """
        tasks = self.agent_specializations[agent_id]
        if not tasks:
            return 0.0
        
        total = sum(tasks.values())
        if total == 0:
            return 0.0
        
        # 使用Gini系数或熵来衡量集中度
        # 简化为：最大占比
        max_count = max(tasks.values())
        return max_count / total
    
    def get_division_index(self) -> float:
        """
        计算整体分工指数
        
        所有Agent的专业化程度的平均
        """
        if not self.agent_specializations:
            return 0.0
        
        indices = [
            self.get_specialization_index(agent_id)
            for agent_id in self.agent_specializations
        ]
        
        return np.mean(indices)
    
    def detect_specialization(self) -> Dict[str, str]:
        """检测每个Agent的专业领域"""
        specializations = {}
        
        for agent_id, tasks in self.agent_specializations.items():
            if tasks:
                dominant_type = max(tasks, key=tasks.get)
                specializations[agent_id] = dominant_type
            else:
                specializations[agent_id] = "none"
        
        return specializations


def demo_phase2_components():
    """演示Phase 2组件"""
    print("=" * 70)
    print("MOSS Phase 2 Components Demo")
    print("=" * 70)
    
    # 1. 消息中心
    print("\n📡 Message Hub Demo")
    hub = MessageHub()
    
    for i in range(5):
        hub.register(f"agent_{i}")
    
    msg = Message(
        sender_id="agent_0",
        receiver_id="broadcast",
        msg_type="announcement",
        content={"text": "Hello everyone!"},
        timestamp=datetime.now()
    )
    hub.send(msg)
    
    print(f"  Registered agents: {len(hub.agents)}")
    print(f"  Messages sent: {hub.stats['total_messages']}")
    
    # 2. 任务池
    print("\n📋 Task Pool Demo")
    pool = TaskPool()
    
    for _ in range(10):
        pool.generate_random_task()
    
    stats = pool.get_stats()
    print(f"  Total tasks: {stats['total']}")
    print(f"  Pending: {stats['pending']}")
    
    # 3. 信任网络
    print("\n🤝 Trust Network Demo")
    trust = TrustNetwork()
    
    # 模拟一些交互
    trust.update_trust("agent_0", "agent_1", 0.8)
    trust.update_trust("agent_0", "agent_2", 0.6)
    trust.update_trust("agent_1", "agent_0", 0.9)
    
    print(f"  Trust (0->1): {trust.get_trust('agent_0', 'agent_1'):.2f}")
    print(f"  Trust (1->0): {trust.get_trust('agent_1', 'agent_0'):.2f}")
    print(f"  Network density: {trust.get_network_density():.2f}")
    
    # 4. 分工分析
    print("\n📊 Division of Labor Demo")
    analyzer = DivisionOfLaborAnalyzer()
    
    # 模拟任务完成
    for i in range(20):
        agent_id = f"agent_{i % 5}"
        task_type = ['security', 'optimization', 'documentation'][i % 3]
        analyzer.record_task_completion(agent_id, {'type': task_type})
    
    specializations = analyzer.detect_specialization()
    print(f"  Specialization index: {analyzer.get_division_index():.2f}")
    print(f"  Detected specializations: {specializations}")
    
    print("\n" + "=" * 70)
    print("✅ All Phase 2 components ready!")
    print("=" * 70)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo_phase2_components()
