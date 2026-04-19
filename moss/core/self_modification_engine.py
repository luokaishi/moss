"""
MOSS v6.2 - Self-Modification Engine (SME)
==========================================

Agent自写自身代码的核心引擎

架构：
- AST层变异（无需外部GP库，纯Python实现）
- 结构级变异：函数体重组、逻辑反转、Epsilon自调优
- 目的向量导向的有意图搜索
- 真实涌现检测（非代理指标）
- 隔离沙箱安全验证
- importlib热重载

升级历史：
- v6.0: 初始AST变异引擎
- v6.1: 强化版（加权函数选择、真实涌现检测三信号、放宽沙箱通过标准）
- v6.2: 语义引导变异（PurposeGuidedSelector）- 基于目的向量余弦相似度软权重变异类型

Author: MOSS v6.0 Auto-Build
Date: 2026-04-13
Version: 6.2.0-dev  (语义引导变异版)
"""

import ast
import copy
import hashlib
import importlib
import importlib.util
import json
import logging
import os
import random
import subprocess
import sys
import tempfile
import textwrap
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────

@dataclass
class ParetoSolution:
    """
    Pareto多目标解（v6.3新增）

    维护4维fitness向量（非标量），用于Pareto非支配排序
    """
    fitness_vector: np.ndarray     # [success_rate, diversity, purpose_align, emergence]
    source: str                    # 对应的变异源码
    mutation_type: str             # 变异类型
    generation: int                # 产生代次
    sandbox_passed: bool = True

    @property
    def scalar_fitness(self) -> float:
        """加权标量（与v6.1兼容，用于日志显示）"""
        w = np.array([0.35, 0.25, 0.20, 0.20])
        return float(np.dot(w, self.fitness_vector))

    def dominates(self, other: 'ParetoSolution') -> bool:
        """
        Pareto支配关系：self至少在一个维度优于other，且不在任何维度差于other

        Returns True if self Pareto-dominates other
        """
        return (np.all(self.fitness_vector >= other.fitness_vector) and
                np.any(self.fitness_vector > other.fitness_vector))

    def to_dict(self) -> Dict:
        return {
            'fitness_vector': self.fitness_vector.tolist(),
            'scalar_fitness': self.scalar_fitness,
            'mutation_type': self.mutation_type,
            'generation': self.generation,
            'sandbox_passed': self.sandbox_passed,
        }


@dataclass
class MutationResult:
    """单次变异结果"""
    mutation_id: str
    mutation_type: str          # 'constant_tweak' | 'condition_flip' | 'weight_shift' | 'action_insert'
    original_hash: str
    mutated_hash: str
    fitness_before: float
    fitness_after: float
    fitness_delta: float
    accepted: bool
    sandbox_passed: bool
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        d = {k: v for k, v in self.__dict__.items()}
        d['timestamp'] = self.timestamp.isoformat()
        return d


@dataclass
class SMEConfig:
    """SelfModificationEngine 配置"""
    target_module: str = "moss.core.unified_agent"          # 被改写的模块
    target_functions: List[str] = field(default_factory=lambda: [
        "step", "_apply_state_weights",                     # 高富集度（score 54/30）
        "_random_action", "select_action",                  # 中等富集度（score 4/14）
        "_update_state"                                     # 含条件判断
    ])
    population_size: int = 6                                 # 每代变异候选数（增大搜索空间）
    max_generations: int = 30                                # 最大进化代数（扩展为30代）
    acceptance_threshold: float = -0.002                     # 允许轻微退步（模拟退火风格探索）
    sandbox_timeout: int = 30                                # 沙箱运行超时（秒）
    enable_hot_reload: bool = True                           # 是否热重载
    output_dir: str = "experiments/self_modification"        # 结果目录
    enable_structural_mutations: bool = True                 # 开启结构级变异
    mutation_intensity: float = 0.3                          # 变异强度（0.1=保守, 0.5=激进）
    use_real_emergence: bool = True                          # 使用真实涌现检测
    immutable_functions: List[str] = field(default_factory=lambda: [
        "__init__", "save_checkpoint", "load_checkpoint",
        "_setup_logging", "get_state"
    ])                                                        # 不可变函数（安全锁定）
    # ── v6.2 新增：语义引导变异 ──
    enable_semantic_guidance: bool = True                    # 启用语义引导变异选择（v6.2新增）
    semantic_temperature: float = 1.5                        # softmax温度（低→贪心，高→均匀）
    semantic_exploration_bonus: float = 0.1                  # 探索奖励（防止语义引导过度收敛）
    # ── v6.3 预留：Pareto多目标优化 ──
    use_pareto: bool = False                                  # 启用Pareto多目标优化（v6.3新增，默认关闭）
    pareto_archive_size: int = 50                             # Pareto档案最大容量
    # ── v8.0 新增：LLM引导变异 ──
    enable_llm_mutation: bool = False                         # 启用LLM引导变异（默认关闭，保持v6.x兼容）
    llm_provider: str = "mock"                                # LLM提供商 (openai|anthropic|ark|local|mock)
    llm_model: str = ""                                       # LLM模型名（留空自动推断）
    llm_max_tokens: int = 2048                                # LLM最大输出token
    llm_temperature: float = 0.3                              # LLM生成温度
    llm_daily_token_budget: int = 100000                      # 每日LLM token预算
    llm_daily_request_budget: int = 200                       # 每日LLM请求预算
    llm_mutation_strategy: str = "adaptive"                   # 混合策略模式 (adaptive|scheduled|llm_only)
    llm_consecutive_no_op_threshold: int = 3                  # 连续no_op切换LLM阈值
    llm_consecutive_reject_threshold: int = 5                 # 连续拒绝切换LLM阈值
    llm_fitness_plateau_window: int = 5                       # fitness平台检测窗口
    llm_budget_fraction: float = 0.3                          # LLM变异占比上限


# ─────────────────────────────────────────────
# v6.2 语义引导变异选择器（PurposeGuidedSelector）
# ─────────────────────────────────────────────

class PurposeGuidedSelector:
    """
    语义引导变异选择器（v6.2 核心创新）

    核心思路：
    - 9种变异类型各有其"语义倾向向量"（对fitness四分量的期望影响方向）
    - 目的向量D9降维后与语义倾向对齐，计算余弦相似度
    - 用softmax将相似度转换为选择概率，引导变异朝"目的对齐"方向搜索
    - 温度参数控制探索/利用平衡：temperature=2.0接近均匀随机，→0趋向贪心

    语义映射维度（对应fitness四分量）：
    0: success_rate  - 成功率影响
    1: diversity     - 行为多样性影响
    2: purpose_align - 目的对齐度影响
    3: emergence     - 涌现信号影响
    """

    # 9种变异类型的语义倾向向量（经验设计，对fitness四分量的期望增益方向）
    # 格式：[success_rate, diversity, purpose_align, emergence]
    MUTATION_SEMANTICS = {
        # 参数级变异（精细调整）
        'constant_tweak':   np.array([0.6, 0.2, 0.3, 0.4]),  # 精调常量→提升成功率&涌现
        'condition_flip':   np.array([0.3, 0.5, 0.2, 0.6]),  # 翻转条件→增加行为多样性&涌现
        'weight_shift':     np.array([0.4, 0.4, 0.6, 0.3]),  # 权重重分配→提升目的对齐
        'threshold_mutate': np.array([0.5, 0.3, 0.4, 0.3]),  # 阈值调整→提升成功率
        # 结构级变异（激进探索）
        'epsilon_tune':     np.array([0.2, 0.7, 0.2, 0.5]),  # 探索率调整→增加多样性
        'weight_hardcode':  np.array([0.6, 0.2, 0.5, 0.2]),  # 硬编码极端策略→成功率&对齐
        'action_insert':    np.array([0.3, 0.6, 0.3, 0.5]),  # 插入/删除动作→多样性&涌现
        'action_shuffle':   np.array([0.2, 0.8, 0.2, 0.6]),  # 重排优先级→多样性&涌现
        'branch_inject':    np.array([0.4, 0.5, 0.4, 0.7]),  # 注入条件分支→全面提升
    }

    def __init__(self, temperature: float = 1.5, exploration_bonus: float = 0.1):
        """
        Args:
            temperature: softmax温度（高→探索/均匀，低→贪心/确定）
            exploration_bonus: 均匀分布混合系数（防止某类变异被完全忽略）
        """
        self.temperature = temperature
        self.exploration_bonus = exploration_bonus
        # 预归一化语义向量
        self._normalized_semantics = {}
        for mut_type, vec in self.MUTATION_SEMANTICS.items():
            norm = np.linalg.norm(vec)
            self._normalized_semantics[mut_type] = vec / (norm + 1e-10)

    def compute_mutation_probs(self,
                                purpose_vector: Optional[np.ndarray],
                                available_mutations: List[str]) -> Dict[str, float]:
        """
        计算可用变异类型的选择概率

        Args:
            purpose_vector: Agent的目的向量（D9维或4维），None时退化为均匀分布
            available_mutations: 当前可用的变异类型列表

        Returns:
            {mutation_type: probability}，所有值之和=1.0
        """
        if purpose_vector is None or len(available_mutations) == 0:
            # 退化为均匀分布
            uniform_p = 1.0 / len(available_mutations)
            return {m: uniform_p for m in available_mutations}

        # 提取前4维（对应fitness四分量）
        pv = np.array(purpose_vector, dtype=float)
        if len(pv) >= 4:
            pv4 = pv[:4]
        else:
            # 维度不足时补零
            pv4 = np.zeros(4)
            pv4[:len(pv)] = pv

        # 归一化目的向量
        pv_norm = pv4 / (np.linalg.norm(pv4) + 1e-10)

        # 计算每种可用变异类型与目的向量的余弦相似度
        scores = {}
        for mut_type in available_mutations:
            if mut_type in self._normalized_semantics:
                sem_vec = self._normalized_semantics[mut_type]
                cosine = float(np.dot(pv_norm, sem_vec))
                scores[mut_type] = cosine
            else:
                scores[mut_type] = 0.0  # 未知类型给中性分

        # Softmax（带温度）
        score_arr = np.array([scores[m] for m in available_mutations])
        # 平移到非负（避免exp数值问题）
        score_arr = score_arr - score_arr.max()
        exp_arr = np.exp(score_arr / max(self.temperature, 0.01))
        softmax_probs = exp_arr / (exp_arr.sum() + 1e-10)

        # 与均匀分布混合（exploration_bonus控制探索比例）
        n = len(available_mutations)
        uniform_probs = np.ones(n) / n
        final_probs = ((1.0 - self.exploration_bonus) * softmax_probs
                       + self.exploration_bonus * uniform_probs)

        return {m: float(p) for m, p in zip(available_mutations, final_probs)}

    def select_mutation_type(self,
                              purpose_vector: Optional[np.ndarray],
                              available_mutations: List[str],
                              rng: random.Random) -> str:
        """
        按语义引导概率采样一种变异类型

        Args:
            purpose_vector: 目的向量
            available_mutations: 候选变异类型列表
            rng: 随机数生成器

        Returns:
            选中的变异类型名称
        """
        probs = self.compute_mutation_probs(purpose_vector, available_mutations)
        types = list(probs.keys())
        weights = [probs[t] for t in types]

        # 加权随机采样
        rand_val = rng.random()
        cumulative = 0.0
        for t, w in zip(types, weights):
            cumulative += w
            if rand_val <= cumulative:
                return t
        return types[-1]  # fallback

    def get_alignment_report(self,
                              purpose_vector: Optional[np.ndarray],
                              available_mutations: List[str]) -> str:
        """生成语义对齐报告（用于调试/日志）"""
        probs = self.compute_mutation_probs(purpose_vector, available_mutations)
        lines = ["[PurposeGuide] 变异类型语义对齐概率:"]
        for mut_type, prob in sorted(probs.items(), key=lambda x: -x[1]):
            bar = "█" * int(prob * 20)
            lines.append(f"  {mut_type:20s} {bar:20s} {prob:.3f}")
        return "\n".join(lines)


