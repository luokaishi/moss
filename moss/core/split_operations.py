#!/usr/bin/env python3
"""
MOSS v9.2 - Module Split Operations
模块拆分操作 - 将大模块拆分为多个子模块

Author: MOSS v9.2
Date: 2026-04-23
"""

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class SplitPlan:
    """模块拆分计划"""
    original_module: str
    original_path: str
    new_modules: List['NewModule']
    import_updates: List['ImportUpdate']


@dataclass
class NewModule:
    """新模块定义"""
    name: str
    path: str
    symbols: List[str]
    imports: List[str]


@dataclass
class ImportUpdate:
    """导入更新"""
    file_path: str
    old_import: str
    new_import: str


class ModuleAnalyzer:
    """模块分析器 - 分析大模块的拆分机会"""

    def analyze_module(self, file_path: str) -> Optional['ModuleAnalysis']:
        """分析模块结构"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return None

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return None

        # 收集所有顶层定义
        functions = []
        classes = []
        imports = []
        constants = []

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    'name': node.name,
                    'line_start': node.lineno,
                    'line_end': node.end_lineno or node.lineno,
                    'docstring': ast.get_docstring(node),
                })
            elif isinstance(node, ast.ClassDef):
                classes.append({
                    'name': node.name,
                    'line_start': node.lineno,
                    'line_end': node.end_lineno or node.lineno,
                    'methods': [m.name for m in node.body if isinstance(m, ast.FunctionDef)],
                })
            elif isinstance(node, ast.Import):
                imports.append(f"import {', '.join(a.name for a in node.names)}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [a.name for a in node.names]
                imports.append(f"from {node.module} import {', '.join(names)}")
            elif isinstance(node, ast.Assign):
                # 检查是否是常量
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        constants.append({
                            'name': target.id,
                            'line': node.lineno
                        })

        return ModuleAnalysis(
            file_path=file_path,
            total_lines=len(content.split('\n')),
            functions=functions,
            classes=classes,
            imports=imports,
            constants=constants
        )

    def suggest_split_strategy(self, analysis: 'ModuleAnalysis') -> List['SplitSuggestion']:
        """建议拆分策略"""
        suggestions = []

        # 策略1: 按类型拆分 (functions vs classes)
        if len(analysis.functions) > 5 and len(analysis.classes) > 3:
            suggestions.append(SplitSuggestion(
                name="by_type",
                description="按类型拆分：functions.py 和 classes.py",
                new_modules=[
                    f"{analysis.module_name}_functions",
                    f"{analysis.module_name}_classes"
                ],
                confidence=0.8
            ))

        # 策略2: 按功能分组（基于命名前缀）
        prefixes = self._extract_prefixes(
            [f['name'] for f in analysis.functions] +
            [c['name'] for c in analysis.classes]
        )
        if len(prefixes) >= 2:
            for prefix in prefixes[:3]:  # 最多3个前缀分组
                suggestions.append(SplitSuggestion(
                    name=f"by_prefix_{prefix}",
                    description=f"按前缀 '{prefix}' 分组",
                    new_modules=[f"{analysis.module_name}_{prefix}"],
                    confidence=0.6
                ))

        # 策略3: 提取大型类到单独模块
        large_classes = [c for c in analysis.classes if c['line_end'] - c['line_start'] > 100]
        if large_classes:
            suggestions.append(SplitSuggestion(
                name="extract_large_classes",
                description=f"提取 {len(large_classes)} 个大类到单独模块",
                new_modules=[f"{analysis.module_name}_{c['name'].lower()}" for c in large_classes[:3]],
                confidence=0.9
            ))

        return suggestions

    def _extract_prefixes(self, names: List[str]) -> List[str]:
        """从名称中提取公共前缀"""
        prefixes = {}
        for name in names:
            parts = re.split(r'[_A-Z]', name)
            if parts and parts[0]:
                prefix = parts[0].lower()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1

        # 返回出现次数>2的前缀
        return [p for p, c in prefixes.items() if c > 2]


@dataclass
class ModuleAnalysis:
    """模块分析结果"""
    file_path: str
    total_lines: int
    functions: List[Dict]
    classes: List[Dict]
    imports: List[str]
    constants: List[Dict]

    @property
    def module_name(self) -> str:
        return Path(self.file_path).stem


@dataclass
class SplitSuggestion:
    """拆分建议"""
    name: str
    description: str
    new_modules: List[str]
    confidence: float


class SplitExecutor:
    """模块拆分执行器"""

    def __init__(self, source_extractor):
        self.extractor = source_extractor

    async def split_by_type(
        self,
        module_path: str,
        dry_run: bool = False
    ) -> Dict:
        """
        按类型拆分模块：functions 和 classes 分开

        例如:
        utils.py (1000行) → utils_functions.py + utils_classes.py
        """
        analyzer = ModuleAnalyzer()
        analysis = analyzer.analyze_module(module_path)

        if not analysis:
            return {'success': False, 'message': '无法分析模块'}

        if len(analysis.functions) < 3 and len(analysis.classes) < 2:
            return {'success': False, 'message': '模块太小，不需要拆分'}

        base_path = Path(module_path).parent
        base_name = Path(module_path).stem

        # 创建新模块路径
        functions_path = base_path / f"{base_name}_functions.py"
        classes_path = base_path / f"{base_name}_classes.py"

        if dry_run:
            return {
                'success': True,
                'dry_run': True,
                'message': f'[预览] 将拆分 {base_name}.py',
                'new_files': [
                    str(functions_path),
                    str(classes_path)
                ],
                'functions_count': len(analysis.functions),
                'classes_count': len(analysis.classes)
            }

        # 实际执行拆分
        try:
            # 1. 创建 functions 模块
            functions_content = self._build_functions_module(analysis)
            functions_path.write_text(functions_content, encoding='utf-8')

            # 2. 创建 classes 模块
            classes_content = self._build_classes_module(analysis)
            classes_path.write_text(classes_content, encoding='utf-8')

            # 3. 更新原模块为聚合模块
            aggregate_content = self._build_aggregate_module(
                base_name, analysis.imports
            )
            Path(module_path).write_text(aggregate_content, encoding='utf-8')

            return {
                'success': True,
                'message': f'成功拆分 {base_name}.py',
                'new_files': [str(functions_path), str(classes_path)],
                'modified_files': [module_path]
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'拆分失败: {e}'
            }

    async def extract_large_classes(
        self,
        module_path: str,
        min_lines: int = 100,
        dry_run: bool = False
    ) -> Dict:
        """
        提取大到一个单独模块
        """
        analyzer = ModuleAnalyzer()
        analysis = analyzer.analyze_module(module_path)

        if not analysis:
            return {'success': False, 'message': '无法分析模块'}

        large_classes = [
            c for c in analysis.classes
            if c['line_end'] - c['line_start'] > min_lines
        ]

        if not large_classes:
            return {
                'success': False,
                'message': f'没有超过 {min_lines} 行的大类'
            }

        base_path = Path(module_path).parent
        base_name = Path(module_path).stem

        extracted = []

        for cls in large_classes:
            new_module_name = f"{base_name}_{cls['name'].lower()}"
            new_path = base_path / f"{new_module_name}.py"

            if dry_run:
                extracted.append({
                    'class': cls['name'],
                    'new_module': new_module_name,
                    'lines': cls['line_end'] - cls['line_start']
                })
                continue

            # 提取类源码
            class_source = self.extractor.extract_symbol_source(module_path, cls['name'])
            if class_source:
                # 添加必要的导入
                full_content = self._add_required_imports(
                    class_source, analysis.imports
                )
                new_path.write_text(full_content, encoding='utf-8')
                extracted.append(str(new_path))

        if dry_run:
            return {
                'success': True,
                'dry_run': True,
                'message': f'[预览] 将提取 {len(extracted)} 个大类',
                'extracted': extracted
            }

        return {
            'success': True,
            'message': f'成功提取 {len(extracted)} 个大类',
            'new_files': extracted
        }

    async def create_package(
        self,
        module_path: str,
        dry_run: bool = False
    ) -> Dict:
        """
        将大模块转换为包

        例如:
        utils.py (2000行) → utils/__init__.py + utils/core.py + utils/helpers.py
        """
        analyzer = ModuleAnalyzer()
        analysis = analyzer.analyze_module(module_path)

        if not analysis:
            return {'success': False, 'message': '无法分析模块'}

        if analysis.total_lines < 500:
            return {'success': False, 'message': '模块太小，不需要转换为包'}

        base_path = Path(module_path).parent
        module_name = Path(module_path).stem
        package_path = base_path / module_name

        if dry_run:
            return {
                'success': True,
                'dry_run': True,
                'message': f'[预览] 将创建包 {module_name}/',
                'package_path': str(package_path),
                'structure': [
                    f'{module_name}/__init__.py',
                    f'{module_name}/core.py',
                    f'{module_name}/helpers.py'
                ]
            }

        try:
            # 1. 创建包目录
            package_path.mkdir(exist_ok=True)

            # 2. 创建 __init__.py
            init_content = self._build_init_module(analysis)
            (package_path / '__init__.py').write_text(init_content, encoding='utf-8')

            # 3. 拆分到子模块
            self._split_to_package_modules(analysis, package_path)

            # 4. 备份原文件（不删除，供参考）
            backup_path = base_path / f"{module_name}_backup.py"
            Path(module_path).rename(backup_path)

            return {
                'success': True,
                'message': f'成功创建包 {module_name}/',
                'package_path': str(package_path),
                'backup': str(backup_path)
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'创建包失败: {e}'
            }

    def _build_functions_module(self, analysis: ModuleAnalysis) -> str:
        """构建函数模块"""
        lines = [
            f'"""',
            f'{analysis.module_name} - Functions',
            f'Auto-generated by MOSS v9.2',
            f'"""',
            ''
        ]

        # 添加原始导入
        lines.extend(analysis.imports)
        lines.append('')

        # 提取所有函数
        try:
            with open(analysis.file_path, 'r') as f:
                content = f.read()

            for func in analysis.functions:
                source = self.extractor.extract_symbol_source(analysis.file_path, func['name'])
                if source:
                    lines.append(source)
                    lines.append('')
        except Exception:
            pass

        return '\n'.join(lines)

    def _build_classes_module(self, analysis: ModuleAnalysis) -> str:
        """构建类模块"""
        lines = [
            f'"""',
            f'{analysis.module_name} - Classes',
            f'Auto-generated by MOSS v9.2',
            f'"""',
            ''
        ]

        lines.extend(analysis.imports)
        lines.append('')

        try:
            with open(analysis.file_path, 'r') as f:
                content = f.read()

            for cls in analysis.classes:
                source = self.extractor.extract_symbol_source(analysis.file_path, cls['name'])
                if source:
                    lines.append(source)
                    lines.append('')
        except Exception:
            pass

        return '\n'.join(lines)

    def _build_aggregate_module(self, base_name: str, imports: List[str]) -> str:
        """构建聚合模块（重新导出）"""
        lines = [
            f'"""',
            f'{base_name} - Aggregated Module',
            f'Auto-generated by MOSS v9.2',
            f'"""',
            ''
        ]

        # 从子模块重新导出
        lines.append(f'from {base_name}_functions import *')
        lines.append(f'from {base_name}_classes import *')
        lines.append('')

        return '\n'.join(lines)

    def _add_required_imports(self, source: str, available_imports: List[str]) -> str:
        """为提取的源码添加必要的导入"""
        lines = ['"""Auto-extracted by MOSS v9.2"""', '']
        lines.extend(available_imports)
        lines.append('')
        lines.append(source)
        return '\n'.join(lines)

    def _build_init_module(self, analysis: ModuleAnalysis) -> str:
        """构建包的 __init__.py"""
        lines = [
            f'"""',
            f'{analysis.module_name} Package',
            f'Auto-generated by MOSS v9.2',
            f'"""',
            ''
        ]

        # 从子模块导入
        lines.append('from .core import *')
        lines.append('from .helpers import *')
        lines.append('')

        # __all__ 定义
        all_exports = [f"'{f['name']}'" for f in analysis.functions]
        all_exports.extend([f"'{c['name']}'" for c in analysis.classes])
        lines.append(f"__all__ = [{', '.join(all_exports)}]")
        lines.append('')

        return '\n'.join(lines)

    def _split_to_package_modules(self, analysis: ModuleAnalysis, package_path: Path):
        """将内容拆分到包的子模块"""
        # core.py - 主要函数和类
        core_lines = ['"""Core functionality"""', '']
        core_lines.extend(analysis.imports)
        core_lines.append('')

        # helpers.py - 辅助函数
        helper_lines = ['"""Helper functions"""', '']
        helper_lines.extend(analysis.imports)
        helper_lines.append('')

        # 简单拆分：前一半函数放core，后一半放helpers
        mid = len(analysis.functions) // 2

        try:
            with open(analysis.file_path, 'r') as f:
                content = f.read()

            for i, func in enumerate(analysis.functions):
                source = self.extractor.extract_symbol_source(analysis.file_path, func['name'])
                if source:
                    if i < mid:
                        core_lines.append(source)
                        core_lines.append('')
                    else:
                        helper_lines.append(source)
                        helper_lines.append('')

            # 类都放core
            for cls in analysis.classes:
                source = self.extractor.extract_symbol_source(analysis.file_path, cls['name'])
                if source:
                    core_lines.append(source)
                    core_lines.append('')

        except Exception:
            pass

        (package_path / 'core.py').write_text('\n'.join(core_lines), encoding='utf-8')
        (package_path / 'helpers.py').write_text('\n'.join(helper_lines), encoding='utf-8')


