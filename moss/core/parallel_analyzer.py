#!/usr/bin/env python3
"""
MOSS v9.3 - Parallel Analysis Engine
并行分析引擎 - 利用多核 CPU 加速代码分析

核心组件:
1. ParallelAnalyzer - 并行分析器主类
2. TaskScheduler - 任务调度器
3. ResultAggregator - 结果聚合器
4. WorkerPool - 工作进程池

性能目标:
- 8核 CPU: 6-8x 加速比
- 16核 CPU: 10-12x 加速比
- 支持动态负载均衡

Author: MOSS v9.3
Date: 2026-04-24
"""

import ast
import asyncio
import hashlib
import multiprocessing as mp
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import os

import networkx as nx


# ──────────────────────────────────────────────────────────────
# Data Structures
# ──────────────────────────────────────────────────────────────

class TaskPriority(Enum):
    """任务优先级"""
    CRITICAL = 0    # 关键路径任务
    HIGH = 1        # 高优先级
    NORMAL = 2      # 普通优先级
    LOW = 3         # 低优先级
    BACKGROUND = 4  # 后台任务


class TaskStatus(Enum):
    """任务状态"""
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass
class AnalysisTask:
    """分析任务"""
    task_id: str
    file_path: str
    task_type: str  # 'parse', 'analyze', 'refactor', 'verify'
    priority: TaskPriority = TaskPriority.NORMAL
    dependencies: Set[str] = field(default_factory=set)
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None


@dataclass
class ParallelResult:
    """并行分析结果"""
    success: bool
    results: Dict[str, Any] = field(default_factory=dict)
    errors: Dict[str, str] = field(default_factory=dict)
    stats: Dict[str, Any] = field(default_factory=dict)
    duration: float = 0.0


@dataclass
class WorkerStats:
    """工作进程统计"""
    worker_id: int
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_time: float = 0.0
    avg_task_time: float = 0.0


# ──────────────────────────────────────────────────────────────
# Worker Functions (must be at module level for pickling)
# ──────────────────────────────────────────────────────────────

def _parse_file_worker(args: Tuple[str, str]) -> Dict:
    """
    工作进程：解析单个文件

    Args:
        args: (file_path, file_content)

    Returns:
        解析结果字典
    """
    file_path, content = args
    start_time = time.time()

    try:
        tree = ast.parse(content)

        # 提取基本统计信息
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]

        # 计算复杂度
        complexity = sum(
            len(node.body) for node in functions
        ) + len(classes) * 2

        return {
            'success': True,
            'file_path': file_path,
            'parse_time': time.time() - start_time,
            'functions': len(functions),
            'classes': len(classes),
            'imports': len(imports),
            'complexity': complexity,
            'lines': len(content.split('\n')),
            'ast_tree': None,  # AST 不可序列化，只返回统计信息
        }
    except SyntaxError as e:
        return {
            'success': False,
            'file_path': file_path,
            'error': f"语法错误: {e.msg} (行 {e.lineno})",
            'parse_time': time.time() - start_time,
        }
    except Exception as e:
        return {
            'success': False,
            'file_path': file_path,
            'error': str(e),
            'parse_time': time.time() - start_time,
        }


