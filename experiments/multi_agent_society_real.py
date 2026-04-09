#!/usr/bin/env python3
"""
MOSS v4.0 Phase 2: 多Agent真实世界社会实验

目标: 10-20个MOSS Agent并行运行，观察Purpose分化→自然分工

运行: python3 experiments/multi_agent_society_real.py
作者: Cash
日期: 2026-03-21
"""

import sys
import time
import json
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
import threading
import queue

sys.path.insert(0, '/workspace/projects/moss')
sys.path.insert(0, '/workspace/projects/moss/v3')
sys.path.insert(0, '/workspace/projects/moss/v3/core')
sys.path.insert(0, '/workspace/projects/moss/core')

from agent_9d import MOSSv3Agent9D
from core.real_world_bridge import RealWorldBridge

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('experiments/society_experiment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AgentSociety:
    """
    MOSS多Agent社会
    
    核心功能:
    1. 管理多个MOSS Agent实例
    2. 任务路由（基于Purpose匹配）
    3. 信任网络维护
    4. 资源分配
    """
    
    def __init__(self, n_agents: int = 10, duration_hours: int = 72):
        self.n_agents = n_agents
        self.duration = timedelta(hours=duration_hours)
        self.start_time = datetime.now()
        self.end_time = self.start_time + self.duration
        
        # 创建Agent池
        self.agents: List[MOSSv3Agent9D] = []
        self.bridges: List[RealWorldBridge] = []
        self.agent_threads: List[threading.Thread] = []
        
        # 共享资源
        self.task_queue = queue.Queue()
        self.results_queue = queue.Queue()
        
        # 信任网络
        self.trust_matrix: Dict[str, Dict[str, float]] = {}
        
        # 统计
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'purpose_distribution': {},
            'trust_updates': 0
        }
        
        self._init_agents()
        
        logger.info(f"[Society] Initialized with {n_agents} agents for {duration_hours}h")
    
    def _init_agents(self):
        """初始化Agent池"""
        for i in range(self.n_agents):
            agent_id = f"society_agent_{i:02d}"
            
            # 创建Agent
            agent = MOSSv3Agent9D(
                agent_id=agent_id,
                enable_purpose=True,
                purpose_interval=2000
            )
            
            # 创建Bridge
            bridge = RealWorldBridge(agent)
            
            self.agents.append(agent)
            self.bridges.append(bridge)
            self.trust_matrix[agent_id] = {}
            
            logger.info(f"[Society] Agent {agent_id} initialized")
    
    def route_task(self, task: str) -> int:
        """
        任务路由: 选择最适合的Agent
        
        策略:
        1. 根据任务类型匹配Purpose
        2. 考虑Agent负载
        3. 信任度加权
        """
        # 简化的任务分类
        task_type = self._classify_task(task)
        preferred_purposes = self._get_preferred_purposes(task_type)
        
        best_agent_idx = 0
        best_score = -1
        
        for idx, agent in enumerate(self.agents):
            if not hasattr(agent, 'purpose_generator') or not agent.purpose_generator:
                continue
            
            # 获取当前主导Purpose
            pg = agent.purpose_generator
            vector = pg.purpose_vector if hasattr(pg, 'purpose_vector') else [0.25]*9
            
            dims = ['Survival', 'Curiosity', 'Influence', 'Optimization']
            dominant_idx = vector[:4].index(max(vector[:4]))
            dominant = dims[dominant_idx]
            
            # 匹配度分数
            match_score = 1.0 if dominant in preferred_purposes else 0.0
            
            # 负载分数 (简化: 随机)
            load_score = 1.0  # TODO: 实际负载计算
            
            # 总分
            total_score = match_score * 0.7 + load_score * 0.3
            
            if total_score > best_score:
                best_score = total_score
                best_agent_idx = idx
        
        return best_agent_idx
    
    def _classify_task(self, task: str) -> str:
        """任务分类"""
        task_lower = task.lower()
        if any(kw in task_lower for kw in ['security', 'backup', 'health']):
            return 'survival'
        elif any(kw in task_lower for kw in ['explore', 'learn', 'test']):
            return 'exploration'
        elif any(kw in task_lower for kw in ['review', 'document', 'pr']):
            return 'coordination'
        elif any(kw in task_lower for kw in ['optimize', 'refactor', 'improve']):
            return 'optimization'
        return 'general'
    
    def _get_preferred_purposes(self, task_type: str) -> List[str]:
        """获取任务类型偏好的Purpose"""
        mapping = {
            'survival': ['Survival'],
            'exploration': ['Curiosity'],
            'coordination': ['Influence'],
            'optimization': ['Optimization'],
            'general': ['Survival', 'Curiosity', 'Influence', 'Optimization']
        }
        return mapping.get(task_type, mapping['general'])
    
    def run_agent_loop(self, agent_idx: int):
        """单个Agent的运行循环"""
        agent = self.agents[agent_idx]
        bridge = self.bridges[agent_idx]
        agent_id = agent.agent_id
        
        logger.info(f"[{agent_id}] Starting loop")
        
        step = 0
        while datetime.now() < self.end_time:
            try:
                # 获取任务
                task = self._get_task_for_agent(agent_idx)
                
                # 执行
                result = bridge.execute_real_action(task, step)
                
                # 记录结果
                self.results_queue.put({
                    'agent_id': agent_id,
                    'step': step,
                    'task': task,
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                })
                
                step += 100
                time.sleep(1)  # 控制频率
                
            except Exception as e:
                logger.error(f"[{agent_id}] Error: {e}")
                time.sleep(5)
        
        logger.info(f"[{agent_id}] Loop ended")
    
    def _get_task_for_agent(self, agent_idx: int) -> str:
        """为Agent获取任务"""
        # 任务池
        tasks = [
            "Check GitHub issues for bugs",
            "Review recent commits",
            "Run test suite",
            "Check documentation freshness",
            "Monitor repository health",
            "Analyze code quality",
            "Check for security updates",
            "Review pull requests",
            "Update dependencies",
            "git status",
            "git log --oneline -10",
            "Check CI/CD status"
        ]
        
        # 基于Agent Purpose选择任务
        agent = self.agents[agent_idx]
        if hasattr(agent, 'purpose_generator') and agent.purpose_generator:
            pg = agent.purpose_generator
            vector = pg.purpose_vector if hasattr(pg, 'purpose_vector') else [0.25]*9
            max_idx = vector[:4].index(max(vector[:4]))
            
            # Purpose-based task selection
            if max_idx == 0:  # Survival
                return tasks[6]  # security
            elif max_idx == 1:  # Curiosity
                return tasks[2]  # test
            elif max_idx == 2:  # Influence
                return tasks[1]  # review
            elif max_idx == 3:  # Optimization
                return tasks[7]  # update
        
        # 默认随机
        import random
        return random.choice(tasks)
    
    def run(self):
        """运行社会实验"""
        logger.info("=" * 70)
        logger.info("🚀 Starting Multi-Agent Society Experiment")
        logger.info("=" * 70)
        logger.info(f"Agents: {self.n_agents}")
        logger.info(f"Duration: {self.duration}")
        logger.info(f"End: {self.end_time}")
        
        # 启动所有Agent线程
        for i in range(self.n_agents):
            thread = threading.Thread(
                target=self.run_agent_loop,
                args=(i,),
                name=f"Agent-{i:02d}"
            )
            thread.daemon = True
            thread.start()
            self.agent_threads.append(thread)
        
        logger.info(f"All {self.n_agents} agents started")
        
        # 主监控循环
        try:
            while datetime.now() < self.end_time:
                self._report_status()
                time.sleep(60)  # 每分钟报告一次
        except KeyboardInterrupt:
            logger.info("\n⚠️  Experiment interrupted")
        
        # 结束
        self._finalize()
    
    def _report_status(self):
        """报告状态"""
        elapsed = datetime.now() - self.start_time
        remaining = self.end_time - datetime.now()
        
        # 统计Purpose分布
        purpose_dist = {}
        for agent in self.agents:
            if hasattr(agent, 'purpose_generator') and agent.purpose_generator:
                pg = agent.purpose_generator
                vector = pg.purpose_vector if hasattr(pg, 'purpose_vector') else [0.25]*9
                max_idx = vector[:4].index(max(vector[:4]))
                dims = ['S', 'C', 'I', 'O']
                dominant = dims[max_idx]
                purpose_dist[dominant] = purpose_dist.get(dominant, 0) + 1
        
        logger.info(f"[Status] Elapsed: {elapsed} | Remaining: {remaining}")
        logger.info(f"[Status] Purpose Distribution: {purpose_dist}")
    
    def _finalize(self):
        """结束实验"""
        logger.info("=" * 70)
        logger.info("✅ Society Experiment Complete")
        logger.info("=" * 70)
        
        # 生成报告
        report = {
            'experiment': 'Multi-Agent Society',
            'n_agents': self.n_agents,
            'start_time': self.start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'stats': self.stats
        }
        
        report_path = Path('experiments/society_experiment_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to: {report_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='MOSS Multi-Agent Society Experiment')
    parser.add_argument('--agents', type=int, default=10, help='Number of agents')
    parser.add_argument('--hours', type=int, default=72, help='Experiment duration')
    args = parser.parse_args()
    
    society = AgentSociety(n_agents=args.agents, duration_hours=args.hours)
    society.run()


if __name__ == "__main__":
    main()
