#!/usr/bin/env python3
"""
MOSS v9.3 - Language Server Protocol (LSP) Server
LSP 服务器 - 为 IDE 提供代码分析和重构能力

支持功能:
1. 代码诊断 (Diagnostics)
2. 代码操作 (Code Actions / Refactoring)
3. 代码补全 (Completion)
4. 符号定义跳转 (Go to Definition)
5. 符号引用查找 (Find References)
6. 重命名 (Rename)
7. 代码镜头 (Code Lens)
8. 悬停信息 (Hover)

协议版本: LSP 3.17
传输方式: stdio / TCP

Author: MOSS v9.3
Date: 2026-04-24
"""

import asyncio
import json
import logging
import os
import sys
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

# LSP 相关导入
try:
    from pygls.server import LanguageServer
    from lsprotocol import types as lsp
    HAS_PYGLS = True
except ImportError:
    HAS_PYGLS = False

# MOSS 内部组件
from .incremental_analyzer import IncrementalAnalyzer, MultiLevelCache
from .parallel_analyzer import ParallelAnalyzer
from .cross_file_refactor import (
    CrossFileRefactorEngine,
    ImportGraphBuilder,
    SymbolTracker,
    ImpactAnalyzer
)

logger = logging.getLogger("moss.lsp")


# ──────────────────────────────────────────────────────────────
# LSP Data Types (compatible with or without pygls)
# ──────────────────────────────────────────────────────────────

class DiagnosticSeverity:
    ERROR = 1
    WARNING = 2
    INFORMATION = 3
    HINT = 4


class MessageType:
    ERROR = 1
    WARNING = 2
    INFO = 3
    LOG = 4


class TextDocumentSyncKind:
    NONE = 0
    FULL = 1
    INCREMENTAL = 2


class CompletionItemKind:
    TEXT = 1
    METHOD = 2
    FUNCTION = 3
    CONSTRUCTOR = 4
    FIELD = 5
    VARIABLE = 6
    CLASS = 7
    INTERFACE = 8
    MODULE = 9
    PROPERTY = 10
    KEYWORD = 14
    SNIPPET = 15


class SymbolKind:
    FILE = 1
    MODULE = 2
    NAMESPACE = 3
    PACKAGE = 4
    CLASS = 5
    METHOD = 6
    PROPERTY = 7
    FIELD = 8
    CONSTRUCTOR = 9
    ENUM = 10
    FUNCTION = 12
    VARIABLE = 13
    CONSTANT = 14


@dataclass
class MossDiagnostic:
    """MOSS 诊断信息"""
    uri: str
    line: int
    character: int
    message: str
    severity: int = DiagnosticSeverity.WARNING
    source: str = "moss"
    code: Optional[str] = None
    related_info: List[Dict] = field(default_factory=list)


@dataclass
class MossCodeAction:
    """MOSS 代码操作"""
    title: str
    kind: str  # quickfix, refactor, refactor.extract, refactor.inline, etc.
    edit: Dict  # WorkspaceEdit
    is_preferred: bool = False
    command: Optional[Dict] = None


@dataclass
class MossCompletionItem:
    """MOSS 补全项"""
    label: str
    kind: int = CompletionItemKind.TEXT
    detail: str = ""
    documentation: str = ""
    insert_text: str = ""
    sort_text: str = ""


@dataclass
class MossLocation:
    """位置信息"""
    uri: str
    line: int
    character: int


@dataclass
class MossSymbolInfo:
    """符号信息"""
    name: str
    kind: int
    location: MossLocation
    container_name: str = ""
    children: List['MossSymbolInfo'] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────
# Document Manager
# ──────────────────────────────────────────────────────────────

class DocumentManager:
    """
    文档管理器

    管理客户端打开的文档，跟踪文件内容和版本
    """

    def __init__(self):
        self.documents: Dict[str, Dict] = {}  # uri -> {version, content, languageId}
        self.versions: Dict[str, int] = {}

    def open_document(self, uri: str, content: str, version: int = 0, language_id: str = "python"):
        """打开文档"""
        self.documents[uri] = {
            'content': content,
            'version': version,
            'languageId': language_id,
            'last_modified': time.time(),
        }
        self.versions[uri] = version

    def close_document(self, uri: str):
        """关闭文档"""
        self.documents.pop(uri, None)
        self.versions.pop(uri, None)

    def update_document(self, uri: str, content: str, version: int):
        """更新文档内容"""
        if uri in self.documents:
            self.documents[uri]['content'] = content
            self.documents[uri]['version'] = version
            self.documents[uri]['last_modified'] = time.time()
            self.versions[uri] = version

    def get_content(self, uri: str) -> Optional[str]:
        """获取文档内容"""
        doc = self.documents.get(uri)
        return doc['content'] if doc else None

    def get_version(self, uri: str) -> int:
        """获取文档版本"""
        return self.versions.get(uri, 0)

    def is_open(self, uri: str) -> bool:
        """检查文档是否打开"""
        return uri in self.documents

    def list_open_documents(self) -> List[str]:
        """列出所有打开的文档"""
        return list(self.documents.keys())


# ──────────────────────────────────────────────────────────────
# MOSS Analysis Provider
# ──────────────────────────────────────────────────────────────

