#!/usr/bin/env python3
"""
多 Agent 协作协调器 - 支持多个 Agent 协同完成任务

核心功能:
1. Agent 注册与管理
2. 任务分配与调度
3. 结果聚合与共识
4. 冲突检测与解决
"""

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
import time
import random


@dataclass
class AgentInfo:
    """Agent 信息"""
    agent_id: str
    capabilities: List[str]  # 能力列表
    current_task: Optional[str] = None
    status: str = 'idle'  # idle, working, completed, failed
    performance_score: float = 0.5  # 0-1


class MultiAgentCoordinator:
    """
    多 Agent 协作协调器
    
    管理多个 Agent 的协作，实现任务分配和结果聚合
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.agents: Dict[str, AgentInfo] = {}
        self.task_queue: List[Dict] = []
        self.task_results: Dict[str, List[Dict]] = {}
        self.consensus_threshold = self.config.get('consensus_threshold', 0.7)
        self.max_agents_per_task = self.config.get('max_agents_per_task', 3)
        
    def register_agent(self, agent_id: str, capabilities: List[str]) -> bool:
        """
        注册 Agent
        
        Args:
            agent_id: Agent 唯一标识
            capabilities: Agent 能力列表
            
        Returns:
            是否注册成功
        """
        if agent_id in self.agents:
            return False
        
        self.agents[agent_id] = AgentInfo(
            agent_id=agent_id,
            capabilities=capabilities,
            status='idle'
        )
        return True
    
    def unregister_agent(self, agent_id: str) -> bool:
        """注销 Agent"""
        if agent_id not in self.agents:
            return False
        
        del self.agents[agent_id]
        return True
    
    def submit_task(self, task: Dict) -> str:
        """
        提交任务
        
        Args:
            task: 任务配置
            
        Returns:
            任务 ID
        """
        task_id = f"task_{int(time.time())}_{random.randint(1000, 9999)}"
        task['task_id'] = task_id
        task['status'] = 'pending'
        
        self.task_queue.append(task)
        self.task_results[task_id] = []
        
        return task_id
    
    def distribute_tasks(self) -> Dict[str, List[str]]:
        """
        分配任务给 Agent
        
        Returns:
            任务分配方案 {task_id: [agent_ids]}
        """
        assignments = {}
        
        # 获取空闲 Agent
        idle_agents = [
            agent_id for agent_id, info in self.agents.items()
            if info.status == 'idle'
        ]
        
        if not idle_agents:
            return assignments
        
        # 分配待处理任务
        for task in self.task_queue:
            if task['status'] != 'pending':
                continue
            
            task_id = task['task_id']
            required_capabilities = task.get('capabilities', [])
            
            # 选择最适合的 Agent
            suitable_agents = self._select_agents_for_task(
                required_capabilities, 
                idle_agents,
                self.max_agents_per_task
            )
            
            if suitable_agents:
                assignments[task_id] = suitable_agents
                task['status'] = 'assigned'
                
                # 更新 Agent 状态
                for agent_id in suitable_agents:
                    self.agents[agent_id].status = 'working'
                    self.agents[agent_id].current_task = task_id
                
                # 从空闲列表中移除
                for agent_id in suitable_agents:
                    if agent_id in idle_agents:
                        idle_agents.remove(agent_id)
            
            # 如果没有更多空闲 Agent，停止分配
            if not idle_agents:
                break
        
        return assignments
    
    def _select_agents_for_task(self, required_capabilities: List[str], 
                                   available_agents: List[str],
                                   max_agents: int) -> List[str]:
        """
        为任务选择最合适的 Agent
        
        策略:
        1. 匹配能力
        2. 考虑性能分数
        3. 限制数量
        """
        if not required_capabilities:
            # 如果没有特定能力要求，随机选择
            return random.sample(available_agents, 
                               min(max_agents, len(available_agents)))
        
        # 计算每个 Agent 的匹配分数
        agent_scores = []
        for agent_id in available_agents:
            info = self.agents[agent_id]
            
            # 计算能力匹配度
            matched = sum(1 for cap in required_capabilities 
                         if cap in info.capabilities)
            match_score = matched / len(required_capabilities)
            
            # 综合分数 = 能力匹配 * 性能分数
            total_score = match_score * info.performance_score
            
            agent_scores.append((agent_id, total_score))
        
        # 按分数排序，选择前 N 个
        agent_scores.sort(key=lambda x: x[1], reverse=True)
        selected = [agent_id for agent_id, _ in agent_scores[:max_agents]]
        
        return selected
    
    def submit_result(self, agent_id: str, task_id: str, result: Dict) -> bool:
        """
        Agent 提交任务结果
        
        Args:
            agent_id: Agent ID
            task_id: 任务 ID
            result: 任务结果
            
        Returns:
            是否提交成功
        """
        if task_id not in self.task_results:
            return False
        
        if agent_id not in self.agents:
            return False
        
        # 保存结果
        self.task_results[task_id].append({
            'agent_id': agent_id,
            'result': result,
            'timestamp': time.time()
        })
        
        # 更新 Agent 状态
        self.agents[agent_id].status = 'completed'
        self.agents[agent_id].current_task = None
        
        # 更新性能分数
        if result.get('success'):
            self.agents[agent_id].performance_score = min(
                1.0, 
                self.agents[agent_id].performance_score + 0.1
            )
        else:
            self.agents[agent_id].performance_score = max(
                0.0,
                self.agents[agent_id].performance_score - 0.1
            )
        
        return True
    
    def aggregate_results(self, task_id: str) -> Optional[Dict]:
        """
        聚合多个 Agent 的结果
        
        策略:
        1. 投票机制
        2. 加权平均
        3. 共识检测
        
        Args:
            task_id: 任务 ID
            
        Returns:
            聚合后的结果
        """
        if task_id not in self.task_results:
            return None
        
        results = self.task_results[task_id]
        
        if not results:
            return None
        
        if len(results) == 1:
            return results[0]['result']
        
        # 多 Agent 结果聚合
        return self._consensus_aggregation(results)
    
    def _consensus_aggregation(self, results: List[Dict]) -> Dict:
        """
        共识聚合
        
        找到大多数 Agent 同意的结果
        """
        # 收集所有结果
        result_values = [r['result'] for r in results]
        
        # 对于布尔结果，使用投票
        if all(isinstance(r.get('success'), bool) for r in result_values):
            success_votes = sum(1 for r in result_values if r.get('success'))
            total = len(result_values)
            
            consensus = success_votes / total >= self.consensus_threshold
            
            return {
                'success': consensus,
                'confidence': max(success_votes, total - success_votes) / total,
                'agent_count': total,
                'consensus_reached': consensus
            }
        
        # 对于数值结果，使用加权平均
        if all('value' in r for r in result_values):
            values = [r['value'] for r in result_values]
            avg_value = sum(values) / len(values)
            
            return {
                'value': avg_value,
                'min': min(values),
                'max': max(values),
                'std': self._calculate_std(values),
                'agent_count': len(results)
            }
        
        # 默认：返回第一个结果
        return result_values[0]
    
    def _calculate_std(self, values: List[float]) -> float:
        """计算标准差"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def detect_conflicts(self, task_id: str) -> List[Dict]:
        """
        检测结果冲突
        
        Args:
            task_id: 任务 ID
            
        Returns:
            冲突列表
        """
        if task_id not in self.task_results:
            return []
        
        results = self.task_results[task_id]
        
        if len(results) < 2:
            return []
        
        conflicts = []
        
        # 检查成功/失败冲突
        success_results = [r for r in results if r['result'].get('success')]
        failure_results = [r for r in results if not r['result'].get('success')]
        
        if success_results and failure_results:
            conflicts.append({
                'type': 'success_conflict',
                'description': f'{len(success_results)} agents succeeded, {len(failure_results)} failed',
                'severity': 'high'
            })
        
        # 检查数值冲突
        if all('value' in r['result'] for r in results):
            values = [r['result']['value'] for r in results]
            std = self._calculate_std(values)
            mean = sum(values) / len(values)
            
            if std / mean > 0.5:  # 变异系数 > 50%
                conflicts.append({
                    'type': 'value_divergence',
                    'description': f'Values diverge significantly (CV={std/mean:.2f})',
                    'severity': 'medium'
                })
        
        return conflicts
    
    def resolve_conflict(self, task_id: str, conflict: Dict) -> Optional[Dict]:
        """
        解决冲突
        
        Args:
            task_id: 任务 ID
            conflict: 冲突信息
            
        Returns:
            解决方案
        """
        if task_id not in self.task_results:
            return None
        
        results = self.task_results[task_id]
        
        if conflict['type'] == 'success_conflict':
            # 选择性能分数更高的 Agent 的结果
            success_results = [r for r in results if r['result'].get('success')]
            if success_results:
                # 按 Agent 性能排序
                sorted_results = sorted(
                    success_results,
                    key=lambda r: self.agents[r['agent_id']].performance_score,
                    reverse=True
                )
                return {
                    'resolution': 'highest_performance',
                    'selected_agent': sorted_results[0]['agent_id'],
                    'result': sorted_results[0]['result']
                }
            else:
                return {
                    'resolution': 'all_failed',
                    'result': {'success': False}
                }
        
        elif conflict['type'] == 'value_divergence':
            # 使用中位数
            values = [r['result']['value'] for r in results]
            median = sorted(values)[len(values) // 2]
            
            return {
                'resolution': 'median',
                'value': median,
                'confidence': 'medium'
            }
        
        return None
    
    def get_status(self) -> Dict:
        """获取协调器状态"""
        return {
            'registered_agents': len(self.agents),
            'idle_agents': sum(1 for a in self.agents.values() if a.status == 'idle'),
            'working_agents': sum(1 for a in self.agents.values() if a.status == 'working'),
            'pending_tasks': sum(1 for t in self.task_queue if t['status'] == 'pending'),
            'assigned_tasks': sum(1 for t in self.task_queue if t['status'] == 'assigned'),
            'completed_tasks': len([t for t in self.task_results if len(self.task_results.get(t, [])) > 0])
        }
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict]:
        """获取 Agent 状态"""
        if agent_id not in self.agents:
            return None
        
        info = self.agents[agent_id]
        return {
            'agent_id': info.agent_id,
            'capabilities': info.capabilities,
            'status': info.status,
            'current_task': info.current_task,
            'performance_score': info.performance_score
        }


# 便捷函数
def create_coordinator(config: Dict = None) -> MultiAgentCoordinator:
    """创建协调器"""
    return MultiAgentCoordinator(config)
