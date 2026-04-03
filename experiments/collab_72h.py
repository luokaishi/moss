#!/usr/bin/env python3
"""
MOSS v5.4 - 72h Multi-Agent Collaboration Experiment
72 小时多 Agent 协作实验

实验目标:
- 验证协作效率
- 测量集体智能涌现
- 评估知识共享效果

Author: MOSS Project
Date: 2026-04-03
Version: 5.4.0-dev
"""

import argparse
import json
import os
from typing import Dict
from datetime import datetime
from pathlib import Path
import numpy as np

from core.collaboration import (
    CollaborationCoordinator, 
    CollaborationMode,
    Task, 
    TaskStatus
)
from core.communication import (
    CommunicationNetwork,
    create_task_request,
    create_knowledge_share
)


class CollaborationExperiment:
    """协作实验管理器"""
    
    def __init__(self, n_agents: int = 10, mode: str = "hybrid"):
        self.n_agents = n_agents
        self.mode = CollaborationMode(mode)
        
        # 初始化协调器和网络
        self.coordinator = CollaborationCoordinator(self.mode)
        self.network = CommunicationNetwork()
        
        # 创建 Agent
        self._create_agents()
        
        # 创建通信信道
        self.network.create_channel(
            "main_channel",
            [f"agent_{i}" for i in range(n_agents)]
        )
        
        # 实验数据
        self.experiment_data = {
            'start_time': datetime.now().isoformat(),
            'config': {
                'n_agents': n_agents,
                'mode': self.mode.value
            },
            'metrics': [],
            'events': []
        }
    
    def _create_agents(self):
        """创建 Agent 并注册"""
        # 定义技能池
        skill_pool = ['coding', 'analysis', 'communication', 'design', 'testing']
        
        for i in range(self.n_agents):
            # 随机生成 Agent 技能
            skills = {
                skill: np.random.uniform(0.3, 1.0)
                for skill in np.random.choice(skill_pool, size=3, replace=False)
            }
            self.coordinator.register_agent(f"agent_{i}", skills)
    
    def generate_tasks(self, n_tasks: int = 100):
        """生成任务池"""
        task_types = [
            ('Implement feature', ['coding', 'testing']),
            ('Analyze data', ['analysis', 'coding']),
            ('Design system', ['design', 'analysis']),
            ('Write documentation', ['communication', 'design']),
            ('Debug issue', ['coding', 'analysis']),
        ]
        task_probs = [0.3, 0.2, 0.2, 0.15, 0.15]
        
        for i in range(n_tasks):
            idx = np.random.choice(len(task_types), p=task_probs)
            task_type, required_skills = task_types[idx]
            task = Task(
                id=f"task_{i}",
                description=f"{task_type} #{i}",
                difficulty=np.random.uniform(0.3, 0.9),
                priority=np.random.uniform(0.3, 1.0),
                required_skills=required_skills,
                reward=np.random.uniform(1.0, 3.0)
            )
            self.coordinator.add_task(task)
    
    def run_simulation(self, n_iterations: int = 1000):
        """运行模拟"""
        print(f"\n🚀 开始 {n_iterations} 轮协作模拟...")
        print(f"   Agent 数量：{self.n_agents}")
        print(f"   协作模式：{self.mode.value}")
        
        for iteration in range(n_iterations):
            # 1. 分配任务
            assignments = self.coordinator.assign_tasks()
            
            # 2. 模拟任务执行
            for agent_id, task_ids in assignments.items():
                for task_id in task_ids:
                    # 随机成功/失败
                    success = np.random.random() > 0.1  # 90% 成功率
                    self.coordinator.complete_task(task_id, success)
                    
                    if success:
                        # 知识共享
                        if np.random.random() < 0.3:  # 30% 概率分享
                            knowledge = {
                                'lesson': f'Learned from {task_id}',
                                'efficiency_gain': np.random.uniform(0.05, 0.2)
                            }
                            self.coordinator.share_knowledge(
                                from_agent=agent_id,
                                to_agents=[a for a in self.coordinator.agents.keys() if a != agent_id],
                                knowledge=knowledge
                            )
            
            # 3. 记录指标
            if iteration % 100 == 0:
                status = self.coordinator.get_status()
                self.experiment_data['metrics'].append({
                    'iteration': iteration,
                    'efficiency': status['efficiency'],
                    'tasks_completed': status['tasks']['completed'],
                    'knowledge_sharing': status['stats']['knowledge_sharing_events']
                })
        
        self.experiment_data['end_time'] = datetime.now().isoformat()
    
    def analyze_results(self) -> Dict:
        """分析实验结果"""
        metrics = self.experiment_data['metrics']
        
        if not metrics:
            return {}
        
        efficiencies = [m['efficiency'] for m in metrics]
        
        results = {
            'final_efficiency': efficiencies[-1] if efficiencies else 0,
            'avg_efficiency': np.mean(efficiencies),
            'efficiency_improvement': efficiencies[-1] - efficiencies[0] if len(efficiencies) > 1 else 0,
            'total_knowledge_sharing': metrics[-1]['knowledge_sharing'] if metrics else 0,
            'task_completion_rate': self.coordinator.stats['tasks_completed'] / max(self.coordinator.stats['tasks_assigned'], 1)
        }
        
        return results
    
    def save_results(self, output_dir: str = "experiments/results/v5.4"):
        """保存结果"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 添加分析结果
        self.experiment_data['results'] = self.analyze_results()
        
        # 保存 JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"collab_72h_{timestamp}.json"
        filepath = output_path / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.experiment_data, f, indent=2, default=str)
        
        return filepath


def main():
    parser = argparse.ArgumentParser(description='MOSS v5.4 协作实验')
    parser.add_argument('--agents', type=int, default=10, help='Agent 数量')
    parser.add_argument('--iterations', type=int, default=1000, help='模拟轮数')
    parser.add_argument('--mode', type=str, default='hybrid', 
                       choices=['centralized', 'decentralized', 'hybrid'],
                       help='协作模式')
    parser.add_argument('--output', type=str, default='experiments/results/v5.4', 
                       help='输出目录')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎯 MOSS v5.4 - 多 Agent 协作实验")
    print("=" * 60)
    
    # 创建实验
    experiment = CollaborationExperiment(
        n_agents=args.agents,
        mode=args.mode
    )
    
    # 生成任务
    experiment.generate_tasks(n_tasks=100)
    
    # 运行模拟
    experiment.run_simulation(n_iterations=args.iterations)
    
    # 分析结果
    results = experiment.analyze_results()
    
    # 保存结果
    filepath = experiment.save_results(args.output)
    
    # 打印结果
    print("\n" + "=" * 60)
    print("🎉 实验完成！")
    print("=" * 60)
    print(f"   最终协作效率   : {results['final_efficiency']:.3f}")
    print(f"   平均协作效率   : {results['avg_efficiency']:.3f}")
    print(f"   效率提升       : {results['efficiency_improvement']:+.3f}")
    print(f"   任务完成率     : {results['task_completion_rate']:.1%}")
    print(f"   知识共享次数   : {results['total_knowledge_sharing']}")
    print(f"\n📊 结果已保存到：{filepath}")
    print("=" * 60)


if __name__ == '__main__':
    main()