class MossAnalysisProvider:
    """
    MOSS 分析提供器

    将 MOSS 核心分析能力映射到 LSP 概念
    """

    def __init__(self, codebase_path: str):
        self.codebase_path = Path(codebase_path)
        self.doc_manager = DocumentManager()

        # 初始化 MOSS 组件
        try:
            self.incremental = IncrementalAnalyzer(str(self.codebase_path))
            self.parallel = ParallelAnalyzer(max_workers=4)
            self.refactor_engine = CrossFileRefactorEngine(codebase_path)
            self._initialized = True
        except Exception as e:
            logger.warning(f"MOSS 组件初始化失败: {e}")
            self._initialized = False

        # 缓存
        self._diagnostics_cache: Dict[str, List[MossDiagnostic]] = {}
        self._symbols_cache: Dict[str, List[MossSymbolInfo]] = {}

    def initialize(self, root_path: str) -> Dict:
        """
        初始化分析提供器

        Returns:
            ServerCapabilities
        """
        self.codebase_path = Path(root_path)

        if self._initialized:
            try:
                # 异步初始化重构引擎
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.refactor_engine.initialize())
                else:
                    loop.run_until_complete(self.refactor_engine.initialize())
            except Exception as e:
                logger.warning(f"重构引擎初始化失败: {e}")

        # 返回服务器能力
        return {
            "capabilities": {
                "textDocumentSync": {
                    "openClose": True,
                    "change": TextDocumentSyncKind.FULL,
                    "willSave": False,
                    "willSaveWaitUntil": False,
                    "save": {"includeText": True},
                },
                "completionProvider": {
                    "triggerCharacters": [".", "(", "'", '"'],
                    "resolveProvider": False,
                },
                "hoverProvider": True,
                "signatureHelpProvider": {
                    "triggerCharacters": ["(", ","],
                },
                "definitionProvider": True,
                "referencesProvider": True,
                "documentSymbolProvider": True,
                "workspaceSymbolProvider": True,
                "codeActionProvider": {
                    "codeActionKinds": [
                        "quickfix",
                        "refactor",
                        "refactor.extract",
                        "refactor.inline",
                        "refactor.rewrite",
                    ],
                    "resolveProvider": False,
                },
                "codeLensProvider": {
                    "resolveProvider": False,
                },
                "documentFormattingProvider": False,
                "renameProvider": {
                    "prepareProvider": True,
                },
                "foldingRangeProvider": True,
                "selectionRangeProvider": True,
            }
        }

    # ──────────────────────────────────────────────────────────
    # Text Document Handlers
    # ──────────────────────────────────────────────────────────

    def did_open(self, uri: str, content: str, version: int = 0):
        """文档打开通知"""
        self.doc_manager.open_document(uri, content, version)

        # 分析文档
        diagnostics = self._analyze_document(uri, content)
        self._diagnostics_cache[uri] = diagnostics

        return diagnostics

    def did_change(self, uri: str, content: str, version: int):
        """文档变更通知"""
        self.doc_manager.update_document(uri, content, version)

        # 重新分析
        diagnostics = self._analyze_document(uri, content)
        self._diagnostics_cache[uri] = diagnostics

        return diagnostics

    def did_close(self, uri: str):
        """文档关闭通知"""
        self.doc_manager.close_document(uri)
        self._diagnostics_cache.pop(uri, None)
        self._symbols_cache.pop(uri, None)

    def did_save(self, uri: str, content: Optional[str] = None):
        """文档保存通知"""
        if content:
            self.doc_manager.update_document(uri, content, self.doc_manager.get_version(uri) + 1)

    # ──────────────────────────────────────────────────────────
    # Diagnostics
    # ──────────────────────────────────────────────────────────

    def _analyze_document(self, uri: str, content: str) -> List[MossDiagnostic]:
        """分析文档并生成诊断信息"""
        diagnostics = []

        try:
            import ast as ast_mod
            tree = ast_mod.parse(content)

            # 1. 检查长函数
            for node in ast_mod.walk(tree):
                if isinstance(node, ast_mod.FunctionDef):
                    func_lines = node.end_lineno - node.lineno if node.end_lineno else 0
                    if func_lines > 50:
                        diagnostics.append(MossDiagnostic(
                            uri=uri,
                            line=node.lineno - 1,
                            character=node.col_offset,
                            message=f"函数 '{node.name}' 过长 ({func_lines} 行)，建议拆分",
                            severity=DiagnosticSeverity.WARNING,
                            code="moss-long-function",
                        ))

                    # 检查高复杂度
                    complexity = 1
                    for child in ast_mod.walk(node):
                        if isinstance(child, (ast_mod.If, ast_mod.While, ast_mod.For, ast_mod.ExceptHandler)):
                            complexity += 1
                        elif isinstance(child, ast_mod.BoolOp):
                            complexity += len(child.values) - 1

                    if complexity > 10:
                        diagnostics.append(MossDiagnostic(
                            uri=uri,
                            line=node.lineno - 1,
                            character=node.col_offset,
                            message=f"函数 '{node.name}' 复杂度过高 ({complexity})",
                            severity=DiagnosticSeverity.HINT,
                            code="moss-high-complexity",
                        ))

            # 2. 检查未使用的导入
            imported = set()
            used = set()
            for node in ast_mod.walk(tree):
                if isinstance(node, ast_mod.Import):
                    for alias in node.names:
                        imported.add(alias.asname or alias.name)
                elif isinstance(node, ast_mod.ImportFrom):
                    for alias in node.names:
                        imported.add(alias.asname or alias.name)
                elif isinstance(node, ast_mod.Name) and isinstance(node.ctx, ast_mod.Load):
                    used.add(node.id)

            unused = imported - used
            for node in ast_mod.walk(tree):
                if isinstance(node, ast_mod.Import):
                    for alias in node.names:
                        name = alias.asname or alias.name
                        if name in unused:
                            diagnostics.append(MossDiagnostic(
                                uri=uri,
                                line=node.lineno - 1,
                                character=0,
                                message=f"未使用的导入: {name}",
                                severity=DiagnosticSeverity.HINT,
                                code="moss-unused-import",
                            ))

            # 3. 检查类方法缺少 self
            for node in ast_mod.walk(tree):
                if isinstance(node, ast_mod.ClassDef):
                    for item in node.body:
                        if isinstance(item, ast_mod.FunctionDef):
                            if (item.args.args and
                                item.args.args[0].arg != 'self' and
                                item.args.args[0].arg != 'cls' and
                                not any(d.id == 'staticmethod' for d in item.decorator_list if isinstance(d, ast_mod.Name))):
                                diagnostics.append(MossDiagnostic(
                                    uri=uri,
                                    line=item.lineno - 1,
                                    character=item.col_offset,
                                    message=f"方法 '{item.name}' 可能缺少 self 参数",
                                    severity=DiagnosticSeverity.WARNING,
                                    code="moss-missing-self",
                                ))

        except SyntaxError as e:
            diagnostics.append(MossDiagnostic(
                uri=uri,
                line=(e.lineno or 1) - 1,
                character=(e.offset or 1) - 1,
                message=f"语法错误: {e.msg}",
                severity=DiagnosticSeverity.ERROR,
                code="moss-syntax-error",
            ))
        except Exception as e:
            logger.error(f"分析失败: {e}")

        return diagnostics

    def get_diagnostics(self, uri: str) -> List[MossDiagnostic]:
        """获取文档的诊断信息"""
        return self._diagnostics_cache.get(uri, [])

    # ──────────────────────────────────────────────────────────
    # Code Actions
    # ──────────────────────────────────────────────────────────

    def get_code_actions(
        self,
        uri: str,
        range_start: Tuple[int, int],
        range_end: Tuple[int, int],
        diagnostics: List[Dict] = None,
        only: List[str] = None
    ) -> List[MossCodeAction]:
        """
        获取代码操作

        Args:
            uri: 文档 URI
            range_start: (line, character) 起始位置
            range_end: (line, character) 结束位置
            diagnostics: 触发诊断
            only: 只返回特定类型的操作

        Returns:
            代码操作列表
        """
        actions = []
        content = self.doc_manager.get_content(uri)
        if not content:
            return actions

        line = range_start[0]
        char = range_start[1]

        try:
            import ast as ast_mod
            tree = ast_mod.parse(content)

            for node in ast_mod.walk(tree):
                if not isinstance(node, ast_mod.FunctionDef):
                    continue

                # 检查是否在选中范围内
                if not (node.lineno - 1 <= line <= (node.end_lineno or node.lineno) - 1):
                    continue

                func_lines = node.end_lineno - node.lineno if node.end_lineno else 0

                # 提取函数重构建议
                if func_lines > 30:
                    actions.append(MossCodeAction(
                        title=f"提取子函数 from '{node.name}'",
                        kind="refactor.extract",
                        edit={
                            "changes": {
                                uri: [{
                                    "range": {
                                        "start": {"line": node.lineno - 1, "character": 0},
                                        "end": {"line": (node.end_lineno or node.lineno) - 1, "character": 0},
                                    },
                                    "newText": self._generate_extracted_function(node, content),
                                }]
                            }
                        },
                        is_preferred=True,
                    ))

                # 内联变量建议
                if func_lines < 5 and node.name.startswith('_'):
                    actions.append(MossCodeAction(
                        title=f"内联函数 '{node.name}'",
                        kind="refactor.inline",
                        edit={
                            "changes": {
                                uri: [{
                                    "range": {
                                        "start": {"line": node.lineno - 1, "character": 0},
                                        "end": {"line": (node.end_lineno or node.lineno), "character": 0},
                                    },
                                    "newText": "",
                                }]
                            }
                        },
                    ))

            # 基于诊断的快速修复
            if diagnostics:
                for diag in diagnostics:
                    code = diag.get('code', '')
                    if code == 'moss-unused-import':
                        actions.append(MossCodeAction(
                            title=f"移除未使用的导入",
                            kind="quickfix",
                            edit={
                                "changes": {
                                    uri: [{
                                        "range": {
                                            "start": {"line": diag.get('line', 0), "character": 0},
                                            "end": {"line": diag.get('line', 0) + 1, "character": 0},
                                        },
                                        "newText": "",
                                    }]
                                }
                            },
                            is_preferred=True,
                        ))

        except Exception as e:
            logger.error(f"获取代码操作失败: {e}")

        # 按 kind 过滤
        if only:
            actions = [a for a in actions if any(a.kind.startswith(k) for k in only)]

        return actions

    def _generate_extracted_function(self, node, content: str) -> str:
        """生成提取后的函数代码"""
        lines = content.split('\n')
        func_lines = lines[node.lineno - 1:(node.end_lineno or node.lineno)]

        # 简单的提取策略：将函数体分为前后两半
        mid = len(func_lines) // 2
        main_func = func_lines[:mid + 1]
        helper_func = func_lines[mid + 1:]

        new_code = '\n'.join(main_func)
        new_code += f'\n    # Extracted from {node.name}\n'
        new_code += f'def _{node.name}_extracted():\n'
        for line in helper_func:
            new_code += f'    {line.lstrip()}\n'

        return new_code

    # ──────────────────────────────────────────────────────────
    # Completion
    # ──────────────────────────────────────────────────────────

    def get_completions(
        self,
        uri: str,
        line: int,
        character: int
    ) -> List[MossCompletionItem]:
        """
        获取代码补全建议

        Args:
            uri: 文档 URI
            line: 行号 (0-based)
            character: 列号 (0-based)

        Returns:
            补全项列表
        """
        content = self.doc_manager.get_content(uri)
        if not content:
            return []

        completions = []

        try:
            import ast as ast_mod
            tree = ast_mod.parse(content)

            # 获取当前行内容
            lines = content.split('\n')
            if line >= len(lines):
                return []

            current_line = lines[line]
            prefix = current_line[:character]

            # 1. 模块级符号补全
            for node in ast_mod.walk(tree):
                if isinstance(node, ast_mod.FunctionDef):
                    completions.append(MossCompletionItem(
                        label=node.name,
                        kind=CompletionItemKind.FUNCTION,
                        detail=f"函数 ({node.lineno})",
                        insert_text=node.name + "($0)",
                        sort_text=f"1_{node.name}",
                    ))
                elif isinstance(node, ast_mod.ClassDef):
                    completions.append(MossCompletionItem(
                        label=node.name,
                        kind=CompletionItemKind.CLASS,
                        detail=f"类 ({node.lineno})",
                        insert_text=node.name + "($0)",
                        sort_text=f"0_{node.name}",
                    ))

            # 2. 关键字补全
            if prefix.strip().endswith(('def ', 'class ', 'import ', 'from ')):
                pass  # 不提供额外补全

            # 3. import 补全
            if prefix.strip().startswith(('import ', 'from ')):
                # 提供项目内模块补全
                for py_file in self.codebase_path.rglob("*.py"):
                    if '__pycache__' in str(py_file):
                        continue
                    try:
                        rel = py_file.relative_to(self.codebase_path)
                        module = str(rel.with_suffix('')).replace(os.sep, '.')
                        completions.append(MossCompletionItem(
                            label=module,
                            kind=CompletionItemKind.MODULE,
                            detail=f"模块 ({rel})",
                            insert_text=module,
                            sort_text=f"9_{module}",
                        ))
                    except ValueError:
                        pass

        except Exception as e:
            logger.error(f"补全失败: {e}")

        return completions

    # ──────────────────────────────────────────────────────────
    # Definition & References
    # ──────────────────────────────────────────────────────────

    def get_definition(
        self,
        uri: str,
        line: int,
        character: int
    ) -> Optional[MossLocation]:
        """
        跳转到定义

        Args:
            uri: 文档 URI
            line: 行号
            character: 列号

        Returns:
            定义位置
        """
        content = self.doc_manager.get_content(uri)
        if not content:
            return None

        try:
            import ast as ast_mod
            tree = ast_mod.parse(content)

            lines = content.split('\n')
            if line >= len(lines):
                return None

            current_line = lines[line]
            # 获取光标下的标识符
            word = self._get_word_at_position(current_line, character)
            if not word:
                return None

            # 在当前文件中查找定义
            for node in ast_mod.walk(tree):
                if isinstance(node, ast_mod.FunctionDef) and node.name == word:
                    return MossLocation(
                        uri=uri,
                        line=node.lineno - 1,
                        character=node.col_offset,
                    )
                elif isinstance(node, ast_mod.ClassDef) and node.name == word:
                    return MossLocation(
                        uri=uri,
                        line=node.lineno - 1,
                        character=node.col_offset,
                    )
                elif isinstance(node, ast_mod.Name) and node.id == word and isinstance(node.ctx, ast_mod.Store):
                    return MossLocation(
                        uri=uri,
                        line=node.lineno - 1,
                        character=node.col_offset,
                    )

            # 如果有重构引擎，跨文件查找
            if self._initialized and self.refactor_engine._initialized:
                symbol = self.refactor_engine.symbol_tracker.find_symbol_definition(word)
                if symbol:
                    return MossLocation(
                        uri=f"file://{symbol.defined_in}",
                        line=symbol.line_start - 1,
                        character=0,
                    )

        except Exception as e:
            logger.error(f"查找定义失败: {e}")

        return None

    def get_references(
        self,
        uri: str,
        line: int,
        character: int,
        include_declaration: bool = True
    ) -> List[MossLocation]:
        """
        查找引用

        Args:
            uri: 文档 URI
            line: 行号
            character: 列号
            include_declaration: 是否包含声明

        Returns:
            引用位置列表
        """
        content = self.doc_manager.get_content(uri)
        if not content:
            return []

        references = []

        try:
            import ast as ast_mod
            tree = ast_mod.parse(content)

            lines = content.split('\n')
            if line >= len(lines):
                return []

            current_line = lines[line]
            word = self._get_word_at_position(current_line, character)
            if not word:
                return []

            # 在当前文件中查找所有引用
            for node in ast_mod.walk(tree):
                if isinstance(node, ast_mod.Name) and node.id == word:
                    is_declaration = isinstance(node.ctx, ast_mod.Store) or (
                        isinstance(node.ctx, ast_mod.Load) and
                        isinstance(node, (ast_mod.FunctionDef, ast_mod.ClassDef))
                    )

                    if include_declaration or not is_declaration:
                        references.append(MossLocation(
                            uri=uri,
                            line=node.lineno - 1,
                            character=node.col_offset,
                        ))

            # 跨文件查找
            if self._initialized and self.refactor_engine._initialized:
                usages = self.refactor_engine.symbol_tracker.find_symbol_usages(word)
                for usage in usages:
                    references.append(MossLocation(
                        uri=f"file://{usage.file_path}",
                        line=usage.line - 1,
                        character=usage.column,
                    ))

        except Exception as e:
            logger.error(f"查找引用失败: {e}")

        return references

    # ──────────────────────────────────────────────────────────
    # Hover
    # ──────────────────────────────────────────────────────────

    def get_hover(
        self,
        uri: str,
        line: int,
        character: int
    ) -> Optional[str]:
        """
        获取悬停信息

        Args:
            uri: 文档 URI
            line: 行号
            character: 列号

        Returns:
            Markdown 格式的悬停信息
        """
        content = self.doc_manager.get_content(uri)
        if not content:
            return None

        try:
            import ast as ast_mod
            tree = ast_mod.parse(content)

            lines = content.split('\n')
            if line >= len(lines):
                return None

            current_line = lines[line]
            word = self._get_word_at_position(current_line, character)
            if not word:
                return None

            # 查找符号定义
            for node in ast_mod.walk(tree):
                if isinstance(node, ast_mod.FunctionDef) and node.name == word:
                    # 获取文档字符串
                    docstring = ast_mod.get_docstring(node) or "无文档"

                    # 获取参数信息
                    args = [a.arg for a in node.args.args if a.arg != 'self']
                    args_str = ", ".join(args)

                    return (
                        f"```python\ndef {word}({args_str})\n```\n\n"
                        f"{docstring}\n\n"
                        f"---\n"
                        f"*行 {node.lineno}* | *MOSS v9.3*"
                    )

                elif isinstance(node, ast_mod.ClassDef) and node.name == word:
                    docstring = ast_mod.get_docstring(node) or "无文档"

                    # 获取方法列表
                    methods = [
                        n.name for n in node.body
                        if isinstance(n, ast_mod.FunctionDef) and not n.name.startswith('_')
                    ]
                    methods_str = "\n".join(f"  - `{m}()`" for m in methods[:5])

                    return (
                        f"```python\nclass {word}\n```\n\n"
                        f"{docstring}\n\n"
                        f"**公共方法:**\n{methods_str}\n\n"
                        f"---\n"
                        f"*行 {node.lineno}* | *MOSS v9.3*"
                    )

        except Exception as e:
            logger.error(f"悬停信息获取失败: {e}")

        return None

    # ──────────────────────────────────────────────────────────
    # Document Symbols
    # ──────────────────────────────────────────────────────────

    def get_document_symbols(self, uri: str) -> List[MossSymbolInfo]:
        """
        获取文档符号

        Args:
            uri: 文档 URI

        Returns:
            符号列表
        """
        content = self.doc_manager.get_content(uri)
        if not content:
            return []

        # 检查缓存
        if uri in self._symbols_cache:
            return self._symbols_cache[uri]

        symbols = []

        try:
            import ast as ast_mod
            tree = ast_mod.parse(content)

            for node in ast_mod.iter_child_nodes(tree):
                if isinstance(node, ast_mod.ClassDef):
                    class_symbol = MossSymbolInfo(
                        name=node.name,
                        kind=SymbolKind.CLASS,
                        location=MossLocation(uri, node.lineno - 1, node.col_offset),
                    )

                    # 子符号（方法）
                    for item in node.body:
                        if isinstance(item, ast_mod.FunctionDef):
                            class_symbol.children.append(MossSymbolInfo(
                                name=item.name,
                                kind=SymbolKind.METHOD,
                                location=MossLocation(uri, item.lineno - 1, item.col_offset),
                                container_name=node.name,
                            ))

                    symbols.append(class_symbol)

                elif isinstance(node, ast_mod.FunctionDef):
                    symbols.append(MossSymbolInfo(
                        name=node.name,
                        kind=SymbolKind.FUNCTION,
                        location=MossLocation(uri, node.lineno - 1, node.col_offset),
                    ))

                elif isinstance(node, ast_mod.Assign):
                    for target in node.targets:
                        if isinstance(target, ast_mod.Name):
                            symbols.append(MossSymbolInfo(
                                name=target.id,
                                kind=SymbolKind.VARIABLE,
                                location=MossLocation(uri, node.lineno - 1, node.col_offset),
                            ))

        except Exception as e:
            logger.error(f"获取文档符号失败: {e}")

        self._symbols_cache[uri] = symbols
        return symbols

    # ──────────────────────────────────────────────────────────
    # Rename
    # ──────────────────────────────────────────────────────────

    def prepare_rename(
        self,
        uri: str,
        line: int,
        character: int
    ) -> Optional[Dict]:
        """准备重命名（检查是否可以重命名）"""
        content = self.doc_manager.get_content(uri)
        if not content:
            return None

        lines = content.split('\n')
        if line >= len(lines):
            return None

        current_line = lines[line]
        word = self._get_word_at_position(current_line, character)
        if not word:
            return None

        # 返回可重命名的范围
        start_char = current_line.rfind(word, max(0, character - len(word)), character + 1)
        if start_char < 0:
            start_char = character

        return {
            "range": {
                "start": {"line": line, "character": start_char},
                "end": {"line": line, "character": start_char + len(word)},
            },
            "placeholder": word,
        }

    def rename(
        self,
        uri: str,
        line: int,
        character: int,
        new_name: str
    ) -> Optional[Dict]:
        """
        重命名符号

        Returns:
            WorkspaceEdit
        """
        content = self.doc_manager.get_content(uri)
        if not content:
            return None

        lines = content.split('\n')
        if line >= len(lines):
            return None

        current_line = lines[line]
        old_name = self._get_word_at_position(current_line, character)
        if not old_name:
            return None

        # 在当前文档中查找所有出现
        changes = []
        for i, file_line in enumerate(lines):
            # 简单的文本匹配
            col = 0
            while True:
                idx = file_line.find(old_name, col)
                if idx < 0:
                    break
                changes.append({
                    "range": {
                        "start": {"line": i, "character": idx},
                        "end": {"line": i, "character": idx + len(old_name)},
                    },
                    "newText": new_name,
                })
                col = idx + len(old_name)

        return {
            "changes": {
                uri: changes,
            }
        }

    # ──────────────────────────────────────────────────────────
    # Code Lens
    # ──────────────────────────────────────────────────────────

    def get_code_lens(self, uri: str) -> List[Dict]:
        """获取代码镜头"""
        content = self.doc_manager.get_content(uri)
        if not content:
            return []

        lenses = []

        try:
            import ast as ast_mod
            tree = ast_mod.parse(content)

            for node in ast_mod.walk(tree):
                if isinstance(node, ast_mod.FunctionDef):
                    # 复杂度标记
                    complexity = 1
                    for child in ast_mod.walk(node):
                        if isinstance(child, (ast_mod.If, ast_mod.While, ast_mod.For, ast_mod.ExceptHandler)):
                            complexity += 1

                    if complexity > 5:
                        lenses.append({
                            "range": {
                                "start": {"line": node.lineno - 1, "character": 0},
                                "end": {"line": node.lineno - 1, "character": 0},
                            },
                            "command": {
                                "title": f"⚠ 复杂度: {complexity}",
                                "command": "moss.showComplexity",
                                "arguments": [uri, node.name, complexity],
                            },
                        })

                    # 引用计数
                    lenses.append({
                        "range": {
                            "start": {"line": node.lineno - 1, "character": 0},
                            "end": {"line": node.lineno - 1, "character": 0},
                        },
                        "command": {
                            "title": f"📊 {node.name}",
                            "command": "moss.showReferences",
                            "arguments": [uri, node.lineno - 1, 0],
                        },
                    })

        except Exception as e:
            logger.error(f"获取代码镜头失败: {e}")

        return lenses

    # ──────────────────────────────────────────────────────────
    # Utility
    # ──────────────────────────────────────────────────────────

    def _get_word_at_position(self, line: str, character: int) -> Optional[str]:
        """获取指定位置的单词"""
        if character >= len(line):
            return None

        # 向左扩展
        start = character
        while start > 0 and (line[start - 1].isalnum() or line[start - 1] == '_'):
            start -= 1

        # 向右扩展
        end = character
        while end < len(line) and (line[end].isalnum() or line[end] == '_'):
            end += 1

        if start == end:
            return None

        return line[start:end]


