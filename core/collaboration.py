#!/usr/bin/env python3
"""
MOSS v5.4 - Multi-Agent Collaboration Module
多 Agent 协作协调器

核心功能:
- 任务分配与协调
- 知识共享机制
- 集体决策
- 协作效率评估

Author: MOSS Project
Date: 2026-04-03
Version: 5.4.0-dev
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class CollaborationMode(Enum):
    """协作模式"""
    CENTRALIZED = "centralized"      # 集中式协调
    DECENTRALIZED = "decentralized"  # 去中心化协作
    HYBRID = "hybrid"                # 混合模式


@dataclass
class Task:
    """任务定义"""
    id: str
    description: str
    difficulty: float  # 0-1
    priority: float    # 0-1
    required_skills: List[str]
    status: TaskStatus = TaskStatus.PENDING
    assigned_to: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    reward: float = 1.0
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'description': self.description,
            'difficulty': self.difficulty,
            'priority': self.priority,
            'required_skills': self.required_skills,
            'status': self.status.value,
            'assigned_to': self.assigned_to,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'reward': self.reward
        }


@dataclass
class AgentCapability:
    """Agent 能力定义"""
    agent_id: str
    skills: Dict[str, float]  # skill_name -> proficiency (0-1)
    availability: float       # 0-1 (1=完全可用)
    current_load: float       # 0-1 (0=无负载)
    
    def match_task(self, task: Task) -> float:
        """计算与任务的匹配度"""
        if not task.required_skills:
            return self.availability * (1 - self.current_load)
        
        # 计算技能匹配度
        skill_matches = []
        for skill in task.required_skills:
            proficiency = self.skills.get(skill, 0)
            skill_matches.append(proficiency)
        
        avg_skill = np.mean(skill_matches) if skill_matches else 0
        return avg_skill * self.availability * (1 - self.current_load)


class CollaborationCoordinator:
    """
    协作协调器
    
    管理多 Agent 协作的核心逻辑
    """
    
    def __init__(self, mode: CollaborationMode = CollaborationMode.HYBRID):
        self.mode = mode
        self.agents: Dict[str, AgentCapability] = {}
        self.tasks: Dict[str, Task] = {}
        self.collaboration_history: List[Dict] = []
        
        # 统计指标
        self.stats = {
            'tasks_assigned': 0,
            'tasks_completed': 0,
            'avg_collaboration_efficiency': 0.0,
            'knowledge_sharing_events': 0
        }
    
    def register_agent(self, agent_id: str, skills: Dict[str, float]):
        """注册 Agent"""
        self.agents[agent_id] = AgentCapability(
            agent_id=agent_id,
            skills=skills,
            availability=1.0,
            current_load=0.0
        )
    
    def add_task(self, task: Task):
        """添加任务"""
        self.tasks[task.id] = task
    
    def assign_tasks(self) -> Dict[str, List[str]]:
        """
        分配任务给 Agent
        
        Returns:
            {agent_id: [task_ids]}
        """
        assignments = {agent_id: [] for agent_id in self.agents}
        
        # 按优先级排序任务
        pending_tasks = [
            t for t in self.tasks.values() 
            if t.status == TaskStatus.PENDING
        ]
        pending_tasks.sort(key=lambda t: t.priority, reverse=True)
        
        for task in pending_tasks:
            # 找到最合适的 Agent
            best_agent = None
            best_score = -1
            
            for agent_id, agent in self.agents.items():
                if agent.availability < 0.1:  # 跳过不可用 Agent
                    continue
                
                score = agent.match_task(task)
                if score > best_score:
                    best_score = score
                    best_agent = agent_id
            
            if best_agent and best_score > 0.3:  # 最低匹配阈值
                task.assigned_to = best_agent
                task.status = TaskStatus.IN_PROGRESS
                task.started_at = datetime.now()
                assignments[best_agent].append(task.id)
                self.stats['tasks_assigned'] += 1
                
                # 更新 Agent 负载
                self.agents[best_agent].current_load += task.difficulty * 0.1
        
        return assignments
    
    def complete_task(self, task_id: str, success: bool = True):
        """完成任务"""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        task.completed_at = datetime.now()
        
        if success:
            self.stats['tasks_completed'] += 1
        
        # 释放 Agent 负载
        if task.assigned_to and task.assigned_to in self.agents:
            self.agents[task.assigned_to].current_load = max(
                0, 
                self.agents[task.assigned_to].current_load - task.difficulty * 0.1
            )
    
    def share_knowledge(self, from_agent: str, to_agents: List[str], knowledge: Dict):
        """知识共享"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'from': from_agent,
            'to': to_agents,
            'knowledge': knowledge
        }
        self.collaboration_history.append(event)
        self.stats['knowledge_sharing_events'] += 1
    
    def calculate_efficiency(self) -> float:
        """计算协作效率"""
        if self.stats['tasks_assigned'] == 0:
            return 0.0
        
        completion_rate = (
            self.stats['tasks_completed'] / 
            self.stats['tasks_assigned']
        )
        
        # 考虑平均匹配质量
        avg_match_quality = 0.5  # 简化
        
        efficiency = completion_rate * 0.7 + avg_match_quality * 0.3
        self.stats['avg_collaboration_efficiency'] = efficiency
        return efficiency
    
    def get_status(self) -> Dict:
        """获取协作状态"""
        return {
            'mode': self.mode.value,
            'agents': len(self.agents),
            'tasks': {
                'total': len(self.tasks),
                'pending': sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING),
                'in_progress': sum(1 for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS),
                'completed': sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED),
                'failed': sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)
            },
            'stats': self.stats,
            'efficiency': self.calculate_efficiency()
        }


