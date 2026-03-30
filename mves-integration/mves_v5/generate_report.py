#!/usr/bin/env python3
"""
MVES v5 - 生成实验报告（文本模式）

从检查点数据生成可视化报告和统计分析
"""

import json
import gzip
from pathlib import Path
from datetime import datetime


def load_checkpoints(checkpoint_dir: str = "checkpoints"):
    """加载所有检查点数据"""
    checkpoints = []
    checkpoint_files = sorted(Path(checkpoint_dir).glob("checkpoint_gen*.json.gz"))
    
    for file in checkpoint_files:
        try:
            with gzip.open(file, 'rt') as f:
                data = json.load(f)
                checkpoints.append({
                    'file': file.name,
                    'generation': data.get('generation', 0),
                    'population_size': data.get('population_size', 0),
                    'history': data.get('history', {}),
                    'config': data.get('config', {}),
                    'top_agents': data.get('top_agents', [])
                })
        except Exception as e:
            print(f"读取 {file} 失败：{e}")
    
    return checkpoints


def generate_report(checkpoints, output_file: str = "EXPERIMENT_VISUALIZATION_REPORT.md"):
    """生成实验报告"""
    report = []
    report.append("# MVES v5 实验可视化报告")
    report.append(f"\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"\n**检查点数量**: {len(checkpoints)}\n")
    
    # 演化趋势
    report.append("## 📈 演化趋势\n")
    report.append("### 代数进展")
    report.append("\n```")
    report.append(f"{'代数':<8} {'种群大小':<12} {'平均适应度':<15} {'最佳适应度':<15}")
    report.append("-" * 50)
    
    for cp in checkpoints:
        gen = cp['generation']
        pop_size = cp['population_size']
        history = cp['history']
        # history 是列表，取最后一个
        if isinstance(history, list) and history:
            last_hist = history[-1]
            avg_fitness = last_hist.get('avg_fitness', 0)
            best_fitness = last_hist.get('best_fitness', 0)
        else:
            avg_fitness = 0
            best_fitness = 0
        
        report.append(f"{gen:<8} {pop_size:<12} {avg_fitness:<15.3f} {best_fitness:<15.3f}")
    
    report.append("```\n")
    
    # 文本演化曲线
    report.append("### 适应度演化曲线 (文本可视化)\n")
    
    all_fitness = []
    all_gens = []
    for cp in checkpoints:
        gen = cp['generation']
        history = cp['history']
        if isinstance(history, list) and history:
            avg_fitness = history[-1].get('avg_fitness', 0)
            all_gens.append(gen)
            all_fitness.append(avg_fitness)
    
    if all_fitness:
        max_fit = max(all_fitness)
        min_fit = min(all_fitness)
        range_fit = max_fit - min_fit if max_fit != min_fit else 1
        
        report.append("```\n")
        for gen, fitness in zip(all_gens, all_fitness):
            bar_len = int((fitness - min_fit) / range_fit * 50)
            bar = "█" * bar_len
            marker = "← MAX" if fitness == max_fit else ""
            report.append(f"Gen {gen:3d}: {bar} {fitness:.3f} {marker}")
        report.append("```\n")
    
    # 顶级智能体分析
    report.append("\n## 🏆 顶级智能体分析\n")
    
    for cp in checkpoints[-3:]:  # 最近 3 个检查点
        report.append(f"### 第 {cp['generation']} 代\n")
        
        top_agents = cp.get('top_agents', [])
        if top_agents:
            for i, agent in enumerate(top_agents[:3], 1):
                report.append(f"**Top {i}**: {agent.get('id', 'unknown')}")
                report.append(f"- 适应度：{agent.get('fitness', 0):.3f}")
                report.append(f"- 能力：{', '.join(agent.get('abilities', [])[:5])}")
                if 'mutations' in agent:
                    report.append(f"- 突变：{agent['mutations'][:100]}...")
                report.append("")
    
    # 统计摘要
    report.append("\n## 📊 统计摘要\n")
    
    if all_fitness:
        report.append(f"- **初始适应度**: {all_fitness[0]:.3f}")
        report.append(f"- **最终适应度**: {all_fitness[-1]:.3f}")
        report.append(f"- **最大适应度**: {max(all_fitness):.3f}")
        report.append(f"- **提升幅度**: {((all_fitness[-1] / all_fitness[0]) - 1) * 100:.1f}%" if all_fitness[0] > 0 else "N/A")
        report.append(f"- **平均适应度**: {sum(all_fitness) / len(all_fitness):.3f}")
    
    # 保存报告
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"✓ 报告已生成：{output_file}")
    return output_file


if __name__ == "__main__":
    checkpoints = load_checkpoints()
    if checkpoints:
        generate_report(checkpoints)
        print(f"\n共加载 {len(checkpoints)} 个检查点")
    else:
        print("未找到检查点数据")
