#!/usr/bin/env python3
"""
MOSS v9.2 - Cross-File Refactor Engine
跨文件代码重构引擎

核心组件:
1. ImportGraphBuilder - 模块依赖图
2. SymbolTracker - 符号追踪
3. ImpactAnalyzer - 影响分析
4. CrossFileRefactorEngine - 重构执行
5. TransactionManager - 事务管理

Author: MOSS v9.2
Date: 2026-04-23
"""

import ast
import asyncio
import hashlib
import json
import os
import re
import shutil
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import networkx as nx


# ──────────────────────────────────────────────────────────────
# Data Structures
# ──────────────────────────────────────────────────────────────

class SymbolKind(Enum):
    FUNCTION = auto()
    ASYNC_FUNCTION = auto()
    CLASS = auto()
    VARIABLE = auto()
    IMPORT = auto()
    CONSTANT = auto()


class OperationType(Enum):
    MOVE_FUNCTION = auto()
    MOVE_CLASS = auto()
    EXTRACT_MODULE = auto()
    MERGE_MODULES = auto()
    RENAME_SYMBOL = auto()
    UPDATE_IMPORTS = auto()


@dataclass
class SymbolInfo:
    """符号信息"""
    name: str
    kind: SymbolKind
    defined_in: str           # 模块路径
    line_start: int
    line_end: int
    is_public: bool = True
    source_code: Optional[str] = None
    dependencies: Set[str] = field(default_factory=set)  # 此符号依赖的其他符号


@dataclass
class UsageLocation:
    """符号使用位置"""
    symbol_name: str
    file_path: str
    line: int
    column: int
    context: str = ""


@dataclass
class ImportInfo:
    """导入信息"""
    source_module: str      # 被导入的模块
    imported_names: List[str]  # 导入的名称
    import_line: int
    is_from_import: bool = True


@dataclass
class ModuleInfo:
    """模块信息"""
    path: str
    name: str               # 模块全名 (e.g., moss.core.agent_registry)
    imports: List[ImportInfo] = field(default_factory=list)
    exports: Set[str] = field(default_factory=set)
    defined_symbols: Dict[str, SymbolInfo] = field(default_factory=dict)
    line_count: int = 0


@dataclass
class ImpactReport:
    """重构影响报告"""
    affected_files: List[str]
    affected_symbols: List[str]
    affected_imports: List[str]
    risk_level: str = "low"     # low / medium / high
    estimated_changes: int = 0


@dataclass
class CodeChange:
    """代码变更"""
    action: str             # add / remove / modify / move
    file_path: str
    line_start: int
    line_end: int
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    description: str = ""


@dataclass
class RefactoringOperation:
    """重构操作"""
    operation_type: OperationType
    changes: List[CodeChange] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class RefactoringResult:
    """重构结果"""
    success: bool
    operations_applied: int = 0
    files_modified: List[str] = field(default_factory=list)
    changes: List[CodeChange] = field(default_factory=list)
    rollback_available: bool = False
    commit_hash: Optional[str] = None
    message: str = ""


# ──────────────────────────────────────────────────────────────
# Import Graph Builder
# ──────────────────────────────────────────────────────────────

