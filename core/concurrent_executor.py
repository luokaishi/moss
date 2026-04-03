#!/usr/bin/env python3
"""
MOSS v6.1 - Concurrent Executor
并发执行器

核心功能:
- 线程池管理
- 任务队列
- 异步执行
- 结果聚合

Author: MOSS Project
Date: 2026-04-03
Version: 6.1.0-dev
"""

import threading
import queue
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, Future
import functools


@dataclass
class Task:
    """任务定义"""
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.now)


class TaskQueue:
    """
    任务队列
    
    优先级队列实现
    """
    
    def __init__(self):
        self.queue: queue.PriorityQueue = queue.PriorityQueue()
        self.lock = threading.Lock()
        
        self.stats = {
            'tasks_submitted': 0,
            'tasks_completed': 0,
            'tasks_failed': 0
        }
    
    def submit(self, task: Task):
        """提交任务"""
        # 优先级越低越优先
        self.queue.put((task.priority, task))
        with self.lock:
            self.stats['tasks_submitted'] += 1
    
    def get(self, timeout: float = 1.0) -> Optional[Task]:
        """获取任务"""
        try:
            priority, task = self.queue.get(timeout=timeout)
            return task
        except queue.Empty:
            return None
    
    def task_done(self, success: bool = True):
        """任务完成"""
        self.queue.task_done()
        with self.lock:
            if success:
                self.stats['tasks_completed'] += 1
            else:
                self.stats['tasks_failed'] += 1
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            'stats': self.stats,
            'queue_size': self.queue.qsize()
        }


class Worker(threading.Thread):
    """
    工作线程
    
    执行任务的线程
    """
    
    def __init__(self, worker_id: int, task_queue: TaskQueue):
        super().__init__()
        self.worker_id = worker_id
        self.task_queue = task_queue
        self.running = True
        self.daemon = True
        
        self.stats = {
            'tasks_executed': 0,
            'execution_time': 0.0
        }
    
    def run(self):
        """线程运行"""
        while self.running:
            task = self.task_queue.get(timeout=1.0)
            
            if task is None:
                continue
            
            start_time = time.time()
            try:
                result = task.func(*task.args, **task.kwargs)
                elapsed = time.time() - start_time
                
                self.stats['tasks_executed'] += 1
                self.stats['execution_time'] += elapsed
                
                self.task_queue.task_done(success=True)
                
            except Exception as e:
                self.task_queue.task_done(success=False)
    
    def stop(self):
        """停止线程"""
        self.running = False


class ConcurrentExecutor:
    """
    并发执行器
    
    管理线程池和任务执行
    """
    
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.task_queue = TaskQueue()
        self.workers: List[Worker] = []
        self.running = False
        
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'avg_execution_time': 0.0
        }
    
    def start(self):
        """启动执行器"""
        if self.running:
            return
        
        self.running = True
        
        # 创建工作线程
        for i in range(self.max_workers):
            worker = Worker(i, self.task_queue)
            worker.start()
            self.workers.append(worker)
    
    def stop(self):
        """停止执行器"""
        if not self.running:
            return
        
        self.running = False
        
        # 停止所有工作线程
        for worker in self.workers:
            worker.stop()
        
        # 等待线程结束
        for worker in self.workers:
            worker.join(timeout=2.0)
        
        self.workers = []
    
    def submit(self, func: Callable, *args, 
               priority: int = 0, **kwargs) -> bool:
        """
        提交任务
        
        Args:
            func: 执行函数
            *args: 位置参数
            priority: 优先级 (0-10, 越低越优先)
            **kwargs: 关键字参数
            
        Returns:
            是否成功提交
        """
        if not self.running:
            self.start()
        
        task = Task(
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority
        )
        
        self.task_queue.submit(task)
        self.stats['total_tasks'] += 1
        
        return True
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        同步执行任务
        
        Args:
            func: 执行函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            执行结果
        """
        return func(*args, **kwargs)
    
    def map(self, func: Callable, items: List[Any], 
            parallel: bool = True) -> List[Any]:
        """
        映射执行
        
        Args:
            func: 映射函数
            items: 输入列表
            parallel: 是否并行
            
        Returns:
            结果列表
        """
        if not parallel:
            return [func(item) for item in items]
        
        if not self.running:
            self.start()
        
        results = []
        futures: List[Future] = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for item in items:
                future = executor.submit(func, item)
                futures.append(future)
            
            for future in futures:
                try:
                    result = future.result(timeout=10.0)
                    results.append(result)
                except Exception as e:
                    results.append(None)
        
        return results
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            'stats': self.stats,
            'workers': len(self.workers),
            'max_workers': self.max_workers,
            'running': self.running,
            'queue': self.task_queue.get_stats()
        }


# 测试代码
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v6.1 - Concurrent Executor Test")
    print("=" * 60)
    
    # 创建执行器
    executor = ConcurrentExecutor(max_workers=5)
    
    # 测试任务提交
    print("\n1. 测试任务提交...")
    
    def task_func(x):
        time.sleep(0.1)
        return x * 2
    
    for i in range(10):
        executor.submit(task_func, i, priority=i % 3)
    
    # 等待任务完成
    time.sleep(2.0)
    
    # 获取状态
    status = executor.get_status()
    print(f"   提交任务：{status['stats']['total_tasks']}")
    print(f"   队列大小：{status['queue']['queue_size']}")
    
    # 测试映射
    print("\n2. 测试映射执行...")
    
    def square(x):
        time.sleep(0.05)
        return x * x
    
    start = time.time()
    results = executor.map(square, range(10), parallel=True)
    elapsed = time.time() - start
    
    print(f"   并行执行：{elapsed*1000:.1f}ms")
    print(f"   结果：{results[:5]}...")
    
    # 测试同步执行
    print("\n3. 测试同步执行...")
    result = executor.execute(task_func, 5)
    print(f"   同步结果：{result}")
    
    # 停止执行器
    executor.stop()
    
    # 获取最终状态
    print("\n4. 执行器状态:")
    final_status = executor.get_status()
    print(f"   工作线程：{final_status['workers']}")
    print(f"   运行状态：{final_status['running']}")
    print(f"   总任务数：{final_status['stats']['total_tasks']}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)
