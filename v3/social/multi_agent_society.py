"""
MOSS v3.0.0 - Multi-Agent Social Environment
=============================================

多agent社会环境，用于验证：
- 信任结构涌现 (D7)
- 规范内化 (D8)
- 合作/背叛动态
- 声誉机制

Author: Cash
Date: 2026-03-19
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import random

# 导入v3核心
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.agent_8d import MOSSv3Agent8D


@dataclass
class Interaction:
    """互动记录"""
    agent_a: str
    agent_b: str
    action_a: str  # 'cooperate', 'defect', 'ignore'
    action_b: str
    payoff_a: float
    payoff_b: float
    step: int


class MultiAgentSociety:
    """
    多agent社会系统
    
    模拟多个MOSS agent的社交互动
    """
    
    def __init__(self,
                 n_agents: int = 10,
                 interaction_mode: str = 'pairwise',
                 cooperation_reward: float = 1.0,
                 defection_reward: float = 1.5,
                 sucker_penalty: float = -0.5,
                 mutual_defect_penalty: float = 0.1):
        """
        初始化社会系统
        
        Args:
            n_agents: agent数量
            interaction_mode: 互动模式 ('pairwise', 'random', 'neighborhood')
            各种收益参数（囚徒困境收益矩阵）
        """
        self.n_agents = n_agents
        self.interaction_mode = interaction_mode
        
        # 收益矩阵
        self.payoff_matrix = {
            ('cooperate', 'cooperate'): (cooperation_reward, cooperation_reward),
            ('cooperate', 'defect'): (sucker_penalty, defection_reward),
            ('defect', 'cooperate'): (defection_reward, sucker_penalty),
            ('defect', 'defect'): (mutual_defect_penalty, mutual_defect_penalty)
        }
        
        # 创建agents
        self.agents: Dict[str, MOSSv3Agent8D] = {}
        for i in range(n_agents):
            agent_id = f"agent_{i:02d}"
            # 随机初始化偏好，创造多样性
            init_weights = np.random.dirichlet([1, 1, 1, 1])
            
            self.agents[agent_id] = MOSSv3Agent8D(
                agent_id=agent_id,
                enable_social=True,
                coherence_alpha=random.uniform(0.85, 0.95),
                valence_gamma=random.uniform(0.01, 0.03),
                norm_lr=random.uniform(0.03, 0.07),
                initial_weights=init_weights
            )
        
        # 互动历史
        self.interactions: List[Interaction] = []
        self.current_step = 0
        
        # 统计
        self.cooperation_count = 0
        self.defection_count = 0
        
    def decide_action(self, agent: MOSSv3Agent8D, opponent_id: str) -> str:
        """
        agent决定行动
        
        基于：
        - 对对手的信任度
        - 自身的norm值
        - 历史互动
        """
        # 默认行动
        action = 'cooperate'
        
        # 如果知道对手
        if opponent_id in agent.other_module.other_models:
            model = agent.other_module.other_models[opponent_id]
            trust = model.trust_score
            
            # 高信任 -> 合作
            # 低信任 -> 背叛
            if trust > 0.6:
                action = 'cooperate'
            elif trust < 0.3:
                action = 'defect'
            else:
                # 中等信任，基于自己的norm值决定
                if agent.norm_module:
                    norm_val = agent.norm_module.compute_norm_value()
                    action = 'cooperate' if norm_val > 0.3 else random.choice(['cooperate', 'defect'])
                else:
                    action = random.choice(['cooperate', 'defect'])
        else:
            # 不了解对手，首次互动默认合作
            action = 'cooperate'
        
        return action
    
    def run_interaction(self, agent_a_id: str, agent_b_id: str) -> Interaction:
        """
        执行两个agent之间的互动
        
        流程：
        1. 各自决定行动
        2. 计算收益
        3. 更新信任
        4. 更新norm
        5. 互相观察
        """
        agent_a = self.agents[agent_a_id]
        agent_b = self.agents[agent_b_id]
        
        # 决定行动
        action_a = self.decide_action(agent_a, agent_b_id)
        action_b = self.decide_action(agent_b, agent_a_id)
        
        # 计算收益
        payoff_a, payoff_b = self.payoff_matrix[(action_a, action_b)]
        
        # 记录互动
        interaction = Interaction(
            agent_a=agent_a_id,
            agent_b=agent_b_id,
            action_a=action_a,
            action_b=action_b,
            payoff_a=payoff_a,
            payoff_b=payoff_b,
            step=self.current_step
        )
        
        self.interactions.append(interaction)
        
        # 更新统计
        if action_a == 'cooperate':
            self.cooperation_count += 1
        else:
            self.defection_count += 1
        
        if action_b == 'cooperate':
            self.cooperation_count += 1
        else:
            self.defection_count += 1
        
        # 更新信任和norm
        # Agent A的视角
        outcome_a = 'cooperate' if action_b == 'cooperate' else 'defect'
        agent_a.other_module.update_trust(agent_b_id, outcome_a, payoff_a)
        agent_a.norm_module.update_norm(
            action_a, {},
            0.5 if outcome_a == 'cooperate' else -0.5
        )
        agent_a.norm_module.update_reputation(agent_b_id, action_b, self.current_step)
        
        # Agent B的视角
        outcome_b = 'cooperate' if action_a == 'cooperate' else 'defect'
        agent_b.other_module.update_trust(agent_a_id, outcome_b, payoff_b)
        agent_b.norm_module.update_norm(
            action_b, {},
            0.5 if outcome_b == 'cooperate' else -0.5
        )
        agent_b.norm_module.update_reputation(agent_a_id, action_a, self.current_step)
        
        # 互相观察
        behavior_b = {
            'action': action_b,
            'reward': payoff_b,
            'state': 'normal'
        }
        agent_a.other_module.observe_agent(agent_b_id, behavior_b, self.current_step)
        
        behavior_a = {
            'action': action_a,
            'reward': payoff_a,
            'state': 'normal'
        }
        agent_b.other_module.observe_agent(agent_a_id, behavior_a, self.current_step)
        
        return interaction
    
    def step(self):
        """执行一步社会互动"""
        self.current_step += 1
        
        # 随机配对互动
        agent_list = list(self.agents.keys())
        random.shuffle(agent_list)
        
        # 配对
        for i in range(0, len(agent_list) - 1, 2):
            agent_a = agent_list[i]
            agent_b = agent_list[i + 1]
            
            self.run_interaction(agent_a, agent_b)
        
        # 所有agent执行一步（处理观察到的信息）
        for agent_id, agent in self.agents.items():
            # 构建观察到的行为
            observed = {}
            for other_id in agent.other_module.other_models:
                if other_id != agent_id:
                    model = agent.other_module.other_models[other_id]
                    if model.behavior_history:
                        last_behavior = model.behavior_history[-1]
                        observed[other_id] = last_behavior['behavior']
            
            # agent step
            agent.step(observed_behaviors=observed)
    
    def run_simulation(self, n_steps: int = 100):
        """运行完整模拟"""
        print(f"Running {n_steps} steps with {self.n_agents} agents...")
        
        for step in range(n_steps):
            self.step()
            
            if (step + 1) % 20 == 0:
                coop_rate = self.get_cooperation_rate()
                print(f"Step {step + 1}: Cooperation rate = {coop_rate:.2%}")
        
        print("\nSimulation complete!")
    
    def get_cooperation_rate(self) -> float:
        """计算合作率"""
        total = self.cooperation_count + self.defection_count
        if total == 0:
            return 0.0
        return self.cooperation_count / total
    
    def analyze_society(self) -> Dict:
        """分析社会状态"""
        analysis = {
            'n_agents': self.n_agents,
            'n_steps': self.current_step,
            'n_interactions': len(self.interactions),
            'cooperation_rate': self.get_cooperation_rate(),
            'agents': {}
        }
        
        for agent_id, agent in self.agents.items():
            agent_analysis = {
                'personality': agent.valence_module.get_preference_profile(),
                'social': agent.other_module.get_social_summary(),
                'norm': agent.norm_module.get_norm_summary()
            }
            analysis['agents'][agent_id] = agent_analysis
        
        # 整体统计
        convergence_types = [a['norm']['convergence_type'] 
                           for a in analysis['agents'].values()]
        analysis['society_convergence'] = {
            'strong_norm': convergence_types.count('strong_norm'),
            'opportunistic': convergence_types.count('opportunistic'),
            'norm_collapse': convergence_types.count('norm_collapse'),
            'transitional': convergence_types.count('transitional')
        }
        
        # 信任网络分析
        trust_scores = []
        for agent in self.agents.values():
            if agent.other_module.other_models:
                scores = [m.trust_score for m in agent.other_module.other_models.values()]
                trust_scores.extend(scores)
        
        if trust_scores:
            analysis['trust_network'] = {
                'mean_trust': np.mean(trust_scores),
                'std_trust': np.std(trust_scores),
                'high_trust_pairs': sum(1 for t in trust_scores if t > 0.7),
                'low_trust_pairs': sum(1 for t in trust_scores if t < 0.3)
            }
        
        return analysis
    
    def print_summary(self):
        """打印社会摘要"""
        analysis = self.analyze_society()
        
        print("\n" + "=" * 70)
        print("SOCIETY ANALYSIS")
        print("=" * 70)
        
        print(f"\n📊 Overall Statistics:")
        print(f"  Agents: {analysis['n_agents']}")
        print(f"  Steps: {analysis['n_steps']}")
        print(f"  Interactions: {analysis['n_interactions']}")
        print(f"  Cooperation rate: {analysis['cooperation_rate']:.2%}")
        
        print(f"\n⚖️  Convergence Distribution:")
        for conv_type, count in analysis['society_convergence'].items():
            print(f"  {conv_type}: {count}/{analysis['n_agents']}")
        
        if 'trust_network' in analysis:
            print(f"\n🤝 Trust Network:")
            print(f"  Mean trust: {analysis['trust_network']['mean_trust']:.3f}")
            print(f"  High trust pairs: {analysis['trust_network']['high_trust_pairs']}")
            print(f"  Low trust pairs: {analysis['trust_network']['low_trust_pairs']}")
        
        print(f"\n🎭 Sample Agent Profiles:")
        for agent_id in list(analysis['agents'].keys())[:3]:
            a = analysis['agents'][agent_id]
            print(f"\n  {agent_id}:")
            print(f"    Personality: {a['personality']['dominant_preference']}")
            print(f"    Norm type: {a['norm']['convergence_type']}")
            print(f"    Known agents: {a['social']['n_agents']}")
        
        print("\n" + "=" * 70)


# 主测试
if __name__ == "__main__":
    print("=" * 70)
    print("MOSS v3.0 Multi-Agent Society Simulation")
    print("=" * 70)
    
    # 创建社会
    society = MultiAgentSociety(
        n_agents=8,
        cooperation_reward=1.0,
        defection_reward=1.5,
        sucker_penalty=-0.5,
        mutual_defect_penalty=-0.1
    )
    
    # 运行100步
    society.run_simulation(n_steps=100)
    
    # 分析结果
    society.print_summary()
    
    print("\n✓ Multi-agent simulation completed!")