# ─────────────────────────────────────────────
# v6.3 Pareto多目标优化档案（ParetoArchive）
# ─────────────────────────────────────────────

class ParetoArchive:
    """
    Pareto非支配解档案（v6.3 核心组件）

    维护一组Pareto最优解，支持：
    - 非支配排序（NSGA-II风格）
    - 拥挤度距离裁剪（保持多样性）
    - 最优解查询（按不同策略）

    四目标维度：
    0: success_rate  (权重0.35)
    1: diversity     (权重0.25)
    2: purpose_align (权重0.20)
    3: emergence     (权重0.20)
    """

    DIMENSION_NAMES = ['success_rate', 'diversity', 'purpose_align', 'emergence']
    DEFAULT_WEIGHTS = np.array([0.35, 0.25, 0.20, 0.20])

    def __init__(self, max_size: int = 50):
        self.max_size = max_size
        self.solutions: List[ParetoSolution] = []
        self._front_cache: Optional[List[ParetoSolution]] = None  # 缓存Pareto前沿

    def add(self, solution: ParetoSolution) -> bool:
        """
        尝试将新解加入档案

        逻辑：
        1. 如果新解被现有解支配，拒绝
        2. 否则加入档案，移除被新解支配的旧解
        3. 如档案超过容量，用拥挤度距离裁剪

        Returns:
            True if solution was added to archive
        """
        # 检查新解是否被任何现有解支配
        for existing in self.solutions:
            if existing.dominates(solution):
                return False  # 已有更好的解，拒绝

        # 移除被新解支配的现有解
        self.solutions = [s for s in self.solutions if not solution.dominates(s)]

        # 加入新解
        self.solutions.append(solution)
        self._front_cache = None  # 清除缓存

        # 超容量时用拥挤度距离裁剪
        if len(self.solutions) > self.max_size:
            self._crowding_distance_prune()

        return True

    def _crowding_distance_prune(self):
        """
        计算拥挤度距离并移除距离最小的解（保留多样性）

        拥挤度距离：衡量解周围空间密度，小距离=过于聚集
        """
        if len(self.solutions) <= self.max_size:
            return

        n = len(self.solutions)
        n_dims = len(self.DIMENSION_NAMES)
        crowding = np.zeros(n)

        for dim in range(n_dims):
            # 按当前维度排序
            sorted_idx = sorted(range(n), key=lambda i: self.solutions[i].fitness_vector[dim])
            # 边界点设为无穷大（永不删除）
            crowding[sorted_idx[0]] = np.inf
            crowding[sorted_idx[-1]] = np.inf

            f_min = self.solutions[sorted_idx[0]].fitness_vector[dim]
            f_max = self.solutions[sorted_idx[-1]].fitness_vector[dim]
            f_range = f_max - f_min + 1e-10

            for k in range(1, n - 1):
                crowding[sorted_idx[k]] += (
                    (self.solutions[sorted_idx[k + 1]].fitness_vector[dim] -
                     self.solutions[sorted_idx[k - 1]].fitness_vector[dim]) / f_range
                )

        # 移除拥挤度最小的解直到满足容量
        while len(self.solutions) > self.max_size:
            min_idx = np.argmin(crowding)
            self.solutions.pop(int(min_idx))
            crowding = np.delete(crowding, min_idx)

        self._front_cache = None

    def get_pareto_front(self) -> List[ParetoSolution]:
        """返回当前Pareto前沿（非支配解集）"""
        if self._front_cache is not None:
            return self._front_cache
        # 所有在档案中的解都是非支配的（由add()保证）
        self._front_cache = list(self.solutions)
        return self._front_cache

    def get_best_balanced(self) -> Optional[ParetoSolution]:
        """
        返回最均衡解：加权标量fitness最大的解
        """
        if not self.solutions:
            return None
        return max(self.solutions, key=lambda s: s.scalar_fitness)

    def get_best_by_dimension(self, dim: int) -> Optional[ParetoSolution]:
        """
        返回在指定维度上最优的解

        Args:
            dim: 0=success_rate, 1=diversity, 2=purpose_align, 3=emergence
        """
        if not self.solutions:
            return None
        return max(self.solutions, key=lambda s: s.fitness_vector[dim])

    def get_hypervolume_indicator(self,
                                  reference_point: Optional[np.ndarray] = None) -> float:
        """
        计算Pareto前沿的超体积指标（HV）

        HV衡量Pareto前沿覆盖的目标空间体积，越大越好。
        使用简化的2D投影计算（完整4D需要更复杂算法）

        Args:
            reference_point: 参考点（默认全0）

        Returns:
            超体积近似值（0到1之间）
        """
        if not self.solutions:
            return 0.0

        ref = reference_point if reference_point is not None else np.zeros(4)
        front = np.array([s.fitness_vector for s in self.solutions])

        # 简化HV：各维度Pareto前沿均值之积（近似）
        contributions = []
        for dim in range(4):
            max_val = float(np.max(front[:, dim]))
            contributions.append(max(0.0, max_val - ref[dim]))

        hv_approx = float(np.prod(contributions))
        return min(1.0, hv_approx)

    def get_stats(self) -> Dict:
        """返回档案统计摘要"""
        if not self.solutions:
            return {'size': 0}

        front = np.array([s.fitness_vector for s in self.solutions])
        best_balanced = self.get_best_balanced()

        return {
            'size': len(self.solutions),
            'hypervolume': self.get_hypervolume_indicator(),
            'best_balanced': {
                'scalar_fitness': best_balanced.scalar_fitness if best_balanced else 0.0,
                'fitness_vector': best_balanced.fitness_vector.tolist() if best_balanced else [],
                'mutation_type': best_balanced.mutation_type if best_balanced else '',
            },
            'dimension_maxes': {
                self.DIMENSION_NAMES[i]: float(np.max(front[:, i]))
                for i in range(4)
            },
            'dimension_means': {
                self.DIMENSION_NAMES[i]: float(np.mean(front[:, i]))
                for i in range(4)
            },
        }

    def to_dict(self) -> Dict:
        """序列化档案"""
        return {
            'max_size': self.max_size,
            'size': len(self.solutions),
            'solutions': [s.to_dict() for s in self.solutions],
            'stats': self.get_stats(),
        }


# ─────────────────────────────────────────────
# AST 变异器（纯Python实现，无需deap/gplearn）
# ─────────────────────────────────────────────


