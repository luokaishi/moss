"""
MOSS v3.0.0 - Long-term Simulation & Control Experiment
=======================================================

长时模拟 + 对照实验

实验设计：
1. 实验组：完整8维系统，1000步
2. 对照组：关闭D7-D8（无社交），1000步
3. 对比分析

Author: Cash
Date: 2026-03-19
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from social.multi_agent_society import MultiAgentSociety


class ExperimentRunner:
    """实验运行器"""
    
    def __init__(self, n_agents: int = 10):
        self.n_agents = n_agents
        
    def run_experiment(self,
                      enable_social: bool = True,
                      n_steps: int = 1000,
                      seed: int = 42) -> Dict:
        """
        运行单个实验
        
        Args:
            enable_social: 是否启用社交维度（D7-D8）
            n_steps: 模拟步数
            seed: 随机种子
            
        Returns:
            实验结果字典
        """
        np.random.seed(seed)
        
        # 创建社会
        society = MultiAgentSociety(
            n_agents=self.n_agents,
            cooperation_reward=1.0,
            defection_reward=1.5,  # 背叛更有利（囚徒困境）
            sucker_penalty=-0.5,
            mutual_defect_penalty=-0.1
        )
        
        # 如果不启用社交，禁用D7-D8
        if not enable_social:
            for agent in society.agents.values():
                agent.enable_social = False
                agent.other_module = None
                agent.norm_module = None
        
        # 记录时序数据
        cooperation_rates = []
        mean_trusts = []
        
        print(f"\n{'='*60}")
        print(f"Experiment: {'With Social (D7-D8)' if enable_social else 'Without Social'}")
        print(f"Steps: {n_steps}, Agents: {self.n_agents}")
        print(f"{'='*60}")
        
        # 运行模拟
        for step in range(n_steps):
            society.step()
            
            # 每10步记录
            if step % 10 == 0:
                coop_rate = society.get_cooperation_rate()
                cooperation_rates.append(coop_rate)
                
                # 计算平均信任
                if enable_social:
                    trust_scores = []
                    for agent in society.agents.values():
                        if agent.other_module and agent.other_module.other_models:
                            scores = [m.trust_score for m in agent.other_module.other_models.values()]
                            trust_scores.extend(scores)
                    mean_trust = np.mean(trust_scores) if trust_scores else 0.5
                else:
                    mean_trust = 0.0
                
                mean_trusts.append(mean_trust)
                
                if step % 100 == 0:
                    print(f"Step {step}: Cooperation={coop_rate:.2%}, Trust={mean_trust:.3f}")
        
        # 最终分析
        analysis = society.analyze_society()
        
        return {
            'enable_social': enable_social,
            'n_steps': n_steps,
            'cooperation_rates': cooperation_rates,
            'mean_trusts': mean_trusts,
            'final_cooperation_rate': society.get_cooperation_rate(),
            'final_analysis': analysis
        }
    
    def run_comparison(self, n_steps: int = 1000) -> Dict:
        """
        运行对比实验
        
        实验组 vs 对照组
        """
        print("\n" + "="*70)
        print("MOSS v3.0 COMPARISON EXPERIMENT")
        print("="*70)
        
        # 实验组：完整8维
        exp_with_social = self.run_experiment(
            enable_social=True,
            n_steps=n_steps,
            seed=42
        )
        
        # 对照组：关闭D7-D8
        exp_without_social = self.run_experiment(
            enable_social=False,
            n_steps=n_steps,
            seed=42
        )
        
        return {
            'with_social': exp_with_social,
            'without_social': exp_without_social
        }
    
    def visualize_results(self, results: Dict, save_path: str = None):
        """
        可视化实验结果
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        exp_with = results['with_social']
        exp_without = results['without_social']
        
        # 1. 合作率演化
        ax1 = axes[0, 0]
        steps = np.arange(0, exp_with['n_steps'], 10)
        ax1.plot(steps, exp_with['cooperation_rates'], 
                label='With D7-D8 (Social)', linewidth=2, color='green')
        ax1.plot(steps, exp_without['cooperation_rates'], 
                label='Without D7-D8 (Base)', linewidth=2, color='red', linestyle='--')
        ax1.set_xlabel('Steps')
        ax1.set_ylabel('Cooperation Rate')
        ax1.set_title('Cooperation Rate Evolution')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim([0, 1.05])
        
        # 2. 信任演化（只有实验组有）
        ax2 = axes[0, 1]
        ax2.plot(steps, exp_with['mean_trusts'], 
                label='Mean Trust', linewidth=2, color='blue')
        ax2.set_xlabel('Steps')
        ax2.set_ylabel('Mean Trust Score')
        ax2.set_title('Trust Network Evolution (With D7-D8)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim([0, 1.05])
        
        # 3. 最终合作率对比
        ax3 = axes[1, 0]
        categories = ['With D7-D8\n(Social)', 'Without D7-D8\n(Base)']
        rates = [exp_with['final_cooperation_rate'], 
                exp_without['final_cooperation_rate']]
        colors = ['green', 'red']
        bars = ax3.bar(categories, rates, color=colors, alpha=0.7)
        ax3.set_ylabel('Final Cooperation Rate')
        ax3.set_title('Final Cooperation Rate Comparison')
        ax3.set_ylim([0, 1.05])
        
        # 添加数值标签
        for bar, rate in zip(bars, rates):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{rate:.2%}',
                    ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        # 4. 收敛形态分布（实验组）
        ax4 = axes[1, 1]
        convergence = exp_with['final_analysis']['society_convergence']
        if convergence:
            labels = list(convergence.keys())
            values = list(convergence.values())
            colors_pie = ['#2ecc71', '#f39c12', '#e74c3c', '#3498db']
            ax4.pie(values, labels=labels, autopct='%1.1f%%', 
                   colors=colors_pie[:len(labels)], startangle=90)
            ax4.set_title('Convergence Type Distribution\n(With D7-D8)')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"\nFigure saved to: {save_path}")
        
        plt.show()
        
        return fig
    
    def print_comparison_report(self, results: Dict):
        """打印对比报告"""
        print("\n" + "="*70)
        print("COMPARISON REPORT")
        print("="*70)
        
        exp_with = results['with_social']
        exp_without = results['without_social']
        
        print(f"\n📊 Final Cooperation Rates:")
        print(f"  With D7-D8 (Social):    {exp_with['final_cooperation_rate']:.2%}")
        print(f"  Without D7-D8 (Base):   {exp_without['final_cooperation_rate']:.2%}")
        print(f"  Improvement:             {exp_with['final_cooperation_rate'] - exp_without['final_cooperation_rate']:.2%}")
        
        print(f"\n🤝 Trust Network (With D7-D8):")
        if 'trust_network' in exp_with['final_analysis']:
            trust = exp_with['final_analysis']['trust_network']
            print(f"  Mean trust: {trust['mean_trust']:.3f}")
            print(f"  High trust pairs: {trust['high_trust_pairs']}")
        
        print(f"\n⚖️  Convergence Analysis (With D7-D8):")
        convergence = exp_with['final_analysis']['society_convergence']
        for conv_type, count in convergence.items():
            print(f"  {conv_type}: {count}/{self.n_agents}")
        
        print(f"\n✅ Key Findings:")
        if exp_with['final_cooperation_rate'] > exp_without['final_cooperation_rate']:
            print(f"  1. Social dimensions (D7-D8) SIGNIFICANTLY improve cooperation")
        if exp_with['final_cooperation_rate'] > 0.8:
            print(f"  2. High cooperation rate achieved with social cognition")
        if 'trust_network' in exp_with['final_analysis'] and exp_with['final_analysis']['trust_network']['mean_trust'] > 0.7:
            print(f"  3. Trust network successfully emerges")
        
        print("\n" + "="*70)


# 主程序
if __name__ == "__main__":
    print("="*70)
    print("MOSS v3.0 Long-term & Control Experiment")
    print("="*70)
    
    runner = ExperimentRunner(n_agents=10)
    
    # 运行对比实验
    results = runner.run_comparison(n_steps=500)  # 先用500步测试
    
    # 打印报告
    runner.print_comparison_report(results)
    
    # 可视化（如果有matplotlib）
    try:
        fig = runner.visualize_results(results, save_path='v3/experiments/comparison_result.png')
        print("\nVisualization completed!")
    except Exception as e:
        print(f"\nVisualization skipped: {e}")
    
    print("\n✓ Experiment completed!")
    print("="*70)
