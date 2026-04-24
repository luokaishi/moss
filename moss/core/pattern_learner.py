#!/usr/bin/env python3
"""
MOSS v9.3 - Pattern Learning System
代码模式学习系统

学习目标:
1. 识别项目中的常见代码模式
2. 检测反模式 (Anti-patterns)
3. 学习最佳实践
4. 提供项目特定的重构建议

Author: MOSS v9.3
Date: 2026-04-24
"""

import ast
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import re


# ──────────────────────────────────────────────────────────────
# Data Structures
# ──────────────────────────────────────────────────────────────

@dataclass
class CodePattern:
    """代码模式"""
    pattern_id: str
    pattern_type: str  # 'structural', 'naming', 'idiom', 'anti-pattern'
    description: str
    examples: List[str] = field(default_factory=list)
    frequency: int = 0
    confidence: float = 0.0
    files: Set[str] = field(default_factory=set)
    metadata: Dict = field(default_factory=dict)


@dataclass
class AntiPattern:
    """反模式"""
    anti_pattern_id: str
    name: str
    description: str
    severity: str  # 'critical', 'warning', 'info'
    detection_pattern: str
    suggested_fix: str
    occurrences: List[Dict] = field(default_factory=list)


@dataclass
class ProjectProfile:
    """项目画像"""
    project_path: str
    total_files: int
    total_lines: int
    language_distribution: Dict[str, int]
    naming_conventions: Dict[str, str]
    common_imports: List[str]
    detected_patterns: List[CodePattern]
    detected_anti_patterns: List[AntiPattern]
    complexity_distribution: Dict[str, int]


# ──────────────────────────────────────────────────────────────
# Pattern Detectors
# ──────────────────────────────────────────────────────────────

class StructuralPatternDetector:
    """结构模式检测器"""

    def __init__(self):
        self.patterns = []

    def detect(self, file_path: str, tree: ast.AST) -> List[CodePattern]:
        """检测结构模式"""
        patterns = []

        # 1. 检测单例模式
        singletons = self._detect_singleton(tree)
        if singletons:
            patterns.append(CodePattern(
                pattern_id=f"singleton_{hash(file_path)}",
                pattern_type='structural',
                description='单例模式实现',
                examples=[f"{file_path}:{s['line']}" for s in singletons],
                frequency=len(singletons),
                confidence=0.9,
                files={file_path},
            ))

        # 2. 检测工厂模式
        factories = self._detect_factory(tree)
        if factories:
            patterns.append(CodePattern(
                pattern_id=f"factory_{hash(file_path)}",
                pattern_type='structural',
                description='工厂模式实现',
                examples=[f"{file_path}:{f['line']}" for f in factories],
                frequency=len(factories),
                confidence=0.85,
                files={file_path},
            ))

        # 3. 检测装饰器模式
        decorators = self._detect_decorator_usage(tree)
        if decorators:
            patterns.append(CodePattern(
                pattern_id=f"decorator_{hash(file_path)}",
                pattern_type='structural',
                description='装饰器模式使用',
                examples=[f"{file_path}:{d['line']}" for d in decorators],
                frequency=len(decorators),
                confidence=0.95,
                files={file_path},
            ))

        # 4. 检测上下文管理器
        context_managers = self._detect_context_manager(tree)
        if context_managers:
            patterns.append(CodePattern(
                pattern_id=f"context_manager_{hash(file_path)}",
                pattern_type='structural',
                description='上下文管理器使用',
                examples=[f"{file_path}:{cm['line']}" for cm in context_managers],
                frequency=len(context_managers),
                confidence=0.95,
                files={file_path},
            ))

        return patterns

    def _detect_singleton(self, tree: ast.AST) -> List[Dict]:
        """检测单例模式"""
        singletons = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # 检查是否有 __new__ 或 _instance 类变量
                has_new = any(isinstance(n, ast.FunctionDef) and n.name == '__new__'
                             for n in node.body)
                has_instance = any(isinstance(n, ast.Assign) and
                                  any(isinstance(t, ast.Name) and t.id == '_instance'
                                      for t in n.targets)
                                  for n in node.body)
                if has_new or has_instance:
                    singletons.append({'class': node.name, 'line': node.lineno})
        return singletons

    def _detect_factory(self, tree: ast.AST) -> List[Dict]:
        """检测工厂模式"""
        factories = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # 检查函数名是否包含 create/make/build
                if any(keyword in node.name.lower() for keyword in ['create', 'make', 'build', 'factory']):
                    # 检查是否返回类实例
                    for child in ast.walk(node):
                        if isinstance(child, ast.Return):
                            if isinstance(child.value, ast.Call):
                                factories.append({'function': node.name, 'line': node.lineno})
                                break
        return factories

    def _detect_decorator_usage(self, tree: ast.AST) -> List[Dict]:
        """检测装饰器使用"""
        decorators = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if node.decorator_list:
                    for dec in node.decorator_list:
                        if isinstance(dec, ast.Name):
                            decorators.append({
                                'target': node.name,
                                'decorator': dec.id,
                                'line': node.lineno,
                            })
        return decorators

    def _detect_context_manager(self, tree: ast.AST) -> List[Dict]:
        """检测上下文管理器"""
        context_managers = []
        for node in ast.walk(tree):
            if isinstance(node, ast.With):
                for item in node.items:
                    if isinstance(item.context_expr, ast.Call):
                        context_managers.append({
                            'type': 'with',
                            'line': node.lineno,
                        })
            elif isinstance(node, ast.ClassDef):
                has_enter = any(isinstance(n, ast.FunctionDef) and n.name == '__enter__'
                               for n in node.body)
                has_exit = any(isinstance(n, ast.FunctionDef) and n.name == '__exit__'
                              for n in node.body)
                if has_enter and has_exit:
                    context_managers.append({
                        'type': 'class',
                        'class': node.name,
                        'line': node.lineno,
                    })
        return context_managers


