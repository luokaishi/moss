#!/usr/bin/env python3
"""
MOSS v9.0 - Agent Registry
Agent注册中心 - 统一管理Agent生命周期

Author: MOSS v9.0
Date: 2026-04-23
"""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
import asyncio
import uuid


class AgentStatus(Enum):
    """Agent状态"""
    INITIALIZING = auto()  # 初始化中
    IDLE = auto()          # 空闲
    BUSY = auto()          # 忙碌
    OFFLINE = auto()       # 离线
    ERROR = auto()         # 错误
    SHUTDOWN = auto()      # 已关闭


class HealthStatus(Enum):
    """健康状态"""
    HEALTHY = auto()
    DEGRADED = auto()
    UNHEALTHY = auto()
    UNKNOWN = auto()


@dataclass
class AgentInfo:
    """Agent信息"""
    agent_id: str
    name: str
    capabilities: List[str]
    status: AgentStatus = AgentStatus.INITIALIZING
    health: HealthStatus = HealthStatus.UNKNOWN
    current_task: Optional[str] = None
    performance_score: float = 0.5
    created_at: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    agent_id: str
    status: HealthStatus
    metrics: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    message: str = ""


class AgentRegistry:
    """
    Agent注册中心
    
    核心功能:
    1. Agent注册/注销
    2. 能力索引
    3. 健康状态管理
    4. 发现与查找
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.agents: Dict[str, AgentInfo] = {}  # agent_id -> AgentInfo
        self.capability_index: Dict[str, List[str]] = {}  # capability -> [agent_ids]
        self.health_checks: Dict[str, Callable] = {}  # agent_id -> health_check_func
        self._lock = asyncio.Lock()
        self._health_check_interval = self.config.get('health_check_interval', 30)
        self._health_check_task: Optional[asyncio.Task] = None
        
    async def initialize(self) -> bool:
        """初始化注册中心"""
        try:
            # 启动健康检查循环
            self._health_check_task = asyncio.create_task(
                self._health_check_loop()
            )
            return True
        except Exception as e:
            print(f"[AgentRegistry] 初始化失败: {e}")
            return False
    
    async def register(
        self,
        name: str,
        capabilities: List[str],
        health_check: Optional[Callable] = None,
        metadata: Dict = None
    ) -> str:
        """
        注册Agent
        
        Args:
            name: Agent名称
            capabilities: 能力列表
            health_check: 健康检查函数
            metadata: 元数据
            
        Returns:
            agent_id: 分配的Agent ID
        """
        agent_id = f"agent_{uuid.uuid4().hex[:8]}"
        
        async with self._lock:
            # 创建Agent信息
            agent_info = AgentInfo(
                agent_id=agent_id,
                name=name,
                capabilities=capabilities,
                metadata=metadata or {}
            )
            
            # 注册Agent
            self.agents[agent_id] = agent_info
            
            # 更新能力索引
            for cap in capabilities:
                if cap not in self.capability_index:
                    self.capability_index[cap] = []
                self.capability_index[cap].append(agent_id)
            
            # 注册健康检查
            if health_check:
                self.health_checks[agent_id] = health_check
            
            print(f"[AgentRegistry] Agent注册成功: {agent_id} ({name})")
            return agent_id
    
    async def unregister(self, agent_id: str) -> bool:
        """
        注销Agent
        
        Args:
            agent_id: Agent ID
            
        Returns:
            是否成功
        """
        async with self._lock:
            if agent_id not in self.agents:
                return False
            
            agent_info = self.agents[agent_id]
            
            # 从能力索引中移除
            for cap in agent_info.capabilities:
                if cap in self.capability_index:
                    self.capability_index[cap].remove(agent_id)
                    if not self.capability_index[cap]:
                        del self.capability_index[cap]
            
            # 移除Agent
            del self.agents[agent_id]
            
            # 移除健康检查
            if agent_id in self.health_checks:
                del self.health_checks[agent_id]
            
            print(f"[AgentRegistry] Agent注销: {agent_id}")
            return True
    
    async def update_status(
        self,
        agent_id: str,
        status: AgentStatus,
        current_task: Optional[str] = None
    ) -> bool:
        """更新Agent状态"""
        async with self._lock:
            if agent_id not in self.agents:
                return False
            
            agent_info = self.agents[agent_id]
            agent_info.status = status
            agent_info.last_seen = datetime.now()
            
            if current_task is not None:
                agent_info.current_task = current_task
            
            return True
    
    async def update_health(
        self,
        agent_id: str,
        health: HealthStatus,
        metrics: Dict = None
    ) -> bool:
        """更新Agent健康状态"""
        async with self._lock:
            if agent_id not in self.agents:
                return False
            
            agent_info = self.agents[agent_id]
            agent_info.health = health
            agent_info.last_seen = datetime.now()
            
            if metrics:
                agent_info.metadata.update(metrics)
            
            return True
    
    async def find_by_capability(self, capability: str) -> List[AgentInfo]:
        """
        按能力查找Agent
        
        Args:
            capability: 能力名称
            
        Returns:
            Agent信息列表
        """
        async with self._lock:
            agent_ids = self.capability_index.get(capability, [])
            return [self.agents[aid] for aid in agent_ids if aid in self.agents]
    
    async def find_by_capabilities(
        self,
        capabilities: List[str],
        match_all: bool = True
    ) -> List[AgentInfo]:
        """
        按多个能力查找Agent
        
        Args:
            capabilities: 能力列表
            match_all: 是否要求匹配所有能力
            
        Returns:
            Agent信息列表
        """
        async with self._lock:
            if not capabilities:
                return list(self.agents.values())
            
            if match_all:
                # 交集
                agent_ids = set(self.capability_index.get(capabilities[0], []))
                for cap in capabilities[1:]:
                    agent_ids &= set(self.capability_index.get(cap, []))
            else:
                # 并集
                agent_ids = set()
                for cap in capabilities:
                    agent_ids |= set(self.capability_index.get(cap, []))
            
            return [self.agents[aid] for aid in agent_ids if aid in self.agents]
    
    async def get_healthy_agents(self) -> List[AgentInfo]:
        """获取健康Agent列表"""
        async with self._lock:
            return [
                agent for agent in self.agents.values()
                if agent.health == HealthStatus.HEALTHY
                and agent.status in [AgentStatus.IDLE, AgentStatus.BUSY]
            ]
    
    async def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """获取Agent信息"""
        async with self._lock:
            return self.agents.get(agent_id)
    
    async def get_all_agents(self) -> List[AgentInfo]:
        """获取所有Agent"""
        async with self._lock:
            return list(self.agents.values())
    
    async def get_statistics(self) -> Dict:
        """获取统计信息"""
        async with self._lock:
            status_counts = {}
            health_counts = {}
            
            for agent in self.agents.values():
                status_counts[agent.status.name] = status_counts.get(
                    agent.status.name, 0
                ) + 1
                health_counts[agent.health.name] = health_counts.get(
                    agent.health.name, 0
                ) + 1
            
            return {
                'total_agents': len(self.agents),
                'status_distribution': status_counts,
                'health_distribution': health_counts,
                'total_capabilities': len(self.capability_index),
            }
    
    async def _health_check_loop(self):
        """健康检查循环"""
        while True:
            try:
                await asyncio.sleep(self._health_check_interval)
                await self._run_health_checks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[AgentRegistry] 健康检查错误: {e}")
    
    async def _run_health_checks(self):
        """执行健康检查"""
        for agent_id, check_func in list(self.health_checks.items()):
            try:
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
                
                if isinstance(result, HealthCheckResult):
                    await self.update_health(
                        agent_id,
                        result.status,
                        result.metrics
                    )
                elif isinstance(result, bool):
                    health = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                    await self.update_health(agent_id, health)
                
            except Exception as e:
                print(f"[AgentRegistry] Agent {agent_id} 健康检查失败: {e}")
                await self.update_health(agent_id, HealthStatus.UNHEALTHY)
    
    async def shutdown(self) -> bool:
        """关闭注册中心"""
        try:
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass
            
            # 注销所有Agent
            for agent_id in list(self.agents.keys()):
                await self.unregister(agent_id)
            
            print("[AgentRegistry] 已关闭")
            return True
        except Exception as e:
            print(f"[AgentRegistry] 关闭失败: {e}")
            return False


# 全局注册中心实例
_registry: Optional[AgentRegistry] = None


def get_registry(config: Dict = None) -> AgentRegistry:
    """获取全局注册中心实例"""
    global _registry
    if _registry is None:
        _registry = AgentRegistry(config)
    return _registry


async def create_registry(config: Dict = None) -> AgentRegistry:
    """创建并初始化注册中心"""
    registry = AgentRegistry(config)
    await registry.initialize()
    return registry


# 测试代码
if __name__ == "__main__":
    async def test():
        # 创建注册中心
        registry = await create_registry()
        
        # 注册测试Agent
        agent_id = await registry.register(
            name="TestAgent",
            capabilities=["file_management", "classification"],
            metadata={"version": "1.0"}
        )
        print(f"注册Agent: {agent_id}")
        
        # 更新状态
        await registry.update_status(agent_id, AgentStatus.IDLE)
        await registry.update_health(agent_id, HealthStatus.HEALTHY, {"cpu": 50})
        
        # 查找Agent
        agents = await registry.find_by_capability("file_management")
        print(f"找到 {len(agents)} 个文件管理Agent")
        
        # 获取统计
        stats = await registry.get_statistics()
        print(f"统计: {stats}")
        
        # 关闭
        await registry.shutdown()
    
    asyncio.run(test())
