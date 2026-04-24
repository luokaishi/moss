#!/usr/bin/env python3
"""
MOSS v9.3.0 - Installation Test Script
验证安装和核心功能
"""

import sys
from pathlib import Path

def test_imports():
    """测试所有核心导入"""
    print("Testing imports...")

    # v9.3 Performance
    from moss.core import IncrementalAnalyzer, ParallelAnalyzer, PerformanceEngine
    from moss.core import MultiLevelCache, PerformanceConfig

    # v9.3 LSP
    from moss.core import MossAnalysisProvider, LSPProtocolHandler

    # v9.3 ML
    from moss.core import RefactoringRecommender, CodeFeatures, PatternLearningEngine

    # v9.3 Team
    from moss.core import TeamManager, TeamConfig, QualityDashboard

    print("  ✓ All v9.3 components imported successfully")

def test_cli():
    """测试 CLI"""
    print("Testing CLI...")
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "moss.cli", "--version"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    assert "9.3.0" in result.stdout, f"Version not found: {result.stdout}"
    print(f"  ✓ CLI version: {result.stdout.strip()}")

def test_performance_engine():
    """测试性能引擎"""
    print("Testing PerformanceEngine...")
    from moss.core import PerformanceEngine, PerformanceConfig

    config = PerformanceConfig(
        enable_l1_cache=True,
        enable_l2_cache=True,
        max_workers=4
    )
    assert config.enable_l1_cache
    assert config.max_workers == 4
    print("  ✓ PerformanceConfig works")

def test_ml_recommender():
    """测试 ML 推荐器"""
    print("Testing ML Recommender...")
    from moss.core import RefactoringRecommender, CodeFeatures

    # Test CodeFeatures creation
    features = CodeFeatures(
        lines_of_code=100,
        num_functions=5,
        num_classes=2,
        num_imports=10,
        cyclomatic_complexity=5,
        cognitive_complexity=8,
        max_function_length=20,
        avg_function_length=15.5,
        nesting_depth=2,
        num_branches=8,
        num_loops=3,
        num_returns=4,
        has_docstring=True,
        num_comments=15,
        identifier_density=0.7,
        duplicate_code_score=0.1,
        coupling_score=0.3
    )

    vector = features.to_vector()
    assert len(vector) == 17, f"Expected 17 features, got {len(vector)}"
    print(f"  ✓ CodeFeatures vector: {len(vector)} dimensions")

def test_pattern_learning():
    """测试模式学习"""
    print("Testing PatternLearningEngine...")
    from moss.core import PatternLearningEngine

    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = PatternLearningEngine(tmpdir)
        assert engine.project_path == Path(tmpdir)
        print("  ✓ PatternLearningEngine initialized")

def main():
    print("=" * 60)
    print("MOSS v9.3.0 Installation Test")
    print("=" * 60)

    tests = [
        test_imports,
        test_cli,
        test_performance_engine,
        test_ml_recommender,
        test_pattern_learning,
    ]

    failed = []
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"  ✗ {test.__name__} failed: {e}")
            failed.append((test.__name__, e))

    print("\n" + "=" * 60)
    if not failed:
        print("✓ All tests passed! MOSS v9.3.0 is ready.")
        return 0
    else:
        print(f"✗ {len(failed)} test(s) failed:")
        for name, error in failed:
            print(f"  - {name}: {error}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