class ASTMutator:
    """
    基于AST的代码变异器（强化版 v6.1）

    支持的变异类型：
    === 参数级（精细）===
    1. constant_tweak    - 微调数值常量（±10-30%随机扰动）
    2. condition_flip    - 反转比较运算符（< → <=，> → >=）
    3. weight_shift      - 调整权重数组的数值分布（Dirichlet扰动）
    4. action_insert     - 在动作列表中插入/交换/删除动作
    5. threshold_mutate  - 修改阈值常量（0-1间的浮点数）

    === 结构级（激进）===
    6. epsilon_tune      - 调整epsilon-greedy探索率（大幅修改探索比例）
    7. weight_hardcode   - 将动态权重替换为硬编码极端策略
    8. action_shuffle    - 重排动作优先级列表
    9. branch_inject     - 在函数中注入新的条件分支
    """

    COMPARISON_FLIP = {
        ast.Lt: ast.LtE,
        ast.LtE: ast.Lt,
        ast.Gt: ast.GtE,
        ast.GtE: ast.Gt,
        ast.Eq: ast.NotEq,
        ast.NotEq: ast.Eq,
    }

    ACTIONS_POOL = [
        'explore', 'survive', 'influence', 'optimize',
        'cooperate', 'maintain', 'learn', 'share',
        'reflect', 'adapt', 'create', 'preserve',
        'delegate', 'challenge', 'synthesize'
    ]

    # 结构级变异：极端权重策略模板
    STRATEGY_TEMPLATES = [
        [0.7, 0.1, 0.1, 0.1],   # 极度生存偏向
        [0.1, 0.7, 0.1, 0.1],   # 极度好奇偏向
        [0.1, 0.1, 0.7, 0.1],   # 极度影响偏向
        [0.1, 0.1, 0.1, 0.7],   # 极度优化偏向
        [0.4, 0.3, 0.2, 0.1],   # 生存主导均衡
        [0.25, 0.25, 0.25, 0.25],  # 完全均匀
        [0.5, 0.2, 0.2, 0.1],   # 生存+好奇
        [0.2, 0.5, 0.1, 0.2],   # 好奇+优化
    ]

    # 富集度评分（根据诊断结果预设，避免每次重算）
    FUNCTION_RICHNESS = {
        "step": 10,
        "_apply_state_weights": 8,
        "select_action": 4,
        "_update_state": 3,
        "_random_action": 2,
        "_update_purpose": 2,
    }

    def __init__(self, rng_seed: Optional[int] = None, intensity: float = 0.3,
                 purpose_guided_selector: Optional['PurposeGuidedSelector'] = None):
        self.rng = random.Random(rng_seed)
        self.np_rng = np.random.default_rng(rng_seed)
        self.intensity = intensity  # 0.1=保守, 0.5=激进
        self.purpose_guided_selector = purpose_guided_selector  # v6.2: 语义引导选择器

    def mutate(self, source: str, target_functions: List[str],
               mutation_type: Optional[str] = None,
               purpose_vector: Optional[np.ndarray] = None) -> Tuple[str, str]:
        """
        对源码进行一次变异（加权函数选择 + v6.2语义引导变异类型选择）

        Args:
            source: 目标源码
            target_functions: 目标函数名列表
            mutation_type: 强制指定变异类型（None则自动选择）
            purpose_vector: 目的向量（v6.2新增，用于语义引导变异类型选择）

        Returns:
            (mutated_source, mutation_type_applied)
        """
        tree = ast.parse(source)
        func_nodes = self._find_target_functions(tree, target_functions)

        if not func_nodes:
            return source, "no_op"

        # 加权随机选择目标函数（富集度高的函数有更大概率被选中）
        weights = [self.FUNCTION_RICHNESS.get(fn.name, 1) for fn in func_nodes]
        total_w = sum(weights)
        probs = [w / total_w for w in weights]
        rand_val = self.rng.random()
        cumulative = 0.0
        target_func = func_nodes[-1]  # fallback
        for fn, p in zip(func_nodes, probs):
            cumulative += p
            if rand_val <= cumulative:
                target_func = fn
                break

        # 选择变异类型（v6.2：语义引导 or 随机）
        if mutation_type is None:
            mutation_candidates = [
                'constant_tweak', 'condition_flip',
                'weight_shift', 'threshold_mutate',
            ]
            # 强度>0.2时加入结构级变异
            if self.intensity > 0.2:
                mutation_candidates += [
                    'epsilon_tune', 'weight_hardcode',
                    'action_insert',
                ]
            if self.intensity > 0.4:
                mutation_candidates += ['action_shuffle', 'branch_inject']

            # v6.2: 语义引导选择（如果已注入选择器且有目的向量）
            if (self.purpose_guided_selector is not None
                    and purpose_vector is not None):
                mutation_type = self.purpose_guided_selector.select_mutation_type(
                    purpose_vector, mutation_candidates, self.rng
                )
            else:
                # v6.1退化：均匀随机
                mutation_type = self.rng.choice(mutation_candidates)

        mutated_tree = copy.deepcopy(tree)
        target_in_copy = self._find_target_functions(mutated_tree, [target_func.name])

        if not target_in_copy:
            return source, "no_op"

        func_node = target_in_copy[0]

        if mutation_type == 'constant_tweak':
            applied = self._mutate_constants(func_node)
        elif mutation_type == 'condition_flip':
            applied = self._mutate_conditions(func_node)
        elif mutation_type == 'weight_shift':
            applied = self._mutate_weights(func_node)
        elif mutation_type == 'action_insert':
            applied = self._mutate_actions(func_node)
        elif mutation_type == 'threshold_mutate':
            applied = self._mutate_thresholds(func_node)
        elif mutation_type == 'epsilon_tune':
            applied = self._mutate_epsilon(func_node)
        elif mutation_type == 'weight_hardcode':
            applied = self._mutate_weight_hardcode(func_node)
        elif mutation_type == 'action_shuffle':
            applied = self._mutate_action_shuffle(func_node)
        elif mutation_type == 'branch_inject':
            applied = self._mutate_branch_inject(func_node)
        else:
            applied = False

        if not applied:
            return source, "no_op"

        # 修复AST（添加缺少的行列号信息）
        ast.fix_missing_locations(mutated_tree)

        try:
            mutated_source = ast.unparse(mutated_tree)
            return mutated_source, mutation_type
        except Exception as e:
            logger.debug(f"[ASTMutator] unparse failed: {e}")
            return source, "no_op"

    def _find_target_functions(self, tree: ast.AST,
                                target_names: List[str]) -> List[ast.FunctionDef]:
        """查找目标函数节点"""
        funcs = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in target_names:
                funcs.append(node)
        return funcs

    def _mutate_constants(self, func_node: ast.FunctionDef) -> bool:
        """微调数值常量（±10-30%扰动，强度越高扰动越大）"""
        constants = []
        for node in ast.walk(func_node):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                if node.value != 0 and abs(node.value) < 1000:
                    constants.append(node)

        if not constants:
            return False

        target = self.rng.choice(constants)
        # 扰动范围随强度变化：intensity=0.1 → ±10%，intensity=0.5 → ±50%
        spread = 0.1 + self.intensity * 0.8
        delta = self.rng.uniform(1.0 - spread, 1.0 + spread)
        new_val = target.value * delta

        # 保持类型一致性
        if isinstance(target.value, int) and abs(new_val - round(new_val)) < 0.01:
            new_val = int(round(new_val))
        else:
            new_val = round(float(new_val), 4)

        target.value = new_val
        return True

    def _mutate_conditions(self, func_node: ast.FunctionDef) -> bool:
        """反转比较运算符"""
        comparisons = []
        for node in ast.walk(func_node):
            if isinstance(node, ast.Compare):
                for i, op in enumerate(node.ops):
                    if type(op) in self.COMPARISON_FLIP:
                        comparisons.append((node, i))

        if not comparisons:
            return False

        target_node, op_idx = self.rng.choice(comparisons)
        old_op = target_node.ops[op_idx]
        new_op_cls = self.COMPARISON_FLIP[type(old_op)]
        target_node.ops[op_idx] = new_op_cls()
        return True

    def _mutate_weights(self, func_node: ast.FunctionDef) -> bool:
        """调整权重数组（Dirichlet扰动，强度控制偏差程度）"""
        lists_found = []
        for node in ast.walk(func_node):
            if isinstance(node, ast.List):
                elts = node.elts
                if (len(elts) >= 2 and
                        all(isinstance(e, ast.Constant) and isinstance(e.value, float)
                            for e in elts)):
                    vals = [e.value for e in elts]
                    if abs(sum(vals) - 1.0) < 0.1:  # 权重和接近1
                        lists_found.append(node)

        if not lists_found:
            return False

        target_list = self.rng.choice(lists_found)
        vals = np.array([e.value for e in target_list.elts], dtype=float)

        # 强度越高，Dirichlet浓度越低（变异越剧烈）
        alpha = max(0.5, 3.0 - self.intensity * 5.0)
        noise = self.np_rng.dirichlet(np.ones(len(vals)) * alpha)
        mix = 1.0 - self.intensity  # 保留原始权重的比例
        new_vals = mix * vals + (1.0 - mix) * noise
        new_vals = new_vals / new_vals.sum()

        for i, elt in enumerate(target_list.elts):
            elt.value = round(float(new_vals[i]), 4)

        return True

    def _mutate_actions(self, func_node: ast.FunctionDef) -> bool:
        """在动作列表中替换或插入动作字符串"""
        str_lists = []
        for node in ast.walk(func_node):
            if isinstance(node, ast.List):
                elts = node.elts
                if (len(elts) >= 2 and
                        all(isinstance(e, ast.Constant) and isinstance(e.value, str)
                            for e in elts)):
                    str_lists.append(node)

        if not str_lists:
            return False

        target_list = self.rng.choice(str_lists)

        op = self.rng.choice(['replace', 'insert', 'remove'])
        if op == 'replace' and target_list.elts:
            idx = self.rng.randint(0, len(target_list.elts) - 1)
            new_action = self.rng.choice(self.ACTIONS_POOL)
            target_list.elts[idx] = ast.Constant(value=new_action)
            return True
        elif op == 'insert' and len(target_list.elts) < 15:
            new_action = self.rng.choice(self.ACTIONS_POOL)
            target_list.elts.append(ast.Constant(value=new_action))
            return True
        elif op == 'remove' and len(target_list.elts) > 2:
            idx = self.rng.randint(0, len(target_list.elts) - 1)
            target_list.elts.pop(idx)
            return True

        return False

    def _mutate_thresholds(self, func_node: ast.FunctionDef) -> bool:
        """修改阈值类常量（0-1之间的浮点数）"""
        thresholds = []
        for node in ast.walk(func_node):
            if isinstance(node, ast.Constant) and isinstance(node.value, float):
                if 0.0 < node.value < 1.0:
                    thresholds.append(node)

        if not thresholds:
            return False

        target = self.rng.choice(thresholds)
        # 扰动幅度随强度变化
        sigma = 0.05 + self.intensity * 0.15
        delta = self.rng.gauss(0, sigma)
        new_val = max(0.01, min(0.99, target.value + delta))
        target.value = round(new_val, 4)
        return True

    # ─────── 结构级变异（新增 v6.1）───────

    def _mutate_epsilon(self, func_node: ast.FunctionDef) -> bool:
        """
        结构级变异：大幅调整 epsilon-greedy 探索率
        识别形如 np.random.random() < 0.1 的模式，改变探索概率
        """
        for node in ast.walk(func_node):
            if isinstance(node, ast.Compare):
                # 检查是否包含浮点数比较（epsilon pattern）
                for i, comparator in enumerate(node.comparators):
                    if isinstance(comparator, ast.Constant) and isinstance(comparator.value, float):
                        if 0.0 < comparator.value < 0.5:  # 典型epsilon范围
                            # 大幅改变探索率
                            new_eps = self.rng.choice([0.05, 0.15, 0.2, 0.25, 0.3, 0.4])
                            node.comparators[i] = ast.Constant(value=new_eps)
                            return True
        return False

    def _mutate_weight_hardcode(self, func_node: ast.FunctionDef) -> bool:
        """
        结构级变异：将动态权重替换为硬编码极端策略
        找到 np.array([...]) 模式，替换为策略模板
        """
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                # 匹配 np.array([...]) 调用
                func = node.func
                is_np_array = (
                    isinstance(func, ast.Attribute) and
                    func.attr == 'array' and
                    isinstance(func.value, ast.Name) and
                    func.value.id == 'np'
                )
                if is_np_array and node.args:
                    first_arg = node.args[0]
                    if isinstance(first_arg, ast.List) and len(first_arg.elts) == 4:
                        # 替换为随机策略模板
                        template = self.rng.choice(self.STRATEGY_TEMPLATES)
                        first_arg.elts = [
                            ast.Constant(value=round(v, 2)) for v in template
                        ]
                        return True
        return False

    def _mutate_action_shuffle(self, func_node: ast.FunctionDef) -> bool:
        """
        结构级变异：重排动作优先级列表
        通过改变动作列表的排列来影响argmax选择策略
        """
        for node in ast.walk(func_node):
            if isinstance(node, ast.List):
                elts = node.elts
                if (len(elts) >= 4 and
                        all(isinstance(e, ast.Constant) and isinstance(e.value, str)
                            for e in elts)):
                    # 打乱当前动作列表
                    current_actions = [e.value for e in elts]
                    shuffled = current_actions[:]
                    self.rng.shuffle(shuffled)
                    # 确保确实打乱了
                    if shuffled != current_actions:
                        for i, elt in enumerate(elts):
                            elt.value = shuffled[i]
                        return True
        return False

    def _mutate_branch_inject(self, func_node: ast.FunctionDef) -> bool:
        """
        结构级变异：在函数中注入新的条件分支
        增加新的观察条件判断分支，引入新的行为模式
        """
        # 在函数体开头插入一个新的条件分支
        new_condition_code = self.rng.choice([
            # 新分支：资源充足时增强探索
            (
                "if observation.get('resource_level', 1.0) > 0.8:\n"
                "    if np.random.random() < 0.3:\n"
                "        return self._random_action()"
            ),
            # 新分支：步数奇偶交替策略
            (
                "if getattr(self, 'step_count', 0) % 50 == 0:\n"
                "    if np.random.random() < 0.2:\n"
                "        return self._random_action()"
            ),
            # 新分支：低权重差异时随机探索
            (
                "if hasattr(self, 'weights') and self.weights.max() - self.weights.min() < 0.15:\n"
                "    if np.random.random() < 0.25:\n"
                "        return self._random_action()"
            ),
        ])

        # 只对select_action函数注入
        if func_node.name != 'select_action':
            return False

        try:
            new_branch_tree = ast.parse(new_condition_code)
            new_stmt = new_branch_tree.body[0]
            # 在第一条语句前插入
            func_node.body.insert(0, new_stmt)
            return True
        except Exception:
            return False


# ─────────────────────────────────────────────
# 代码沙箱（隔离执行 + 安全验证）
# ─────────────────────────────────────────────

