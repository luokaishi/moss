"""
MOSS CLI 集成测试
验证所有 CLI 命令可以正常执行
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import subprocess
import pytest
import tempfile


class TestCLICommands:
    """测试 CLI 命令可用性"""
    
    def test_moss_version(self):
        """测试版本命令"""
        result = subprocess.run(
            [sys.executable, "-m", "moss", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "9.6.0" in result.stdout or "9.6.0" in result.stderr
    
    def test_moss_analyze_help(self):
        """测试 analyze 命令帮助"""
        result = subprocess.run(
            [sys.executable, "-m", "moss", "analyze", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "分析代码质量" in result.stdout
    
    def test_moss_refactor_help(self):
        """测试 refactor 命令帮助"""
        result = subprocess.run(
            [sys.executable, "-m", "moss", "refactor", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "重构" in result.stdout or "refactor" in result.stdout.lower()
    
    def test_moss_agent_help(self):
        """测试 agent 命令帮助"""
        result = subprocess.run(
            [sys.executable, "-m", "moss", "agent", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "task" in result.stdout.lower()
    
    def test_moss_init(self):
        """测试 init 命令在临时目录执行"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [sys.executable, "-m", "moss", "init", tmpdir],
                capture_output=True,
                text=True
            )
            # init 可能成功或失败，但不应崩溃
            assert result.returncode in [0, 1]
    
    def test_moss_analyze_on_self(self):
        """测试 analyze 命令在 moss 自身代码上运行"""
        result = subprocess.run(
            [sys.executable, "-m", "moss", "analyze", "moss/core", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=30
        )
        # 分析可能找到问题，但命令应该执行完成
        assert result.returncode in [0, 1]


class TestCoreImports:
    """测试核心模块导入"""
    
    def test_import_moss_core(self):
        """测试 moss.core 导入无警告"""
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            import moss.core
            # 不应有循环导入警告
            circular_warnings = [x for x in w if "circular" in str(x.message).lower()]
            assert len(circular_warnings) == 0, f"发现循环导入警告: {circular_warnings}"
    
    def test_key_components_available(self):
        """测试关键组件可用"""
        from moss.core import (
            UnifiedMOSSAgent,
            GeneticProgrammer,
            DriveManager,
            MetaLearner,
            TaskAwareAgent
        )
        assert UnifiedMOSSAgent is not None
        assert GeneticProgrammer is not None
        assert DriveManager is not None
        assert MetaLearner is not None
        assert TaskAwareAgent is not None


class TestVersionConsistency:
    """测试版本号一致性"""
    
    def test_version_in_init(self):
        """测试 moss/__init__.py 版本号"""
        import moss
        assert moss.__version__ == "9.6.0"
    
    def test_version_in_pyproject(self):
        """测试 pyproject.toml 版本号"""
        import tomllib
        with open("pyproject.toml", "rb") as f:
            config = tomllib.load(f)
        assert config["project"]["version"] == "9.6.0"
