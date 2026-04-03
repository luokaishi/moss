#!/usr/bin/env python3
"""
MOSS v5.6 - Social Learning Module
社会学习模块

核心功能:
- 观察学习
- 模仿算法
- 知识传递效率
- 社会网络影响

Author: MOSS Project
Date: 2026-04-03
Version: 5.6.0-dev
"""

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class SocialConnection:
    """社会连接"""
    from_agent: str
    to_agent: str
    strength: float = 0.5
    trust: float = 0.5
    
    def to_dict(self) -> Dict:
        return {
            'from': self.from_agent,
            'to': self.to_agent,
            'strength': self.strength,
            'trust': self.trust
        }


class SocialNetwork:
    """
    社会网络
    
    管理 Agent 间的社会连接
    """
    
    def __init__(self, n_agents: int = 20):
        self.n_agents = n_agents
        self.connections: List[SocialConnection] = []
        self.adjacency_matrix = np.zeros((n_agents, n_agents))
        
        self.stats = {
            'total_connections': 0,
            'avg_strength': 0.0,
            'avg_trust': 0.0,
            'network_density': 0.0
        }
    
    def add_connection(self, from_id: int, to_id: int, 
                      strength: float = 0.5, trust: float = 0.5):
        """添加社会连接"""
        if from_id == to_id:
            return
        
        connection = SocialConnection(
            from_agent=f"agent_{from_id}",
            to_agent=f"agent_{to_id}",
            strength=strength,
            trust=trust
        )
        
        self.connections.append(connection)
        self.adjacency_matrix[from_id, to_id] = strength
        
        self.stats['total_connections'] = len(self.connections)
        self._update_stats()
    
    def initialize_random_network(self, connection_prob: float = 0.3):
        """初始化随机社会网络"""
        for i in range(self.n_agents):
            for j in range(self.n_agents):
                if i != j and np.random.random() < connection_prob:
                    strength = np.random.uniform(0.3, 0.8)
                    trust = np.random.uniform(0.4, 0.7)
                    self.add_connection(i, j, strength, trust)
    
    def get_neighbors(self, agent_id: int) -> List[int]:
        """获取 Agent 的邻居"""
        neighbors = []
        for i in range(self.n_agents):
            if self.adjacency_matrix[agent_id, i] > 0:
                neighbors.append(i)
        return neighbors
    
    def _update_stats(self):
        """更新统计"""
        if self.connections:
            self.stats['avg_strength'] = np.mean([c.strength for c in self.connections])
            self.stats['avg_trust'] = np.mean([c.trust for c in self.connections])
        
        max_connections = self.n_agents * (self.n_agents - 1)
        self.stats['network_density'] = len(self.connections) / max_connections
    
    def get_status(self) -> Dict:
        """获取网络状态"""
        return {
            'stats': self.stats,
            'n_agents': self.n_agents,
            'connections': len(self.connections)
        }


class SocialLearner:
    """
    社会学习器
    
    实现观察学习和模仿算法
    """
    
    def __init__(self, agent_id: int, network: SocialNetwork):
        self.agent_id = agent_id
        self.network = network
        self.knowledge: Dict[str, float] = {}
        self.learning_history: List[Dict] = []
        
        self.stats = {
            'learning_events': 0,
            'knowledge_gained': 0,
            'imitation_success_rate': 0.0
        }
    
    def observe(self, model_agent_id: int, 
                model_knowledge: Dict[str, float]) -> Dict[str, float]:
        """
        观察学习
        
        Args:
            model_agent_id: 被观察的 Agent
            model_knowledge: 模型 Agent 的知识
            
        Returns:
            学到的知识
        """
        # 检查社会连接
        if model_agent_id not in self.network.get_neighbors(self.agent_id):
            return {}
        
        # 获取连接强度和信任度
        connection = None
        for conn in self.network.connections:
            if (conn.from_agent == f"agent_{self.agent_id}" and 
                conn.to_agent == f"agent_{model_agent_id}"):
                connection = conn
                break
        
        if not connection:
            return {}
        
        # 基于信任和强度学习知识
        learned_knowledge = {}
        for key, value in model_knowledge.items():
            # 学习效率 = 信任度 × 连接强度
            learning_efficiency = connection.trust * connection.strength
            
            if np.random.random() < learning_efficiency:
                # 成功学习
                self.knowledge[key] = value
                learned_knowledge[key] = value
                
                self.stats['knowledge_gained'] += 1
        
        self.stats['learning_events'] += 1
        self.learning_history.append({
            'timestamp': datetime.now().isoformat(),
            'model': model_agent_id,
            'learned': learned_knowledge
        })
        
        return learned_knowledge
    
    def imitate(self, model_agent_id: int, 
                model_behavior: str) -> bool:
        """
        模仿行为
        
        Args:
            model_agent_id: 被模仿的 Agent
            model_behavior: 被模仿的行为
            
        Returns:
            模仿是否成功
        """
        # 检查社会连接
        if model_agent_id not in self.network.get_neighbors(self.agent_id):
            return False
        
        # 获取连接
        connection = None
        for conn in self.network.connections:
            if (conn.from_agent == f"agent_{self.agent_id}" and 
                conn.to_agent == f"agent_{model_agent_id}"):
                connection = conn
                break
        
        if not connection:
            return False
        
        # 模仿成功率 = 信任度 × 连接强度 × 随机因子
        success_rate = connection.trust * connection.strength * np.random.uniform(0.8, 1.2)
        
        success = np.random.random() < success_rate
        
        if success:
            # 成功模仿
            if model_behavior not in self.knowledge:
                self.knowledge[model_behavior] = 0.5
            else:
                self.knowledge[model_behavior] = min(1.0, self.knowledge[model_behavior] + 0.1)
        
        self.stats['imitation_success_rate'] = (
            (self.stats['imitation_success_rate'] * self.stats['learning_events'] + 
             (1 if success else 0)) / 
            (self.stats['learning_events'] + 1)
        )
        
        return success
    
    def get_knowledge(self) -> Dict[str, float]:
        """获取知识"""
        return self.knowledge.copy()
    
    def get_status(self) -> Dict:
        """获取学习器状态"""
        return {
            'stats': self.stats,
            'knowledge_size': len(self.knowledge),
            'learning_events': self.stats['learning_events']
        }