class CollectiveDecision:
    """
    集体决策机制
    
    支持多种投票和共识算法
    """
    
    def __init__(self):
        self.votes: Dict[str, Dict[str, float]] = {}  # proposal_id -> {agent_id: vote}
    
    def propose(self, proposal_id: str, description: str):
        """提出议案"""
        self.votes[proposal_id] = {}
    
    def vote(self, proposal_id: str, agent_id: str, vote: float):
        """投票 (0-1)"""
        if proposal_id in self.votes:
            self.votes[proposal_id][agent_id] = vote
    
    def get_result(self, proposal_id: str) -> Tuple[bool, float]:
        """
        获取投票结果
        
        Returns:
            (通过与否，平均支持度)
        """
        if proposal_id not in self.votes:
            return False, 0.0
        
        votes = list(self.votes[proposal_id].values())
        if not votes:
            return False, 0.0
        
        avg_support = np.mean(votes)
        passed = avg_support > 0.5
        
        return passed, avg_support


# 测试代码
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v5.4 - Collaboration Module Test")
    print("=" * 60)
    
    # 创建协调器
    coordinator = CollaborationCoordinator()
    
    # 注册 Agent
    coordinator.register_agent("agent_1", {
        'coding': 0.9,
        'analysis': 0.7,
        'communication': 0.5
    })
    coordinator.register_agent("agent_2", {
        'coding': 0.6,
        'analysis': 0.9,
        'communication': 0.8
    })
    
    # 添加任务
    coordinator.add_task(Task(
        id="task_1",
        description="Implement feature X",
        difficulty=0.7,
        priority=0.9,
        required_skills=['coding'],
        reward=2.0
    ))
    
    # 分配任务
    assignments = coordinator.assign_tasks()
    print(f"\n任务分配结果：{assignments}")
    
    # 完成任务
    if assignments['agent_1']:
        coordinator.complete_task(assignments['agent_1'][0], success=True)
    
    # 知识共享
    coordinator.share_knowledge(
        from_agent="agent_1",
        to_agents=["agent_2"],
        knowledge={'tip': 'Use caching for better performance'}
    )
    
    # 获取状态
    status = coordinator.get_status()
    print(f"\n协作状态:")
    print(f"  Agent 数量：{status['agents']}")
    print(f"  任务总数：{status['tasks']['total']}")
    print(f"  已完成：{status['tasks']['completed']}")
    print(f"  协作效率：{status['efficiency']:.2f}")
    print(f"  知识共享：{status['stats']['knowledge_sharing_events']} 次")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)
