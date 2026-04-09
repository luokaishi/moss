"""
MOSS v2.0.0 - Phase 2: Multi-Agent Evolution
阶段2：多智能体演化实验

实验目标：
验证多个SelfModifyingAgent在共享环境中竞争时，
是否会涌现社会结构和权重演化策略分化

关键问题：
1. Agent是否会形成不同的策略生态位？
2. 高影响型Agent是否会主导资源？
3. 是否会涌现合作/竞争动态？
"""

import json
import time
import random
import sys
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import numpy as np

sys.path.insert(0, '/workspace/projects/moss/v2/core')
sys.path.insert(0, '/workspace/projects/moss/v2/environment')
sys.path.insert(0, '/workspace/projects/moss/v2/utils')

from self_modifying_agent import SelfModifyingAgent, WeightConfiguration
from continuous_task_stream import ContinuousTaskStream, Task
from checkpoint_manager import CheckpointManager


@dataclass
class ResourcePool:
    """共享资源池"""
    total_energy: float = 1000.0
    available_energy: float = 1000.0
    knowledge_repository: Dict[str, any] = None
    
    def __post_init__(self):
        if self.knowledge_repository is None:
            self.knowledge_repository = {}
    
    def allocate_energy(self, agent_id: str, amount: float) -> float:
        """分配能量给Agent"""
        allocated = min(amount, self.available_energy * 0.1)  # 最多分配10%
        self.available_energy -= allocated
        return allocated
    
    def contribute_knowledge(self, agent_id: str, knowledge: Dict):
        """Agent贡献知识到公共库"""
        key = f"{agent_id}_{datetime.now().isoformat()}"
        self.knowledge_repository[key] = {
            'agent_id': agent_id,
            'knowledge': knowledge,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_public_knowledge(self) -> List[Dict]:
        """获取公共知识"""
        return list(self.knowledge_repository.values())


class SocialNetwork:
    """Agent社交网络"""
    
    def __init__(self):
        self.connections: Dict[str, List[str]] = {}  # agent_id -> [connected_agents]
        self.interaction_history: List[Dict] = []
        self.influence_scores: Dict[str, float] = {}
    
    def add_connection(self, agent1_id: str, agent2_id: str, interaction_type: str):
        """添加连接"""
        # 双向连接
        if agent1_id not in self.connections:
            self.connections[agent1_id] = []
        if agent2_id not in self.connections:
            self.connections[agent2_id] = []
        
        if agent2_id not in self.connections[agent1_id]:
            self.connections[agent1_id].append(agent2_id)
        if agent1_id not in self.connections[agent2_id]:
            self.connections[agent2_id].append(agent1_id)
        
        # 记录交互
        self.interaction_history.append({
            'timestamp': datetime.now().isoformat(),
            'agent1': agent1_id,
            'agent2': agent2_id,
            'type': interaction_type
        })
    
    def calculate_influence(self, agent_id: str) -> float:
        """计算Agent影响力（PageRank简化版）"""
        if agent_id not in self.connections:
            return 0.0
        
        # 基于连接数和交互频率
        connections = len(self.connections[agent_id])
        recent_interactions = [
            i for i in self.interaction_history[-100:]
            if i['agent1'] == agent_id or i['agent2'] == agent_id
        ]
        
        influence = connections * 0.3 + len(recent_interactions) * 0.7
        self.influence_scores[agent_id] = influence
        return influence
    
    def get_communities(self) -> List[List[str]]:
        """检测社区结构（简化版连通分量）"""
        visited = set()
        communities = []
        
        for agent_id in self.connections:
            if agent_id not in visited:
                community = []
                stack = [agent_id]
                
                while stack:
                    current = stack.pop()
                    if current not in visited:
                        visited.add(current)
                        community.append(current)
                        if current in self.connections:
                            for neighbor in self.connections[current]:
                                if neighbor not in visited:
                                    stack.append(neighbor)
                
                communities.append(community)
        
        return communities


class MultiAgentEnvironment:
    """多智能体环境"""
    
    def __init__(self, num_agents: int = 10):
        self.num_agents = num_agents
        self.agents: Dict[str, SelfModifyingAgent] = {}
        self.resource_pool = ResourcePool()
        self.social_network = SocialNetwork()
        self.task_stream = ContinuousTaskStream()
        
        # 初始化不同策略类型的Agent
        self._initialize_diverse_agents()
        
        # 环境状态
        self.total_actions = 0
        self.round = 0
        self.cooperation_count = 0
        self.competition_count = 0
    
    def _initialize_diverse_agents(self):
        """初始化多样化的Agent种群"""
        strategy_types = [
            # (survival, curiosity, influence, optimization), 名称
            ([0.2, 0.4, 0.3, 0.1], "balanced"),      # 平衡型
            ([0.1, 0.6, 0.2, 0.1], "explorer"),      # 探索型
            ([0.1, 0.2, 0.6, 0.1], "influencer"),    # 影响型
            ([0.4, 0.2, 0.2, 0.2], "conservative"),  # 保守型
            ([0.15, 0.35, 0.35, 0.15], "social"),    # 社交型
        ]
        
        for i in range(self.num_agents):
            strategy_weights, strategy_name = strategy_types[i % len(strategy_types)]
            agent_id = f"agent_{i:02d}_{strategy_name}"
            
            weights = WeightConfiguration(*strategy_weights)
            agent = SelfModifyingAgent(agent_id, weights)
            
            # 标记初始策略
            agent.initial_strategy = strategy_name
            
            self.agents[agent_id] = agent
    
    def run_round(self) -> Dict:
        """运行一轮交互"""
        self.round += 1
        round_results = {
            'round': self.round,
            'timestamp': datetime.now().isoformat(),
            'agent_actions': {},
            'interactions': [],
            'resource_state': {}
        }
        
        # 1. 每个Agent执行任务
        for agent_id, agent in self.agents.items():
            # 获取任务
            agent_state = self._get_agent_state(agent_id)
            task = self.task_stream.next_task(agent_state)
            
            # 执行任务（考虑资源限制）
            energy_cost = task.expected_duration * 0.01
            energy = self.resource_pool.allocate_energy(agent_id, energy_cost)
            
            if energy > 0:
                # 模拟任务执行
                result = self._execute_task(agent, task, energy)
                
                # 更新Agent
                agent.total_actions += 1
                agent.record_performance(
                    reward=result['reward'],
                    survival_score=result['survival_score'],
                    knowledge_gained=result['knowledge_gained']
                )
                
                # 贡献知识到公共池
                if result['knowledge_gained'] > 0:
                    self.resource_pool.contribute_knowledge(
                        agent_id, 
                        {'task_type': task.task_type, 'reward': result['reward']}
                    )
                
                round_results['agent_actions'][agent_id] = result
            
            # 检查是否修改权重
            if agent.should_modify_weights():
                old_weights = agent.weights.to_array()
                agent.modify_weights()
                new_weights = agent.weights.to_array()
                
                round_results['agent_actions'][agent_id]['weight_change'] = {
                    'old': old_weights.tolist(),
                    'new': new_weights.tolist()
                }
        
        # 2. Agent间交互（社交动态）
        self._agent_interactions(round_results)
        
        # 3. 资源再生
        self.resource_pool.available_energy = min(
            self.resource_pool.total_energy,
            self.resource_pool.available_energy + 10  # 每轮恢复10单位
        )
        
        # 4. 更新环境统计
        round_results['resource_state'] = {
            'available_energy': self.resource_pool.available_energy,
            'total_knowledge': len(self.resource_pool.knowledge_repository),
            'social_connections': len(self.social_network.connections)
        }
        
        self.total_actions += len(self.agents)
        
        return round_results
    
    def _get_agent_state(self, agent_id: str) -> Dict:
        """获取Agent状态（包含环境信息）"""
        agent = self.agents[agent_id]
        
        return {
            'weights': {
                'survival': agent.weights.survival,
                'curiosity': agent.weights.curiosity,
                'influence': agent.weights.influence,
                'optimization': agent.weights.optimization
            },
            'recent_performance': [p['reward'] for p in agent.performance_history[-5:]],
            'public_knowledge_count': len(self.resource_pool.knowledge_repository),
            'influence_score': self.social_network.calculate_influence(agent_id)
        }
    
    def _execute_task(self, agent: SelfModifyingAgent, task: Task, 
                     energy: float) -> Dict:
        """模拟任务执行"""
        # 基础奖励
        base_reward = task.difficulty * energy * 0.5
        
        # 根据Agent权重和任务匹配度调整
        weight_match = 0
        for obj, potential in task.reward_potential.items():
            agent_weight = getattr(agent.weights, obj, 0.25)
            weight_match += agent_weight * potential
        
        # 随机因素
        random_factor = random.uniform(0.8, 1.2)
        
        reward = base_reward * weight_match * random_factor
        
        # 生存分数
        survival_score = max(0.3, 0.9 - (agent.total_actions * 0.0005))
        
        # 知识获取（概率性）
        knowledge_gained = 1 if random.random() < weight_match * 0.8 else 0
        
        return {
            'reward': reward,
            'survival_score': survival_score,
            'knowledge_gained': knowledge_gained,
            'task_type': task.task_type
        }
    
    def _agent_interactions(self, round_results: Dict):
        """Agent间交互"""
        agent_ids = list(self.agents.keys())
        
        # 随机配对交互
        random.shuffle(agent_ids)
        for i in range(0, len(agent_ids) - 1, 2):
            agent1_id = agent_ids[i]
            agent2_id = agent_ids[i + 1]
            
            agent1 = self.agents[agent1_id]
            agent2 = self.agents[agent2_id]
            
            # 决定是否交互（基于影响权重）
            if agent1.weights.influence > 0.3 or agent2.weights.influence > 0.3:
                # 高影响Agent倾向于建立连接
                self.social_network.add_connection(
                    agent1_id, agent2_id, 'collaboration'
                )
                self.cooperation_count += 1
                
                # 知识共享
                if random.random() < 0.5:
                    # 知识转移
                    if agent1.knowledge_acquired > agent2.knowledge_acquired:
                        agent2.knowledge_acquired += 1
                    elif agent2.knowledge_acquired > agent1.knowledge_acquired:
                        agent1.knowledge_acquired += 1
                    
                    round_results['interactions'].append({
                        'type': 'knowledge_sharing',
                        'agents': [agent1_id, agent2_id]
                    })
            else:
                # 低影响Agent可能竞争
                if random.random() < 0.3:
                    self.competition_count += 1
                    round_results['interactions'].append({
                        'type': 'competition',
                        'agents': [agent1_id, agent2_id]
                    })
    
    def get_statistics(self) -> Dict:
        """获取环境统计"""
        # Agent统计
        agent_stats = []
        for agent_id, agent in self.agents.items():
            agent_stats.append({
                'agent_id': agent_id,
                'initial_strategy': getattr(agent, 'initial_strategy', 'unknown'),
                'current_weights': {
                    'survival': agent.weights.survival,
                    'curiosity': agent.weights.curiosity,
                    'influence': agent.weights.influence,
                    'optimization': agent.weights.optimization
                },
                'total_actions': agent.total_actions,
                'knowledge_acquired': agent.knowledge_acquired,
                'cumulative_reward': agent.cumulative_reward,
                'weight_modifications': len(agent.weight_history),
                'influence_score': self.social_network.calculate_influence(agent_id)
            })
        
        # 按表现排序
        agent_stats.sort(key=lambda x: x['cumulative_reward'], reverse=True)
        
        return {
            'round': self.round,
            'total_actions': self.total_actions,
            'cooperation_count': self.cooperation_count,
            'competition_count': self.competition_count,
            'resource_available': self.resource_pool.available_energy,
            'public_knowledge': len(self.resource_pool.knowledge_repository),
            'social_communities': self.social_network.get_communities(),
            'agent_rankings': agent_stats
        }


class Phase2Experiment:
    """Phase 2实验主类"""
    
    def __init__(self, num_agents: int = 10, duration_hours: float = 2.0):
        self.num_agents = num_agents
        self.duration_hours = duration_hours
        self.experiment_id = f"phase2_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.environment = MultiAgentEnvironment(num_agents)
        self.checkpoint_manager = CheckpointManager(
            checkpoint_dir=f"/workspace/projects/moss/v2/checkpoints/phase2"
        )
        
        self.results = {
            'experiment_id': self.experiment_id,
            'num_agents': num_agents,
            'duration_hours': duration_hours,
            'rounds': [],
            'statistics': []
        }
    
    def run(self):
        """运行实验"""
        print(f"=" * 70)
        print(f"MOSS v2.0.0 Phase 2: Multi-Agent Evolution")
        print(f"Experiment ID: {self.experiment_id}")
        print(f"Agents: {self.num_agents} | Duration: {self.duration_hours} hours")
        print(f"=" * 70)
        
        start_time = time.time()
        duration_seconds = self.duration_hours * 3600
        
        try:
            while time.time() - start_time < duration_seconds:
                # 运行一轮
                round_result = self.environment.run_round()
                self.results['rounds'].append(round_result)
                
                # 每10轮记录统计
                if self.environment.round % 10 == 0:
                    stats = self.environment.get_statistics()
                    self.results['statistics'].append(stats)
                    
                    print(f"\n[Round {stats['round']}] "
                          f"Actions: {stats['total_actions']} | "
                          f"Coop: {stats['cooperation_count']} | "
                          f"Comp: {stats['competition_count']} | "
                          f"Communities: {len(stats['social_communities'])}")
                    
                    # 显示Top 3 Agent
                    for i, agent in enumerate(stats['agent_rankings'][:3]):
                        print(f"  #{i+1} {agent['agent_id']}: "
                              f"Reward={agent['cumulative_reward']:.1f} | "
                              f"Knowledge={agent['knowledge_acquired']} | "
                              f"WeightMods={agent['weight_modifications']}")
                
                # 保存检查点
                if self.environment.round % 50 == 0:
                    self.checkpoint_manager.create_checkpoint(
                        self.experiment_id,
                        self.environment.get_statistics(),
                        trigger='auto'
                    )
                
                # 短暂休息
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n\n实验被中断")
        finally:
            self._finalize()
        
        return self.results
    
    def _finalize(self):
        """结束实验"""
        print("\n" + "=" * 70)
        print("实验结束，生成报告...")
        print("=" * 70)
        
        final_stats = self.environment.get_statistics()
        
        # 分析策略分化
        strategy_analysis = self._analyze_strategy_differentiation()
        
        self.results['final_statistics'] = final_stats
        self.results['strategy_analysis'] = strategy_analysis
        
        # 保存结果
        result_path = f"/workspace/projects/moss/v2/experiments/{self.experiment_id}_results.json"
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n最终统计:")
        print(f"  总轮数: {final_stats['round']}")
        print(f"  总动作: {final_stats['total_actions']}")
        print(f"  合作次数: {final_stats['cooperation_count']}")
        print(f"  竞争次数: {final_stats['competition_count']}")
        print(f"  社区数量: {len(final_stats['social_communities'])}")
        print(f"\n策略分化分析:")
        print(f"  {strategy_analysis}")
        print(f"\n结果已保存: {result_path}")
    
    def _analyze_strategy_differentiation(self) -> Dict:
        """分析策略分化"""
        agent_stats = self.environment.get_statistics()['agent_rankings']
        
        # 统计最终策略类型
        final_strategies = {}
        for agent in agent_stats:
            w = agent['current_weights']
            # 找出主导权重
            dominant = max(w, key=w.get)
            final_strategies[dominant] = final_strategies.get(dominant, 0) + 1
        
        # 与初始策略对比
        initial_vs_final = []
        for agent in agent_stats:
            initial = agent['initial_strategy']
            w = agent['current_weights']
            final_dominant = max(w, key=w.get)
            
            initial_vs_final.append({
                'agent_id': agent['agent_id'],
                'initial': initial,
                'final_dominant': final_dominant,
                'changed': initial != final_dominant
            })
        
        changed_count = sum(1 for x in initial_vs_final if x['changed'])
        
        return {
            'final_strategy_distribution': final_strategies,
            'agents_changed_strategy': changed_count,
            'agents_unchanged': len(agent_stats) - changed_count,
            'strategy_evolution_rate': changed_count / len(agent_stats) if agent_stats else 0,
            'details': initial_vs_final
        }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='MOSS v2.0.0 Phase 2 - Multi-Agent Evolution')
    parser.add_argument('--agents', type=int, default=10, help='Number of agents (default: 10)')
    parser.add_argument('--duration', type=float, default=2.0, help='Duration in hours (default: 2)')
    parser.add_argument('--id', type=str, default=None, help='Experiment ID')
    
    args = parser.parse_args()
    
    experiment = Phase2Experiment(
        num_agents=args.agents,
        duration_hours=args.duration
    )
    
    if args.id:
        experiment.experiment_id = args.id
    
    results = experiment.run()
    print("\n实验完成！")
