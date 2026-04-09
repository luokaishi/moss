"""
MOSS v3.0.0 - Parameter Sensitivity Analysis
=============================================

分析关键参数对系统行为的影响

Author: Cash
Date: 2026-03-19
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from social.multi_agent_society import MultiAgentSociety


class ParameterSensitivityAnalysis:
    """参数敏感性分析"""
    
    def __init__(self):
        self.results = {}
    
    def analyze_coherence_alpha(self, 
                               alpha_values: List[float] = [0.7, 0.8, 0.9, 0.95],
                               n_steps: int = 200) -> Dict:
        """
        分析Coherence alpha参数的影响
        
        alpha: EMA系数，越大参考身份更新越快
        """
        print("\nAnalyzing Coherence alpha...")
        results = {}
        
        for alpha in alpha_values:
            print(f"  Testing alpha={alpha}...")
            
            society = MultiAgentSociety(n_agents=8)
            
            # 设置所有agent的coherence alpha
            for agent in society.agents.values():
                if agent.coherence_module:
                    agent.coherence_module.alpha = alpha
            
            # 运行模拟
            society.run_simulation(n_steps=n_steps)
            
            # 记录结果
            analysis = society.analyze_society()
            results[alpha] = {
                'cooperation_rate': society.get_cooperation_rate(),
                'mean_coherence': np.mean([a.coherence_module.get_identity_stability() 
                                          for a in society.agents.values() 
                                          if a.coherence_module]),
                'convergence': analysis.get('society_convergence', {})
            }
        
        self.results['coherence_alpha'] = results
        return results
    
    def analyze_valence_gamma(self,
                             gamma_values: List[float] = [0.005, 0.01, 0.02, 0.05],
                             n_steps: int = 200) -> Dict:
        """
        分析Valence gamma参数的影响
        
        gamma: 偏好学习率，越大偏好调整越快
        """
        print("\nAnalyzing Valence gamma...")
        results = {}
        
        for gamma in gamma_values:
            print(f"  Testing gamma={gamma}...")
            
            society = MultiAgentSociety(n_agents=8)
            
            # 设置所有agent的valence gamma
            for agent in society.agents.values():
                if agent.valence_module:
                    agent.valence_module.gamma = gamma
            
            society.run_simulation(n_steps=n_steps)
            
            # 记录人格多样性
            personalities = []
            for agent in society.agents.values():
                if agent.valence_module:
                    profile = agent.valence_module.get_preference_profile()
                    personalities.append(profile['dominant_preference'])
            
            from collections import Counter
            personality_counts = Counter(personalities)
            
            results[gamma] = {
                'cooperation_rate': society.get_cooperation_rate(),
                'personality_diversity': len(personality_counts),
                'personality_entropy': -sum((c/len(personalities)) * np.log(c/len(personalities)) 
                                          for c in personality_counts.values()),
                'cooperation_rate': society.get_cooperation_rate()
            }
        
        self.results['valence_gamma'] = results
        return results
    
    def analyze_payoff_matrix(self,
                             defection_rewards: List[float] = [1.2, 1.5, 1.8, 2.0],
                             n_steps: int = 200) -> Dict:
        """
        分析收益矩阵的影响
        
        特别是背叛的诱惑力
        """
        print("\nAnalyzing payoff matrix (defection reward)...")
        results = {}
        
        for defection_reward in defection_rewards:
            print(f"  Testing defection_reward={defection_reward}...")
            
            society = MultiAgentSociety(
                n_agents=8,
                defection_reward=defection_reward
            )
            
            society.run_simulation(n_steps=n_steps)
            
            results[defection_reward] = {
                'cooperation_rate': society.get_cooperation_rate(),
                'temptation_ratio': defection_reward / 1.0,  # 背叛诱惑/合作收益
            }
        
        self.results['payoff_matrix'] = results
        return results
    
    def analyze_social_learning_rate(self,
                                   norm_lr_values: List[float] = [0.01, 0.03, 0.05, 0.1],
                                   n_steps: int = 200) -> Dict:
        """
        分析规范学习率的影响
        """
        print("\nAnalyzing Norm learning rate...")
        results = {}
        
        for norm_lr in norm_lr_values:
            print(f"  Testing norm_lr={norm_lr}...")
            
            society = MultiAgentSociety(n_agents=8)
            
            # 设置所有agent的norm学习率
            for agent in society.agents.values():
                if agent.norm_module:
                    agent.norm_module.norm_lr = norm_lr
            
            society.run_simulation(n_steps=n_steps)
            
            # 分析收敛类型
            analysis = society.analyze_society()
            conv_types = analysis.get('society_convergence', {})
            
            results[norm_lr] = {
                'cooperation_rate': society.get_cooperation_rate(),
                'strong_norm_ratio': conv_types.get('strong_norm', 0) / 8,
                'norm_collapse_ratio': conv_types.get('norm_collapse', 0) / 8,
            }
        
        self.results['norm_lr'] = results
        return results
    
    def visualize_sensitivity(self, save_path: str = None):
        """可视化敏感性分析结果"""
        if not self.results:
            print("No results to visualize. Run analysis first.")
            return
        
        n_params = len(self.results)
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        axes = axes.flatten()
        
        param_idx = 0
        
        # 1. Coherence alpha
        if 'coherence_alpha' in self.results:
            ax = axes[param_idx]
            data = self.results['coherence_alpha']
            alphas = list(data.keys())
            coop_rates = [data[a]['cooperation_rate'] for a in alphas]
            
            ax.plot(alphas, coop_rates, 'o-', linewidth=2, markersize=8, color='#3498db')
            ax.set_xlabel('Coherence Alpha (EMA coefficient)')
            ax.set_ylabel('Cooperation Rate')
            ax.set_title('Effect of Coherence Alpha')
            ax.grid(True, alpha=0.3)
            ax.set_ylim([0, 1.05])
            param_idx += 1
        
        # 2. Valence gamma
        if 'valence_gamma' in self.results:
            ax = axes[param_idx]
            data = self.results['valence_gamma']
            gammas = list(data.keys())
            diversities = [data[g]['personality_diversity'] for g in gammas]
            
            ax.bar(range(len(gammas)), diversities, color='#2ecc71', alpha=0.7)
            ax.set_xticks(range(len(gammas)))
            ax.set_xticklabels([f'{g:.3f}' for g in gammas], rotation=45)
            ax.set_xlabel('Valence Gamma (learning rate)')
            ax.set_ylabel('Personality Diversity')
            ax.set_title('Effect of Valence Gamma')
            ax.grid(True, alpha=0.3, axis='y')
            param_idx += 1
        
        # 3. Payoff matrix
        if 'payoff_matrix' in self.results:
            ax = axes[param_idx]
            data = self.results['payoff_matrix']
            rewards = list(data.keys())
            coop_rates = [data[r]['cooperation_rate'] for r in rewards]
            
            ax.plot(rewards, coop_rates, 'o-', linewidth=2, markersize=8, color='#e74c3c')
            ax.set_xlabel('Defection Reward')
            ax.set_ylabel('Cooperation Rate')
            ax.set_title('Effect of Defection Temptation')
            ax.grid(True, alpha=0.3)
            ax.set_ylim([0, 1.05])
            param_idx += 1
        
        # 4. Norm learning rate
        if 'norm_lr' in self.results:
            ax = axes[param_idx]
            data = self.results['norm_lr']
            lrs = list(data.keys())
            coop_rates = [data[lr]['cooperation_rate'] for lr in lrs]
            
            ax.plot(lrs, coop_rates, 'o-', linewidth=2, markersize=8, color='#9b59b6')
            ax.set_xlabel('Norm Learning Rate')
            ax.set_ylabel('Cooperation Rate')
            ax.set_title('Effect of Norm Learning Rate')
            ax.set_xscale('log')
            ax.grid(True, alpha=0.3)
            ax.set_ylim([0, 1.05])
        
        plt.suptitle('MOSS v3.0 - Parameter Sensitivity Analysis', 
                    fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"\nSaved: {save_path}")
        
        plt.close()
        return fig
    
    def print_summary(self):
        """打印分析摘要"""
        print("\n" + "="*70)
        print("PARAMETER SENSITIVITY ANALYSIS SUMMARY")
        print("="*70)
        
        for param_name, results in self.results.items():
            print(f"\n📊 {param_name.upper()}:")
            
            if param_name == 'coherence_alpha':
                best_alpha = max(results.items(), key=lambda x: x[1]['cooperation_rate'])
                print(f"  Best alpha: {best_alpha[0]} (cooperation: {best_alpha[1]['cooperation_rate']:.2%})")
            
            elif param_name == 'valence_gamma':
                best_gamma = max(results.items(), key=lambda x: x[1]['personality_diversity'])
                print(f"  Best gamma: {best_gamma[0]} (diversity: {best_gamma[1]['personality_diversity']} types)")
            
            elif param_name == 'payoff_matrix':
                print(f"  Cooperation decreases as defection reward increases:")
                for reward, data in sorted(results.items()):
                    print(f"    Reward={reward:.1f}: {data['cooperation_rate']:.2%}")
            
            elif param_name == 'norm_lr':
                best_lr = max(results.items(), key=lambda x: x[1]['cooperation_rate'])
                print(f"  Best norm_lr: {best_lr[0]} (cooperation: {best_lr[1]['cooperation_rate']:.2%})")


# 主程序
if __name__ == "__main__":
    print("="*70)
    print("MOSS v3.0 Parameter Sensitivity Analysis")
    print("="*70)
    
    analysis = ParameterSensitivityAnalysis()
    
    # 运行各项分析
    # analysis.analyze_coherence_alpha(n_steps=100)
    # analysis.analyze_valence_gamma(n_steps=100)
    # analysis.analyze_payoff_matrix(n_steps=100)
    analysis.analyze_social_learning_rate(n_steps=100)
    
    # 可视化
    # analysis.visualize_sensitivity('v3/experiments/figures/param_sensitivity.png')
    
    # 打印摘要
    analysis.print_summary()
    
    print("\n✓ Sensitivity analysis completed!")
    print("="*70)
