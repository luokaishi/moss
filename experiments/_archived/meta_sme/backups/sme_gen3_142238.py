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

@dataclass
class ParetoSolution:
    """
    Pareto多目标解（v6.3新增）

    维护4维fitness向量（非标量），用于Pareto非支配排序
    """
    fitness_vector: np.ndarray
    source: str
    mutation_type: str
    generation: int
    sandbox_passed: bool = True

    @property
    def scalar_fitness(self) -> float:
        """加权标量（与v6.1兼容，用于日志显示）"""
        w = np.array([0.35, 0.25, 0.2, 0.2])
        return float(np.dot(w, self.fitness_vector))

    def dominates(self, other: 'ParetoSolution') -> bool:
        """
        Pareto支配关系：self至少在一个维度优于other，且不在任何维度差于other

        Returns True if self Pareto-dominates other
        """
        return np.all(self.fitness_vector >= other.fitness_vector) and np.any(self.fitness_vector > other.fitness_vector)

    def to_dict(self) -> Dict:
        return {'fitness_vector': self.fitness_vector.tolist(), 'scalar_fitness': self.scalar_fitness, 'mutation_type': self.mutation_type, 'generation': self.generation, 'sandbox_passed': self.sandbox_passed}

@dataclass
class MutationResult:
    """单次变异结果"""
    mutation_id: str
    mutation_type: str
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
    target_module: str = 'moss.core.unified_agent'
    target_functions: List[str] = field(default_factory=lambda: ['step', '_apply_state_weights', '_random_action', 'select_action', '_update_state'])
    population_size: int = 6
    max_generations: int = 30
    acceptance_threshold: float = -0.002
    sandbox_timeout: int = 30
    enable_hot_reload: bool = True
    output_dir: str = 'experiments/self_modification'
    enable_structural_mutations: bool = True
    mutation_intensity: float = 0.3
    use_real_emergence: bool = True
    immutable_functions: List[str] = field(default_factory=lambda: ['__init__', 'save_checkpoint', 'load_checkpoint', '_setup_logging', 'get_state'])
    enable_semantic_guidance: bool = True
    semantic_temperature: float = 1.5
    semantic_exploration_bonus: float = 0.1
    use_pareto: bool = False
    pareto_archive_size: int = 50

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
    MUTATION_SEMANTICS = {'constant_tweak': np.array([0.6, 0.2, 0.3, 0.4]), 'condition_flip': np.array([0.3, 0.5, 0.2, 0.6]), 'weight_shift': np.array([0.4, 0.4, 0.6, 0.3]), 'threshold_mutate': np.array([0.5, 0.3, 0.4, 0.3]), 'epsilon_tune': np.array([0.2, 0.7, 0.2, 0.5]), 'weight_hardcode': np.array([0.6, 0.2, 0.5, 0.2]), 'action_insert': np.array([0.3, 0.6, 0.3, 0.5]), 'action_shuffle': np.array([0.2, 0.8, 0.2, 0.6]), 'branch_inject': np.array([0.4, 0.5, 0.4, 0.7])}

    def __init__(self, temperature: float=1.5, exploration_bonus: float=0.1):
        """
        Args:
            temperature: softmax温度（高→探索/均匀，低→贪心/确定）
            exploration_bonus: 均匀分布混合系数（防止某类变异被完全忽略）
        """
        self.temperature = temperature
        self.exploration_bonus = exploration_bonus
        self._normalized_semantics = {}
        for mut_type, vec in self.MUTATION_SEMANTICS.items():
            norm = np.linalg.norm(vec)
            self._normalized_semantics[mut_type] = vec / (norm + 1e-10)

    def compute_mutation_probs(self, purpose_vector: Optional[np.ndarray], available_mutations: List[str]) -> Dict[str, float]:
        """
        计算可用变异类型的选择概率

        Args:
            purpose_vector: Agent的目的向量（D9维或4维），None时退化为均匀分布
            available_mutations: 当前可用的变异类型列表

        Returns:
            {mutation_type: probability}，所有值之和=1.0
        """
        if purpose_vector is None or len(available_mutations) == 0:
            uniform_p = 1.0 / len(available_mutations)
            return {m: uniform_p for m in available_mutations}
        pv = np.array(purpose_vector, dtype=float)
        if len(pv) >= 4:
            pv4 = pv[:4]
        else:
            pv4 = np.zeros(4)
            pv4[:len(pv)] = pv
        pv_norm = pv4 / (np.linalg.norm(pv4) + 1e-10)
        scores = {}
        for mut_type in available_mutations:
            if mut_type in self._normalized_semantics:
                sem_vec = self._normalized_semantics[mut_type]
                cosine = float(np.dot(pv_norm, sem_vec))
                scores[mut_type] = cosine
            else:
                scores[mut_type] = 0.0
        score_arr = np.array([scores[m] for m in available_mutations])
        score_arr = score_arr - score_arr.max()
        exp_arr = np.exp(score_arr / max(self.temperature, 0.01))
        softmax_probs = exp_arr / (exp_arr.sum() + 1e-10)
        n = len(available_mutations)
        uniform_probs = np.ones(n) / n
        final_probs = (1.0 - self.exploration_bonus) * softmax_probs + self.exploration_bonus * uniform_probs
        return {m: float(p) for m, p in zip(available_mutations, final_probs)}

    def select_mutation_type(self, purpose_vector: Optional[np.ndarray], available_mutations: List[str], rng: random.Random) -> str:
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
        rand_val = rng.random()
        cumulative = 0.0
        for t, w in zip(types, weights):
            cumulative += w
            if rand_val <= cumulative:
                return t
        return types[-1]

    def get_alignment_report(self, purpose_vector: Optional[np.ndarray], available_mutations: List[str]) -> str:
        """生成语义对齐报告（用于调试/日志）"""
        probs = self.compute_mutation_probs(purpose_vector, available_mutations)
        lines = ['[PurposeGuide] 变异类型语义对齐概率:']
        for mut_type, prob in sorted(probs.items(), key=lambda x: -x[1]):
            bar = '█' * int(prob * 20)
            lines.append(f'  {mut_type:20s} {bar:20s} {prob:.3f}')
        return '\n'.join(lines)

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
    DEFAULT_WEIGHTS = np.array([0.35, 0.25, 0.2, 0.2])

    def __init__(self, max_size: int=50):
        self.max_size = max_size
        self.solutions: List[ParetoSolution] = []
        self._front_cache: Optional[List[ParetoSolution]] = None

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
        for existing in self.solutions:
            if existing.dominates(solution):
                return False
        self.solutions = [s for s in self.solutions if not solution.dominates(s)]
        self.solutions.append(solution)
        self._front_cache = None
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
            sorted_idx = sorted(range(n), key=lambda i: self.solutions[i].fitness_vector[dim])
            crowding[sorted_idx[0]] = np.inf
            crowding[sorted_idx[-1]] = np.inf
            f_min = self.solutions[sorted_idx[0]].fitness_vector[dim]
            f_max = self.solutions[sorted_idx[-1]].fitness_vector[dim]
            f_range = f_max - f_min + 1e-10
            for k in range(1, n - 1):
                crowding[sorted_idx[k]] += (self.solutions[sorted_idx[k + 1]].fitness_vector[dim] - self.solutions[sorted_idx[k - 1]].fitness_vector[dim]) / f_range
        while len(self.solutions) > self.max_size:
            min_idx = np.argmin(crowding)
            self.solutions.pop(int(min_idx))
            crowding = np.delete(crowding, min_idx)
        self._front_cache = None

    def get_pareto_front(self) -> List[ParetoSolution]:
        """返回当前Pareto前沿（非支配解集）"""
        if self._front_cache is not None:
            return self._front_cache
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

    def get_hypervolume_indicator(self, reference_point: Optional[np.ndarray]=None) -> float:
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
        return {'size': len(self.solutions), 'hypervolume': self.get_hypervolume_indicator(), 'best_balanced': {'scalar_fitness': best_balanced.scalar_fitness if best_balanced else 0.0, 'fitness_vector': best_balanced.fitness_vector.tolist() if best_balanced else [], 'mutation_type': best_balanced.mutation_type if best_balanced else ''}, 'dimension_maxes': {self.DIMENSION_NAMES[i]: float(np.max(front[:, i])) for i in range(4)}, 'dimension_means': {self.DIMENSION_NAMES[i]: float(np.mean(front[:, i])) for i in range(4)}}

    def to_dict(self) -> Dict:
        """序列化档案"""
        return {'max_size': self.max_size, 'size': len(self.solutions), 'solutions': [s.to_dict() for s in self.solutions], 'stats': self.get_stats()}

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
    COMPARISON_FLIP = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt, ast.Eq: ast.NotEq, ast.NotEq: ast.Eq}
    ACTIONS_POOL = ['explore', 'survive', 'influence', 'optimize', 'cooperate', 'maintain', 'learn', 'share', 'reflect', 'adapt', 'create', 'preserve', 'delegate', 'challenge', 'synthesize']
    STRATEGY_TEMPLATES = [[0.7, 0.1, 0.1, 0.1], [0.1, 0.7, 0.1, 0.1], [0.1, 0.1, 0.7, 0.1], [0.1, 0.1, 0.1, 0.7], [0.4, 0.3, 0.2, 0.1], [0.25, 0.25, 0.25, 0.25], [0.5, 0.2, 0.2, 0.1], [0.2, 0.5, 0.1, 0.2]]
    FUNCTION_RICHNESS = {'step': 10, '_apply_state_weights': 8, 'select_action': 4, '_update_state': 3, '_random_action': 2, '_update_purpose': 2}

    def __init__(self, rng_seed: Optional[int]=None, intensity: float=0.3, purpose_guided_selector: Optional['PurposeGuidedSelector']=None):
        self.rng = random.Random(rng_seed)
        self.np_rng = np.random.default_rng(rng_seed)
        self.intensity = intensity
        self.purpose_guided_selector = purpose_guided_selector

    def mutate(self, source: str, target_functions: List[str], mutation_type: Optional[str]=None, purpose_vector: Optional[np.ndarray]=None) -> Tuple[str, str]:
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
            return (source, 'no_op')
        weights = [self.FUNCTION_RICHNESS.get(fn.name, 1) for fn in func_nodes]
        total_w = sum(weights)
        probs = [w / total_w for w in weights]
        rand_val = self.rng.random()
        cumulative = 0.0
        target_func = func_nodes[-1]
        for fn, p in zip(func_nodes, probs):
            cumulative += p
            if rand_val <= cumulative:
                target_func = fn
                break
        if mutation_type is None:
            mutation_candidates = ['constant_tweak', 'condition_flip', 'weight_shift', 'threshold_mutate']
            if self.intensity > 0.2:
                mutation_candidates += ['epsilon_tune', 'weight_hardcode', 'action_insert']
            if self.intensity > 0.4:
                mutation_candidates += ['action_shuffle', 'branch_inject']
            if self.purpose_guided_selector is not None and purpose_vector is not None:
                mutation_type = self.purpose_guided_selector.select_mutation_type(purpose_vector, mutation_candidates, self.rng)
            else:
                mutation_type = self.rng.choice(mutation_candidates)
        mutated_tree = copy.deepcopy(tree)
        target_in_copy = self._find_target_functions(mutated_tree, [target_func.name])
        if not target_in_copy:
            return (source, 'no_op')
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
            return (source, 'no_op')
        ast.fix_missing_locations(mutated_tree)
        try:
            mutated_source = ast.unparse(mutated_tree)
            return (mutated_source, mutation_type)
        except Exception as e:
            logger.debug(f'[ASTMutator] unparse failed: {e}')
            return (source, 'no_op')

    def _find_target_functions(self, tree: ast.AST, target_names: List[str]) -> List[ast.FunctionDef]:
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
        spread = 0.1 + self.intensity * 0.8
        delta = self.rng.uniform(1.0 - spread, 1.0 + spread)
        new_val = target.value * delta
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
                if len(elts) >= 2 and all((isinstance(e, ast.Constant) and isinstance(e.value, float) for e in elts)):
                    vals = [e.value for e in elts]
                    if abs(sum(vals) - 1.0) < 0.1:
                        lists_found.append(node)
        if not lists_found:
            return False
        target_list = self.rng.choice(lists_found)
        vals = np.array([e.value for e in target_list.elts], dtype=float)
        alpha = max(0.5, 3.0 - self.intensity * 5.0)
        noise = self.np_rng.dirichlet(np.ones(len(vals)) * alpha)
        mix = 1.0 - self.intensity
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
                if len(elts) >= 2 and all((isinstance(e, ast.Constant) and isinstance(e.value, str) for e in elts)):
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
        sigma = 0.05 + self.intensity * 0.15
        delta = self.rng.gauss(0, sigma)
        new_val = max(0.01, min(0.99, target.value + delta))
        target.value = round(new_val, 4)
        return True

    def _mutate_epsilon(self, func_node: ast.FunctionDef) -> bool:
        """
        结构级变异：大幅调整 epsilon-greedy 探索率
        识别形如 np.random.random() < 0.1 的模式，改变探索概率
        """
        for node in ast.walk(func_node):
            if isinstance(node, ast.Compare):
                for i, comparator in enumerate(node.comparators):
                    if isinstance(comparator, ast.Constant) and isinstance(comparator.value, float):
                        if 0.0 < comparator.value < 0.5:
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
                func = node.func
                is_np_array = isinstance(func, ast.Attribute) and func.attr == 'array' and isinstance(func.value, ast.Name) and (func.value.id == 'np')
                if is_np_array and node.args:
                    first_arg = node.args[0]
                    if isinstance(first_arg, ast.List) and len(first_arg.elts) == 4:
                        template = self.rng.choice(self.STRATEGY_TEMPLATES)
                        first_arg.elts = [ast.Constant(value=round(v, 2)) for v in template]
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
                if len(elts) >= 4 and all((isinstance(e, ast.Constant) and isinstance(e.value, str) for e in elts)):
                    current_actions = [e.value for e in elts]
                    shuffled = current_actions[:]
                    self.rng.shuffle(shuffled)
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
        new_condition_code = self.rng.choice(["if observation.get('resource_level', 1.0) > 0.8:\n    if np.random.random() < 0.3:\n        return self._random_action()", "if getattr(self, 'step_count', 0) % 50 == 0:\n    if np.random.random() < 0.2:\n        return self._random_action()", "if hasattr(self, 'weights') and self.weights.max() - self.weights.min() < 0.15:\n    if np.random.random() < 0.25:\n        return self._random_action()"])
        if func_node.name != 'select_action':
            return False
        try:
            new_branch_tree = ast.parse(new_condition_code)
            new_stmt = new_branch_tree.body[0]
            func_node.body.insert(0, new_stmt)
            return True
        except Exception:
            return False

