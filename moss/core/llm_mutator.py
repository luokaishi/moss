"""
MOSS v8.0 - LLM-Guided Mutator
================================

用LLM替代随机AST变异，实现有意图、有方向的代码改进。

核心区别（vs ASTMutator）：
- ASTMutator：盲变异，随机选择AST节点修改
- LLMMutator：理解代码上下文，基于目的向量和fitness历史生成定向变异

4种策略：
1. parameter_tune - 数值参数精调（权重、阈值、epsilon）
2. logic_refine   - 条件逻辑优化（分支条件、比较运算）
3. behavior_shift - 行为策略调整（动作选择权重、动作池）
4. structure_add  - 新增条件分支（状态依赖行为）

安全机制：
- 7层预验证（语法→结构→不可变→diff→危险→import→大小）
- 必须通过 CodeSandbox 二次验证

Author: MOSS v8.0 Auto-Build
Version: 8.0.0-dev
"""

import ast
import json
import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from .llm_backend import LLMBackend, LLMConfig

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────

@dataclass
class LLMMutationResult:
    """LLM变异结果"""
    mutated_source: str
    mutation_type: str           # "llm_guided" | "llm_no_op"
    mutation_strategy: str       # "parameter_tune" | "logic_refine" | "behavior_shift" | "structure_add"
    target_function: str         # 被修改的函数名
    change_description: str      # LLM描述的修改原因
    confidence: float            # LLM自评置信度 (0-1)
    llm_cost_usd: float
    llm_tokens_used: int
    validation_passed: bool = True  # 预验证是否通过


# ─────────────────────────────────────────────
# Prompt 模板
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """You are a code mutation specialist for an AI agent framework called MOSS.
Your task is to make a SINGLE, TARGETED modification to the agent's code that improves its fitness.

FITNESS CRITERIA (weighted):
- success_rate (35%): How often the agent's actions succeed
- diversity (25%): Behavioral diversity (Shannon entropy of action distribution)
- purpose_alignment (20%): Alignment with the agent's purpose vector
- emergence (20%): Detection of emergent behaviors (phase transitions, self-organization)

RULES:
1. Modify ONLY functions in the allowed list. NEVER touch immutable functions.
2. Make ONE focused change, not multiple unrelated changes.
3. Preserve all function signatures and class interfaces.
4. Do NOT add new imports unless absolutely necessary.
5. Do NOT use eval(), exec(), subprocess, os.system, __import__, or any dangerous operations.
6. Do NOT open or write files. Do NOT make network requests.
7. Keep changes minimal and incremental.
8. Output ONLY the complete modified Python source code, no markdown fences, no explanations.
9. At the very END of the output, add a single comment line with mutation metadata:
   # MUTATION_INFO: {"strategy": "...", "target_function": "...", "description": "...", "confidence": 0.0-1.0}
"""


# ─────────────────────────────────────────────
# LLMMutator 主类
# ─────────────────────────────────────────────

