"""
JavaScript Language Refactorer

基础重构操作实现。
"""

import re
from typing import Dict, List, Any

from . import LanguageRefactorer, LanguageType, ParseResult, RefactorResult


class JavaScriptRefactorer(LanguageRefactorer):
    """JavaScript 代码重构器"""
    
    def get_supported_language(self) -> LanguageType:
        """获取支持的语言类型"""
        return LanguageType.JAVASCRIPT
    
    def refactor(self, parse_result: ParseResult, operation: str, params: Dict) -> RefactorResult:
        """执行重构"""
        operations = {
            'organize_imports': self._refactor_organize_imports,
            'remove_unused_imports': self._refactor_remove_unused_imports,
            'convert_var_to_const': self._refactor_convert_var,
            'remove_console_logs': self._refactor_remove_console_logs,
        }
        
        handler = operations.get(operation)
        if not handler:
            return RefactorResult(
                file_path=parse_result.file_path,
                language=LanguageType.JAVASCRIPT,
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
        other_lines = []
        in_import_block = True
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            if in_import_block:
                if stripped.startswith('import ') or stripped.startswith('const ') and 'require(' in stripped:
                    imports.append(line)
                elif stripped == '' or stripped.startswith('//'):
                    other_lines.append(line)
                else:
                    in_import_block = False
                    other_lines.append(line)
            else:
                other_lines.append(line)
        
        # 分类导入
        builtin = []      # 内置模块 (fs, path, etc.)
        external = []     # 第三方 (react, lodash, etc.)
        internal = []     # 项目内部 (./, ../)
        
        for imp in imports:
            # 提取模块名
            match = re.search(r'from\s+[\'"]([^\'"]+)[\'"]', imp)
            if match:
                module = match.group(1)
            else:
                match = re.search(r'require\([\'"]([^\'"]+)[\'"]\)', imp)
                module = match.group(1) if match else ''
            
            if module.startswith('.'):
                internal.append(imp)
            elif module in ('fs', 'path', 'http', 'https', 'url', 'querystring', 'util', 'os', 'crypto', 'stream', 'events', 'buffer', 'process', 'child_process', 'cluster', 'dns', 'net', 'dgram', 'tls', 'zlib', 'string_decoder', 'punycode', 'readline', 'repl', 'vm', 'module', 'async_hooks', 'inspector', 'perf_hooks', 'trace_events', 'worker_threads', 'v8', 'timers', 'domain', 'constants'):
                builtin.append(imp)
            else:
                external.append(imp)
        
        # 排序
        builtin.sort()
        external.sort()
        internal.sort()
        
        # 组装
        new_imports = []
        if builtin:
            new_imports.extend(builtin)
        if external:
            if new_imports:
                new_imports.append('')
            new_imports.extend(external)
        if internal:
            if new_imports:
                new_imports.append('')
            new_imports.extend(internal)
        
        # 重建内容
        result = new_imports + [''] + other_lines
        return '\n'.join(result)
    
    def extract_function(self, content: str, start_line: int, end_line: int, name: str) -> str:
        """提取选中代码为新函数"""
        lines = content.split('\n')
        
        # 提取选中代码
        selected = '\n'.join(lines[start_line - 1:end_line])
        
        # 计算缩进
        base_indent = len(lines[start_line - 1]) - len(lines[start_line - 1].lstrip())
        indent_str = ' ' * base_indent
        
        # 创建新函数
        inner_content = '\n'.join(line[base_indent:] if line.strip() else line 
                                  for line in lines[start_line - 1:end_line])
        new_func = f"{indent_str}function {name}() {{\n{inner_content}\n{indent_str}}}"
        
        # 替换原代码
        new_lines = lines[:start_line - 1] + [new_func] + lines[end_line:]
        
        return '\n'.join(new_lines)
    
    def rename_symbol(self, content: str, old_name: str, new_name: str) -> str:
        """重命名符号"""
        # 使用正则表达式匹配单词边界
        pattern = r'\b' + re.escape(old_name) + r'\b'
        return re.sub(pattern, new_name, content)
    
    def _refactor_organize_imports(self, parse_result: ParseResult, params: Dict) -> RefactorResult:
        """整理导入重构"""
        content = params.get('content', '')
        
        if not content:
            return RefactorResult(
                file_path=parse_result.file_path,
                language=LanguageType.JAVASCRIPT,
                success=False,
                changes=[]
            )
        
        new_content = self.organize_imports(content)
        
        return RefactorResult(
            file_path=parse_result.file_path,
            language=LanguageType.JAVASCRIPT,
            success=True,
            changes=[{
                'type': 'organize_imports',
                'description': 'Organized import statements'
            }],
            original_content=content,
            new_content=new_content
        )
    
    def _refactor_remove_unused_imports(self, parse_result: ParseResult, params: Dict) -> RefactorResult:
        """移除未使用的导入"""
        unused = params.get('unused_imports', [])
        content = params.get('content', '')
        
        if not unused or not content:
            return RefactorResult(
                file_path=parse_result.file_path,
                language=LanguageType.JAVASCRIPT,
                success=False,
                changes=[]
            )
        
        lines = content.split('\n')
        new_lines = []
        
        for line in lines:
            is_unused = False
            
            # 检查是否是未使用的导入
            if line.strip().startswith('import ') or 'require(' in line:
                for imp in unused:
                    if imp in line:
                        is_unused = True
                        break
            
            if not is_unused:
                new_lines.append(line)
        
        new_content = '\n'.join(new_lines)
        
        return RefactorResult(
            file_path=parse_result.file_path,
            language=LanguageType.JAVASCRIPT,
            success=True,
            changes=[{
                'type': 'remove_unused_imports',
                'removed': unused
            }],
            original_content=content,
            new_content=new_content
        )
    
    def _refactor_convert_var(self, parse_result: ParseResult, params: Dict) -> RefactorResult:
        """将var转换为const/let"""
        content = params.get('content', '')
        
        if not content:
            return RefactorResult(
                file_path=parse_result.file_path,
                language=LanguageType.JAVASCRIPT,
                success=False,
                changes=[]
            )
        
        # 简单替换：所有var -> const
        # 实际应该分析变量是否被重新赋值
        new_content = re.sub(r'\bvar\b', 'const', content)
        
        changes_count = content.count('var ') - new_content.count('var ')
        
        return RefactorResult(
            file_path=parse_result.file_path,
            language=LanguageType.JAVASCRIPT,
            success=True,
            changes=[{
                'type': 'convert_var_to_const',
                'count': changes_count
            }],
            original_content=content,
            new_content=new_content
        )
    
    def _refactor_remove_console_logs(self, parse_result: ParseResult, params: Dict) -> RefactorResult:
        """移除console.log"""
        content = params.get('content', '')
        
        if not content:
            return RefactorResult(
                file_path=parse_result.file_path,
                language=LanguageType.JAVASCRIPT,
                success=False,
                changes=[]
            )
        
        lines = content.split('\n')
        new_lines = []
        removed_count = 0
        
        for line in lines:
            if 'console.log' in line:
                removed_count += 1
            else:
                new_lines.append(line)
        
        new_content = '\n'.join(new_lines)
        
        return RefactorResult(
            file_path=parse_result.file_path,
            language=LanguageType.JAVASCRIPT,
            success=True,
            changes=[{
                'type': 'remove_console_logs',
                'count': removed_count
            }],
            original_content=content,
            new_content=new_content
        )


__all__ = ['JavaScriptRefactorer']
