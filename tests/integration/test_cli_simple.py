#!/usr/bin/env python3
"""
MOSS CLI 简单集成测试 - 直接运行，不依赖 pytest
"""

import subprocess
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def test_version():
    """测试版本命令"""
    result = subprocess.run(
        [sys.executable, "-m", "moss", "--version"],
        capture_output=True,
        text=True
    )
    output = result.stdout + result.stderr
    assert "9.6.0" in output, f"Expected 9.6.0 in output, got: {output}"
    print("✓ test_version passed")


def test_analyze_help():
    """测试 analyze 命令帮助"""
    result = subprocess.run(
        [sys.executable, "-m", "moss", "analyze", "--help"],
        capture_output=True,
        text=True
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, f"Command failed: {output}"
    assert "分析" in output or "analyze" in output.lower(), f"Unexpected output: {output}"
    print("✓ test_analyze_help passed")


def test_import_no_circular_warning():
    """测试导入 moss.core 没有循环导入警告"""
    result = subprocess.run(
        [sys.executable, "-c", "import moss.core; print('OK')"],
        capture_output=True,
        text=True
    )
    output = result.stdout + result.stderr
    assert "OK" in output, f"Import failed: {output}"
    assert "circular" not in output.lower(), f"Circular import warning found: {output}"
    print("✓ test_import_no_circular_warning passed")


def test_key_components():
    """测试关键组件可用"""
    code = """
from moss.core import UnifiedMOSSAgent, GeneticProgrammer, DriveManager, MetaLearner
print("All components available")
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True
    )
    output = result.stdout + result.stderr
    assert "All components available" in output, f"Components import failed: {output}"
    print("✓ test_key_components passed")


def test_version_consistency():
    """测试版本号一致性"""
    code = """
import moss
assert moss.__version__ == "9.6.0", f"Version mismatch: {moss.__version__}"
print("Version OK")
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True
    )
    output = result.stdout + result.stderr
    assert "Version OK" in output, f"Version check failed: {output}"
    print("✓ test_version_consistency passed")


def test_analyze_command():
    """测试 analyze 命令实际执行"""
    result = subprocess.run(
        [sys.executable, "-m", "moss", "analyze", "moss/core", "--format", "json"],
        capture_output=True,
        text=True,
        timeout=30
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, f"Analyze command failed: {output}"
    assert "Python 文件" in output or "files" in output.lower(), f"Unexpected output: {output}"
    print("✓ test_analyze_command passed")


def test_agent_list():
    """测试 agent --list 命令"""
    result = subprocess.run(
        [sys.executable, "-m", "moss", "agent", "--list"],
        capture_output=True,
        text=True
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, f"Agent list failed: {output}"
    assert "file_organization" in output, f"Missing expected task: {output}"
    assert "code_review" in output, f"Missing expected task: {output}"
    print("✓ test_agent_list passed")


def test_refactor_help():
    """测试 refactor 命令帮助"""
    result = subprocess.run(
        [sys.executable, "-m", "moss", "refactor", "--help"],
        capture_output=True,
        text=True
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, f"Refactor help failed: {output}"
    assert "move" in output and "extract" in output and "imports" in output, f"Missing subcommands: {output}"
    print("✓ test_refactor_help passed")


def test_cache_status():
    """测试 cache status 命令"""
    result = subprocess.run(
        [sys.executable, "-m", "moss", "cache", "status"],
        capture_output=True,
        text=True
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, f"Cache status failed: {output}"
    assert "缓存" in output or "cache" in output.lower(), f"Unexpected output: {output}"
    print("✓ test_cache_status passed")


def test_validate_help():
    """测试 validate 命令帮助"""
    result = subprocess.run(
        [sys.executable, "-m", "moss", "validate", "--help"],
        capture_output=True,
        text=True
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, f"Validate help failed: {output}"
    assert "experiment" in output.lower(), f"Missing experiment option: {output}"
    print("✓ test_validate_help passed")


if __name__ == "__main__":
    print("Running MOSS Integration Tests...")
    print("=" * 50)
    
    tests = [
        test_version,
        test_analyze_help,
        test_import_no_circular_warning,
        test_key_components,
        test_version_consistency,
        test_analyze_command,
        test_agent_list,
        test_refactor_help,
        test_cache_status,
        test_validate_help,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1
    
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    
    sys.exit(0 if failed == 0 else 1)