class NamingConventionDetector:
    """命名约定检测器"""

    def __init__(self):
        self.conventions = {
            'snake_case': re.compile(r'^[a-z_][a-z0-9_]*$'),
            'camelCase': re.compile(r'^[a-z][a-zA-Z0-9]*$'),
            'PascalCase': re.compile(r'^[A-Z][a-zA-Z0-9]*$'),
            'UPPER_CASE': re.compile(r'^[A-Z_][A-Z0-9_]*$'),
        }

    def detect(self, file_path: str, tree: ast.AST) -> Dict[str, str]:
        """检测命名约定"""
        naming_stats = defaultdict(lambda: defaultdict(int))

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                naming_stats['function'][self._classify_name(node.name)] += 1
            elif isinstance(node, ast.ClassDef):
                naming_stats['class'][self._classify_name(node.name)] += 1
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                naming_stats['variable'][self._classify_name(node.id)] += 1

        # 确定主要约定
        conventions = {}
        for category, stats in naming_stats.items():
            if stats:
                conventions[category] = max(stats.items(), key=lambda x: x[1])[0]

        return conventions

    def _classify_name(self, name: str) -> str:
        """分类命名风格"""
        for style, pattern in self.conventions.items():
            if pattern.match(name):
                return style
        return 'mixed'


