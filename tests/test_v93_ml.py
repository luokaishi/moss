#!/usr/bin/env python3
"""
MOSS v9.3 - ML Features Tests
ML 特性测试套件
"""

import tempfile
from pathlib import Path

import pytest

from moss.core import (
    RefactoringRecommender,
    PatternLearningEngine,
    CodeFeatures,
)


class TestRefactoringRecommender:
    """测试重构推荐器"""

    @pytest.fixture
    def temp_project(self):
        """创建临时项目"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def sample_code(self):
        """示例代码"""
        return """
def very_long_function(x, y, z, a, b, c):
    result = 0
    for i in range(x):
        if i % 2 == 0:
            result += i * y
        else:
            result -= i * z
    for j in range(y):
        for k in range(z):
            if j > k:
                result += j * k
            elif j < k:
                result -= j * k
    return result

import os
import sys
"""

    def test_recommender_init(self, temp_project):
        """测试初始化"""
        recommender = RefactoringRecommender(temp_project)
        assert recommender is not None

    def test_recommendations(self, temp_project, sample_code):
        """测试生成推荐"""
        recommender = RefactoringRecommender(temp_project)

        recommendations = recommender.recommend("test.py", sample_code)

        assert isinstance(recommendations, list)
        # 应该检测到长函数和未使用的导入
        assert len(recommendations) > 0

    def test_feature_extraction(self, sample_code):
        """测试特征提取"""
        from moss.core.ml_recommender import CodeFeatureExtractor

        extractor = CodeFeatureExtractor()
        features = extractor.extract("test.py", sample_code)

        assert isinstance(features, CodeFeatures)
        assert features.lines_of_code > 0
        assert features.num_functions >= 1


class TestPatternLearningEngine:
    """测试模式学习引擎"""

    @pytest.fixture
    def temp_project(self):
        """创建临时项目"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            # 创建测试文件
            (project / "test.py").write_text("""
class Singleton:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

def create_object():
    return Singleton()

@decorator
def helper():
    pass
""")
            yield project

    def test_engine_init(self, temp_project):
        """测试初始化"""
        engine = PatternLearningEngine(str(temp_project))
        assert engine is not None

    def test_pattern_learning(self, temp_project):
        """测试模式学习"""
        engine = PatternLearningEngine(str(temp_project))

        profile = engine.learn(max_files=10)

        assert profile is not None
        assert profile.total_files >= 1

    def test_detect_patterns(self, temp_project):
        """测试模式检测"""
        engine = PatternLearningEngine(str(temp_project))
        profile = engine.learn(max_files=10)

        # 应该检测到单例模式
        patterns = profile.detected_patterns
        assert len(patterns) > 0

    def test_generate_report(self, temp_project):
        """测试生成报告"""
        engine = PatternLearningEngine(str(temp_project))
        engine.learn(max_files=10)

        report = engine.generate_report()

        assert isinstance(report, str)
        assert "MOSS" in report

    def test_get_suggestions(self, temp_project):
        """测试获取建议"""
        engine = PatternLearningEngine(str(temp_project))
        engine.learn(max_files=10)

        suggestions = engine.get_suggestions()

        assert isinstance(suggestions, list)


class TestCodeFeatures:
    """测试代码特征"""

    def test_to_vector(self):
        """测试特征向量化"""
        features = CodeFeatures(
            lines_of_code=100,
            num_functions=5,
            num_classes=2,
            num_imports=3,
            cyclomatic_complexity=10,
            cognitive_complexity=8,
            max_function_length=50,
            avg_function_length=30.0,
            nesting_depth=3,
            num_branches=5,
            num_loops=2,
            num_returns=3,
            has_docstring=True,
            num_comments=10,
            identifier_density=0.5,
            duplicate_code_score=0.1,
            coupling_score=0.2,
        )

        vector = features.to_vector()

        assert len(vector) == 17
        assert vector[0] == 100  # lines_of_code
        assert vector[12] == 1.0  # has_docstring


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
