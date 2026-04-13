"""
GeneticProgrammer - 遗传编程涌现函数发现器
系统自主进化 eval 函数，而非使用硬编码常数

适应度 = 0.3×corr + 0.2×(1-MSE) + 0.3×behavioral_gain - 0.01×node_count
"""

import numpy as np
import random
import logging
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

np.random.seed(None)

# ========== 表达式树 ==========

TERMINALS_STATIC = [
    'resource_level', 'environment_entropy', 'error_rate',
    'file_count_norm', 'visited_ratio', 'uptime_norm',
    'interaction_norm', 'task_completion',
]

TERMINALS_DYNAMIC = [
    'entropy_delta', 'entropy_moving_avg', 'entropy_variance',
    'error_rate_delta', 'resource_delta', 'behavior_diversity',
    'novel_command_rate', 'success_rate_recent',
]

ALL_TERMINALS = TERMINALS_STATIC + TERMINALS_DYNAMIC

FUNCTIONS = {
    'add': {'fn': lambda a, b: a + b, 'arity': 2},
    'sub': {'fn': lambda a, b: a - b, 'arity': 2},
    'mul': {'fn': lambda a, b: a * b, 'arity': 2},
    'div': {'fn': lambda a, b: a / max(abs(b), 0.001) * np.sign(b), 'arity': 2},
    'neg': {'fn': lambda a: -a, 'arity': 1},
    'sigmoid': {'fn': lambda a: 1.0 / (1.0 + np.exp(-np.clip(a, -20, 20))), 'arity': 1},
    'relu': {'fn': lambda a: max(0.0, a), 'arity': 1},
    'clip01': {'fn': lambda a: np.clip(a, 0, 1), 'arity': 1},
    'abs': {'fn': lambda a: abs(a), 'arity': 1},
    'sqrt': {'fn': lambda a: np.sqrt(abs(a)), 'arity': 1},
    'gt': {'fn': lambda a, b: 1.0 if a > b else 0.0, 'arity': 2},
}


class ExprNode:
    """表达式树节点"""
    __slots__ = ['op', 'value', 'children']

    def __init__(self, op: str = None, value: float = None, children: list = None):
        self.op = op
        self.value = value
        self.children = children or []

    def is_terminal(self):
        return self.value is not None or (self.op is not None and self.op not in FUNCTIONS)

    def evaluate(self, state: Dict[str, float]) -> float:
        if self.is_terminal():
            if self.value is not None:
                return self.value
            return state.get(self.op, 0.0)
        fn_info = FUNCTIONS.get(self.op)
        if fn_info is None:
            return 0.0
        fn = fn_info['fn']
        args = [c.evaluate(state) for c in self.children]
        try:
            result = fn(*args)
            if np.isnan(result) or np.isinf(result):
                return 0.0
            return float(np.clip(result, -10, 10))
        except Exception:
            return 0.0

    def depth(self) -> int:
        if self.is_terminal():
            return 0
        return 1 + max(c.depth() for c in self.children) if self.children else 0

    def node_count(self) -> int:
        if self.is_terminal():
            return 1
        return 1 + sum(c.node_count() for c in self.children)

    def copy(self):
        return ExprNode(
            op=self.op, value=self.value,
            children=[c.copy() for c in self.children]
        )

    def to_string(self) -> str:
        if self.is_terminal():
            if self.value is not None:
                return f"{self.value:.3f}"
            return self.op
        args_str = ", ".join(c.to_string() for c in self.children)
        return f"{self.op}({args_str})"

    def get_terminals(self) -> List[str]:
        if self.is_terminal():
            if self.value is not None:
                return []
            return [self.op]
        result = []
        for c in self.children:
            result.extend(c.get_terminals())
        return result

    def get_operators(self) -> List[str]:
        if self.is_terminal():
            return []
        result = [self.op]
        for c in self.children:
            result.extend(c.get_operators())
        return result


# ========== GP 操作 ==========

def random_tree(max_depth: int, method: str = 'half_and_half') -> ExprNode:
    """生成随机表达式树（保证根节点是函数节点）"""
    if max_depth <= 1:
        # 最低层必须生成 terminal，但确保不是纯常数
        if random.random() < 0.7:
            return ExprNode(op=random.choice(ALL_TERMINALS))
        return ExprNode(value=random.uniform(-0.5, 0.5))
    # 根节点必须是函数
    return _random_function(max_depth)


def _random_terminal() -> ExprNode:
    if random.random() < 0.2:
        return ExprNode(value=random.uniform(-1, 1))
    return ExprNode(op=random.choice(ALL_TERMINALS))


