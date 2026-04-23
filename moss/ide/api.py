#!/usr/bin/env python3
"""
MOSS v9.2 - IDE Plugin API
IDE插件API - 支持VSCode、PyCharm等IDE集成

Author: MOSS v9.2
Date: 2026-04-23
"""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union


@dataclass
class Issue:
    """代码问题"""
    file_path: str
    line: int
    column: int
    severity: str  # error / warning / info
    message: str
    code: str = ""  # 问题类型代码
    suggestion: Optional[str] = None


@dataclass
class QuickFix:
    """快速修复"""
    title: str
    description: str
    edit: 'TextEdit'
    is_preferred: bool = False


@dataclass
class TextEdit:
    """文本编辑"""
    file_path: str
    start_line: int
    start_column: int
    end_line: int
    end_column: int
    new_text: str


@dataclass
class RefactoringSuggestion:
    """重构建议"""
    title: str
    description: str
    type: str  # function_split / import_organize / etc.
    preview: str
    impact: str


class MOSSIDEPlugin:
    """
    MOSS IDE 插件主类

    为IDE提供统一的API接口:
    - 代码分析
    - 问题检测
    - 快速修复
    - 重构建议
    - 代码补全
    """

    def __init__(self, codebase_path: str = "."):
        self.codebase_path = Path(codebase_path)
        self._engine = None
        self._config = None

    async def initialize(self):
        """初始化插件"""
        from moss.core.cross_file_refactor import create_cross_file_engine
        from moss.core.config_manager import ConfigManager

        # 加载配置
        config_mgr = ConfigManager()
        self._config = config_mgr.load_config()

        # 初始化引擎
        self._engine = await create_cross_file_engine(str(self.codebase_path))

        return True

    # ─────────────────────────────────────────────────────────
    # 代码分析
    # ─────────────────────────────────────────────────────────

    async def analyze_file(self, file_path: str, content: Optional[str] = None) -> List[Issue]:
        """
        分析单个文件，返回发现的问题

        Args:
            file_path: 文件路径
            content: 文件内容（如果为None，则读取文件）

        Returns:
            问题列表
        """
        issues = []

        # 1. 语法检查
        if content:
            syntax_issues = self._check_syntax(content, file_path)
            issues.extend(syntax_issues)

        # 2. 导入分析
        import_issues = self._analyze_imports(file_path, content)
        issues.extend(import_issues)

        # 3. 代码质量问题
        quality_issues = self._analyze_quality(file_path, content)
        issues.extend(quality_issues)

        return issues

    def _check_syntax(self, content: str, file_path: str) -> List[Issue]:
        """检查语法错误"""
        import ast
        issues = []

        try:
            ast.parse(content)
        except SyntaxError as e:
            issues.append(Issue(
                file_path=file_path,
                line=e.lineno or 1,
                column=e.offset or 0,
                severity="error",
                message=f"语法错误: {e.msg}",
                code="E001"
            ))

        return issues

    def _analyze_imports(self, file_path: str, content: Optional[str] = None) -> List[Issue]:
        """分析导入问题"""
        import ast
        import re
        issues = []

        if content is None:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
            except Exception:
                return issues

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        # 检查重复导入
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for alias in node.names:
                    import_str = f"{node.module}.{alias.name}"
                    if import_str in imports:
                        issues.append(Issue(
                            file_path=file_path,
                            line=node.lineno,
                            column=0,
                            severity="warning",
                            message=f"重复导入: {alias.name}",
                            code="W001",
                            suggestion=f"移除重复的 from {node.module} import {alias.name}"
                        ))
                    imports.append(import_str)

        # 检查未使用的导入
        defined_imports = {}
        used_names = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for alias in node.names:
                    name = alias.asname or alias.name
                    defined_imports[name] = node.lineno
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used_names.add(node.id)

        for name, line in defined_imports.items():
            if name not in used_names and not name.startswith('_'):
                issues.append(Issue(
                    file_path=file_path,
                    line=line,
                    column=0,
                    severity="info",
                    message=f"未使用的导入: {name}",
                    code="I001",
                    suggestion=f"移除未使用的导入 {name}"
                ))

        return issues

    def _analyze_quality(self, file_path: str, content: Optional[str] = None) -> List[Issue]:
        """分析代码质量问题"""
        import ast
        issues = []

        if content is None:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
            except Exception:
                return issues

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        lines = content.split('\n')

        # 检查长函数
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_lines = node.end_lineno - node.lineno if node.end_lineno else 0
                if func_lines > 50:
                    issues.append(Issue(
                        file_path=file_path,
                        line=node.lineno,
                        column=0,
                        severity="warning",
                        message=f"函数过长 ({func_lines} 行): {node.name}",
                        code="W101",
                        suggestion="考虑拆分为更小的函数"
                    ))

        # 检查复杂表达式
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                issues.append(Issue(
                    file_path=file_path,
                    line=i,
                    column=0,
                    severity="info",
                    message=f"行过长 ({len(line)} 字符)",
                    code="I101",
                    suggestion="考虑换行"
                ))

        return issues

    # ─────────────────────────────────────────────────────────
    # 快速修复
    # ─────────────────────────────────────────────────────────

    def get_quick_fixes(self, issue: Issue) -> List[QuickFix]:
        """
        获取问题的快速修复方案
        """
        fixes = []

        if issue.code == "W001":  # 重复导入
            fixes.append(self._create_remove_import_fix(issue))

        elif issue.code == "I001":  # 未使用导入
            fixes.append(self._create_remove_import_fix(issue))

        elif issue.code == "W101":  # 长函数
            fixes.append(QuickFix(
                title="提取函数",
                description="将部分逻辑提取为新函数",
                edit=TextEdit(
                    file_path=issue.file_path,
                    start_line=issue.line,
                    start_column=0,
                    end_line=issue.line,
                    end_column=0,
                    new_text="# TODO: 提取函数\n"
                ),
                is_preferred=False
            ))

        elif issue.code == "I101":  # 行过长
            fixes.append(QuickFix(
                title="自动换行",
                description="尝试自动格式化换行",
                edit=TextEdit(
                    file_path=issue.file_path,
                    start_line=issue.line,
                    start_column=0,
                    end_line=issue.line,
                    end_column=0,
                    new_text="# TODO: 手动换行\n"
                ),
                is_preferred=True
            ))

        return fixes

    def _create_remove_import_fix(self, issue: Issue) -> QuickFix:
        """创建移除导入的修复"""
        return QuickFix(
            title="移除导入",
            description=f"移除 {issue.message.split(':')[1].strip()}",
            edit=TextEdit(
                file_path=issue.file_path,
                start_line=issue.line,
                start_column=0,
                end_line=issue.line + 1,
                end_column=0,
                new_text=""
            ),
            is_preferred=True
        )

    def apply_quick_fix(self, fix: QuickFix) -> bool:
        """应用快速修复"""
        try:
            file_path = Path(fix.edit.file_path)
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')

            # 删除旧内容
            start = fix.edit.start_line - 1
            end = fix.edit.end_line - 1
            del lines[start:end]

            # 插入新内容
            if fix.edit.new_text:
                lines.insert(start, fix.edit.new_text.rstrip('\n'))

            file_path.write_text('\n'.join(lines), encoding='utf-8')
            return True
        except Exception as e:
            print(f"应用修复失败: {e}")
            return False

    # ─────────────────────────────────────────────────────────
    # 重构建议
    # ─────────────────────────────────────────────────────────

    async def get_refactoring_suggestions(self, file_path: str) -> List[RefactoringSuggestion]:
        """
        获取文件的重构建议
        """
        suggestions = []

        # 1. 导入组织
        suggestions.append(RefactoringSuggestion(
            title="组织导入",
            description="排序导入语句，合并重复导入",
            type="import_organize",
            preview="from typing import List, Dict\nimport os\nimport sys",
            impact="影响当前文件"
        ))

        # 2. 检查是否需要函数拆分
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            import ast
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_lines = node.end_lineno - node.lineno if node.end_lineno else 0
                    if func_lines > 80:
                        suggestions.append(RefactoringSuggestion(
                            title=f"拆分函数: {node.name}",
                            description=f"函数 {node.name} 有 {func_lines} 行，建议拆分",
                            type="function_split",
                            preview=f"def {node.name}():\n    # 提取辅助函数\n    ...",
                            impact="影响当前文件"
                        ))
        except Exception:
            pass

        return suggestions

    # ─────────────────────────────────────────────────────────
    # 代码补全
    # ─────────────────────────────────────────────────────────

    def get_completions(
        self,
        file_path: str,
        line: int,
        column: int,
        prefix: str
    ) -> List[Dict]:
        """
        获取代码补全建议
        """
        completions = []

        # 从符号表中查找匹配
        if self._engine:
            for sym_name in self._engine.symbol_tracker.usage_map.keys():
                if sym_name.startswith(prefix) and len(sym_name) > len(prefix):
                    completions.append({
                        'label': sym_name,
                        'kind': 'symbol',
                        'detail': f'来自符号表'
                    })

        return completions

    # ─────────────────────────────────────────────────────────
    # 文件保存钩子
    # ─────────────────────────────────────────────────────────

    async def on_file_save(self, file_path: str, content: str) -> Optional[List[QuickFix]]:
        """
        文件保存时调用

        Returns:
            自动修复列表，或 None
        """
        if not self._config or not self._config.refactor.ast_enabled:
            return None

        # 自动修复导入问题
        issues = self._analyze_imports(file_path, content)
        fixes = []

        for issue in issues:
            if issue.code in ["W001", "I001"]:  # 重复/未使用导入
                quick_fixes = self.get_quick_fixes(issue)
                for fix in quick_fixes:
                    if fix.is_preferred:
                        fixes.append(fix)

        return fixes if fixes else None

    # ─────────────────────────────────────────────────────────
    # 跨文件操作
    # ─────────────────────────────────────────────────────────

    async def move_symbol(
        self,
        symbol_name: str,
        source_file: str,
        target_file: str,
        dry_run: bool = True
    ) -> Dict:
        """
        移动符号到另一个文件
        """
        if not self._engine:
            return {'success': False, 'message': '引擎未初始化'}

        # 转换文件路径为模块名
        source_module = self._file_to_module(source_file)
        target_module = self._file_to_module(target_file)

        from moss.core.move_operations import MoveExecutor
        executor = MoveExecutor(self._engine)

        return await executor.move_function(
            symbol_name, source_module, target_module, dry_run
        )

    def _file_to_module(self, file_path: str) -> str:
        """文件路径转模块名"""
        rel_path = Path(file_path).relative_to(self.codebase_path)
        parts = list(rel_path.with_suffix('').parts)
        if parts[-1] == '__init__':
            parts = parts[:-1]
        return '.'.join(parts)


# 测试
if __name__ == "__main__":
    async def test():
        print("=" * 60)
        print("MOSS v9.2 - IDE Plugin API 测试")
        print("=" * 60)

        plugin = MOSSIDEPlugin('/workspace/moss/moss')
        await plugin.initialize()

        # 1. 分析文件
        print("\n[1] 分析文件...")
        test_file = '/workspace/moss/moss/core/agent_registry.py'
        issues = await plugin.analyze_file(test_file)

        print(f"  发现 {len(issues)} 个问题:")
        for issue in issues[:5]:
            icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(issue.severity, "•")
            print(f"    {icon} [{issue.code}] {issue.message}")

        # 2. 获取快速修复
        if issues:
            print("\n[2] 快速修复...")
            fixes = plugin.get_quick_fixes(issues[0])
            for fix in fixes:
                print(f"    • {fix.title}: {fix.description}")

        # 3. 重构建议
        print("\n[3] 重构建议...")
        suggestions = await plugin.get_refactoring_suggestions(test_file)
        for s in suggestions:
            print(f"    • {s.title}: {s.description}")

        print("\n测试完成!")

    asyncio.run(test())
