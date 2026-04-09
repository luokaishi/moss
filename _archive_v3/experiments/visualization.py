"""
MOSS v3.0.0 - Comprehensive Visualization
=========================================

生成全面的可视化图表，用于论文展示

Author: Cash
Date: 2026-03-19
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.agent_8d import MOSSv3Agent8D
from social.multi_agent_society import MultiAgentSociety


class MOSSVisualizer:
    """MOSS可视化工具"""
    
    def __init__(self, figsize=(16, 12)):
        self.figsize = figsize
        
    def plot_8d_evolution(self, agent: MOSSv3Agent8D, save_path: str = None):
        """
        绘制8维目标值演化图
        """
        if not agent.history:
            print("No history data available")
            return
        
        fig, axes = plt.subplots(2, 4, figsize=self.figsize)
        axes = axes.flatten()
        
        steps = range(len(agent.history))
        
        # 8个维度的数据
        dimensions = [
            ('survival', 'D1: Survival', '#e74c3c'),
            ('curiosity', 'D2: Curiosity', '#3498db'),
            ('influence', 'D3: Influence', '#2ecc71'),
            ('optimization', 'D4: Optimization', '#9b59b6'),
            ('coherence', 'D5: Coherence', '#f39c12'),
            ('valence', 'D6: Valence', '#1abc9c'),
            ('other', 'D7: Other', '#e67e22'),
            ('norm', 'D8: Norm', '#34495e')
        ]
        
        for idx, (attr, title, color) in enumerate(dimensions):
            ax = axes[idx]
            values = [getattr(state, attr) for state in agent.history]
            
            ax.plot(steps, values, color=color, linewidth=2)
            ax.set_title(title, fontsize=12, fontweight='bold')
            ax.set_xlabel('Step')
            ax.set_ylabel('Value')
            ax.grid(True, alpha=0.3)
            
            # 添加均值线
            mean_val = np.mean(values)
            ax.axhline(y=mean_val, color='red', linestyle='--', alpha=0.5, 
                      label=f'Mean: {mean_val:.3f}')
            ax.legend(fontsize=8)
        
        plt.suptitle('MOSS v3.0 - 8D Objective Evolution', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved: {save_path}")
        
        plt.close()
        return fig
    
    def plot_personality_distribution(self, society: MultiAgentSociety, save_path: str = None):
        """
        绘制人格类型分布图
        """
        # 收集所有agent的人格类型
        personality_types = []
        for agent in society.agents.values():
            if agent.valence_module:
                profile = agent.valence_module.get_preference_profile()
                p_type = profile['dominant_preference']
                personality_types.append(p_type)
        
        if not personality_types:
            print("No personality data available")
            return
        
        # 统计
        from collections import Counter
        type_counts = Counter(personality_types)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # 饼图
        colors = ['#e74c3c', '#3498db', '#2ecc71', '#9b59b6', '#f39c12']
        wedges, texts, autotexts = ax1.pie(
            type_counts.values(),
            labels=type_counts.keys(),
            autopct='%1.1f%%',
            colors=colors[:len(type_counts)],
            startangle=90
        )
        ax1.set_title('Personality Type Distribution', fontsize=14, fontweight='bold')
        
        # 柱状图
        bars = ax2.bar(type_counts.keys(), type_counts.values(), 
                      color=colors[:len(type_counts)], alpha=0.8)
        ax2.set_title('Personality Type Counts', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Count')
        ax2.grid(True, alpha=0.3, axis='y')
        
        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        plt.suptitle('MOSS v3.0 - Personality Analysis (D6 Valence)', 
                    fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved: {save_path}")
        
        plt.close()
        return fig
    
    def plot_trust_network(self, society: MultiAgentSociety, save_path: str = None):
        """
        绘制信任网络图
        """
        import networkx as nx
        
        G = nx.Graph()
        
        # 添加节点
        for agent_id in society.agents.keys():
            G.add_node(agent_id)
        
        # 添加边（信任关系）
        for agent_id, agent in society.agents.items():
            if agent.other_module:
                for other_id, model in agent.other_module.other_models.items():
                    if other_id in society.agents:
                        # 双向信任的平均值
                        trust = model.trust_score
                        if trust > 0.3:  # 只显示有意义的信任关系
                            G.add_edge(agent_id, other_id, weight=trust)
        
        fig, ax = plt.subplots(figsize=(12, 12))
        
        # 布局
        pos = nx.spring_layout(G, k=3, iterations=50)
        
        # 绘制节点
        node_colors = []
        for node in G.nodes():
            agent = society.agents[node]
            if agent.valence_module:
                profile = agent.valence_module.get_preference_profile()
                p_type = profile['dominant_preference']
                color_map = {
                    'Survival': '#e74c3c',
                    'Curiosity': '#3498db',
                    'Influence': '#2ecc71',
                    'Optimization': '#9b59b6'
                }
                node_colors.append(color_map.get(p_type, '#95a5a6'))
            else:
                node_colors.append('#95a5a6')
        
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, 
                              node_size=2000, alpha=0.9, ax=ax)
        
        # 绘制边
        edges = G.edges()
        weights = [G[u][v]['weight'] for u, v in edges]
        
        nx.draw_networkx_edges(G, pos, width=[w*3 for w in weights],
                              alpha=0.5, edge_color='gray', ax=ax)
        
        # 绘制标签
        nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold', ax=ax)
        
        # 添加图例
        legend_elements = [
            mpatches.Patch(color='#e74c3c', label='Survival'),
            mpatches.Patch(color='#3498db', label='Curiosity'),
            mpatches.Patch(color='#2ecc71', label='Influence'),
            mpatches.Patch(color='#9b59b6', label='Optimization')
        ]
        ax.legend(handles=legend_elements, loc='upper left')
        
        ax.set_title('MOSS v3.0 - Trust Network (D7 Other)\nNode color = Personality, Edge width = Trust',
                    fontsize=14, fontweight='bold')
        ax.axis('off')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved: {save_path}")
        
        plt.close()
        return fig
    
    def plot_norm_convergence(self, society: MultiAgentSociety, save_path: str = None):
        """
        绘制规范收敛过程
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # 1. 规范值演化
        ax1 = axes[0, 0]
        norm_values = []
        for agent in society.agents.values():
            if agent.norm_module:
                # 从历史中重建（简化版本）
                pass
        
        # 2. 收敛类型分布
        ax2 = axes[0, 1]
        analysis = society.analyze_society()
        if 'society_convergence' in analysis:
            conv_types = analysis['society_convergence']
            bars = ax2.bar(conv_types.keys(), conv_types.values(), 
                          color=['#2ecc71', '#f39c12', '#e74c3c', '#3498db'])
            ax2.set_title('Convergence Type Distribution (D8 Norm)', 
                         fontsize=12, fontweight='bold')
            ax2.set_ylabel('Count')
            
            for bar in bars:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}',
                        ha='center', va='bottom', fontsize=10)
        
        # 3. 规范代价热力图
        ax3 = axes[1, 0]
        norm_costs = []
        agent_ids = []
        for agent_id, agent in society.agents.items():
            if agent.norm_module:
                costs = agent.norm_module.norm_costs
                if costs:
                    norm_costs.append(list(costs.values()))
                    agent_ids.append(agent_id)
        
        if norm_costs:
            im = ax3.imshow(norm_costs, cmap='RdYlGn_r', aspect='auto')
            ax3.set_title('Norm Costs by Agent', fontsize=12, fontweight='bold')
            ax3.set_xlabel('Action Type')
            ax3.set_ylabel('Agent')
            ax3.set_yticks(range(len(agent_ids)))
            ax3.set_yticklabels(agent_ids, fontsize=8)
            plt.colorbar(im, ax=ax3)
        
        # 4. 声誉分布
        ax4 = axes[1, 1]
        reputations = []
        for agent in society.agents.values():
            if agent.norm_module and agent.norm_module.reputation:
                reputations.extend(list(agent.norm_module.reputation.values()))
        
        if reputations:
            ax4.hist(reputations, bins=20, color='#3498db', alpha=0.7, edgecolor='black')
            ax4.set_title('Reputation Score Distribution', fontsize=12, fontweight='bold')
            ax4.set_xlabel('Reputation Score')
            ax4.set_ylabel('Frequency')
            ax4.axvline(x=np.mean(reputations), color='red', linestyle='--', 
                       label=f'Mean: {np.mean(reputations):.3f}')
            ax4.legend()
        
        plt.suptitle('MOSS v3.0 - Norm Analysis (D8 Norm)', 
                    fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved: {save_path}")
        
        plt.close()
        return fig
    
    def generate_all_visualizations(self, output_dir: str = 'v3/experiments/figures'):
        """生成所有可视化图表"""
        os.makedirs(output_dir, exist_ok=True)
        
        print("Generating MOSS v3.0 visualizations...")
        
        # 创建单个agent进行8维演化可视化
        print("\n1. Creating 8D evolution plot...")
        agent = MOSSv3Agent8D(agent_id="viz_agent", enable_social=True)
        for _ in range(200):
            agent.step()
        self.plot_8d_evolution(agent, os.path.join(output_dir, '8d_evolution.png'))
        
        # 创建社会进行其他可视化
        print("2. Creating multi-agent society...")
        society = MultiAgentSociety(n_agents=10)
        society.run_simulation(n_steps=100)
        
        print("3. Generating personality distribution...")
        self.plot_personality_distribution(society, 
                                          os.path.join(output_dir, 'personality_distribution.png'))
        
        print("4. Generating trust network...")
        self.plot_trust_network(society, 
                               os.path.join(output_dir, 'trust_network.png'))
        
        print("5. Generating norm analysis...")
        self.plot_norm_convergence(society, 
                                  os.path.join(output_dir, 'norm_convergence.png'))
        
        print(f"\n✓ All visualizations saved to {output_dir}/")


# 主程序
if __name__ == "__main__":
    print("="*70)
    print("MOSS v3.0 Visualization Generator")
    print("="*70)
    
    viz = MOSSVisualizer()
    viz.generate_all_visualizations()
    
    print("\n✓ Visualization generation completed!")
    print("="*70)
