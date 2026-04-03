#!/usr/bin/env python3
"""
MOSS v6.0 - Open Environment 72h Experiment
开放环境 72h 实验

实验目标:
- 验证真实世界交互能力
- 测量任务完成率
- 评估 API 调用成功率
- 测试错误恢复能力

Author: MOSS Project
Date: 2026-04-03
Version: 6.0.0-dev
"""

import argparse
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

from core.open_environment import OpenEnvironment
from tools.web_automation import WebAutomation
from tools.api_integration import APIIntegration, APIConfig


class OpenEnvironmentExperiment:
    """开放环境实验管理器"""
    
    def __init__(self, duration_hours: int = 72, 
                 checkpoint_interval: int = 3600):
        self.duration_hours = duration_hours
        self.checkpoint_interval = checkpoint_interval
        
        # 初始化模块
        print("🔧 初始化实验环境...")
        self.env = OpenEnvironment("./experiment_workspace")
        self.web = WebAutomation()
        
        api_config = APIConfig(
            base_url='https://httpbin.org',
            rate_limit=60,
            timeout=10
        )
        self.api = APIIntegration(api_config)
        
        # 实验状态
        self.running = False
        self.start_time = None
        self.checkpoints = []
        
        # 实验数据
        self.experiment_data = {
            'config': {
                'duration_hours': duration_hours,
                'checkpoint_interval': checkpoint_interval
            },
            'metrics': [],
            'events': []
        }
        
        print("   ✅ 开放环境")
        print("   ✅ Web 自动化")
        print("   ✅ API 集成")
    
    def generate_tasks(self) -> list:
        """生成实验任务"""
        task_templates = [
            {'type': 'fs_scan', 'desc': '扫描目录', 'params': {'path': '.', 'max_depth': 2}},
            {'type': 'fs_read', 'desc': '读取文件', 'params': {'path': 'test.txt'}},
            {'type': 'fs_write', 'desc': '写入文件', 'params': {'path': 'output.txt', 'content': 'test'}},
            {'type': 'api_get', 'desc': 'API GET', 'params': {'endpoint': '/get', 'params': {'test': 'value'}}},
            {'type': 'api_post', 'desc': 'API POST', 'params': {'endpoint': '/post', 'data': {'key': 'value'}}},
        ]
        
        tasks = []
        for i in range(np.random.randint(10, 30)):
            template = np.random.choice(task_templates)
            tasks.append({
                'id': f'task_{datetime.now().strftime("%Y%m%d_%H%M%S")}_{i}',
                'type': template['type'],
                'description': template['desc'],
                'params': template['params']
            })
        
        return tasks
    
    def execute_task(self, task: dict) -> bool:
        """执行单个任务"""
        try:
            task_type = task['type']
            params = task['params']
            
            if task_type.startswith('fs_'):
                success, _ = self.env.execute_action(task_type, **params)
            elif task_type.startswith('api_'):
                success, _ = self.api.execute_action(task_type, **params)
            else:
                success = False
            
            return success
        except Exception as e:
            return False
    
    def run_experiment_cycle(self) -> tuple:
        """运行一个实验周期"""
        tasks = self.generate_tasks()
        
        completed = 0
        failed = 0
        api_success = 0
        api_total = 0
        fs_success = 0
        fs_total = 0
        
        for task in tasks:
            success = self.execute_task(task)
            
            if success:
                completed += 1
            else:
                failed += 1
            
            if task['type'].startswith('api_'):
                api_total += 1
                if success:
                    api_success += 1
            elif task['type'].startswith('fs_'):
                fs_total += 1
                if success:
                    fs_success += 1
        
        return completed, failed, api_success, api_total, fs_success, fs_total
    
    def save_checkpoint(self):
        """保存检查点"""
        checkpoint = {
            'timestamp': datetime.now().isoformat(),
            'elapsed_hours': (datetime.now() - self.start_time).total_seconds() / 3600,
            'metrics': self.experiment_data['metrics'][-1] if self.experiment_data['metrics'] else {}
        }
        
        self.checkpoints.append(checkpoint)
        self.experiment_data['checkpoints'] = self.checkpoints
        
        # 保存到文件
        checkpoint_file = Path(f"./experiment_checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        
        print(f"   💾 检查点已保存")
    
    def run_simulation(self, n_iterations: int = 100):
        """运行模拟实验"""
        print(f"\n🚀 开始 {n_iterations} 轮开放环境模拟...")
        
        for iteration in range(n_iterations):
            # 运行周期
            completed, failed, api_success, api_total, fs_success, fs_total = self.run_experiment_cycle()
            
            # 记录指标
            self.experiment_data['metrics'].append({
                'iteration': iteration,
                'timestamp': datetime.now().isoformat(),
                'tasks_completed': completed,
                'tasks_failed': failed,
                'task_success_rate': completed / max(completed + failed, 1),
                'api_success_rate': api_success / max(api_total, 1),
                'fs_success_rate': fs_success / max(fs_total, 1)
            })
            
            # 保存检查点
            if iteration % 20 == 0:
                print(f"\n📍 迭代 {iteration}...")
                self.save_checkpoint()
            
            # 短暂休息
            time.sleep(0.1)
        
        self.experiment_data['end_time'] = datetime.now().isoformat()
    
    def analyze_results(self) -> dict:
        """分析实验结果"""
        metrics = self.experiment_data['metrics']
        
        if not metrics:
            return {}
        
        final = metrics[-1]
        
        avg_task_rate = np.mean([m['task_success_rate'] for m in metrics])
        avg_api_rate = np.mean([m['api_success_rate'] for m in metrics])
        avg_fs_rate = np.mean([m['fs_success_rate'] for m in metrics])
        
        return {
            'final_task_success_rate': final.get('task_success_rate', 0),
            'avg_task_success_rate': avg_task_rate,
            'avg_api_success_rate': avg_api_rate,
            'avg_fs_success_rate': avg_fs_rate,
            'total_iterations': len(metrics)
        }
    
    def save_results(self, output_dir: str = "experiments/results/v6.0"):
        """保存结果"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        self.experiment_data['results'] = self.analyze_results()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"open_env_{timestamp}.json"
        filepath = output_path / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.experiment_data, f, indent=2, default=str)
        
        return filepath


def main():
    parser = argparse.ArgumentParser(description='MOSS v6.0 - 开放环境实验')
    parser.add_argument('--iterations', type=int, default=100, help='模拟轮数')
    parser.add_argument('--output', type=str, default='experiments/results/v6.0')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎯 MOSS v6.0 - 开放环境实验")
    print("=" * 60)
    
    # 创建实验
    experiment = OpenEnvironmentExperiment()
    
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
    print(f"   平均任务成功率   : {results['avg_task_success_rate']:.1%}")
    print(f"   平均 API 成功率    : {results['avg_api_success_rate']:.1%}")
    print(f"   平均文件系统成功率 : {results['avg_fs_success_rate']:.1%}")
    print(f"   总迭代数         : {results['total_iterations']}")
    print(f"\n📊 结果已保存到：{filepath}")
    print("=" * 60)


if __name__ == '__main__':
    main()