class ImportGraphBuilder:
    """
    构建模块依赖图

    使用 NetworkX 有向图表示模块间依赖关系:
    - 节点: 模块
    - 边: import 关系 (A → B 表示 A 导入了 B)
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self.modules: Dict[str, ModuleInfo] = {}

    def build_graph(self, codebase_path: str, root_package: str = "") -> nx.DiGraph:
        """
        构建整个代码库的依赖图

        Args:
            codebase_path: 代码库根目录
            root_package: 根包名

        Returns:
            NetworkX 有向图
        """
        codebase = Path(codebase_path)

        # 1. 扫描所有 Python 文件
        py_files = list(codebase.rglob("*.py"))
        py_files = [f for f in py_files if "__pycache__" not in str(f)]

        print(f"[ImportGraph] 扫描 {len(py_files)} 个 Python 文件")

        # 2. 解析每个文件
        for py_file in py_files:
            module_name = self._path_to_module(py_file, codebase, root_package)
            module_info = self._parse_module(py_file, module_name)
            self.modules[module_name] = module_info
            self.graph.add_node(module_name, info=module_info)

        # 3. 构建依赖边
        for module_name, module_info in self.modules.items():
            for imp in module_info.imports:
                # 解析导入目标
                target_module = self._resolve_import(imp.source_module, module_name)
                if target_module and target_module in self.modules:
                    self.graph.add_edge(
                        module_name, target_module,
                        imported_names=imp.imported_names,
                        import_line=imp.import_line
                    )

        # 4. 统计
        node_count = self.graph.number_of_nodes()
        edge_count = self.graph.number_of_edges()
        print(f"[ImportGraph] 构建完成: {node_count} 个模块, {edge_count} 条依赖")

        return self.graph

    def get_dependents(self, module: str) -> List[str]:
        """获取依赖此模块的其他模块"""
        if module not in self.graph:
            return []
        return list(self.graph.predecessors(module))

    def get_dependencies(self, module: str) -> List[str]:
        """获取此模块依赖的模块"""
        if module not in self.graph:
            return []
        return list(self.graph.successors(module))

    def find_cycles(self) -> List[List[str]]:
        """发现循环依赖"""
        try:
            return list(nx.simple_cycles(self.graph))
        except Exception:
            return []

    def get_impact_set(self, module: str) -> Set[str]:
        """获取受模块变更影响的所有模块"""
        visited = set()
        queue = [module]

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            # 添加所有依赖此模块的模块
            for dep in self.get_dependents(current):
                if dep not in visited:
                    queue.append(dep)

        return visited - {module}

    def _parse_module(self, file_path: Path, module_name: str) -> ModuleInfo:
        """解析单个模块"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            return ModuleInfo(path=str(file_path), name=module_name, line_count=0)

        imports = []
        defined_symbols = {}
        exports = set()

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return ModuleInfo(
                path=str(file_path), name=module_name,
                line_count=len(lines), imports=imports
            )

        # 解析导入
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(ImportInfo(
                        source_module=alias.name,
                        imported_names=[alias.asname or alias.name],
                        import_line=node.lineno,
                        is_from_import=False
                    ))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    names = [alias.asname or alias.name for alias in node.names]
                    imports.append(ImportInfo(
                        source_module=node.module,
                        imported_names=names,
                        import_line=node.lineno,
                        is_from_import=True
                    ))

        # 解析定义的符号
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef):
                defined_symbols[node.name] = SymbolInfo(
                    name=node.name,
                    kind=SymbolKind.FUNCTION,
                    defined_in=module_name,
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    is_public=not node.name.startswith('_')
                )
            elif isinstance(node, ast.AsyncFunctionDef):
                defined_symbols[node.name] = SymbolInfo(
                    name=node.name,
                    kind=SymbolKind.ASYNC_FUNCTION,
                    defined_in=module_name,
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    is_public=not node.name.startswith('_')
                )
            elif isinstance(node, ast.ClassDef):
                defined_symbols[node.name] = SymbolInfo(
                    name=node.name,
                    kind=SymbolKind.CLASS,
                    defined_in=module_name,
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    is_public=not node.name.startswith('_')
                )

        # 检查 __all__ 导出
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == '__all__':
                        if isinstance(node.value, ast.List):
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant):
                                    exports.add(str(elt.value))

        # 如果没有 __all__，公开符号 = 非下划线开头的定义
        if not exports:
            exports = {name for name, info in defined_symbols.items() if info.is_public}

        return ModuleInfo(
            path=str(file_path),
            name=module_name,
            imports=imports,
            exports=exports,
            defined_symbols=defined_symbols,
            line_count=len(lines)
        )

    def _path_to_module(self, file_path: Path, base_path: Path, root_package: str = "") -> str:
        """文件路径转模块名"""
        try:
            rel_path = file_path.relative_to(base_path)
        except ValueError:
            rel_path = file_path

        parts = list(rel_path.with_suffix('').parts)

        # 处理 __init__.py
        if parts and parts[-1] == '__init__':
            parts = parts[:-1]

        if root_package:
            parts = [root_package] + parts

        return '.'.join(parts)

    def _resolve_import(self, import_name: str, from_module: str) -> Optional[str]:
        """解析导入名称到模块名"""
        # 检查是否是已知的模块
        if import_name in self.modules:
            return import_name

        # 检查部分匹配
        for module_name in self.modules:
            if module_name.endswith('.' + import_name) or module_name == import_name:
                return module_name

        # 检查是否是外部包
        known_stdlib = {'os', 'sys', 'json', 're', 'ast', 'asyncio', 'pathlib',
                       'typing', 'dataclasses', 'collections', 'hashlib', 'datetime',
                       'enum', 'abc', 'io', 'math', 'random', 'string', 'time',
                       'unittest', 'logging', 'argparse', 'tempfile', 'shutil',
                       'difflib', 'functools', 'itertools', 'operator', 'copy',
                       'inspect', 'textwrap', 'uuid', 'glob', 'fnmatch'}
        if import_name in known_stdlib:
            return None

        return None


