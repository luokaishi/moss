#!/usr/bin/env python3
"""
MOSS v5.5 - Dynamic Agent Management
动态 Agent 管理系统

核心功能:
- 动态 Agent 创建/销毁
- 自适应负载均衡
- 故障恢复机制
- 弹性扩展

Author: MOSS Project
Date: 2026-04-03
Version: 5.5.0-dev
"""

import uuid
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class AgentStatus(Enum):
    """Agent 状态"""
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


@dataclass
class AgentConfig:
    """Agent 配置"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    skills: Dict[str, float] = field(default_factory=dict)
    max_load: float = 0.8
    auto_scale: bool = True
    created_at: datetime = field(default_factory=datetime.now)


class DynamicAgent:
    """动态 Agent"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.id = config.id
        self.skills = config.skills
        self.max_load = config.max_load
        
        self.status = AgentStatus.IDLE
        self.current_load = 0.0
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.last_active = datetime.now()
    
    def assign_task(self, difficulty: float) -> bool:
        """分配任务"""
        if self.status == AgentStatus.OFFLINE:
            return False
        
        if self.current_load + difficulty > self.max_load:
            return False
        
        self.current_load += difficulty
        self.status = AgentStatus.BUSY
        self.last_active = datetime.now()
        return True
    
    def complete_task(self, success: bool):
        """完成任务"""
        self.current_load = max(0, self.current_load - 0.1)
        
        if success:
            self.tasks_completed += 1
        else:
            self.tasks_failed += 1
        
        if self.current_load < 0.1:
            self.status = AgentStatus.IDLE
        
        self.last_active = datetime.now()
    
    def get_efficiency(self) -> float:
        """计算效率"""
        total = self.tasks_completed + self.tasks_failed
        if total == 0:
            return 0.5
        return self.tasks_completed / total
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'status': self.status.value,
            'current_load': self.current_load,
            'skills': self.skills,
            'efficiency': self.get_efficiency(),
            'tasks_completed': self.tasks_completed,
            'last_active': self.last_active.isoformat()
        }


class DynamicAgentManager:
    """
    动态 Agent 管理器
    
    管理 Agent 的生命周期
    """
    
    def __init__(self, min_agents: int = 5, max_agents: int = 100):
        self.min_agents = min_agents
        self.max_agents = max_agents
        self.agents: Dict[str, DynamicAgent] = {}
        
        self.stats = {
            'agents_created': 0,
            'agents_destroyed': 0,
            'auto_scale_events': 0,
            'recovery_events': 0
        }
    
    def create_agent(self, skills: Optional[Dict[str, float]] = None) -> str:
        """创建 Agent"""
        if len(self.agents) >= self.max_agents:
            raise ValueError(f"Reached max agents: {self.max_agents}")
        
        # 默认技能
        if not skills:
            skill_pool = ['coding', 'analysis', 'communication', 'testing']
            skills = {
                skill: np.random.uniform(0.5, 1.0)
                for skill in np.random.choice(skill_pool, size=3, replace=False)
            }
        
        config = AgentConfig(skills=skills)
        agent = DynamicAgent(config)
        self.agents[agent.id] = agent
        
        self.stats['agents_created'] += 1
        
        return agent.id
    
    def destroy_agent(self, agent_id: str) -> bool:
        """销毁 Agent"""
        if agent_id not in self.agents:
            return False
        
        if len(self.agents) <= self.min_agents:
            raise ValueError(f"Cannot go below min agents: {self.min_agents}")
        
        agent = self.agents[agent_id]
        if agent.status == AgentStatus.BUSY:
            return False  # 忙碌中不能销毁
        
        del self.agents[agent_id]
        self.stats['agents_destroyed'] += 1
        
        return True
    
    def get_available_agents(self) -> List[DynamicAgent]:
        """获取可用 Agent"""
        return [
            agent for agent in self.agents.values()
            if agent.status == AgentStatus.IDLE
        ]
    
    def auto_scale(self, current_load: float, task_queue_size: int):
        """
        自动扩展/收缩
        
        Args:
            current_load: 当前平均负载
            task_queue_size: 任务队列大小
        """
        # 高负载 + 大队列 → 扩展
        if current_load > 0.7 and task_queue_size > 10:
            if len(self.agents) < self.max_agents:
                self.create_agent()
                self.stats['auto_scale_events'] += 1
                print(f"   📈 扩展：Agent 数量 {len(self.agents)}")
        
        # 低负载 → 收缩
        elif current_load < 0.2 and task_queue_size < 5:
            if len(self.agents) > self.min_agents:
                # 销毁效率最低的 Agent
                agents_by_efficiency = sorted(
                    self.agents.values(),
                    key=lambda a: a.get_efficiency()
                )
                
                for agent in agents_by_efficiency:
                    if agent.status == AgentStatus.IDLE:
                        self.destroy_agent(agent.id)
                        self.stats['auto_scale_events'] += 1
                        print(f"   📉 收缩：Agent 数量 {len(self.agents)}")
                        break
    
    def recover_failed_agents(self) -> int:
        """恢复故障 Agent"""
        recovered = 0
        
        for agent in list(self.agents.values()):
            if agent.status == AgentStatus.ERROR:
                # 重置状态
                agent.status = AgentStatus.IDLE
                agent.current_load = 0.0
                recovered += 1
        
        if recovered > 0:
            self.stats['recovery_events'] += 1
            print(f"   🔄 恢复：{recovered} 个 Agent")
        
        return recovered
    
    def get_status(self) -> Dict:
        """获取管理器状态"""
        if not self.agents:
            return {
                'total_agents': 0,
                'stats': self.stats
            }
        
        efficiencies = [a.get_efficiency() for a in self.agents.values()]
        loads = [a.current_load for a in self.agents.values()]
        
        return {
            'total_agents': len(self.agents),
            'min_agents': self.min_agents,
            'max_agents': self.max_agents,
            'avg_efficiency': np.mean(efficiencies),
            'avg_load': np.mean(loads),
            'status_distribution': {
                'idle': sum(1 for a in self.agents.values() if a.status == AgentStatus.IDLE),
                'busy': sum(1 for a in self.agents.values() if a.status == AgentStatus.BUSY),
                'offline': sum(1 for a in self.agents.values() if a.status == AgentStatus.OFFLINE),
                'error': sum(1 for a in self.agents.values() if a.status == AgentStatus.ERROR)
            },
            'stats': self.stats
        }


