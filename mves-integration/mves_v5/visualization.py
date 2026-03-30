#!/usr/bin/env python3
"""
MVES v5 - 数据可视化模块

功能:
- 适应度演化曲线
- 种群多样性热力图
- 能力分布饼图
- 代际对比图
"""

import json
import os
from pathlib import Path
from datetime import datetime

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.colors import LinearSegmentedColormap
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("警告：matplotlib 未安装，使用文本模式输出")


class MetricsVisualizer:
    """指标可视化器"""
    
    def __init__(self, checkpoint_dir: str, output_dir: str = "plots"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        if not HAS_MATPLOTLIB:
            print("使用文本模式生成报告")
    
    def load_experiment_data(self) -> dict:
        """加载实验数据"""
        report_path = self.checkpoint_dir / "experiment_100gen_report.json"
        if report_path.exists():
            with open(report_path, 'r') as f:
                return json.load(f)
        return {}
    
    def plot_fitness_evolution(self, generations: list, fitness_scores: list):
        """绘制适应度演化曲线"""
        if not HAS_MATPLOTLIB:
            self._text_fitness_evolution(generations, fitness_scores)
            return
        
        plt.figure(figsize=(12, 6))
        plt.plot(generations, fitness_scores, 'b-o', linewidth=2, markersize=4)
        plt.xlabel('Generation')
        plt.ylabel('Fitness Score')
        plt.title('MVES v5 - Fitness Evolution Over Generations')
        plt.grid(True, alpha=0.3)
        
        # 标注关键点
        max_idx = fitness_scores.index(max(fitness_scores))
        plt.annotate(f'Max: {fitness_scores[max_idx]:.2f}', 
                    xy=(generations[max_idx], fitness_scores[max_idx]),
                    xytext=(generations[max_idx]+5, fitness_scores[max_idx]+0.5),
                    arrowprops=dict(arrowstyle='->', color='red'))
        
        plt.savefig(self.output_dir / 'fitness_evolution.png', dpi=150, bbox_inches='tight')
        plt.close()
        print(f"✓ 适应度演化图已保存：{self.output_dir / 'fitness_evolution.png'}")
    
    def _text_fitness_evolution(self, generations: list, fitness_scores: list):
        """文本模式输出适应度演化"""
        print("\n" + "="*60)
        print("适应度演化曲线 (文本模式)")
        print("="*60)
        
        max_score = max(fitness_scores)
        min_score = min(fitness_scores)
        range_score = max_score - min_score if max_score != min_score else 1
        
        for i, (gen, score) in enumerate(zip(generations, fitness_scores)):
            bar_len = int((score - min_score) / range_score * 40)
            bar = "█" * bar_len
            marker = "← MAX" if score == max_score else ""
            print(f"Gen {gen:3d}: {bar} {score:.2f} {marker}")
        
        print("="*60 + "\n")
    
    def plot_population_diversity(self, gen_data: dict):
        """绘制种群多样性分析图"""
        if not HAS_MATPLOTLIB:
            self._text_diversity(gen_data)
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # 1. 能力分布
        if 'abilities' in gen_data:
            abilities = gen_data['abilities']
            ability_names = list(abilities.keys())
            ability_counts = list(abilities.values())
            
            axes[0, 0].bar(ability_names, ability_counts, color='steelblue')
            axes[0, 0].set_xlabel('Ability Type')
            axes[0, 0].set_ylabel('Count')
            axes[0, 0].set_title('Ability Distribution')
            axes[0, 0].tick_params(axis='x', rotation=45)
        
        # 2. 健康度分布
        if 'health_distribution' in gen_data:
            health_dist = gen_data['health_distribution']
            axes[0, 1].pie(health_dist.values(), labels=health_dist.keys(), autopct='%1.1f%%')
            axes[0, 1].set_title('Health Distribution')
        
        # 3. 种群统计
        if 'population_stats' in gen_data:
            stats = gen_data['population_stats']
            metrics = ['avg_fitness', 'diversity', 'health']
            values = [stats.get(m, 0) for m in metrics]
            
            axes[1, 0].bar(metrics, values, color=['coral', 'lightgreen', 'skyblue'])
            axes[1, 0].set_ylabel('Score')
            axes[1, 0].set_title('Population Statistics')
            axes[1, 0].set_ylim(0, 1.5)
        
        # 4. 代际对比
        if 'generation' in gen_data:
            axes[1, 1].text(0.5, 0.5, f"Generation {gen_data['generation']}\n", 
                          ha='center', va='center', fontsize=16, fontweight='bold')
            axes[1, 1].axis('off')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'population_analysis.png', dpi=150, bbox_inches='tight')
        plt.close()
        print(f"✓ 种群分析图已保存：{self.output_dir / 'population_analysis.png'}")
    
    def _text_diversity(self, gen_data: dict):
        """文本模式输出多样性分析"""
        print("\n" + "="*60)
        print("种群多样性分析 (文本模式)")
        print("="*60)
        
        if 'abilities' in gen_data:
            print("\n能力分布:")
            for ability, count in gen_data['abilities'].items():
                bar = "█" * min(count, 30)
                print(f"  {ability:15s}: {bar} ({count})")
        
        if 'population_stats' in gen_data:
            stats = gen_data['population_stats']
            print(f"\n种群统计:")
            print(f"  平均适应度：{stats.get('avg_fitness', 0):.3f}")
            print(f"  多样性：  {stats.get('diversity', 0):.3f}")
            print(f"  健康度：  {stats.get('health', 0):.3f}")
        
        print("="*60 + "\n")
    
    def generate_summary_report(self):
        """生成汇总报告"""
        data = self.load_experiment_data()
        
        report = []
        report.append("# MVES v5 实验可视化报告")
        report.append(f"\n生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"\n检查点目录：{self.checkpoint_dir}")
        
        if data:
            report.append("\n## 关键指标")
            if 'generations' in data:
                report.append(f"- 总代数：{len(data['generations'])}")
            if 'final_fitness' in data:
                report.append(f"- 最终适应度：{data['final_fitness']:.2f}")
            if 'improvement' in data:
                report.append(f"- 提升幅度：{data['improvement']}%")
        
        report_path = self.output_dir / 'SUMMARY.md'
        with open(report_path, 'w') as f:
            f.write('\n'.join(report))
        
        print(f"✓ 汇总报告已保存：{report_path}")
        return report_path


def create_all_visualizations(checkpoint_dir: str = "checkpoints"):
    """创建所有可视化图表"""
    visualizer = MetricsVisualizer(checkpoint_dir)
    
    # 加载实验数据
    data = visualizer.load_experiment_data()
    
    if not data:
        print("未找到实验数据，跳过可视化")
        return
    
    # 生成图表
    if 'generations' in data and 'fitness_scores' in data:
        visualizer.plot_fitness_evolution(data['generations'], data['fitness_scores'])
    
    # 加载最新检查点数据
    latest_gen = data.get('generations', [])[-1] if data.get('generations') else 100
    checkpoint_file = Path(checkpoint_dir) / f"gen{latest_gen}.json"
    
    if checkpoint_file.exists():
        with open(checkpoint_file, 'r') as f:
            gen_data = json.load(f)
        visualizer.plot_population_diversity(gen_data)
    
    # 生成汇总报告
    visualizer.generate_summary_report()
    
    print("\n✓ 所有可视化完成！")


if __name__ == "__main__":
    import sys
    
    checkpoint_dir = sys.argv[1] if len(sys.argv) > 1 else "checkpoints"
    create_all_visualizations(checkpoint_dir)