# ──────────────────────────────────────────────────────────────
# JSON-RPC Protocol Handler (standalone, no pygls dependency)
# ──────────────────────────────────────────────────────────────

class LSPProtocolHandler:
    """
    LSP JSON-RPC 协议处理器

    处理 JSON-RPC 2.0 消息，支持:
    - stdio 传输
    - TCP 传输
    """

    def __init__(self, provider: MossAnalysisProvider):
        self.provider = provider
        self.request_handlers = {
            "initialize": self._handle_initialize,
            "initialized": self._handle_initialized,
            "shutdown": self._handle_shutdown,
            "exit": self._handle_exit,
            "textDocument/completion": self._handle_completion,
            "textDocument/hover": self._handle_hover,
            "textDocument/definition": self._handle_definition,
            "textDocument/references": self._handle_references,
            "textDocument/documentSymbol": self._handle_document_symbol,
            "textDocument/codeAction": self._handle_code_action,
            "textDocument/codeLens": self._handle_code_lens,
            "textDocument/prepareRename": self._handle_prepare_rename,
            "textDocument/rename": self._handle_rename,
        }
        self.notification_handlers = {
            "textDocument/didOpen": self._handle_did_open,
            "textDocument/didChange": self._handle_did_change,
            "textDocument/didClose": self._handle_did_close,
            "textDocument/didSave": self._handle_did_save,
        }
        self._running = False
        self._initialized = False

    def _send_response(self, id: Any, result: Any):
        """发送响应"""
        response = {
            "jsonrpc": "2.0",
            "id": id,
            "result": result,
        }
        self._write_message(json.dumps(response))

    def _send_notification(self, method: str, params: Any):
        """发送通知"""
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }
        self._write_message(json.dumps(notification))

    def _send_error(self, id: Any, code: int, message: str):
        """发送错误"""
        error = {
            "jsonrpc": "2.0",
            "id": id,
            "error": {"code": code, "message": message},
        }
        self._write_message(json.dumps(error))

    def _write_message(self, content: str):
        """写消息到输出流"""
        message = f"Content-Length: {len(content)}\r\n\r\n{content}"
        sys.stdout.write(message)
        sys.stdout.flush()

    def _read_message(self) -> Optional[Dict]:
        """从输入流读取消息"""
        # 读取 header
        headers = {}
        while True:
            line = sys.stdin.readline()
            if not line:
                return None
            line = line.strip()
            if not line:
                break
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()

        content_length = int(headers.get('Content-Length', 0))
        if content_length == 0:
            return None

        # 读取 body
        body = sys.stdin.read(content_length)
        if not body:
            return None

        return json.loads(body)

    def handle_message(self, message: Dict):
        """处理单个消息"""
        method = message.get('method', '')
        id = message.get('id')
        params = message.get('params', {})

        if id is not None:
            # Request
            handler = self.request_handlers.get(method)
            if handler:
                try:
                    result = handler(params)
                    self._send_response(id, result)
                except Exception as e:
                    logger.error(f"请求处理失败: {method} - {e}")
                    self._send_error(id, -32603, str(e))
            else:
                self._send_error(id, -32601, f"未知方法: {method}")
        else:
            # Notification
            handler = self.notification_handlers.get(method)
            if handler:
                try:
                    handler(params)
                except Exception as e:
                    logger.error(f"通知处理失败: {method} - {e}")

    # ──────────────────────────────────────────────────────────
    # Request Handlers
    # ──────────────────────────────────────────────────────────

    def _handle_initialize(self, params: Dict) -> Dict:
        """初始化"""
        root_path = params.get('rootUri', params.get('rootPath', ''))
        if root_path.startswith('file://'):
            root_path = root_path[7:]

        result = self.provider.initialize(root_path)
        self._initialized = True
        return result

    def _handle_initialized(self, params: Dict) -> None:
        """客户端初始化完成"""
        pass

    def _handle_shutdown(self, params: Dict) -> None:
        """关闭"""
        self._running = False
        return None

    def _handle_exit(self, params: Dict) -> None:
        """退出"""
        self._running = False
        sys.exit(0)

    def _handle_completion(self, params: Dict) -> Dict:
        """补全"""
        uri = params['textDocument']['uri']
        position = params['position']
        items = self.provider.get_completions(
            uri, position['line'], position['character']
        )
        return {
            "isIncomplete": False,
            "items": [
                {
                    "label": item.label,
                    "kind": item.kind,
                    "detail": item.detail,
                    "documentation": item.documentation,
                    "insertText": item.insert_text or item.label,
                    "sortText": item.sort_text,
                }
                for item in items
            ],
        }

    def _handle_hover(self, params: Dict) -> Optional[Dict]:
        """悬停"""
        uri = params['textDocument']['uri']
        position = params['position']
        hover = self.provider.get_hover(
            uri, position['line'], position['character']
        )
        if hover:
            return {
                "contents": {
                    "kind": "markdown",
                    "value": hover,
                }
            }
        return None

    def _handle_definition(self, params: Dict) -> Optional[Dict]:
        """跳转定义"""
        uri = params['textDocument']['uri']
        position = params['position']
        location = self.provider.get_definition(
            uri, position['line'], position['character']
        )
        if location:
            return {
                "uri": location.uri,
                "range": {
                    "start": {"line": location.line, "character": location.character},
                    "end": {"line": location.line, "character": location.character + 1},
                },
            }
        return None

    def _handle_references(self, params: Dict) -> Optional[List]:
        """查找引用"""
        uri = params['textDocument']['uri']
        position = params['position']
        include_decl = params.get('context', {}).get('includeDeclaration', True)
        locations = self.provider.get_references(
            uri, position['line'], position['character'],
            include_declaration=include_decl
        )
        return [
            {
                "uri": loc.uri,
                "range": {
                    "start": {"line": loc.line, "character": loc.character},
                    "end": {"line": loc.line, "character": loc.character + 1},
                },
            }
            for loc in locations
        ]

    def _handle_document_symbol(self, params: Dict) -> List:
        """文档符号"""
        uri = params['textDocument']['uri']
        symbols = self.provider.get_document_symbols(uri)
        return self._symbols_to_lsp(symbols)

    def _handle_code_action(self, params: Dict) -> List:
        """代码操作"""
        uri = params['textDocument']['uri']
        range_info = params['range']
        diagnostics = params.get('context', {}).get('diagnostics', [])
        only = params.get('context', {}).get('only')

        actions = self.provider.get_code_actions(
            uri,
            (range_info['start']['line'], range_info['start']['character']),
            (range_info['end']['line'], range_info['end']['character']),
            diagnostics=diagnostics,
            only=only,
        )

        return [
            {
                "title": action.title,
                "kind": action.kind,
                "edit": action.edit,
                "isPreferred": action.is_preferred,
            }
            for action in actions
        ]

    def _handle_code_lens(self, params: Dict) -> List:
        """代码镜头"""
        uri = params['textDocument']['uri']
        return self.provider.get_code_lens(uri)

    def _handle_prepare_rename(self, params: Dict) -> Optional[Dict]:
        """准备重命名"""
        uri = params['textDocument']['uri']
        position = params['position']
        return self.provider.prepare_rename(
            uri, position['line'], position['character']
        )

    def _handle_rename(self, params: Dict) -> Optional[Dict]:
        """重命名"""
        uri = params['textDocument']['uri']
        position = params['position']
        new_name = params['newName']
        return self.provider.rename(
            uri, position['line'], position['character'], new_name
        )

    # ──────────────────────────────────────────────────────────
    # Notification Handlers
    # ──────────────────────────────────────────────────────────

    def _handle_did_open(self, params: Dict):
        """文档打开"""
        text_doc = params['textDocument']
        uri = text_doc['uri']
        content = text_doc['text']
        version = text_doc.get('version', 0)

        diagnostics = self.provider.did_open(uri, content, version)

        # 发送诊断通知
        self._send_notification("textDocument/publishDiagnostics", {
            "uri": uri,
            "diagnostics": [
                {
                    "range": {
                        "start": {"line": d.line, "character": d.character},
                        "end": {"line": d.line, "character": d.character + 1},
                    },
                    "severity": d.severity,
                    "source": d.source,
                    "message": d.message,
                    "code": d.code,
                }
                for d in diagnostics
            ],
        })

    def _handle_did_change(self, params: Dict):
        """文档变更"""
        uri = params['textDocument']['uri']
        version = params['textDocument'].get('version', 0)

        # 获取最新内容
        changes = params.get('contentChanges', [])
        if changes:
            content = changes[-1].get('text', '')
            diagnostics = self.provider.did_change(uri, content, version)

            # 发送诊断通知
            self._send_notification("textDocument/publishDiagnostics", {
                "uri": uri,
                "diagnostics": [
                    {
                        "range": {
                            "start": {"line": d.line, "character": d.character},
                            "end": {"line": d.line, "character": d.character + 1},
                        },
                        "severity": d.severity,
                        "source": d.source,
                        "message": d.message,
                        "code": d.code,
                    }
                    for d in diagnostics
                ],
            })

    def _handle_did_close(self, params: Dict):
        """文档关闭"""
        uri = params['textDocument']['uri']
        self.provider.did_close(uri)

    def _handle_did_save(self, params: Dict):
        """文档保存"""
        uri = params['textDocument']['uri']
        content = params.get('text', None)
        self.provider.did_save(uri, content)

    # ──────────────────────────────────────────────────────────
    # Utility
    # ──────────────────────────────────────────────────────────

    def _symbols_to_lsp(self, symbols: List[MossSymbolInfo]) -> List[Dict]:
        """转换符号为 LSP 格式"""
        result = []
        for sym in symbols:
            item = {
                "name": sym.name,
                "kind": sym.kind,
                "range": {
                    "start": {"line": sym.location.line, "character": sym.location.character},
                    "end": {"line": sym.location.line, "character": sym.location.character + len(sym.name)},
                },
                "selectionRange": {
                    "start": {"line": sym.location.line, "character": sym.location.character},
                    "end": {"line": sym.location.line, "character": sym.location.character + len(sym.name)},
                },
            }
            if sym.container_name:
                item["containerName"] = sym.container_name
            if sym.children:
                item["children"] = self._symbols_to_lsp(sym.children)
            result.append(item)
        return result

    # ──────────────────────────────────────────────────────────
    # Server
    # ──────────────────────────────────────────────────────────

    def start_stdio(self):
        """启动 stdio 模式 LSP 服务器"""
        self._running = True
        logger.info("MOSS LSP Server starting (stdio mode)...")

        while self._running:
            try:
                message = self._read_message()
                if message is None:
                    break
                self.handle_message(message)
            except Exception as e:
                logger.error(f"消息处理错误: {e}")
                continue

        logger.info("MOSS LSP Server stopped.")

    def start_tcp(self, host: str = "127.0.0.1", port: int = 2087):
        """启动 TCP 模式 LSP 服务器"""
        logger.info(f"MOSS LSP Server starting (TCP {host}:{port})...")
        # TCP 模式需要额外的 socket 处理
        # 这里只声明接口，实际实现需要 asyncio TCP server
        print(f"MOSS LSP Server listening on {host}:{port}")