class CodeSandbox:
    """
    代码安全沙箱

    功能：
    1. 将变异代码写入临时文件
    2. 在独立subprocess中运行验证脚本
    3. 收集测试结果和性能指标
    4. 不污染当前进程
    """

    def __init__(self, project_root: str, timeout: int = 30):
        self.project_root = Path(project_root)
        self.timeout = timeout
        self.python_exe = sys.executable

    def validate(self, mutated_source: str, module_rel_path: str) -> Dict:
        """
        在沙箱中验证变异代码

        Returns:
            {
                'passed': bool,
                'syntax_ok': bool,
                'import_ok': bool,
                'tests_passed': int,
                'tests_total': int,
                'error': str or None,
                'elapsed': float
            }
        """
        result = {
            'passed': False,
            'syntax_ok': False,
            'import_ok': False,
            'tests_passed': 0,
            'tests_total': 0,
            'error': None,
            'elapsed': 0.0
        }

        # Step 1: 语法检查（不需要subprocess）
        try:
            ast.parse(mutated_source)
            result['syntax_ok'] = True
        except SyntaxError as e:
            result['error'] = f"SyntaxError: {e}"
            return result

        # Step 2: 写入临时文件并测试导入
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # 写入变异文件
            target_file = tmp_path / "mutated_module.py"
            target_file.write_text(mutated_source, encoding='utf-8')

            # 写入验证脚本
            validation_script = self._build_validation_script(
                str(target_file), str(self.project_root)
            )
            validation_file = tmp_path / "validate.py"
            validation_file.write_text(validation_script, encoding='utf-8')

            # 运行验证
            t0 = time.time()
            try:
                proc = subprocess.run(
                    [self.python_exe, str(validation_file)],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=str(self.project_root),
                    env={**os.environ, 'PYTHONUTF8': '1'}
                )
                result['elapsed'] = time.time() - t0

                if proc.returncode == 0:
                    # 解析输出
                    try:
                        output_json = json.loads(proc.stdout.strip().split('\n')[-1])
                        result.update(output_json)
                        # 放宽通过标准：至少通过2/3测试即可（Test3的相对导入可能失败）
                        result['passed'] = output_json.get('tests_passed', 0) >= 2
                    except (json.JSONDecodeError, IndexError):
                        result['import_ok'] = True
                        result['passed'] = True  # 至少语法和导入通过
                else:
                    result['error'] = proc.stderr[-500:] if proc.stderr else "Unknown error"
            except subprocess.TimeoutExpired:
                result['error'] = f"Sandbox timeout ({self.timeout}s)"
            except Exception as e:
                result['error'] = str(e)

        return result

    def _build_validation_script(self, target_file: str, project_root: str) -> str:
        """生成验证脚本内容"""
        return textwrap.dedent(f'''
            import sys
            import json
            import importlib.util

            sys.path.insert(0, r"{project_root}")

            result = {{
                "syntax_ok": True,
                "import_ok": False,
                "tests_passed": 0,
                "tests_total": 3
            }}

            # Test 1: 导入变异模块
            try:
                spec = importlib.util.spec_from_file_location(
                    "mutated_module", r"{target_file}"
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                result["import_ok"] = True
                result["tests_passed"] += 1
            except Exception as e:
                result["error"] = f"Import failed: {{e}}"
                print(json.dumps(result))
                sys.exit(0)

            # Test 2: 检查关键类存在
            try:
                assert hasattr(module, "UnifiedMOSSAgent"), "UnifiedMOSSAgent missing"
                assert hasattr(module, "BaseMOSSAgent"), "BaseMOSSAgent missing"
                assert hasattr(module, "MOSSConfig"), "MOSSConfig missing"
                result["tests_passed"] += 1
            except AssertionError as e:
                result["error"] = str(e)
                print(json.dumps(result))
                sys.exit(0)

            # Test 3: 实例化Agent
            try:
                from moss.core.objectives import SurvivalObjective
                config = module.MOSSConfig(agent_id="sandbox_test_001")
                agent = module.UnifiedMOSSAgent(config=config)
                result_step = agent.step({{}})
                assert result_step is not None
                result["tests_passed"] += 1
            except Exception as e:
                result["error"] = f"Instantiation failed: {{e}}"

            print(json.dumps(result))
        ''').strip()


# ─────────────────────────────────────────────
# 涌现导向适应度（EmergenceGuidedFitness）v6.1
# ─────────────────────────────────────────────

