#!/usr/bin/env python3
"""
MOSS v4.0 Phase 2: 多Agent真实世界社会实验 (Windows修复版)

目标: 10-20个MOSS Agent并行运行，观察Purpose分化→自然分工

运行: python3 experiments/multi_agent_society_real_fixed.py
作者: Cash (修复: WorkBuddy)
日期: 2026-04-10
"""

import sys
import os
import time
import json
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
import threading
import queue

# 修复：Windows路径设置
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, '_archive_v3'))
sys.path.insert(0, os.path.join(project_root, '_archive_v3', 'core'))
sys.path.insert(0, os.path.join(project_root, 'moss', 'core'))

# 调整导入路径
try:
    from _archive_v3.core.agent_9d import MOSSv3Agent9D
    from moss.core.real_world_bridge import RealWorldBridge
except ImportError as e:
    print(f"导入错误: {e}")
    print("尝试备用导入路径...")
    sys.path.insert(0, os.path.join(project_root, 'agents'))
    try:
        from agents.moss_9d import MOSSv3Agent9D
        from moss.core.real_world_bridge import RealWorldBridge
    except ImportError as e2:
        print(f"备用导入也失败: {e2}")
        sys.exit(1)

# Windows路径兼容性
def win_path(path_str):
    """确保路径适合Windows"""
    return str(path_str).replace('/', '\\')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(win_path('experiments/society_experiment.log')),
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
    
    def __init__(self, n_agents: int = 3, duration_minutes: int = 10):
        """轻量版本：3个Agent运行10分钟测试"""
        self.n_agents = n_agents
        self.duration = timedelta(minutes=duration_minutes)
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
        self._init_tasks()
        
        logger.info(f"[Society] 初始化 {n_agents} 个Agent，运行 {duration_minutes} 分钟")
        logger.info(f"[Society] 开始时间: {self.start_time}")
        logger.info(f"[Society] 结束时间: {self.end_time}")
    
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
            
            logger.info(f"[Society] Agent {agent_id} 初始化完成")
    
    def _init_tasks(self):
        """初始化测试任务"""
        test_tasks = [
            "检查文件系统安全状态",
            "学习Python新特性",
            "优化代码性能",
            "整理项目文档",
            "测试API接口",
            "分析日志文件"
        ]
        
        for task in test_tasks:
            self.task_queue.put(task)
        
        self.stats['total_tasks'] = len(test_tasks)
        logger.info(f"[Society] 加载 {len(test_tasks)} 个测试任务")
    
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
    
    def _get_task_for_agent(self, agent_idx: int) -> str:
        """为Agent获取任务"""
        try:
            task = self.task_queue.get(timeout=1)
            return task
        except queue.Empty:
            # 如果没有任务，返回默认任务
            return f"默认任务_{agent_idx}"
    
    def run_agent_loop(self, agent_idx: int):
        """单个Agent的运行循环"""
        agent = self.agents[agent_idx]
        bridge = self.bridges[agent_idx]
        agent_id = agent.agent_id
        
        logger.info(f"[{agent_id}] 启动循环")
        
        step = 0
        while datetime.now() < self.end_time:
            try:
                # 获取任务
                task = self._get_task_for_agent(agent_idx)
                
                logger.info(f"[{agent_id}] 执行任务: {task}")
                
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
                time.sleep(2)  # 控制频率
                
            except Exception as e:
                logger.error(f"[{agent_id}] 循环错误: {e}")
                time.sleep(5)  # 错误后暂停
        
        logger.info(f"[{agent_id}] 循环结束")
    
    def start(self):
        """启动多Agent社会"""
        logger.info(f"[Society] 开始运行")
        
        # 启动Agent线程
        for i in range(self.n_agents):
            thread = threading.Thread(
                target=self.run_agent_loop,
                args=(i,),
                name=f"agent_{i:02d}"
            )
            self.agent_threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in self.agent_threads:
            thread.join()
        
        logger.info(f"[Society] 所有Agent完成")
        self._save_results()
    
    def _save_results(self):
        """保存结果"""
        results_dir = Path(win_path('experiments/society_results'))
        results_dir.mkdir(exist_ok=True)
        
        # 收集所有结果
        all_results = []
        while not self.results_queue.empty():
            try:
                all_results.append(self.results_queue.get_nowait())
            except queue.Empty:
                break
        
        # 保存JSON文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = results_dir / f"society_results_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'start_time': self.start_time.isoformat(),
                    'end_time': self.end_time.isoformat(),
                    'n_agents': self.n_agents,
                    'duration_minutes': int(self.duration.total_seconds() / 60)
                },
                'stats': self.stats,
                'results': all_results
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"[Society] 结果保存到: {results_file}")
        
        # 打印摘要
        self._print_summary()
    
    def _print_summary(self):
        """打印实验摘要"""
        print("\n" + "="*60)
        print("多Agent社会实验摘要")
        print("="*60)
        print(f"Agent数量: {self.n_agents}")
        print(f"运行时间: {int(self.duration.total_seconds() / 60)} 分钟")
        print(f"完成任务: {self.stats.get('completed_tasks', 0)}")
        print("-"*60)


def main():
    parser = argparse.ArgumentParser(description='MOSS多Agent社会实验')
    parser.add_argument('--agents', type=int, default=3, help='Agent数量 (默认: 3)')
    parser.add_argument('--minutes', type=int, default=10, help='运行分钟数 (默认: 10)')
    parser.add_argument('--verbose', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print(f"启动多Agent社会实验")
    print(f"Agent数量: {args.agents}")
    print(f"运行时间: {args.minutes} 分钟")
    print("-"*40)
    
    society = AgentSociety(
        n_agents=args.agents,
        duration_minutes=args.minutes
    )
    
    try:
        society.start()
        print("\n✅ 实验成功完成！")
    except KeyboardInterrupt:
        print("\n🛑 用户中断")
    except Exception as e:
        print(f"\n❌ 实验失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()