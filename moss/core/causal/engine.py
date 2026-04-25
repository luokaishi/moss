"""
MOSS v8.0 - Causal Reasoning Engine
因果推理引擎

核心功能:
- 因果发现
- 因果图
- 干预模拟
- 反事实推理

Author: MOSS Project
Date: 2026-04-19
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import json


@dataclass
class CausalRelationship:
    """因果关系"""
    cause: str
    effect: str
    strength: float          # 因果强度 (0-1)
    confidence: float        # 置信度 (0-1)
    mechanism: str = ""      # 因果机制描述
    timestamp: datetime = field(default_factory=datetime.now)
    evidence_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            'cause': self.cause,
            'effect': self.effect,
            'strength': self.strength,
            'confidence': self.confidence,
            'mechanism': self.mechanism,
            'evidence_count': self.evidence_count,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class Intervention:
    """干预"""
    variable: str
    value: float
    description: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'variable': self.variable,
            'value': self.value,
            'description': self.description,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class Counterfactual:
    """反事实"""
    original_state: Dict
    intervention: Intervention
    predicted_outcome: Dict
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'original_state': self.original_state,
            'intervention': self.intervention.to_dict(),
            'predicted_outcome': self.predicted_outcome,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat()
        }


class CausalGraph:
    """
    因果图
    
    表示变量间的因果关系
    """
    
    def __init__(self):
        self.nodes: Set[str] = set()
        self.edges: Dict[str, List[str]] = defaultdict(list)  # cause -> [effects]
        self.edge_weights: Dict[Tuple[str, str], float] = {}
        self.edge_confidence: Dict[Tuple[str, str], float] = {}
        
        # 反向边 (用于查找原因)
        self.reverse_edges: Dict[str, List[str]] = defaultdict(list)
    
    def add_node(self, variable: str):
        """添加节点"""
        self.nodes.add(variable)
    
    def add_edge(self, cause: str, effect: str, 
                weight: float = 1.0, confidence: float = 0.5):
        """添加边"""
        self.add_node(cause)
        self.add_node(effect)
        
        if effect not in self.edges[cause]:
            self.edges[cause].append(effect)
            self.reverse_edges[effect].append(cause)
        
        self.edge_weights[(cause, effect)] = weight
        self.edge_confidence[(cause, effect)] = confidence
    
    def get_parents(self, variable: str) -> List[str]:
        """获取父节点 (直接原因)"""
        return self.reverse_edges[variable]
    
    def get_children(self, variable: str) -> List[str]:
        """获取子节点 (直接结果)"""
        return self.edges[variable]
    
    def get_ancestors(self, variable: str) -> Set[str]:
        """获取祖先节点 (所有原因)"""
        ancestors = set()
        to_visit = [variable]
        visited = set()
        
        while to_visit:
            node = to_visit.pop()
            if node in visited:
                continue
            visited.add(node)
            
            parents = self.get_parents(node)
            for parent in parents:
                ancestors.add(parent)
                to_visit.append(parent)
        
        return ancestors
    
    def get_descendants(self, variable: str) -> Set[str]:
        """获取后代节点 (所有结果)"""
        descendants = set()
        to_visit = [variable]
        visited = set()
        
        while to_visit:
            node = to_visit.pop()
            if node in visited:
                continue
            visited.add(node)
            
            children = self.get_children(node)
            for child in children:
                descendants.add(child)
                to_visit.append(child)
        
        return descendants
    
    def is_cause(self, potential_cause: str, effect: str) -> bool:
        """检查是否为原因"""
        return potential_cause in self.get_ancestors(effect)
    
    def get_causal_path(self, cause: str, effect: str) -> Optional[List[str]]:
        """获取因果路径"""
        # 使用 BFS 找路径
        from collections import deque
        
        if cause == effect:
            return [cause]
        
        queue = deque([(cause, [cause])])
        visited = {cause}
        
        while queue:
            current, path = queue.popleft()
            
            for child in self.get_children(current):
                if child == effect:
                    return path + [child]
                
                if child not in visited:
                    visited.add(child)
                    queue.append((child, path + [child]))
        
        return None
    
    def to_dict(self) -> Dict:
        """导出为字典"""
        return {
            'nodes': list(self.nodes),
            'edges': [
                {
                    'cause': cause,
                    'effect': effect,
                    'weight': self.edge_weights.get((cause, effect), 1.0),
                    'confidence': self.edge_confidence.get((cause, effect), 0.5)
                }
                for cause in self.edges
                for effect in self.edges[cause]
            ]
        }


class CausalReasoningEngine:
    """
    因果推理引擎
    
    实现因果发现、干预模拟和反事实推理
    """
    
    def __init__(self):
        self.causal_graph = CausalGraph()
        self.relationships: List[CausalRelationship] = []
        self.interventions: List[Intervention] = []
        self.counterfactuals: List[Counterfactual] = []
        
        # 观察数据
        self.observations: List[Dict] = []
        
        # 统计
        self.stats = {
            'relationships_discovered': 0,
            'interventions_simulated': 0,
            'counterfactuals_generated': 0,
            'predictions_made': 0
        }
    
    def discover_causal_relationships(self, data: List[Dict],
                                    variables: List[str]) -> List[CausalRelationship]:
        """
        发现因果关系
        
        Args:
            data: 观察数据
            variables: 变量列表
            
        Returns:
            发现的因果关系
        """
        discovered = []
        
        # 简化实现：基于相关性推断因果
        # 实际应该使用更复杂的因果发现算法 (PC, GES, etc.)
        
        for i, var1 in enumerate(variables):
            for var2 in variables[i+1:]:
                # 计算相关性
                values1 = [d.get(var1, 0) for d in data if var1 in d and var2 in d]
                values2 = [d.get(var2, 0) for d in data if var1 in d and var2 in d]
                
                if len(values1) < 3:
                    continue
                
                correlation = np.corrcoef(values1, values2)[0, 1]
                
                if abs(correlation) > 0.5:  # 阈值
                    # 推断因果方向 (简化：假设时间顺序)
                    # 实际应该使用更复杂的方法
                    
                    strength = abs(correlation)
                    confidence = min(strength * 1.2, 0.9)
                    
                    # 假设 var1 -> var2 (简化)
                    relationship = CausalRelationship(
                        cause=var1,
                        effect=var2,
                        strength=strength,
                        confidence=confidence,
                        mechanism=f"Correlation-based inference: {correlation:.3f}",
                        evidence_count=len(values1)
                    )
                    
                    discovered.append(relationship)
                    self.relationships.append(relationship)
                    
                    # 更新因果图
                    self.causal_graph.add_edge(var1, var2, strength, confidence)
        
        self.stats['relationships_discovered'] += len(discovered)
        return discovered
    
    def simulate_intervention(self, intervention: Intervention,
                             current_state: Dict) -> Dict:
        """
        模拟干预
        
        Args:
            intervention: 干预
            current_state: 当前状态
            
        Returns:
            干预后的预测状态
        """
        self.interventions.append(intervention)
        self.stats['interventions_simulated'] += 1
        
        # 创建新状态 (深拷贝)
        new_state = current_state.copy()
        
        # 应用干预
        new_state[intervention.variable] = intervention.value
        
        # 传播因果影响
        affected = self.causal_graph.get_descendants(intervention.variable)
        
        for variable in affected:
            parents = self.causal_graph.get_parents(variable)
            if not parents:
                continue
            
            # 基于父节点计算新值 (简化线性模型)
            new_value = 0
            total_weight = 0
            
            for parent in parents:
                if parent == intervention.variable:
                    parent_value = intervention.value
                else:
                    parent_value = new_state.get(parent, 0)
                
                weight = self.causal_graph.edge_weights.get((parent, variable), 0.5)
                new_value += parent_value * weight
                total_weight += weight
            
            if total_weight > 0:
                new_state[variable] = new_value / total_weight
        
        return new_state
    
    def generate_counterfactual(self, original_state: Dict,
                             intervention: Intervention) -> Counterfactual:
        """
        生成反事实
        
        Args:
            original_state: 原始状态
            intervention: 干预
            
        Returns:
            反事实
        """
        # 预测干预后的结果
        predicted_outcome = self.simulate_intervention(intervention, original_state)
        
        # 计算置信度
        confidence = self._calculate_counterfactual_confidence(
            original_state, intervention, predicted_outcome
        )
        
        counterfactual = Counterfactual(
            original_state=original_state.copy(),
            intervention=intervention,
            predicted_outcome=predicted_outcome,
            confidence=confidence
        )
        
        self.counterfactuals.append(counterfactual)
        self.stats['counterfactuals_generated'] += 1
        
        return counterfactual
    
    def _calculate_counterfactual_confidence(self, original_state: Dict,
                                          intervention: Intervention,
                                          predicted_outcome: Dict) -> float:
        """计算反事实置信度"""
        # 基于因果图路径的置信度
        variable = intervention.variable
        affected = self.causal_graph.get_descendants(variable)
        
        if not affected:
            return 0.9  # 高置信度 (无影响)
        
        # 基于边置信度计算
        total_confidence = 1.0
        for effect in affected:
            path = self.causal_graph.get_causal_path(variable, effect)
            if path and len(path) > 1:
                path_confidence = 1.0
                for i in range(len(path) - 1):
                    edge_conf = self.causal_graph.edge_confidence.get(
                        (path[i], path[i+1]), 0.5
                    )
                    path_confidence *= edge_conf
                total_confidence *= path_confidence
        
        return max(total_confidence, 0.3)  # 最低 0.3
    
    def predict_outcome(self, current_state: Dict, 
                       actions: List[str]) -> Dict[str, float]:
        """
        预测结果
        
        Args:
            current_state: 当前状态
            actions: 动作列表
            
        Returns:
            预测结果
        """
        predictions = {}
        
        for action in actions:
            # 模拟动作作为干预
            intervention = Intervention(
                variable=action,
                value=1.0,  # 执行动作
                description=f"Action: {action}"
            )
            
            predicted_state = self.simulate_intervention(intervention, current_state)
            
            # 提取关键预测
            predictions[action] = predicted_state.get('performance', 0.5)
        
        self.stats['predictions_made'] += len(actions)
        return predictions
    
    def explain_causation(self, effect: str) -> List[Dict]:
        """
        解释因果
        
        Args:
            effect: 结果变量
            
        Returns:
            因果解释
        """
        explanations = []
        
        # 获取直接原因
        direct_causes = self.causal_graph.get_parents(effect)
        
        for cause in direct_causes:
            weight = self.causal_graph.edge_weights.get((cause, effect), 0)
            confidence = self.causal_graph.edge_confidence.get((cause, effect), 0)
            
            explanations.append({
                'cause': cause,
                'effect': effect,
                'relationship': 'direct',
                'strength': weight,
                'confidence': confidence,
                'explanation': f"{cause} directly causes {effect} with strength {weight:.3f}"
            })
        
        # 获取间接原因 (祖先)
        ancestors = self.causal_graph.get_ancestors(effect)
        for ancestor in ancestors:
            if ancestor in direct_causes:
                continue
            
            path = self.causal_graph.get_causal_path(ancestor, effect)
            if path:
                explanations.append({
                    'cause': ancestor,
                    'effect': effect,
                    'relationship': 'indirect',
                    'path': path,
                    'explanation': f"{ancestor} indirectly causes {effect} via {' -> '.join(path)}"
                })
        
        return explanations
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            **self.stats,
            'total_relationships': len(self.relationships),
            'total_interventions': len(self.interventions),
            'total_counterfactuals': len(self.counterfactuals),
            'graph_nodes': len(self.causal_graph.nodes),
            'graph_edges': sum(len(effects) for effects in self.causal_graph.edges.values())
        }


# 测试
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v8.0 - Causal Reasoning Engine Test")
    print("=" * 60)
    
    # 创建因果推理引擎
    engine = CausalReasoningEngine()
    
    # 模拟观察数据
    print("\n1. Discovering causal relationships...")
    np.random.seed(42)
    
    # 生成模拟数据: A -> B -> C
    data = []
    for i in range(100):
        a = np.random.randn()
        b = a * 0.8 + np.random.randn() * 0.2  # B 受 A 影响
        c = b * 0.7 + np.random.randn() * 0.3  # C 受 B 影响
        data.append({'A': a, 'B': b, 'C': c})
    
    relationships = engine.discover_causal_relationships(data, ['A', 'B', 'C'])
    print(f"   Discovered {len(relationships)} relationships:")
    for rel in relationships:
        print(f"     - {rel.cause} -> {rel.effect}: {rel.strength:.3f} (confidence: {rel.confidence:.3f})")
    
    # 因果图
    print("\n2. Causal graph:")
    print(f"   Nodes: {len(engine.causal_graph.nodes)}")
    print(f"   Edges: {sum(len(effects) for effects in engine.causal_graph.edges.values())}")
    
    # 模拟干预
    print("\n3. Simulating intervention...")
    current_state = {'A': 0.5, 'B': 0.4, 'C': 0.3}
    intervention = Intervention(variable='A', value=1.0, description='Set A to 1.0')
    
    new_state = engine.simulate_intervention(intervention, current_state)
    print(f"   Original state: {current_state}")
    print(f"   Intervention: {intervention.variable} = {intervention.value}")
    print(f"   Predicted state: {new_state}")
    
    # 反事实
    print("\n4. Generating counterfactual...")
    counterfactual = engine.generate_counterfactual(current_state, intervention)
    print(f"   Confidence: {counterfactual.confidence:.3f}")
    print(f"   Predicted outcome: {counterfactual.predicted_outcome}")
    
    # 因果解释
    print("\n5. Explaining causation for C:")
    explanations = engine.explain_causation('C')
    for exp in explanations:
        print(f"   - {exp['explanation']}")
    
    # 统计
    print("\n6. Engine stats:")
    stats = engine.get_stats()
    print(f"   Relationships discovered: {stats['relationships_discovered']}")
    print(f"   Interventions simulated: {stats['interventions_simulated']}")
    print(f"   Counterfactuals generated: {stats['counterfactuals_generated']}")
    print(f"   Graph nodes: {stats['graph_nodes']}")
    print(f"   Graph edges: {stats['graph_edges']}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)