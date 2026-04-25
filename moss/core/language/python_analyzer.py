"""
Python Language Analyzer

实现 LanguageAnalyzer 抽象接口，分析 Python 代码质量。
"""

import ast
from typing import List, Dict, Any, Set, Optional
from dataclasses import dataclass

from . import (
    LanguageAnalyzer, LanguageType, ParseResult, AnalysisResult
)


@dataclass
class FunctionInfo:
    """函数信息"""
    name: str
    start_line: int
    end_line: int
    complexity: int
    num_params: int
    docstring: Optional[str]


class PythonAnalyzer(LanguageAnalyzer):
    """Python 代码分析器"""
    
    def __init__(self):
        self.long_function_threshold = 50
        self.high_complexity_threshold = 10
    
    def get_supported_language(self) -> LanguageType:
        """获取支持的语言类型"""
        return LanguageType.PYTHON
    
    def analyze(self, parse_result: ParseResult) -> AnalysisResult:
        """分析 Python 代码"""
        issues = []
        
        if not parse_result.success or parse_result.ast is None:
            return AnalysisResult(
                file_path=parse_result.file_path,
                language=LanguageType.PYTHON,
                issues=[{
                    'type': 'parse_error',
                    'message': 'Failed to parse file',
                    'severity': 'error'
                }],
                complexity=0,
                maintainability_index=0.0
            )
        
        # 检测未使用的导入
        unused_imports = self.detect_unused_imports(parse_result)
        for imp in unused_imports:
            issues.append({
                'type': 'unused_import',
                'message': f"Unused import: {imp}",
                'severity': 'warning',
                'line': None
            })
        
        # 检测过长函数
        long_functions = self.detect_long_functions(parse_result)
        for func in long_functions:
            issues.append({
                'type': 'long_function',
                'message': f"Function '{func['name']}' is too long ({func['lines']} lines)",
                'severity': 'warning',
                'line': func['start_line']
            })
        
        # 检测高复杂度
        high_complexity = self.detect_high_complexity(parse_result)
        for func in high_complexity:
            issues.append({
                'type': 'high_complexity',
                'message': f"Function '{func['name']}' has high complexity ({func['complexity']})",
                'severity': 'warning',
                'line': func['start_line']
            })
        
        # 检测缺少文档字符串
        missing_docs = self._detect_missing_docstrings(parse_result)
        for func in missing_docs:
            issues.append({
                'type': 'missing_docstring',
                'message': f"Function '{func}' is missing docstring",
                'severity': 'info',
                'line': None
            })
        
        # 计算复杂度
        total_complexity = self.calculate_complexity(parse_result)
        
        # 计算可维护性指数（简化版）
        loc = self._count_lines(parse_result)
        maintainability = self._calculate_maintainability(
            total_complexity, loc, len(issues)
        )
        
        return AnalysisResult(
            file_path=parse_result.file_path,
            language=LanguageType.PYTHON,
            issues=issues,
            complexity=total_complexity,
            maintainability_index=maintainability
        )
    
    def detect_unused_imports(self, parse_result: ParseResult) -> List[str]:
        """检测未使用的导入"""
        if parse_result.ast is None:
            return []
        
        # 收集所有导入
        imports = set()
        for node in ast.walk(parse_result.ast):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imports.add(name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imports.add(name)
        
        # 收集所有使用的名称
        used_names: Set[str] = set()
        for node in ast.walk(parse_result.ast):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                # 处理 obj.attr 形式的使用
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)
        
        # 找出未使用的导入
        unused = []
        for imp in imports:
            if imp not in used_names:
                unused.append(imp)
        
        return unused
    
    def detect_long_functions(self, parse_result: ParseResult, threshold: int = None) -> List[Dict]:
        """检测过长的函数"""
        threshold = threshold or self.long_function_threshold
        
        if parse_result.ast is None:
            return []
        
        long_functions = []
        
        for node in ast.walk(parse_result.ast):
            if isinstance(node, ast.FunctionDef):
                # 计算函数行数
                start_line = node.lineno
                end_line = self._get_end_line(node)
                lines = end_line - start_line + 1
                
                if lines > threshold:
                    long_functions.append({
                        'name': node.name,
                        'start_line': start_line,
                        'end_line': end_line,
                        'lines': lines
                    })
        
        return long_functions
    
    def detect_high_complexity(self, parse_result: ParseResult, threshold: int = None) -> List[Dict]:
        """检测高复杂度函数"""
        threshold = threshold or self.high_complexity_threshold
        
        if parse_result.ast is None:
            return []
        
        high_complexity = []
        
        for node in ast.walk(parse_result.ast):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_function_complexity(node)
                if complexity > threshold:
                    high_complexity.append({
                        'name': node.name,
                        'start_line': node.lineno,
                        'complexity': complexity
                    })
        
        return high_complexity
    
    def calculate_complexity(self, parse_result: ParseResult) -> int:
        """计算代码复杂度"""
        if parse_result.ast is None:
            return 0
        
        total_complexity = 1
        
        for node in ast.walk(parse_result.ast):
            if isinstance(node, (ast.If, ast.While, ast.For)):
                total_complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                total_complexity += 1
            elif isinstance(node, ast.BoolOp):
                total_complexity += len(node.values) - 1
            elif isinstance(node, (ast.And, ast.Or)):
                total_complexity += 1
        
        return total_complexity
    
    def _get_end_line(self, node: ast.AST) -> int:
        """获取节点的结束行号"""
        end_line = node.lineno
        
        for child in ast.walk(node):
            if hasattr(child, 'lineno'):
                end_line = max(end_line, child.lineno)
            if hasattr(child, 'end_lineno') and child.end_lineno:
                end_line = max(end_line, child.end_lineno)
        
        return end_line
    
    def _calculate_function_complexity(self, node: ast.FunctionDef) -> int:
        """计算函数的圈复杂度"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
                if child.ifs:
                    complexity += len(child.ifs)
        
        return complexity
    
    def _detect_missing_docstrings(self, parse_result: ParseResult) -> List[str]:
        """检测缺少文档字符串的函数"""
        if parse_result.ast is None:
            return []
        
        missing = []
        
        for node in ast.walk(parse_result.ast):
            if isinstance(node, ast.FunctionDef):
                # 跳过私有方法和特殊方法
                if node.name.startswith('_'):
                    continue
                
                # 检查是否有文档字符串
                if not (node.body and isinstance(node.body[0], ast.Expr) 
                        and isinstance(node.body[0].value, ast.Constant)
                        and isinstance(node.body[0].value.value, str)):
                    missing.append(node.name)
        
        return missing
    
    def _count_lines(self, parse_result: ParseResult) -> int:
        """计算代码行数"""
        if parse_result.ast is None:
            return 0
        
        max_line = 0
        for node in ast.walk(parse_result.ast):
            if hasattr(node, 'lineno'):
                max_line = max(max_line, node.lineno)
        
        return max_line
    
    def _calculate_maintainability(self, complexity: int, loc: int, issues_count: int) -> float:
        """计算可维护性指数"""
        if loc == 0:
            return 100.0
        
        # 简化的可维护性指数计算
        # 基于 SEI 可维护性指数简化版
        volume = max(loc, 1)
        
        # 复杂度因子
        complexity_factor = 1 - min(complexity / 100, 0.5)
        
        # 问题因子
        issues_factor = 1 - min(issues_count / 50, 0.3)
        
        maintainability = 100 * complexity_factor * issues_factor
        
        return max(0, min(100, maintainability))


__all__ = ['PythonAnalyzer', 'FunctionInfo']
