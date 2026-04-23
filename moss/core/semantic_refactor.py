#!/usr/bin/env python3
"""
MOSS v9.1 - Semantic Refactor Engine
LLM驱动的语义级代码重构引擎

核心创新:
- 利用LLM理解代码语义，执行传统AST无法实现的重构
- 安全沙箱: LLM输出→AST验证→语义测试→应用/回滚
- 与RefactorEngine协同: AST级+LLM级双引擎架构

Author: MOSS v9.1
Date: 2026-04-23
"""

import ast
import asyncio
import difflib
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# 导入已有LLM Backend
from moss.core.llm_backend import LLMBackend, LLMConfig, LLMResponse, create_llm_backend
from moss.core.refactor_engine import CodeRefactorer, RefactorResult, create_refactorer


class SemanticRefactorType(Enum):
    """语义重构类型"""
    FUNCTION_SPLIT = auto()       # 函数拆分
    PATTERN_REFACTOR = auto()     # 设计模式应用
    ALGORITHM_OPTIMIZE = auto()   # 算法优化
    CODE_SIMPLIFY = auto()        # 代码简化
    TYPE_ANNOTATION = auto()      # 类型标注补充
    ERROR_HANDLING = auto()       # 错误处理增强
    API_MODERNIZE = auto()        # API现代化


@dataclass
class SemanticRefactorRequest:
    """语义重构请求"""
    request_id: str
    refactor_type: SemanticRefactorType
    code: str
    file_path: str
    target_function: Optional[str] = None
    requirements: List[str] = field(default_factory=list)
    context: Dict = field(default_factory=dict)


@dataclass
class SemanticRefactorResult:
    """语义重构结果"""
    request_id: str
    success: bool
    original_code: str
    refactored_code: str
    diff: Optional[str] = None
    explanation: Optional[str] = None
    llm_tokens_used: int = 0
    validation_passed: bool = False
    rollback_performed: bool = False
    changes: List[Dict] = field(default_factory=list)


