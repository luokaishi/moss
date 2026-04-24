#!/usr/bin/env python3
"""
MOSS v9.3 - ML Refactoring Recommender
ML 重构推荐引擎

基于历史重构数据和代码特征，智能推荐重构操作。

核心功能:
1. 重构历史分析
2. 代码特征提取
3. 重构推荐模型
4. 推荐排序和过滤
5. 效果预测

Author: MOSS v9.3
Date: 2026-04-24
"""

import ast
import json
import hashlib
import pickle
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import time

import numpy as np


# ──────────────────────────────────────────────────────────────
# Data Structures
# ──────────────────────────────────────────────────────────────

@dataclass
class RefactoringAction:
    """重构操作记录"""
    action_id: str
    action_type: str  # 'extract_function', 'rename', 'move', etc.
    target_file: str
    target_symbol: str
    line_start: int
    line_end: int
    before_code: str
    after_code: str
    timestamp: float
    user_accepted: bool = True
    metrics_before: Dict = field(default_factory=dict)
    metrics_after: Dict = field(default_factory=dict)
    context: Dict = field(default_factory=dict)


@dataclass
class CodeFeatures:
    """代码特征向量"""
    # 基础统计
    lines_of_code: int
    num_functions: int
    num_classes: int
    num_imports: int

    # 复杂度
    cyclomatic_complexity: int
    cognitive_complexity: int
    max_function_length: int
    avg_function_length: float

    # 结构
    nesting_depth: int
    num_branches: int
    num_loops: int
    num_returns: int

    # 语义
    has_docstring: bool
    num_comments: int
    identifier_density: float

    # 质量
    duplicate_code_score: float
    coupling_score: float

    def to_vector(self) -> np.ndarray:
        """转换为数值向量"""
        return np.array([
            self.lines_of_code,
            self.num_functions,
            self.num_classes,
            self.num_imports,
            self.cyclomatic_complexity,
            self.cognitive_complexity,
            self.max_function_length,
            self.avg_function_length,
            self.nesting_depth,
            self.num_branches,
            self.num_loops,
            self.num_returns,
            1.0 if self.has_docstring else 0.0,
            self.num_comments,
            self.identifier_density,
            self.duplicate_code_score,
            self.coupling_score,
        ])


@dataclass
class RefactoringRecommendation:
    """重构推荐"""
    recommendation_id: str
    action_type: str
    target_file: str
    target_symbol: str
    line_start: int
    line_end: int
    confidence: float  # 0.0 - 1.0
    priority: int  # 1-5
    reason: str
    expected_impact: Dict = field(default_factory=dict)
    suggested_changes: Optional[str] = None


# ──────────────────────────────────────────────────────────────
# Feature Extractor
# ──────────────────────────────────────────────────────────────

class CodeFeatureExtractor:
    """代码特征提取器"""

    def __init__(self):
        self.cache: Dict[str, CodeFeatures] = {}

    def extract(self, file_path: str, content: str) -> CodeFeatures:
        """从代码中提取特征"""
        cache_key = hashlib.sha256(content.encode()).hexdigest()
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return self._empty_features()

        features = CodeFeatures(
            lines_of_code=len(content.split('\n')),
            num_functions=0,
            num_classes=0,
            num_imports=0,
            cyclomatic_complexity=0,
            cognitive_complexity=0,
            max_function_length=0,
            avg_function_length=0.0,
            nesting_depth=0,
            num_branches=0,
            num_loops=0,
            num_returns=0,
            has_docstring=False,
            num_comments=content.count('#'),
            identifier_density=0.0,
            duplicate_code_score=0.0,
            coupling_score=0.0,
        )

        function_lengths = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                features.num_functions += 1
                length = (node.end_lineno or node.lineno) - node.lineno
                function_lengths.append(length)
                features.max_function_length = max(features.max_function_length, length)

                # 复杂度
                func_complexity = 1
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                        func_complexity += 1
                        features.num_branches += 1
                    elif isinstance(child, ast.BoolOp):
                        func_complexity += len(child.values) - 1
                    elif isinstance(child, (ast.For, ast.While, ast.AsyncFor)):
                        features.num_loops += 1
                    elif isinstance(child, ast.Return):
                        features.num_returns += 1

                features.cyclomatic_complexity += func_complexity

                # 文档字符串
                if ast.get_docstring(node):
                    features.has_docstring = True

            elif isinstance(node, ast.ClassDef):
                features.num_classes += 1

            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                features.num_imports += 1

        if function_lengths:
            features.avg_function_length = sum(function_lengths) / len(function_lengths)

        # 计算嵌套深度
        features.nesting_depth = self._calculate_nesting_depth(tree)

        # 标识符密度
        identifiers = [node.id for node in ast.walk(tree) if isinstance(node, ast.Name)]
        if identifiers:
            features.identifier_density = len(set(identifiers)) / len(identifiers)

        self.cache[cache_key] = features
        return features

    def _calculate_nesting_depth(self, tree: ast.AST) -> int:
        """计算最大嵌套深度"""
        max_depth = 0

        def visit(node, depth=0):
            nonlocal max_depth
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.If, ast.For, ast.While)):
                depth += 1
                max_depth = max(max_depth, depth)
            for child in ast.iter_child_nodes(node):
                visit(child, depth)

        visit(tree)
        return max_depth

    def _empty_features(self) -> CodeFeatures:
        """返回空特征"""
        return CodeFeatures(
            lines_of_code=0, num_functions=0, num_classes=0, num_imports=0,
            cyclomatic_complexity=0, cognitive_complexity=0,
            max_function_length=0, avg_function_length=0.0,
            nesting_depth=0, num_branches=0, num_loops=0, num_returns=0,
            has_docstring=False, num_comments=0, identifier_density=0.0,
            duplicate_code_score=0.0, coupling_score=0.0,
        )