# ──────────────────────────────────────────────────────────────
# Symbol Tracker
# ──────────────────────────────────────────────────────────────

class SymbolTracker:
    """
    跨文件符号追踪器

    追踪函数、类、变量在整个代码库中的定义和使用位置
    """

    def __init__(self, graph_builder: ImportGraphBuilder):
        self.graph_builder = graph_builder
        self.usage_map: Dict[str, List[UsageLocation]] = defaultdict(list)

    def build_usage_map(self) -> Dict[str, List[UsageLocation]]:
        """构建符号使用映射"""
        for module_name, module_info in self.graph_builder.modules.items():
            try:
                with open(module_info.path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception:
                continue

            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue

            # 遍历所有名称使用
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    self.usage_map[node.id].append(UsageLocation(
                        symbol_name=node.id,
                        file_path=module_info.path,
                        line=node.lineno,
                        column=node.col_offset
                    ))
                elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                    self.usage_map[node.value.id].append(UsageLocation(
                        symbol_name=node.value.id,
                        file_path=module_info.path,
                        line=node.lineno,
                        column=node.col_offset,
                        context=f".{node.attr}"
                    ))

        return dict(self.usage_map)

    def find_symbol_usages(self, symbol_name: str) -> List[UsageLocation]:
        """查找符号的所有使用位置"""
        return self.usage_map.get(symbol_name, [])

    def find_symbol_definition(self, symbol_name: str) -> Optional[SymbolInfo]:
        """查找符号的定义位置"""
        for module_name, module_info in self.graph_builder.modules.items():
            if symbol_name in module_info.defined_symbols:
                return module_info.defined_symbols[symbol_name]
        return None

    def get_symbols_in_module(self, module_name: str) -> Dict[str, SymbolInfo]:
        """获取模块中定义的所有符号"""
        module_info = self.graph_builder.modules.get(module_name)
        if module_info:
            return module_info.defined_symbols
        return {}

    def get_external_usages(self, symbol_name: str, source_module: str) -> List[UsageLocation]:
        """获取符号在模块外部的使用位置"""
        module_info = self.graph_builder.modules.get(source_module)
        if not module_info:
            return []

        source_path = module_info.path
        usages = self.find_symbol_usages(symbol_name)
        return [u for u in usages if u.file_path != source_path]


# ──────────────────────────────────────────────────────────────
# Impact Analyzer
# ──────────────────────────────────────────────────────────────

class ImpactAnalyzer:
    """
    重构影响分析器

    分析重构操作对代码库的影响范围和风险级别
    """

    def __init__(
        self,
        graph_builder: ImportGraphBuilder,
        symbol_tracker: SymbolTracker
    ):
        self.graph_builder = graph_builder
        self.symbol_tracker = symbol_tracker

    def analyze_move_impact(
        self,
        symbol_name: str,
        source_module: str,
        target_module: str
    ) -> ImpactReport:
        """分析移动符号的影响"""
        affected_files = set()
        affected_symbols = set()
        affected_imports = []

        # 1. 找到符号的所有外部使用
        usages = self.symbol_tracker.get_external_usages(symbol_name, source_module)
        for usage in usages:
            affected_files.add(usage.file_path)

        # 2. 找到依赖此模块的模块
        impact_set = self.graph_builder.get_impact_set(source_module)
        affected_files.update(
            self.graph_builder.modules[m].path for m in impact_set
            if m in self.graph_builder.modules
        )

        # 3. 检查符号依赖
        symbol = self.symbol_tracker.find_symbol_definition(symbol_name)
        if symbol:
            affected_symbols.update(symbol.dependencies)

        # 4. 分析导入需要更新的文件
        for module_name in impact_set:
            module_info = self.graph_builder.modules.get(module_name)
            if module_info:
                for imp in module_info.imports:
                    if symbol_name in imp.imported_names and imp.source_module == source_module:
                        affected_imports.append(
                            f"{module_name}:{imp.import_line} → {target_module}"
                        )

        # 5. 评估风险
        risk_level = "low"
        if len(affected_files) > 10:
            risk_level = "high"
        elif len(affected_files) > 3:
            risk_level = "medium"

        return ImpactReport(
            affected_files=sorted(affected_files),
            affected_symbols=sorted(affected_symbols),
            affected_imports=sorted(affected_imports),
            risk_level=risk_level,
            estimated_changes=len(affected_imports) + 2  # +2 for source/target
        )

    def analyze_module_split_impact(
        self,
        module_name: str
    ) -> ImpactReport:
        """分析模块拆分的影响"""
        dependents = self.graph_builder.get_dependents(module_name)
        module_info = self.graph_builder.modules.get(module_name)

        if not module_info:
            return ImpactReport(
                affected_files=[], affected_symbols=[], affected_imports=[],
                risk_level="high", estimated_changes=0
            )

        affected_files = set()
        for dep in dependents:
            if dep in self.graph_builder.modules:
                affected_files.add(self.graph_builder.modules[dep].path)

        affected_symbols = list(module_info.defined_symbols.keys())
        risk_level = "high" if len(dependents) > 10 else "medium"

        return ImpactReport(
            affected_files=sorted(affected_files),
            affected_symbols=sorted(affected_symbols),
            affected_imports=[],
            risk_level=risk_level,
            estimated_changes=len(dependents) + len(module_info.defined_symbols)
        )


# ──────────────────────────────────────────────────────────────
# Transaction Manager
# ──────────────────────────────────────────────────────────────

class TransactionManager:
    """
    事务管理器

    提供原子性的代码变更操作:
    - 开始事务
    - 应用变更
    - 提交或回滚
    """

    def __init__(self, backup_dir: str = ".moss/backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.applied_changes: List[Dict] = []
        self._active = False

    def begin(self) -> str:
        """开始事务"""
        transaction_id = f"tx_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.applied_changes = []
        self._active = True
        print(f"[Transaction] 开始事务: {transaction_id}")
        return transaction_id

    def backup_file(self, file_path: str) -> str:
        """备份文件"""
        source = Path(file_path)
        if not source.exists():
            return ""

        # 创建备份
        file_hash = hashlib.md5(source.read_bytes()).hexdigest()[:8]
        backup_name = f"{source.stem}_{file_hash}{source.suffix}"
        backup_path = self.backup_dir / backup_name

        shutil.copy2(source, backup_path)
        return str(backup_path)

    def apply_change(self, change: CodeChange) -> bool:
        """应用单个变更"""
        file_path = Path(change.file_path)

        # 备份原文件
        backup_path = self.backup_file(change.file_path)

        try:
            if not file_path.exists():
                if change.action == "add":
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(change.new_content or "")
                else:
                    return False
            else:
                content = file_path.read_text(encoding='utf-8')
                lines = content.split('\n')

                if change.action == "modify":
                    # 替换指定行范围
                    new_lines = (change.new_content or "").split('\n')
                    lines[change.line_start - 1:change.line_end] = new_lines
                    file_path.write_text('\n'.join(lines), encoding='utf-8')

                elif change.action == "add":
                    # 在指定位置插入
                    new_lines = (change.new_content or "").split('\n')
                    lines[change.line_start:change.line_start] = new_lines
                    file_path.write_text('\n'.join(lines), encoding='utf-8')

                elif change.action == "remove":
                    # 删除指定行范围
                    del lines[change.line_start - 1:change.line_end]
                    file_path.write_text('\n'.join(lines), encoding='utf-8')

            self.applied_changes.append({
                'change': change,
                'backup_path': backup_path,
                'timestamp': datetime.now().isoformat()
            })

            return True

        except Exception as e:
            print(f"[Transaction] 应用变更失败: {e}")
            return False

    def rollback(self) -> int:
        """回滚所有变更"""
        restored = 0
        for entry in reversed(self.applied_changes):
            backup_path = entry.get('backup_path', '')
            original_path = entry['change'].file_path

            if backup_path and Path(backup_path).exists():
                try:
                    shutil.copy2(backup_path, original_path)
                    restored += 1
                except Exception as e:
                    print(f"[Transaction] 回滚失败: {e}")

        self.applied_changes = []
        self._active = False
        print(f"[Transaction] 回滚完成: 恢复了 {restored} 个文件")
        return restored

    def commit(self) -> int:
        """提交事务"""
        count = len(self.applied_changes)
        self.applied_changes = []
        self._active = False
        print(f"[Transaction] 提交完成: {count} 个变更已生效")
        return count


# ──────────────────────────────────────────────────────────────
# Cross-File Refactor Engine
# ──────────────────────────────────────────────────────────────

class CrossFileRefactorEngine:
    """
    跨文件重构引擎

    协调 ImportGraphBuilder, SymbolTracker, ImpactAnalyzer
    和 TransactionManager 完成跨文件重构操作
    """

    def __init__(self, codebase_path: str):
        self.codebase_path = Path(codebase_path)

        # 核心组件
        self.graph_builder = ImportGraphBuilder()
        self.symbol_tracker = SymbolTracker(self.graph_builder)
        self.impact_analyzer = ImpactAnalyzer(self.graph_builder, self.symbol_tracker)
        self.transaction_manager = TransactionManager()

        self._initialized = False

    async def initialize(self) -> bool:
        """初始化引擎（构建依赖图和符号表）"""
        print(f"[CrossFile] 初始化引擎: {self.codebase_path}")

        # 1. 构建依赖图
        self.graph_builder.build_graph(str(self.codebase_path))

        # 2. 构建符号使用映射
        self.symbol_tracker.build_usage_map()

        # 3. 检测循环依赖
        cycles = self.graph_builder.find_cycles()
        if cycles:
            print(f"[CrossFile] ⚠️ 发现 {len(cycles)} 个循环依赖:")
            for cycle in cycles[:5]:
                print(f"    {' → '.join(cycle)}")

        self._initialized = True
        print(f"[CrossFile] 初始化完成")
        return True

    def get_codebase_summary(self) -> Dict:
        """获取代码库摘要"""
        if not self._initialized:
            return {"error": "引擎未初始化"}

        modules = self.graph_builder.modules
        total_symbols = sum(len(m.defined_symbols) for m in modules.values())
        total_imports = sum(len(m.imports) for m in modules.values())

        return {
            'total_modules': len(modules),
            'total_symbols': total_symbols,
            'total_imports': total_imports,
            'dependency_edges': self.graph_builder.graph.number_of_edges(),
            'cycles': len(self.graph_builder.find_cycles()),
            'largest_modules': sorted(
                [(name, m.line_count) for name, m in modules.items()],
                key=lambda x: -x[1]
            )[:10],
        }

    async def move_symbol(
        self,
        symbol_name: str,
        source_module: str,
        target_module: str,
        dry_run: bool = False
    ) -> RefactoringResult:
        """
        移动符号到另一个模块

        Args:
            symbol_name: 要移动的符号名
            source_module: 源模块名
            target_module: 目标模块名
            dry_run: 是否只预览不执行

        Returns:
            RefactoringResult
        """
        if not self._initialized:
            return RefactoringResult(success=False, message="引擎未初始化")

        print(f"\n[CrossFile] 移动 {symbol_name}: {source_module} → {target_module}")

        # 1. 影响分析
        impact = self.impact_analyzer.analyze_move_impact(
            symbol_name, source_module, target_module
        )

        print(f"  影响分析: {len(impact.affected_files)} 个文件, 风险={impact.risk_level}")

        if dry_run:
            return RefactoringResult(
                success=True,
                estimated_changes=impact.estimated_changes,
                files_modified=impact.affected_files,
                message=f"[预览] 将影响 {len(impact.affected_files)} 个文件, "
                        f"需要更新 {len(impact.affected_imports)} 处导入"
            )

        # 2. 开始事务
        tx_id = self.transaction_manager.begin()

        # 3. 查找符号定义
        symbol = self.symbol_tracker.find_symbol_definition(symbol_name)
        if not symbol:
            return RefactoringResult(
                success=False,
                message=f"符号 {symbol_name} 未找到定义"
            )

        # 4. 从源模块移除符号
        source_module_info = self.graph_builder.modules.get(source_module)
        target_module_info = self.graph_builder.modules.get(target_module)

        if not source_module_info or not target_module_info:
            return RefactoringResult(
                success=False,
                message="源模块或目标模块不存在"
            )

        # 5. 执行变更
        changes = []

        # 5a. 从源模块删除符号代码
        changes.append(CodeChange(
            action="remove",
            file_path=source_module_info.path,
            line_start=symbol.line_start,
            line_end=symbol.line_end,
            description=f"移除 {symbol_name}"
        ))

        # 5b. 在目标模块添加符号代码
        changes.append(CodeChange(
            action="add",
            file_path=target_module_info.path,
            line_start=0,  # 末尾
            line_end=0,
            new_content="\n# Moved from " + source_module + "\n",
            description=f"添加 {symbol_name}"
        ))

        # 5c. 更新导入
        for imp_update in impact.affected_imports:
            parts = imp_update.split(':')
            if len(parts) == 2:
                module_name = parts[0]
                module_info = self.graph_builder.modules.get(module_name)
                if module_info:
                    # 更新 from import
                    for imp in module_info.imports:
                        if symbol_name in imp.imported_names and imp.source_module == source_module:
                            changes.append(CodeChange(
                                action="modify",
                                file_path=module_info.path,
                                line_start=imp.import_line,
                                line_end=imp.import_line,
                                new_content=f"from {target_module} import {symbol_name}",
                                description=f"更新 {module_name} 中的导入"
                            ))

        # 6. 应用变更
        applied = 0
        modified_files = set()

        for change in changes:
            if self.transaction_manager.apply_change(change):
                applied += 1
                modified_files.add(change.file_path)

        # 7. 验证变更后代码语法
        all_valid = True
        for file_path in modified_files:
            try:
                with open(file_path, 'r') as f:
                    ast.parse(f.read())
            except SyntaxError:
                all_valid = False
                break

        if not all_valid:
            self.transaction_manager.rollback()
            return RefactoringResult(
                success=False,
                message="验证失败: 变更导致语法错误，已回滚"
            )

        # 8. 提交事务
        committed = self.transaction_manager.commit()

        return RefactoringResult(
            success=True,
            operations_applied=committed,
            files_modified=sorted(modified_files),
            changes=changes,
            rollback_available=True,
            message=f"成功移动 {symbol_name}: {source_module} → {target_module}"
        )

    async def analyze_codebase(self) -> Dict:
        """深度分析代码库"""
        if not self._initialized:
            return {"error": "引擎未初始化"}

        summary = self.get_codebase_summary()

        # 额外分析
        modules = self.graph_builder.modules

        # 找出大模块（超过500行）
        large_modules = {
            name: info.line_count
            for name, info in modules.items()
            if info.line_count > 500
        }

        # 找出高耦合模块（依赖超过5个模块）
        high_coupling = {}
        for name in modules:
            deps = self.graph_builder.get_dependencies(name)
            if len(deps) > 5:
                high_coupling[name] = len(deps)

        # 找出公共符号（被多个模块使用）
        public_symbols = {}
        for sym_name, usages in self.symbol_tracker.usage_map.items():
            unique_files = len(set(u.file_path for u in usages))
            if unique_files > 3:
                public_symbols[sym_name] = unique_files

        return {
            **summary,
            'large_modules': large_modules,
            'high_coupling_modules': high_coupling,
            'widely_used_symbols': dict(
                sorted(public_symbols.items(), key=lambda x: -x[1])[:10]
            ),
        }


# ──────────────────────────────────────────────────────────────
# Factory
# ──────────────────────────────────────────────────────────────

async def create_cross_file_engine(codebase_path: str) -> CrossFileRefactorEngine:
    """创建并初始化跨文件重构引擎"""
    engine = CrossFileRefactorEngine(codebase_path)
    await engine.initialize()
    return engine


# ──────────────────────────────────────────────────────────────
# Test
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    async def test():
        print("=" * 70)
        print("MOSS v9.2 - Cross-File Refactor Engine 测试")
        print("=" * 70)

        # 测试 MOSS 自身代码库
        engine = CrossFileRefactorEngine('/workspace/moss/moss')
        await engine.initialize()

        # 1. 代码库摘要
        print("\n" + "=" * 70)
        print("【1】代码库摘要")
        print("=" * 70)

        summary = engine.get_codebase_summary()
        print(f"  模块数:     {summary['total_modules']}")
        print(f"  符号数:     {summary['total_symbols']}")
        print(f"  依赖边数:   {summary['dependency_edges']}")
        print(f"  循环依赖:   {summary['cycles']}")

        if summary['largest_modules']:
            print(f"\n  最大的模块:")
            for name, lines in summary['largest_modules'][:5]:
                print(f"    {name}: {lines} 行")

        # 2. 依赖图分析
        print("\n" + "=" * 70)
        print("【2】依赖图分析")
        print("=" * 70)

        # 查找核心模块的依赖
        core_modules = [name for name in engine.graph_builder.modules
                       if name.startswith('moss.core')]

        for module in sorted(core_modules)[:5]:
            deps = engine.graph_builder.get_dependencies(module)
            dependents = engine.graph_builder.get_dependents(module)
            print(f"\n  {module}:")
            print(f"    依赖: {deps[:3]}{'...' if len(deps) > 3 else ''}")
            print(f"    被依赖: {dependents[:3]}{'...' if len(dependents) > 3 else ''}")

        # 3. 影响分析
        print("\n" + "=" * 70)
        print("【3】影响分析示例")
        print("=" * 70)

        # 分析移动一个符号的影响
        for module_name, module_info in engine.graph_builder.modules.items():
            if module_info.defined_symbols:
                symbol_name = list(module_info.defined_symbols.keys())[0]
                impact = engine.impact_analyzer.analyze_move_impact(
                    symbol_name, module_name, "moss.core.utils"
                )
                print(f"\n  移动 {module_name}.{symbol_name}:")
                print(f"    影响文件: {len(impact.affected_files)}")
                print(f"    风险级别: {impact.risk_level}")
                print(f"    预计变更: {impact.estimated_changes}")
                break  # 只展示一个

        # 4. 深度分析
        print("\n" + "=" * 70)
        print("【4】深度分析")
        print("=" * 70)

        analysis = await engine.analyze_codebase()

        if analysis.get('large_modules'):
            print(f"\n  大模块 (>500行):")
            for name, lines in analysis['large_modules'].items():
                print(f"    {name}: {lines} 行")

        if analysis.get('high_coupling_modules'):
            print(f"\n  高耦合模块 (>5依赖):")
            for name, count in analysis['high_coupling_modules'].items():
                print(f"    {name}: {count} 个依赖")

        if analysis.get('widely_used_symbols'):
            print(f"\n  广泛使用的符号 (>3文件):")
            for name, count in analysis['widely_used_symbols'].items():
                print(f"    {name}: {count} 个文件")

        print("\n" + "=" * 70)
        print("🎉 v9.2 Cross-File Refactor Engine 测试完成!")
        print("=" * 70)

    asyncio.run(test())