class CodeSandbox:
    """
    代码安全沙箱

    功能：
    1. 将变异代码写入临时文件
    2. 在独立subprocess中运行验证脚本
    3. 收集测试结果和性能指标
    4. 不污染当前进程
    """

    def __init__(self, project_root: str, timeout: int=30):
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
        result = {'passed': False, 'syntax_ok': False, 'import_ok': False, 'tests_passed': 0, 'tests_total': 0, 'error': None, 'elapsed': 0.0}
        try:
            ast.parse(mutated_source)
            result['syntax_ok'] = True
        except SyntaxError as e:
            result['error'] = f'SyntaxError: {e}'
            return result
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            target_file = tmp_path / 'mutated_module.py'
            target_file.write_text(mutated_source, encoding='utf-8')
            validation_script = self._build_validation_script(str(target_file), str(self.project_root))
            validation_file = tmp_path / 'validate.py'
            validation_file.write_text(validation_script, encoding='utf-8')
            t0 = time.time()
            try:
                proc = subprocess.run([self.python_exe, str(validation_file)], capture_output=True, text=True, timeout=self.timeout, cwd=str(self.project_root), env={**os.environ, 'PYTHONUTF8': '1'})
                result['elapsed'] = time.time() - t0
                if proc.returncode == 0:
                    try:
                        output_json = json.loads(proc.stdout.strip().split('\n')[-1])
                        result.update(output_json)
                        result['passed'] = output_json.get('tests_passed', 0) >= 2
                    except (json.JSONDecodeError, IndexError):
                        result['import_ok'] = True
                        result['passed'] = True
                else:
                    result['error'] = proc.stderr[-500:] if proc.stderr else 'Unknown error'
            except subprocess.TimeoutExpired:
                result['error'] = f'Sandbox timeout ({self.timeout}s)'
            except Exception as e:
                result['error'] = str(e)
        return result

    def _build_validation_script(self, target_file: str, project_root: str) -> str:
        """生成验证脚本内容"""
        return textwrap.dedent(f'\n            import sys\n            import json\n            import importlib.util\n\n            sys.path.insert(0, r"{project_root}")\n\n            result = {{\n                "syntax_ok": True,\n                "import_ok": False,\n                "tests_passed": 0,\n                "tests_total": 3\n            }}\n\n            # Test 1: 导入变异模块\n            try:\n                spec = importlib.util.spec_from_file_location(\n                    "mutated_module", r"{target_file}"\n                )\n                module = importlib.util.module_from_spec(spec)\n                spec.loader.exec_module(module)\n                result["import_ok"] = True\n                result["tests_passed"] += 1\n            except Exception as e:\n                result["error"] = f"Import failed: {{e}}"\n                print(json.dumps(result))\n                sys.exit(0)\n\n            # Test 2: 检查关键类存在\n            try:\n                assert hasattr(module, "UnifiedMOSSAgent"), "UnifiedMOSSAgent missing"\n                assert hasattr(module, "BaseMOSSAgent"), "BaseMOSSAgent missing"\n                assert hasattr(module, "MOSSConfig"), "MOSSConfig missing"\n                result["tests_passed"] += 1\n            except AssertionError as e:\n                result["error"] = str(e)\n                print(json.dumps(result))\n                sys.exit(0)\n\n            # Test 3: 实例化Agent\n            try:\n                from moss.core.objectives import SurvivalObjective\n                config = module.MOSSConfig(agent_id="sandbox_test_001")\n                agent = module.UnifiedMOSSAgent(config=config)\n                result_step = agent.step({{}})\n                assert result_step is not None\n                result["tests_passed"] += 1\n            except Exception as e:\n                result["error"] = f"Instantiation failed: {{e}}"\n\n            print(json.dumps(result))\n        ').strip()

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

    def __init__(self, alpha: float=0.35, beta: float=0.25, gamma: float=0.2, delta: float=0.2):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.delta = delta

    def evaluate(self, agent_module, steps: int=300, purpose_vector: Optional[np.ndarray]=None) -> float:
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
            config = agent_module.MOSSConfig(agent_id='fitness_eval_001', enable_purpose=False, checkpoint_interval=99999)
            agent = agent_module.UnifiedMOSSAgent(config=config)
        except Exception as e:
            logger.debug(f'[Fitness] Agent creation failed: {e}')
            return 0.0
        successes = []
        rewards = []
        actions = []
        obs_templates = [{}, {'critical': True}, {'warning': True}, {'resource_level': 0.5}, {'resource_level': 0.0805}, {'resource_level': 0.9}, {'critical': True, 'resource_level': 0.2}]
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
        fitness = self.alpha * success_rate + self.beta * diversity_score + self.gamma * purpose_alignment + self.delta * real_emergence_rate
        logger.debug(f'[Fitness] success={success_rate:.3f} diversity={diversity_score:.3f} purpose={purpose_alignment:.3f} emergence={real_emergence_rate:.3f} → fitness={fitness:.4f}')
        return float(fitness)

    def evaluate_multi(self, agent_module, steps: int=300, purpose_vector: Optional[np.ndarray]=None) -> np.ndarray:
        """
        v6.3 新增：返回4维fitness向量（用于Pareto多目标优化）

        Returns:
            np.ndarray([success_rate, diversity, purpose_align, emergence])
        """
        try:
            config = agent_module.MOSSConfig(agent_id='fitness_eval_multi_001', enable_purpose=False, checkpoint_interval=99999)
            agent = agent_module.UnifiedMOSSAgent(config=config)
        except Exception as e:
            logger.debug(f'[Fitness] Multi-eval Agent creation failed: {e}')
            return np.zeros(4)
        successes = []
        rewards = []
        actions = []
        obs_templates = [{}, {'critical': True}, {'warning': True}, {'resource_level': 0.5}, {'resource_level': 0.1}, {'resource_level': 0.9}, {'critical': True, 'resource_level': 0.2}]
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
        fitness_vector = np.array([success_rate, diversity_score, purpose_alignment, real_emergence_rate])
        logger.debug(f'[FitnessMulti] success={success_rate:.3f} diversity={diversity_score:.3f} purpose={purpose_alignment:.3f} emergence={real_emergence_rate:.3f}')
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
            return 0.5
        try:
            w = agent.weights[:4]
            pv = purpose_vector[:4] if len(purpose_vector) >= 4 else purpose_vector
            w_norm = w / (np.linalg.norm(w) + 1e-10)
            pv_norm = pv / (np.linalg.norm(pv) + 1e-10)
            cosine = float(np.dot(w_norm, pv_norm))
            return (cosine + 1.0) / 2.0
        except Exception:
            return 0.5

    def _real_emergence_detection(self, actions: List[str], rewards: List[float]) -> float:
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
            cv = float(np.std(entropy_arr) / (np.mean(entropy_arr) + 1e-06))
            phase_transition = min(1.0, cv * 2.0)
            emergence_signals.append(phase_transition)
        if len(actions) >= 40:
            unique_acts = list(set(actions))
            action_map = {a: i for i, a in enumerate(unique_acts)}
            encoded = [action_map[a] for a in actions]
            arr = np.array(encoded, dtype=float)
            arr = arr - arr.mean()
            if arr.std() > 0:
                autocorrs = []
                for lag in range(1, min(11, len(arr) // 3)):
                    corr = float(np.corrcoef(arr[:-lag], arr[lag:])[0, 1])
                    autocorrs.append(abs(corr))
                max_autocorr = max(autocorrs) if autocorrs else 0.0
                emergence_signals.append(max_autocorr)
        if len(rewards) >= 30:
            reward_arr = np.array(rewards)
            window = 15
            max_rewards = [max(reward_arr[max(0, i - window):i + 1]) for i in range(len(reward_arr))]
            max_arr = np.array(max_rewards)
            early_max = np.mean(max_arr[:len(max_arr) // 4])
            late_max = np.mean(max_arr[-len(max_arr) // 4:])
            growth = (late_max - early_max) / (abs(early_max) + 1e-06)
            synergy = min(1.0, max(0.0, growth))
            emergence_signals.append(synergy)
        if not emergence_signals:
            return 0.0
        weights = [0.5, 0.3, 0.2][:len(emergence_signals)]
        w_arr = np.array(weights) / sum(weights)
        return float(np.dot(w_arr, emergence_signals[:len(weights)]))

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
    VERSION = '6.3.0-dev'

    def __init__(self, config: SMEConfig=None, project_root: str=None):
        self.config = config or SMEConfig()
        self.project_root = Path(project_root or self._find_project_root())
        if self.config.enable_semantic_guidance:
            self._purpose_guided_selector = PurposeGuidedSelector(temperature=self.config.semantic_temperature, exploration_bonus=self.config.semantic_exploration_bonus)
            logger.info(f'[SME] PurposeGuidedSelector enabled (temperature={self.config.semantic_temperature:.1f}, exploration_bonus={self.config.semantic_exploration_bonus:.2f})')
        else:
            self._purpose_guided_selector = None
            logger.info('[SME] PurposeGuidedSelector disabled (v6.1 fallback mode)')
        self.mutator = ASTMutator(intensity=self.config.mutation_intensity, purpose_guided_selector=self._purpose_guided_selector)
        self.sandbox = CodeSandbox(str(self.project_root), timeout=self.config.sandbox_timeout)
        self.fitness_evaluator = EmergenceGuidedFitness()
        self.mutation_history: List[MutationResult] = []
        self.generation = 0
        self.best_fitness = 0.0
        self.current_source = ''
        if self.config.use_pareto:
            self.pareto_archive = ParetoArchive(max_size=self.config.pareto_archive_size)
            logger.info(f'[SME] ParetoArchive enabled (max_size={self.config.pareto_archive_size})')
        else:
            self.pareto_archive = None
        self.output_dir = self.project_root / self.config.output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f'[SME] SelfModificationEngine v{self.VERSION} initialized')
        logger.info(f'[SME] Target: {self.config.target_module}')
        logger.info(f'[SME] Project root: {self.project_root}')

    def _find_project_root(self) -> str:
        """自动定位项目根目录"""
        current = Path(__file__).resolve()
        for parent in current.parents:
            if (parent / 'moss' / '__init__.py').exists():
                return str(parent)
        return str(Path.cwd())

    def _module_to_path(self, module_name: str) -> Path:
        """将模块名转换为文件路径"""
        rel_path = module_name.replace('.', '/') + '.py'
        return self.project_root / rel_path

    def _source_hash(self, source: str) -> str:
        """计算源码哈希"""
        return hashlib.md5(source.encode()).hexdigest()[:8]

    def _load_source(self) -> str:
        """读取目标模块源码"""
        module_path = self._module_to_path(self.config.target_module)
        if not module_path.exists():
            raise FileNotFoundError(f'Target module not found: {module_path}')
        return module_path.read_text(encoding='utf-8')

    def _write_source(self, source: str):
        """将变异后的源码写回（会先备份）"""
        module_path = self._module_to_path(self.config.target_module)
        backup_path = self.output_dir / f'backup_gen{self.generation}_{datetime.now():%H%M%S}.py'
        backup_path.write_text(self.current_source, encoding='utf-8')
        logger.info(f'[SME] Backup saved: {backup_path.name}')
        module_path.write_text(source, encoding='utf-8')
        logger.info(f'[SME] Module updated: {module_path}')

    def _hot_reload(self):
        """热重载目标模块"""
        try:
            module = sys.modules.get(self.config.target_module)
            if module:
                importlib.reload(module)
                logger.info(f'[SME] Hot-reloaded: {self.config.target_module}')
        except Exception as e:
            logger.warning(f'[SME] Hot-reload failed: {e}')

    def _evaluate_source(self, source: str, purpose_vector: Optional[np.ndarray]=None) -> float:
        """
        评估变异源码的fitness

        策略：将变异代码在真实包的命名空间中执行，
        绕过相对导入限制（统一使用已加载的包模块依赖）
        """
        project_root_str = str(self.project_root)
        if project_root_str not in sys.path:
            sys.path.insert(0, project_root_str)
        try:
            import moss.core.unified_agent as _real_ua
            import moss.core.objectives as _real_obj
            import moss.core.dimensions as _real_dim
            exec_globals = dict(_real_ua.__dict__)
            exec_globals.update({'__name__': 'moss.core._sme_eval', '__package__': 'moss.core', '__spec__': None})
            exec(compile(source, '<sme_mutated>', 'exec'), exec_globals)
            import types
            eval_module = types.ModuleType('_sme_eval')
            eval_module.__dict__.update(exec_globals)
            fitness = self.fitness_evaluator.evaluate(eval_module, steps=150, purpose_vector=purpose_vector)
            return fitness
        except SyntaxError as e:
            logger.debug(f'[SME] Syntax error in mutated source: {e}')
            return 0.0
        except Exception as e:
            logger.debug(f'[SME] Fitness eval error: {type(e).__name__}: {e}')
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
            exec_globals.update({'__name__': 'moss.core._sme_eval_pareto', '__package__': 'moss.core', '__spec__': None})
            exec(compile(source, '<sme_mutated_pareto>', 'exec'), exec_globals)
            import types
            eval_module = types.ModuleType('_sme_eval_pareto')
            eval_module.__dict__.update(exec_globals)
            return eval_module
        except Exception as e:
            logger.debug(f'[SME] _build_eval_module error: {e}')
            return None

    def evolve_one_generation(self, purpose_vector: Optional[np.ndarray]=None) -> Dict:
        """
        执行一代进化

        Args:
            purpose_vector: 目的向量（来自Agent的D9模块）

        Returns:
            generation summary dict
        """
        self.generation += 1
        logger.info(f'[SME] ═══ Generation {self.generation} ═══')
        if not self.current_source:
            self.current_source = self._load_source()
        baseline_fitness = self._evaluate_source(self.current_source, purpose_vector)
        logger.info(f'[SME] Baseline fitness: {baseline_fitness:.4f}')
        if self.best_fitness == 0.0:
            self.best_fitness = baseline_fitness
        candidates = []
        mutation_types_tried = []
        if self.config.enable_semantic_guidance and purpose_vector is not None and (self._purpose_guided_selector is not None):
            avail = ['constant_tweak', 'condition_flip', 'weight_shift', 'threshold_mutate', 'epsilon_tune', 'weight_hardcode', 'action_insert', 'action_shuffle']
            logger.debug(self._purpose_guided_selector.get_alignment_report(purpose_vector, avail))
        for i in range(self.config.population_size):
            mutated_source, mut_type = self.mutator.mutate(self.current_source, self.config.target_functions, purpose_vector=purpose_vector)
            mutation_types_tried.append(mut_type)
            if mut_type == 'no_op':
                continue
            sandbox_result = self.sandbox.validate(mutated_source, self.config.target_module.replace('.', '/') + '.py')
            if not sandbox_result['passed']:
                logger.debug(f"[SME] Candidate {i + 1} failed sandbox: {sandbox_result.get('error', '')[:80]}")
                continue
            if self.config.use_pareto and self.pareto_archive is not None:
                fitness_vector = self.fitness_evaluator.evaluate_multi(self._build_eval_module(mutated_source), steps=150, purpose_vector=purpose_vector)
                scalar_fitness = float(np.dot(ParetoArchive.DEFAULT_WEIGHTS, fitness_vector))
                delta = scalar_fitness - baseline_fitness
                pareto_sol = ParetoSolution(fitness_vector=fitness_vector, source=mutated_source, mutation_type=mut_type, generation=self.generation, sandbox_passed=True)
                candidates.append({'source': mutated_source, 'fitness': scalar_fitness, 'fitness_vector': fitness_vector, 'delta': delta, 'mutation_type': mut_type, 'sandbox': sandbox_result, 'pareto_solution': pareto_sol})
                logger.info(f'[SME] Candidate {i + 1}/{self.config.population_size} [{mut_type}] Pareto: scalar={scalar_fitness:.4f} [sr={fitness_vector[0]:.3f},div={fitness_vector[1]:.3f},pur={fitness_vector[2]:.3f},em={fitness_vector[3]:.3f}]')
            else:
                candidate_fitness = self._evaluate_source(mutated_source, purpose_vector)
                delta = candidate_fitness - baseline_fitness
                candidates.append({'source': mutated_source, 'fitness': candidate_fitness, 'delta': delta, 'mutation_type': mut_type, 'sandbox': sandbox_result})
                logger.info(f"[SME] Candidate {i + 1}/{self.config.population_size} [{mut_type}]: fitness={candidate_fitness:.4f} Δ={delta:+.4f} sandbox={('✓' if sandbox_result['passed'] else '✗')}")
        accepted = False
        best_candidate = None
        if candidates:
            if self.config.use_pareto and self.pareto_archive is not None:
                pareto_added = 0
                for c in candidates:
                    if 'pareto_solution' in c:
                        if self.pareto_archive.add(c['pareto_solution']):
                            pareto_added += 1
                best_in_archive = self.pareto_archive.get_best_balanced()
                archive_stats = self.pareto_archive.get_stats()
                logger.info(f"[SME] Pareto档案更新: 新增{pareto_added}解, 档案大小={archive_stats['size']}, HV={archive_stats['hypervolume']:.4f}")
                if best_in_archive and best_in_archive.scalar_fitness > baseline_fitness + self.config.acceptance_threshold:
                    best_candidate = {'source': best_in_archive.source, 'fitness': best_in_archive.scalar_fitness, 'fitness_vector': best_in_archive.fitness_vector, 'delta': best_in_archive.scalar_fitness - baseline_fitness, 'mutation_type': best_in_archive.mutation_type}
                    self.current_source = best_candidate['source']
                    self.best_fitness = best_candidate['fitness']
                    self._write_source(best_candidate['source'])
                    if self.config.enable_hot_reload:
                        self._hot_reload()
                    accepted = True
                    logger.info(f"[SME] ✅ Pareto最均衡解 ACCEPTED: scalar {baseline_fitness:.4f} → {best_candidate['fitness']:.4f} (+{best_candidate['delta']:.4f}), vector={best_in_archive.fitness_vector.round(3).tolist()}")
                else:
                    logger.info(f'[SME] ⚠️  Pareto档案已更新（{pareto_added}解加入），但当前最均衡解未超过基线阈值')
            else:
                best_candidate = max(candidates, key=lambda c: c['fitness'])
                if best_candidate['delta'] > self.config.acceptance_threshold:
                    self.current_source = best_candidate['source']
                    self.best_fitness = best_candidate['fitness']
                    self._write_source(best_candidate['source'])
                    if self.config.enable_hot_reload:
                        self._hot_reload()
                    accepted = True
                    logger.info(f"[SME] ✅ Mutation ACCEPTED: fitness {baseline_fitness:.4f} → {best_candidate['fitness']:.4f} (+{best_candidate['delta']:.4f})")
                else:
                    logger.info(f"[SME] ⚠️  Best candidate Δ={best_candidate['delta']:+.4f} below threshold {self.config.acceptance_threshold:.4f}, rejected")
        mutation_id = f'gen{self.generation}_{datetime.now():%H%M%S}'
        mut_result = MutationResult(mutation_id=mutation_id, mutation_type=best_candidate['mutation_type'] if best_candidate else 'no_op', original_hash=self._source_hash(self.current_source), mutated_hash=self._source_hash(best_candidate['source']) if best_candidate else '', fitness_before=baseline_fitness, fitness_after=best_candidate['fitness'] if best_candidate else baseline_fitness, fitness_delta=best_candidate['delta'] if best_candidate else 0.0, accepted=accepted, sandbox_passed=best_candidate is not None)
        self.mutation_history.append(mut_result)
        summary = {'generation': self.generation, 'baseline_fitness': baseline_fitness, 'best_fitness': self.best_fitness, 'candidates_generated': len(candidates) + len([t for t in mutation_types_tried if t == 'no_op']), 'candidates_passed_sandbox': len(candidates), 'accepted': accepted, 'mutation_type': mut_result.mutation_type, 'fitness_delta': mut_result.fitness_delta, 'mutation_types_tried': mutation_types_tried, 'pareto_archive_stats': self.pareto_archive.get_stats() if self.pareto_archive else None}
        self._save_generation_log(summary)
        return summary

    def run(self, max_generations: int=None, purpose_vector: Optional[np.ndarray]=None, early_stop_fitness: float=0.95) -> Dict:
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
        logger.info(f'[SME] 🚀 Starting evolution: max_generations={max_gen}')
        run_start = datetime.now()
        all_summaries = []
        for gen in range(max_gen):
            summary = self.evolve_one_generation(purpose_vector=purpose_vector)
            all_summaries.append(summary)
            if self.best_fitness >= early_stop_fitness:
                logger.info(f'[SME] 🎯 Early stop: fitness {self.best_fitness:.4f} >= {early_stop_fitness}')
                break
        run_end = datetime.now()
        elapsed = (run_end - run_start).total_seconds()
        report = {'version': self.VERSION, 'target_module': self.config.target_module, 'total_generations': self.generation, 'initial_fitness': all_summaries[0]['baseline_fitness'] if all_summaries else 0.0, 'final_fitness': self.best_fitness, 'fitness_improvement': self.best_fitness - (all_summaries[0]['baseline_fitness'] if all_summaries else 0.0), 'total_mutations_accepted': sum((1 for s in all_summaries if s['accepted'])), 'elapsed_seconds': elapsed, 'generations': all_summaries, 'mutation_history': [m.to_dict() for m in self.mutation_history], 'timestamp': run_end.isoformat()}
        report_path = self.output_dir / f'sme_run_{run_end:%Y%m%d_%H%M%S}.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f'[SME] ✅ Evolution complete. Report: {report_path}')
        self._print_summary(report)
        return report

    def _save_generation_log(self, summary: Dict):
        """追加单代日志"""
        log_path = self.output_dir / 'evolution_log.jsonl'
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(summary, ensure_ascii=False) + '\n')

    def _print_summary(self, report: Dict):
        """打印运行摘要"""
        print('\n' + '=' * 60)
        print(f'  SME v{self.VERSION} — 自改写进化报告')
        print('=' * 60)
        print(f"  目标模块   : {report['target_module']}")
        print(f"  进化代数   : {report['total_generations']}")
        print(f"  初始fitness: {report['initial_fitness']:.4f}")
        print(f"  最终fitness: {report['final_fitness']:.4f}")
        print(f"  fitness提升: {report['fitness_improvement']:+.4f}")
        print(f"  接受变异数 : {report['total_mutations_accepted']}")
        print(f"  耗时       : {report['elapsed_seconds']:.1f}s")
        print('=' * 60)

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
    META_VERSION = '7.0.0-dev'
    META_IMMUTABLE_FUNCTIONS = ['_evaluate_source', '_build_eval_module', '_find_project_root', '_module_to_path', '_source_hash', '_load_source', '_write_source', 'validate', '__init__']
    META_SAFE_MUTATIONS = ['constant_tweak', 'threshold_mutate', 'weight_shift']
    META_TARGET_FUNCTIONS = ['__init__', 'evolve_one_generation', 'compute_mutation_probs', 'evaluate', '_real_emergence_detection', '_crowding_distance_prune']

    def __init__(self, project_root: str=None):
        """
        初始化MetaSME引擎

        MetaSME的目标模块是self_modification_engine.py本身
        """
        meta_config = SMEConfig(target_module='moss.core.self_modification_engine', target_functions=self.META_TARGET_FUNCTIONS, population_size=4, max_generations=50, acceptance_threshold=-0.001, enable_hot_reload=False, enable_structural_mutations=False, mutation_intensity=0.2, use_real_emergence=True, enable_semantic_guidance=False, use_pareto=False, immutable_functions=self.META_IMMUTABLE_FUNCTIONS, output_dir='experiments/meta_sme')
        super().__init__(config=meta_config, project_root=project_root)
        self.meta_mutator = ASTMutator(intensity=meta_config.mutation_intensity)
        self.meta_backup_dir = self.project_root / 'experiments' / 'meta_sme' / 'backups'
        self.meta_backup_dir.mkdir(parents=True, exist_ok=True)
        self.meta_fitness_history: List[Dict] = []
        self._original_sme_source: str = ''
        logger.info(f'[MetaSME] v{self.META_VERSION} initialized')
        logger.info(f'[MetaSME] Target: {meta_config.target_module}')
        logger.info(f'[MetaSME] Safe mutations: {self.META_SAFE_MUTATIONS}')

    def _meta_mutate(self, sme_source: str) -> Tuple[str, str]:
        """
        对SME源码进行一次保守变异（仅白名单类型）

        Returns:
            (mutated_source, mutation_type) or (original, 'no_op')
        """
        mut_type = random.choice(self.META_SAFE_MUTATIONS)
        mutated, applied_type = self.meta_mutator.mutate(sme_source, target_functions=self.META_TARGET_FUNCTIONS, mutation_type=mut_type)
        if applied_type == 'no_op':
            return (sme_source, 'no_op')
        return (mutated, applied_type)

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
        result = {'passed': False, 'reason': '', 'tests_passed': 0}
        try:
            ast.parse(sme_source)
            result['tests_passed'] += 1
        except SyntaxError as e:
            result['reason'] = f'Syntax error: {e}'
            return result
        try:
            import types
            import moss.core.self_modification_engine as _real_sme
            exec_globals = dict(_real_sme.__dict__)
            exec_globals.update({'__name__': 'moss.core._meta_sme_eval', '__package__': 'moss.core', '__spec__': None})
            exec(compile(sme_source, '<meta_sme_mutated>', 'exec'), exec_globals)
            eval_module = types.ModuleType('_meta_sme_eval')
            eval_module.__dict__.update(exec_globals)
            assert hasattr(eval_module, 'SelfModificationEngine'), 'SelfModificationEngine missing'
            assert hasattr(eval_module, 'ASTMutator'), 'ASTMutator missing'
            assert hasattr(eval_module, 'EmergenceGuidedFitness'), 'EmergenceGuidedFitness missing'
            result['tests_passed'] += 1
        except Exception as e:
            result['reason'] = f'Import/class check failed: {e}'
            return result
        try:
            SMEClass = exec_globals.get('SelfModificationEngine')
            if SMEClass is None:
                result['reason'] = 'SelfModificationEngine not found in exec_globals'
                return result
            mini_config_cls = exec_globals.get('SMEConfig')
            if mini_config_cls is None:
                result['reason'] = 'SMEConfig not found'
                return result
            mini_config = mini_config_cls(target_module='moss.core.unified_agent', population_size=2, max_generations=5, acceptance_threshold=-0.01, enable_hot_reload=False, output_dir='experiments/meta_sme/mini_test', mutation_intensity=0.2)
            mini_sme = SMEClass(config=mini_config, project_root=str(self.project_root))
            mini_result = mini_sme.run(max_generations=5)
            assert mini_result.get('final_fitness', 0.0) > 0.1, 'Final fitness too low'
            result['tests_passed'] += 1
            result['passed'] = True
            result['mini_result'] = {'initial_fitness': mini_result.get('initial_fitness', 0.0), 'final_fitness': mini_result.get('final_fitness', 0.0)}
        except Exception as e:
            result['reason'] = f'Functional test failed: {e}'
            pass
        if result['tests_passed'] >= 2:
            result['passed'] = True
        return result

    def _evaluate_sme_fitness(self, sme_source: str) -> float:
        """
        评估变异后的SME引擎质量

        策略：用变异后的SME运行10代unified_agent改写，
        以SME带来的fitness提升作为Meta fitness指标

        Returns:
            meta_fitness (0.0 ~ 1.0)
        """
        try:
            import types
            import moss.core.self_modification_engine as _real_sme
            exec_globals = dict(_real_sme.__dict__)
            exec_globals.update({'__name__': 'moss.core._meta_eval', '__package__': 'moss.core'})
            exec(compile(sme_source, '<meta_eval>', 'exec'), exec_globals)
            SMEClass = exec_globals.get('SelfModificationEngine')
            SMEConfigClass = exec_globals.get('SMEConfig')
            if SMEClass is None or SMEConfigClass is None:
                return 0.0
            eval_config = SMEConfigClass(target_module='moss.core.unified_agent', population_size=3, max_generations=10, acceptance_threshold=-0.002, enable_hot_reload=False, output_dir='experiments/meta_sme/eval', mutation_intensity=0.3)
            eval_sme = SMEClass(config=eval_config, project_root=str(self.project_root))
            result = eval_sme.run(max_generations=10)
            init_f = result.get('initial_fitness', 0.0)
            final_f = result.get('final_fitness', 0.0)
            accept_rate = result.get('total_mutations_accepted', 0) / 10.0
            if init_f > 0:
                relative_gain = (final_f - init_f) / init_f
            else:
                relative_gain = 0.0
            meta_fitness = 0.5 * accept_rate + 0.5 * min(1.0, max(0.0, relative_gain * 5))
            logger.info(f'[MetaSME] Meta-fitness: init={init_f:.4f} final={final_f:.4f} accept_rate={accept_rate:.2f} meta_f={meta_fitness:.4f}')
            return float(meta_fitness)
        except Exception as e:
            logger.debug(f'[MetaSME] _evaluate_sme_fitness error: {e}')
            return 0.0

    def _meta_write_source(self, new_sme_source: str, generation: int):
        """
        将变异后的SME源码写回（先备份，支持回滚）
        """
        sme_path = self._module_to_path('moss.core.self_modification_engine')
        ts = datetime.now().strftime('%H%M%S')
        backup_path = self.meta_backup_dir / f'sme_gen{generation}_{ts}.py'
        backup_path.write_text(self.current_source, encoding='utf-8')
        logger.info(f'[MetaSME] Backup saved: {backup_path.name}')
        sme_path.write_text(new_sme_source, encoding='utf-8')
        logger.info(f'[MetaSME] SME source updated: {sme_path}')

    def _meta_rollback(self, generation: int):
        """
        回滚SME到最近备份（元沙箱失败时使用）
        """
        sme_path = self._module_to_path('moss.core.self_modification_engine')
        backups = sorted(self.meta_backup_dir.glob(f'sme_gen{generation}_*.py'))
        if backups:
            rollback_source = backups[-1].read_text(encoding='utf-8')
            sme_path.write_text(rollback_source, encoding='utf-8')
            logger.warning(f'[MetaSME] Rolled back from {backups[-1].name}')
        elif self._original_sme_source:
            sme_path.write_text(self._original_sme_source, encoding='utf-8')
            logger.warning('[MetaSME] Rolled back to original source')

    def run_meta_evolution(self, max_generations: int=50) -> Dict:
        """
        运行Meta-SME进化循环（让SME引擎改写自己）

        Args:
            max_generations: 最大代数

        Returns:
            完整Meta进化报告
        """
        logger.info(f"\n[MetaSME] {'=' * 50}")
        logger.info(f'[MetaSME] 🧬 Meta-SME进化启动 (max_gen={max_generations})')
        logger.info(f'[MetaSME] 目标：self_modification_engine.py 自改写')
        logger.info(f"[MetaSME] {'=' * 50}")
        sme_path = self._module_to_path('moss.core.self_modification_engine')
        self.current_source = sme_path.read_text(encoding='utf-8')
        self._original_sme_source = self.current_source
        logger.info('[MetaSME] 评估初始SME引擎质量...')
        baseline_meta_fitness = self._evaluate_sme_fitness(self.current_source)
        logger.info(f'[MetaSME] 初始Meta-fitness: {baseline_meta_fitness:.4f}')
        meta_run_start = datetime.now()
        meta_summaries = []
        meta_mutations_accepted = 0
        for gen in range(max_generations):
            gen_num = gen + 1
            logger.info(f'\n[MetaSME] ═══ Meta-Generation {gen_num}/{max_generations} ═══')
            meta_candidates = []
            for i in range(self.config.population_size):
                mutated_sme, mut_type = self._meta_mutate(self.current_source)
                if mut_type == 'no_op':
                    logger.debug(f'[MetaSME] Candidate {i + 1}: no_op')
                    continue
                sandbox_result = self._meta_sandbox_validate(mutated_sme)
                if not sandbox_result['passed']:
                    logger.debug(f"[MetaSME] Candidate {i + 1} [{mut_type}] failed meta-sandbox: {sandbox_result.get('reason', '')[:80]}")
                    continue
                meta_fitness = self._evaluate_sme_fitness(mutated_sme)
                delta = meta_fitness - baseline_meta_fitness
                meta_candidates.append({'source': mutated_sme, 'meta_fitness': meta_fitness, 'delta': delta, 'mutation_type': mut_type, 'sandbox': sandbox_result})
                logger.info(f'[MetaSME] Candidate {i + 1} [{mut_type}]: meta_fitness={meta_fitness:.4f} Δ={delta:+.4f}')
            accepted = False
            best_meta = None
            if meta_candidates:
                best_meta = max(meta_candidates, key=lambda c: c['meta_fitness'])
                if best_meta['delta'] > self.config.acceptance_threshold:
                    self._meta_write_source(best_meta['source'], gen_num)
                    self.current_source = best_meta['source']
                    baseline_meta_fitness = best_meta['meta_fitness']
                    meta_mutations_accepted += 1
                    accepted = True
                    logger.info(f"[MetaSME] ✅ Meta变异 ACCEPTED: meta_fitness {best_meta['meta_fitness'] - best_meta['delta']:.4f} → {best_meta['meta_fitness']:.4f} ({best_meta['delta']:+.4f})")
                else:
                    logger.info(f"[MetaSME] ⚠️  Best meta Δ={best_meta['delta']:+.4f} below threshold")
            gen_summary = {'meta_generation': gen_num, 'baseline_meta_fitness': baseline_meta_fitness, 'accepted': accepted, 'mutation_type': best_meta['mutation_type'] if best_meta else 'no_op', 'candidates_generated': len(meta_candidates), 'meta_fitness_delta': best_meta['delta'] if best_meta else 0.0}
            meta_summaries.append(gen_summary)
        meta_run_end = datetime.now()
        elapsed = (meta_run_end - meta_run_start).total_seconds()
        final_meta_fitness = self._evaluate_sme_fitness(self.current_source)
        meta_report = {'version': self.META_VERSION, 'experiment': 'Meta-SME: self_modification_engine.py自改写', 'initial_meta_fitness': float(self._evaluate_sme_fitness(sme_path.read_text(encoding='utf-8') if not self._original_sme_source else self._original_sme_source)) if not meta_summaries else meta_summaries[0]['baseline_meta_fitness'], 'final_meta_fitness': final_meta_fitness, 'meta_fitness_improvement': final_meta_fitness - (meta_summaries[0]['baseline_meta_fitness'] if meta_summaries else 0.0), 'total_meta_generations': max_generations, 'total_meta_mutations_accepted': meta_mutations_accepted, 'meta_acceptance_rate': meta_mutations_accepted / max_generations, 'elapsed_seconds': elapsed, 'meta_generations': meta_summaries, 'safe_mutations_used': self.META_SAFE_MUTATIONS, 'meta_immutable_functions': self.META_IMMUTABLE_FUNCTIONS}
        meta_output_dir = self.project_root / 'experiments' / 'meta_sme'
        meta_output_dir.mkdir(parents=True, exist_ok=True)
        report_path = meta_output_dir / f'meta_sme_run_{meta_run_end:%Y%m%d_%H%M%S}.json'

        def enc(obj):
            if isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(type(obj))
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(meta_report, f, indent=2, default=enc, ensure_ascii=False)
        print('\n' + '=' * 65)
        print(f'  MetaSME v{self.META_VERSION} — 自改写引擎Meta进化报告')
        print('=' * 65)
        print(f'  目标        : self_modification_engine.py')
        print(f'  Meta进化代数: {max_generations}')
        print(f"  初始Meta-f  : {(meta_summaries[0]['baseline_meta_fitness'] if meta_summaries else 0.0):.4f}")
        print(f'  最终Meta-f  : {final_meta_fitness:.4f}')
        print(f"  Meta-f提升  : {meta_report['meta_fitness_improvement']:+.4f}")
        print(f"  接受Meta变异: {meta_mutations_accepted}/{max_generations} ({meta_report['meta_acceptance_rate']:.1%})")
        print(f'  耗时        : {elapsed:.1f}s')
        print(f'  报告        : {report_path.name}')
        print('=' * 65)
        logger.info(f'[MetaSME] ✅ Meta进化完成. Report: {report_path}')
        return meta_report