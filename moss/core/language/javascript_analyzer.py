"""
JavaScript Language Analyzer

基于轻量级解析的代码分析器。
"""

import re
from typing import List, Dict, Any, Optional

from . import LanguageAnalyzer, LanguageType, ParseResult, AnalysisResult
from .javascript_parser import JavaScriptParser


class JavaScriptAnalyzer(LanguageAnalyzer):
    """JavaScript 代码分析器"""
    
    def __init__(self):
        self.parser = JavaScriptParser()
        self.long_function_threshold = 50
        self.high_complexity_threshold = 10
    
    def get_supported_language(self) -> LanguageType:
        """获取支持的语言类型"""
        return LanguageType.JAVASCRIPT
    
    def analyze(self, parse_result: ParseResult, content: str = None) -> AnalysisResult:
        """分析 JavaScript 代码"""
        issues = []
        
        if not parse_result.success:
            return AnalysisResult(
                file_path=parse_result.file_path,
                language=LanguageType.JAVASCRIPT,
                issues=[{
                    'type': 'parse_error',
                    'message': 'Failed to parse file',
                    'severity': 'error'
                }],
                complexity=0,
                maintainability_index=0.0
            )
        
        ast = parse_result.ast or {}
        # 优先使用传入的content，否则从AST获取
        if content is None:
            content = self._get_content_from_ast(ast)
        
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
        
        # 检测var使用
        var_usages = self._detect_var_usage(content)
        for line in var_usages:
            issues.append({
                'type': 'prefer_const_let',
                'message': "Consider using 'const' or 'let' instead of 'var'",
                'severity': 'info',
                'line': line
            })
        
        # 检测console.log
        console_logs = self._detect_console_logs(content)
        for line in console_logs:
            issues.append({
                'type': 'console_log',
                'message': "console.log found - consider removing for production",
                'severity': 'info',
                'line': line
            })
        
        # 检测未使用的变量
        unused_vars = self._detect_unused_variables(content)
        for var in unused_vars:
            issues.append({
                'type': 'unused_variable',
                'message': f"Unused variable: {var['name']}",
                'severity': 'info',
                'line': var['line']
            })
        
        # 计算复杂度
        total_complexity = self.calculate_complexity(parse_result)
        
        # 计算可维护性指数
        loc = content.count('\n') + 1 if content else 0
        maintainability = self._calculate_maintainability(
            total_complexity, loc, len(issues)
        )
        
        return AnalysisResult(
            file_path=parse_result.file_path,
            language=LanguageType.JAVASCRIPT,
            issues=issues,
            complexity=total_complexity,
            maintainability_index=maintainability
        )
    
    def detect_unused_imports(self, parse_result: ParseResult) -> List[str]:
        """检测未使用的导入"""
        ast = parse_result.ast or {}
        imports = ast.get('imports', [])
        
        if not imports:
            return []
        
        # 获取所有符号使用情况
        content = self._get_content_from_ast(ast)
        if not content:
            return []
        
        unused = []
        
        for imp in imports:
            # 简化检查：导入模块名是否出现在代码中（不包括导入语句本身）
            # 更精确的做法是跟踪每个导入的符号使用情况
            import_pattern = re.compile(rf'\b{re.escape(imp)}\b')
            matches = list(import_pattern.finditer(content))
            
            # 如果只有导入语句中有出现，则视为未使用
            # 这里简化处理，实际应该解析每个导入的符号
            if len(matches) <= 1:  # 只在import语句中出现
                unused.append(imp)
        
        return unused
    
    def detect_long_functions(self, parse_result: ParseResult, threshold: int = None) -> List[Dict]:
        """检测过长的函数"""
        threshold = threshold or self.long_function_threshold
        ast = parse_result.ast or {}
        content = self._get_content_from_ast(ast)
        
        if not content:
            return []
        
        long_functions = []
        functions = ast.get('functions', [])
        
        for func in functions:
            func_name = func.get('name')
            start_line = func.get('line', 1)
            
            # 使用解析器的方法计算函数长度
            lines = self._calculate_function_lines(content, func_name)
            
            if lines > threshold:
                long_functions.append({
                    'name': func_name,
                    'start_line': start_line,
                    'lines': lines
                })
        
        return long_functions
    
    def detect_high_complexity(self, parse_result: ParseResult, threshold: int = None) -> List[Dict]:
        """检测高复杂度函数"""
        threshold = threshold or self.high_complexity_threshold
        ast = parse_result.ast or {}
        content = self._get_content_from_ast(ast)
        
        if not content:
            return []
        
        high_complexity = []
        functions = ast.get('functions', [])
        
        for func in functions:
            func_name = func.get('name')
            if not func_name:
                continue
            
            complexity = self.parser.get_function_complexity(content, func_name)
            
            if complexity > threshold:
                high_complexity.append({
                    'name': func_name,
                    'start_line': func.get('line', 1),
                    'complexity': complexity
                })
        
        return high_complexity
    
    def calculate_complexity(self, parse_result: ParseResult) -> int:
        """计算代码复杂度"""
        ast = parse_result.ast or {}
        content = self._get_content_from_ast(ast)
        
        if not content:
            return 0
        
        total_complexity = 1
        
        # 计算所有函数的复杂度
        functions = ast.get('functions', [])
        for func in functions:
            func_name = func.get('name')
            if func_name:
                total_complexity += self.parser.get_function_complexity(content, func_name)
        
        return total_complexity
    
    def _get_content_from_ast(self, ast: dict) -> str:
        """从AST获取原始内容"""
        # 轻量级解析器不保存原始内容，返回空字符串
        # 完整实现应该存储原始内容
        return ""
    
    def _calculate_function_lines(self, content: str, func_name: str) -> int:
        """计算函数行数"""
        # 简化实现：找到函数定义，估算行数
        pattern = rf'(?:async\s+)?function\s+{re.escape(func_name)}\s*\([^)]*\)\s*\{{'
        match = re.search(pattern, content, re.MULTILINE)
        
        if not match:
            return 0
        
        start = match.end()
        end = self.parser._find_matching_brace(content, start)
        
        if end == -1:
            return 0
        
        func_content = content[start:end]
        return func_content.count('\n') + 1
    
    def _detect_var_usage(self, content: str) -> List[int]:
        """检测var关键字使用"""
        lines = []
        pattern = re.compile(r'\bvar\b\s+')
        
        for match in pattern.finditer(content):
            line = content[:match.start()].count('\n') + 1
            lines.append(line)
        
        return lines
    
    def _detect_console_logs(self, content: str) -> List[int]:
        """检测console.log"""
        lines = []
        pattern = re.compile(r'console\.log\s*\(')
        
        for match in pattern.finditer(content):
            line = content[:match.start()].count('\n') + 1
            lines.append(line)
        
        return lines
    
    def _detect_unused_variables(self, content: str) -> List[dict]:
        """检测未使用的变量"""
        unused = []
        
        # 找出所有变量声明
        var_pattern = re.compile(r'(?:const|let|var)\s+(\w+)', re.MULTILINE)
        
        for match in var_pattern.finditer(content):
            var_name = match.group(1)
            line = content[:match.start()].count('\n') + 1
            
            # 检查变量是否在其他地方使用（简化检查）
            # 排除声明本身，查找其他使用
            usage_pattern = rf'\b{re.escape(var_name)}\b'
            usages = list(re.finditer(usage_pattern, content))
            
            # 如果只出现一次（即声明本身），视为未使用
            if len(usages) == 1:
                unused.append({'name': var_name, 'line': line})
        
        return unused
    
    def _calculate_maintainability(self, complexity: int, loc: int, issues_count: int) -> float:
        """计算可维护性指数"""
        if loc == 0:
            return 100.0
        
        # 简化的可维护性指数
        volume = max(loc, 1)
        complexity_factor = 1 - min(complexity / 100, 0.5)
        issues_factor = 1 - min(issues_count / 50, 0.3)
        
        maintainability = 100 * complexity_factor * issues_factor
        
        return max(0, min(100, maintainability))


__all__ = ['JavaScriptAnalyzer']
