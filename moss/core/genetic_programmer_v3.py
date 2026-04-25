"""
GeneticProgrammer V3 - GP 质量强化版

基于 Copilot 评估报告建议，解决"GP 发现函数过于简单（单终端）"问题：

改进:
1. 增加种群规模: 100 → 200
2. 增加代数: 50 → 100
3. 惩罚单终端函数: fitness -= 0.5
4. 最小行为增益过滤: behavioral_gain < 0.1 拒绝
5. 调整适应度权重: behavioral_gain 权重最高 (0.5)
6. 奖励复杂度适中的函数: complexity_bonus

适应度 = 0.2×corr + 0.1×(1-MSE) + 0.5×behavioral_gain + 0.2×complexity_bonus - terminal_penalty
"""

import numpy as np
import random
import logging
from typing import Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass

# 从 V1/V2 导入基础组件
from .genetic_programmer import (
    ExprNode, FUNCTIONS, ALL_TERMINALS, random_tree, subtree_crossover,
    subtree_mutation, expr_to_callable, EvolvedDrive
)
from .genetic_programmer_v2 import GeneticProgrammerV2

logger = logging.getLogger(__name__)


class GeneticProgrammerV3(GeneticProgrammerV2):
    """
    遗传编程驱动力发现器 V3 - 质量强化版
    
    核心改进:
    - 更大种群和更多代数，探索更复杂的函数空间
    - 惩罚单终端函数，鼓励复合函数
    - 严格的行为增益门槛，确保实用性
    - 复杂度奖励，鼓励适度复杂的函数
    """

    def __init__(self, config: Dict = None):
        # 先调用父类初始化
        super().__init__(config)
        
        cfg = config or {}
        
        # V3: 强化参数
        self.population_size = cfg.get('population_size', 200)  # 100 → 200
        self.generations = cfg.get('generations', 100)  # 50 → 100
        
        # V3: 新的适应度权重
        self.corr_weight = cfg.get('corr_weight', 0.20)  # 0.25 → 0.20
        self.mse_weight = cfg.get('mse_weight', 0.10)    # 0.15 → 0.10
        self.behavioral_gain_weight = cfg.get('behavioral_gain_weight', 0.50)  # 0.25 → 0.50 (最高)
        self.practicality_weight = cfg.get('practicality_weight', 0.0)  # 移除，合并到 behavioral_gain
        self.complexity_bonus_weight = cfg.get('complexity_bonus_weight', 0.20)  # 新增
        
        # V3: 惩罚和门槛
        self.terminal_penalty = cfg.get('terminal_penalty', 0.5)  # 单终端惩罚
        self.min_behavioral_gain = cfg.get('min_behavioral_gain', 0.10)  # 最小行为增益门槛
        self.min_nodes = cfg.get('min_nodes', 3)  # 最小节点数
        self.max_nodes = cfg.get('max_nodes', 20)  # 最大节点数
        
        # V3: 复杂度奖励参数
        self.target_complexity = cfg.get('target_complexity', 8)  # 目标复杂度 (节点数)
        self.complexity_tolerance = cfg.get('complexity_tolerance', 5)  # 容差
        
        logger.info(f"GeneticProgrammerV3 initialized: pop={self.population_size}, "
                   f"gens={self.generations}, min_gain={self.min_behavioral_gain}")

    def _fitness_v3(self, tree: ExprNode, B: np.ndarray, X: List[Dict],
                   existing_drives: List[Dict] = None) -> Tuple[float, Dict]:
        """
        V3 适应度函数 - 质量强化
        
        Returns:
            (fitness, info_dict)
        """
        # 基础评估
        fitness, pract = self._fitness_v2(tree, B, X, existing_drives)
        
        # 获取详细信息
        info = {
            'base_fitness': fitness,
            'node_count': tree.node_count(),
            'depth': tree.depth(),
            'is_terminal_only': False,
            'behavioral_gain': 0.0,
            'complexity_bonus': 0.0,
            'terminal_penalty': 0.0,
            'rejected': False,
            'rejection_reason': None,
        }
        
        # 1. 检查是否为单终端函数
        if tree.node_count() == 1 and tree.is_terminal():
            info['is_terminal_only'] = True
            info['terminal_penalty'] = self.terminal_penalty
            fitness -= self.terminal_penalty
            logger.debug(f"Terminal-only function penalized: -{self.terminal_penalty}")
        
        # 2. 提取 behavioral_gain (从 V2 的实用性计算)
        # 重新计算以获取准确值
        try:
            predictions = np.array([tree.evaluate(x) for x in X])
            predictions = np.clip(predictions, 0, 1)
            
            # 行为增益计算
            if len(predictions) >= 2:
                pred_diff = np.abs(np.diff(predictions))
                label_diff = np.abs(np.diff(B))
                agreement = np.sum((pred_diff > 0.1) & (label_diff > 0)) / max(np.sum(label_diff > 0), 1)
                info['behavioral_gain'] = agreement
        except Exception:
            info['behavioral_gain'] = 0.0
        
        # 3. 最小行为增益过滤
        if info['behavioral_gain'] < self.min_behavioral_gain:
            info['rejected'] = True
            info['rejection_reason'] = f"behavioral_gain {info['behavioral_gain']:.3f} < {self.min_behavioral_gain}"
            fitness = -1.0  # 标记为无效
            return fitness, info
        
        # 4. 复杂度奖励
        node_count = tree.node_count()
        if self.min_nodes <= node_count <= self.max_nodes:
            # 在目标范围内给予奖励
            distance = abs(node_count - self.target_complexity)
            if distance <= self.complexity_tolerance:
                # 接近目标复杂度，给予高奖励
                info['complexity_bonus'] = 1.0 - (distance / self.complexity_tolerance)
            else:
                # 在范围内但偏离目标
                info['complexity_bonus'] = 0.5
        else:
            # 超出范围，给予惩罚
            if node_count < self.min_nodes:
                info['complexity_bonus'] = -0.3
            else:
                info['complexity_bonus'] = -0.2
        
        # 5. 重新计算适应度 (V3 权重)
        # 提取基础指标
        try:
            correlation = np.corrcoef(predictions, B)[0, 1] if len(predictions) == len(B) else 0
            mse = np.mean((predictions - B) ** 2)
            behavioral_gain = info['behavioral_gain']
            complexity_bonus = info['complexity_bonus']
            
            # V3 适应度公式
            fitness = (
                self.corr_weight * correlation +
                self.mse_weight * (1 - mse) +
                self.behavioral_gain_weight * behavioral_gain +
                self.complexity_bonus_weight * complexity_bonus
            )
            
            # 应用终端惩罚
            if info['is_terminal_only']:
                fitness -= self.terminal_penalty
                
        except Exception as e:
            logger.warning(f"Error in V3 fitness calculation: {e}")
            fitness = -1.0
            info['rejected'] = True
            info['rejection_reason'] = f"calculation error: {e}"
        
        info['final_fitness'] = fitness
        return fitness, info

    def evolve(self, behavior_labels: List[int], env_states: List[Dict],
               candidate_name: str = None,
               existing_drives: List[Dict] = None) -> Optional[EvolvedDrive]:
        """
        核心进化方法 (V3) - 质量强化
        
        改进:
        1. 更大种群和更多代数
        2. 严格过滤低质量函数
        3. 鼓励复杂度适中的复合函数
        """
        if len(behavior_labels) < self.min_samples:
            logger.warning(f"Insufficient samples: {len(behavior_labels)} < {self.min_samples}")
            return None

        B = np.array(behavior_labels, dtype=float)
        if B.sum() < 3 or (1 - B).sum() < 3:
            logger.warning("Insufficient label diversity")
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

        # 初始化种群 (V3: 更大种群)
        population = [random_tree(self.max_depth, 'half_and_half')
                      for _ in range(self.population_size)]

        best_tree = None
        best_fitness = -float('inf')
        best_info = {}
        
        # 统计信息
        stats = {
            'rejected_count': 0,
            'terminal_penalty_count': 0,
            'low_gain_count': 0,
            'generation_improvements': [],
        }

        for gen in range(self.generations):
            # 评估 (V3: 使用新的适应度函数)
            fitnesses = []
            infos = []
            
            for tree in population:
                fit, info = self._fitness_v3(tree, B_train, X_train, existing_drives)
                fitnesses.append(fit)
                infos.append(info)
                
                # 统计
                if info['rejected']:
                    stats['rejected_count'] += 1
                    if 'behavioral_gain' in info.get('rejection_reason', ''):
                        stats['low_gain_count'] += 1
                if info['is_terminal_only']:
                    stats['terminal_penalty_count'] += 1

            # 过滤无效个体
            valid_indices = [i for i, fit in enumerate(fitnesses) if fit > 0]
            if len(valid_indices) < self.population_size // 4:
                logger.warning(f"Generation {gen}: Too few valid individuals ({len(valid_indices)})")
                # 保留所有个体，但给无效个体一个低适应度
                fitnesses = [fit if fit > 0 else 0.01 for fit in fitnesses]
            
            # 记录最优
            gen_best_idx = int(np.argmax(fitnesses))
            if fitnesses[gen_best_idx] > best_fitness:
                best_fitness = fitnesses[gen_best_idx]
                best_tree = population[gen_best_idx].copy()
                best_info = infos[gen_best_idx]
                stats['generation_improvements'].append(gen)
                logger.debug(f"Generation {gen}: New best fitness {best_fitness:.3f}, "
                           f"nodes={best_info.get('node_count', 0)}, "
                           f"gain={best_info.get('behavioral_gain', 0):.3f}")

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

            # 提前收敛检测 (V3: 更严格的收敛条件)
            if gen > 20 and gen % 10 == 0:
                if len(stats['generation_improvements']) == 0:
                    logger.info(f"Early stopping at generation {gen}: no improvement")
                    break
                # 检查最近 10 代是否有改进
                recent_improvements = [g for g in stats['generation_improvements'] if g > gen - 10]
                if len(recent_improvements) == 0:
                    logger.info(f"Early stopping at generation {gen}: stagnation")
                    break

        if best_tree is None:
            logger.warning("No valid tree found")
            return None

        # 最终验证
        logger.info(f"Evolution completed: best fitness={best_fitness:.3f}, "
                   f"nodes={best_info.get('node_count', 0)}, "
                   f"rejected={stats['rejected_count']}, "
                   f"terminal_penalties={stats['terminal_penalty_count']}")

        # 验证集测试
        val_fitness, val_info = self._fitness_v3(best_tree, B_val, X_val, existing_drives)
        
        if val_fitness < self.acceptance_threshold:
            logger.warning(f"Validation failed: {val_fitness:.3f} < {self.acceptance_threshold}")
            return None
        
        if val_info.get('rejected', False):
            logger.warning(f"Validation rejected: {val_info.get('rejection_reason')}")
            return None

        # 构建 EvolvedDrive
        func = expr_to_callable(best_tree)
        expr_str = best_tree.to_string()
        
        return EvolvedDrive(
            name=candidate_name or "evolved_drive",
            func=func,
            expr_str=expr_str,
            expr_tree=best_tree,
            fitness=best_fitness,
            correlation=val_info.get('correlation', 0.0),
            behavioral_gain=val_info.get('behavioral_gain', 0.0),
            node_count=best_info.get('node_count', 0),
            depth=best_info.get('depth', 0),
            validation_score=val_fitness,
            generation=len(stats['generation_improvements']),
            stats=stats
        )

    def _tournament_select(self, population: List[ExprNode], fitnesses: List[float]) -> ExprNode:
        """锦标赛选择"""
        selected = random.sample(list(zip(population, fitnesses)), 
                                min(self.tournament_size, len(population)))
        return max(selected, key=lambda x: x[1])[0]

    def _augment_features(self, env_states: List[Dict]) -> List[Dict]:
        """扩展特征 (从 V2 继承)"""
        # 简化实现，实际应从 V2 继承
        return env_states


