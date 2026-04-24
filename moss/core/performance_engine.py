#!/usr/bin/env python3
"""
MOSS v9.3 - Performance Engine
性能引擎 - 整合增量分析 + 并行处理

这是 v9.3.0 Phase 1 的核心集成模块，提供：
1. 智能缓存策略 (L1/L2/L3)
2. 并行代码分析
3. 性能监控和基准测试
4. 与 CrossFileRefactorEngine 无缝集成

Author: MOSS v9.3
Date: 2026-04-24
"""

import ast
import asyncio
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# 导入 v9.3 新组件
from .incremental_analyzer import (
    IncrementalAnalyzer,
    MultiLevelCache,
    PerformanceBenchmark
)
from .parallel_analyzer import (
    ParallelAnalyzer,
    IncrementalParallelAnalyzer,
    ParallelBenchmark
)

# 导入 v9.2 现有组件
from .cross_file_refactor import (
    CrossFileRefactorEngine,
    ImportGraphBuilder,
    SymbolTracker,
    ImpactAnalyzer,
    RefactoringResult
)


@dataclass
class PerformanceConfig:
    """性能引擎配置"""
    # 缓存配置
    enable_l1_cache: bool = True      # 内存缓存
    enable_l2_cache: bool = True      # SQLite 缓存
    enable_l3_cache: bool = True      # JSON 项目缓存
    l1_cache_size: int = 1000         # L1 缓存条目数
    l2_cache_ttl: int = 3600          # L2 缓存 TTL (秒)

    # 并行配置
    enable_parallel: bool = True
    max_workers: Optional[int] = None  # None = 自动检测 CPU 核心数
    use_thread_pool: bool = False      # False = 进程池（适合 CPU 密集型）

    # 增量分析配置
    enable_incremental: bool = True
    checksum_algorithm: str = 'sha256'

    # 性能目标
    target_speedup: float = 10.0       # 目标加速比
    target_throughput: int = 500       # 目标吞吐量 (文件/秒)


@dataclass
class AnalysisReport:
    """分析报告"""
    file_count: int
    duration: float
    cache_hits: int
    cache_misses: int
    parallel_speedup: float
    issues_found: int
    timestamp: float = field(default_factory=time.time)