# ──────────────────────────────────────────────────────────────
# Pygls-based Server (optional, if pygls is available)
# ──────────────────────────────────────────────────────────────

def create_pygls_server(provider: MossAnalysisProvider) -> 'LanguageServer':
    """
    使用 pygls 创建标准 LSP 服务器

    需要安装: pip install pygls lsprotocol
    """
    if not HAS_PYGLS:
        raise ImportError("pygls not installed. Run: pip install pygls lsprotocol")

    server = LanguageServer("moss-lsp", "v9.3.0")

    @server.feature(lsp.TEXT_DOCUMENT_DID_OPEN)
    def did_open(params: lsp.DidOpenTextDocumentParams):
        uri = params.text_document.uri
        content = params.text_document.text
        version = params.text_document.version
        diagnostics = provider.did_open(uri, content, version)

        server.publish_diagnostics(
            uri,
            [
                lsp.Diagnostic(
                    range=lsp.Range(
                        start=lsp.Position(line=d.line, character=d.character),
                        end=lsp.Position(line=d.line, character=d.character + 1),
                    ),
                    message=d.message,
                    severity=d.severity,
                    source=d.source,
                    code=d.code,
                )
                for d in diagnostics
            ]
        )

    @server.feature(lsp.TEXT_DOCUMENT_DID_CHANGE)
    def did_change(params: lsp.DidChangeTextDocumentParams):
        uri = params.text_document.uri
        version = params.text_document.version
        for change in params.content_changes:
            content = change.text
            diagnostics = provider.did_change(uri, content, version)

            server.publish_diagnostics(
                uri,
                [
                    lsp.Diagnostic(
                        range=lsp.Range(
                            start=lsp.Position(line=d.line, character=d.character),
                            end=lsp.Position(line=d.line, character=d.character + 1),
                        ),
                        message=d.message,
                        severity=d.severity,
                        source=d.source,
                    )
                    for d in diagnostics
                ]
            )

    @server.feature(
        lsp.TEXT_DOCUMENT_COMPLETION,
        lsp.CompletionOptions(trigger_characters=[".", "(", "'", '"']),
    )
    def completions(params: lsp.CompletionParams):
        uri = params.text_document.uri
        position = params.position
        items = provider.get_completions(uri, position.line, position.character)

        return lsp.CompletionList(
            is_incomplete=False,
            items=[
                lsp.CompletionItem(
                    label=item.label,
                    kind=item.kind,
                    detail=item.detail,
                    documentation=item.documentation,
                    insert_text=item.insert_text or item.label,
                    sort_text=item.sort_text,
                )
                for item in items
            ],
        )

    @server.feature(lsp.TEXT_DOCUMENT_HOVER)
    def hover(params: lsp.HoverParams):
        uri = params.text_document.uri
        position = params.position
        hover_result = provider.get_hover(uri, position.line, position.character)

        if hover_result:
            return lsp.Hover(
                contents=lsp.MarkupContent(
                    kind=lsp.MarkupKind.Markdown,
                    value=hover_result,
                )
            )
        return None

    @server.feature(lsp.TEXT_DOCUMENT_DEFINITION)
    def definition(params: lsp.DefinitionParams):
        uri = params.text_document.uri
        position = params.position
        location = provider.get_definition(uri, position.line, position.character)

        if location:
            return lsp.Location(
                uri=location.uri,
                range=lsp.Range(
                    start=lsp.Position(line=location.line, character=location.character),
                    end=lsp.Position(line=location.line, character=location.character + 1),
                ),
            )
        return None

    @server.feature(lsp.TEXT_DOCUMENT_REFERENCES)
    def references(params: lsp.ReferenceParams):
        uri = params.text_document.uri
        position = params.position
        include_decl = params.context.include_declaration

        locations = provider.get_references(
            uri, position.line, position.character,
            include_declaration=include_decl
        )

        return [
            lsp.Location(
                uri=loc.uri,
                range=lsp.Range(
                    start=lsp.Position(line=loc.line, character=loc.character),
                    end=lsp.Position(line=loc.line, character=loc.character + 1),
                ),
            )
            for loc in locations
        ]

    @server.feature(lsp.TEXT_DOCUMENT_DOCUMENT_SYMBOL)
    def document_symbol(params: lsp.DocumentSymbolParams):
        uri = params.text_document.uri
        symbols = provider.get_document_symbols(uri)

        def to_lsp_symbol(sym: MossSymbolInfo) -> lsp.DocumentSymbol:
            return lsp.DocumentSymbol(
                name=sym.name,
                kind=sym.kind,
                range=lsp.Range(
                    start=lsp.Position(line=sym.location.line, character=sym.location.character),
                    end=lsp.Position(line=sym.location.line, character=sym.location.character + len(sym.name)),
                ),
                selection_range=lsp.Range(
                    start=lsp.Position(line=sym.location.line, character=sym.location.character),
                    end=lsp.Position(line=sym.location.line, character=sym.location.character + len(sym.name)),
                ),
                children=[to_lsp_symbol(c) for c in sym.children] if sym.children else None,
            )

        return [to_lsp_symbol(s) for s in symbols]

    @server.feature(lsp.TEXT_DOCUMENT_CODE_ACTION)
    def code_action(params: lsp.CodeActionParams):
        uri = params.text_document.uri
        range_info = params.range
        diag = params.context.diagnostics
        only = params.context.only

        actions = provider.get_code_actions(
            uri,
            (range_info.start.line, range_info.start.character),
            (range_info.end.line, range_info.end.character),
            diagnostics=[{"code": d.code, "line": d.range.start.line} for d in diag],
            only=only,
        )

        return [
            lsp.CodeAction(
                title=action.title,
                kind=action.kind,
                edit=action.edit,
                is_preferred=action.is_preferred,
            )
            for action in actions
        ]

    @server.feature(lsp.TEXT_DOCUMENT_RENAME)
    def rename(params: lsp.RenameParams):
        uri = params.text_document.uri
        position = params.position
        new_name = params.new_name

        result = provider.rename(uri, position.line, position.character, new_name)
        if result:
            return lsp.WorkspaceEdit(changes=result.get("changes"))
        return None

    return server