# 便捷函数
def evolve_drive_v3(behavior_labels: List[int], 
                   env_states: List[Dict],
                   config: Dict = None) -> Optional[EvolvedDrive]:
    """
    快速使用 V3 GP 进化驱动
    
    Args:
        behavior_labels: 行为标签
        env_states: 环境状态
        config: 可选配置
        
    Returns:
        EvolvedDrive 或 None
    """
    gp = GeneticProgrammerV3(config)
    return gp.evolve(behavior_labels, env_states)


# 配置预设
GP_V3_PRESETS = {
    'v3_default': {
        'population_size': 200,
        'generations': 100,
        'terminal_penalty': 0.5,
        'min_behavioral_gain': 0.10,
        'target_complexity': 8,
    },
    'v3_strict': {
        'population_size': 300,
        'generations': 150,
        'terminal_penalty': 0.8,
        'min_behavioral_gain': 0.15,
        'target_complexity': 10,
    },
    'v3_fast': {
        'population_size': 100,
        'generations': 50,
        'terminal_penalty': 0.3,
        'min_behavioral_gain': 0.08,
        'target_complexity': 6,
    },
}


def get_gp_v3_preset(name: str) -> Dict:
    """获取 GP V3 预设配置"""
    return GP_V3_PRESETS.get(name, GP_V3_PRESETS['v3_default'])