# 测试
if __name__ == "__main__":
    import asyncio

    async def test():
        print("=" * 60)
        print("MOSS v9.2 - Module Split Operations 测试")
        print("=" * 60)

        # 分析一个大模块
        from moss.core.move_operations import SourceExtractor

        test_file = '/workspace/moss/moss/core/self_modification_engine.py'

        analyzer = ModuleAnalyzer()
        analysis = analyzer.analyze_module(test_file)

        if analysis:
            print(f"\n[分析结果] {Path(test_file).name}")
            print(f"  总行数: {analysis.total_lines}")
            print(f"  函数数: {len(analysis.functions)}")
            print(f"  类数:   {len(analysis.classes)}")
            print(f"  导入数: {len(analysis.imports)}")

            # 建议拆分策略
            suggestions = analyzer.suggest_split_strategy(analysis)
            print(f"\n[拆分建议]")
            for s in suggestions:
                print(f"  • {s.description} (置信度: {s.confidence:.0%})")

            # 预览拆分
            executor = SplitExecutor(SourceExtractor())

            print(f"\n[预览: 按类型拆分]")
            result = await executor.split_by_type(test_file, dry_run=True)
            print(f"  {result['message']}")
            print(f"  新文件: {result.get('new_files', [])}")

            print(f"\n[预览: 提取大类]")
            result = await executor.extract_large_classes(test_file, min_lines=100, dry_run=True)
            print(f"  {result['message']}")
            if 'extracted' in result:
                for e in result['extracted']:
                    print(f"    - {e['class']}: {e['lines']} 行 → {e['new_module']}")

            print(f"\n[预览: 创建包]")
            result = await executor.create_package(test_file, dry_run=True)
            print(f"  {result['message']}")
            print(f"  结构: {result.get('structure', [])}")

        print("\n测试完成!")

    asyncio.run(test())