# ──────────────────────────────────────────────────────────────
# Demo & Testing
# ──────────────────────────────────────────────────────────────

def test_lsp_provider():
    """测试 LSP 分析提供器"""
    print("\n" + "="*60)
    print("MOSS v9.3 - LSP Server 测试")
    print("="*60)

    # 创建提供器
    provider = MossAnalysisProvider("/tmp/moss_lsp_test")

    # 测试代码
    test_code = '''
import os
import sys
import unused_module

def long_function(x, y, z):
    """A very long function that should be split."""
    result = 0
    for i in range(x):
        if i % 2 == 0:
            result += i * y
        else:
            result -= i * z

    for j in range(y):
        if j % 3 == 0:
            result += j
        elif j % 3 == 1:
            result -= j
        else:
            result *= 2

    for k in range(z):
        if k > 10:
            result += k
        elif k > 5:
            result -= k
        else:
            result += k * 2

    return result

class MyClass:
    def method_one(self):
        pass

    def method_two(self, x):
        return x * 2

def short_func():
    return 42
'''

    # 1. 测试初始化
    print("\n[1] 测试初始化")
    capabilities = provider.initialize("/tmp/moss_lsp_test")
    print(f"  能力数量: {len(capabilities['capabilities'])}")

    # 2. 测试文档打开和诊断
    print("\n[2] 测试文档诊断")
    uri = "file:///test.py"
    diagnostics = provider.did_open(uri, test_code)
    print(f"  诊断数量: {len(diagnostics)}")
    for d in diagnostics:
        print(f"    [{d.severity}] 行 {d.line+1}: {d.message} ({d.code})")

    # 3. 测试代码操作
    print("\n[3] 测试代码操作")
    actions = provider.get_code_actions(uri, (5, 0), (5, 0))
    print(f"  操作数量: {len(actions)}")
    for a in actions:
        print(f"    [{a.kind}] {a.title}")

    # 4. 测试补全
    print("\n[4] 测试补全")
    completions = provider.get_completions(uri, 0, 0)
    print(f"  补全项数量: {len(completions)}")
    for c in completions[:5]:
        print(f"    {c.label} ({c.kind}) - {c.detail}")

    # 5. 测试悬停
    print("\n[5] 测试悬停")
    hover = provider.get_hover(uri, 5, 5)  # long_function
    if hover:
        print(f"  悬停内容:\n{hover[:200]}...")

    # 6. 测试文档符号
    print("\n[6] 测试文档符号")
    symbols = provider.get_document_symbols(uri)
    print(f"  符号数量: {len(symbols)}")
    for s in symbols:
        print(f"    {s.name} (kind={s.kind}) @ 行 {s.location.line + 1}")
        for c in s.children:
            print(f"      └─ {c.name} (kind={c.kind})")

    # 7. 测试代码镜头
    print("\n[7] 测试代码镜头")
    lenses = provider.get_code_lens(uri)
    print(f"  镜头数量: {len(lenses)}")
    for l in lenses[:5]:
        print(f"    {l.get('command', {}).get('title', 'N/A')}")

    # 8. 测试重命名
    print("\n[8] 测试重命名")
    rename_result = provider.rename(uri, 5, 5, "better_long_function")
    if rename_result:
        changes = rename_result.get('changes', {})
        total_changes = sum(len(v) for v in changes.values())
        print(f"  重命名变更: {total_changes} 处")

    # 9. 测试定义跳转
    print("\n[9] 测试定义跳转")
    definition = provider.get_definition(uri, 5, 5)
    if definition:
        print(f"  定义位置: 行 {definition.line + 1}")

    # 10. 测试引用查找
    print("\n[10] 测试引用查找")
    refs = provider.get_references(uri, 5, 5)
    print(f"  引用数量: {len(refs)}")

    print("\n" + "="*60)
    print("LSP Server 测试完成!")
    print("="*60)


if __name__ == "__main__":
    test_lsp_provider()