class AntiPatternDetector:
    """反模式检测器"""

    def __init__(self):
        self.anti_patterns = [
            {
                'id': 'god_class',
                'name': '上帝类',
                'description': '类包含过多方法和属性',
                'severity': 'warning',
                'check': self._check_god_class,
            },
            {
                'id': 'long_method',
                'name': '长方法',
                'description': '方法过长，建议拆分',
                'severity': 'warning',
                'check': self._check_long_method,
            },
            {
                'id': 'duplicate_code',
                'name': '重复代码',
                'description': '检测到相似的代码块',
                'severity': 'info',
                'check': self._check_duplicate_code,
            },
            {
                'id': 'deep_nesting',
                'name': '深层嵌套',
                'description': '代码嵌套层级过深',
                'severity': 'warning',
                'check': self._check_deep_nesting,
            },
            {
                'id': 'unused_import',
                'name': '未使用的导入',
                'description': '存在未使用的导入语句',
                'severity': 'info',
                'check': self._check_unused_import,
            },
            {
                'id': 'bare_except',
                'name': '裸异常捕获',
                'description': '使用裸 except: 捕获所有异常',
                'severity': 'critical',
                'check': self._check_bare_except,
            },
        ]

    def detect(self, file_path: str, content: str, tree: ast.AST) -> List[AntiPattern]:
        """检测反模式"""
        anti_patterns = []

        for pattern_def in self.anti_patterns:
            occurrences = pattern_def['check'](tree, content)
            if occurrences:
                anti_patterns.append(AntiPattern(
                    anti_pattern_id=f"{pattern_def['id']}_{hash(file_path)}",
                    name=pattern_def['name'],
                    description=pattern_def['description'],
                    severity=pattern_def['severity'],
                    detection_pattern=pattern_def['id'],
                    suggested_fix=self._get_suggested_fix(pattern_def['id']),
                    occurrences=occurrences,
                ))

        return anti_patterns

    def _check_god_class(self, tree: ast.AST, content: str) -> List[Dict]:
        """检查上帝类"""
        occurrences = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                method_count = sum(1 for n in node.body if isinstance(n, ast.FunctionDef))
                if method_count > 20:
                    occurrences.append({
                        'class': node.name,
                        'line': node.lineno,
                        'details': f'{method_count} 个方法',
                    })
        return occurrences

    def _check_long_method(self, tree: ast.AST, content: str) -> List[Dict]:
        """检查长方法"""
        occurrences = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                lines = (node.end_lineno or node.lineno) - node.lineno
                if lines > 50:
                    occurrences.append({
                        'function': node.name,
                        'line': node.lineno,
                        'details': f'{lines} 行',
                    })
        return occurrences

    def _check_duplicate_code(self, tree: ast.AST, content: str) -> List[Dict]:
        """检查重复代码（简化版）"""
        occurrences = []
        # 实际实现需要更复杂的代码相似度算法
        return occurrences

    def _check_deep_nesting(self, tree: ast.AST, content: str) -> List[Dict]:
        """检查深层嵌套"""
        occurrences = []

        def get_nesting_depth(node, depth=0):
            max_depth = depth
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.FunctionDef)):
                    max_depth = max(max_depth, get_nesting_depth(child, depth + 1))
                else:
                    max_depth = max(max_depth, get_nesting_depth(child, depth))
            return max_depth

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                depth = get_nesting_depth(node)
                if depth > 4:
                    occurrences.append({
                        'function': node.name,
                        'line': node.lineno,
                        'details': f'{depth} 层嵌套',
                    })

        return occurrences

    def _check_unused_import(self, tree: ast.AST, content: str) -> List[Dict]:
        """检查未使用的导入"""
        occurrences = []
        imported = {}
        used = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imported[name] = node.lineno
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imported[name] = node.lineno
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used.add(node.id)

        for name, line in imported.items():
            if name not in used and name != '*':
                occurrences.append({
                    'import': name,
                    'line': line,
                    'details': name,
                })

        return occurrences

    def _check_bare_except(self, tree: ast.AST, content: str) -> List[Dict]:
        """检查裸异常捕获"""
        occurrences = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    occurrences.append({
                        'line': node.lineno,
                        'details': 'bare except:',
                    })
        return occurrences

    def _get_suggested_fix(self, pattern_id: str) -> str:
        """获取建议修复"""
        fixes = {
            'god_class': '拆分为多个职责单一的类',
            'long_method': '提取子函数，拆分逻辑',
            'duplicate_code': '提取公共函数或类',
            'deep_nesting': '使用卫语句或提取函数',
            'unused_import': '删除未使用的导入',
            'bare_except': '捕获具体的异常类型',
        }
        return fixes.get(pattern_id, '参考最佳实践重构')


# ──────────────────────────────────────────────────────────────
# Pattern Learning Engine
# ──────────────────────────────────────────────────────────────

