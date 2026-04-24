#!/usr/bin/env python3
"""
MOSS v9.3 - Incremental Analyzer
增量分析引擎 - 只分析变更的文件，实现10x性能提升

核心组件:
1. ChangeDetector - 文件变更检测 (checksum/git)
2. DependencyInvalidator - 依赖影响传播
3. ResultMerger - 结果合并
4. MultiLevelCache - 多级缓存

Author: MOSS v9.3
Date: 2026-04-23
"""

import asyncio
import hashlib
import json
import os
import sqlite3
import time
from collections import OrderedDict
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx


# ──────────────────────────────────────────────────────────────
# Checksum Calculator
# ──────────────────────────────────────────────────────────────

class ChecksumCalculator:
    """文件校验和计算器"""

    def calculate(self, file_path: Path) -> str:
        """计算文件SHA256校验和"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""

    def calculate_content(self, content: str) -> str:
        """计算内容校验和"""
        return hashlib.sha256(content.encode()).hexdigest()


# ──────────────────────────────────────────────────────────────
# Multi-Level Cache
# ──────────────────────────────────────────────────────────────

class LRUCache:
    """LRU内存缓存 (L1)"""

    def __init__(self, maxsize: int = 1000):
        self.maxsize = maxsize
        self.cache: OrderedDict[str, Any] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            self.cache.move_to_end(key)
            self.hits += 1
            return self.cache[key]
        self.misses += 1
        return None

    def set(self, key: str, value: Any):
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.maxsize:
                self.cache.popitem(last=False)
        self.cache[key] = value

    def get_stats(self) -> Dict:
        total = self.hits + self.misses
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': self.hits / total if total > 0 else 0,
            'size': len(self.cache),
            'maxsize': self.maxsize,
        }


class DiskCache:
    """磁盘缓存 (L2) - SQLite存储"""

    def __init__(self, cache_dir: str = ".moss/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "analysis_cache.db"
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    checksum TEXT,
                    timestamp REAL,
                    ttl INTEGER
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON cache(timestamp)
            """)

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute(
                    "SELECT value, timestamp, ttl FROM cache WHERE key = ?",
                    (key,)
                ).fetchone()

                if row:
                    value, timestamp, ttl = row
                    # 检查TTL
                    if ttl > 0 and time.time() - timestamp > ttl:
                        conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                        return None
                    return json.loads(value)
        except Exception:
            pass
        return None

    def set(self, key: str, value: Any, ttl: int = 86400):
        """设置缓存值"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO cache (key, value, checksum, timestamp, ttl)
                       VALUES (?, ?, ?, ?, ?)""",
                    (key, json.dumps(value), "", time.time(), ttl)
                )
        except Exception:
            pass

    def get_by_checksum(self, checksum: str) -> Optional[Any]:
        """通过校验和获取"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute(
                    "SELECT value FROM cache WHERE checksum = ?",
                    (checksum,)
                ).fetchone()
                if row:
                    return json.loads(row[0])
        except Exception:
            pass
        return None

    def set_checksum(self, file_path: str, checksum: str, value: Any):
        """设置文件校验和关联的缓存"""
        key = f"file:{file_path}"
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO cache (key, value, checksum, timestamp, ttl)
                       VALUES (?, ?, ?, ?, ?)""",
                    (key, json.dumps(value), checksum, time.time(), 86400)
                )
        except Exception:
            pass

    def cleanup(self, max_age: int = 604800):
        """清理过期缓存"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff = time.time() - max_age
                conn.execute("DELETE FROM cache WHERE timestamp < ?", (cutoff,))
        except Exception:
            pass


class ProjectCache:
    """项目级缓存 (L3) - JSON文件"""

    def __init__(self, project_dir: str = "."):
        self.cache_dir = Path(project_dir) / ".moss" / "project_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_file(self, key: str) -> Path:
        """获取缓存文件路径"""
        # 使用哈希避免文件名过长
        key_hash = hashlib.md5(key.encode()).hexdigest()[:16]
        return self.cache_dir / f"{key_hash}.json"

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        cache_file = self._get_cache_file(key)
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                # 检查TTL
                if 'expires' in data and data['expires'] < time.time():
                    cache_file.unlink()
                    return None
                return data.get('value')
            except Exception:
                pass
        return None

    def set(self, key: str, value: Any, ttl: int = 604800):
        """设置缓存"""
        cache_file = self._get_cache_file(key)
        try:
            data = {
                'key': key,
                'value': value,
                'timestamp': time.time(),
                'expires': time.time() + ttl if ttl > 0 else 0,
            }
            with open(cache_file, 'w') as f:
                json.dump(data, f)
        except Exception:
            pass


class MultiLevelCache:
    """
    多级缓存系统

    L1: 内存LRU (最快，进程内)
    L2: 磁盘SQLite (持久，项目级)
    L3: 项目JSON (可共享，版本控制)
    """

    def __init__(self, project_dir: str = "."):
        self.l1 = LRUCache(maxsize=1000)
        self.l2 = DiskCache(f"{project_dir}/.moss/cache")
        self.l3 = ProjectCache(project_dir)
        self.stats = {'promotions': 0, 'evictions': 0}

    def get(self, key: str) -> Optional[Any]:
        """获取缓存，自动提升热点数据"""
        # L1
        value = self.l1.get(key)
        if value is not None:
            return value

        # L2
        value = self.l2.get(key)
        if value is not None:
            # 提升到L1
            self.l1.set(key, value)
            self.stats['promotions'] += 1
            return value

        # L3
        value = self.l3.get(key)
        if value is not None:
            # 提升到L1和L2
            self.l1.set(key, value)
            self.l2.set(key, value)
            self.stats['promotions'] += 1
            return value

        return None

    def set(self, key: str, value: Any, level: int = 2):
        """设置缓存到指定级别及以上"""
        if level <= 1:
            self.l1.set(key, value)
        if level <= 2:
            self.l2.set(key, value)
        if level <= 3:
            self.l3.set(key, value)

    def get_file_analysis(self, file_path: str, checksum: str) -> Optional[Any]:
        """通过文件路径和校验和获取分析结果"""
        # 先通过校验和查找
        key = f"analysis:{file_path}"

        # 检查L2的校验和关联
        result = self.l2.get_by_checksum(checksum)
        if result:
            # 更新L1
            self.l1.set(key, result)
            return result

        # 常规查找
        cached = self.get(key)
        if cached and cached.get('checksum') == checksum:
            return cached.get('result')

        return None

    def set_file_analysis(self, file_path: str, checksum: str, result: Any):
        """缓存文件分析结果"""
        key = f"analysis:{file_path}"
        value = {
            'checksum': checksum,
            'result': result,
            'timestamp': time.time(),
        }
        self.set(key, value, level=2)
        self.l2.set_checksum(file_path, checksum, value)

    def get_stats(self) -> Dict:
        """获取缓存统计"""
        return {
            'l1': self.l1.get_stats(),
            'promotions': self.stats['promotions'],
        }


# ──────────────────────────────────────────────────────────────
# Change Detector
# ──────────────────────────────────────────────────────────────

class ChangeDetector:
    """文件变更检测器"""

    def __init__(self, cache: MultiLevelCache):
        self.cache = cache
        self.checksum = ChecksumCalculator()

    def detect_changes(self, files: List[Path]) -> Tuple[List[Path], List[Path]]:
        """
        检测变更的文件

        Returns:
            (changed_files, unchanged_files)
        """
        changed = []
        unchanged = []

        for file in files:
            current_hash = self.checksum.calculate(file)
            cached = self.cache.l2.get(f"checksum:{file}")

            if cached and cached.get('hash') == current_hash:
                unchanged.append(file)
            else:
                changed.append(file)
                # 更新校验和缓存
                self.cache.l2.set(f"checksum:{file}", {'hash': current_hash})

        return changed, unchanged

    def get_file_checksum(self, file: Path) -> str:
        """获取文件校验和"""
        return self.checksum.calculate(file)


# ──────────────────────────────────────────────────────────────
# Dependency Invalidator
# ──────────────────────────────────────────────────────────────

class DependencyInvalidator:
    """依赖影响传播计算器"""

    def __init__(self, dependency_graph: nx.DiGraph):
        self.graph = dependency_graph

    def calculate_impact_set(self, changed_files: List[Path]) -> Set[Path]:
        """
        计算变更的影响范围

        包括:
        1. 直接变更的文件
        2. 依赖这些文件的模块
        3. 这些模块导出的符号被使用的文件
        """
        impact_set = set()

        for file in changed_files:
            impact_set.add(file)

            # 找到文件对应的模块名
            module = self._file_to_module(file)
            if module and module in self.graph:
                # 添加所有依赖此模块的模块
                dependents = nx.descendants(self.graph, module)
                for dep in dependents:
                    dep_file = self._module_to_file(dep)
                    if dep_file:
                        impact_set.add(dep_file)

        return impact_set

    def _file_to_module(self, file: Path) -> Optional[str]:
        """文件路径转模块名"""
        # 简化实现，实际需要根据项目结构
        try:
            parts = list(file.with_suffix('').parts)
            if parts[-1] == '__init__':
                parts = parts[:-1]
            return '.'.join(parts)
        except Exception:
            return None

    def _module_to_file(self, module: str) -> Optional[Path]:
        """模块名转文件路径"""
        # 简化实现
        parts = module.split('.')
        return Path(*parts).with_suffix('.py')


# ──────────────────────────────────────────────────────────────
# Incremental Analyzer
# ──────────────────────────────────────────────────────────────

class IncrementalAnalyzer:
    """
    增量分析引擎

    核心流程:
    1. 检测变更文件
    2. 计算影响范围
    3. 加载未变更文件的缓存结果
    4. 分析变更+影响文件
    5. 合并结果
    6. 更新缓存
    """

    def __init__(self, project_dir: str = "."):
        self.cache = MultiLevelCache(project_dir)
        self.change_detector = ChangeDetector(self.cache)
        self.checksum = ChecksumCalculator()
        self.dependency_graph: Optional[nx.DiGraph] = None

    def set_dependency_graph(self, graph: nx.DiGraph):
        """设置依赖图"""
        self.dependency_graph = graph
        self.invalidator = DependencyInvalidator(graph)

    async def analyze(
        self,
        files: List[Path],
        analyzer_func,
        use_cache: bool = True
    ) -> Tuple[List[Any], Dict]:
        """
        增量分析

        Args:
            files: 要分析的文件列表
            analyzer_func: 分析函数 (file) -> result
            use_cache: 是否使用缓存

        Returns:
            (results, stats)
        """
        start_time = time.time()
        stats = {
            'total_files': len(files),
            'changed_files': 0,
            'unchanged_files': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'analysis_time': 0,
        }

        if not use_cache:
            # 全量分析
            results = await self._analyze_all(files, analyzer_func)
            stats['cache_misses'] = len(files)
            return results, stats

        # 1. 检测变更
        changed, unchanged = self.change_detector.detect_changes(files)
        stats['changed_files'] = len(changed)
        stats['unchanged_files'] = len(unchanged)

        # 2. 计算影响范围
        if self.dependency_graph:
            impact_set = self.invalidator.calculate_impact_set(changed)
            # 过滤到实际存在的文件
            to_analyze = [f for f in impact_set if f in files]
        else:
            to_analyze = changed

        # 3. 收集结果
        results = []

        # 3a. 未变更文件 - 从缓存加载
        for file in unchanged:
            if file not in to_analyze:
                checksum = self.checksum.calculate(file)
                cached = self.cache.get_file_analysis(str(file), checksum)
                if cached:
                    results.append(cached)
                    stats['cache_hits'] += 1
                else:
                    # 缓存未命中，需要分析
                    to_analyze.append(file)
                    stats['cache_misses'] += 1

        # 3b. 变更/影响文件 - 重新分析
        analysis_start = time.time()
        for file in to_analyze:
            result = await analyzer_func(file)
            results.append(result)
            stats['cache_misses'] += 1

            # 更新缓存
            checksum = self.checksum.calculate(file)
            self.cache.set_file_analysis(str(file), checksum, result)

        stats['analysis_time'] = time.time() - analysis_start
        stats['total_time'] = time.time() - start_time

        return results, stats

    async def _analyze_all(self, files: List[Path], analyzer_func) -> List[Any]:
        """全量分析"""
        results = []
        for file in files:
            result = await analyzer_func(file)
            results.append(result)
        return results

    def get_cache_stats(self) -> Dict:
        """获取缓存统计"""
        return self.cache.get_stats()


# ──────────────────────────────────────────────────────────────
# Parallel Analyzer
# ──────────────────────────────────────────────────────────────

class ParallelAnalyzer:
    """并行分析器"""

    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or max(4, os.cpu_count() or 4)

    async def analyze_batch(
        self,
        files: List[Path],
        analyzer_func,
        batch_size: int = None
    ) -> List[Any]:
        """并行分析一批文件"""
        batch_size = batch_size or max(1, len(files) // self.max_workers)

        # 分批
        batches = [
            files[i:i+batch_size]
            for i in range(0, len(files), batch_size)
        ]

        # 并行处理
        tasks = [
            self._analyze_batch(batch, analyzer_func)
            for batch in batches
        ]

        results = await asyncio.gather(*tasks)
        return [r for batch in results for r in batch]

    async def _analyze_batch(self, files: List[Path], analyzer_func) -> List[Any]:
        """分析一批文件"""
        results = []
        for file in files:
            result = await analyzer_func(file)
            results.append(result)
        return results


# ──────────────────────────────────────────────────────────────
# Performance Benchmark
# ──────────────────────────────────────────────────────────────

class PerformanceBenchmark:
    """性能基准测试"""

    def __init__(self):
        self.results = []

    async def benchmark(
        self,
        files: List[Path],
        analyzer_func,
        iterations: int = 3
    ) -> Dict:
        """运行性能基准测试"""
        print(f"\n[Benchmark] 测试 {len(files)} 个文件")

        # 全量分析基准
        full_times = []
        for i in range(iterations):
            start = time.time()
            await self._analyze_all(files, analyzer_func)
            elapsed = time.time() - start
            full_times.append(elapsed)
            print(f"  全量分析 #{i+1}: {elapsed:.2f}s")

        # 增量分析基准 (首次，无缓存)
        incremental = IncrementalAnalyzer()
        cold_times = []
        for i in range(iterations):
            start = time.time()
            await incremental.analyze(files, analyzer_func, use_cache=True)
            elapsed = time.time() - start
            cold_times.append(elapsed)
            print(f"  增量分析(冷) #{i+1}: {elapsed:.2f}s")

        # 增量分析基准 (热缓存)
        hot_times = []
        for i in range(iterations):
            start = time.time()
            _, stats = await incremental.analyze(files, analyzer_func, use_cache=True)
            elapsed = time.time() - start
            hot_times.append(elapsed)
            print(f"  增量分析(热) #{i+1}: {elapsed:.2f}s (命中: {stats['cache_hits']})")

        return {
            'full_analysis': {
                'avg': sum(full_times) / len(full_times),
                'min': min(full_times),
                'max': max(full_times),
            },
            'incremental_cold': {
                'avg': sum(cold_times) / len(cold_times),
            },
            'incremental_hot': {
                'avg': sum(hot_times) / len(hot_times),
            },
            'speedup_cold': full_times[0] / cold_times[0] if cold_times[0] > 0 else 0,
            'speedup_hot': full_times[0] / hot_times[0] if hot_times[0] > 0 else 0,
        }

    async def _analyze_all(self, files: List[Path], analyzer_func):
        """全量分析"""
        for file in files:
            await analyzer_func(file)


# ──────────────────────────────────────────────────────────────
# Test
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    async def test():
        print("=" * 70)
        print("MOSS v9.3 - Incremental Analyzer 测试")
        print("=" * 70)

        # 1. 测试缓存
        print("\n[1] 测试多级缓存...")
        cache = MultiLevelCache("/tmp/moss_test_cache")

        # 设置缓存
        cache.set("test_key", {"data": "test_value"})

        # 获取缓存
        value = cache.get("test_key")
        print(f"   L1缓存: {value is not None}")

        # 获取统计
        stats = cache.get_stats()
        print(f"   缓存统计: {stats}")

        # 2. 测试文件分析缓存
        print("\n[2] 测试文件分析缓存...")
        test_file = Path("/workspace/moss/moss/core/agent_registry.py")
        if test_file.exists():
            checksum = ChecksumCalculator().calculate(test_file)
            result = {"issues": 5, "complexity": 10}

            cache.set_file_analysis(str(test_file), checksum, result)
            cached = cache.get_file_analysis(str(test_file), checksum)
            print(f"   原始结果: {result}")
            print(f"   缓存结果: {cached}")
            print(f"   缓存命中: {cached == result}")

        # 3. 测试增量分析
        print("\n[3] 测试增量分析...")

        # 模拟分析函数
        async def mock_analyzer(file: Path) -> Dict:
            await asyncio.sleep(0.01)  # 模拟分析时间
            return {"file": str(file), "issues": []}

        # 准备测试文件
        test_files = list(Path("/workspace/moss/moss/core").glob("*.py"))[:20]

        incremental = IncrementalAnalyzer("/tmp/moss_test")

        # 首次分析 (冷缓存)
        start = time.time()
        results, stats = await incremental.analyze(test_files, mock_analyzer)
        cold_time = time.time() - start
        print(f"   冷缓存分析: {cold_time:.2f}s")
        print(f"   统计: {stats}")

        # 二次分析 (热缓存)
        start = time.time()
        results, stats = await incremental.analyze(test_files, mock_analyzer)
        hot_time = time.time() - start
        print(f"   热缓存分析: {hot_time:.2f}s")
        print(f"   统计: {stats}")

        if hot_time > 0:
            print(f"   加速比: {cold_time/hot_time:.1f}x")

        print("\n测试完成!")

    asyncio.run(test())