# ──────────────────────────────────────────────────────────────
# Historical Data Manager
# ──────────────────────────────────────────────────────────────

class RefactoringHistoryManager:
    """重构历史管理器"""

    def __init__(self, storage_path: str = ".moss/refactoring_history"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.actions: List[RefactoringAction] = []
        self._load_history()

    def record_action(self, action: RefactoringAction):
        """记录重构操作"""
        self.actions.append(action)
        self._save_history()

    def get_actions_by_type(self, action_type: str) -> List[RefactoringAction]:
        """获取特定类型的重构操作"""
        return [a for a in self.actions if a.action_type == action_type]

    def get_actions_for_file(self, file_path: str) -> List[RefactoringAction]:
        """获取特定文件的重构操作"""
        return [a for a in self.actions if a.target_file == file_path]

    def get_success_rate(self, action_type: Optional[str] = None) -> float:
        """计算成功率"""
        actions = self.actions if action_type is None else self.get_actions_by_type(action_type)
        if not actions:
            return 0.0
        accepted = sum(1 for a in actions if a.user_accepted)
        return accepted / len(actions)

    def get_common_patterns(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """获取最常见的重构模式"""
        pattern_counts = defaultdict(int)
        for action in self.actions:
            key = f"{action.action_type}:{action.target_symbol}"
            pattern_counts[key] += 1
        return sorted(pattern_counts.items(), key=lambda x: -x[1])[:top_n]

    def _load_history(self):
        """加载历史数据"""
        history_file = self.storage_path / "actions.json"
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    self.actions = [RefactoringAction(**item) for item in data]
            except Exception:
                pass

    def _save_history(self):
        """保存历史数据"""
        history_file = self.storage_path / "actions.json"
        try:
            with open(history_file, 'w') as f:
                json.dump([self._action_to_dict(a) for a in self.actions], f, indent=2)
        except Exception:
            pass

    def _action_to_dict(self, action: RefactoringAction) -> Dict:
        """转换操作记录为字典"""
        return {
            'action_id': action.action_id,
            'action_type': action.action_type,
            'target_file': action.target_file,
            'target_symbol': action.target_symbol,
            'line_start': action.line_start,
            'line_end': action.line_end,
            'timestamp': action.timestamp,
            'user_accepted': action.user_accepted,
            'metrics_before': action.metrics_before,
            'metrics_after': action.metrics_after,
        }


# ──────────────────────────────────────────────────────────────
# ML Recommender
# ──────────────────────────────────────────────────────────────

class RefactoringRecommender:
    """
    重构推荐引擎

    基于历史数据和代码特征，推荐最优的重构操作。
    """

    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.feature_extractor = CodeFeatureExtractor()
        self.history_manager = RefactoringHistoryManager(
            str(self.project_path / ".moss" / "refactoring_history")
        )

        # 重构规则库
        self.refactoring_rules = self._init_rules()

        # 模型权重（简化版，实际可用机器学习模型）
        self.weights = self._load_weights()

    def _init_rules(self) -> Dict[str, Dict]:
        """初始化重构规则"""
        return {
            'extract_function': {
                'description': '提取过长函数',
                'conditions': {
                    'max_function_length': 50,
                    'cyclomatic_complexity': 10,
                },
                'priority': 1,
            },
            'extract_variable': {
                'description': '提取复杂表达式',
                'conditions': {
                    'identifier_density': 0.3,
                },
                'priority': 3,
            },
            'rename_symbol': {
                'description': '重命名符号',
                'conditions': {},
                'priority': 4,
            },
            'organize_imports': {
                'description': '整理导入',
                'conditions': {
                    'num_imports': 5,
                },
                'priority': 5,
            },
            'remove_unused': {
                'description': '移除未使用代码',
                'conditions': {},
                'priority': 2,
            },
        }

    def _load_weights(self) -> Dict[str, float]:
        """加载模型权重"""
        weights_file = self.project_path / ".moss" / "recommender_weights.json"
        if weights_file.exists():
            try:
                with open(weights_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            'complexity_weight': 1.0,
            'length_weight': 1.0,
            'history_weight': 0.5,
            'coupling_weight': 0.8,
        }

    def recommend(self, file_path: str, content: str) -> List[RefactoringRecommendation]:
        """
        为文件生成重构推荐

        Args:
            file_path: 文件路径
            content: 文件内容

        Returns:
            推荐列表（按优先级排序）
        """
        recommendations = []
        features = self.feature_extractor.extract(file_path, content)

        # 1. 基于规则生成推荐
        rule_recommendations = self._apply_rules(file_path, content, features)
        recommendations.extend(rule_recommendations)

        # 2. 基于历史数据生成推荐
        history_recommendations = self._apply_history(file_path, features)
        recommendations.extend(history_recommendations)

        # 3. 基于模式匹配生成推荐
        pattern_recommendations = self._apply_patterns(file_path, content, features)
        recommendations.extend(pattern_recommendations)

        # 排序和过滤
        recommendations = self._rank_recommendations(recommendations, features)

        return recommendations[:10]  # 返回前 10 个

    def _apply_rules(self, file_path: str, content: str, features: CodeFeatures) -> List[RefactoringRecommendation]:
        """应用重构规则"""
        recommendations = []

        # 检查长函数
        if features.max_function_length > self.refactoring_rules['extract_function']['conditions']['max_function_length']:
            recommendations.append(RefactoringRecommendation(
                recommendation_id=f"rule_extract_{hash(file_path)}",
                action_type='extract_function',
                target_file=file_path,
                target_symbol='long_function',
                line_start=1,
                line_end=features.lines_of_code,
                confidence=min(0.9, features.max_function_length / 100),
                priority=1,
                reason=f"发现长函数 ({features.max_function_length} 行)，建议拆分",
                expected_impact={'lines_reduced': features.max_function_length * 0.3},
            ))

        # 检查高复杂度
        if features.cyclomatic_complexity > self.refactoring_rules['extract_function']['conditions']['cyclomatic_complexity']:
            recommendations.append(RefactoringRecommendation(
                recommendation_id=f"rule_complexity_{hash(file_path)}",
                action_type='extract_function',
                target_file=file_path,
                target_symbol='complex_function',
                line_start=1,
                line_end=features.lines_of_code,
                confidence=min(0.85, features.cyclomatic_complexity / 20),
                priority=1,
                reason=f"函数复杂度过高 (圈复杂度 {features.cyclomatic_complexity})",
                expected_impact={'complexity_reduced': features.cyclomatic_complexity * 0.4},
            ))

        # 检查导入
        if features.num_imports > self.refactoring_rules['organize_imports']['conditions']['num_imports']:
            recommendations.append(RefactoringRecommendation(
                recommendation_id=f"rule_imports_{hash(file_path)}",
                action_type='organize_imports',
                target_file=file_path,
                target_symbol='',
                line_start=1,
                line_end=min(20, features.lines_of_code),
                confidence=0.7,
                priority=5,
                reason=f"导入语句较多 ({features.num_imports} 个)，建议整理",
            ))

        return recommendations

    def _apply_history(self, file_path: str, features: CodeFeatures) -> List[RefactoringRecommendation]:
        """基于历史数据生成推荐"""
        recommendations = []

        # 获取该文件的常见重构模式
        file_actions = self.history_manager.get_actions_for_file(file_path)

        if file_actions:
            # 分析该文件最常做的重构
            action_types = defaultdict(int)
            for action in file_actions:
                if action.user_accepted:
                    action_types[action.action_type] += 1

            for action_type, count in sorted(action_types.items(), key=lambda x: -x[1])[:3]:
                success_rate = self.history_manager.get_success_rate(action_type)
                if success_rate > 0.7:  # 成功率高的才推荐
                    recommendations.append(RefactoringRecommendation(
                        recommendation_id=f"history_{action_type}_{hash(file_path)}",
                        action_type=action_type,
                        target_file=file_path,
                        target_symbol='',
                        line_start=1,
                        line_end=features.lines_of_code,
                        confidence=success_rate,
                        priority=2,
                        reason=f"历史数据显示 {action_type} 成功率高 ({success_rate:.0%})",
                    ))

        return recommendations

    def _apply_patterns(self, file_path: str, content: str, features: CodeFeatures) -> List[RefactoringRecommendation]:
        """应用代码模式匹配"""
        recommendations = []

        try:
            tree = ast.parse(content)

            # 检查嵌套过深
            if features.nesting_depth > 4:
                recommendations.append(RefactoringRecommendation(
                    recommendation_id=f"pattern_nesting_{hash(file_path)}",
                    action_type='extract_function',
                    target_file=file_path,
                    target_symbol='deeply_nested',
                    line_start=1,
                    line_end=features.lines_of_code,
                    confidence=0.75,
                    priority=2,
                    reason=f"代码嵌套过深 ({features.nesting_depth} 层)，建议提取函数",
                ))

            # 检查缺少文档字符串
            if not features.has_docstring and features.num_functions > 0:
                recommendations.append(RefactoringRecommendation(
                    recommendation_id=f"pattern_docstring_{hash(file_path)}",
                    action_type='add_docstring',
                    target_file=file_path,
                    target_symbol='',
                    line_start=1,
                    line_end=features.lines_of_code,
                    confidence=0.6,
                    priority=5,
                    reason="函数缺少文档字符串",
                ))

        except SyntaxError:
            pass

        return recommendations

    def _rank_recommendations(self, recommendations: List[RefactoringRecommendation],
                             features: CodeFeatures) -> List[RefactoringRecommendation]:
        """对推荐进行排序"""

        def score(rec: RefactoringRecommendation) -> float:
            # 综合评分
            s = rec.confidence * 10  # 置信度权重
            s += (6 - rec.priority) * 2  # 优先级权重（优先级数字越小越重要）

            # 根据特征调整
            if rec.action_type == 'extract_function' and features.max_function_length > 100:
                s += 5  # 超长函数额外加分

            return s

        return sorted(recommendations, key=score, reverse=True)

    def learn_from_feedback(self, recommendation: RefactoringRecommendation, accepted: bool):
        """从用户反馈中学习"""
        action = RefactoringAction(
            action_id=recommendation.recommendation_id,
            action_type=recommendation.action_type,
            target_file=recommendation.target_file,
            target_symbol=recommendation.target_symbol,
            line_start=recommendation.line_start,
            line_end=recommendation.line_end,
            before_code='',
            after_code='',
            timestamp=time.time(),
            user_accepted=accepted,
        )
        self.history_manager.record_action(action)

    def get_statistics(self) -> Dict:
        """获取推荐系统统计"""
        return {
            'total_actions_recorded': len(self.history_manager.actions),
            'overall_success_rate': self.history_manager.get_success_rate(),
            'success_rate_by_type': {
                action_type: self.history_manager.get_success_rate(action_type)
                for action_type in set(a.action_type for a in self.history_manager.actions)
            },
            'common_patterns': self.history_manager.get_common_patterns(5),
            'rules_active': len(self.refactoring_rules),
        }


# ──────────────────────────────────────────────────────────────
# Demo
# ──────────────────────────────────────────────────────────────

def demo():
    """演示推荐引擎功能"""
    print("\n" + "="*60)
    print("MOSS v9.3 - ML Refactoring Recommender Demo")
    print("="*60)

    # 创建推荐器
    recommender = RefactoringRecommender("/tmp/moss_demo")

    # 测试代码
    test_code = '''
def very_long_function(x, y, z, a, b, c):
    result = 0
    for i in range(x):
        if i % 2 == 0:
            if i % 3 == 0:
                if i % 5 == 0:
                    result += i * y * z
                else:
                    result -= i * a
            else:
                result += i * b
        else:
            result -= i * c
    
    for j in range(y):
        for k in range(z):
            if j > k:
                result += j * k
            elif j < k:
                result -= j * k
            else:
                result *= 2
    
    for m in range(a):
        if m % 2 == 0:
            result += m
        else:
            result -= m
    
    return result

import os
import sys
import json
import re
from pathlib import Path

def another_function():
    pass
'''

    # 生成推荐
    print("\n[1] 分析代码并生成重构推荐...")
    recommendations = recommender.recommend("test.py", test_code)

    print(f"\n[2] 生成 {len(recommendations)} 个推荐:")
    print("-" * 60)

    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. [{rec.action_type}] 优先级: {rec.priority}")
        print(f"   置信度: {rec.confidence:.0%}")
        print(f"   原因: {rec.reason}")
        if rec.expected_impact:
            print(f"   预期改进: {rec.expected_impact}")

    # 显示统计
    print("\n" + "="*60)
    print("[3] 推荐系统统计:")
    stats = recommender.get_statistics()
    print(f"   记录的操作: {stats['total_actions_recorded']}")
    print(f"   整体成功率: {stats['overall_success_rate']:.0%}")
    print(f"   活跃规则: {stats['rules_active']}")

    # 模拟用户反馈
    print("\n[4] 模拟用户反馈学习...")
    if recommendations:
        recommender.learn_from_feedback(recommendations[0], accepted=True)
        print("   ✓ 已记录用户接受推荐")

    print("\n" + "="*60)
    print("Demo 完成!")
    print("="*60)


if __name__ == "__main__":
    demo()