class PatternLearningEngine:
    """
    模式学习引擎

    分析项目代码，学习常见模式和最佳实践。
    """

    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.structural_detector = StructuralPatternDetector()
        self.naming_detector = NamingConventionDetector()
        self.anti_pattern_detector = AntiPatternDetector()

        self.learned_patterns: List[CodePattern] = []
        self.project_profile: Optional[ProjectProfile] = None

    def learn(self, max_files: int = 100) -> ProjectProfile:
        """
        学习项目模式

        Args:
            max_files: 最大分析文件数

        Returns:
            项目画像
        """
        print(f"\n[PatternLearning] 开始学习项目: {self.project_path}")

        # 收集 Python 文件
        python_files = []
        for py_file in self.project_path.rglob("*.py"):
            if '__pycache__' not in str(py_file) and '.moss' not in str(py_file):
                python_files.append(py_file)

        python_files = python_files[:max_files]
        print(f"  分析 {len(python_files)} 个文件...")

        # 统计信息
        total_lines = 0
        all_patterns = []
        all_anti_patterns = []
        naming_conventions = defaultdict(lambda: defaultdict(int))
        complexity_dist = defaultdict(int)
        common_imports = Counter()

        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                total_lines += len(content.split('\n'))

                try:
                    tree = ast.parse(content)
                except SyntaxError:
                    continue

                # 检测结构模式
                patterns = self.structural_detector.detect(str(file_path), tree)
                all_patterns.extend(patterns)

                # 检测反模式
                anti_patterns = self.anti_pattern_detector.detect(str(file_path), content, tree)
                all_anti_patterns.extend(anti_patterns)

                # 检测命名约定
                conventions = self.naming_detector.detect(str(file_path), tree)
                for category, style in conventions.items():
                    naming_conventions[category][style] += 1

                # 统计导入
                for node in ast.walk(tree):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        for alias in node.names:
                            common_imports[alias.name] += 1

                # 统计复杂度
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        complexity = 1
                        for child in ast.walk(node):
                            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                                complexity += 1
                        if complexity <= 5:
                            complexity_dist['low'] += 1
                        elif complexity <= 10:
                            complexity_dist['medium'] += 1
                        else:
                            complexity_dist['high'] += 1

            except Exception as e:
                print(f"  警告: 无法分析 {file_path}: {e}")

        # 合并相同模式
        merged_patterns = self._merge_patterns(all_patterns)

        # 确定主要命名约定
        final_conventions = {}
        for category, stats in naming_conventions.items():
            if stats:
                final_conventions[category] = max(stats.items(), key=lambda x: x[1])[0]

        # 创建项目画像
        self.project_profile = ProjectProfile(
            project_path=str(self.project_path),
            total_files=len(python_files),
            total_lines=total_lines,
            language_distribution={'python': len(python_files)},
            naming_conventions=final_conventions,
            common_imports=[name for name, _ in common_imports.most_common(10)],
            detected_patterns=merged_patterns,
            detected_anti_patterns=all_anti_patterns,
            complexity_distribution=dict(complexity_dist),
        )

        print(f"\n[PatternLearning] 学习完成!")
        print(f"  发现 {len(merged_patterns)} 个代码模式")
        print(f"  发现 {len(all_anti_patterns)} 个反模式")

        return self.project_profile

    def _merge_patterns(self, patterns: List[CodePattern]) -> List[CodePattern]:
        """合并相同的模式"""
        pattern_groups = defaultdict(list)
        for p in patterns:
            key = (p.pattern_type, p.description)
            pattern_groups[key].append(p)

        merged = []
        for (p_type, desc), group in pattern_groups.items():
            merged.append(CodePattern(
                pattern_id=f"merged_{p_type}_{hash(desc)}",
                pattern_type=p_type,
                description=desc,
                examples=[ex for p in group for ex in p.examples],
                frequency=sum(p.frequency for p in group),
                confidence=sum(p.confidence for p in group) / len(group),
                files=set().union(*[p.files for p in group]),
            ))

        return sorted(merged, key=lambda p: -p.frequency)

    def generate_report(self) -> str:
        """生成学习报告"""
        if not self.project_profile:
            return "请先运行 learn()"

        lines = []
        lines.append("=" * 60)
        lines.append("MOSS v9.3 - 项目模式学习报告")
        lines.append("=" * 60)
        lines.append(f"\n项目: {self.project_profile.project_path}")
        lines.append(f"文件数: {self.project_profile.total_files}")
        lines.append(f"总行数: {self.project_profile.total_lines}")

        lines.append("\n" + "-" * 60)
        lines.append("命名约定:")
        for category, style in self.project_profile.naming_conventions.items():
            lines.append(f"  {category}: {style}")

        lines.append("\n" + "-" * 60)
        lines.append("常用导入:")
        for imp in self.project_profile.common_imports[:5]:
            lines.append(f"  - {imp}")

        lines.append("\n" + "-" * 60)
        lines.append("检测到的代码模式:")
        for pattern in self.project_profile.detected_patterns[:5]:
            lines.append(f"  [{pattern.pattern_type}] {pattern.description}")
            lines.append(f"    频率: {pattern.frequency}, 置信度: {pattern.confidence:.0%}")

        lines.append("\n" + "-" * 60)
        lines.append("检测到的反模式:")
        for anti in self.project_profile.detected_anti_patterns[:5]:
            lines.append(f"  [{anti.severity}] {anti.name}")
            lines.append(f"    {anti.description}")
            lines.append(f"    建议: {anti.suggested_fix}")

        lines.append("\n" + "-" * 60)
        lines.append("复杂度分布:")
        for level, count in self.project_profile.complexity_distribution.items():
            lines.append(f"  {level}: {count} 个函数")

        lines.append("\n" + "=" * 60)

        return '\n'.join(lines)

    def get_suggestions(self) -> List[Dict]:
        """获取改进建议"""
        suggestions = []

        if not self.project_profile:
            return suggestions

        # 基于反模式生成建议
        for anti in self.project_profile.detected_anti_patterns:
            if anti.severity in ['critical', 'warning']:
                suggestions.append({
                    'type': 'anti_pattern',
                    'priority': 1 if anti.severity == 'critical' else 2,
                    'title': f"修复: {anti.name}",
                    'description': anti.description,
                    'suggestion': anti.suggested_fix,
                    'occurrences': len(anti.occurrences),
                })

        # 基于复杂度分布生成建议
        high_complexity = self.project_profile.complexity_distribution.get('high', 0)
        if high_complexity > 10:
            suggestions.append({
                'type': 'complexity',
                'priority': 2,
                'title': "降低代码复杂度",
                'description': f"发现 {high_complexity} 个高复杂度函数",
                'suggestion': "提取子函数，简化条件逻辑",
            })

        # 基于命名约定生成建议
        if len(self.project_profile.naming_conventions) > 1:
            styles = set(self.project_profile.naming_conventions.values())
            if len(styles) > 1:
                suggestions.append({
                    'type': 'convention',
                    'priority': 3,
                    'title': "统一命名约定",
                    'description': f"项目中使用了多种命名风格: {', '.join(styles)}",
                    'suggestion': "建议统一使用一种命名约定",
                })

        return sorted(suggestions, key=lambda x: x['priority'])


