"""
GeneticProgrammer V2 - 涌现驱动效用优化版

改进:
1. 增加实用性权重 (practicality_weight)
2. 优化适应度函数，鼓励高权重涌现
3. 支持涌现驱动淘汰机制
4. 增加与初始驱动的竞争评估

适应度 = 0.25×corr + 0.15×(1-MSE) + 0.25×behavioral_gain + 0.25×practicality - 0.01×complexity
"""

import numpy as np
import random
import logging
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass

# 从 V1 导入基础组件
from .genetic_programmer import (
    ExprNode, FUNCTIONS, ALL_TERMINALS, random_tree, subtree_crossover,
    subtree_mutation, expr_to_callable, EvolvedDrive
)

logger = logging.getLogger(__name__)


class GeneticProgrammerV2:
    """遗传编程驱动力发现器 V2 - 效用优化版"""

    def __init__(self, config: Dict = None):
        cfg = config or {}
        
        # 基础参数
        self.population_size = cfg.get('population_size', 100)
        self.generations = cfg.get('generations', 50)
        self.max_depth = cfg.get('max_depth', 5)
        self.crossover_rate = cfg.get('crossover_rate', 0.4)
        self.mutation_rate = cfg.get('mutation_rate', 0.3)
        self.tournament_size = cfg.get('tournament_size', 5)
        
        # V2: 新的权重配置
        self.corr_weight = cfg.get('corr_weight', 0.25)
        self.mse_weight = cfg.get('mse_weight', 0.15)
        self.behavioral_gain_weight = cfg.get('behavioral_gain_weight', 0.25)
        self.practicality_weight = cfg.get('practicality_weight', 0.25)  # 新增
        self.complexity_penalty = cfg.get('complexity_penalty', 0.01)
        
        # 验证参数
        self.validation_ratio = cfg.get('validation_ratio', 0.3)
        self.acceptance_threshold = cfg.get('acceptance_threshold', 0.2)
        self.min_samples = cfg.get('min_samples', 20)
        self.null_model_samples = cfg.get('null_model_samples', 100)
        
        # V2: 实用性阈值
        self.practicality_threshold = cfg.get('practicality_threshold', 0.3)
        self.min_weight_target = cfg.get('min_weight_target', 0.20)  # 目标权重 0.20+

    def evolve(self, behavior_labels: List[int], env_states: List[Dict],
               candidate_name: str = None,
               existing_drives: List[Dict] = None) -> Optional[EvolvedDrive]:
        """
        核心进化方法 (V2)
        
        Args:
            behavior_labels: 行为标签
            env_states: 环境状态
            candidate_name: 候选名称
            existing_drives: 现有驱动力列表 (V2新增，用于竞争评估)
        """
        if len(behavior_labels) < self.min_samples:
            return None

        B = np.array(behavior_labels, dtype=float)
        if B.sum() < 3 or (1 - B).sum() < 3:
            return None

        # 扩展特征
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

        best_tree = None
        best_fitness = -float('inf')
        best_practicality = 0.0

        for gen in range(self.generations):
            # 评估 (V2: 使用新的适应度函数)
            fitnesses = []
            practicalities = []
            for tree in population:
                fit, pract = self._fitness_v2(tree, B_train, X_train, existing_drives)
                fitnesses.append(fit)
                practicalities.append(pract)

            # 记录最优
            gen_best_idx = int(np.argmax(fitnesses))
            if fitnesses[gen_best_idx] > best_fitness:
                best_fitness = fitnesses[gen_best_idx]
                best_tree = population[gen_best_idx].copy()
                best_practicality = practicalities[gen_best_idx]

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
                recent_best = self._fitness_v2(best_tree, B_train, X_train, existing_drives)[0]
                if abs(recent_best - best_fitness) < 1e-6:
                    break

        if best_tree is None:
            return None

        # 验证集评估
        val_fitness, val_practicality = self._fitness_v2(best_tree, B_val, X_val, existing_drives)
        if val_fitness < self.acceptance_threshold:
            return None

        # V2: 实用性检查
        if val_practicality < self.practicality_threshold:
            logger.warning(f"候选驱动实用性不足: {val_practicality:.3f} < {self.practicality_threshold}")
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

    def _fitness_v2(self, tree: ExprNode, B: np.ndarray, X: List[Dict],
                   existing_drives: List[Dict] = None) -> tuple:
        """
        V2 适应度函数
        
        Returns:
            (fitness, practicality)
        """
        predictions = np.array([tree.evaluate(s) for s in X])
        predictions = np.clip(predictions, 0, 1)

        # 惩罚纯常数
        if tree.is_terminal() and tree.value is not None:
            return -1.0, 0.0

        # 基础指标
        if np.std(B) < 1e-8 or np.std(predictions) < 1e-8:
            corr = 0.0
        else:
            corr = abs(np.corrcoef(B, predictions)[0, 1])

        mse = float(np.mean((B - predictions) ** 2))
        gain = self._behavioral_gain_from_preds(B, predictions)
        nc = tree.node_count()

        # V2: 实用性评估
        practicality = self._evaluate_practicality(tree, B, X, existing_drives)

        fitness = (
            self.corr_weight * corr
            + self.mse_weight * (1 - min(mse, 1))
            + self.behavioral_gain_weight * max(gain, 0)
            + self.practicality_weight * practicality
            - self.complexity_penalty * nc
        )
        return float(fitness), practicality

    def _evaluate_practicality(self, tree: ExprNode, B: np.ndarray, X: List[Dict],
                               existing_drives: List[Dict] = None) -> float:
        """
        评估实用性 (V2新增)
        
        实用性 = 区分度 × 独立性 × 稳定性
        """
        predictions = np.array([tree.evaluate(s) for s in X])
        predictions = np.clip(predictions, 0, 1)
        
        # 1. 区分度 (discriminative power)
        high_mask = predictions > 0.5
        low_mask = ~high_mask
        if high_mask.sum() < 3 or low_mask.sum() < 3:
            discriminative = 0.0
        else:
            p_target_high = B[high_mask].mean()
            p_target_low = B[low_mask].mean()
            discriminative = abs(p_target_high - p_target_low)
        
        # 2. 独立性 (independence from existing drives)
        independence = 1.0
        if existing_drives:
            correlations = []
            for drive in existing_drives:
                if 'eval_fn' in drive:
                    try:
                        existing_preds = np.array([drive['eval_fn'](s) for s in X])
                        if np.std(predictions) > 1e-8 and np.std(existing_preds) > 1e-8:
                            corr = abs(np.corrcoef(predictions, existing_preds)[0, 1])
                            correlations.append(corr)
                    except:
                        pass
            if correlations:
                max_corr = max(correlations)
                independence = 1.0 - max_corr  # 越低相关性，越高独立性
        
        # 3. 稳定性 (stability across different states)
        stability = 1.0 - np.std(predictions) / (np.mean(predictions) + 0.001)
        stability = max(0.0, min(1.0, stability))
        
        practicality = (discriminative * 0.4 + independence * 0.4 + stability * 0.2)
        return practicality

    def _augment_features(self, states: List[Dict]) -> List[Dict]:
        """扩展环境状态，加入动态特征"""
        augmented = []
        prev = None
        entropy_history = []
        for s in states:
            s = dict(s)
            curr_entropy = s.get('environment_entropy', 0)
            entropy_history.append(curr_entropy)

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

            s.setdefault('behavior_diversity', 0)
            s.setdefault('novel_command_rate', 0)
            s.setdefault('success_rate_recent', s.get('task_completion', 0.5))

            augmented.append(s)
            prev = s
        return augmented

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
        high_mask = P > 0.5
        low_mask = ~high_mask
        if high_mask.sum() < 3 or low_mask.sum() < 3:
            return 0.0
        p_target_high = B[high_mask].mean()
        p_target_low = B[low_mask].mean()
        return float(p_target_high - p_target_low)

    def _null_model_test(self, tree: ExprNode, B: np.ndarray, X: List[Dict]) -> bool:
        best_fitness = self._fitness_v2(tree, B, X)[0]
        random_fitnesses = []
        for _ in range(self.null_model_samples):
            rtree = random_tree(self.max_depth)
            rf = self._fitness_v2(rtree, B, X)[0]
            random_fitnesses.append(rf)

        random_fitnesses = np.array(random_fitnesses)
        if np.std(random_fitnesses) < 1e-8:
            return best_fitness > np.mean(random_fitnesses)

        z_score = (best_fitness - np.mean(random_fitnesses)) / np.std(random_fitnesses)
        return z_score > 1.96

    def _tournament_select(self, population: List[ExprNode], fitnesses: List[float]) -> ExprNode:
        indices = random.sample(range(len(population)), min(self.tournament_size, len(population)))
        best_idx = max(indices, key=lambda i: fitnesses[i])
        return population[best_idx]

    def _top_n(self, items: List[str], n: int) -> List[str]:
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


