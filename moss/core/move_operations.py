#!/usr/bin/env python3
"""
MOSS v9.2 - Move Operations
函数/类移动操作 - 实际执行跨文件代码移动

Author: MOSS v9.2
Date: 2026-04-23
"""

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from moss.core.cross_file_refactor import (
    CrossFileRefactorEngine, CodeChange, ImportInfo, ModuleInfo,
    OperationType, RefactoringOperation, RefactoringResult, SymbolInfo, SymbolKind,
    TransactionManager
)


class SourceExtractor:
    """从源文件中提取函数/类的源代码"""

    def extract_symbol_source(self, file_path: str, symbol_name: str) -> Optional[str]:
        """提取符号的完整源代码"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return None

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return None

        lines = content.split('\n')

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name == symbol_name:
                    # 提取源代码（包含装饰器）
                    start = node.lineno
                    # 检查装饰器
                    if node.decorator_list:
                        start = min(d.lineno for d in node.decorator_list)
                    end = node.end_lineno or node.lineno

                    source = '\n'.join(lines[start - 1:end])

                    # 提取相关导入
                    needed_imports = self._extract_needed_imports(source, tree, lines)

                    return needed_imports + '\n\n' + source

        return None

    def _extract_needed_imports(self, symbol_source: str, tree: ast.AST,
                                 lines: List[str]) -> str:
        """提取符号需要的导入语句"""
        try:
            symbol_tree = ast.parse(symbol_source)
        except SyntaxError:
            return ""

        # 收集符号中使用的名称
        used_names = set()
        for node in ast.walk(symbol_tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                used_names.add(node.value.id)

        # 内置名称不需要导入
        builtins = {'print', 'len', 'range', 'str', 'int', 'float', 'list', 'dict',
                    'set', 'tuple', 'bool', 'None', 'True', 'False', 'type', 'isinstance',
                    'enumerate', 'zip', 'map', 'filter', 'sorted', 'super', 'property',
                    'staticmethod', 'classmethod', 'Exception', 'ValueError', 'TypeError',
                    'KeyError', 'IndexError', 'AttributeError', 'RuntimeError', 'any',
                    'all', 'abs', 'max', 'min', 'sum', 'round', 'hash', 'id', 'format',
                    'repr', 'bytes', 'hasattr', 'getattr', 'setattr', 'NotImplementedError',
                    'Optional', 'List', 'Dict', 'Set', 'Tuple', 'Union', 'Any',
                    'Callable', 'Iterable', 'Iterator', 'Generator', 'overload',
                    }

        # 从原始文件中找到匹配的导入
        needed_imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for alias in node.names:
                    name = alias.asname or alias.name
                    if name in used_names and name not in builtins:
                        needed_imports.append(
                            f"from {node.module} import {alias.name}"
                            + (f" as {alias.asname}" if alias.asname else "")
                        )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split('.')[0]
                    if name in used_names and name not in builtins:
                        needed_imports.append(
                            f"import {alias.name}"
                            + (f" as {alias.asname}" if alias.asname else "")
                        )

        return '\n'.join(needed_imports)

    def remove_symbol_from_source(self, file_path: str, symbol_name: str) -> Optional[str]:
        """从源文件中移除符号，返回修改后的内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return None

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return None

        lines = content.split('\n')

        # 找到符号位置
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name == symbol_name:
                    start = node.lineno
                    if node.decorator_list:
                        start = min(d.lineno for d in node.decorator_list)
                    end = node.end_lineno or node.lineno

                    # 移除行
                    new_lines = lines[:start - 1] + lines[end:]

                    # 清理多余空行
                    result = '\n'.join(new_lines)
                    result = re.sub(r'\n{3,}', '\n\n', result)

                    return result.strip() + '\n'

        return None

    def add_import_to_file(self, file_path: str, module_name: str,
                           symbol_name: str, is_from_import: bool = True) -> Optional[str]:
        """在文件中添加导入语句"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return None

        # 检查是否已有此导入
        if symbol_name in content and f'from {module_name} import' in content:
            return content  # 已存在

        # 找到合适的插入位置（在现有导入之后）
        lines = content.split('\n')
        last_import_line = 0

        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    last_import_line = max(last_import_line, node.end_lineno or node.lineno)
        except SyntaxError:
            last_import_line = 0

        # 构建新导入
        if is_from_import:
            new_import = f"from {module_name} import {symbol_name}"
        else:
            new_import = f"import {module_name}"

        # 插入
        if last_import_line > 0:
            lines.insert(last_import_line, new_import)
        else:
            # 文件开头
            lines.insert(0, new_import)

        return '\n'.join(lines)

    def update_import_in_file(self, file_path: str, old_module: str,
                              new_module: str, symbol_name: str) -> Optional[str]:
        """更新文件中的导入语句"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return None

        # 替换 from old_module import symbol → from new_module import symbol
        old_pattern = f"from {old_module} import"
        new_pattern = f"from {new_module} import"

        # 逐行处理
        lines = content.split('\n')
        updated = False
        new_lines = []

        for line in lines:
            if old_pattern in line and symbol_name in line:
                # 简单替换模块名
                new_line = line.replace(old_pattern, new_pattern)
                new_lines.append(new_line)
                updated = True
            else:
                new_lines.append(line)

        if updated:
            return '\n'.join(new_lines)

        # 如果没有找到 from import，尝试添加
        return self.add_import_to_file(file_path, new_module, symbol_name)

    def remove_import_from_file(self, file_path: str, module_name: str,
                                symbol_name: str) -> Optional[str]:
        """移除文件中不再需要的导入"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return None

        lines = content.split('\n')
        new_lines = []

        for line in lines:
            stripped = line.strip()
            # 检查是否是从指定模块导入指定符号
            if (f'from {module_name} import' in stripped and symbol_name in stripped):
                # 如果只导入了这一个符号，删除整行
                import_match = re.match(
                    r'from\s+' + re.escape(module_name) + r'\s+import\s+(.*)',
                    stripped
                )
                if import_match:
                    imported = [s.strip() for s in import_match.group(1).split(',')]
                    if len(imported) == 1 and imported[0] == symbol_name:
                        continue  # 跳过此行
                    elif symbol_name in imported:
                        # 移除其中一个导入
                        imported.remove(symbol_name)
                        indent = len(line) - len(line.lstrip())
                        new_lines.append(' ' * indent + f"from {module_name} import {', '.join(imported)}")
                        continue
            new_lines.append(line)

        return '\n'.join(new_lines)


class MoveExecutor:
    """
    移动操作执行器

    完整的函数/类移动流程:
    1. 提取源码 + 依赖导入
    2. 从源模块移除
    3. 添加到目标模块
    4. 更新所有引用的导入
    5. 验证语法
    """

    def __init__(self, engine: CrossFileRefactorEngine):
        self.engine = engine
        self.extractor = SourceExtractor()
        self.transaction = TransactionManager()

    async def move_function(
        self,
        function_name: str,
        source_module: str,
        target_module: str,
        dry_run: bool = False
    ) -> RefactoringResult:
        """
        移动函数到另一个模块

        完整流程:
        1. 提取函数源码 + 依赖导入
        2. 从源文件删除函数
        3. 添加函数到目标文件
        4. 在源文件添加 from target import func
        5. 更新所有外部引用
        """
        print(f"\n[MoveExecutor] 移动函数: {function_name}")
        print(f"  {source_module} → {target_module}")

        # 验证模块存在
        src_info = self.engine.graph_builder.modules.get(source_module)
        tgt_info = self.engine.graph_builder.modules.get(target_module)

        if not src_info:
            return RefactoringResult(success=False, message=f"源模块不存在: {source_module}")
        if not tgt_info:
            return RefactoringResult(success=False, message=f"目标模块不存在: {target_module}")

        # 验证函数存在
        symbol = self.engine.symbol_tracker.find_symbol_definition(function_name)
        if not symbol or symbol.defined_in != source_module:
            return RefactoringResult(success=False, message=f"函数 {function_name} 不在 {source_module} 中")

        # 1. 提取源码
        extracted = self.extractor.extract_symbol_source(src_info.path, function_name)
        if not extracted:
            return RefactoringResult(success=False, message=f"无法提取函数源码")

        if dry_run:
            preview_lines = extracted.split('\n')[:8]
            preview = '\n'.join(f"    {l}" for l in preview_lines)
            return RefactoringResult(
                success=True,
                message=f"[预览] 将移动 {function_name} ({len(extracted.split(chr(10)))} 行)\n{preview}...",
                files_modified=[src_info.path, tgt_info.path],
                rollback_available=False
            )

        # 2. 影响分析
        impact = self.engine.impact_analyzer.analyze_move_impact(
            function_name, source_module, target_module
        )
        print(f"  影响文件: {len(impact.affected_files)}, 风险: {impact.risk_level}")

        # 3. 开始事务
        self.transaction.begin()

        # 4. 从源文件移除函数
        new_source = self.extractor.remove_symbol_from_source(src_info.path, function_name)
        if new_source is not None:
            Path(src_info.path).write_text(new_source, encoding='utf-8')
            print(f"  ✅ 从源文件移除 {function_name}")

        # 5. 添加到目标文件
        with open(tgt_info.path, 'r', encoding='utf-8') as f:
            target_content = f.read()

        # 在文件末尾添加
        new_target = target_content.rstrip() + '\n\n' + extracted + '\n'
        Path(tgt_info.path).write_text(new_target, encoding='utf-8')
        print(f"  ✅ 添加 {function_name} 到目标文件")

        # 6. 在源文件添加 from target import func
        updated_source = self.extractor.add_import_to_file(
            src_info.path, target_module, function_name
        )
        if updated_source:
            Path(src_info.path).write_text(updated_source, encoding='utf-8')
            print(f"  ✅ 更新源文件导入")

        # 7. 更新所有外部引用的导入
        for imp_update in impact.affected_imports:
            parts = imp_update.split(':')
            if len(parts) >= 2:
                module_name = parts[0]
                mod_info = self.engine.graph_builder.modules.get(module_name)
                if mod_info:
                    updated = self.extractor.update_import_in_file(
                        mod_info.path, source_module, target_module, function_name
                    )
                    if updated:
                        Path(mod_info.path).write_text(updated, encoding='utf-8')
                        print(f"  ✅ 更新 {module_name} 的导入")

        # 8. 验证所有修改文件的语法
        modified_files = [src_info.path, tgt_info.path]
        for f in impact.affected_files:
            if f not in modified_files:
                modified_files.append(f)

        all_valid = True
        for file_path in modified_files:
            try:
                with open(file_path, 'r') as f:
                    ast.parse(f.read())
            except (SyntaxError, FileNotFoundError):
                all_valid = False
                print(f"  ❌ 语法验证失败: {file_path}")
                break

        if not all_valid:
            # 回滚
            self.transaction.rollback()
            return RefactoringResult(
                success=False,
                message="语法验证失败，已回滚所有变更"
            )

        # 9. 提交
        committed = self.transaction.commit()

        return RefactoringResult(
            success=True,
            operations_applied=committed,
            files_modified=modified_files,
            rollback_available=True,
            message=f"成功移动 {function_name}: {source_module} → {target_module} "
                    f"({len(modified_files)} 个文件)"
        )

    async def move_class(
        self,
        class_name: str,
        source_module: str,
        target_module: str,
        dry_run: bool = False
    ) -> RefactoringResult:
        """移动类到另一个模块（复用函数移动逻辑）"""
        # 类移动与函数移动逻辑相同
        return await self.move_function(class_name, source_module, target_module, dry_run)