# ──────────────────────────────────────────────────────────────
# Demo
# ──────────────────────────────────────────────────────────────

def demo():
    """演示模式学习功能"""
    print("\n" + "="*60)
    print("MOSS v9.3 - Pattern Learning System Demo")
    print("="*60)

    # 创建测试代码
    test_code = '''
import os
import sys
import json
import re

class DatabaseManager:
    """单例数据库管理器"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self):
        pass

class UserService:
    def create_user(self, name, email, age, role, permissions):
        if name and email and age:
            if age > 18:
                if role == 'admin':
                    if permissions:
                        return {'name': name, 'email': email}
        return None

    def update_user(self, user_id, data):
        try:
            # 更新用户
            pass
        except:
            pass  # 裸异常

def create_connection():
    return DatabaseManager()

@decorator
def helper_function():
    pass
'''

    # 保存测试文件
    test_dir = Path("/tmp/moss_pattern_demo")
    test_dir.mkdir(exist_ok=True)

    for i in range(3):
        (test_dir / f"test_{i}.py").write_text(test_code)

    # 学习模式
    engine = PatternLearningEngine(str(test_dir))
    profile = engine.learn()

    # 打印报告
    print(engine.generate_report())

    # 打印建议
    print("\n" + "="*60)
    print("改进建议:")
    print("="*60)
    for suggestion in engine.get_suggestions():
        print(f"\n[{suggestion['priority']}] {suggestion['title']}")
        print(f"  {suggestion['description']}")
        print(f"  建议: {suggestion['suggestion']}")

    print("\n" + "="*60)
    print("Demo 完成!")
    print("="*60)


if __name__ == "__main__":
    demo()