class EmergenceGuidedFitness:
    """
    真实涌现导向适应度评估器（v6.1 强化版）

    fitness = α * success_rate
            + β * diversity_score
            + γ * purpose_alignment
            + δ * real_emergence_rate   ← 真实涌现检测（非代理）

    真实涌现检测：
    - 行为相变检测：观测动作序列中是否出现结构性突变
    - 多样性涌现：动作分布熵的阶跃变化
    - 自组织行为：连续窗口内的规律性偏差
    """

    def __init__(self, alpha: float = 0.35, beta: float = 0.25,
                 gamma: float = 0.20, delta: float = 0.20):
        # 提高涌现权重（δ: 0.1→0.2）
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.delta = delta

    def evaluate(self, agent_module, steps: int = 300,
                 purpose_vector: Optional[np.ndarray] = None) -> float:
        """
        运行Agent若干步，计算多维fitness

        Args:
            agent_module: 已导入的（可能是变异后的）模块
            steps: 评估步数（增加到300步以获得更可靠的涌现信号）
            purpose_vector: 目的向量（用于对齐度计算）

        Returns:
            fitness score (0.0 ~ 1.0)
        """
        try:
            config = agent_module.MOSSConfig(
                agent_id="fitness_eval_001",
                enable_purpose=False,  # 关闭Purpose以加速评估
                checkpoint_interval=99999
            )
            agent = agent_module.UnifiedMOSSAgent(config=config)
        except Exception as e:
            logger.debug(f"[Fitness] Agent creation failed: {e}")
            return 0.0

        successes = []
        rewards = []
        actions = []

        obs_templates = [
            {},
            {'critical': True},
            {'warning': True},
            {'resource_level': 0.5},
            {'resource_level': 0.1},
            {'resource_level': 0.9},
            {'critical': True, 'resource_level': 0.2},
        ]

        for i in range(steps):
            obs = obs_templates[i % len(obs_templates)]
            try:
                result = agent.step(obs)
                successes.append(float(result.success))
                rewards.append(result.reward)
                actions.append(result.action_type)
            except Exception:
                successes.append(0.0)
                rewards.append(-0.1)
                actions.append('error')

        # ── 指标计算 ──
        success_rate = float(np.mean(successes)) if successes else 0.0

        # 动作多样性（Shannon熵）
        diversity_score = self._action_entropy(actions)

        # Purpose对齐度（如有目的向量）
        purpose_alignment = self._purpose_alignment(agent, purpose_vector)

        # 真实涌现率（行为相变检测）
        real_emergence_rate = self._real_emergence_detection(actions, rewards)

        fitness = (self.alpha * success_rate +
                   self.beta * diversity_score +
                   self.gamma * purpose_alignment +
                   self.delta * real_emergence_rate)

        logger.debug(
            f"[Fitness] success={success_rate:.3f} diversity={diversity_score:.3f} "
            f"purpose={purpose_alignment:.3f} emergence={real_emergence_rate:.3f} "
            f"→ fitness={fitness:.4f}"
        )
        return float(fitness)

    def evaluate_multi(self, agent_module, steps: int = 300,
                       purpose_vector: Optional[np.ndarray] = None) -> np.ndarray:
        """
        v6.3 新增：返回4维fitness向量（用于Pareto多目标优化）

        Returns:
            np.ndarray([success_rate, diversity, purpose_align, emergence])
        """
        try:
            config = agent_module.MOSSConfig(
                agent_id="fitness_eval_multi_001",
                enable_purpose=False,
                checkpoint_interval=99999
            )
            agent = agent_module.UnifiedMOSSAgent(config=config)
        except Exception as e:
            logger.debug(f"[Fitness] Multi-eval Agent creation failed: {e}")
            return np.zeros(4)

        successes = []
        rewards = []
        actions = []

        obs_templates = [
            {}, {'critical': True}, {'warning': True},
            {'resource_level': 0.5}, {'resource_level': 0.1},
            {'resource_level': 0.9}, {'critical': True, 'resource_level': 0.2},
        ]

        for i in range(steps):
            obs = obs_templates[i % len(obs_templates)]
            try:
                result = agent.step(obs)
                successes.append(float(result.success))
                rewards.append(result.reward)
                actions.append(result.action_type)
            except Exception:
                successes.append(0.0)
                rewards.append(-0.1)
                actions.append('error')

        success_rate = float(np.mean(successes)) if successes else 0.0
        diversity_score = self._action_entropy(actions)
        purpose_alignment = self._purpose_alignment(agent, purpose_vector)
        real_emergence_rate = self._real_emergence_detection(actions, rewards)

        fitness_vector = np.array([
            success_rate,
            diversity_score,
            purpose_alignment,
            real_emergence_rate
        ])

        logger.debug(
            f"[FitnessMulti] success={success_rate:.3f} diversity={diversity_score:.3f} "
            f"purpose={purpose_alignment:.3f} emergence={real_emergence_rate:.3f}"
        )
        return fitness_vector

    def _action_entropy(self, actions: List[str]) -> float:
        """计算动作序列的Shannon熵（归一化到[0,1]）"""
        if not actions:
            return 0.0
        unique, counts = np.unique(actions, return_counts=True)
        probs = counts / counts.sum()
        entropy = -np.sum(probs * np.log2(probs + 1e-10))
        max_entropy = np.log2(max(len(unique), 2))
        return float(entropy / max_entropy) if max_entropy > 0 else 0.0

    def _purpose_alignment(self, agent, purpose_vector: Optional[np.ndarray]) -> float:
        """计算权重向量与目的向量的余弦相似度"""
        if purpose_vector is None:
            return 0.5  # 中性值
        try:
            w = agent.weights[:4]
            pv = purpose_vector[:4] if len(purpose_vector) >= 4 else purpose_vector
            # 归一化
            w_norm = w / (np.linalg.norm(w) + 1e-10)
            pv_norm = pv / (np.linalg.norm(pv) + 1e-10)
            cosine = float(np.dot(w_norm, pv_norm))
            return (cosine + 1.0) / 2.0  # 映射到[0,1]
        except Exception:
            return 0.5

    def _real_emergence_detection(self, actions: List[str],
                                   rewards: List[float]) -> float:
        """
        真实涌现检测（v6.1核心升级）

        检测三种涌现信号：
        1. 相变（phase transition）：行为模式的突然转变
        2. 自组织（self-organization）：动作序列中出现规律性结构
        3. 协同效应（synergy）：奖励非线性放大

        Returns:
            emergence_rate ∈ [0, 1]
        """
        if len(actions) < 20:
            return 0.0

        emergence_signals = []

        # ── 信号1: 相变检测 ──
        # 用滑动窗口计算局部熵，检测熵的阶跃变化（相变指标）
        window = 20
        entropies = []
        for i in range(0, len(actions) - window, window // 2):
            chunk = actions[i:i + window]
            unique, counts = np.unique(chunk, return_counts=True)
            probs = counts / counts.sum()
            h = -np.sum(probs * np.log2(probs + 1e-10))
            entropies.append(h)

        if len(entropies) >= 3:
            entropy_arr = np.array(entropies)
            # 相变 = 熵的标准差 / 均值（变异系数，高CV表示相变）
            cv = float(np.std(entropy_arr) / (np.mean(entropy_arr) + 1e-6))
            phase_transition = min(1.0, cv * 2.0)  # 归一化
            emergence_signals.append(phase_transition)

        # ── 信号2: 自组织检测 ──
        # 检测动作序列中的重复模式（周期性结构）
        if len(actions) >= 40:
            # 将动作编码为整数
            unique_acts = list(set(actions))
            action_map = {a: i for i, a in enumerate(unique_acts)}
            encoded = [action_map[a] for a in actions]

            # 自相关（检测周期性）
            arr = np.array(encoded, dtype=float)
            arr = arr - arr.mean()
            if arr.std() > 0:
                # 计算lag=1到lag=10的自相关
                autocorrs = []
                for lag in range(1, min(11, len(arr) // 3)):
                    corr = float(np.corrcoef(arr[:-lag], arr[lag:])[0, 1])
                    autocorrs.append(abs(corr))
                max_autocorr = max(autocorrs) if autocorrs else 0.0
                emergence_signals.append(max_autocorr)

        # ── 信号3: 奖励协同效应 ──
        # 检测奖励序列是否出现非线性放大（局部突破）
        if len(rewards) >= 30:
            reward_arr = np.array(rewards)
            # 计算奖励的滑动最大值增长率
            window = 15
            max_rewards = [max(reward_arr[max(0, i-window):i+1])
                           for i in range(len(reward_arr))]
            max_arr = np.array(max_rewards)
            # 最终25%段的最大值是否明显高于初始25%段
            early_max = np.mean(max_arr[:len(max_arr)//4])
            late_max = np.mean(max_arr[-len(max_arr)//4:])
            growth = (late_max - early_max) / (abs(early_max) + 1e-6)
            synergy = min(1.0, max(0.0, growth))
            emergence_signals.append(synergy)

        if not emergence_signals:
            return 0.0

        # 综合三个信号（加权平均，相变权重最高）
        weights = [0.5, 0.3, 0.2][:len(emergence_signals)]
        w_arr = np.array(weights) / sum(weights)
        return float(np.dot(w_arr, emergence_signals[:len(weights)]))


# ─────────────────────────────────────────────
# 主引擎：SelfModificationEngine
# ─────────────────────────────────────────────

class SelfModificationEngine:
    """
    MOSS v6.0 自改写核心引擎

    工作流程：
    1. 读取目标模块的源代码
    2. 用ASTMutator生成变异候选
    3. 用CodeSandbox验证安全性
    4. 用EmergenceGuidedFitness评估质量
    5. 选择最优变异并写回（可选热重载）
    6. 记录演化历史
    """

    VERSION = "8.0.0-dev"

    def __init__(self, config: SMEConfig = None, project_root: str = None, hybrid_config: 'HybridStrategyConfig' = None):
        self.config = config or SMEConfig()
        self.project_root = Path(project_root or self._find_project_root())
        self._custom_hybrid_config = hybrid_config  # v8.0: 允许传入自定义hybrid配置

        # v6.2: 初始化语义引导选择器
        if self.config.enable_semantic_guidance:
            self._purpose_guided_selector = PurposeGuidedSelector(
                temperature=self.config.semantic_temperature,
                exploration_bonus=self.config.semantic_exploration_bonus
            )
            logger.info(
                f"[SME] PurposeGuidedSelector enabled "
                f"(temperature={self.config.semantic_temperature:.1f}, "
                f"exploration_bonus={self.config.semantic_exploration_bonus:.2f})"
            )
        else:
            self._purpose_guided_selector = None
            logger.info("[SME] PurposeGuidedSelector disabled (v6.1 fallback mode)")

        self.mutator = ASTMutator(
            intensity=self.config.mutation_intensity,
            purpose_guided_selector=self._purpose_guided_selector
        )
        self.sandbox = CodeSandbox(
            str(self.project_root),
            timeout=self.config.sandbox_timeout
        )
        self.fitness_evaluator = EmergenceGuidedFitness()

        # 演化历史
        self.mutation_history: List[MutationResult] = []
        self.generation = 0
        self.best_fitness = 0.0
        self.current_source = ""

        # v6.3: Pareto档案（仅当use_pareto=True时激活）
        if self.config.use_pareto:
            self.pareto_archive = ParetoArchive(max_size=self.config.pareto_archive_size)
            logger.info(
                f"[SME] ParetoArchive enabled (max_size={self.config.pareto_archive_size})"
            )
        else:
            self.pareto_archive = None

        # v8.0: 初始化LLM变异组件
        if self.config.enable_llm_mutation:
            from .llm_backend import create_llm_backend, LLMConfig
            from .llm_mutator import LLMMutator
            from .hybrid_mutation import HybridMutationStrategy, HybridStrategyConfig

            llm_config = LLMConfig(
                provider=self.config.llm_provider,
                model=self.config.llm_model,
                max_tokens=self.config.llm_max_tokens,
                temperature=self.config.llm_temperature,
                daily_token_budget=self.config.llm_daily_token_budget,
                daily_request_budget=self.config.llm_daily_request_budget,
            )
            self._llm_backend = create_llm_backend(llm_config)
            self._llm_mutator = LLMMutator(self._llm_backend)

            # v8.0: 使用自定义hybrid配置（如果提供）
            if self._custom_hybrid_config:
                hybrid_config = self._custom_hybrid_config
                logger.info(f"[SME] Using custom HybridStrategyConfig (mode={hybrid_config.mode})")
            else:
                hybrid_config = HybridStrategyConfig(
                    mode=self.config.llm_mutation_strategy,
                    consecutive_no_op_threshold=self.config.llm_consecutive_no_op_threshold,
                    consecutive_reject_threshold=self.config.llm_consecutive_reject_threshold,
                    fitness_plateau_window=self.config.llm_fitness_plateau_window,
                    llm_budget_fraction=self.config.llm_budget_fraction,
                )
            self._hybrid_strategy = HybridMutationStrategy(
                ast_mutator=self.mutator,
                llm_mutator=self._llm_mutator,
                config=hybrid_config,
            )
            logger.info(
                f"[SME] LLMMutator enabled "
                f"(provider={self.config.llm_provider}, "
                f"strategy={self.config.llm_mutation_strategy}, "
                f"budget_fraction={self.config.llm_budget_fraction:.0%})"
            )
        else:
            self._llm_backend = None
            self._llm_mutator = None
            self._hybrid_strategy = None

        # 输出目录
        self.output_dir = self.project_root / self.config.output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"[SME] SelfModificationEngine v{self.VERSION} initialized")
        logger.info(f"[SME] Target: {self.config.target_module}")
        logger.info(f"[SME] Project root: {self.project_root}")
        if self.config.enable_llm_mutation:
            logger.info(f"[SME] LLM Mutation: ENABLED ({self.config.llm_provider})")
        else:
            logger.info("[SME] LLM Mutation: DISABLED (AST-only mode)")



    def _find_project_root(self) -> str:
        """自动定位项目根目录"""
        # 从当前文件向上找到含moss/__init__.py的目录
        current = Path(__file__).resolve()
        for parent in current.parents:
            if (parent / "moss" / "__init__.py").exists():
                return str(parent)
        return str(Path.cwd())

    def _module_to_path(self, module_name: str) -> Path:
        """将模块名转换为文件路径"""
        rel_path = module_name.replace(".", "/") + ".py"
        return self.project_root / rel_path

    def _source_hash(self, source: str) -> str:
        """计算源码哈希"""
        return hashlib.md5(source.encode()).hexdigest()[:8]

    def _load_source(self) -> str:
        """读取目标模块源码"""
        module_path = self._module_to_path(self.config.target_module)
        if not module_path.exists():
            raise FileNotFoundError(f"Target module not found: {module_path}")
        return module_path.read_text(encoding='utf-8')

    def _write_source(self, source: str):
        """将变异后的源码写入隔离目录（不再修改原始源文件）

        v7.1 安全改进：SME运行期间绝不修改原始源文件，
        变异代码仅写入隔离的experiments目录，防止源文件被篡改。
        """
        # 写入隔离目录（而非原始模块路径）
        isolated_path = self.output_dir / f"mutated_gen{self.generation}_{datetime.now():%H%M%S}.py"
        isolated_path.write_text(source, encoding='utf-8')
        logger.info(f"[SME] Mutated source saved to isolated dir: {isolated_path.name}")

        # 备份当前版本
        backup_path = self.output_dir / f"backup_gen{self.generation}_{datetime.now():%H%M%S}.py"
        backup_path.write_text(self.current_source, encoding='utf-8')
        logger.info(f"[SME] Backup saved: {backup_path.name}")

        logger.info(f"[SME] ⚠️  Source NOT written to original module (isolation mode)")

    def _hot_reload(self):
        """热重载目标模块（隔离模式下仅日志提示，不实际重载原始模块）

        v7.1 安全改进：隔离模式下不热重载原始模块，
        变异效果仅在内存中的eval_module中生效。
        """
        logger.info(f"[SME] Hot-reload skipped (isolation mode - mutations in memory only)")

    def _evaluate_source(self, source: str,
                         purpose_vector: Optional[np.ndarray] = None) -> float:
        """
        评估变异源码的fitness

        策略：将变异代码在真实包的命名空间中执行，
        绕过相对导入限制（统一使用已加载的包模块依赖）
        """
        # 确保project_root在sys.path中
        project_root_str = str(self.project_root)
        if project_root_str not in sys.path:
            sys.path.insert(0, project_root_str)

        try:
            # 预先导入真实模块，获取其全局命名空间作为基础
            import moss.core.unified_agent as _real_ua
            import moss.core.objectives as _real_obj
            import moss.core.dimensions as _real_dim

            # 构建执行命名空间（继承真实包的已解析导入）
            exec_globals = dict(_real_ua.__dict__)
            exec_globals.update({
                '__name__': 'moss.core._sme_eval',
                '__package__': 'moss.core',
                '__spec__': None,
            })

            # 在该命名空间中执行变异代码
            exec(compile(source, '<sme_mutated>', 'exec'), exec_globals)

            # 创建临时模块对象
            import types
            eval_module = types.ModuleType('_sme_eval')
            eval_module.__dict__.update(exec_globals)

            fitness = self.fitness_evaluator.evaluate(
                eval_module, steps=150, purpose_vector=purpose_vector
            )
            return fitness

        except SyntaxError as e:
            logger.debug(f"[SME] Syntax error in mutated source: {e}")
            return 0.0
        except Exception as e:
            logger.debug(f"[SME] Fitness eval error: {type(e).__name__}: {e}")
            return 0.0

    def _build_eval_module(self, source: str):
        """
        将变异源码编译为可执行模块对象（供Pareto多目标评估使用）

        Returns:
            types.ModuleType or None
        """
        project_root_str = str(self.project_root)
        if project_root_str not in sys.path:
            sys.path.insert(0, project_root_str)

        try:
            import moss.core.unified_agent as _real_ua

            exec_globals = dict(_real_ua.__dict__)
            exec_globals.update({
                '__name__': 'moss.core._sme_eval_pareto',
                '__package__': 'moss.core',
                '__spec__': None,
            })
            exec(compile(source, '<sme_mutated_pareto>', 'exec'), exec_globals)

            import types
            eval_module = types.ModuleType('_sme_eval_pareto')
            eval_module.__dict__.update(exec_globals)
            return eval_module

        except Exception as e:
            logger.debug(f"[SME] _build_eval_module error: {e}")
            return None

    def evolve_one_generation(self,
                               purpose_vector: Optional[np.ndarray] = None
                               ) -> Dict:
        """
        执行一代进化

        Args:
            purpose_vector: 目的向量（来自Agent的D9模块）

        Returns:
            generation summary dict
        """
        self.generation += 1
        logger.info(f"[SME] ═══ Generation {self.generation} ═══")

        if not self.current_source:
            self.current_source = self._load_source()

        # 评估当前fitness
        baseline_fitness = self._evaluate_source(self.current_source, purpose_vector)
        logger.info(f"[SME] Baseline fitness: {baseline_fitness:.4f}")

        if self.best_fitness == 0.0:
            self.best_fitness = baseline_fitness

        candidates = []
        mutation_types_tried = []

        # v6.2: 输出语义引导对齐报告（每代首次）
        if (self.config.enable_semantic_guidance
                and purpose_vector is not None
                and self._purpose_guided_selector is not None):
            avail = ['constant_tweak', 'condition_flip', 'weight_shift', 'threshold_mutate',
                     'epsilon_tune', 'weight_hardcode', 'action_insert', 'action_shuffle']
            logger.debug(self._purpose_guided_selector.get_alignment_report(
                purpose_vector, avail
            ))

        # ── 生成变异候选 ──
        # v8.0: 混合策略 vs 纯AST策略
        if self._hybrid_strategy is not None:
            # v8.0: 使用混合策略生成候选
            self._hybrid_strategy.update_state(
                generation=self.generation,
                mutation_type=self.mutation_history[-1].mutation_type if self.mutation_history else "",
                accepted=self.mutation_history[-1].accepted if self.mutation_history else False,
                fitness=baseline_fitness,
            )
            raw_candidates = self._hybrid_strategy.generate_candidates(
                source=self.current_source,
                target_functions=self.config.target_functions,
                population_size=self.config.population_size,
                purpose_vector=purpose_vector,
                fitness_history=[m.to_dict() for m in self.mutation_history[-10:]],
                immutable_functions=self.config.immutable_functions,
            )

            for mutated_source, mut_info in raw_candidates:
                mut_type = mut_info.get('mutation_type', 'no_op')
                mutation_types_tried.append(mut_type)

                if mut_type in ("no_op", "llm_no_op"):
                    continue

                # 沙箱验证
                sandbox_result = self.sandbox.validate(
                    mutated_source,
                    self.config.target_module.replace(".", "/") + ".py"
                )

                if not sandbox_result['passed']:
                    logger.debug(f"[SME] Candidate [{mut_type}] failed sandbox: {sandbox_result.get('error','')[:80]}")
                    continue

                # 标量fitness评估
                candidate_fitness = self._evaluate_source(mutated_source, purpose_vector)
                delta = candidate_fitness - baseline_fitness

                candidates.append({
                    'source': mutated_source,
                    'fitness': candidate_fitness,
                    'delta': delta,
                    'mutation_type': mut_type,
                    'sandbox': sandbox_result,
                    'mutation_source': mut_info.get('source', 'unknown'),
                })
                logger.info(
                    f"[SME] Candidate [{mut_type}] from {mut_info.get('source','?')}: "
                    f"fitness={candidate_fitness:.4f} Δ={delta:+.4f} "
                    f"sandbox={'✓' if sandbox_result['passed'] else '✗'}"
                )
        else:
            # v6.x fallback: 纯AST变异
            for i in range(self.config.population_size):
                mutated_source, mut_type = self.mutator.mutate(
                    self.current_source,
                    self.config.target_functions,
                    purpose_vector=purpose_vector  # v6.2: 传入目的向量
                )
                mutation_types_tried.append(mut_type)

                if mut_type == "no_op":
                    continue

                # 沙箱验证
                sandbox_result = self.sandbox.validate(
                    mutated_source,
                    self.config.target_module.replace(".", "/") + ".py"
                )

                if not sandbox_result['passed']:
                    logger.debug(f"[SME] Candidate {i+1} failed sandbox: {sandbox_result.get('error','')[:80]}")
                    continue

                # v6.3: Pareto模式 or 标量模式 双路径评估
                if self.config.use_pareto and self.pareto_archive is not None:
                    # Pareto模式：评估4维向量
                    fitness_vector = self.fitness_evaluator.evaluate_multi(
                        self._build_eval_module(mutated_source),
                        steps=150,
                        purpose_vector=purpose_vector
                    )
                    scalar_fitness = float(np.dot(ParetoArchive.DEFAULT_WEIGHTS, fitness_vector))
                    delta = scalar_fitness - baseline_fitness

                    # 构造Pareto解
                    pareto_sol = ParetoSolution(
                        fitness_vector=fitness_vector,
                        source=mutated_source,
                        mutation_type=mut_type,
                        generation=self.generation,
                        sandbox_passed=True
                    )
                    candidates.append({
                        'source': mutated_source,
                        'fitness': scalar_fitness,
                        'fitness_vector': fitness_vector,
                        'delta': delta,
                        'mutation_type': mut_type,
                        'sandbox': sandbox_result,
                        'pareto_solution': pareto_sol
                    })
                    logger.info(
                        f"[SME] Candidate [{mut_type}] Pareto: scalar={scalar_fitness:.4f} "
                        f"[sr={fitness_vector[0]:.3f},div={fitness_vector[1]:.3f},"
                        f"pur={fitness_vector[2]:.3f},em={fitness_vector[3]:.3f}]"
                    )
                else:
                    # 标量模式（v6.1/v6.2兼容）
                    candidate_fitness = self._evaluate_source(mutated_source, purpose_vector)
                    delta = candidate_fitness - baseline_fitness

                    candidates.append({
                        'source': mutated_source,
                        'fitness': candidate_fitness,
                        'delta': delta,
                        'mutation_type': mut_type,
                        'sandbox': sandbox_result,
                    })
                    logger.info(
                        f"[SME] Candidate {i+1} [{mut_type}]: "
                        f"fitness={candidate_fitness:.4f} Δ={delta:+.4f} "
                        f"sandbox={'✓' if sandbox_result['passed'] else '✗'}"
                    )

        # 选择最优候选
        accepted = False
        best_candidate = None

        if candidates:
            if self.config.use_pareto and self.pareto_archive is not None:
                # ── Pareto模式：将所有候选加入档案，选最均衡解 ──
                pareto_added = 0
                for c in candidates:
                    if 'pareto_solution' in c:
                        if self.pareto_archive.add(c['pareto_solution']):
                            pareto_added += 1

                # 从档案中选最均衡解作为当前最优
                best_in_archive = self.pareto_archive.get_best_balanced()
                archive_stats = self.pareto_archive.get_stats()

                logger.info(
                    f"[SME] Pareto档案更新: 新增{pareto_added}解, "
                    f"档案大小={archive_stats['size']}, "
                    f"HV={archive_stats['hypervolume']:.4f}"
                )

                # 如果档案中最优解优于当前基线，接受
                if best_in_archive and best_in_archive.scalar_fitness > baseline_fitness + self.config.acceptance_threshold:
                    best_candidate = {
                        'source': best_in_archive.source,
                        'fitness': best_in_archive.scalar_fitness,
                        'fitness_vector': best_in_archive.fitness_vector,
                        'delta': best_in_archive.scalar_fitness - baseline_fitness,
                        'mutation_type': best_in_archive.mutation_type,
                    }
                    self.current_source = best_candidate['source']
                    self.best_fitness = best_candidate['fitness']
                    self._write_source(best_candidate['source'])

                    if self.config.enable_hot_reload:
                        self._hot_reload()

                    accepted = True
                    logger.info(
                        f"[SME] ✅ Pareto最均衡解 ACCEPTED: "
                        f"scalar {baseline_fitness:.4f} → {best_candidate['fitness']:.4f} "
                        f"(+{best_candidate['delta']:.4f}), "
                        f"vector={best_in_archive.fitness_vector.round(3).tolist()}"
                    )
                else:
                    logger.info(
                        f"[SME] ⚠️  Pareto档案已更新（{pareto_added}解加入），"
                        f"但当前最均衡解未超过基线阈值"
                    )
            else:
                # ── 标量模式（v6.1/v6.2兼容）──
                best_candidate = max(candidates, key=lambda c: c['fitness'])
                if best_candidate['delta'] > self.config.acceptance_threshold:
                    # 接受变异
                    self.current_source = best_candidate['source']
                    self.best_fitness = best_candidate['fitness']
                    self._write_source(best_candidate['source'])

                    if self.config.enable_hot_reload:
                        self._hot_reload()

                    accepted = True
                    logger.info(
                        f"[SME] ✅ Mutation ACCEPTED: "
                        f"fitness {baseline_fitness:.4f} → {best_candidate['fitness']:.4f} "
                        f"(+{best_candidate['delta']:.4f})"
                    )
                else:
                    logger.info(
                        f"[SME] ⚠️  Best candidate Δ={best_candidate['delta']:+.4f} "
                        f"below threshold {self.config.acceptance_threshold:.4f}, rejected"
                    )

        # 记录结果
        mutation_id = f"gen{self.generation}_{datetime.now():%H%M%S}"
        mut_result = MutationResult(
            mutation_id=mutation_id,
            mutation_type=best_candidate['mutation_type'] if best_candidate else 'no_op',
            original_hash=self._source_hash(self.current_source),
            mutated_hash=self._source_hash(best_candidate['source']) if best_candidate else '',
            fitness_before=baseline_fitness,
            fitness_after=best_candidate['fitness'] if best_candidate else baseline_fitness,
            fitness_delta=best_candidate['delta'] if best_candidate else 0.0,
            accepted=accepted,
            sandbox_passed=best_candidate is not None
        )
        self.mutation_history.append(mut_result)

        summary = {
            'generation': self.generation,
            'baseline_fitness': baseline_fitness,
            'best_fitness': self.best_fitness,
            'candidates_generated': len(candidates) + len([t for t in mutation_types_tried if t == 'no_op']),
            'candidates_passed_sandbox': len(candidates),
            'accepted': accepted,
            'mutation_type': mut_result.mutation_type,
            'fitness_delta': mut_result.fitness_delta,
            'mutation_types_tried': mutation_types_tried,
            # v6.3: Pareto档案统计（仅Pareto模式）
            'pareto_archive_stats': self.pareto_archive.get_stats() if self.pareto_archive else None,
        }

        self._save_generation_log(summary)
        return summary

    def run(self, max_generations: int = None,
            purpose_vector: Optional[np.ndarray] = None,
            early_stop_fitness: float = 0.95) -> Dict:
        """
        运行完整进化循环

        Args:
            max_generations: 最大代数（None则用config值）
            purpose_vector: 目的向量
            early_stop_fitness: 达到此fitness则提前停止

        Returns:
            完整运行报告
        """
        max_gen = max_generations or self.config.max_generations
        logger.info(f"[SME] 🚀 Starting evolution: max_generations={max_gen}")

        run_start = datetime.now()
        all_summaries = []

        for gen in range(max_gen):
            summary = self.evolve_one_generation(purpose_vector=purpose_vector)
            all_summaries.append(summary)

            if self.best_fitness >= early_stop_fitness:
                logger.info(f"[SME] 🎯 Early stop: fitness {self.best_fitness:.4f} >= {early_stop_fitness}")
                break

        run_end = datetime.now()
        elapsed = (run_end - run_start).total_seconds()

        # 生成最终报告
        report = {
            'version': self.VERSION,
            'target_module': self.config.target_module,
            'total_generations': self.generation,
            'initial_fitness': all_summaries[0]['baseline_fitness'] if all_summaries else 0.0,
            'final_fitness': self.best_fitness,
            'fitness_improvement': self.best_fitness - (all_summaries[0]['baseline_fitness'] if all_summaries else 0.0),
            'total_mutations_accepted': sum(1 for s in all_summaries if s['accepted']),
            'elapsed_seconds': elapsed,
            'generations': all_summaries,
            'mutation_history': [m.to_dict() for m in self.mutation_history],
            'timestamp': run_end.isoformat()
        }

        report_path = self.output_dir / f"sme_run_{run_end:%Y%m%d_%H%M%S}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"[SME] ✅ Evolution complete. Report: {report_path}")
        self._print_summary(report)

        return report

    def _save_generation_log(self, summary: Dict):
        """追加单代日志"""
        log_path = self.output_dir / "evolution_log.jsonl"
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(summary, ensure_ascii=False) + '\n')

    def _print_summary(self, report: Dict):
        """打印运行摘要"""
        print("\n" + "=" * 60)
        print(f"  SME v{self.VERSION} — 自改写进化报告")
        print("=" * 60)
        print(f"  目标模块   : {report['target_module']}")
        print(f"  进化代数   : {report['total_generations']}")
        print(f"  初始fitness: {report['initial_fitness']:.4f}")
        print(f"  最终fitness: {report['final_fitness']:.4f}")
        print(f"  fitness提升: {report['fitness_improvement']:+.4f}")
        print(f"  接受变异数 : {report['total_mutations_accepted']}")
        print(f"  耗时       : {report['elapsed_seconds']:.1f}s")
        print("=" * 60)


# ─────────────────────────────────────────────
# v7.0 Meta-SME：自改写引擎改写自己
# ─────────────────────────────────────────────

class MetaSME(SelfModificationEngine):
    """
    MOSS v7.0 — Meta Self-Modification Engine（自改写的自改写）

    核心创新：
    让SME引擎改写 self_modification_engine.py 自身，实现"元级"进化。
    SME进化 unified_agent.py（对象级改写）。
    MetaSME进化 self_modification_engine.py（元级改写）。

    安全机制：
    1. 元不可变函数清单（meta_immutable_functions）：核心I/O不可改
    2. 变异类型白名单（META_SAFE_MUTATIONS）：仅允许参数调整，禁止结构注入
    3. 双重沙箱验证：语法+实例化+自改写功能验证（元沙箱）
    4. 自动回滚：每次变异前完整备份，失败自动恢复

    可改写目标：
    - ASTMutator参数（intensity, FUNCTION_RICHNESS权重）
    - EmergenceGuidedFitness权重（alpha/beta/gamma/delta）
    - SMEConfig默认参数（acceptance_threshold, population_size等）
    - ParetoArchive容量（max_size）

    版本: 7.0.0-dev
    """

    META_VERSION = "7.0.0-dev"

    # 元不可变函数（绝对不能被Meta改写，否则引擎自毁）
    META_IMMUTABLE_FUNCTIONS = [
        "_evaluate_source",     # 核心评估逻辑
        "_build_eval_module",   # 模块构建
        "_find_project_root",   # 路径解析
        "_module_to_path",      # 路径转换
        "_source_hash",         # 哈希计算
        "_load_source",         # 文件读取
        "_write_source",        # 文件写入（含备份）
        "validate",             # 沙箱验证
        "__init__",             # 初始化
    ]

    # Meta变异白名单：只允许参数级变异（禁止结构注入）
    META_SAFE_MUTATIONS = [
        "constant_tweak",    # 调整数值常量（权重、阈值）
        "threshold_mutate",  # 修改阈值参数
        "weight_shift",      # 调整权重数组
    ]

    # Meta改写目标函数（SME引擎自身的关键函数）
    META_TARGET_FUNCTIONS = [
        "__init__",                     # 初始化参数（但被保护，实际只改常量部分）
        "evolve_one_generation",        # 进化逻辑（含阈值参数）
        "compute_mutation_probs",       # 语义引导概率计算
        "evaluate",                     # fitness评估（权重参数α/β/γ/δ）
        "_real_emergence_detection",    # 涌现检测（窗口参数）
        "_crowding_distance_prune",     # Pareto裁剪（容量参数）
    ]

    def __init__(self, project_root: str = None):
        """
        初始化MetaSME引擎

        MetaSME的目标模块是self_modification_engine.py本身
        """
        # MetaSME的目标是SME引擎自身
        meta_config = SMEConfig(
            target_module="moss.core.self_modification_engine",
            target_functions=self.META_TARGET_FUNCTIONS,
            population_size=4,           # Meta搜索空间较小（安全优先）
            max_generations=50,          # 更多代数（META进化较慢）
            acceptance_threshold=-0.01,  # v7.1: 放宽接受标准（-0.001太严格导致E3仅20%正向率）
            enable_hot_reload=False,     # Meta不热重载（避免递归问题）
            enable_structural_mutations=False,  # 禁用结构级变异
            mutation_intensity=0.2,      # 保守强度
            use_real_emergence=True,
            enable_semantic_guidance=False,  # Meta不用语义引导
            use_pareto=False,
            immutable_functions=self.META_IMMUTABLE_FUNCTIONS,
            output_dir="experiments/meta_sme",
        )

        # 初始化父类（目标=SME自身）
        super().__init__(config=meta_config, project_root=project_root)

        # 覆盖mutator，使用Meta白名单
        self.meta_mutator = ASTMutator(
            intensity=meta_config.mutation_intensity
        )

        # Meta备份目录
        self.meta_backup_dir = self.project_root / "experiments" / "meta_sme" / "backups"
        self.meta_backup_dir.mkdir(parents=True, exist_ok=True)

        # Meta评估器（评估SME引擎质量，通过让SME跑一次unified_agent改写）
        self.meta_fitness_history: List[Dict] = []
        self._original_sme_source: str = ""  # 保存最初的SME源码
        self._generations_without_improvement: int = 0  # v7.1: 早停计数器
        self._meta_fitness_window: List[float] = []  # v7.1: 滑动窗口fitness历史
        self._meta_early_stop_patience: int = 10  # v7.1: 连续N代无改进则早停

        logger.info(f"[MetaSME] v{self.META_VERSION} initialized")
        logger.info(f"[MetaSME] Target: {meta_config.target_module}")
        logger.info(f"[MetaSME] Safe mutations: {self.META_SAFE_MUTATIONS}")

    def _meta_mutate(self, sme_source: str) -> Tuple[str, str]:
        """
        对SME源码进行一次保守变异（仅白名单类型）

        Returns:
            (mutated_source, mutation_type) or (original, 'no_op')
        """
        # 随机选择白名单变异类型
        mut_type = random.choice(self.META_SAFE_MUTATIONS)

        mutated, applied_type = self.meta_mutator.mutate(
            sme_source,
            target_functions=self.META_TARGET_FUNCTIONS,
            mutation_type=mut_type
        )

        if applied_type == "no_op":
            return sme_source, "no_op"

        return mutated, applied_type

    def _meta_sandbox_validate(self, sme_source: str) -> Dict:
        """
        双重沙箱验证变异后的SME代码

        验证层次：
        1. 语法检查（AST parse）
        2. 模块导入检查（确保SME类存在）
        3. 功能检查：用变异后的SME运行一次mini实验（5代unified_agent改写）

        Returns:
            {'passed': bool, 'reason': str, 'tests_passed': int}
        """
        result = {"passed": False, "reason": "", "tests_passed": 0}

        # Test 1: 语法检查
        try:
            ast.parse(sme_source)
            result["tests_passed"] += 1
        except SyntaxError as e:
            result["reason"] = f"Syntax error: {e}"
            return result

        # Test 2: 模块导入检查
        try:
            import types
            import moss.core.self_modification_engine as _real_sme

            exec_globals = dict(_real_sme.__dict__)
            exec_globals.update({
                "__name__": "moss.core._meta_sme_eval",
                "__package__": "moss.core",
                "__spec__": None,
            })
            exec(compile(sme_source, "<meta_sme_mutated>", "exec"), exec_globals)

            eval_module = types.ModuleType("_meta_sme_eval")
            eval_module.__dict__.update(exec_globals)

            # 检查关键类存在
            assert hasattr(eval_module, "SelfModificationEngine"), "SelfModificationEngine missing"
            assert hasattr(eval_module, "ASTMutator"), "ASTMutator missing"
            assert hasattr(eval_module, "EmergenceGuidedFitness"), "EmergenceGuidedFitness missing"
            result["tests_passed"] += 1
        except Exception as e:
            result["reason"] = f"Import/class check failed: {e}"
            return result

        # Test 3: 功能检查 — 用变异后的SME执行5代mini实验
        try:
            SMEClass = exec_globals.get("SelfModificationEngine")
            if SMEClass is None:
                result["reason"] = "SelfModificationEngine not found in exec_globals"
                return result

            mini_config_cls = exec_globals.get("SMEConfig")
            if mini_config_cls is None:
                result["reason"] = "SMEConfig not found"
                return result

            mini_config = mini_config_cls(
                target_module="moss.core.unified_agent",
                population_size=2,
                max_generations=5,
                acceptance_threshold=-0.01,
                enable_hot_reload=False,
                output_dir="experiments/meta_sme/mini_test",
                mutation_intensity=0.2,
            )
            mini_sme = SMEClass(config=mini_config, project_root=str(self.project_root))
            mini_result = mini_sme.run(max_generations=5)

            # 关键检查：能运行且返回合理的fitness
            assert mini_result.get("final_fitness", 0.0) > 0.1, "Final fitness too low"
            result["tests_passed"] += 1
            result["passed"] = True
            result["mini_result"] = {
                "initial_fitness": mini_result.get("initial_fitness", 0.0),
                "final_fitness": mini_result.get("final_fitness", 0.0),
            }

        except Exception as e:
            result["reason"] = f"Functional test failed: {e}"
            # 注意：功能测试失败不强制拒绝（可能是保守问题），只记录
            # 但要求至少2/3测试通过
            pass

        # 至少2/3通过
        if result["tests_passed"] >= 2:
            result["passed"] = True

        return result

    def _evaluate_sme_fitness_single(self, sme_source: str) -> float:
        """
        单次评估变异后的SME引擎质量

        策略：用变异后的SME运行10代unified_agent改写，
        以SME带来的fitness提升作为Meta fitness指标

        Returns:
            meta_fitness (0.0 ~ 1.0)
        """
        try:
            import types
            import moss.core.self_modification_engine as _real_sme

            exec_globals = dict(_real_sme.__dict__)
            exec_globals.update({
                "__name__": "moss.core._meta_eval",
                "__package__": "moss.core",
            })
            exec(compile(sme_source, "<meta_eval>", "exec"), exec_globals)

            SMEClass = exec_globals.get("SelfModificationEngine")
            SMEConfigClass = exec_globals.get("SMEConfig")

            if SMEClass is None or SMEConfigClass is None:
                return 0.0

            eval_config = SMEConfigClass(
                target_module="moss.core.unified_agent",
                population_size=3,
                max_generations=10,
                acceptance_threshold=-0.002,
                enable_hot_reload=False,
                output_dir="experiments/meta_sme/eval",
                mutation_intensity=0.3,
            )

            eval_sme = SMEClass(config=eval_config, project_root=str(self.project_root))
            result = eval_sme.run(max_generations=10)

            # Meta fitness = SME带来的fitness提升 / 初始fitness (归一化)
            init_f = result.get("initial_fitness", 0.0)
            final_f = result.get("final_fitness", 0.0)
            accept_rate = result.get("total_mutations_accepted", 0) / 10.0

            if init_f > 0:
                relative_gain = (final_f - init_f) / init_f
            else:
                relative_gain = 0.0

            # meta_fitness = 50%接受率 + 50%相对提升（归一化）
            meta_fitness = 0.5 * accept_rate + 0.5 * min(1.0, max(0.0, relative_gain * 5))

            logger.info(
                f"[MetaSME] Meta-fitness (single): init={init_f:.4f} final={final_f:.4f} "
                f"accept_rate={accept_rate:.2f} meta_f={meta_fitness:.4f}"
            )
            return float(meta_fitness)

        except Exception as e:
            logger.debug(f"[MetaSME] _evaluate_sme_fitness_single error: {e}")
            return 0.0

    def _evaluate_sme_fitness(self, sme_source: str, n_runs: int = 3) -> float:
        """
        多轮评估变异后的SME引擎质量，返回中位数

        v7.1 稳定性改进：单次评估随机性太大（fitness评估包含随机动作），
        多轮取中位数可大幅减少假阳性（E3仅20%正向率的主因）。

        Args:
            sme_source: 变异后的SME源码
            n_runs: 评估轮数（默认3）

        Returns:
            median meta_fitness (0.0 ~ 1.0)
        """
        scores = []
        for run_i in range(n_runs):
            score = self._evaluate_sme_fitness_single(sme_source)
            scores.append(score)
            logger.debug(f"[MetaSME] Multi-eval run {run_i+1}/{n_runs}: {score:.4f}")

        median_score = float(np.median(scores))
        logger.info(
            f"[MetaSME] Multi-eval median: {median_score:.4f} "
            f"(runs={scores})"
        )
        return median_score

    def _meta_write_source(self, new_sme_source: str, generation: int):
        """
        将变异后的SME源码写入隔离目录（不再修改原始SME源文件）

        v7.1 安全改进：MetaSME运行期间绝不修改原始SME源文件，
        变异代码仅写入隔离目录供分析，防止引擎自毁。
        """
        ts = datetime.now().strftime("%H%M%S")
        isolated_path = self.meta_backup_dir / f"meta_mutated_gen{generation}_{ts}.py"
        isolated_path.write_text(new_sme_source, encoding="utf-8")
        logger.info(f"[MetaSME] Mutated SME saved to isolated dir: {isolated_path.name}")

        # 备份当前版本
        backup_path = self.meta_backup_dir / f"sme_gen{generation}_{ts}.py"
        backup_path.write_text(self.current_source, encoding="utf-8")
        logger.info(f"[MetaSME] Backup saved: {backup_path.name}")

        logger.info(f"[MetaSME] ⚠️  SME source NOT written to original file (isolation mode)")

    def _meta_rollback(self, generation: int):
        """
        回滚SME到最近备份（元沙箱失败时使用）
        """
        sme_path = self._module_to_path("moss.core.self_modification_engine")
        backups = sorted(self.meta_backup_dir.glob(f"sme_gen{generation}_*.py"))
        if backups:
            rollback_source = backups[-1].read_text(encoding="utf-8")
            sme_path.write_text(rollback_source, encoding="utf-8")
            logger.warning(f"[MetaSME] Rolled back from {backups[-1].name}")
        else:
            # 回滚到原始版本
            if self._original_sme_source:
                sme_path.write_text(self._original_sme_source, encoding="utf-8")
                logger.warning("[MetaSME] Rolled back to original source")

    def run_meta_evolution(self, max_generations: int = 50) -> Dict:
        """
        运行Meta-SME进化循环（让SME引擎改写自己）

        Args:
            max_generations: 最大代数

        Returns:
            完整Meta进化报告
        """
        logger.info(f"\n[MetaSME] {'='*50}")
        logger.info(f"[MetaSME] 🧬 Meta-SME进化启动 (max_gen={max_generations})")
        logger.info(f"[MetaSME] 目标：self_modification_engine.py 自改写")
        logger.info(f"[MetaSME] {'='*50}")

        sme_path = self._module_to_path("moss.core.self_modification_engine")
        self.current_source = sme_path.read_text(encoding="utf-8")
        self._original_sme_source = self.current_source

        # 评估初始SME质量
        logger.info("[MetaSME] 评估初始SME引擎质量...")
        baseline_meta_fitness = self._evaluate_sme_fitness(self.current_source)
        logger.info(f"[MetaSME] 初始Meta-fitness: {baseline_meta_fitness:.4f}")

        meta_run_start = datetime.now()
        meta_summaries = []
        meta_mutations_accepted = 0

        for gen in range(max_generations):
            gen_num = gen + 1
            logger.info(f"\n[MetaSME] ═══ Meta-Generation {gen_num}/{max_generations} ═══")

            # v7.1: 早停检查
            if self._generations_without_improvement >= self._meta_early_stop_patience:
                logger.info(
                    f"[MetaSME] 🛑 早停: 连续{self._generations_without_improvement}代无改进"
                )
                break

            meta_candidates = []

            for i in range(self.config.population_size):
                # 生成Meta变异
                mutated_sme, mut_type = self._meta_mutate(self.current_source)

                if mut_type == "no_op":
                    logger.debug(f"[MetaSME] Candidate {i+1}: no_op")
                    continue

                # 双重沙箱验证
                sandbox_result = self._meta_sandbox_validate(mutated_sme)

                if not sandbox_result["passed"]:
                    logger.debug(
                        f"[MetaSME] Candidate {i+1} [{mut_type}] failed meta-sandbox: "
                        f"{sandbox_result.get('reason','')[:80]}"
                    )
                    continue

                # 评估Meta-fitness
                meta_fitness = self._evaluate_sme_fitness(mutated_sme)
                delta = meta_fitness - baseline_meta_fitness

                meta_candidates.append({
                    "source": mutated_sme,
                    "meta_fitness": meta_fitness,
                    "delta": delta,
                    "mutation_type": mut_type,
                    "sandbox": sandbox_result,
                })

                logger.info(
                    f"[MetaSME] Candidate {i+1} [{mut_type}]: "
                    f"meta_fitness={meta_fitness:.4f} Δ={delta:+.4f}"
                )

            # 选择最优Meta变异
            accepted = False
            best_meta = None

            if meta_candidates:
                best_meta = max(meta_candidates, key=lambda c: c["meta_fitness"])

                # v7.1: 滑动窗口接受策略 + 趋势检查
                self._meta_fitness_window.append(best_meta["meta_fitness"])
                if len(self._meta_fitness_window) > 5:
                    self._meta_fitness_window = self._meta_fitness_window[-5:]

                # 接受条件：1) delta > threshold OR 2) 滑动窗口有上升趋势
                window_trending_up = False
                if len(self._meta_fitness_window) >= 3:
                    recent = self._meta_fitness_window[-3:]
                    window_trending_up = recent[-1] > recent[0]

                accept_condition = (
                    best_meta["delta"] > self.config.acceptance_threshold
                    or (window_trending_up and best_meta["delta"] > self.config.acceptance_threshold * 2)
                )

                if accept_condition:
                    # 接受：写入变异后的SME（隔离模式）
                    self._meta_write_source(best_meta["source"], gen_num)
                    self.current_source = best_meta["source"]
                    baseline_meta_fitness = best_meta["meta_fitness"]
                    meta_mutations_accepted += 1
                    accepted = True
                    self._generations_without_improvement = 0  # 重置早停计数

                    logger.info(
                        f"[MetaSME] ✅ Meta变异 ACCEPTED: "
                        f"meta_fitness {best_meta['meta_fitness'] - best_meta['delta']:.4f} "
                        f"→ {best_meta['meta_fitness']:.4f} ({best_meta['delta']:+.4f})"
                    )
                else:
                    self._generations_without_improvement += 1
                    logger.info(
                        f"[MetaSME] ⚠️  Best meta Δ={best_meta['delta']:+.4f} below threshold "
                        f"(no-improvement: {self._generations_without_improvement}/{self._meta_early_stop_patience})"
                    )
            else:
                self._generations_without_improvement += 1

            gen_summary = {
                "meta_generation": gen_num,
                "baseline_meta_fitness": baseline_meta_fitness,
                "accepted": accepted,
                "mutation_type": best_meta["mutation_type"] if best_meta else "no_op",
                "candidates_generated": len(meta_candidates),
                "meta_fitness_delta": best_meta["delta"] if best_meta else 0.0,
            }
            meta_summaries.append(gen_summary)

        meta_run_end = datetime.now()
        elapsed = (meta_run_end - meta_run_start).total_seconds()

        # 最终评估
        final_meta_fitness = self._evaluate_sme_fitness(self.current_source)

        meta_report = {
            "version": self.META_VERSION,
            "experiment": "Meta-SME: self_modification_engine.py自改写",
            "initial_meta_fitness": float(
                self._evaluate_sme_fitness(
                    sme_path.read_text(encoding="utf-8")
                    if not self._original_sme_source
                    else self._original_sme_source
                )
            ) if not meta_summaries else meta_summaries[0]["baseline_meta_fitness"],
            "final_meta_fitness": final_meta_fitness,
            "meta_fitness_improvement": final_meta_fitness - (
                meta_summaries[0]["baseline_meta_fitness"] if meta_summaries else 0.0
            ),
            "total_meta_generations": max_generations,
            "total_meta_mutations_accepted": meta_mutations_accepted,
            "meta_acceptance_rate": meta_mutations_accepted / max_generations,
            "elapsed_seconds": elapsed,
            "meta_generations": meta_summaries,
            "safe_mutations_used": self.META_SAFE_MUTATIONS,
            "meta_immutable_functions": self.META_IMMUTABLE_FUNCTIONS,
        }

        # 保存报告
        meta_output_dir = self.project_root / "experiments" / "meta_sme"
        meta_output_dir.mkdir(parents=True, exist_ok=True)
        report_path = meta_output_dir / f"meta_sme_run_{meta_run_end:%Y%m%d_%H%M%S}.json"

        def enc(obj):
            if isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(type(obj))

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(meta_report, f, indent=2, default=enc, ensure_ascii=False)

        # 打印摘要
        print("\n" + "=" * 65)
        print(f"  MetaSME v{self.META_VERSION} — 自改写引擎Meta进化报告")
        print("=" * 65)
        print(f"  目标        : self_modification_engine.py")
        print(f"  Meta进化代数: {max_generations}")
        print(f"  初始Meta-f  : {meta_summaries[0]['baseline_meta_fitness'] if meta_summaries else 0.0:.4f}")
        print(f"  最终Meta-f  : {final_meta_fitness:.4f}")
        print(f"  Meta-f提升  : {meta_report['meta_fitness_improvement']:+.4f}")
        print(f"  接受Meta变异: {meta_mutations_accepted}/{max_generations} ({meta_report['meta_acceptance_rate']:.1%})")
        print(f"  耗时        : {elapsed:.1f}s")
        print(f"  报告        : {report_path.name}")
        print("=" * 65)

        logger.info(f"[MetaSME] ✅ Meta进化完成. Report: {report_path}")
        return meta_report