class PerformanceEngine:
    """
    MOSS v9.3 性能引擎

    整合增量分析、多层缓存和并行处理，实现 10x+ 性能提升。

    Architecture:
    ┌─────────────────────────────────────────────┐
    │           PerformanceEngine                 │
    ├─────────────────────────────────────────────┤
    │  ┌─────────────┐    ┌──────────────────┐   │
    │  │ Incremental │◄──►│ ParallelAnalyzer │   │
    │  │  Analyzer   │    │                  │   │
    │  └──────┬──────┘    └──────────────────┘   │
    │         │                                   │
    │  ┌──────▼──────┐    ┌──────────────────┐   │
    │  │MultiLevel   │    │ CrossFileRefactor │   │
    │  │   Cache     │◄──►│     Engine       │   │
    │  └─────────────┘    └──────────────────┘   │
    └─────────────────────────────────────────────┘
    """

    def __init__(
        self,
        codebase_path: Union[str, Path],
        config: Optional[PerformanceConfig] = None
    ):
        """
        初始化性能引擎

        Args:
            codebase_path: 代码库路径
            config: 性能配置
        """
        self.codebase_path = Path(codebase_path)
        self.config = config or PerformanceConfig()

        print("\n" + "="*60)
        print("MOSS v9.3 - Performance Engine 初始化")
        print("="*60)

        # 初始化多层缓存
        self.cache = MultiLevelCache(
            str(self.codebase_path)
        ) if (self.config.enable_l1_cache or
              self.config.enable_l2_cache or
              self.config.enable_l3_cache) else None

        # 初始化增量分析器
        self.incremental = IncrementalAnalyzer(
            str(self.codebase_path)
        ) if self.config.enable_incremental else None

        # 初始化并行分析器
        self.parallel = ParallelAnalyzer(
            max_workers=self.config.max_workers,
            use_threads=self.config.use_thread_pool
        ) if self.config.enable_parallel else None

        # 初始化混合分析器（增量 + 并行）
        if self.incremental and self.parallel:
            self.hybrid = IncrementalParallelAnalyzer(
                self.incremental,
                max_workers=self.config.max_workers
            )
        else:
            self.hybrid = None

        # 初始化跨文件重构引擎
        self.refactor_engine = CrossFileRefactorEngine(codebase_path)

        # 性能统计
        self.stats = {
            'analyses_run': 0,
            'total_time_saved': 0.0,
            'cache_hits_total': 0,
            'cache_misses_total': 0,
        }

        print(f"配置状态:")
        print(f"  增量分析: {'✓' if self.incremental else '✗'}")
        print(f"  多层缓存: {'✓' if self.cache else '✗'}")
        print(f"  并行处理: {'✓' if self.parallel else '✗'}")
        print(f"  混合模式: {'✓' if self.hybrid else '✗'}")
        print("="*60)

    async def analyze_codebase(
        self,
        file_paths: Optional[List[str]] = None,
        analysis_type: str = 'full',
        use_incremental: bool = True,
        use_parallel: bool = True
    ) -> AnalysisReport:
        """
        分析代码库（智能选择最优策略）

        Args:
            file_paths: 指定文件列表，None = 分析整个代码库
            analysis_type: 分析类型 ('parse', 'analyze', 'metrics', 'full')
            use_incremental: 使用增量分析
            use_parallel: 使用并行处理

        Returns:
            AnalysisReport
        """
        start_time = time.time()

        # 1. 收集文件
        if file_paths is None:
            file_paths = self._collect_python_files()

        print(f"\n[PerformanceEngine] 开始分析")
        print(f"  文件数: {len(file_paths)}")
        print(f"  分析类型: {analysis_type}")

        # 2. 读取文件内容
        files_content = []
        for fp in file_paths:
            path = self.codebase_path / fp
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        files_content.append((str(path), f.read()))
                except Exception as e:
                    print(f"  警告: 无法读取 {fp}: {e}")

        # 3. 选择分析策略
        if use_incremental and use_parallel and self.hybrid:
            # 混合模式：增量 + 并行
            print("  策略: 增量并行混合")
            result = await self.hybrid.analyze_project(
                files_content,
                analysis_type,
                use_cache=True
            )
        elif use_parallel and self.parallel and len(files_content) > 10:
            # 纯并行模式
            print("  策略: 并行分析")
            result = await self.parallel.analyze_files_parallel(
                files_content,
                analysis_type
            )
        elif use_incremental and self.incremental:
            # 纯增量模式
            print("  策略: 增量分析")
            result = await self._run_incremental_only(files_content, analysis_type)
        else:
            # 串行模式（回退）
            print("  策略: 串行分析")
            result = await self._run_serial(files_content, analysis_type)

        duration = time.time() - start_time

        # 4. 更新统计
        self.stats['analyses_run'] += 1
        cache_hits = result.stats.get('cache_hits', 0)
        cache_misses = result.stats.get('cache_misses', len(files_content))
        self.stats['cache_hits_total'] += cache_hits
        self.stats['cache_misses_total'] += cache_misses

        # 估算节省时间
        estimated_serial_time = len(files_content) * 0.05  # 假设每个文件 50ms
        time_saved = estimated_serial_time - duration
        self.stats['total_time_saved'] += max(0, time_saved)

        # 5. 生成报告
        report = AnalysisReport(
            file_count=len(files_content),
            duration=duration,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            parallel_speedup=result.stats.get('speedup_factor', 1.0),
            issues_found=sum(
                r.get('issue_count', 0)
                for r in result.results.values()
                if isinstance(r, dict)
            )
        )

        print(f"\n[PerformanceEngine] 分析完成")
        print(f"  耗时: {duration:.2f}s")
        print(f"  缓存命中: {cache_hits}/{len(files_content)} ({cache_hits/len(files_content)*100:.1f}%)")
        print(f"  加速比: {report.parallel_speedup:.1f}x")
        print(f"  发现问题: {report.issues_found}")

        return report

    async def refactor_with_performance(
        self,
        symbol_name: str,
        source_module: str,
        target_module: str,
        dry_run: bool = False
    ) -> RefactoringResult:
        """
        高性能重构（先增量分析影响范围，再执行）

        Args:
            symbol_name: 符号名
            source_module: 源模块
            target_module: 目标模块
            dry_run: 是否只预览

        Returns:
            RefactoringResult
        """
        print(f"\n[PerformanceEngine] 高性能重构")
        print(f"  移动: {symbol_name}")
        print(f"  从: {source_module} → {target_module}")

        # 1. 快速影响分析（使用缓存）
        if self.incremental:
            impact_set = await self.incremental.get_impact_set(
                f"{source_module}.{symbol_name}"
            )
            print(f"  影响范围: {len(impact_set)} 个文件")

        # 2. 使用重构引擎执行
        result = await self.refactor_engine.move_symbol(
            symbol_name,
            source_module,
            target_module,
            dry_run
        )

        # 3. 如果成功，使相关缓存失效
        if result.success and self.cache:
            for file_path in result.files_modified:
                self.cache.invalidate(str(file_path))
            print(f"  已使 {len(result.files_modified)} 个缓存项失效")

        return result

    async def run_performance_benchmark(self) -> Dict:
        """
        运行完整性能基准测试

        Returns:
            基准测试结果
        """
        print("\n" + "="*60)
        print("MOSS v9.3 - 性能基准测试")
        print("="*60)

        # 收集测试文件
        test_files = self._collect_python_files()
        if len(test_files) < 10:
            print("文件数量不足，跳过基准测试")
            return {'error': 'Insufficient files'}

        # 限制测试文件数量
        test_files = test_files[:100]
        files_content = []
        for fp in test_files[:50]:
            path = self.codebase_path / fp
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    files_content.append((str(path), f.read()))

        results = {}

        # 1. 测试并行分析
        if self.parallel:
            print("\n[1] 并行分析性能测试")
            parallel_benchmark = ParallelBenchmark()
            parallel_results = await parallel_benchmark.run_comparison(
                files_content,
                'parse'
            )
            results['parallel'] = parallel_results

        # 2. 测试增量分析
        if self.incremental:
            print("\n[2] 增量分析性能测试")
            incremental_benchmark = PerformanceBenchmark()

            # 模拟分析函数
            async def mock_analyzer(file_path: Path) -> Dict:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    tree = ast.parse(content)
                    return {
                        'functions': len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
                        'classes': len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
                    }
                except:
                    return {'functions': 0, 'classes': 0}

            # 运行基准测试
            file_paths = [Path(fp) for fp, _ in files_content]
            bench_result = await incremental_benchmark.benchmark(
                file_paths,
                mock_analyzer,
                iterations=2
            )

            results['incremental'] = {
                'avg_time': bench_result.get('avg_time', 0),
                'min_time': bench_result.get('min_time', 0),
                'max_time': bench_result.get('max_time', 0),
            }

        # 3. 测试混合模式
        if self.hybrid:
            print("\n[3] 混合模式性能测试")
            start = time.time()
            hybrid_result = await self.hybrid.analyze_project(
                files_content,
                'parse',
                use_cache=True
            )
            results['hybrid'] = {
                'duration': time.time() - start,
                'cache_hits': hybrid_result.stats.get('cache_hits', 0),
                'throughput': hybrid_result.stats.get('files_per_second', 0),
            }

        # 汇总
        print("\n" + "="*60)
        print("性能基准测试汇总")
        print("="*60)

        if 'parallel' in results:
            r = results['parallel']
            print(f"\n并行分析:")
            print(f"  加速比: {r['speedup']:.2f}x")
            print(f"  效率: {r['efficiency']:.1f}%")

        if 'incremental' in results:
            r = results['incremental']
            print(f"\n增量分析:")
            print(f"  平均耗时: {r.get('avg_time', 0):.3f}s")
            print(f"  最小耗时: {r.get('min_time', 0):.3f}s")
            print(f"  最大耗时: {r.get('max_time', 0):.3f}s")

        if 'hybrid' in results:
            r = results['hybrid']
            print(f"\n混合模式:")
            print(f"  总耗时: {r['duration']:.3f}s")
            print(f"  吞吐量: {r['throughput']:.1f} 文件/秒")
            print(f"  缓存命中: {r['cache_hits']}")

        # 评估是否达到目标
        print("\n目标达成情况:")
        target_speedup = self.config.target_speedup
        actual_speedup = results.get('parallel', {}).get('speedup', 1.0)

        if actual_speedup >= target_speedup:
            print(f"  ✓ 加速比目标: {actual_speedup:.1f}x / {target_speedup}x")
        else:
            print(f"  ✗ 加速比目标: {actual_speedup:.1f}x / {target_speedup}x")
            print(f"    差距: {target_speedup - actual_speedup:.1f}x")

        return results

    def get_performance_stats(self) -> Dict:
        """获取性能统计"""
        total_cache_ops = self.stats['cache_hits_total'] + self.stats['cache_misses_total']
        cache_hit_rate = (
            self.stats['cache_hits_total'] / total_cache_ops * 100
            if total_cache_ops > 0 else 0
        )

        return {
            **self.stats,
            'cache_hit_rate': cache_hit_rate,
            'config': {
                'incremental_enabled': self.config.enable_incremental,
                'parallel_enabled': self.config.enable_parallel,
                'cache_layers': [
                    'L1' if self.config.enable_l1_cache else None,
                    'L2' if self.config.enable_l2_cache else None,
                    'L3' if self.config.enable_l3_cache else None,
                ],
            }
        }

    def _collect_python_files(self) -> List[str]:
        """收集 Python 文件"""
        files = []
        for py_file in self.codebase_path.rglob("*.py"):
            # 排除缓存和虚拟环境
            if '.moss' not in str(py_file) and '__pycache__' not in str(py_file):
                try:
                    rel_path = py_file.relative_to(self.codebase_path)
                    files.append(str(rel_path))
                except ValueError:
                    files.append(str(py_file))
        return files

    async def _run_incremental_only(
        self,
        files: List[Tuple[str, str]],
        analysis_type: str
    ) -> Any:
        """仅使用增量分析（串行）"""
        results = {}
        errors = {}
        start = time.time()

        for file_path, content in files:
            try:
                result = await self.incremental.analyze_with_cache(
                    file_path,
                    content
                )
                results[file_path] = result
            except Exception as e:
                errors[file_path] = str(e)

        from parallel_analyzer import ParallelResult
        return ParallelResult(
            success=len(errors) == 0,
            results=results,
            errors=errors,
            stats={'duration': time.time() - start},
            duration=time.time() - start
        )

    async def _run_serial(
        self,
        files: List[Tuple[str, str]],
        analysis_type: str
    ) -> Any:
        """纯串行模式"""
        results = {}
        errors = {}
        start = time.time()

        for file_path, content in files:
            try:
                tree = ast.parse(content)
                results[file_path] = {
                    'success': True,
                    'functions': len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
                }
            except Exception as e:
                errors[file_path] = str(e)

        from parallel_analyzer import ParallelResult
        return ParallelResult(
            success=len(errors) == 0,
            results=results,
            errors=errors,
            stats={'duration': time.time() - start},
            duration=time.time() - start
        )


# ──────────────────────────────────────────────────────────────
# Demo & Testing
# ──────────────────────────────────────────────────────────────

async def demo():
    """演示性能引擎功能"""
    print("\n" + "="*60)
    print("MOSS v9.3 - Performance Engine Demo")
    print("="*60)

    # 使用 moss 自身代码库作为测试
    codebase_path = Path(__file__).parent.parent.parent

    # 初始化性能引擎
    config = PerformanceConfig(
        enable_incremental=True,
        enable_parallel=True,
        max_workers=4,  # 限制为 4 核以控制资源使用
    )

    engine = PerformanceEngine(codebase_path, config)

    # 运行性能基准测试
    benchmark_results = await engine.run_performance_benchmark()

    # 获取统计
    stats = engine.get_performance_stats()
    print("\n引擎统计:")
    print(f"  分析运行次数: {stats['analyses_run']}")
    print(f"  缓存命中率: {stats['cache_hit_rate']:.1f}%")
    print(f"  总节省时间: {stats['total_time_saved']:.2f}s")

    return benchmark_results


if __name__ == "__main__":
    asyncio.run(demo())
