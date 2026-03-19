"""
MOSS v3.0.0 - Long-term Simulation (10,000+ steps)
==================================================

长时模拟以观察：
1. 三种收敛形态的分化（强规范/机会主义/规范崩塌）
2. 身份锁定的稳定性
3. 人格类型的长期演化
4. 社会结构的动态变化

Author: Cash
Date: 2026-03-19
"""

import numpy as np
import json
from datetime import datetime
from typing import Dict, List
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from social.multi_agent_society import MultiAgentSociety


class LongTermSimulation:
    """长时模拟器"""
    
    def __init__(self, n_agents: int = 10):
        self.n_agents = n_agents
        self.checkpoint_interval = 1000  # 每1000步保存检查点
        
    def run_long_term(self, 
                     n_steps: int = 10000,
                     checkpoint_dir: str = 'v3/experiments/long_term_checkpoints') -> Dict:
        """
        运行长时模拟
        
        Args:
            n_steps: 总步数（默认10,000）
            checkpoint_dir: 检查点保存目录
            
        Returns:
            完整模拟结果
        """
        os.makedirs(checkpoint_dir, exist_ok=True)
        
        print("="*70)
        print(f"MOSS v3.0 Long-term Simulation")
        print(f"Steps: {n_steps:,}, Agents: {self.n_agents}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        # 创建社会
        society = MultiAgentSociety(n_agents=self.n_agents)
        
        # 历史记录
        history = {
            'cooperation_rates': [],
            'trust_evolution': [],
            'norm_evolution': [],
            'personality_evolution': [],
            'checkpoints': []
        }
        
        # 运行模拟
        for step in range(n_steps):
            society.step()
            
            # 每100步记录
            if step % 100 == 0:
                # 合作率
                coop_rate = society.get_cooperation_rate()
                history['cooperation_rates'].append(coop_rate)
                
                # 信任网络
                trust_scores = []
                for agent in society.agents.values():
                    if agent.other_module and agent.other_module.other_models:
                        scores = [m.trust_score for m in agent.other_module.other_models.values()]
                        trust_scores.extend(scores)
                
                if trust_scores:
                    history['trust_evolution'].append({
                        'step': step,
                        'mean': np.mean(trust_scores),
                        'std': np.std(trust_scores),
                        'min': np.min(trust_scores),
                        'max': np.max(trust_scores)
                    })
                
                # 人格类型分布
                personalities = []
                for agent in society.agents.values():
                    if agent.valence_module:
                        profile = agent.valence_module.get_preference_profile()
                        personalities.append(profile['dominant_preference'])
                
                from collections import Counter
                history['personality_evolution'].append({
                    'step': step,
                    'distribution': dict(Counter(personalities))
                })
                
                # 规范值
                norm_values = []
                for agent in society.agents.values():
                    if agent.norm_module:
                        norm_values.append(agent.norm_module.compute_norm_value())
                
                if norm_values:
                    history['norm_evolution'].append({
                        'step': step,
                        'mean': np.mean(norm_values),
                        'std': np.std(norm_values)
                    })
            
            # 检查点保存
            if step > 0 and step % self.checkpoint_interval == 0:
                print(f"\n{'='*70}")
                print(f"Checkpoint at step {step:,}")
                print(f"{'='*70}")
                
                checkpoint = self._create_checkpoint(society, step)
                history['checkpoints'].append(checkpoint)
                
                # 保存到文件
                checkpoint_file = os.path.join(
                    checkpoint_dir, 
                    f'checkpoint_{step:06d}.json'
                )
                with open(checkpoint_file, 'w') as f:
                    json.dump(checkpoint, f, indent=2, default=str)
                
                print(f"Cooperation rate: {coop_rate:.2%}")
                if trust_scores:
                    print(f"Mean trust: {np.mean(trust_scores):.4f}")
                print(f"Saved to: {checkpoint_file}")
        
        # 最终分析
        final_analysis = society.analyze_society()
        
        results = {
            'config': {
                'n_agents': self.n_agents,
                'n_steps': n_steps,
                'start_time': datetime.now().isoformat()
            },
            'history': history,
            'final_state': final_analysis,
            'convergence_analysis': self._analyze_convergence(history, society)
        }
        
        # 保存完整结果
        result_file = os.path.join(checkpoint_dir, 'final_results.json')
        with open(result_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        return results
    
    def _create_checkpoint(self, society: MultiAgentSociety, step: int) -> Dict:
        """创建检查点"""
        checkpoint = {
            'step': step,
            'cooperation_rate': society.get_cooperation_rate(),
            'agents': {}
        }
        
        for agent_id, agent in society.agents.items():
            agent_data = {
                'weights': agent.weights.tolist() if hasattr(agent.weights, 'tolist') else list(agent.weights),
                'state': agent._determine_state(agent.current_M) if hasattr(agent, 'current_M') else 'unknown'
            }
            
            # 人格
            if agent.valence_module:
                profile = agent.valence_module.get_preference_profile()
                agent_data['personality'] = {
                    'type': profile['dominant_preference'],
                    'weight': float(profile['dominant_weight']),
                    'entropy': float(profile['preference_entropy'])
                }
            
            # 信任网络
            if agent.other_module:
                agent_data['social'] = {
                    'known_agents': len(agent.other_module.other_models),
                    'avg_trust': np.mean([m.trust_score for m in agent.other_module.other_models.values()]) 
                                if agent.other_module.other_models else 0.0
                }
            
            # 规范
            if agent.norm_module:
                norm_summary = agent.norm_module.get_norm_summary()
                agent_data['norm'] = {
                    'type': norm_summary.get('convergence_type', 'unknown'),
                    'value': float(norm_summary.get('norm_value', 0)),
                    'violation_rate': float(norm_summary.get('violation_rate', 0))
                }
            
            checkpoint['agents'][agent_id] = agent_data
        
        return checkpoint
    
    def _analyze_convergence(self, history: Dict, society: MultiAgentSociety) -> Dict:
        """分析收敛模式"""
        analysis = {
            'cooperation_stability': {},
            'trust_stability': {},
            'norm_convergence_types': {}
        }
        
        # 合作率稳定性（后50%的方差）
        if history['cooperation_rates']:
            mid_point = len(history['cooperation_rates']) // 2
            late_rates = history['cooperation_rates'][mid_point:]
            analysis['cooperation_stability'] = {
                'late_mean': np.mean(late_rates),
                'late_std': np.std(late_rates),
                'stability_score': 1.0 - np.std(late_rates)  # 越稳定越接近1
            }
        
        # 信任稳定性
        if history['trust_evolution']:
            late_trust = history['trust_evolution'][-10:]  # 最后10个记录
            analysis['trust_stability'] = {
                'final_mean': np.mean([t['mean'] for t in late_trust]),
                'final_std': np.mean([t['std'] for t in late_trust])
            }
        
        # 规范收敛类型统计
        conv_types = {'strong_norm': 0, 'opportunistic': 0, 'norm_collapse': 0, 'transitional': 0}
        for agent in society.agents.values():
            if agent.norm_module:
                norm_summary = agent.norm_module.get_norm_summary()
                conv_type = norm_summary.get('convergence_type', 'unknown')
                if conv_type in conv_types:
                    conv_types[conv_type] += 1
        
        analysis['norm_convergence_types'] = conv_types
        
        return analysis
    
    def print_summary(self, results: Dict):
        """打印模拟摘要"""
        print("\n" + "="*70)
        print("LONG-TERM SIMULATION SUMMARY")
        print("="*70)
        
        config = results['config']
        print(f"\n📊 Configuration:")
        print(f"  Agents: {config['n_agents']}")
        print(f"  Steps: {config['n_steps']:,}")
        
        history = results['history']
        print(f"\n📈 Cooperation Evolution:")
        if history['cooperation_rates']:
            print(f"  Initial: {history['cooperation_rates'][0]:.2%}")
            print(f"  Final: {history['cooperation_rates'][-1]:.2%}")
            print(f"  Mean: {np.mean(history['cooperation_rates']):.2%}")
        
        print(f"\n🤝 Trust Evolution:")
        if history['trust_evolution']:
            print(f"  Initial: {history['trust_evolution'][0]['mean']:.4f}")
            print(f"  Final: {history['trust_evolution'][-1]['mean']:.4f}")
        
        print(f"\n⚖️  Norm Convergence Types:")
        conv_analysis = results['convergence_analysis']
        for conv_type, count in conv_analysis['norm_convergence_types'].items():
            print(f"  {conv_type}: {count}/{self.n_agents}")
        
        print(f"\n🎭 Personality Stability:")
        if history['personality_evolution']:
            first_dist = history['personality_evolution'][0]['distribution']
            last_dist = history['personality_evolution'][-1]['distribution']
            print(f"  Initial types: {len(first_dist)}")
            print(f"  Final types: {len(last_dist)}")
            print(f"  Types: {list(last_dist.keys())}")
        
        coop_stability = conv_analysis.get('cooperation_stability', {})
        if coop_stability:
            print(f"\n🎯 Stability Metrics:")
            print(f"  Cooperation stability: {coop_stability.get('stability_score', 0):.4f}")
            print(f"  Late-stage std: {coop_stability.get('late_std', 0):.4f}")
        
        print("\n" + "="*70)


# 主程序
if __name__ == "__main__":
    print("="*70)
    print("MOSS v3.0 Long-term Simulation (10,000 steps)")
    print("="*70)
    
    # 使用较小的步数进行测试
    simulator = LongTermSimulation(n_agents=10)
    
    # 先运行1000步测试
    results = simulator.run_long_term(
        n_steps=1000,  # 先用1000步测试
        checkpoint_dir='v3/experiments/long_term_checkpoints'
    )
    
    # 打印摘要
    simulator.print_summary(results)
    
    print("\n✓ Long-term simulation completed!")
    print("="*70)