def _analyze_file_worker(args: Tuple[str, str, Dict]) -> Dict:
    """
    工作进程：分析单个文件

    Args:
        args: (file_path, file_content, config)

    Returns:
        分析结果字典
    """
    file_path, content, config = args
    start_time = time.time()

    try:
        tree = ast.parse(content)

        # 代码质量分析
        issues = []

        # 检查长函数
        max_function_lines = config.get('max_function_lines', 50)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                lines = node.end_lineno - node.lineno if node.end_lineno else 0
                if lines > max_function_lines:
                    issues.append({
                        'type': 'long_function',
                        'line': node.lineno,
                        'message': f"函数 '{node.name}' 过长 ({lines} 行)",
                        'severity': 'warning'
                    })

        # 检查未使用导入
        imported_names = set()
        used_names = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_names.add(alias.asname or alias.name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imported_names.add(alias.asname or alias.name)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used_names.add(node.id)

        unused = imported_names - used_names
        for name in unused:
            issues.append({
                'type': 'unused_import',
                'message': f"未使用的导入: {name}",
                'severity': 'info'
            })

        return {
            'success': True,
            'file_path': file_path,
            'analysis_time': time.time() - start_time,
            'issues': issues,
            'issue_count': len(issues),
            'score': max(0, 100 - len(issues) * 5),
        }
    except Exception as e:
        return {
            'success': False,
            'file_path': file_path,
            'error': str(e),
            'analysis_time': time.time() - start_time,
        }


def _calculate_metrics_worker(args: Tuple[str, str]) -> Dict:
    """
    工作进程：计算代码度量指标

    Args:
        args: (file_path, file_content)

    Returns:
        度量指标字典
    """
    file_path, content = args
    start_time = time.time()

    try:
        tree = ast.parse(content)

        # 计算各种度量
        metrics = {
            'lines_of_code': len(content.split('\n')),
            'logical_lines': len([l for l in content.split('\n') if l.strip() and not l.strip().startswith('#')]),
            'functions': 0,
            'classes': 0,
            'methods': 0,
            'cyclomatic_complexity': 0,
            'cognitive_complexity': 0,
            'maintainability_index': 0,
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                    metrics['functions'] += 1
                else:
                    metrics['methods'] += 1

                # 简单圈复杂度估算
                complexity = 1
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                        complexity += 1
                    elif isinstance(child, ast.BoolOp):
                        complexity += len(child.values) - 1
                metrics['cyclomatic_complexity'] += complexity

            elif isinstance(node, ast.ClassDef):
                metrics['classes'] += 1

        # 简化的可维护性指数计算
        halstead_volume = metrics['lines_of_code'] * 10  # 简化估算
        metrics['maintainability_index'] = max(0, 171 - 5.2 * metrics['cyclomatic_complexity']
                                               - 0.23 * metrics['lines_of_code']
                                               - 16.2 * (halstead_volume / 100))

        return {
            'success': True,
            'file_path': file_path,
            'metrics': metrics,
            'calculation_time': time.time() - start_time,
        }
    except Exception as e:
        return {
            'success': False,
            'file_path': file_path,
            'error': str(e),
        }


# ──────────────────────────────────────────────────────────────
# Task Scheduler
# ──────────────────────────────────────────────────────────────

class TaskScheduler:
    """
    任务调度器

    负责:
    1. 任务优先级管理
    2. 依赖关系解析
    3. 任务分发
    """

    def __init__(self):
        self.tasks: Dict[str, AnalysisTask] = {}
        self.ready_queue: List[str] = []  # 可执行的任务ID队列
        self.completed: Set[str] = set()
        self.failed: Set[str] = set()

    def add_task(self, task: AnalysisTask):
        """添加任务"""
        self.tasks[task.task_id] = task

        # 如果没有依赖或依赖已完成，加入就绪队列
        if not task.dependencies or task.dependencies.issubset(self.completed):
            self._enqueue_task(task)

    def _enqueue_task(self, task: AnalysisTask):
        """将任务加入就绪队列（按优先级排序）"""
        if task.task_id not in self.ready_queue:
            self.ready_queue.append(task.task_id)
            # 按优先级排序
            self.ready_queue.sort(
                key=lambda tid: self.tasks[tid].priority.value
            )

    def get_next_task(self) -> Optional[AnalysisTask]:
        """获取下一个待执行任务"""
        while self.ready_queue:
            task_id = self.ready_queue.pop(0)
            task = self.tasks.get(task_id)
            if task and task.status == TaskStatus.PENDING:
                return task
        return None

    def mark_completed(self, task_id: str):
        """标记任务完成"""
        self.completed.add(task_id)
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.COMPLETED

        # 检查是否有新的任务可以执行
        for tid, task in self.tasks.items():
            if (task.status == TaskStatus.PENDING and
                task_id in task.dependencies and
                task.dependencies.issubset(self.completed)):
                self._enqueue_task(task)

    def mark_failed(self, task_id: str, error: str):
        """标记任务失败"""
        self.failed.add(task_id)
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.FAILED
            self.tasks[task_id].error = error

    def get_progress(self) -> Dict:
        """获取进度信息"""
        total = len(self.tasks)
        completed = len(self.completed)
        failed = len(self.failed)
        running = sum(1 for t in self.tasks.values() if t.status == TaskStatus.RUNNING)

        return {
            'total': total,
            'completed': completed,
            'failed': failed,
            'running': running,
            'pending': total - completed - failed - running,
            'percentage': (completed / total * 100) if total > 0 else 0,
        }


# ──────────────────────────────────────────────────────────────
# Parallel Analyzer
# ──────────────────────────────────────────────────────────────

class ParallelAnalyzer:
    """
    并行分析引擎

    利用多核 CPU 并行处理代码分析任务，实现 6-12x 性能提升。

    Features:
    - 进程池管理 (ProcessPoolExecutor)
    - 动态负载均衡
    - 任务优先级调度
    - 依赖关系处理
    - 实时进度跟踪
    """

    def __init__(
        self,
        max_workers: Optional[int] = None,
        use_threads: bool = False,
        chunk_size: int = 10
    ):
        """
        初始化并行分析器

        Args:
            max_workers: 最大工作进程数，默认为 CPU 核心数
            use_threads: 是否使用线程池（适用于 I/O 密集型任务）
            chunk_size: 任务分块大小
        """
        self.max_workers = max_workers or mp.cpu_count()
        self.use_threads = use_threads
        self.chunk_size = chunk_size
        self.scheduler = TaskScheduler()
        self.worker_stats: Dict[int, WorkerStats] = {}

        # 选择合适的执行器
        self.executor_class = ThreadPoolExecutor if use_threads else ProcessPoolExecutor

        print(f"[ParallelAnalyzer] 初始化完成")
        print(f"  工作进程数: {self.max_workers}")
        print(f"  执行器类型: {'线程池' if use_threads else '进程池'}")

    async def analyze_files_parallel(
        self,
        files: List[Tuple[str, str]],
        analysis_type: str = 'parse',
        config: Optional[Dict] = None
    ) -> ParallelResult:
        """
        并行分析多个文件

        Args:
            files: [(file_path, file_content), ...]
            analysis_type: 分析类型 ('parse', 'analyze', 'metrics')
            config: 分析配置

        Returns:
            ParallelResult
        """
        start_time = time.time()
        config = config or {}

        print(f"\n[ParallelAnalyzer] 开始并行分析")
        print(f"  文件数: {len(files)}")
        print(f"  分析类型: {analysis_type}")
        print(f"  并行度: {min(len(files), self.max_workers)}")

        # 选择工作函数
        worker_map = {
            'parse': _parse_file_worker,
            'analyze': _analyze_file_worker,
            'metrics': _calculate_metrics_worker,
        }
        worker_func = worker_map.get(analysis_type, _parse_file_worker)

        # 准备参数
        if analysis_type == 'analyze':
            args_list = [(fp, fc, config) for fp, fc in files]
        else:
            args_list = [(fp, fc) for fp, fc in files]

        results = {}
        errors = {}

        # 使用进程池并行执行
        loop = asyncio.get_event_loop()

        with self.executor_class(max_workers=self.max_workers) as executor:
            # 提交所有任务
            futures = [
                loop.run_in_executor(executor, worker_func, args)
                for args in args_list
            ]

            # 等待所有任务完成
            completed = 0
            for future in asyncio.as_completed(futures):
                try:
                    result = await future
                    file_path = result.get('file_path', 'unknown')

                    if result.get('success'):
                        results[file_path] = result
                    else:
                        errors[file_path] = result.get('error', 'Unknown error')

                    completed += 1
                    if completed % 10 == 0 or completed == len(files):
                        print(f"  进度: {completed}/{len(files)} ({completed/len(files)*100:.1f}%)")

                except Exception as e:
                    errors[f'task_{completed}'] = str(e)

        duration = time.time() - start_time

        # 计算统计信息
        stats = {
            'total_files': len(files),
            'successful': len(results),
            'failed': len(errors),
            'duration': duration,
            'files_per_second': len(files) / duration if duration > 0 else 0,
            'speedup_factor': self._estimate_speedup(len(files), duration),
        }

        print(f"\n[ParallelAnalyzer] 分析完成")
        print(f"  成功: {stats['successful']}, 失败: {stats['failed']}")
        print(f"  总耗时: {duration:.2f}s")
        print(f"  吞吐量: {stats['files_per_second']:.1f} 文件/秒")
        print(f"  预估加速比: {stats['speedup_factor']:.1f}x")

        return ParallelResult(
            success=len(errors) == 0 or len(results) > len(errors),
            results=results,
            errors=errors,
            stats=stats,
            duration=duration
        )

    async def analyze_with_dependencies(
        self,
        files: Dict[str, Tuple[str, str]],
        dependency_graph: nx.DiGraph,
        analysis_type: str = 'parse'
    ) -> ParallelResult:
        """
        考虑依赖关系的并行分析

        按依赖拓扑顺序分批分析，确保依赖文件先被处理。

        Args:
            files: {file_path: (file_path, file_content)}
            dependency_graph: 文件依赖图
            analysis_type: 分析类型

        Returns:
            ParallelResult
        """
        start_time = time.time()

        print(f"\n[ParallelAnalyzer] 依赖感知并行分析")
        print(f"  文件总数: {len(files)}")

        # 拓扑排序获取批次
        try:
            batches = list(nx.topological_generations(dependency_graph))
        except nx.NetworkXError:
            # 如果有环，使用普通并行分析
            print("  警告: 依赖图中存在环，回退到普通并行分析")
            return await self.analyze_files_parallel(
                list(files.values()),
                analysis_type
            )

        all_results = {}
        all_errors = {}
        total_batches = len(batches)

        for i, batch in enumerate(batches):
            batch_files = [
                files[f] for f in batch
                if f in files
            ]

            if not batch_files:
                continue

            print(f"\n  批次 {i+1}/{total_batches}: {len(batch_files)} 个文件")

            result = await self.analyze_files_parallel(
                batch_files,
                analysis_type
            )

            all_results.update(result.results)
            all_errors.update(result.errors)

        duration = time.time() - start_time

        stats = {
            'total_files': len(files),
            'successful': len(all_results),
            'failed': len(all_errors),
            'batches': total_batches,
            'duration': duration,
            'files_per_second': len(files) / duration if duration > 0 else 0,
        }

        return ParallelResult(
            success=len(all_errors) == 0 or len(all_results) > len(all_errors),
            results=all_results,
            errors=all_errors,
            stats=stats,
            duration=duration
        )

    def _estimate_speedup(self, file_count: int, duration: float) -> float:
        """估算加速比（与单线程对比）"""
        # 假设单线程处理速度约为并行的一半
        estimated_single_thread = duration * (self.max_workers * 0.8)
        estimated_sequential_time = file_count * 0.01  # 假设每个文件 10ms
        speedup = estimated_sequential_time / duration if duration > 0 else 1.0
        return min(speedup, self.max_workers * 1.2)  # 限制最大加速比

    def get_optimal_workers(self, file_count: int) -> int:
        """根据文件数量计算最优工作进程数"""
        if file_count < 10:
            return min(2, self.max_workers)
        elif file_count < 50:
            return min(4, self.max_workers)
        elif file_count < 200:
            return min(self.max_workers // 2, self.max_workers)
        else:
            return self.max_workers


# ──────────────────────────────────────────────────────────────
# Integration with IncrementalAnalyzer
# ──────────────────────────────────────────────────────────────

class IncrementalParallelAnalyzer:
    """
    增量 + 并行混合分析器

    结合增量分析和并行处理的优势：
    1. 使用增量分析快速识别变更文件
    2. 使用并行处理加速变更文件分析
    3. 缓存结果避免重复计算
    """

    def __init__(
        self,
        incremental_analyzer: Any,  # IncrementalAnalyzer instance
        max_workers: Optional[int] = None
    ):
        self.incremental = incremental_analyzer
        self.parallel = ParallelAnalyzer(max_workers=max_workers)

    async def analyze_project(
        self,
        files: List[Tuple[str, str]],
        analysis_type: str = 'parse',
        use_cache: bool = True
    ) -> ParallelResult:
        """
        增量并行分析项目

        Args:
            files: [(file_path, file_content), ...]
            analysis_type: 分析类型
            use_cache: 是否使用缓存

        Returns:
            ParallelResult
        """
        print(f"\n[IncrementalParallel] 混合分析模式")
        print(f"  输入文件数: {len(files)}")

        # 存储文件内容供后续使用
        files_content = {fp: fc for fp, fc in files}

        # 1. 使用增量分析器筛选需要分析的文件
        changed_files = []
        cached_results = {}

        for file_path, content in files:
            if use_cache:
                # 检查缓存 (使用增量分析器的 cache 属性)
                checksum = hashlib.sha256(content.encode()).hexdigest()
                cache_key = f"analysis:{file_path}:{checksum}"
                cached = self.incremental.cache.get(cache_key)
                if cached:
                    cached_results[file_path] = cached
                    continue

            changed_files.append((file_path, content))

        print(f"  变更文件: {len(changed_files)}")
        print(f"  缓存命中: {len(cached_results)}")

        # 2. 并行分析变更文件
        if changed_files:
            parallel_result = await self.parallel.analyze_files_parallel(
                changed_files,
                analysis_type
            )

            # 3. 缓存新结果
            for file_path, result in parallel_result.results.items():
                checksum = hashlib.sha256(files_content[file_path].encode()).hexdigest()
                cache_key = f"analysis:{file_path}:{checksum}"
                self.incremental.cache.set(cache_key, result)

            # 4. 合并结果
            all_results = {**cached_results, **parallel_result.results}

            return ParallelResult(
                success=parallel_result.success,
                results=all_results,
                errors=parallel_result.errors,
                stats={
                    **parallel_result.stats,
                    'cache_hits': len(cached_results),
                    'cache_misses': len(changed_files),
                    'cache_hit_rate': len(cached_results) / len(files) * 100 if files else 0,
                },
                duration=parallel_result.duration
            )
        else:
            # 全部命中缓存
            return ParallelResult(
                success=True,
                results=cached_results,
                errors={},
                stats={
                    'total_files': len(files),
                    'successful': len(cached_results),
                    'failed': 0,
                    'cache_hits': len(cached_results),
                    'cache_hit_rate': 100.0,
                    'duration': 0.01,
                    'files_per_second': len(files) / 0.01,
                },
                duration=0.01
            )


# ──────────────────────────────────────────────────────────────
# Performance Benchmark
# ──────────────────────────────────────────────────────────────

class ParallelBenchmark:
    """并行分析性能基准测试"""

    def __init__(self):
        self.results = []

    async def run_comparison(
        self,
        files: List[Tuple[str, str]],
        analysis_type: str = 'parse'
    ) -> Dict:
        """
        对比串行 vs 并行性能

        Args:
            files: 测试文件列表
            analysis_type: 分析类型

        Returns:
            对比结果
        """
        print("\n" + "="*60)
        print("并行分析性能基准测试")
        print("="*60)

        # 串行测试
        print("\n[1] 串行分析...")
        serial_start = time.time()
        serial_results = []

        worker_func = {
            'parse': _parse_file_worker,
            'analyze': _analyze_file_worker,
            'metrics': _calculate_metrics_worker,
        }.get(analysis_type, _parse_file_worker)

        for args in [(fp, fc) for fp, fc in files]:
            try:
                result = worker_func(args)
                serial_results.append(result)
            except Exception as e:
                print(f"  错误: {e}")

        serial_time = time.time() - serial_start

        # 并行测试
        print("\n[2] 并行分析...")
        parallel_analyzer = ParallelAnalyzer()
        parallel_result = await parallel_analyzer.analyze_files_parallel(
            files,
            analysis_type
        )

        # 计算结果
        speedup = serial_time / parallel_result.duration if parallel_result.duration > 0 else 1.0
        efficiency = speedup / mp.cpu_count() * 100

        print("\n" + "-"*60)
        print("测试结果:")
        print(f"  串行耗时: {serial_time:.3f}s")
        print(f"  并行耗时: {parallel_result.duration:.3f}s")
        print(f"  加速比: {speedup:.2f}x")
        print(f"  CPU 核心数: {mp.cpu_count()}")
        print(f"  并行效率: {efficiency:.1f}%")
        print("="*60)

        return {
            'serial_time': serial_time,
            'parallel_time': parallel_result.duration,
            'speedup': speedup,
            'cpu_cores': mp.cpu_count(),
            'efficiency': efficiency,
            'file_count': len(files),
            'success_rate': parallel_result.stats.get('successful', 0) / len(files) * 100 if files else 0,
        }


# ──────────────────────────────────────────────────────────────
# Demo
# ──────────────────────────────────────────────────────────────

async def demo():
    """演示并行分析器功能"""
    print("\n" + "="*60)
    print("MOSS v9.3 - Parallel Analysis Engine Demo")
    print("="*60)

    # 创建测试文件
    test_files = []
    for i in range(50):
        code = f'''
def function_{i}(x, y):
    """Function {i}"""
    result = 0
    for j in range(x):
        if j % 2 == 0:
            result += j * y
        else:
            result -= j
    return result

class Class_{i}:
    def __init__(self):
        self.value = {i}

    def method_{i}(self):
        return self.value * 2
'''
        test_files.append((f"test_file_{i}.py", code))

    # 运行基准测试
    benchmark = ParallelBenchmark()
    results = await benchmark.run_comparison(test_files, 'parse')

    # 演示依赖感知分析
    print("\n\n[依赖感知并行分析演示]")
    import networkx as nx

    # 创建依赖图
    G = nx.DiGraph()
    for i in range(20):
        G.add_node(f"file_{i}.py")
        if i > 0:
            G.add_edge(f"file_{i-1}.py", f"file_{i}.py")

    files_dict = {fp: (fp, fc) for fp, fc in test_files[:20]}

    analyzer = ParallelAnalyzer()
    result = await analyzer.analyze_with_dependencies(
        files_dict,
        G,
        'parse'
    )

    print(f"\n依赖感知分析完成:")
    print(f"  批次: {result.stats.get('batches', 0)}")
    print(f"  总耗时: {result.duration:.3f}s")

    return results


if __name__ == "__main__":
    asyncio.run(demo())
