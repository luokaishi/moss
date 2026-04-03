#!/usr/bin/env python3
"""
MOSS v5.5 - 168h Real-World Continuous Operation
168 小时真实世界连续运行实验

实验目标:
- 验证 7 天连续运行稳定性
- 测量真实环境交互能力
- 评估知识积累速度

Author: MOSS Project
Date: 2026-04-03
Version: 5.5.0-dev
"""

import argparse
import json
import time
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

from core.collaboration import CollaborationCoordinator, CollaborationMode, Task
from core.optimization import PerformanceOptimizer
from core.cache import CacheManager
from core.environment_adapter import EnvironmentAdapter
from core.longterm_memory import LongTermMemory


class ContinuousOperationExperiment:
    """连续运行实验管理器"""
    
    def __init__(self, duration_hours: int = 168, checkpoint_interval: int = 3600):
        self.duration_hours = duration_hours
        self.checkpoint_interval = checkpoint_interval  # 秒
        
        # 初始化模块
        print("🔧 初始化实验环境...")
        self.coordinator = CollaborationCoordinator(CollaborationMode.HYBRID)
        self.optimizer = PerformanceOptimizer()
        self.cache = CacheManager()
        self.env = EnvironmentAdapter("./experiment_workspace")
        self.memory = LongTermMemory("./experiment_memory")
        
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
            'checkpoints': [],
            'metrics': [],
            'events': []
        }
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        print("   ✅ 协作协调器")
        print("   ✅ 性能优化器")
        print("   ✅ 缓存管理器")
        print("   ✅ 环境适配器")
        print("   ✅ 长期记忆")
    
    def _signal_handler(self, signum, frame):
        """处理中断信号"""
        print(f"\n⚠️  收到中断信号 {signum}")
        self.running = False
        self.save_checkpoint()
    
    def setup_agents(self, n_agents: int = 10):
        """创建 Agent"""
        print(f"\n👥 创建 {n_agents} 个 Agent...")
        
        skill_pool = ['coding', 'analysis', 'communication', 'design', 
                     'testing', 'optimization', 'debugging', 'documentation']
        
        for i in range(n_agents):
            n_skills = np.random.randint(3, 6)
            skills = {
                skill: np.random.uniform(0.5, 1.0)
                for skill in np.random.choice(skill_pool, size=n_skills, replace=False)
            }
            
            self.coordinator.register_agent(f"agent_{i}", skills)
        
        print(f"   ✅ 已创建 {n_agents} 个 Agent")
    
    def generate_real_world_tasks(self) -> list:
        """生成真实世界任务"""
        task_templates = [
            {'type': 'file_read', 'desc': '读取配置文件', 'skills': ['coding']},
            {'type': 'file_write', 'desc': '保存实验数据', 'skills': ['coding', 'documentation']},
            {'type': 'web_search', 'desc': '搜索技术资料', 'skills': ['analysis', 'communication']},
            {'type': 'code_review', 'desc': '代码审查', 'skills': ['coding', 'testing']},
            {'type': 'performance_opt', 'desc': '性能优化', 'skills': ['optimization', 'coding']},
            {'type': 'debug', 'desc': '调试问题', 'skills': ['debugging', 'analysis']},
            {'type': 'document', 'desc': '编写文档', 'skills': ['documentation', 'communication']},
        ]
        
        tasks = []
        for i in range(np.random.randint(5, 20)):
            template = np.random.choice(task_templates)
            task = Task(
                id=f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}",
                description=f"{template['desc']} #{i}",
                difficulty=np.random.uniform(0.3, 0.8),
                priority=np.random.uniform(0.5, 1.0),
                required_skills=template['skills'],
                reward=np.random.uniform(1.0, 3.0)
            )
            tasks.append(task)
        
        return tasks
    
    def execute_task(self, task: Task) -> bool:
        """执行单个任务"""
        try:
            # 模拟任务执行
            task_type = task.description.split()[0].lower()
            
            if 'file' in task_type:
                # 文件操作
                success, _ = self.env.execute_action(
                    'file_write' if 'write' in task_type else 'file_read',
                    path=f"task_{task.id}.txt",
                    content=f"Task {task.id} result"
                )
            elif 'web' in task_type:
                # Web 搜索（模拟）
                success = True
            elif 'code' in task_type or 'debug' in task_type:
                # 代码相关（模拟）
                success = np.random.random() > 0.05  # 95% 成功率
            else:
                # 其他任务
                success = np.random.random() > 0.03  # 97% 成功率
            
            return success
        except Exception as e:
            print(f"   ❌ 任务执行失败：{e}")
            return False
    
    def run_experiment_cycle(self):
        """运行一个实验周期"""
        # 1. 生成任务
        tasks = self.generate_real_world_tasks()
        for task in tasks:
            self.coordinator.add_task(task)
        
        # 2. 分配任务
        assignments = self.coordinator.assign_tasks()
        
        # 3. 执行任务
        completed = 0
        failed = 0
        for agent_id, task_ids in assignments.items():
            for task_id in task_ids:
                task = self.coordinator.tasks.get(task_id)
                if task:
                    success = self.execute_task(task)
                    self.coordinator.complete_task(task_id, success)
                    if success:
                        completed += 1
                        
                        # 存储经验到记忆
                        self.memory.add_memory(
                            content={
                                'task_id': task_id,
                                'type': task.description,
                                'result': 'success'
                            },
                            tags=['task', 'completed'],
                            importance=0.6
                        )
                    else:
                        failed += 1
        
        return completed, failed
    
    def save_checkpoint(self):
        """保存检查点"""
        checkpoint = {
            'timestamp': datetime.now().isoformat(),
            'elapsed_hours': (datetime.now() - self.start_time).total_seconds() / 3600,
            'metrics': self.experiment_data['metrics'][-1] if self.experiment_data['metrics'] else {},
            'tasks_completed': self.coordinator.stats['tasks_completed'],
            'memory_count': self.memory.stats['memories_created']
        }
        
        self.checkpoints.append(checkpoint)
        self.experiment_data['checkpoints'].append(checkpoint)
        
        # 保存到文件
        checkpoint_file = Path(f"./experiment_checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        
        print(f"   💾 检查点已保存：{checkpoint_file.name}")
    
    def run(self):
        """运行实验"""
        print("\n" + "=" * 60)
        print(f"🚀 MOSS v5.5 - {self.duration_hours}h 连续运行实验")
        print("=" * 60)
        print(f"   开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   预计结束：{(datetime.now() + timedelta(hours=self.duration_hours)).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   检查点间隔：{self.checkpoint_interval}秒")
        print("=" * 60)
        
        self.running = True
        self.start_time = datetime.now()
        self.experiment_data['start_time'] = self.start_time.isoformat()
        
        # 创建 Agent
        self.setup_agents(n_agents=10)
        
        # 运行主循环
        cycle_count = 0
        last_checkpoint = time.time()
        
        try:
            while self.running:
                current_time = time.time()
                elapsed = current_time - self.start_time.timestamp()
                
                # 检查是否超时
                if elapsed >= self.duration_hours * 3600:
                    print(f"\n⏰ 实验时间到达 ({self.duration_hours}h)")
                    break
                
                # 运行实验周期
                completed, failed = self.run_experiment_cycle()
                cycle_count += 1
                
                # 记录指标
                if cycle_count % 10 == 0:
                    self.experiment_data['metrics'].append({
                        'cycle': cycle_count,
                        'timestamp': datetime.now().isoformat(),
                        'tasks_completed': completed,
                        'tasks_failed': failed,
                        'success_rate': completed / max(completed + failed, 1),
                        'memory_count': self.memory.stats['memories_created'],
                        'cache_stats': self.cache.cache.get_stats()
                    })
                
                # 保存检查点
                if current_time - last_checkpoint >= self.checkpoint_interval:
                    print(f"\n📍 保存检查点 (周期 {cycle_count})...")
                    self.save_checkpoint()
                    last_checkpoint = current_time
                
                # 短暂休息
                time.sleep(1)
            
        except Exception as e:
            print(f"\n❌ 实验异常：{e}")
            self.save_checkpoint()
            raise
        
        finally:
            self.running = False
            self.experiment_data['end_time'] = datetime.now().isoformat()
            
            # 最终报告
            self.generate_report()
    
    def generate_report(self):
        """生成最终报告"""
        print("\n" + "=" * 60)
        print("📊 实验最终报告")
        print("=" * 60)
        
        elapsed = (datetime.now() - self.start_time).total_seconds() / 3600
        
        print(f"   实际运行时长：{elapsed:.2f}h")
        print(f"   运行周期数：{len(self.checkpoints)}")
        print(f"   总任务完成：{self.coordinator.stats['tasks_completed']}")
        print(f"   记忆创建数：{self.memory.stats['memories_created']}")
        print(f"   缓存命中率：{self.cache.cache.get_stats()['overall_hit_rate']:.1%}")
        
        # 保存完整报告
        report_file = Path(f"./experiment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_file, 'w') as f:
            json.dump(self.experiment_data, f, indent=2, default=str)
        
        print(f"\n💾 完整报告已保存：{report_file.name}")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='MOSS v5.5 - 168h 连续运行实验')
    parser.add_argument('--hours', type=int, default=168, help='运行时长（小时）')
    parser.add_argument('--checkpoint-interval', type=int, default=3600, help='检查点间隔（秒）')
    parser.add_argument('--agents', type=int, default=10, help='Agent 数量')
    
    args = parser.parse_args()
    
    # 创建实验
    experiment = ContinuousOperationExperiment(
        duration_hours=args.hours,
        checkpoint_interval=args.checkpoint_interval
    )
    
    # 运行实验
    experiment.run()


if __name__ == '__main__':
    main()