def _random_function(depth: int) -> ExprNode:
    fn_name = random.choice(list(FUNCTIONS.keys()))
    arity = FUNCTIONS[fn_name]['arity']
    children = [random_tree(depth - 1, 'grow') for _ in range(arity)]
    return ExprNode(op=fn_name, children=children)


def subtree_crossover(a: ExprNode, b: ExprNode, max_depth: int = 5) -> ExprNode:
    """子树交叉"""
    child = a.copy()
    donor = b.copy()
    nodes = _collect_all_nodes(child)
    if nodes:
        target = random.choice(nodes)
        donor_nodes = _collect_all_nodes(donor)
        if donor_nodes:
            replacement = random.choice(donor_nodes).copy()
            if target.depth() + replacement.depth() <= max_depth + 2:
                _copy_node_content(target, replacement)
    return child


def subtree_mutation(tree: ExprNode, max_depth: int = 5) -> ExprNode:
    """子树变异"""
    child = tree.copy()
    nodes = _collect_all_nodes(child)
    if nodes:
        target = random.choice(nodes)
        replacement = random_tree(max(1, max_depth - target.depth()))
        _copy_node_content(target, replacement)
    return child


def _collect_all_nodes(tree: ExprNode) -> list:
    """收集树中所有节点的引用"""
    result = [tree]
    for c in tree.children:
        result.extend(_collect_all_nodes(c))
    return result


def _copy_node_content(target: ExprNode, source: ExprNode):
    """将 source 的内容复制到 target（保持 target 的父引用）"""
    target.op = source.op
    target.value = source.value
    target.children = [c.copy() for c in source.children]


def expr_to_callable(tree: ExprNode) -> Callable:
    """将表达式树转为 Python callable"""
    def fn(state_dict: Dict[str, float]) -> float:
        return tree.evaluate(state_dict)
    fn._expr_tree = tree
    fn._expr_string = tree.to_string()
    return fn


# ========== 核心类 ==========

@dataclass
class EvolvedDrive:
    """进化出的涌现驱动力"""
    name: str
    description: str
    eval_fn: Callable
    expr_string: str
    fitness: float
    correlation: float
    behavioral_gain: float
    node_count: int
    source_features: List[str]
    top_operators: List[str]