class AdaptiveLoadBalancer:
    """
    自适应负载均衡器
    
    动态分配任务给最优 Agent
    """
    
    def __init__(self, manager: DynamicAgentManager):
        self.manager = manager
        self.assignment_history: List[Dict] = []
        
        self.stats = {
            'tasks_assigned': 0,
            'load_balance_score': 0.0
        }
    
    def assign_task(self, task: Dict) -> Optional[str]:
        """分配任务给最优 Agent"""
        available = self.manager.get_available_agents()
        
        if not available:
            return None
        
        required_skills = task.get('required_skills', [])
        difficulty = task.get('difficulty', 0.5)
        
        # 计算每个 Agent 的得分
        best_agent = None
        best_score = -1
        
        for agent in available:
            score = self._calculate_score(agent, required_skills, difficulty)
            if score > best_score:
                best_score = score
                best_agent = agent
        
        if best_agent:
            if best_agent.assign_task(difficulty):
                self.stats['tasks_assigned'] += 1
                self.assignment_history.append({
                    'task': task.get('id', 'unknown'),
                    'agent': best_agent.id,
                    'score': best_score,
                    'timestamp': datetime.now().isoformat()
                })
                return best_agent.id
        
        return None
    
    def _calculate_score(self, agent: DynamicAgent, 
                        required_skills: List[str], 
                        difficulty: float) -> float:
        """计算 Agent 得分"""
        # 1. 技能匹配 (50%)
        if required_skills:
            skill_matches = [
                agent.skills.get(skill, 0) 
                for skill in required_skills
            ]
            skill_score = np.mean(skill_matches) if skill_matches else 0
        else:
            skill_score = 0.5
        
        # 2. 当前负载 (30%)
        load_score = 1.0 - agent.current_load
        
        # 3. 历史效率 (20%)
        efficiency_score = agent.get_efficiency()
        
        # 加权
        return skill_score * 0.5 + load_score * 0.3 + efficiency_score * 0.2
    
    def get_load_balance_score(self) -> float:
        """计算负载均衡得分"""
        if not self.manager.agents:
            return 0.0
        
        loads = [a.current_load for a in self.manager.agents.values()]
        
        # 变异系数 (越低越均衡)
        mean = np.mean(loads)
        std = np.std(loads)
        
        if mean == 0:
            return 1.0
        
        cv = std / mean
        score = 1.0 / (1.0 + cv)
        
        self.stats['load_balance_score'] = score
        return score
    
    def get_status(self) -> Dict:
        """获取负载均衡器状态"""
        return {
            'stats': self.stats,
            'load_balance': self.get_load_balance_score(),
            'assignment_count': len(self.assignment_history)
        }


# 测试代码
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v5.5 - Dynamic Agent Management Test")
    print("=" * 60)
    
    # 创建管理器
    manager = DynamicAgentManager(min_agents=3, max_agents=10)
    
    # 创建初始 Agent
    print("\n1. 创建初始 Agent...")
    for i in range(3):
        agent_id = manager.create_agent()
        print(f"   创建 Agent: {agent_id}")
    
    # 创建负载均衡器
    balancer = AdaptiveLoadBalancer(manager)
    
    # 模拟任务分配
    print("\n2. 模拟任务分配...")
    tasks = [
        {'id': f'task_{i}', 'required_skills': ['coding'], 'difficulty': 0.3}
        for i in range(10)
    ]
    
    for task in tasks:
        agent_id = balancer.assign_task(task)
        if agent_id:
            agent = manager.agents[agent_id]
            agent.complete_task(success=True)
    
    # 自动扩展测试
    print("\n3. 测试自动扩展...")
    manager.auto_scale(current_load=0.8, task_queue_size=20)
    
    # 获取状态
    print("\n4. 管理器状态:")
    status = manager.get_status()
    print(f"   Agent 数量：{status['total_agents']}")
    print(f"   平均效率：{status['avg_efficiency']:.2f}")
    print(f"   平均负载：{status['avg_load']:.2f}")
    print(f"   创建数：{status['stats']['agents_created']}")
    
    print("\n5. 负载均衡状态:")
    balancer_status = balancer.get_status()
    print(f"   任务分配：{balancer_status['stats']['tasks_assigned']}")
    print(f"   负载均衡：{balancer_status['load_balance']:.2f}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)
