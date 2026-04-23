"""
MOSS v8.0 - Hybrid Mutation Strategy
======================================

AST变异 + LLM变异的协同调度策略。

核心思路：
- AST变异：低成本、快速，适合局部搜索
- LLM变异：高成本、有方向性，适合突破局部最优
- 自适应切换：连续no_op/拒绝/fitness平台 → 调用LLM

模式：
- ast_only:  仅AST（v6.x兼容）
- llm_only:  仅LLM（实验性）
- adaptive:  自适应切换（推荐，默认）
- scheduled: 固定模式（如3AST+1LLM循环）

Author: MOSS v8.0 Auto-Build
Version: 8.0.0-dev
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from .llm_mutator import LLMMutator, LLMMutationResult
from .self_modification_engine import ASTMutator

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────

@dataclass
class HybridStrategyConfig:
    """混合策略配置"""
    # 模式选择
    mode: str = "adaptive"           # ast_only | llm_only | adaptive | scheduled

    # 自适应模式阈值
    consecutive_no_op_threshold: int = 3    # 连续N次no_op后切换LLM
    consecutive_reject_threshold: int = 5   # 连续N次拒绝后切换LLM
    fitness_plateau_window: int = 5         # fitness平台检测窗口（代数）
    fitness_plateau_threshold: float = 0.005  # 最小改进量，低于此为平台

    # 预算分配
    llm_budget_fraction: float = 0.3        # LLM变异占比上限（0.0~1.0）
    ast_budget_fraction: float = 0.7        # AST变异占比

    # 调度模式（固定模式）
    schedule_pattern: List[str] = field(default_factory=lambda: [
        "ast", "ast", "ast", "llm", "ast", "ast", "llm"
    ])

    # LLM冷却
    llm_cooldown_generations: int = 2       # LLM调用后至少N代冷却


# ─────────────────────────────────────────────
# 混合策略主类
# ─────────────────────────────────────────────

class HybridMutationStrategy:
    """
    AST + LLM 混合变异策略（v8.0 核心调度器）

    自适应逻辑：
    1. 默认使用AST变异（低成本）
    2. 当检测到以下信号时切换到LLM：
       a) 连续N次no_op（AST无法产生有效变异）
       b) 连续N次拒绝（AST变异质量不足）
       c) fitness平台（需要突破性变异）
    3. LLM成功后回到AST进行局部搜索
    4. 预算耗尽自动降级为AST-only
    """

    def __init__(self,
                 ast_mutator: ASTMutator,
                 llm_mutator: LLMMutator,
                 config: HybridStrategyConfig = None):
        self.ast_mutator = ast_mutator
        self.llm_mutator = llm_mutator
        self.config = config or HybridStrategyConfig()

        # 状态追踪
        self._consecutive_no_ops: int = 0
        self._consecutive_rejects: int = 0
        self._last_llm_generation: int = -100  # 上次调用LLM的代数
        self._current_generation: int = 0
        self._fitness_history: List[float] = []
        self._llm_calls_this_generation: int = 0

        logger.info(
            f"[HybridStrategy] Initialized (mode={self.config.mode}, "
            f"llm_fraction={self.config.llm_budget_fraction:.0%})"
        )

    def update_state(self,
                     generation: int,
                     mutation_type: str = "",
                     accepted: bool = False,
                     fitness: float = 0.0):
        """
        更新策略状态（由SME每代调用）

        Args:
            generation: 当前代数
            mutation_type: 上次变异类型（ast_xxx / llm_guided / no_op）
            accepted: 是否被接受
            fitness: 当前fitness
        """
        self._current_generation = generation
        self._fitness_history.append(fitness)

        # 更新连续计数器
        if mutation_type == "no_op" or "no_op" in mutation_type:
            self._consecutive_no_ops += 1
            self._consecutive_rejects += 1
        elif not accepted:
            self._consecutive_no_ops = 0
            self._consecutive_rejects += 1
        else:
            # 变异被接受 → 重置计数器
            self._consecutive_no_ops = 0
            self._consecutive_rejects = 0

    def generate_candidates(self,
                            source: str,
                            target_functions: List[str],
                            population_size: int,
                            purpose_vector: Optional[np.ndarray] = None,
                            fitness_history: Optional[List[Dict]] = None,
                            immutable_functions: Optional[List[str]] = None,
                            ) -> List[Tuple[str, Dict]]:
        """
        生成混合变异候选

        Returns:
            List of (mutated_source, mutation_info_dict)
        """
        self._llm_calls_this_generation = 0
        candidates = []

        if self.config.mode == "ast_only":
            candidates = self._generate_ast_only(
                source, target_functions, population_size,
                purpose_vector, fitness_history
            )
        elif self.config.mode == "llm_only":
            candidates = self._generate_llm_only(
                source, target_functions, population_size,
                purpose_vector, fitness_history, immutable_functions
            )
        elif self.config.mode == "scheduled":
            candidates = self._generate_scheduled(
                source, target_functions, population_size,
                purpose_vector, fitness_history, immutable_functions
            )
        else:  # adaptive
            candidates = self._generate_adaptive(
                source, target_functions, population_size,
                purpose_vector, fitness_history, immutable_functions
            )

        logger.info(
            f"[HybridStrategy] Gen {self._current_generation}: "
            f"generated {len(candidates)} candidates "
            f"(llm_calls={self._llm_calls_this_generation}, "
            f"no_ops={self._consecutive_no_ops}, "
            f"rejects={self._consecutive_rejects})"
        )

        return candidates

    # ──────── 模式实现 ────────

    def _generate_ast_only(self,
                           source: str,
                           target_functions: List[str],
                           population_size: int,
                           purpose_vector: Optional[np.ndarray],
                           fitness_history: Optional[List[Dict]]) -> List[Tuple[str, Dict]]:
        """纯AST模式"""
        candidates = []
        for i in range(population_size):
            mutated, mut_type = self.ast_mutator.mutate(
                source, target_functions, purpose_vector=purpose_vector
            )
            candidates.append((mutated, {
                'mutation_type': mut_type,
                'source': 'ast',
            }))
        return candidates

    def _generate_llm_only(self,
                           source: str,
                           target_functions: List[str],
                           population_size: int,
                           purpose_vector: Optional[np.ndarray],
                           fitness_history: Optional[List[Dict]],
                           immutable_functions: Optional[List[str]]) -> List[Tuple[str, Dict]]:
        """纯LLM模式"""
        candidates = []
        for i in range(population_size):
            try:
                mutated, result = self.llm_mutator.mutate(
                    source, target_functions,
                    purpose_vector=purpose_vector,
                    fitness_history=fitness_history,
                    immutable_functions=immutable_functions,
                )
                self._llm_calls_this_generation += 1
                candidates.append((mutated, {
                    'mutation_type': result.mutation_type,
                    'source': 'llm',
                    'strategy': result.mutation_strategy,
                    'target_function': result.target_function,
                    'description': result.change_description,
                    'confidence': result.confidence,
                    'cost_usd': result.llm_cost_usd,
                }))
            except Exception as e:
                logger.warning(f"[HybridStrategy] LLM call failed: {e}")
                candidates.append((source, {
                    'mutation_type': 'llm_no_op',
                    'source': 'llm',
                }))
        return candidates

    def _generate_adaptive(self,
                           source: str,
                           target_functions: List[str],
                           population_size: int,
                           purpose_vector: Optional[np.ndarray],
                           fitness_history: Optional[List[Dict]],
                           immutable_functions: Optional[List[str]]) -> List[Tuple[str, Dict]]:
        """
        自适应模式：根据状态动态分配AST和LLM的候选名额

        触发LLM的条件（满足任一）：
        1. 连续no_op ≥ threshold
        2. 连续reject ≥ threshold
        3. fitness平台（最近N代改进 < threshold）
        4. 冷却期已过 + 随机探索（5%概率）
        """
        should_use_llm = self._should_trigger_llm()
        llm_slots = 0

        if should_use_llm:
            # 计算LLM名额
            llm_slots = max(1, int(population_size * self.config.llm_budget_fraction))
            # 冷却检查
            gens_since_llm = self._current_generation - self._last_llm_generation
            if gens_since_llm < self.config.llm_cooldown_generations:
                llm_slots = 0  # 冷却中，不用LLM

            # 预算检查
            if self.llm_mutator.llm_backend and not self.llm_mutator.llm_backend.check_budget():
                llm_slots = 0  # 预算耗尽

        ast_slots = population_size - llm_slots
        candidates = []

        # AST部分
        for i in range(ast_slots):
            mutated, mut_type = self.ast_mutator.mutate(
                source, target_functions, purpose_vector=purpose_vector
            )
            candidates.append((mutated, {
                'mutation_type': mut_type,
                'source': 'ast',
            }))

        # LLM部分
        if llm_slots > 0:
            for i in range(llm_slots):
                try:
                    mutated, result = self.llm_mutator.mutate(
                        source, target_functions,
                        purpose_vector=purpose_vector,
                        fitness_history=fitness_history,
                        immutable_functions=immutable_functions,
                    )
                    self._llm_calls_this_generation += 1
                    candidates.append((mutated, {
                        'mutation_type': result.mutation_type,
                        'source': 'llm',
                        'strategy': result.mutation_strategy,
                        'target_function': result.target_function,
                        'description': result.change_description,
                        'confidence': result.confidence,
                        'cost_usd': result.llm_cost_usd,
                    }))
                except Exception as e:
                    logger.warning(f"[HybridStrategy] LLM call failed, fallback to AST: {e}")
                    # 降级为AST
                    mutated, mut_type = self.ast_mutator.mutate(
                        source, target_functions, purpose_vector=purpose_vector
                    )
                    candidates.append((mutated, {
                        'mutation_type': mut_type,
                        'source': 'ast_fallback',
                    }))

            self._last_llm_generation = self._current_generation

        return candidates

    def _generate_scheduled(self,
                            source: str,
                            target_functions: List[str],
                            population_size: int,
                            purpose_vector: Optional[np.ndarray],
                            fitness_history: Optional[List[Dict]],
                            immutable_functions: Optional[List[str]]) -> List[Tuple[str, Dict]]:
        """固定调度模式"""
        candidates = []
        pattern = self.config.schedule_pattern

        for i in range(population_size):
            mode = pattern[i % len(pattern)]

            if mode == "llm":
                # Scheduled模式：强制按pattern执行，忽略冷却，只检查预算
                budget_ok = (self.llm_mutator.llm_backend and
                             self.llm_mutator.llm_backend.check_budget())
                if budget_ok:
                    try:
                        mutated, result = self.llm_mutator.mutate(
                            source, target_functions,
                            purpose_vector=purpose_vector,
                            fitness_history=fitness_history,
                            immutable_functions=immutable_functions,
                        )
                        self._llm_calls_this_generation += 1
                        self._last_llm_generation = self._current_generation
                        candidates.append((mutated, {
                            'mutation_type': result.mutation_type,
                            'source': 'llm',
                            'strategy': result.mutation_strategy,
                            'target_function': result.target_function,
                            'description': result.change_description,
                            'confidence': result.confidence,
                            'cost_usd': result.llm_cost_usd,
                        }))
                        continue
                    except Exception as e:
                        logger.warning(f"[HybridStrategy] Scheduled LLM failed: {e}")

            # AST fallback
            mutated, mut_type = self.ast_mutator.mutate(
                source, target_functions, purpose_vector=purpose_vector
            )
            candidates.append((mutated, {
                'mutation_type': mut_type,
                'source': 'ast',
            }))

        return candidates

    # ──────── 辅助方法 ────────

    def _should_trigger_llm(self) -> bool:
        """判断是否应该触发LLM变异"""
        # 条件1: 连续no_op
        if self._consecutive_no_ops >= self.config.consecutive_no_op_threshold:
            logger.info(
                f"[HybridStrategy] LLM trigger: consecutive_no_op={self._consecutive_no_ops}"
            )
            return True

        # 条件2: 连续拒绝
        if self._consecutive_rejects >= self.config.consecutive_reject_threshold:
            logger.info(
                f"[HybridStrategy] LLM trigger: consecutive_rejects={self._consecutive_rejects}"
            )
            return True

        # 条件3: fitness平台
        if len(self._fitness_history) >= self.config.fitness_plateau_window:
            recent = self._fitness_history[-self.config.fitness_plateau_window:]
            improvement = max(recent) - min(recent)
            if improvement < self.config.fitness_plateau_threshold:
                logger.info(
                    f"[HybridStrategy] LLM trigger: fitness plateau "
                    f"(improvement={improvement:.4f} < {self.config.fitness_plateau_threshold})"
                )
                return True

        # 条件4: 随机探索（5%概率）
        if np.random.random() < 0.05:
            logger.info("[HybridStrategy] LLM trigger: random exploration (5%)")
            return True

        return False

    def get_stats(self) -> Dict:
        """获取策略统计"""
        return {
            'mode': self.config.mode,
            'current_generation': self._current_generation,
            'consecutive_no_ops': self._consecutive_no_ops,
            'consecutive_rejects': self._consecutive_rejects,
            'last_llm_generation': self._last_llm_generation,
            'llm_calls_this_generation': self._llm_calls_this_generation,
            'fitness_history_length': len(self._fitness_history),
        }
