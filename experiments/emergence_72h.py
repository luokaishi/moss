#!/usr/bin/env python3
"""
MOSS v5.6 - Goal Emergence Experiment
目标涌现实验

实验目标:
- 验证开放目标自主涌现
- 测量目标层次演化
- 评估价值对齐度

Author: MOSS Project
Date: 2026-04-03
Version: 5.6.0-dev
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
import numpy as np

from core.open_ended_goals import GoalGenerator, GoalType
from core.goal_evolution import GoalEvolution


class GoalEmergenceExperiment:
    """目标涌现实验管理器"""
    
    def __init__(self, duration_hours: int = 72, n_agents: int = 50):
        self.duration_hours = duration_hours
        self.n_agents = n_agents
        
        # 初始化模块
        print("🔧 初始化涌现实验...")
        self.goal_generator = GoalGenerator()
        self.goal_evolution = GoalEvolution(population_size=n_agents)
        
        # 实验数据
        self.experiment_data = {
            'config': {
                'duration_hours': duration_hours,
                'n_agents': n_agents
            },
            'metrics': [],
            'emergence_events': []
        }
        
        print("   ✅ 目标生成器")
        print("   ✅ 目标演化引擎")
    
    def run_emergence_simulation(self, n_iterations: int = 1000):
        """运行涌现模拟"""
        print(f"\n🚀 开始 {n_iterations} 轮涌现模拟...")
        print(f"   Agent 数量：{self.n_agents}")
        print(f"   模拟轮数：{n_iterations}")
        
        # 初始化目标种群
        base_goals = []
        for i in range(min(10, self.n_agents)):
            context = {
                'critical_resource': 'computational_power',
                'current_domain': 'ai_research',
                'urgency': np.random.uniform(0.3, 0.8),
                'alignment': np.random.uniform(0.5, 0.9)
            }
            goal = self.goal_generator.generate_goal(context)
            if goal:
                base_goals.append(goal)
        
        self.goal_evolution.initialize_population(base_goals)
        
        # 演化多代
        for iteration in range(n_iterations):
            # 1. 演化一代
            self.goal_evolution.evolve_generation(
                mutation_rate=0.15,
                crossover_rate=0.75
            )
            
            # 2. 生成新目标
            context = {
                'critical_resource': 'data',
                'current_domain': 'machine_learning',
                'urgency': np.random.uniform(0.4, 0.9),
                'alignment': np.random.uniform(0.6, 0.95)
            }
            
            # 基于主导驱动力生成新目标
            if np.random.random() < 0.3:  # 30% 概率生成新目标
                best_goal = self.goal_evolution.get_best_goal()
                new_goal = self.goal_generator.generate_goal(context, parent_goal=best_goal)
                if new_goal:
                    self.goal_evolution.goals.append(new_goal)
                    self.experiment_data['emergence_events'].append({
                        'iteration': iteration,
                        'event': 'new_goal_emerged',
                        'goal_type': new_goal.goal_type.value
                    })
            
            # 3. 记录指标
            if iteration % 100 == 0:
                status = self.goal_evolution.get_status()
                best_goal = self.goal_evolution.get_best_goal()
                
                self.experiment_data['metrics'].append({
                    'iteration': iteration,
                    'population_size': status['population_size'],
                    'avg_fitness': status['avg_fitness'],
                    'best_fitness': status['best_fitness'],
                    'diversity': status['diversity'],
                    'generations': status['generations'],
                    'hierarchy_depth': self.goal_generator.stats['hierarchy_depth'],
                    'best_goal_type': best_goal.goal_type.value if best_goal else None
                })
        
        self.experiment_data['end_time'] = datetime.now().isoformat()
    
    def analyze_emergence(self) -> dict:
        """分析涌现结果"""
        metrics = self.experiment_data['metrics']
        
        if not metrics:
            return {}
        
        # 计算涌现指标
        final_metrics = metrics[-1] if metrics else {}
        initial_metrics = metrics[0] if metrics else {}
        
        results = {
            'final_population': final_metrics.get('population_size', 0),
            'final_avg_fitness': final_metrics.get('avg_fitness', 0),
            'final_best_fitness': final_metrics.get('best_fitness', 0),
            'fitness_improvement': (
                final_metrics.get('best_fitness', 0) - 
                initial_metrics.get('best_fitness', 0)
            ),
            'diversity': final_metrics.get('diversity', 0),
            'hierarchy_depth': final_metrics.get('hierarchy_depth', 0),
            'total_generations': final_metrics.get('generations', 0),
            'emergence_events': len(self.experiment_data['emergence_events']),
            'goal_type_distribution': self.goal_generator.stats['by_type']
        }
        
        return results
    
    def save_results(self, output_dir: str = "experiments/results/v5.6"):
        """保存结果"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 添加分析结果
        self.experiment_data['results'] = self.analyze_emergence()
        
        # 保存 JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"emergence_{timestamp}.json"
        filepath = output_path / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.experiment_data, f, indent=2, default=str)
        
        return filepath


def main():
    parser = argparse.ArgumentParser(description='MOSS v5.6 - 目标涌现实验')
    parser.add_argument('--agents', type=int, default=50, help='Agent 数量')
    parser.add_argument('--iterations', type=int, default=1000, help='模拟轮数')
    parser.add_argument('--output', type=str, default='experiments/results/v5.6')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎯 MOSS v5.6 - 目标涌现实验")
    print("=" * 60)
    
    # 创建实验
    experiment = GoalEmergenceExperiment(
        n_agents=args.agents
    )
    
    # 运行模拟
    experiment.run_emergence_simulation(n_iterations=args.iterations)
    
    # 分析结果
    results = experiment.analyze_emergence()
    
    # 保存结果
    filepath = experiment.save_results(args.output)
    
    # 打印结果
    print("\n" + "=" * 60)
    print("🎉 实验完成！")
    print("=" * 60)
    print(f"   最终种群大小   : {results['final_population']}")
    print(f"   平均适应度     : {results['final_avg_fitness']:.3f}")
    print(f"   最佳适应度     : {results['final_best_fitness']:.3f}")
    print(f"   适应度提升     : {results['fitness_improvement']:+.3f}")
    print(f"   种群多样性     : {results['diversity']:.3f}")
    print(f"   层次深度       : {results['hierarchy_depth']}")
    print(f"   总代数         : {results['total_generations']}")
    print(f"   涌现事件       : {results['emergence_events']}")
    print(f"\n📊 结果已保存到：{filepath}")
    print("=" * 60)


if __name__ == '__main__':
    main()