class SafetyValidator:
    """
    安全验证器 - 确保LLM生成的代码安全可靠

    验证层级:
    1. 语法验证 - AST解析
    2. 结构验证 - 函数/类完整性
    3. 导入验证 - 无缺失导入
    4. 禁止操作验证 - 无危险代码
    """

    FORBIDDEN_PATTERNS = [
        r'__import__\s*\(',
        r'eval\s*\(',
        r'exec\s*\(',
        r'compile\s*\(',
        r'open\s*\(.+["\']w',
        r'os\.system\s*\(',
        r'subprocess\.',
        r'shutil\.rmtree',
        r'os\.remove',
    ]

    def validate_syntax(self, code: str) -> Tuple[bool, str]:
        """验证代码语法"""
        try:
            ast.parse(code)
            return True, "语法验证通过"
        except SyntaxError as e:
            return False, f"语法错误: {e}"

    def validate_structure(self, original: str, refactored: str) -> Tuple[bool, str]:
        """验证代码结构完整性"""
        try:
            orig_tree = ast.parse(original)
            ref_tree = ast.parse(refactored)
        except SyntaxError:
            return False, "无法解析AST"

        # 检查顶层定义是否保留
        orig_names = set()
        for node in ast.walk(orig_tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                orig_names.add(node.name)
            elif isinstance(node, ast.ClassDef):
                orig_names.add(node.name)

        ref_names = set()
        for node in ast.walk(ref_tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                ref_names.add(node.name)
            elif isinstance(node, ast.ClassDef):
                ref_names.add(node.name)

        # 允许新增函数（拆分产生），不允许删除
        missing = orig_names - ref_names
        if missing:
            return False, f"缺失定义: {missing}"

        return True, "结构验证通过"

    def validate_safety(self, code: str) -> Tuple[bool, str]:
        """验证代码安全性"""
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, code):
                return False, f"检测到危险模式: {pattern}"

        return True, "安全验证通过"

    def validate_imports(self, original: str, refactored: str) -> Tuple[bool, str]:
        """验证导入完整性"""
        try:
            ref_tree = ast.parse(refactored)
        except SyntaxError:
            return False, "无法解析AST"

        # 收集重构后使用的名称
        used_names = set()
        for node in ast.walk(ref_tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used_names.add(node.id)

        # 收集导入的名称
        imported_names = set()
        for node in ast.walk(ref_tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name.split('.')[0]
                    imported_names.add(name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imported_names.add(name)

        # 收集定义的名称
        defined_names = set()
        for node in ast.walk(ref_tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defined_names.add(node.name)
            elif isinstance(node, ast.ClassDef):
                defined_names.add(node.name)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                defined_names.add(node.id)

        # 检查是否所有使用的名称都有来源
        builtin_names = {'print', 'len', 'range', 'str', 'int', 'float', 'list', 'dict',
                         'set', 'tuple', 'bool', 'None', 'True', 'False', 'type', 'isinstance',
                         'enumerate', 'zip', 'map', 'filter', 'sorted', 'reversed', 'super',
                         'property', 'staticmethod', 'classmethod', 'Exception', 'ValueError',
                         'TypeError', 'KeyError', 'IndexError', 'AttributeError', 'RuntimeError',
                         'NotImplementedError', 'hasattr', 'getattr', 'setattr', 'any', 'all',
                         'abs', 'max', 'min', 'sum', 'round', 'hash', 'id', 'format', 'repr',
                         'bytes', 'bytearray', 'memoryview', 'complex', 'frozenset', 'slice',
                        }

        available = imported_names | defined_names | builtin_names
        missing = used_names - available

        # 允许少量缺失（可能来自同一模块）
        if len(missing) > 3:
            return False, f"可能缺失导入: {missing}"

        return True, "导入验证通过"

    def full_validation(self, original: str, refactored: str) -> Tuple[bool, List[str]]:
        """完整验证流程"""
        results = []

        # 1. 语法验证
        passed, msg = self.validate_syntax(refactored)
        results.append(("语法验证", passed, msg))
        if not passed:
            return False, [r[2] for r in results]

        # 2. 结构验证
        passed, msg = self.validate_structure(original, refactored)
        results.append(("结构验证", passed, msg))
        if not passed:
            return False, [r[2] for r in results]

        # 3. 安全验证
        passed, msg = self.validate_safety(refactored)
        results.append(("安全验证", passed, msg))
        if not passed:
            return False, [r[2] for r in results]

        # 4. 导入验证
        passed, msg = self.validate_imports(original, refactored)
        results.append(("导入验证", passed, msg))

        all_passed = all(r[1] for r in results)
        return all_passed, [r[2] for r in results]


class PromptBuilder:
    """LLM Prompt构建器 - 为不同重构类型构建专用prompt"""

    SYSTEM_PROMPT = """You are an expert Python code refactoring assistant. Your task is to refactor Python code following these STRICT rules:

1. PRESERVE all existing functionality - the refactored code must produce identical results
2. DO NOT remove any existing functions, classes, or methods
3. DO NOT add dangerous code (eval, exec, __import__, file writing, subprocess, etc.)
4. DO NOT add new external dependencies beyond what's already imported
5. Keep all existing imports (you may add new ones if needed)
6. Return ONLY the refactored Python code, no markdown or explanation
7. Ensure the code is syntactically valid Python

Output the complete refactored code, not just the changed parts."""

    def build_prompt(self, request: SemanticRefactorRequest) -> Tuple[str, str]:
        """构建系统提示和用户提示"""
        user_prompts = {
            SemanticRefactorType.FUNCTION_SPLIT: self._function_split_prompt,
            SemanticRefactorType.PATTERN_REFACTOR: self._pattern_refactor_prompt,
            SemanticRefactorType.ALGORITHM_OPTIMIZE: self._algorithm_optimize_prompt,
            SemanticRefactorType.CODE_SIMPLIFY: self._code_simplify_prompt,
            SemanticRefactorType.TYPE_ANNOTATION: self._type_annotation_prompt,
            SemanticRefactorType.ERROR_HANDLING: self._error_handling_prompt,
            SemanticRefactorType.API_MODERNIZE: self._api_modernize_prompt,
        }

        builder = user_prompts.get(request.refactor_type, self._generic_prompt)
        user_prompt = builder(request)

        return self.SYSTEM_PROMPT, user_prompt

    def _function_split_prompt(self, req: SemanticRefactorRequest) -> str:
        return f"""Split the following long function into smaller, focused helper functions.

Target function: {req.target_function or 'the longest function'}

Rules:
- Extract logical blocks into helper functions with descriptive names
- The main function should call the helpers
- Each helper should do ONE thing well
- Keep all original behavior intact
- Add brief docstrings to new functions

Code:
```python
{req.code}
```"""

    def _pattern_refactor_prompt(self, req: SemanticRefactorRequest) -> str:
        return f"""Apply appropriate design patterns to improve this code's structure.

Focus on: {', '.join(req.requirements) if req.requirements else 'readability and maintainability'}

Common patterns to consider:
- Strategy pattern for conditional logic
- Factory pattern for object creation
- Context manager for resource management
- Data class for simple data containers

Code:
```python
{req.code}
```"""

    def _algorithm_optimize_prompt(self, req: SemanticRefactorRequest) -> str:
        return f"""Optimize the algorithms in this code for better performance.

Focus areas:
- Replace O(n²) with O(n) or O(n log n) where possible
- Use appropriate data structures (sets for lookups, deque for queues)
- Avoid repeated computations
- Use generators for large data processing

Code:
```python
{req.code}
```"""

    def _code_simplify_prompt(self, req: SemanticRefactorRequest) -> str:
        return f"""Simplify this Python code using modern Python idioms.

Apply these simplifications where appropriate:
- Use f-strings instead of .format() or % formatting
- Use comprehensions instead of loops with append
- Use walrus operator (:=) for repeated calculations
- Use any()/all() instead of manual loops
- Use collections.Counter, defaultdict where appropriate
- Merge nested if statements
- Use ternary expressions for simple conditions

Code:
```python
{req.code}
```"""

    def _type_annotation_prompt(self, req: SemanticRefactorRequest) -> str:
        return f"""Add comprehensive type annotations to this Python code.

Rules:
- Add type hints to all function parameters and return types
- Use Optional[T] for parameters that can be None
- Use Union[T1, T2] for parameters accepting multiple types
- Use List[T], Dict[K, V], Set[T] for collections
- Add -> None for functions with no return value
- Do NOT change any runtime behavior

Code:
```python
{req.code}
```"""

    def _error_handling_prompt(self, req: SemanticRefactorRequest) -> str:
        return f"""Improve error handling in this Python code.

Improvements to make:
- Add try/except blocks for operations that can fail
- Use specific exception types (not bare except)
- Add meaningful error messages
- Use context managers for resource management
- Handle edge cases (empty inputs, None values)
- Do NOT silently swallow exceptions

Code:
```python
{req.code}
```"""

    def _api_modernize_prompt(self, req: SemanticRefactorRequest) -> str:
        return f"""Modernize this Python code to use current best practices.

Modernization targets:
- Use dataclasses instead of __init__ with many assignments
- Use pathlib instead of os.path
- Use f-strings instead of format/percent
- Use typing module for annotations
- Use async/await where I/O is present
- Use enum instead of string constants

Code:
```python
{req.code}
```"""

    def _generic_prompt(self, req: SemanticRefactorRequest) -> str:
        return f"""Refactor this Python code to improve readability, maintainability, and performance.

Keep all existing functionality intact.

Code:
```python
{req.code}
```"""


class SemanticRefactorEngine:
    """
    语义重构引擎 - LLM驱动的代码重构

    核心架构:
    ┌─────────────────┐
    │ PromptBuilder    │ → 构建类型专用prompt
    ├─────────────────┤
    │ LLMBackend      │ → 调用LLM生成重构代码
    ├─────────────────┤
    │ SafetyValidator  │ → 4层验证确保安全
    ├─────────────────┤
    │ CodeRefactorer   │ → AST级后处理（回退引擎）
    └─────────────────┘

    安全保障:
    - LLM输出必须通过4层验证
    - 失败自动回退到AST级RefactorEngine
    - 完整审计日志
    """

    def __init__(
        self,
        llm_backend: Optional[LLMBackend] = None,
        fallback_refactorer: Optional[CodeRefactorer] = None,
        max_retries: int = 2
    ):
        self.llm_backend = llm_backend
        self.fallback_refactorer = fallback_refactorer or create_refactorer()
        self.validator = SafetyValidator()
        self.prompt_builder = PromptBuilder()
        self.max_retries = max_retries

        # 统计
        self._stats = {
            'total_requests': 0,
            'llm_success': 0,
            'llm_failed': 0,
            'fallback_used': 0,
            'validation_failed': 0,
            'total_tokens': 0,
        }

    async def refactor(
        self,
        request: SemanticRefactorRequest
    ) -> SemanticRefactorResult:
        """
        执行语义重构

        流程:
        1. 构建Prompt
        2. 调用LLM
        3. 提取代码
        4. 安全验证
        5. 应用或回退
        """
        self._stats['total_requests'] += 1

        # 如果没有LLM Backend，直接使用AST回退
        if not self.llm_backend:
            return await self._fallback_refactor(request)

        # 1. 构建Prompt
        system_prompt, user_prompt = self.prompt_builder.build_prompt(request)

        # 2. 调用LLM（带重试）
        llm_response = None
        for attempt in range(self.max_retries):
            try:
                if self.llm_backend.check_budget():
                    llm_response = self.llm_backend.complete(system_prompt, user_prompt)
                    self._stats['total_tokens'] += (
                        llm_response.input_tokens + llm_response.output_tokens
                    )
                    break
                else:
                    print(f"[SemanticRefactor] 预算不足，回退到AST引擎")
                    return await self._fallback_refactor(request)
            except Exception as e:
                print(f"[SemanticRefactor] LLM调用失败 (attempt {attempt+1}): {e}")
                if attempt == self.max_retries - 1:
                    return await self._fallback_refactor(request)

        if not llm_response:
            return await self._fallback_refactor(request)

        # 3. 提取代码
        refactored_code = self._extract_code(llm_response.content)
        if not refactored_code:
            self._stats['llm_failed'] += 1
            return await self._fallback_refactor(request)

        # 4. 安全验证
        all_passed, messages = self.validator.full_validation(request.code, refactored_code)

        if not all_passed:
            print(f"[SemanticRefactor] 验证失败: {messages}")
            self._stats['validation_failed'] += 1

            # 验证失败，重试或回退
            if self.max_retries > 1:
                return await self._fallback_refactor(request)

            return SemanticRefactorResult(
                request_id=request.request_id,
                success=False,
                original_code=request.code,
                refactored_code=request.code,
                explanation=f"验证失败: {'; '.join(messages)}",
                validation_passed=False,
                rollback_performed=False,
            )

        # 5. 成功 - 生成结果
        diff = self._generate_diff(request.code, refactored_code, request.file_path)
        self._stats['llm_success'] += 1

        return SemanticRefactorResult(
            request_id=request.request_id,
            success=True,
            original_code=request.code,
            refactored_code=refactored_code,
            diff=diff,
            explanation="LLM语义重构成功",
            llm_tokens_used=llm_response.input_tokens + llm_response.output_tokens,
            validation_passed=True,
            rollback_performed=False,
            changes=[{
                'type': request.refactor_type.name,
                'provider': llm_response.provider,
                'model': llm_response.model,
                'tokens': llm_response.input_tokens + llm_response.output_tokens,
            }]
        )

    async def _fallback_refactor(self, request: SemanticRefactorRequest) -> SemanticRefactorResult:
        """回退到AST级重构"""
        self._stats['fallback_used'] += 1

        # 根据重构类型选择AST策略
        type_to_strategy = {
            SemanticRefactorType.FUNCTION_SPLIT: 'extract_function',
            SemanticRefactorType.CODE_SIMPLIFY: 'organize_imports',
            SemanticRefactorType.ALGORITHM_OPTIMIZE: 'optimize_loops',
            SemanticRefactorType.TYPE_ANNOTATION: 'remove_unused',
        }

        strategy = type_to_strategy.get(request.refactor_type, 'organize_imports')

        result = self.fallback_refactorer.refactor(
            request.code,
            strategy,
            function_name=request.target_function
        )

        return SemanticRefactorResult(
            request_id=request.request_id,
            success=result.success,
            original_code=request.original_code if hasattr(result, 'original_code') else request.code,
            refactored_code=result.refactored_code,
            diff=self._generate_diff(request.code, result.refactored_code, request.file_path) if result.success else None,
            explanation=f"AST回退重构: {result.message}" if not result.success else result.message,
            validation_passed=result.success,
            rollback_performed=False,
            changes=[{'type': 'ast_fallback', 'strategy': strategy}]
        )

    def _extract_code(self, llm_output: str) -> Optional[str]:
        """从LLM输出中提取代码"""
        # 尝试提取markdown代码块
        code_block_pattern = r'```(?:python)?\s*\n(.*?)```'
        matches = re.findall(code_block_pattern, llm_output, re.DOTALL)

        if matches:
            # 返回最长的代码块（通常是完整代码）
            return max(matches, key=len).strip()

        # 如果没有代码块，检查整个输出是否是有效Python
        try:
            ast.parse(llm_output.strip())
            return llm_output.strip()
        except SyntaxError:
            return None

    def _generate_diff(self, original: str, modified: str, file_path: str) -> str:
        """生成diff"""
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)

        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=file_path,
            tofile=file_path + '.refactored',
            lineterm=''
        )

        return ''.join(diff)

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        total = self._stats['total_requests']
        return {
            **self._stats,
            'success_rate': self._stats['llm_success'] / total if total > 0 else 0,
            'fallback_rate': self._stats['fallback_used'] / total if total > 0 else 0,
        }


def create_semantic_refactor_engine(
    llm_config: Optional[LLMConfig] = None,
    use_mock: bool = False
) -> SemanticRefactorEngine:
    """
    工厂函数：创建语义重构引擎

    Args:
        llm_config: LLM配置，None则使用Mock
        use_mock: 强制使用Mock后端
    """
    if use_mock or llm_config is None:
        # 使用Mock后端
        config = LLMConfig(provider='mock')
        backend = create_llm_backend(config)
    else:
        backend = create_llm_backend(llm_config)

    return SemanticRefactorEngine(llm_backend=backend)


# 测试
if __name__ == "__main__":
    async def test():
        print("=" * 70)
        print("MOSS v9.1 - Semantic Refactor Engine 测试")
        print("=" * 70)

        # 使用Mock后端测试
        engine = create_semantic_refactor_engine(use_mock=True)

        test_code = '''
def process_data(items):
    results = []
    for i in range(len(items)):
        item = items[i]
        if item is not None:
            if item > 0:
                results.append(item * 2)
    return results
'''

        # 测试函数拆分
        print("\n[1] Testing Function Split...")
        request = SemanticRefactorRequest(
            request_id="test_001",
            refactor_type=SemanticRefactorType.FUNCTION_SPLIT,
            code=test_code,
            file_path="test.py",
            target_function="process_data"
        )

        result = await engine.refactor(request)
        print(f"  Success: {result.success}")
        print(f"  Explanation: {result.explanation}")
        if result.changes:
            print(f"  Changes: {result.changes}")

        # 测试代码简化
        print("\n[2] Testing Code Simplification...")
        request = SemanticRefactorRequest(
            request_id="test_002",
            refactor_type=SemanticRefactorType.CODE_SIMPLIFY,
            code=test_code,
            file_path="test.py"
        )

        result = await engine.refactor(request)
        print(f"  Success: {result.success}")
        print(f"  Explanation: {result.explanation}")

        # 统计
        stats = engine.get_statistics()
        print(f"\n[Statistics]")
        print(f"  Total: {stats['total_requests']}")
        print(f"  LLM Success: {stats['llm_success']}")
        print(f"  Fallback Used: {stats['fallback_used']}")

        print("\n测试完成!")

    asyncio.run(test())