# ========== 涌现驱动管理器 V2 ==========

class DriveManagerV2:
    """
    驱动力管理器 V2 - 支持涌现驱动淘汰和竞争
    """
    
    def __init__(self, config: Dict = None):
        self.drives: Dict[str, Dict] = {}
        self.emerged_drives: Dict[str, Dict] = {}
        self.drive_history: List[Dict] = []
        
        # V2: 淘汰机制参数
        self.utility_threshold = config.get('utility_threshold', 0.15) if config else 0.15
        self.min_weight_threshold = config.get('min_weight_threshold', 0.05) if config else 0.05
        self.max_emerged_drives = config.get('max_emerged_drives', 5) if config else 5
        
    def add_emerged_drive(self, drive: EvolvedDrive, initial_weight: float = 0.10):
        """添加涌现驱动，触发竞争机制"""
        if drive.name in self.emerged_drives:
            return False
            
        # V2: 检查数量限制
        if len(self.emerged_drives) >= self.max_emerged_drives:
            # 淘汰最低效用的驱动
            self._prune_least_utility()
        
        self.emerged_drives[drive.name] = {
            'drive': drive,
            'weight': initial_weight,
            'utility_history': [],
            'added_cycle': len(self.drive_history),
        }
        return True
    
    def _prune_least_utility(self):
        """淘汰效用最低的涌现驱动"""
        if len(self.emerged_drives) < self.max_emerged_drives:
            return
            
        # 计算每个驱动的平均效用
        utilities = {}
        for name, data in self.emerged_drives.items():
            if data['utility_history']:
                utilities[name] = np.mean(data['utility_history'])
            else:
                utilities[name] = data['weight']  # 默认用权重
        
        # 找出最低效用的驱动
        if utilities:
            min_utility_name = min(utilities, key=utilities.get)
            if utilities[min_utility_name] < self.utility_threshold:
                logger.info(f"淘汰低效用涌现驱动: {min_utility_name} (效用: {utilities[min_utility_name]:.3f})")
                del self.emerged_drives[min_utility_name]
    
    def update_drive_utility(self, drive_name: str, utility: float):
        """更新驱动效用历史"""
        if drive_name in self.emerged_drives:
            self.emerged_drives[drive_name]['utility_history'].append(utility)
            # 保留最近50个记录
            if len(self.emerged_drives[drive_name]['utility_history']) > 50:
                self.emerged_drives[drive_name]['utility_history'] = self.emerged_drives[drive_name]['utility_history'][-50:]
    
    def get_competitive_weights(self) -> Dict[str, float]:
        """
        获取竞争后的权重
        
        V2: 涌现驱动与初始驱动竞争
        """
        all_weights = {}
        
        # 初始驱动
        for name, drive in self.drives.items():
            all_weights[name] = drive.get('weight', 0.25)
        
        # 涌现驱动 (根据效用调整)
        for name, data in self.emerged_drives.items():
            base_weight = data['weight']
            # 根据效用调整
            if data['utility_history']:
                avg_utility = np.mean(data['utility_history'])
                adjusted_weight = base_weight * (1 + avg_utility)
                all_weights[name] = min(adjusted_weight, 0.35)  # 上限 0.35
            else:
                all_weights[name] = base_weight
        
        # 归一化
        total = sum(all_weights.values())
        if total > 0:
            all_weights = {k: v/total for k, v in all_weights.items()}
        
        return all_weights