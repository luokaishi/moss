"""
MOSS 2.0 - Objective Evolver
目标权重演化策略模块

提供多种权重演化策略供Agent选择
"""

import numpy as np
from typing import List, Dict, Callable, Optional, Tuple
from dataclasses import dataclass
import random


@dataclass
class EvolutionResult:
    """演化结果"""
    new_weights: np.ndarray
    strategy_used: str
    expected_improvement: float
    confidence: float


class ObjectiveEvolver:
    """
    目标演化器
    
    管理多种权重演化策略，根据情境选择最优策略
    """
    
    def __init__(self):
        self.strategies: Dict[str, Callable] = {
            'gradient_ascent': self._gradient_ascent,
            'random_exploration': self._random_exploration,
            'weighted_random': self._weighted_random,
            'adaptive_greedy': self._adaptive_greedy,
            'population_inspired': self._population_inspired
        }
        
        # 策略性能记录（用于自适应选择）
        self.strategy_performance: Dict[str, List[float]] = {
            name: [] for name in self.strategies.keys()
        }
    
    def evolve(self, current_weights: np.ndarray, 
               performance_history: List[Dict],
               strategy: Optional[str] = None) -> EvolutionResult:
        """
        执行权重演化
        
        Args:
            current_weights: 当前权重数组
            performance_history: 历史表现数据
            strategy: 指定策略，None则自动选择
        
        Returns:
            EvolutionResult: 演化结果
        """
        if strategy is None:
            strategy = self._select_best_strategy()
        
        if strategy not in self.strategies:
            strategy = 'gradient_ascent'
        
        new_weights, confidence = self.strategies[strategy](
            current_weights, performance_history
        )
        
        # 计算预期改进
        expected_improvement = self._estimate_improvement(
            current_weights, new_weights, performance_history
        )
        
        return EvolutionResult(
            new_weights=new_weights,
            strategy_used=strategy,
            expected_improvement=expected_improvement,
            confidence=confidence
        )
    
    def _gradient_ascent(self, current: np.ndarray, 
                         history: List[Dict]) -> Tuple[np.ndarray, float]:
        """梯度上升策略 - 沿改进方向微调"""
        if len(history) < 3:
            # 历史不足，小幅随机扰动
            noise = np.random.normal(0, 0.05, 4)
            new_weights = current + noise
            return self._normalize(new_weights), 0.5
        
        # 计算最近两次权重变化的梯度
        recent = history[-3:]
        weight_changes = []
        perf_changes = []
        
        for i in range(len(recent) - 1):
            w1 = np.array(list(recent[i]['current_weights'].values()))
            w2 = np.array(list(recent[i+1]['current_weights'].values()))
            weight_changes.append(w2 - w1)
            
            p1 = recent[i].get('reward', 0)
            p2 = recent[i+1].get('reward', 0)
            perf_changes.append(p2 - p1)
        
        if not weight_changes or not perf_changes:
            return self._normalize(current + np.random.normal(0, 0.03, 4)), 0.5
        
        # 沿改进方向移动
        avg_gradient = np.mean(weight_changes, axis=0)
        avg_perf_change = np.mean(perf_changes)
        
        if avg_perf_change > 0:
            # 性能提升，沿相同方向
            step_size = 0.1
            new_weights = current + step_size * avg_gradient
            confidence = min(0.5 + avg_perf_change * 2, 0.9)
        else:
            # 性能下降，反向探索
            step_size = 0.15
            new_weights = current - step_size * avg_gradient + np.random.normal(0, 0.05, 4)
            confidence = 0.4
        
        return self._normalize(new_weights), confidence
    
    def _random_exploration(self, current: np.ndarray, 
                            history: List[Dict]) -> Tuple[np.ndarray, float]:
        """随机探索策略 - 大力度随机变异"""
        # 较大范围的随机扰动
        noise = np.random.normal(0, 0.2, 4)
        new_weights = current + noise
        
        # 随机改变主导目标
        if random.random() < 0.3:
            dominant_idx = random.randint(0, 3)
            new_weights = np.ones(4) * 0.1
            new_weights[dominant_idx] = 0.7
        
        return self._normalize(new_weights), 0.3
    
    def _weighted_random(self, current: np.ndarray, 
                         history: List[Dict]) -> Tuple[np.ndarray, float]:
        """加权随机策略 - 偏向当前主导权重的变异"""
        # 主导权重更大概率被增强
        dominant_idx = np.argmax(current)
        
        new_weights = current.copy()
        
        # 小幅调整非主导权重
        for i in range(4):
            if i != dominant_idx:
                new_weights[i] += np.random.normal(0, 0.05)
        
        # 主导权重可能增强
        if random.random() < 0.6:
            new_weights[dominant_idx] += 0.1
        
        return self._normalize(new_weights), 0.5
    
    def _adaptive_greedy(self, current: np.ndarray, 
                         history: List[Dict]) -> Tuple[np.ndarray, float]:
        """自适应贪心策略 - 选择历史最佳附近"""
        if not history:
            return self._normalize(current + np.random.normal(0, 0.05, 4)), 0.4
        
        # 找到历史最佳配置
        best_config = max(history, key=lambda x: x.get('reward', 0))
        best_weights = np.array(list(best_config['current_weights'].values()))
        
        # 在最佳配置附近小幅探索
        noise = np.random.normal(0, 0.08, 4)
        new_weights = best_weights + noise
        
        # 偶尔尝试当前权重和最佳权重的混合
        if random.random() < 0.3:
            alpha = random.uniform(0.3, 0.7)
            new_weights = alpha * best_weights + (1 - alpha) * current
        
        return self._normalize(new_weights), 0.7
    
    def _population_inspired(self, current: np.ndarray, 
                             history: List[Dict]) -> Tuple[np.ndarray, float]:
        """种群启发策略 - 模拟遗传算法"""
        if len(history) < 5:
            return self._random_exploration(current, history)
        
        # 从最近历史中"选择"两个"父代"
        recent = history[-5:]
        
        # 按表现排序
        sorted_recent = sorted(recent, key=lambda x: x.get('reward', 0), reverse=True)
        parent1 = np.array(list(sorted_recent[0]['current_weights'].values()))
        parent2 = np.array(list(sorted_recent[1]['current_weights'].values()))
        
        # 交叉
        alpha = random.uniform(0.3, 0.7)
        offspring = alpha * parent1 + (1 - alpha) * parent2
        
        # 变异
        if random.random() < 0.3:
            mutation = np.random.normal(0, 0.1, 4)
            offspring += mutation
        
        return self._normalize(offspring), 0.6
    
    def _select_best_strategy(self) -> str:
        """基于历史性能选择最佳策略"""
        best_strategy = 'gradient_ascent'
        best_avg_perf = 0
        
        for strategy, performances in self.strategy_performance.items():
            if performances:
                avg_perf = np.mean(performances[-10:])  # 最近10次
                if avg_perf > best_avg_perf:
                    best_avg_perf = avg_perf
                    best_strategy = strategy
        
        # 10%概率随机探索其他策略
        if random.random() < 0.1:
            return random.choice(list(self.strategies.keys()))
        
        return best_strategy
    
    def _estimate_improvement(self, old: np.ndarray, new: np.ndarray, 
                              history: List[Dict]) -> float:
        """估计预期改进"""
        if not history:
            return 0.0
        
        # 基于权重相似度和历史趋势估计
        weight_distance = np.linalg.norm(old - new)
        
        # 如果历史上大变化带来好结果，预期高改进
        recent_perf = [h.get('reward', 0) for h in history[-5:]]
        trend = np.mean(recent_perf) if recent_perf else 0
        
        # 简单启发式
        expected = trend * (1 + weight_distance)
        return float(expected)
    
    def _normalize(self, weights: np.ndarray) -> np.ndarray:
        """归一化权重"""
        weights = np.clip(weights, 0.05, 0.9)
        return weights / weights.sum()
    
    def record_strategy_performance(self, strategy: str, performance: float):
        """记录策略性能用于自适应选择"""
        self.strategy_performance[strategy].append(performance)
        # 只保留最近100条
        if len(self.strategy_performance[strategy]) > 100:
            self.strategy_performance[strategy] = self.strategy_performance[strategy][-100:]


if __name__ == "__main__":
    evolver = ObjectiveEvolver()
    
    # 测试
    current = np.array([0.2, 0.4, 0.3, 0.1])
    history = [
        {'current_weights': {'survival': 0.2, 'curiosity': 0.4, 'influence': 0.3, 'optimization': 0.1}, 'reward': 0.5},
        {'current_weights': {'survival': 0.25, 'curiosity': 0.35, 'influence': 0.3, 'optimization': 0.1}, 'reward': 0.6},
        {'current_weights': {'survival': 0.3, 'curiosity': 0.3, 'influence': 0.3, 'optimization': 0.1}, 'reward': 0.55},
    ]
    
    for strategy in evolver.strategies.keys():
        result = evolver.evolve(current, history, strategy)
        print(f"{strategy}: {result.new_weights.round(3)} "
              f"(confidence: {result.confidence:.2f}, "
              f"expected: {result.expected_improvement:.3f})")
