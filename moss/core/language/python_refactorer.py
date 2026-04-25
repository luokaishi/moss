"""
Python Language Refactorer

实现 LanguageRefactorer 抽象接口，执行 Python 代码重构。
"""

import ast
import re
import textwrap
from typing import Dict, List, Any, Optional, Tuple

from . import (
    LanguageRefactorer, LanguageType, ParseResult, RefactorResult
)


class PythonRefactorer(LanguageRefactorer):
    """Python 代码重构器"""
    
    def get_supported_language(self) -> LanguageType:
        """获取支持的语言类型"""
        return LanguageType.PYTHON
    
    def refactor(self, parse_result: ParseResult, operation: str, params: Dict) -> RefactorResult:
        """执行重构"""
        operations = {
            'organize_imports': self._refactor_organize_imports,
            'extract_function': self._refactor_extract_function,
            'rename_symbol': self._refactor_rename_symbol,
            'remove_unused_imports': self._refactor_remove_unused_imports,
            'add_docstrings': self._refactor_add_docstrings,
        }
        
        handler = operations.get(operation)
        if not handler:
            return RefactorResult(
                file_path=parse_result.file_path,
                language=LanguageType.PYTHON,
                success=False,
                changes=[],
                error=f"Unknown operation: {operation}"
            )
        
        return handler(parse_result, params)
    
    def organize_imports(self, content: str) -> str:
        """整理导入语句"""
        lines = content.split('\n')
        
        # 收集所有导入
        imports = []
        import_lines = []
        other_lines = []
        in_import_block = True
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            if in_import_block:
                if stripped.startswith('import ') or stripped.startswith('from '):
                    imports.append(stripped)
                    import_lines.append(i)
                elif stripped == '' or stripped.startswith('#'):
                    other_lines.append(line)
                else:
                    in_import_block = False
                    other_lines.append(line)
            else:
                other_lines.append(line)
        
        # 排序导入
        # 标准/第三方库
        stdlib_imports = []
        third_party_imports = []
        local_imports = []
        
        for imp in imports:
            if imp.startswith('from .') or imp.startswith('from ..'):
                local_imports.append(imp)
            elif any(imp.startswith(f'from {m}') or imp == f'import {m}' 
                     for m in ['os', 'sys', 're', 'json', 'time', 'datetime', 'pathlib', 'typing', 'collections', 'itertools', 'functools', 'abc', 'dataclasses', 'enum', 'logging', 'warnings', 'copy', 'math', 'random', 'string', 'io', 'contextlib', 'threading', 'multiprocessing', 'subprocess', 'argparse', 'configparser', 'tempfile', 'shutil', 'glob', 'fnmatch', 'pickle', 'shelve', 'sqlite3', 'hashlib', 'hmac', 'secrets', 'struct', 'codecs', 'unicodedata', 'textwrap', 'difflib', 'heapq', 'bisect', 'array', 'weakref', 'types', 'reprlib', 'pprint', 'repr', 'operator', 'ast', 'tokenize', 'keyword', 'token', 'symbol', 'tokenize', 'parser', 'codeop', 'code', 'codecs', 'encodings', 'runpy', 'importlib', 'pkgutil', 'modulefinder', 'zipimport', 'traceback', 'faulthandler', 'pdb', 'profile', 'cProfile', 'timeit', 'trace', 'unittest', 'doctest', 'venv', 'zipapp', 'socket', 'ssl', 'select', 'selectors', 'asyncio', 'signal', 'mmap', 'email', 'json', 'mailbox', 'mimetypes', 'base64', 'binascii', 'quopri', 'uu', 'html', 'xml', 'xmlrpc', 'webbrowser', 'cgi', 'cgitb', 'wsgiref', 'urllib', 'http', 'ftplib', 'poplib', 'imaplib', 'smtplib', 'nntplib', 'telnetlib', 'uuid', 'socketserver', 'http.server', 'http.client', 'http.cookies', 'http.cookiejar', 'xml.parsers', 'xml.sax', 'xml.dom', 'xml.etree', 'csv', 'configparser', 'netrc', 'xdrlib', 'plistlib', 'platform', 'errno', 'ctypes', 'ctypes.wintypes', 'winsound', 'msvcrt', 'winreg', 'winapi', 'glob', 'fnmatch', 'linecache', 'shutil', 'stat', 'filecmp', 'tempfile', 'glob', 'socket', 'select', 'selectors', 'io', 'os', 'os.path', 'pathlib', 'fileinput', 'stat', 'filecmp', 'tempfile', 'glob', 'fnmatch', 'linecache', 'shutil', 'pickle', 'shelve', 'dbm', 'sqlite3', 'csv', 'configparser', 'netrc', 'xdrlib', 'plistlib', 'email', 'json', 'mailbox', 'mimetypes', 'base64', 'binascii', 'quopri', 'uu']):
                stdlib_imports.append(imp)
            else:
                third_party_imports.append(imp)
        
        # 排序
        stdlib_imports.sort()
        third_party_imports.sort()
        local_imports.sort()
        
        # 组装新导入块
        new_imports = []
        
        if stdlib_imports:
            new_imports.extend(stdlib_imports)
        
        if third_party_imports:
            if new_imports:
                new_imports.append('')  # 空行分隔
            new_imports.extend(third_party_imports)
        
        if local_imports:
            if new_imports:
                new_imports.append('')  # 空行分隔
            new_imports.extend(local_imports)
        
        # 重建内容
        result_lines = []
        result_lines.extend(new_imports)
        result_lines.append('')  # 导入后空行
        result_lines.extend(other_lines)
        
        return '\n'.join(result_lines)
    
    def extract_function(self, content: str, start_line: int, end_line: int, name: str) -> str:
        """提取选中代码为新函数"""
        lines = content.split('\n')
        
        # 提取选中的代码
        selected = '\n'.join(lines[start_line - 1:end_line])
        
        # 计算缩进
        base_indent = len(selected) - len(selected.lstrip())
        indent_str = ' ' * base_indent
        
        # 创建新函数
        new_func = f"{indent_str}def {name}():\n{textwrap.indent(selected, '    ')}\n"
        
        # 替换原代码
        new_lines = lines[:start_line - 1] + [new_func] + lines[end_line:]
        
        return '\n'.join(new_lines)
    
    def rename_symbol(self, content: str, old_name: str, new_name: str) -> str:
        """重命名符号"""
        # 使用 AST 分析确保只重命名正确的位置
        try:
            tree = ast.parse(content)
        except SyntaxError:
            # 如果解析失败，使用简单字符串替换
            return self._simple_rename(content, old_name, new_name)
        
        # 收集需要替换的位置
        replacements: List[Tuple[int, int]] = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == old_name:
                replacements.append((node.lineno, node.col_offset))
            elif isinstance(node, ast.FunctionDef) and node.name == old_name:
                # 函数定义
                replacements.append((node.lineno, node.col_offset))
            elif isinstance(node, ast.ClassDef) and node.name == old_name:
                # 类定义
                replacements.append((node.lineno, node.col_offset))
            elif isinstance(node, ast.arg) and node.arg == old_name:
                # 参数
                replacements.append((node.lineno, node.col_offset))
            elif isinstance(node, ast.Attribute) and node.attr == old_name:
                # 属性
                replacements.append((node.lineno, node.col_offset + len(node.value.id) + 1 if isinstance(node.value, ast.Name) else 0))
        
        # 执行替换（从后向前）
        lines = content.split('\n')
        
        for line_no, col in sorted(replacements, reverse=True):
            line = lines[line_no - 1]
            # 在指定位置替换
            idx = line.find(old_name, col)
            if idx != -1:
                lines[line_no - 1] = line[:idx] + new_name + line[idx + len(old_name):]
        
        return '\n'.join(lines)
    
    def _simple_rename(self, content: str, old_name: str, new_name: str) -> str:
        """简单字符串替换"""
        # 使用正则表达式匹配单词边界
        pattern = r'\b' + re.escape(old_name) + r'\b'
        return re.sub(pattern, new_name, content)
    
    def _refactor_organize_imports(self, parse_result: ParseResult, params: Dict) -> RefactorResult:
        """整理导入重构"""
        if parse_result.ast is None:
            return RefactorResult(
                file_path=parse_result.file_path,
                language=LanguageType.PYTHON,
                success=False,
                changes=[]
            )
        
        # 这里需要原始内容，从 params 获取或重新读取
        content = params.get('content', '')
        if not content:
            return RefactorResult(
                file_path=parse_result.file_path,
                language=LanguageType.PYTHON,
                success=False,
                changes=[]
            )
        
        new_content = self.organize_imports(content)
        
        return RefactorResult(
            file_path=parse_result.file_path,
            language=LanguageType.PYTHON,
            success=True,
            changes=[{
                'type': 'organize_imports',
                'description': 'Organized import statements'
            }],
            original_content=content,
            new_content=new_content
        )
    
    def _refactor_extract_function(self, parse_result: ParseResult, params: Dict) -> RefactorResult:
        """提取函数重构"""
        content = params.get('content', '')
        start_line = params.get('start_line', 1)
        end_line = params.get('end_line', 1)
        name = params.get('name', 'extracted_function')
        
        if not content:
            return RefactorResult(
                file_path=parse_result.file_path,
                language=LanguageType.PYTHON,
                success=False,
                changes=[]
            )
        
        new_content = self.extract_function(content, start_line, end_line, name)
        
        return RefactorResult(
            file_path=parse_result.file_path,
            language=LanguageType.PYTHON,
            success=True,
            changes=[{
                'type': 'extract_function',
                'name': name,
                'start_line': start_line,
                'end_line': end_line
            }],
            original_content=content,
            new_content=new_content
        )
    
    def _refactor_rename_symbol(self, parse_result: ParseResult, params: Dict) -> RefactorResult:
        """重命名符号重构"""
        content = params.get('content', '')
        old_name = params.get('old_name', '')
        new_name = params.get('new_name', '')
        
        if not content or not old_name or not new_name:
            return RefactorResult(
                file_path=parse_result.file_path,
                language=LanguageType.PYTHON,
                success=False,
                changes=[]
            )
        
        new_content = self.rename_symbol(content, old_name, new_name)
        
        return RefactorResult(
            file_path=parse_result.file_path,
            language=LanguageType.PYTHON,
            success=True,
            changes=[{
                'type': 'rename_symbol',
                'old_name': old_name,
                'new_name': new_name
            }],
            original_content=content,
            new_content=new_content
        )
    
    def _refactor_remove_unused_imports(self, parse_result: ParseResult, params: Dict) -> RefactorResult:
        """移除未使用的导入"""
        # 这需要分析器配合
        unused = params.get('unused_imports', [])
        content = params.get('content', '')
        
        if not unused or not content:
            return RefactorResult(
                file_path=parse_result.file_path,
                language=LanguageType.PYTHON,
                success=False,
                changes=[]
            )
        
        lines = content.split('\n')
        new_lines = []
        
        for line in lines:
            stripped = line.strip()
            is_unused = False
            
            if stripped.startswith('import ') or stripped.startswith('from '):
                for imp in unused:
                    if imp in stripped:
                        is_unused = True
                        break
            
            if not is_unused:
                new_lines.append(line)
        
        new_content = '\n'.join(new_lines)
        
        return RefactorResult(
            file_path=parse_result.file_path,
            language=LanguageType.PYTHON,
            success=True,
            changes=[{
                'type': 'remove_unused_imports',
                'removed': unused
            }],
            original_content=content,
            new_content=new_content
        )
    
    def _refactor_add_docstrings(self, parse_result: ParseResult, params: Dict) -> RefactorResult:
        """添加文档字符串"""
        content = params.get('content', '')
        functions = params.get('functions', [])
        
        if not content or not functions:
            return RefactorResult(
                file_path=parse_result.file_path,
                language=LanguageType.PYTHON,
                success=False,
                changes=[]
            )
        
        lines = content.split('\n')
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return RefactorResult(
                file_path=parse_result.file_path,
                language=LanguageType.PYTHON,
                success=False,
                changes=[]
            )
        
        # 找到需要添加文档字符串的函数
        changes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name in functions:
                    # 检查是否已有文档字符串
                    if not (node.body and isinstance(node.body[0], ast.Expr) 
                            and isinstance(node.body[0].value, ast.Constant)):
                        # 添加文档字符串
                        indent = '    '  # 标准缩进
                        docstring = f'{indent}"""TODO: Add docstring for {node.name}"""'
                        lines.insert(node.lineno, docstring)
                        changes.append({
                            'type': 'add_docstring',
                            'function': node.name,
                            'line': node.lineno
                        })
        
        new_content = '\n'.join(lines)
        
        return RefactorResult(
            file_path=parse_result.file_path,
            language=LanguageType.PYTHON,
            success=len(changes) > 0,
            changes=changes,
            original_content=content,
            new_content=new_content
        )


__all__ = ['PythonRefactorer']