class CulturalTransmissionExperiment:
    """
    文化传递实验
    
    验证社会学习和文化传递效果
    """
    
    def __init__(self, n_agents: int = 20, generations: int = 10):
        self.n_agents = n_agents
        self.generations = generations
        
        # 初始化社会网络
        self.network = SocialNetwork(n_agents)
        self.network.initialize_random_network(connection_prob=0.4)
        
        # 创建社会学习器
        self.learners = [
            SocialLearner(i, self.network) 
            for i in range(n_agents)
        ]
        
        # 实验数据
        self.experiment_data = {
            'config': {
                'n_agents': n_agents,
                'generations': generations
            },
            'metrics': [],
            'knowledge_spread': []
        }
    
    def run_experiment(self):
        """运行文化传递实验"""
        print(f"\n🚀 开始文化传递实验...")
        print(f"   Agent 数量：{self.n_agents}")
        print(f"   代数：{self.generations}")
        
        # 初始化：只有一个 Agent 有特殊知识
        initial_knowledge = {'innovation': 0.9, 'efficiency': 0.8}
        self.learners[0].knowledge = initial_knowledge
        
        # 运行多代
        for gen in range(self.generations):
            # 每个 Agent 观察和学习
            for learner in self.learners:
                neighbors = self.network.get_neighbors(learner.agent_id)
                
                for neighbor_id in neighbors:
                    neighbor = self.learners[neighbor_id]
                    
                    # 观察学习
                    if neighbor.knowledge:
                        learner.observe(neighbor_id, neighbor.knowledge)
                    
                    # 模仿行为
                    for behavior in neighbor.knowledge.keys():
                        learner.imitate(neighbor_id, behavior)
            
            # 记录指标
            if gen % 3 == 0:
                metrics = self._calculate_metrics()
                self.experiment_data['metrics'].append(metrics)
                
                print(f"   第{gen}代：知识传播={metrics['knowledge_spread']:.1%}, "
                      f"平均知识量={metrics['avg_knowledge']:.2f}, "
                      f"网络密度={self.network.stats['network_density']:.2f}")
        
        self.experiment_data['end_time'] = datetime.now().isoformat()
    
    def _calculate_metrics(self) -> Dict:
        """计算实验指标"""
        # 知识传播率
        knowledgeable_agents = sum(
            1 for learner in self.learners 
            if learner.knowledge
        )
        knowledge_spread = knowledgeable_agents / self.n_agents
        
        # 平均知识量
        total_knowledge = sum(
            len(learner.knowledge) 
            for learner in self.learners
        )
        avg_knowledge = total_knowledge / self.n_agents
        
        # 平均学习效率
        avg_learning_events = np.mean([
            learner.stats['learning_events'] 
            for learner in self.learners
        ])
        
        return {
            'generation': len(self.experiment_data['metrics']),
            'knowledge_spread': knowledge_spread,
            'avg_knowledge': avg_knowledge,
            'avg_learning_events': avg_learning_events,
            'network_density': self.network.stats['network_density']
        }
    
    def analyze_results(self) -> Dict:
        """分析实验结果"""
        metrics = self.experiment_data['metrics']
        
        if not metrics:
            return {}
        
        final = metrics[-1]
        initial = metrics[0] if metrics else {}
        
        return {
            'final_knowledge_spread': final.get('knowledge_spread', 0),
            'knowledge_retention_rate': (
                final.get('knowledge_spread', 0) / 
                max(initial.get('knowledge_spread', 1), 0.01)
            ),
            'avg_knowledge_growth': (
                final.get('avg_knowledge', 0) - 
                initial.get('avg_knowledge', 0)
            ),
            'generations': len(metrics),
            'intergenerational_stability': 1.0 / (1.0 + final.get('avg_knowledge', 0) * 0.1)
        }
    
    def save_results(self, output_dir: str = "experiments/results/v5.6"):
        """保存结果"""
        from pathlib import Path
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        self.experiment_data['results'] = self.analyze_results()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cultural_transmission_{timestamp}.json"
        filepath = output_path / filename
        
        import json
        with open(filepath, 'w') as f:
            json.dump(self.experiment_data, f, indent=2, default=str)
        
        return filepath


# 测试代码
if __name__ == '__main__':
    print("=" * 60)
    print("MOSS v5.6 - Social Learning Test")
    print("=" * 60)
    
    # 创建实验
    experiment = CulturalTransmissionExperiment(n_agents=20, generations=15)
    
    # 运行实验
    experiment.run_experiment()
    
    # 分析结果
    results = experiment.analyze_results()
    
    # 打印结果
    print("\n" + "=" * 60)
    print("🎉 实验完成！")
    print("=" * 60)
    print(f"   最终知识传播率   : {results['final_knowledge_spread']:.1%}")
    print(f"   知识保留率       : {results['knowledge_retention_rate']:.1%}")
    print(f"   知识增长         : {results['avg_knowledge_growth']:+.2f}")
    print(f"   代际稳定性       : {results['intergenerational_stability']:.3f}")
    print("=" * 60)
