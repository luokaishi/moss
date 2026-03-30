#!/usr/bin/env python3
"""
MVES v5 - 演化指标系统（资源优化版）

核心指标:
1. 行为多样性（熵）
2. 策略复杂度
3. 新能力检测
4. 长期性能提升

资源限制:
- 内存：<10 MB
- 磁盘：<1 MB/代
"""

import math
from typing import Dict, List, Set
from collections import Counter


class EvolutionMetrics:
    """
    演化指标计算器
    """
    
    @staticmethod
    def behavior_diversity(population) -> float:
        """
        行为多样性（策略熵）
        
        计算：H = -Σ p(strategy_i) * log(p(strategy_i))
        
        Args:
            population: agent 种群
        
        Returns:
            多样性分数 (0-1，1=最高多样性)
        """
        if not population:
            return 0.0
        
        # 获取所有 agent 的策略
        strategies = []
        for agent in population:
            if agent.state:  # 只统计存活的
                strategy_str = str(agent.genome.get("strategies", {}))
                strategies.append(strategy_str)
        
        if not strategies:
            return 0.0
        
        # 计算熵
        total = len(strategies)
        counts = Counter(strategies)
        
        entropy = 0.0
        for count in counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log(p)
        
        # 归一化到 [0,1]
        # 最大熵 = log(unique_strategies)
        max_entropy = math.log(len(counts)) if len(counts) > 1 else 1.0
        
        return entropy / max_entropy if max_entropy > 0 else 0.0
    
    @staticmethod
    def strategy_complexity(agent) -> float:
        """
        策略复杂度
        
        计算：模块数 × 策略深度
        
        Args:
            agent: 单个 agent
        
        Returns:
            复杂度分数
        """
        modules = len(agent.genome.get("modules", []))
        strategies = agent.genome.get("strategies", {})
        strategy_depth = sum(len(str(v)) for v in strategies.values())
        
        return modules * max(1, strategy_depth / 10)
    
    @staticmethod
    def avg_complexity(population) -> float:
        """
        平均策略复杂度
        
        Args:
            population: agent 种群
        
        Returns:
            平均复杂度
        """
        if not population:
            return 0.0
        
        survivors = [a for a in population if a.state]
        if not survivors:
            return 0.0
        
        complexities = [EvolutionMetrics.strategy_complexity(a) for a in survivors]
        return sum(complexities) / len(complexities)
    
    @staticmethod
    def novel_capabilities(population, baseline: Set[str]) -> Set[str]:
        """
        未预设能力检测
        
        Args:
            population: agent 种群
            baseline: 预设能力集合
        
        Returns:
            新能力集合
        """
        observed = set()
        for agent in population:
            if agent.state:
                observed.update(agent.get_capabilities())
        
        return observed - baseline
    
    @staticmethod
    def capability_expansion(population, baseline: Set[str]) -> float:
        """
        能力扩展度
        
        Args:
            population: agent 种群
            baseline: 预设能力集合
        
        Returns:
            扩展度 (新能力数 / 基础能力数)
        """
        novel = EvolutionMetrics.novel_capabilities(population, baseline)
        return len(novel) / max(1, len(baseline))
    
    @staticmethod
    def long_term_improvement(history: List[Dict]) -> float:
        """
        长期性能提升
        
        计算：(final_perf - initial_perf) / initial_perf
        
        Args:
            history: 历史数据列表
        
        Returns:
            提升率
        """
        if len(history) < 2:
            return 0.0
        
        initial_perf = history[0].get('avg_fitness', 0)
        final_perf = history[-1].get('avg_fitness', 0)
        
        if initial_perf == 0:
            return 0.0
        
        return (final_perf - initial_perf) / initial_perf
    
    @staticmethod
    def population_health(population) -> Dict:
        """
        种群健康度
        
        Args:
            population: agent 种群
        
        Returns:
            健康度字典
        """
        survivors = [a for a in population if a.state]
        
        if not survivors:
            return {
                'health_score': 0.0,
                'avg_energy': 0,
                'avg_fitness': 0,
                'population_size': 0
            }
        
        avg_energy = sum(a.state.get('energy', 0) for a in survivors) / len(survivors)
        avg_fitness = sum(a.get_fitness() for a in survivors) / len(survivors)
        
        # 健康度 = 能量分数 × 0.5 + 适应度分数 × 0.5
        energy_score = min(1.0, avg_energy / 100)
        fitness_score = min(1.0, avg_fitness)
        
        health_score = energy_score * 0.5 + fitness_score * 0.5
        
        return {
            'health_score': health_score,
            'avg_energy': avg_energy,
            'avg_fitness': avg_fitness,
            'population_size': len(survivors)
        }
    
    @staticmethod
    def evolution_trajectory(history: List[Dict]) -> Dict:
        """
        演化轨迹分析
        
        Args:
            history: 历史数据列表
        
        Returns:
            轨迹分析字典
        """
        if len(history) < 2:
            return {
                'trend': 'stable',
                'volatility': 0.0,
                'improvement_rate': 0.0
            }
        
        # 提取适应度序列
        fitnesses = [h.get('avg_fitness', 0) for h in history]
        
        # 计算趋势
        if fitnesses[-1] > fitnesses[0] * 1.2:
            trend = 'improving'
        elif fitnesses[-1] < fitnesses[0] * 0.8:
            trend = 'declining'
        else:
            trend = 'stable'
        
        # 计算波动性
        mean_fit = sum(fitnesses) / len(fitnesses)
        variance = sum((f - mean_fit) ** 2 for f in fitnesses) / len(fitnesses)
        volatility = math.sqrt(variance) / mean_fit if mean_fit > 0 else 0
        
        # 计算改进率
        improvement_rate = EvolutionMetrics.long_term_improvement(history)
        
        return {
            'trend': trend,
            'volatility': volatility,
            'improvement_rate': improvement_rate
        }
    
    @staticmethod
    def generate_report(population, history: List[Dict], baseline: Set[str]) -> Dict:
        """
        生成完整报告
        
        Args:
            population: agent 种群
            history: 历史数据列表
            baseline: 预设能力集合
        
        Returns:
            完整报告字典
        """
        return {
            'population': EvolutionMetrics.population_health(population),
            'diversity': EvolutionMetrics.behavior_diversity(population),
            'complexity': EvolutionMetrics.avg_complexity(population),
            'novel_capabilities': len(EvolutionMetrics.novel_capabilities(population, baseline)),
            'capability_expansion': EvolutionMetrics.capability_expansion(population, baseline),
            'trajectory': EvolutionMetrics.evolution_trajectory(history),
            'generations': len(history)
        }


if __name__ == "__main__":
    # 快速测试
    print("Testing EvolutionMetrics...")
    
    # 模拟数据
    history = [
        {'avg_fitness': 0.5},
        {'avg_fitness': 0.6},
        {'avg_fitness': 0.8},
        {'avg_fitness': 1.0}
    ]
    
    print(f"Long term improvement: {EvolutionMetrics.long_term_improvement(history):.2%}")
    print(f"Trajectory: {EvolutionMetrics.evolution_trajectory(history)}")
    print("Metrics module ready!")
