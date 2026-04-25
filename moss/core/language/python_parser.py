"""
Python Language Parser

实现 LanguageParser 抽象接口，解析 Python 代码。
"""

import ast
from typing import List, Any, Optional

from . import LanguageParser, LanguageType, ParseResult


class PythonParser(LanguageParser):
    """Python 语言解析器"""
    
    def get_supported_language(self) -> LanguageType:
        """获取支持的语言类型"""
        return LanguageType.PYTHON
    
    def parse(self, content: str, file_path: str) -> ParseResult:
        """解析 Python 代码"""
        errors = []
        ast_tree = None
        symbols = []
        imports = []
        
        try:
            ast_tree = ast.parse(content)
            symbols = self.extract_symbols(ast_tree)
            imports = self.extract_imports(ast_tree)
        except SyntaxError as e:
            errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
        
        return ParseResult(
            file_path=file_path,
            language=LanguageType.PYTHON,
            success=len(errors) == 0,
            ast=ast_tree,
            errors=errors,
            symbols=symbols,
            imports=imports
        )
    
    def extract_symbols(self, ast_tree: Any) -> List[str]:
        """提取符号（函数、类、变量名）"""
        symbols = []
        
        if ast_tree is None:
            return symbols
        
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.FunctionDef):
                symbols.append(node.name)
            elif isinstance(node, ast.ClassDef):
                symbols.append(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        symbols.append(target.id)
        
        return symbols
    
    def extract_imports(self, ast_tree: Any) -> List[str]:
        """提取导入"""
        imports = []
        
        if ast_tree is None:
            return imports
        
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}" if module else alias.name)
        
        return imports
    
    def get_syntax_errors(self, content: str) -> List[str]:
        """检测语法错误"""
        errors = []
        
        try:
            ast.parse(content)
        except SyntaxError as e:
            errors.append(f"Line {e.lineno}: {e.msg}")
        
        return errors
    
    def get_function_complexity(self, node: ast.FunctionDef) -> int:
        """获取函数复杂度（简化版圈复杂度）"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity


__all__ = ['PythonParser']