class LLMMutator:
    """
    LLM引导变异器（v8.0 核心组件）

    与ASTMutator平行，但使用LLM理解代码语义后生成有意图的变异。
    """

    STRATEGIES = {
        "parameter_tune": "Adjust numerical parameters (weights, thresholds, epsilon) with reasoning about expected impact on fitness",
        "logic_refine":   "Refine conditional logic, comparison operators, or branching conditions to improve decision quality",
        "behavior_shift": "Modify action selection weights or action pool composition to increase diversity or purpose alignment",
        "structure_add":  "Add new conditional branches or state-dependent behavior patterns to enable emergent behaviors",
    }

    # 危险模式黑名单
    DANGEROUS_PATTERNS = [
        r'\beval\s*\(',
        r'\bexec\s*\(',
        r'\bsubprocess\b',
        r'\bos\.system\s*\(',
        r'\b__import__\s*\(',
        r'\bopen\s*\([^)]*[\'"][wWaA]',
        r'\bos\.remove',
        r'\bos\.unlink',
        r'\bshutil\.rmtree',
        r'\bsys\.exit',
    ]

    # 允许新增的 import 白名单
    IMPORT_WHITELIST = {"numpy", "random", "math", "logging", "collections"}

    def __init__(self, llm_backend: LLMBackend):
        self.llm_backend = llm_backend

    def mutate(self,
               source: str,
               target_functions: List[str],
               purpose_vector: Optional[np.ndarray] = None,
               fitness_history: Optional[List[Dict]] = None,
               immutable_functions: Optional[List[str]] = None,
               mutation_strategy: Optional[str] = None,
               ) -> Tuple[str, LLMMutationResult]:
        """
        生成LLM引导的变异

        Args:
            source: 目标模块源码
            target_functions: 允许修改的函数名列表
            purpose_vector: Agent的目的向量
            fitness_history: 近期fitness评估历史
            immutable_functions: 不可变函数名列表
            mutation_strategy: 强制指定策略，None则自动选择

        Returns:
            (mutated_source, LLMMutationResult)
        """
        immutable = immutable_functions or []

        # 选择策略
        if mutation_strategy is None:
            mutation_strategy = self._select_strategy(
                purpose_vector, fitness_history
            )

        # 构建 prompt
        user_prompt = self._build_user_prompt(
            source, target_functions, purpose_vector,
            fitness_history, immutable, mutation_strategy
        )

        # 调用 LLM
        try:
            response = self.llm_backend.complete(SYSTEM_PROMPT, user_prompt)
        except Exception as e:
            logger.warning(f"[LLMMutator] LLM call failed: {e}")
            return source, LLMMutationResult(
                mutated_source=source,
                mutation_type="llm_no_op",
                mutation_strategy=mutation_strategy,
                target_function="",
                change_description=f"LLM call failed: {e}",
                confidence=0.0,
                llm_cost_usd=0.0,
                llm_tokens_used=0,
                validation_passed=False,
            )

        # 提取变异代码（LLM 输出完整文件）
        mutated_source = self._clean_llm_output(response.content)

        # 提取变异元数据
        mutation_info = self._extract_mutation_info(mutated_source)
        # 从变异代码中移除 MUTATION_INFO 注释行
        mutated_source_clean = self._remove_mutation_info_comment(mutated_source)

        # 7层预验证
        is_valid, validation_reason = self._validate_llm_output(
            source, mutated_source_clean, target_functions, immutable
        )

        if not is_valid:
            logger.warning(
                f"[LLMMutator] Pre-validation FAILED: {validation_reason}"
            )
            return source, LLMMutationResult(
                mutated_source=source,
                mutation_type="llm_no_op",
                mutation_strategy=mutation_strategy,
                target_function=mutation_info.get("target_function", ""),
                change_description=f"Pre-validation failed: {validation_reason}",
                confidence=0.0,
                llm_cost_usd=response.cost_usd,
                llm_tokens_used=response.input_tokens + response.output_tokens,
                validation_passed=False,
            )

        return mutated_source_clean, LLMMutationResult(
            mutated_source=mutated_source_clean,
            mutation_type="llm_guided",
            mutation_strategy=mutation_info.get("strategy", mutation_strategy),
            target_function=mutation_info.get("target_function", ""),
            change_description=mutation_info.get("description", ""),
            confidence=mutation_info.get("confidence", 0.5),
            llm_cost_usd=response.cost_usd,
            llm_tokens_used=response.input_tokens + response.output_tokens,
            validation_passed=True,
        )

    def _select_strategy(self,
                         purpose_vector: Optional[np.ndarray],
                         fitness_history: Optional[List[Dict]]) -> str:
        """
        根据上下文自动选择变异策略

        逻辑：
        - 有目的向量且alignment低 → behavior_shift
        - fitness持续下降 → parameter_tune（保守）
        - fitness平台 → structure_add（突破）
        - 默认 → 随机选择
        """
        strategies = list(self.STRATEGIES.keys())

        if fitness_history and len(fitness_history) >= 3:
            recent_deltas = [h.get('fitness_delta', 0.0) for h in fitness_history[-3:]]
            avg_delta = sum(recent_deltas) / len(recent_deltas)

            if avg_delta < -0.01:
                # fitness 下降 → 保守策略
                return "parameter_tune"
            elif all(abs(d) < 0.005 for d in recent_deltas):
                # fitness 平台 → 突破策略
                return "structure_add"

        if purpose_vector is not None:
            # 简单启发式：如果目的向量偏重某维度，选择对应策略
            if len(purpose_vector) >= 4:
                max_dim = int(np.argmax(purpose_vector[:4]))
                dim_to_strategy = {
                    0: "parameter_tune",   # success_rate维度高 → 精调参数
                    1: "behavior_shift",   # diversity维度高 → 调整行为
                    2: "behavior_shift",   # purpose_align维度高 → 调整行为对齐
                    3: "structure_add",    # emergence维度高 → 增加结构性
                }
                return dim_to_strategy.get(max_dim, "parameter_tune")

        # 默认：随机选择
        import random
        return random.choice(strategies)

    def _build_user_prompt(self,
                           source: str,
                           target_functions: List[str],
                           purpose_vector: Optional[np.ndarray],
                           fitness_history: Optional[List[Dict]],
                           immutable_functions: List[str],
                           strategy: str) -> str:
        """构建用户提示"""
        parts = [
            "=== CURRENT SOURCE CODE ===",
            source,
            "",
            f"=== MODIFIABLE FUNCTIONS: {target_functions} ===",
            f"=== IMMUTABLE FUNCTIONS (DO NOT TOUCH): {immutable_functions} ===",
        ]

        if purpose_vector is not None:
            pv = np.array(purpose_vector)
            parts.append(f"=== PURPOSE VECTOR: {pv.tolist()} ===")
            parts.append(
                "The purpose vector represents the agent's current goals across dimensions "
                "[survival, curiosity, influence, optimization]. "
                "Mutations that align behavior with this vector will score higher on purpose_alignment."
            )

        if fitness_history:
            parts.append("=== RECENT FITNESS HISTORY ===")
            for entry in fitness_history[-5:]:
                parts.append(
                    f"  Gen {entry.get('generation', '?')}: "
                    f"fitness={entry.get('fitness_after', 0.0):.4f} "
                    f"delta={entry.get('fitness_delta', 0.0):+.4f} "
                    f"type={entry.get('mutation_type', '?')} "
                    f"accepted={entry.get('accepted', False)}"
                )

        parts.append(f"=== MUTATION STRATEGY: {strategy} ===")
        parts.append(f"  Guidance: {self.STRATEGIES[strategy]}")
        parts.append("")
        parts.append(
            "Output ONLY the modified function definition (from 'def' to end of function body). "
            "Produce the COMPLETE modified Python source code (the entire file, not just the changed function). "
            "At the END of the file, add a single comment line with mutation metadata:"
        )
        parts.append(
            '# MUTATION_INFO: {"strategy": "...", "target_function": "...", '
            '"description": "...", "confidence": 0.0-1.0}'
        )

        return "\n".join(parts)

    def _clean_llm_output(self, raw_output: str) -> str:
        """
        清理LLM输出（移除markdown代码围栏等）
        """
        # 移除 markdown 代码围栏
        cleaned = raw_output.strip()
        if cleaned.startswith("```python"):
            cleaned = cleaned[len("```python"):]
        elif cleaned.startswith("```"):
            cleaned = cleaned[len("```"):]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-len("```")]
        cleaned = cleaned.strip()
        return cleaned

    def _extract_mutation_info(self, source: str) -> Dict:
        """
        从变异代码末尾提取 MUTATION_INFO 注释
        """
        # 查找最后一行 MUTATION_INFO
        pattern = r'#\s*MUTATION_INFO:\s*(\{.*\})'
        matches = list(re.finditer(pattern, source))
        if matches:
            try:
                info_str = matches[-1].group(1)
                return json.loads(info_str)
            except json.JSONDecodeError as e:
                logger.debug(f"[LLMMutator] Failed to parse MUTATION_INFO: {e}")
        return {}

    def _remove_mutation_info_comment(self, source: str) -> str:
        """移除 MUTATION_INFO 注释行"""
        pattern = r'\n?\s*#\s*MUTATION_INFO:\s*\{.*\}\s*$'
        return re.sub(pattern, '', source).rstrip()

    def _validate_llm_output(self,
                             original_source: str,
                             mutated_source: str,
                             target_functions: List[str],
                             immutable_functions: List[str]) -> Tuple[bool, str]:
        """
        7层预验证

        Returns:
            (is_valid, reason)
        """
        # Layer 1: 语法检查
        try:
            mutated_tree = ast.parse(mutated_source)
        except SyntaxError as e:
            return False, f"Syntax error in LLM output: {e}"

        try:
            original_tree = ast.parse(original_source)
        except SyntaxError:
            return False, "Original source has syntax error (shouldn't happen)"

        # Layer 2: 结构等价性（相同的类名和函数签名）
        orig_classes = {node.name for node in ast.walk(original_tree) if isinstance(node, ast.ClassDef)}
        mut_classes = {node.name for node in ast.walk(mutated_tree) if isinstance(node, ast.ClassDef)}
        if orig_classes != mut_classes:
            missing = orig_classes - mut_classes
            added = mut_classes - orig_classes
            return False, f"Class structure changed: missing={missing}, added={added}"

        # 检查函数签名
        orig_funcs = self._extract_function_signatures(original_tree)
        mut_funcs = self._extract_function_signatures(mutated_tree)
        # 不要求所有函数都存在（LLM可能只是没显示全部），但已有的函数签名必须匹配
        for name, sig in orig_funcs.items():
            if name in mut_funcs and mut_funcs[name] != sig:
                return False, f"Function signature changed: {name}({sig}) -> {name}({mut_funcs[name]})"

        # Layer 3: 不可变函数保护
        orig_func_sources = self._extract_function_sources(original_source)
        mut_func_sources = self._extract_function_sources(mutated_source)
        for func_name in immutable_functions:
            if func_name in orig_func_sources and func_name in mut_func_sources:
                if orig_func_sources[func_name].strip() != mut_func_sources[func_name].strip():
                    return False, f"Immutable function modified: {func_name}"

        # Layer 4: diff 范围检查（仅目标函数可能有变化）
        changed_funcs = []
        for func_name in orig_func_sources:
            if func_name in mut_func_sources:
                if orig_func_sources[func_name].strip() != mut_func_sources[func_name].strip():
                    changed_funcs.append(func_name)

        illegal_changes = set(changed_funcs) - set(target_functions)
        if illegal_changes:
            return False, f"Non-target functions modified: {illegal_changes}"

        if not changed_funcs:
            return False, "No changes detected in target functions"

        # Layer 5: 危险模式检查（仅在新增代码中检测，忽略原始代码已有的模式）
        orig_lines = set(original_source.split('\n'))
        mut_lines = mutated_source.split('\n')
        new_lines = [line for line in mut_lines if line not in orig_lines]
        new_code = '\n'.join(new_lines)
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, new_code):
                return False, f"Dangerous pattern detected in NEW code: {pattern}"

        # Layer 6: import 检查
        orig_imports = self._extract_imports(original_source)
        mut_imports = self._extract_imports(mutated_source)
        new_imports = mut_imports - orig_imports
        if new_imports:
            illegal_imports = new_imports - self.IMPORT_WHITELIST
            if illegal_imports:
                return False, f"Disallowed new imports: {illegal_imports}"

        # Layer 7: 大小约束（80%-120%）
        orig_len = len(original_source)
        mut_len = len(mutated_source)
        if mut_len < orig_len * 0.8:
            return False, f"Output too short: {mut_len} vs {orig_len} ({mut_len/orig_len:.0%})"
        if mut_len > orig_len * 1.2:
            return False, f"Output too long: {mut_len} vs {orig_len} ({mut_len/orig_len:.0%})"

        return True, "All validation layers passed"

    def _extract_function_signatures(self, tree: ast.AST) -> Dict[str, str]:
        """提取函数签名（名称+参数列表）"""
        sigs = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = [arg.arg for arg in node.args.args]
                sigs[node.name] = ", ".join(args)
        return sigs

    def _extract_function_sources(self, source: str) -> Dict[str, str]:
        """从源码中提取各函数的源文本"""
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return {}

        lines = source.split('\n')
        result = {}

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start = node.lineno - 1
                end = node.end_lineno if hasattr(node, 'end_lineno') and node.end_lineno else start + 1
                func_source = '\n'.join(lines[start:end])
                result[node.name] = func_source

        return result

    def _apply_function_mutation(self,
                                  source: str,
                                  llm_func_code: str,
                                  target_functions: List[str]) -> Optional[str]:
        """
        v8.1: 将 LLM 输出的函数替换到源文件中
        
        LLM 只输出修改后的函数体，此方法将其替换到原始源码中对应位置。
        
        Returns:
            替换后的完整源码，如果替换失败返回 None
        """
        # 解析 LLM 输出中的函数名
        try:
            llm_tree = ast.parse(llm_func_code)
        except SyntaxError as e:
            logger.warning(f"[LLMMutator] LLM output has syntax error: {e}")
            return None

        # 找到 LLM 输出中的函数定义
        llm_funcs = {}
        for node in ast.walk(llm_tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                llm_funcs[node.name] = node

        if not llm_funcs:
            logger.warning("[LLMMutator] No function definition found in LLM output")
            return None

        # 确认修改的函数在允许列表中
        modified_func = None
        for fname, node in llm_funcs.items():
            if fname in target_functions:
                modified_func = fname
                break

        if modified_func is None:
            # 检查是否修改了非目标函数
            non_target = set(llm_funcs.keys()) - set(target_functions)
            if non_target:
                logger.warning(f"[LLMMutator] LLM modified non-target function: {non_target}")
                return None
            # 没有找到任何函数
            logger.warning(f"[LLMMutator] LLM output functions {list(llm_funcs.keys())} not in targets {target_functions}")
            return None

        # 在原始源码中找到该函数并替换
        source_lines = source.split('\n')
        try:
            source_tree = ast.parse(source)
        except SyntaxError:
            return None

        for node in ast.walk(source_tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == modified_func:
                # 找到了要替换的函数
                start_line = node.lineno - 1  # 0-indexed
                end_line = node.end_lineno if hasattr(node, 'end_lineno') and node.end_lineno else start_line + 1

                # 获取 LLM 输出中对应函数的源码
                llm_func_lines = llm_func_code.split('\n')

                # 找到 LLM 输出中的函数起始行
                llm_func_start = None
                for i, line in enumerate(llm_func_lines):
                    if line.strip().startswith(f'def {modified_func}(') or line.strip().startswith(f'async def {modified_func}('):
                        llm_func_start = i
                        break

                if llm_func_start is None:
                    # 整个 LLM 输出就是函数
                    new_func_code = llm_func_code
                else:
                    # 从 def 行开始
                    new_func_code = '\n'.join(llm_func_lines[llm_func_start:])

                # 替换
                new_lines = source_lines[:start_line] + new_func_code.split('\n') + source_lines[end_line:]
                return '\n'.join(new_lines)

        logger.warning(f"[LLMMutator] Function {modified_func} not found in original source")
        return None

    def _extract_imports(self, source: str) -> set:
        """提取导入的模块名"""
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return set()

        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])

        return imports
