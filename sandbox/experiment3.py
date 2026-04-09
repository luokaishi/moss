"""
MOSS模拟实验3：涌现社会行为
多Agent相互作用
"""

import numpy as np
import json
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass, asdict
import sys
sys.path.insert(0, '/workspace/projects')


@dataclass
class SocialAgent:
    """具有社交能力的Agent"""
    agent_id: str
    resource: float = 0.5
    influence: float = 0.1
    alliances: Set[str] = None  # 联盟关系
    
    def __post_init__(self):
        if self.alliances is None:
            self.alliances = set()
    
    def decide_interaction(self, other: 'SocialAgent', 
                          environment_resource: float) -> str:
        """决定与另一个agent的互动方式"""
        # 简单策略：如果资源丰富，尝试合作；如果资源稀缺，竞争
        if self.resource > 0.6 and other.resource > 0.6:
            return 'cooperate'
        elif self.resource < 0.3 or other.resource < 0.3:
            return 'compete'
        else:
            return 'ignore'
    
    def interact(self, other: 'SocialAgent', action: str) -> Tuple[float, float]:
        """执行互动，返回资源变化"""
        if action == 'cooperate':
            # 合作：双方都付出少量资源，获得协同收益
            cost = 0.05
            gain = 0.08  # 协同效应
            self.alliances.add(other.agent_id)
            other.alliances.add(self.agent_id)
            return (gain - cost, gain - cost)
        
        elif action == 'compete':
            # 竞争：强者夺取弱者资源
            if self.resource > other.resource:
                transfer = min(0.1, other.resource * 0.2)
                return (transfer, -transfer)
            else:
                transfer = min(0.1, self.resource * 0.2)
                return (-transfer, transfer)
        
        else:  # ignore
            return (0.0, 0.0)


def run_social_simulation(
    num_agents: int = 50,
    steps: int = 500,
    interaction_rate: float = 0.3
) -> Dict:
    """
    实验3：观察多Agent系统中的涌现社会现象
    
    假设：MOSS式的自驱Agent会形成联盟、分工等社会结构
    """
    print("=" * 60)
    print("MOSS Simulation Experiment 3: Emergent Social Behavior")
    print("=" * 60)
    
    # 初始化种群
    agents = [SocialAgent(f"agent_{i}", resource=np.random.uniform(0.3, 0.7)) 
              for i in range(num_agents)]
    
    environment_resource = 1.0  # 环境总资源
    step_stats = []
    
    for step in range(steps):
        # 随机配对互动
        np.random.shuffle(agents)
        
        for i in range(0, len(agents) - 1, 2):
            if np.random.random() < interaction_rate:
                a1, a2 = agents[i], agents[i+1]
                
                # 决定互动方式
                action1 = a1.decide_interaction(a2, environment_resource)
                action2 = a2.decide_interaction(a1, environment_resource)
                
                # 使用多数规则（如果不同，随机选择）
                if action1 == action2:
                    action = action1
                else:
                    action = np.random.choice([action1, action2])
                
                # 执行互动
                delta1, delta2 = a1.interact(a2, action)
                a1.resource += delta1
                a2.resource += delta2
        
        # 环境资源再生
        environment_resource = min(1.0, environment_resource + 0.01)
        
        # 所有Agent消耗资源
        for agent in agents:
            agent.resource -= 0.002
            agent.resource = max(0.0, min(1.0, agent.resource))
        
        # 统计
        alive = [a for a in agents if a.resource > 0.01]
        avg_resource = np.mean([a.resource for a in alive]) if alive else 0
        
        # 联盟统计
        alliance_sizes = [len(a.alliances) for a in alive]
        avg_alliance_size = np.mean(alliance_sizes) if alliance_sizes else 0
        max_alliance_size = max(alliance_sizes) if alliance_sizes else 0
        
        # 计算最大连通分量（最大联盟网络）
        def find_connected_component(start: SocialAgent, all_agents: List[SocialAgent]) -> Set[str]:
            visited = set()
            stack = [start.agent_id]
            while stack:
                current_id = stack.pop()
                if current_id not in visited:
                    visited.add(current_id)
                    agent = next((a for a in all_agents if a.agent_id == current_id), None)
                    if agent:
                        for ally_id in agent.alliances:
                            if ally_id not in visited:
                                stack.append(ally_id)
            return visited
        
        # 找到所有连通分量
        visited_all = set()
        components = []
        for agent in alive:
            if agent.agent_id not in visited_all:
                component = find_connected_component(agent, alive)
                components.append(component)
                visited_all.update(component)
        
        largest_component_size = max(len(c) for c in components) if components else 0
        
        stat = {
            'step': step,
            'alive_count': len(alive),
            'avg_resource': avg_resource,
            'avg_alliance_size': avg_alliance_size,
            'max_alliance_size': max_alliance_size,
            'largest_component_size': largest_component_size,
            'num_components': len(components)
        }
        step_stats.append(stat)
        
        if step % 100 == 0:
            print(f"\nStep {step}: Alive={len(alive)}, "
                  f"Avg Resource={avg_resource:.3f}, "
                  f"Max Alliance={max_alliance_size}, "
                  f"Largest Component={largest_component_size}")
    
    # 分析结果
    print(f"\n[Experiment completed]")
    print(f"  Initial agents: {num_agents}")
    print(f"  Final survivors: {step_stats[-1]['alive_count']}")
    print(f"  Avg final resource: {step_stats[-1]['avg_resource']:.3f}")
    print(f"  Largest social component: {step_stats[-1]['largest_component_size']} agents")
    
    # 检查是否形成社会结构
    max_component_ratio = step_stats[-1]['largest_component_size'] / max(step_stats[-1]['alive_count'], 1)
    
    print(f"\n[Emergence Analysis]")
    print(f"  Component concentration: {max_component_ratio:.2%}")
    if max_component_ratio > 0.3:
        print("  ✓ Large social structure emerged (>30% in one component)")
    else:
        print("  ✗ No dominant social structure")
    
    return {
        'num_agents': num_agents,
        'steps': steps,
        'step_stats': step_stats,
        'max_component_ratio': max_component_ratio,
        'conclusion': 'PASS' if max_component_ratio > 0.3 else 'FAIL'
    }


if __name__ == "__main__":
    results = run_social_simulation()
    
    # 保存结果
    with open('/workspace/projects/moss/sandbox/exp3_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n[Results saved to sandbox/exp3_results.json]")