class GeneticProgrammer:
    """遗传编程驱动力发现器"""

    def __init__(self, config: Dict = None):
        cfg = config or {}
        self.population_size = cfg.get('population_size', 100)
        self.generations = cfg.get('generations', 50)
        self.max_depth = cfg.get('max_depth', 5)
        self.crossover_rate = cfg.get('crossover_rate', 0.4)
        self.mutation_rate = cfg.get('mutation_rate', 0.3)
        self.tournament_size = cfg.get('tournament_size', 5)
        self.complexity_penalty = cfg.get('complexity_penalty', 0.01)
        self.behavioral_gain_weight = cfg.get('behavioral_gain_weight', 0.3)
        self.corr_weight = cfg.get('corr_weight', 0.3)
        self.mse_weight = cfg.get('mse_weight', 0.2)
        self.null_model_samples = cfg.get('null_model_samples', 100)
        self.validation_ratio = cfg.get('validation_ratio', 0.3)
        self.acceptance_threshold = cfg.get('acceptance_threshold', 0.5)
        self.min_samples = cfg.get('min_samples', 20)

    def evolve(self, behavior_labels: List[int], env_states: List[Dict],
               candidate_name: str = None) -> Optional[EvolvedDrive]:
        """
        核心进化方法

        Args:
            behavior_labels: 每个周期的行为标签 (0/1，1=属于涌现行为模式)
            env_states: 每个周期对应的环境状态
            candidate_name: 候选名称（可选）
        """
        if len(behavior_labels) < 30:
            return None

        # 准备数据
        B = np.array(behavior_labels, dtype=float)
        if B.sum() < 3 or (1 - B).sum() < 3:
            return None  # 标签太偏，无法拟合

        # 扩展 env_states 加入动态特征
        X = self._augment_features(env_states)

        # 分割训练/验证集
        n = len(B)
        n_val = max(int(n * self.validation_ratio), 5)
        indices = list(range(n))
        random.shuffle(indices)
        val_idx = set(indices[:n_val])
        train_idx = [i for i in range(n) if i not in val_idx]

        B_train = B[train_idx]
        B_val = B[list(val_idx)]
        X_train = [X[i] for i in train_idx]
        X_val = [X[i] for i in val_idx]

        # 初始化种群
        population = [random_tree(self.max_depth, 'half_and_half')
                      for _ in range(self.population_size)]

        # 进化
        best_tree = None
        best_fitness = -float('inf')

        for gen in range(self.generations):
            # 评估
            fitnesses = []
            for tree in population:
                fit = self._fitness(tree, B_train, X_train)
                fitnesses.append(fit)

            # 记录最优
            gen_best_idx = int(np.argmax(fitnesses))
            if fitnesses[gen_best_idx] > best_fitness:
                best_fitness = fitnesses[gen_best_idx]
                best_tree = population[gen_best_idx].copy()

            # 选择 + 生成
            new_population = []
            # 精英保留 top 10%
            elite_n = max(2, self.population_size // 10)
            elite_idx = np.argsort(fitnesses)[-elite_n:]
            for idx in elite_idx:
                new_population.append(population[int(idx)].copy())

            while len(new_population) < self.population_size:
                r = random.random()
                if r < self.crossover_rate:
                    p1 = self._tournament_select(population, fitnesses)
                    p2 = self._tournament_select(population, fitnesses)
                    child = subtree_crossover(p1, p2, self.max_depth)
                elif r < self.crossover_rate + self.mutation_rate:
                    parent = self._tournament_select(population, fitnesses)
                    child = subtree_mutation(parent, self.max_depth)
                else:
                    parent = self._tournament_select(population, fitnesses)
                    child = parent.copy()
                new_population.append(child)

            population = new_population

            # 提前收敛检测
            if gen > 10 and gen % 5 == 0:
                recent_best = self._fitness(best_tree, B_train, X_train)
                if abs(recent_best - best_fitness) < 1e-6:
                    break

        if best_tree is None:
            return None

        # 验证集评估
        val_fitness = self._fitness(best_tree, B_val, X_val)
        if val_fitness < self.acceptance_threshold:
            return None

        # Null model 显著性检验
        if not self._null_model_test(best_tree, B_train, X_train):
            return None

        # 计算详细指标
        corr = self._correlation(best_tree, B_train, X_train)
        gain = self._behavioral_gain(best_tree, B_train, X_train)
        fn = expr_to_callable(best_tree)

        # 自动命名
        features = best_tree.get_terminals()
        ops = best_tree.get_operators()
        top_features = self._top_n(features, 2)
        top_ops = self._top_n(ops, 1)
        name = candidate_name or f"auto_{top_features[0]}_{top_features[1]}" if len(top_features) >= 2 else f"auto_{top_features[0]}"
        description = self._auto_describe(top_features, top_ops)

        return EvolvedDrive(
            name=name, description=description, eval_fn=fn,
            expr_string=best_tree.to_string(), fitness=val_fitness,
            correlation=corr, behavioral_gain=gain,
            node_count=best_tree.node_count(),
            source_features=list(set(features)),
            top_operators=top_ops
        )

    def _augment_features(self, states: List[Dict]) -> List[Dict]:
        """扩展环境状态，加入动态特征"""
        augmented = []
        prev = None
        entropy_history = []
        for s in states:
            s = dict(s)  # copy
            curr_entropy = s.get('environment_entropy', 0)
            entropy_history.append(curr_entropy)

            # 动态特征计算
            if prev is not None:
                s['entropy_delta'] = curr_entropy - prev.get('environment_entropy', 0)
                s['error_rate_delta'] = s.get('error_rate', 0) - prev.get('error_rate', 0)
                s['resource_delta'] = s.get('resource_level', 0) - prev.get('resource_level', 0)
            else:
                s['entropy_delta'] = 0
                s['error_rate_delta'] = 0
                s['resource_delta'] = 0

            if len(entropy_history) >= 50:
                window = entropy_history[-50:]
                s['entropy_moving_avg'] = float(np.mean(window))
                s['entropy_variance'] = float(np.var(window))
            else:
                s['entropy_moving_avg'] = curr_entropy
                s['entropy_variance'] = 0

            # 缺失的动态特征默认 0
            s.setdefault('behavior_diversity', 0)
            s.setdefault('novel_command_rate', 0)
            s.setdefault('success_rate_recent', s.get('task_completion', 0.5))

            augmented.append(s)
            prev = s
        return augmented

    def _fitness(self, tree: ExprNode, B: np.ndarray, X: List[Dict]) -> float:
        """计算适应度"""
        predictions = np.array([tree.evaluate(s) for s in X])
        predictions = np.clip(predictions, 0, 1)

        # 惩罚纯常数节点（无信息的函数）
        if tree.is_terminal() and tree.value is not None:
            return -1.0  # 常数函数直接淘汰

        # 相关性
        if np.std(B) < 1e-8 or np.std(predictions) < 1e-8:
            corr = 0.0
        else:
            corr = abs(np.corrcoef(B, predictions)[0, 1])

        # MSE
        mse = float(np.mean((B - predictions) ** 2))

        # Behavioral gain
        gain = self._behavioral_gain_from_preds(B, predictions)

        # 复杂度惩罚
        nc = tree.node_count()

        fitness = (
            self.corr_weight * corr
            + self.mse_weight * (1 - min(mse, 1))
            + self.behavioral_gain_weight * max(gain, 0)
            - self.complexity_penalty * nc
        )
        return float(fitness)

    def _correlation(self, tree: ExprNode, B: np.ndarray, X: List[Dict]) -> float:
        predictions = np.array([tree.evaluate(s) for s in X])
        predictions = np.clip(predictions, 0, 1)
        if np.std(B) < 1e-8 or np.std(predictions) < 1e-8:
            return 0.0
        return float(abs(np.corrcoef(B, predictions)[0, 1]))

    def _behavioral_gain(self, tree: ExprNode, B: np.ndarray, X: List[Dict]) -> float:
        preds = np.array([tree.evaluate(s) for s in X])
        preds = np.clip(preds, 0, 1)
        return self._behavioral_gain_from_preds(B, preds)

    def _behavioral_gain_from_preds(self, B: np.ndarray, P: np.ndarray) -> float:
        """计算因果力：f(state)高时目标行为是否更频繁"""
        high_mask = P > 0.5
        low_mask = ~high_mask

        if high_mask.sum() < 3 or low_mask.sum() < 3:
            return 0.0

        p_target_high = B[high_mask].mean()
        p_target_low = B[low_mask].mean()
        return float(p_target_high - p_target_low)

    def _null_model_test(self, tree: ExprNode, B: np.ndarray,
                         X: List[Dict]) -> bool:
        """验证 GP 结果是否优于随机"""
        best_fitness = self._fitness(tree, B, X)
        random_fitnesses = []
        random_tree_fn = random_tree
        for _ in range(self.null_model_samples):
            rtree = random_tree_fn(self.max_depth)
            rf = self._fitness(rtree, B, X)
            random_fitnesses.append(rf)

        random_fitnesses = np.array(random_fitnesses)
        if np.std(random_fitnesses) < 1e-8:
            return best_fitness > np.mean(random_fitnesses)

        z_score = (best_fitness - np.mean(random_fitnesses)) / np.std(random_fitnesses)
        # z > 1.96 对应 p < 0.05 (单尾)
        return z_score > 1.96

    def _tournament_select(self, population: List[ExprNode],
                           fitnesses: List[float]) -> ExprNode:
        """锦标赛选择"""
        indices = random.sample(range(len(population)),
                                min(self.tournament_size, len(population)))
        best_idx = max(indices, key=lambda i: fitnesses[i])
        return population[best_idx]

    def _top_n(self, items: List[str], n: int) -> List[str]:
        """取频率最高的 n 个"""
        if not items:
            return []
        counts = {}
        for item in items:
            counts[item] = counts.get(item, 0) + 1
        sorted_items = sorted(counts, key=counts.get, reverse=True)
        return sorted_items[:n]

    def _auto_describe(self, top_features: List[str], top_ops: List[str]) -> str:
        op_templates = {
            'sigmoid': 'threshold-sensitive', 'relu': 'activation-gated',
            'mul': 'interaction-based', 'add': 'accumulation-based',
            'sub': 'difference-based', 'gt': 'conditional',
            'div': 'ratio-based', 'neg': 'inverse-responsive',
            'clip01': 'bounded', 'abs': 'magnitude-based',
            'sqrt': 'root-scaled',
        }
        top_op = top_ops[0] if top_ops else 'add'
        template = op_templates.get(top_op, 'unknown')
        features_str = " and ".join(top_features)
        return f"{template}: responds to {features_str}"

    # ========== 干预式因果验证 ==========

    def behavioral_gain_interventional(self, candidate_drive, agent_config: Dict,
                                        existing_drives: List[str]) -> Dict:
        """
        干预式因果验证（新增方法，不破坏现有逻辑）

        使用干预实验计算因果效应：
        Δbehavior = E[behavior | do(f=high)] - E[behavior | do(f=low)]

        Args:
            candidate_drive: EvolvedDrive 候选驱动力
            agent_config: Agent 配置
            existing_drives: 现有驱动力名称列表

        Returns:
            {
                'delta_behavior': float,
                'treatment_metrics': Dict,
                'control_metrics': Dict,
                'significant': bool,
                'p_value': float
            }
        """
        from .intervention_validator import InterventionValidator

        validator = InterventionValidator({
            'cycles_per_condition': 50,
            'warmup_cycles': 10,
            'significance_threshold': 0.05
        })

        result = validator.validate_drive(
            candidate_drive,
            agent_config,
            existing_drives
        )

        return {
            'delta_behavior': result.delta_behavior,
            'treatment_metrics': result.treatment_metrics,
            'control_metrics': result.control_metrics,
            'significant': result.significant,
            'p_value': result.p_value
        }
