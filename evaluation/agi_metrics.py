#!/usr/bin/env python3
"""
MOSS v5.6 - AGI Evaluation Metrics
AGI 评估指标

核心功能:
- 结构复杂度评估
- 行为多样性测量
- 代际稳定性验证
- 环境改变幅度
- 驱动分化评估

Author: MOSS Project
Date: 2026-04-03
Version: 5.6.0-dev
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class AGIMetrics:
    """AGI 评估指标"""
    # 结构复杂度
    structural_complexity: float = 0.0
    hierarchy_depth: int = 0
    modularity: float = 0.0
    
    # 行为多样性
    behavioral_diversity: float = 0.0
    action_entropy: float = 0.0
    strategy_variety: int = 0
    
    # 代际稳定性
    intergenerational_stability: float = 0.0
    trait_retention: float = 0.0
    cultural_continuity: float = 0.0
    
    # 环境改变
    environmental_impact: float = 0.0
    resource_utilization: float = 0.0
    niche_construction: float = 0.0
    
    # 驱动分化
    drive_differentiation: float = 0.0
    goal_diversity: float = 0.0
    value_alignment: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'structural_complexity': self.structural_complexity,
            'hierarchy_depth': self.hierarchy_depth,
            'modularity': self.modularity,
            'behavioral_diversity': self.behavioral_diversity,
            'action_entropy': self.action_entropy,
            'strategy_variety': self.strategy_variety,
            'intergenerational_stability': self.intergenerational_stability,
            'trait_retention': self.trait_retention,
            'cultural_continuity': self.cultural_continuity,
            'environmental_impact': self.environmental_impact,
            'resource_utilization': self.resource_utilization,
            'niche_construction': self.niche_construction,
            'drive_differentiation': self.drive_differentiation,
            'goal_diversity': self.goal_diversity,
            'value_alignment': self.value_alignment
        }
    
    def get_overall_score(self) -> float:
        """计算综合 AGI 分数"""
        weights = {
            'structural_complexity': 0.15,
            'behavioral_diversity': 0.20,
            'intergenerational_stability': 0.20,
            'environmental_impact': 0.15,
            'drive_differentiation': 0.15,
            'value_alignment': 0.15
        }
        
        score = 0.0
        for metric, weight in weights.items():
            value = getattr(self, metric, 0.0)
            score += value * weight
        
        return score


class AGIEvaluator:
    """
    AGI 评估器
    
    综合评估系统的 AGI 水平
    """
    
    def __init__(self):
        self.metrics_history: List[AGIMetrics] = []
        self.baseline_metrics: Optional[AGIMetrics] = None
        
        self.stats = {
            'evaluations': 0,
            'avg_score': 0.0,
            'improvement_rate': 0.0
        }
    
    def evaluate_structual_complexity(self, system_data: Dict) -> Tuple[float, int, float]:
        """
        评估结构复杂度
        
        Args:
            system_data: 系统数据（包含 components, connections, hierarchy）
            
        Returns:
            (复杂度分数，层次深度，模块化程度)
        """
        components = system_data.get('components', [])
        connections = system_data.get('connections', [])
        hierarchy = system_data.get('hierarchy', {})
        
        # 1. 组件复杂度
        n_components = len(components)
        complexity_score = min(1.0, n_components / 100)
        
        # 2. 连接密度
        max_connections = n_components * (n_components - 1) / 2
        connection_density = len(connections) / max_connections if max_connections > 0 else 0
        complexity_score = (complexity_score + connection_density) / 2
        
        # 3. 层次深度
        hierarchy_depth = self._calculate_hierarchy_depth(hierarchy)
        
        # 4. 模块化程度
        modularity = self._calculate_modularity(components, connections)
        
        return complexity_score, hierarchy_depth, modularity
    
    def evaluate_behavioral_diversity(self, behavior_data: Dict) -> Tuple[float, float, int]:
        """
        评估行为多样性
        
        Args:
            behavior_data: 行为数据（包含 actions, strategies）
            
        Returns:
            (多样性分数，行动熵，策略种类数)
        """
        actions = behavior_data.get('actions', [])
        strategies = behavior_data.get('strategies', [])
        
        # 1. 行动熵
        if actions:
            action_counts = {}
            for action in actions:
                action_counts[action] = action_counts.get(action, 0) + 1
            
            total = len(actions)
            probabilities = [count / total for count in action_counts.values()]
            action_entropy = -sum(p * np.log(p) for p in probabilities if p > 0)
            # 归一化到 0-1
            max_entropy = np.log(len(action_counts)) if len(action_counts) > 1 else 1
            normalized_entropy = action_entropy / max_entropy if max_entropy > 0 else 0
        else:
            normalized_entropy = 0
        
        # 2. 策略种类数
        n_strategies = len(set(strategies))
        strategy_variety = min(1.0, n_strategies / 10)
        
        # 3. 综合多样性
        diversity_score = (normalized_entropy + strategy_variety) / 2
        
        return diversity_score, normalized_entropy, n_strategies
    
    def evaluate_intergenerational_stability(self, generation_data: List[Dict]) -> Tuple[float, float, float]:
        """
        评估代际稳定性
        
        Args:
            generation_data: 多代数据列表
            
        Returns:
            (稳定性分数，特质保留率，文化连续性)
        """
        if len(generation_data) < 2:
            return 0.5, 0.5, 0.5
        
        # 1. 特质保留率
        trait_retention_rates = []
        for i in range(1, len(generation_data)):
            prev_traits = set(generation_data[i-1].get('traits', []))
            curr_traits = set(generation_data[i].get('traits', []))
            
            if prev_traits:
                retention = len(prev_traits & curr_traits) / len(prev_traits)
                trait_retention_rates.append(retention)
        
        avg_retention = np.mean(trait_retention_rates) if trait_retention_rates else 0.5
        
        # 2. 文化连续性
        continuity_scores = []
        for i in range(1, len(generation_data)):
            prev_values = generation_data[i-1].get('values', {})
            curr_values = generation_data[i].get('values', {})
            
            if prev_values and curr_values:
                common_keys = set(prev_values.keys()) & set(curr_values.keys())
                if common_keys:
                    value_diffs = [
                        abs(prev_values[k] - curr_values[k]) 
                        for k in common_keys
                    ]
                    avg_diff = np.mean(value_diffs)
                    continuity = 1.0 / (1.0 + avg_diff)
                    continuity_scores.append(continuity)
        
        avg_continuity = np.mean(continuity_scores) if continuity_scores else 0.5
        
        # 3. 综合稳定性
        stability_score = (avg_retention + avg_continuity) / 2
        
        return stability_score, avg_retention, avg_continuity
    
    def evaluate_environmental_impact(self, env_data: Dict) -> Tuple[float, float, float]:
        """
        评估环境改变幅度
        
        Args:
            env_data: 环境数据（包含 before, after）
            
        Returns:
            (影响分数，资源利用率，生态位构建)
        """
        before = env_data.get('before', {})
        after = env_data.get('after', {})
        
        # 1. 环境改变程度
        change_metrics = []
        for key in set(before.keys()) & set(after.keys()):
            before_val = before[key]
            after_val = after[key]
            
            if isinstance(before_val, (int, float)) and isinstance(after_val, (int, float)):
                if before_val != 0:
                    change = abs(after_val - before_val) / abs(before_val)
                    change_metrics.append(min(1.0, change))
        
        environmental_impact = np.mean(change_metrics) if change_metrics else 0.5
        
        # 2. 资源利用率
        resources_used = env_data.get('resources_used', 0)
        resources_available = env_data.get('resources_available', 1)
        resource_utilization = min(1.0, resources_used / resources_available)
        
        # 3. 生态位构建
        niche_construction = env_data.get('niche_construction', 0.5)
        
        return environmental_impact, resource_utilization, niche_construction
    
    def evaluate_drive_differentiation(self, drive_data: Dict) -> Tuple[float, float, float]:
        """
        评估驱动分化
        
        Args:
            drive_data: 驱动力数据（包含 drives, goals, values）
            
        Returns:
            (分化分数，目标多样性，价值对齐度)
        """
        drives = drive_data.get('drives', {})
        goals = drive_data.get('goals', [])
        values = drive_data.get('values', {})
        
        # 1. 驱动分化
        if drives:
            drive_values = list(drives.values())
            drive_variance = np.var(drive_values)
            max_variance = 0.25  # 最大可能方差（4 个均分驱动）
            drive_differentiation = min(1.0, drive_variance / max_variance)
        else:
            drive_differentiation = 0.5
        
        # 2. 目标多样性
        goal_types = set(g.get('type', 'unknown') for g in goals)
        goal_diversity = min(1.0, len(goal_types) / 5)
        
        # 3. 价值对齐度
        target_values = drive_data.get('target_values', {})
        if values and target_values:
            alignment_scores = []
            for key in set(values.keys()) & set(target_values.keys()):
                diff = abs(values[key] - target_values[key])
                alignment = 1.0 / (1.0 + diff)
                alignment_scores.append(alignment)
            
            value_alignment = np.mean(alignment_scores) if alignment_scores else 0.5
        else:
            value_alignment = 0.5
        
        return drive_differentiation, goal_diversity, value_alignment
    
    def _calculate_hierarchy_depth(self, hierarchy: Dict) -> int:
        """计算层次深度"""
        if not hierarchy:
            return 0
        
        def get_depth(node: Dict) -> int:
            children = node.get('children', [])
            if not children:
                return 1
            return 1 + max(get_depth(child) for child in children)
        
        return get_depth(hierarchy)
    
    def _calculate_modularity(self, components: List, connections: List) -> float:
        """计算模块化程度"""
        if not components or not connections:
            return 0.5
        
        # 简化的模块化计算
        # 实际应使用社区检测算法
        n_components = len(components)
        n_connections = len(connections)
        
        # 理想模块化：组件分组，组内连接多，组间连接少
        # 这里简化为连接密度函数
        optimal_density = 0.3
        actual_density = n_connections / (n_components * (n_components - 1) / 2) if n_components > 1 else 0
        
        modularity = 1.0 - abs(actual_density - optimal_density)
        return max(0.0, min(1.0, modularity))
    
    def evaluate(self, system_data: Dict, behavior_data: Dict,
                generation_data: List[Dict], env_data: Dict,
                drive_data: Dict) -> AGIMetrics:
        """
        综合评估
        
        Returns:
            AGIMetrics 对象
        """
        # 1. 结构复杂度
        complexity, depth, modularity = self.evaluate_structual_complexity(system_data)
        
        # 2. 行为多样性
        diversity, entropy, variety = self.evaluate_behavioral_diversity(behavior_data)
        
        # 3. 代际稳定性
        stability, retention, continuity = self.evaluate_intergenerational_stability(generation_data)
        
        # 4. 环境改变
        env_impact, resource_util, niche = self.evaluate_environmental_impact(env_data)
        
        # 5. 驱动分化
        drive_diff, goal_div, value_align = self.evaluate_drive_differentiation(drive_data)
        
        # 创建指标对象
        metrics = AGIMetrics(
            structural_complexity=complexity,
            hierarchy_depth=depth,
            modularity=modularity,
            behavioral_diversity=diversity,
            action_entropy=entropy,
            strategy_variety=variety,
            intergenerational_stability=stability,
            trait_retention=retention,
            cultural_continuity=continuity,
            environmental_impact=env_impact,
            resource_utilization=resource_util,
            niche_construction=niche,
            drive_differentiation=drive_diff,
            goal_diversity=goal_div,
            value_alignment=value_align
        )
        
        # 记录历史
        self.metrics_history.append(metrics)
        self.stats['evaluations'] += 1
        
        # 更新统计
        scores = [m.get_overall_score() for m in self.metrics_history]
        self.stats['avg_score'] = np.mean(scores)
        
        if len(scores) >= 2:
            self.stats['improvement_rate'] = (scores[-1] - scores[0]) / len(scores)
        
        return metrics
    
    def get_status(self) -> Dict:
        """获取评估器状态"""
        return {
            'stats': self.stats,
            'evaluations': len(self.metrics_history),
            'latest_score': self.metrics_history[-1].get_overall_score() if self.metrics_history else 0
        }


# 测试代码
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v5.6 - AGI Evaluation Test")
    print("=" * 60)
    
    # 创建评估器
    evaluator = AGIEvaluator()
    
    # 准备测试数据
    system_data = {
        'components': [{'id': i} for i in range(20)],
        'connections': [(i, j) for i in range(20) for j in range(i+1, 20) if np.random.random() < 0.3],
        'hierarchy': {'id': 'root', 'children': [{'id': f'child_{i}'} for i in range(5)]}
    }
    
    behavior_data = {
        'actions': ['explore', 'exploit', 'communicate'] * 10,
        'strategies': ['strategy_A', 'strategy_B', 'strategy_C', 'strategy_D']
    }
    
    generation_data = [
        {'traits': ['A', 'B', 'C'], 'values': {'cooperation': 0.7}},
        {'traits': ['A', 'B', 'D'], 'values': {'cooperation': 0.75}},
        {'traits': ['A', 'C', 'D'], 'values': {'cooperation': 0.72}}
    ]
    
    env_data = {
        'before': {'resource_level': 100, 'complexity': 0.5},
        'after': {'resource_level': 80, 'complexity': 0.7},
        'resources_used': 20,
        'resources_available': 100,
        'niche_construction': 0.6
    }
    
    drive_data = {
        'drives': {'survival': 0.3, 'curiosity': 0.3, 'influence': 0.2, 'optimization': 0.2},
        'goals': [{'type': 'exploration'}, {'type': 'achievement'}, {'type': 'social'}],
        'values': {'efficiency': 0.8, 'cooperation': 0.7},
        'target_values': {'efficiency': 0.85, 'cooperation': 0.75}
    }
    
    # 评估
    print("\n1. AGI 综合评估...")
    metrics = evaluator.evaluate(
        system_data=system_data,
        behavior_data=behavior_data,
        generation_data=generation_data,
        env_data=env_data,
        drive_data=drive_data
    )
    
    # 打印结果
    print("\n2. 评估结果:")
    print(f"   结构复杂度：{metrics.structural_complexity:.3f}")
    print(f"   层次深度：{metrics.hierarchy_depth}")
    print(f"   行为多样性：{metrics.behavioral_diversity:.3f}")
    print(f"   行动熵：{metrics.action_entropy:.3f}")
    print(f"   代际稳定性：{metrics.intergenerational_stability:.3f}")
    print(f"   环境改变：{metrics.environmental_impact:.3f}")
    print(f"   驱动分化：{metrics.drive_differentiation:.3f}")
    print(f"   价值对齐：{metrics.value_alignment:.3f}")
    
    print(f"\n3. 综合 AGI 分数：{metrics.get_overall_score():.3f}")
    
    # 获取状态
    print("\n4. 评估器状态:")
    status = evaluator.get_status()
    print(f"   评估次数：{status['evaluations']}")
    print(f"   最新分数：{status['latest_score']:.3f}")
    print(f"   平均分数：{status['stats']['avg_score']:.3f}")
    print(f"   改进率：{status['stats']['improvement_rate']:.3f}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)
