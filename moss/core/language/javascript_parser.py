"""
JavaScript Language Parser

基于正则的轻量级解析器，验证语言抽象层有效性。
未来可替换为完整解析器 (esprima/tree-sitter)。
"""

import re
from typing import List, Any, Optional

from . import LanguageParser, LanguageType, ParseResult


class JavaScriptParser(LanguageParser):
    """JavaScript 语言解析器（轻量级实现）"""
    
    # 正则模式
    FUNCTION_PATTERN = re.compile(
        r'(?:async\s+)?function\s+(\w+)\s*\(|'
        r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>|'
        r'(\w+)\s*\([^)]*\)\s*\{',  # 方法简写
        re.MULTILINE
    )
    
    CLASS_PATTERN = re.compile(
        r'class\s+(\w+)(?:\s+extends\s+(\w+))?',
        re.MULTILINE
    )
    
    IMPORT_PATTERN = re.compile(
        r'import\s+(?:(\{[^}]+\}|\*\s+as\s+\w+|\w+)\s+from\s+)?[\'"]([^\'"]+)[\'"]|'
        r'const\s+(\w+)\s+=\s+require\([\'"]([^\'"]+)[\'"]\)',
        re.MULTILINE
    )
    
    EXPORT_PATTERN = re.compile(
        r'export\s+(?:default\s+)?(?:class|function|const|let|var)?\s*(\w+)?',
        re.MULTILINE
    )
    
    def get_supported_language(self) -> LanguageType:
        """获取支持的语言类型"""
        return LanguageType.JAVASCRIPT
    
    def parse(self, content: str, file_path: str) -> ParseResult:
        """解析 JavaScript 代码（轻量级）"""
        errors = self.get_syntax_errors(content)
        
        # 提取符号
        symbols = self.extract_symbols(None, content)
        
        # 提取导入
        imports = self.extract_imports(None, content)
        
        # 简单AST表示
        ast = {
            'type': 'Program',
            'functions': self._extract_functions(content),
            'classes': self._extract_classes(content),
            'imports': imports,
            'exports': self._extract_exports(content),
        }
        
        return ParseResult(
            file_path=file_path,
            language=LanguageType.JAVASCRIPT,
            success=len(errors) == 0,
            ast=ast,
            errors=errors,
            symbols=symbols,
            imports=imports
        )
    
    def extract_symbols(self, ast: Any, content: str = None) -> List[str]:
        """提取符号（函数、类、变量名）"""
        if content is None and ast is not None:
            # 从AST提取
            content = ast.get('raw_content', '')
        
        if content is None:
            return []
        
        symbols = []
        
        # 函数
        for match in self.FUNCTION_PATTERN.finditer(content):
            func_name = match.group(1) or match.group(2) or match.group(3)
            if func_name:
                symbols.append(func_name)
        
        # 类
        for match in self.CLASS_PATTERN.finditer(content):
            class_name = match.group(1)
            if class_name:
                symbols.append(class_name)
        
        # 变量声明
        var_pattern = re.compile(r'(?:const|let|var)\s+(\w+)', re.MULTILINE)
        for match in var_pattern.finditer(content):
            symbols.append(match.group(1))
        
        return list(set(symbols))  # 去重
    
    def extract_imports(self, ast: Any, content: str = None) -> List[str]:
        """提取导入"""
        if content is None and ast is not None:
            content = ast.get('raw_content', '')
        
        if content is None:
            return []
        
        imports = []
        
        for match in self.IMPORT_PATTERN.finditer(content):
            # ES6 import: import X from 'module'
            if match.group(2):
                imports.append(match.group(2))
            # CommonJS: const X = require('module')
            elif match.group(4):
                imports.append(match.group(4))
        
        return imports
    
    def get_syntax_errors(self, content: str) -> List[str]:
        """检测语法错误（基础检查）"""
        errors = []
        
        # 检查括号匹配
        stack = []
        pairs = {'(': ')', '[': ']', '{': '}'}
        
        for i, char in enumerate(content):
            if char in pairs:
                stack.append((char, i))
            elif char in pairs.values():
                if stack and pairs[stack[-1][0]] == char:
                    stack.pop()
                else:
                    line = content[:i].count('\n') + 1
                    errors.append(f"Line {line}: Mismatched bracket '{char}'")
        
        if stack:
            for char, pos in stack:
                line = content[:pos].count('\n') + 1
                errors.append(f"Line {line}: Unclosed bracket '{char}'")
        
        # 检查常见语法错误
        if re.search(r'\bfunction\s*\(', content):
            errors.append("Anonymous function declaration without name")
        
        # 检查未闭合的字符串
        single_quotes = content.count("'") - content.count("\\'")
        double_quotes = content.count('"') - content.count('\\"')
        backticks = content.count('`') - content.count('\\`')
        
        # 简化的字符串检查（在注释中可能会有误报）
        # 实际使用完整解析器更准确
        
        return errors
    
    def _extract_functions(self, content: str) -> List[dict]:
        """提取函数信息"""
        functions = []
        
        for match in self.FUNCTION_PATTERN.finditer(content):
            func_name = match.group(1) or match.group(2) or match.group(3)
            if func_name:
                line = content[:match.start()].count('\n') + 1
                functions.append({
                    'name': func_name,
                    'line': line,
                    'type': 'function'
                })
        
        return functions
    
    def _extract_classes(self, content: str) -> List[dict]:
        """提取类信息"""
        classes = []
        
        for match in self.CLASS_PATTERN.finditer(content):
            class_name = match.group(1)
            parent = match.group(2)
            if class_name:
                line = content[:match.start()].count('\n') + 1
                classes.append({
                    'name': class_name,
                    'line': line,
                    'extends': parent,
                    'type': 'class'
                })
        
        return classes
    
    def _extract_exports(self, content: str) -> List[dict]:
        """提取导出信息"""
        exports = []
        
        for match in self.EXPORT_PATTERN.finditer(content):
            name = match.group(1)
            line = content[:match.start()].count('\n') + 1
            exports.append({
                'name': name,
                'line': line,
                'type': 'export'
            })
        
        return exports
    
    def get_function_complexity(self, content: str, func_name: str) -> int:
        """获取函数复杂度（简化版）"""
        # 找到函数定义
        pattern = rf'(?:async\s+)?function\s+{re.escape(func_name)}\s*\([^)]*\)\s*\{{'
        match = re.search(pattern, content, re.MULTILINE)
        
        if not match:
            return 0
        
        # 提取函数体（简化处理，实际应该找匹配的}）
        start = match.end()
        end = self._find_matching_brace(content, start)
        
        if end == -1:
            return 0
        
        func_body = content[start:end]
        
        # 计算复杂度
        complexity = 1
        complexity += len(re.findall(r'\bif\b', func_body))
        complexity += len(re.findall(r'\belse\s+if\b', func_body))
        complexity += len(re.findall(r'\bwhile\b', func_body))
        complexity += len(re.findall(r'\bfor\b', func_body))
        complexity += len(re.findall(r'\bcatch\b', func_body))
        complexity += len(re.findall(r'\?\s*[^:?]+\s*:', func_body))  # 三元运算符
        complexity += len(re.findall(r'&&|\|\|', func_body))  # 逻辑运算符
        
        return complexity
    
    def _find_matching_brace(self, content: str, start: int) -> int:
        """找到匹配的右大括号"""
        depth = 1
        in_string = False
        string_char = None
        escaped = False
        
        for i in range(start, len(content)):
            char = content[i]
            
            if escaped:
                escaped = False
                continue
            
            if char == '\\':
                escaped = True
                continue
            
            if char in ('"', "'", '`'):
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
                    string_char = None
                continue
            
            if in_string:
                continue
            
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    return i
        
        return -1


__all__ = ['JavaScriptParser']
