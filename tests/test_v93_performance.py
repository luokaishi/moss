#!/usr/bin/env python3
"""
MOSS v9.3 - Performance Tests
性能测试套件
"""

import asyncio
import tempfile
from pathlib import Path

import pytest

from moss.core import (
    IncrementalAnalyzer,
    ParallelAnalyzer,
    PerformanceEngine,
    PerformanceConfig,
)


class TestIncrementalAnalyzer:
    """测试增量分析器"""

    @pytest.fixture
    def temp_project(self):
        """创建临时项目"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            # 创建测试文件
            (project / "test.py").write_text("""
def long_function(x, y, z):
    result = 0
    for i in range(x):
        result += i * y
    return result
""")
            yield project

    def test_incremental_analyzer_init(self, temp_project):
        """测试初始化"""
        analyzer = IncrementalAnalyzer(str(temp_project))
        assert analyzer is not None

    def test_change_detection(self, temp_project):
        """测试变更检测"""
        analyzer = IncrementalAnalyzer(str(temp_project))
        # 首次分析
        files = list(temp_project.glob("*.py"))
        changed, unchanged = analyzer.change_detector.detect_changes(files)
        assert len(changed) > 0  # 首次所有文件都是变更的


class TestParallelAnalyzer:
    """测试并行分析器"""

    @pytest.fixture
    def test_files(self):
        """创建测试文件列表"""
        files = []
        for i in range(5):
            content = f"""
def function_{i}(x):
    return x * {i}
"""
            files.append((f"test_{i}.py", content))
        return files

    @pytest.mark.asyncio
    async def test_parallel_analysis(self, test_files):
        """测试并行分析"""
        analyzer = ParallelAnalyzer(max_workers=2)
        result = await analyzer.analyze_files_parallel(test_files, 'parse')

        assert result.success
        assert len(result.results) == 5
        assert result.stats['total_files'] == 5

    def test_optimal_workers(self):
        """测试最优工作进程数计算"""
        analyzer = ParallelAnalyzer(max_workers=8)

        assert analyzer.get_optimal_workers(5) <= 2
        assert analyzer.get_optimal_workers(20) <= 4
        assert analyzer.get_optimal_workers(100) >= 4


class TestPerformanceEngine:
    """测试性能引擎"""

    @pytest.fixture
    def temp_project(self):
        """创建临时项目"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            # 创建多个测试文件
            for i in range(3):
                (project / f"test_{i}.py").write_text(f"""
def function_{i}():
    pass

class Class_{i}:
    def method(self):
        pass
""")
            yield project

    @pytest.mark.asyncio
    async def test_analyze_codebase(self, temp_project):
        """测试代码库分析"""
        config = PerformanceConfig(
            enable_incremental=True,
            enable_parallel=True,
            max_workers=2,
        )
        engine = PerformanceEngine(temp_project, config)

        report = await engine.analyze_codebase()

        assert report.file_count == 3
        assert report.duration >= 0

    def test_get_performance_stats(self, temp_project):
        """测试获取性能统计"""
        config = PerformanceConfig()
        engine = PerformanceEngine(temp_project, config)

        stats = engine.get_performance_stats()

        assert 'analyses_run' in stats
        assert 'config' in stats


class TestMultiLevelCache:
    """测试多级缓存"""

    @pytest.fixture
    def temp_cache(self):
        """创建临时缓存目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_cache_operations(self, temp_cache):
        """测试缓存操作"""
        from moss.core import MultiLevelCache

        cache = MultiLevelCache(temp_cache)

        # 设置缓存
        cache.set("test_key", {"data": "test_value"})

        # 获取缓存
        value = cache.get("test_key")
        assert value == {"data": "test_value"}

        # 获取统计
        stats = cache.get_stats()
        assert 'l1' in stats
        assert 'size' in stats['l1']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
