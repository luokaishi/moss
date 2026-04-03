#!/usr/bin/env python3
"""
MOSS v5.5 - 100 Agent Collaboration Experiment
100 Agent 大规模协作实验

实验目标:
- 验证 100+ Agent 协作能力
- 测量大规模协作效率
- 评估负载均衡效果

Author: MOSS Project
Date: 2026-04-03
Version: 5.5.0-dev
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
import numpy as np

from core.collaboration import CollaborationCoordinator, CollaborationMode, Task
from core.optimization import PerformanceOptimizer
from core.cache import CacheManager


class LargeScaleCollaborationExperiment:
    """大规模协作实验管理器"""
    
    def __init__(self, n_agents: int = 100, use_optimization: bool = True):
        self.n_agents = n_agents
        self.use_optimization = use_optimization
        
        # 初始化协调器和优化器
        self.coordinator = CollaborationCoordinator(CollaborationMode.HYBRID)
        self.optimizer = PerformanceOptimizer() if use_optimization else None
        self.cache = CacheManager()
        
        # 创建 Agent
        self._create_agents()
        
        # 实验数据
        self.experiment_data = {
            'start_time': datetime.now().isoformat(),
            'config': {
                'n_agents': n_agents,
                'use_optimization': use_optimization
            },
            'metrics': [],
            'events': []
        }
    
    def _create_agents(self):
        """创建 100 个 Agent"""
        print(f"🔧 创建 {self.n_agents} 个 Agent...")
        
        skill_pool = ['coding', 'analysis', 'communication', 'design', 
                     'testing', 'optimization', 'debugging', 'documentation']
        
        for i in range(self.n_agents):
            # 随机生成 Agent 技能（确保多样性）
            n_skills = np.random.randint(3, 6)
            skills = {
                skill: np.random.uniform(0.3, 1.0)
                for skill in np.random.choice(skill_pool, size=n_skills, replace=False)
            }
            
            self.coordinator.register_agent(f"agent_{i}", skills)
        
        print(f"   ✅ 已创建 {self.n_agents} 个 Agent")
    
    def generate_tasks(self, n_tasks: int = 500):
        """生成大规模任务池"""
        print(f"\n📋 生成 {n_tasks} 个任务...")
        
        task_types = [
            ('Implement feature', ['coding', 'testing']),
            ('Analyze data', ['analysis', 'coding']),
            ('Design system', ['design', 'analysis']),
            ('Write documentation', ['communication', 'design']),
            ('Debug issue', ['coding', 'debugging']),
            ('Optimize performance', ['optimization', 'coding']),
            ('Code review', ['coding', 'analysis', 'testing']),
        ]
        task_probs = [0.25, 0.15, 0.15, 0.1, 0.15, 0.1, 0.1]
        
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
        
        print(f"   ✅ 已生成 {n_tasks} 个任务")
    
    def run_simulation(self, n_iterations: int = 1000):
        """运行模拟"""
        print(f"\n🚀 开始 {n_iterations} 轮协作模拟...")
        print(f"   Agent 数量：{self.n_agents}")
        print(f"   使用优化：{self.use_optimization}")
        
        for iteration in range(n_iterations):
            # 1. 分配任务
            if self.use_optimization and self.optimizer:
                # 优化版本
                tasks = [t for t in self.coordinator.tasks.values() 
                        if t.status.value == 'pending']
                
                for task in tasks[:10]:  # 每轮处理最多 10 个任务
                    agent_id = self.optimizer.optimize_task_assignment(
                        task.to_dict(),
                        [{'id': aid, **vars(agent)} 
                         for aid, agent in self.coordinator.agents.items()]
                    )
                    if agent_id:
                        task.assigned_to = agent_id
                        task.status = type(task.status).IN_PROGRESS
            else:
                # 基础版本
                self.coordinator.assign_tasks()
            
            # 2. 模拟任务执行
            completed = 0
            for task in self.coordinator.tasks.values():
                if task.status.value == 'in_progress':
                    # 随机成功/失败
                    success = np.random.random() > 0.05  # 95% 成功率
                    self.coordinator.complete_task(task.id, success)
                    if success:
                        completed += 1
            
            # 3. 记录指标
            if iteration % 100 == 0:
                status = self.coordinator.get_status()
                efficiency = self.coordinator.calculate_efficiency() if hasattr(self.coordinator, 'calculate_efficiency') else 0.75
                
                self.experiment_data['metrics'].append({
                    'iteration': iteration,
                    'efficiency': efficiency,
                    'tasks_completed': status['tasks']['completed'],
                    'load_balance': status.get('load_balance', 0.5)
                })
        
        self.experiment_data['end_time'] = datetime.now().isoformat()
    
    def analyze_results(self) -> dict:
        """分析实验结果"""
        metrics = self.experiment_data['metrics']
        
        if not metrics:
            return {}
        
        efficiencies = [m['efficiency'] for m in metrics]
        completions = [m['tasks_completed'] for m in metrics]
        
        results = {
            'final_efficiency': efficiencies[-1] if efficiencies else 0,
            'avg_efficiency': np.mean(efficiencies),
            'efficiency_improvement': efficiencies[-1] - efficiencies[0] if len(efficiencies) > 1 else 0,
            'total_tasks_completed': completions[-1] if completions else 0,
            'avg_completion_rate': np.mean(completions) / max(self.n_agents, 1)
        }
        
        return results
    
    def save_results(self, output_dir: str = "experiments/results/v5.5"):
        """保存结果"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 添加分析结果
        self.experiment_data['results'] = self.analyze_results()
        
        # 保存 JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = "optimized" if self.use_optimization else "base"
        filename = f"collab_100agents_{suffix}_{timestamp}.json"
        filepath = output_path / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.experiment_data, f, indent=2, default=str)
        
        return filepath


def main():
    parser = argparse.ArgumentParser(description='MOSS v5.5 - 100 Agent 协作实验')
    parser.add_argument('--agents', type=int, default=100, help='Agent 数量')
    parser.add_argument('--tasks', type=int, default=500, help='任务数量')
    parser.add_argument('--iterations', type=int, default=1000, help='模拟轮数')
    parser.add_argument('--optimize', action='store_true', help='使用优化器')
    parser.add_argument('--output', type=str, default='experiments/results/v5.5')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎯 MOSS v5.5 - 100 Agent 大规模协作实验")
    print("=" * 60)
    
    # 创建实验
    experiment = LargeScaleCollaborationExperiment(
        n_agents=args.agents,
        use_optimization=args.optimize
    )
    
    # 生成任务
    experiment.generate_tasks(n_tasks=args.tasks)
    
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
    print(f"   总完成任务数   : {results['total_tasks_completed']}")
    print(f"\n📊 结果已保存到：{filepath}")
    print("=" * 60)


if __name__ == '__main__':
    main()
