#!/usr/bin/env python3
"""
Phase 4a - 数据提取与清洗

从检查点提取关键指标，生成标准化数据集
"""

import json
import gzip
import csv
from pathlib import Path
from datetime import datetime


def load_all_checkpoints(checkpoint_dir: str = "mves_v5/checkpoints"):
    """加载所有检查点数据"""
    checkpoints = []
    checkpoint_files = sorted(Path(checkpoint_dir).glob("checkpoint_gen*.json.gz"))
    
    for file in checkpoint_files:
        try:
            with gzip.open(file, 'rt') as f:
                data = json.load(f)
                
            # 提取关键指标
            gen = data.get('generation', 0)
            history = data.get('history', [])
            
            # 获取该代指标
            if isinstance(history, list) and history:
                last_hist = history[-1]
                avg_fitness = last_hist.get('avg_fitness', 0)
                best_fitness = last_hist.get('best_fitness', 0)
            else:
                avg_fitness = 0
                best_fitness = 0
            
            checkpoints.append({
                'file': file.name,
                'generation': gen,
                'population_size': data.get('population_size', 0),
                'avg_fitness': avg_fitness,
                'best_fitness': best_fitness,
                'diversity': data.get('diversity', 0),
                'complexity': data.get('complexity', 0),
                'health_score': data.get('population', {}).get('health_score', 0),
                'avg_energy': data.get('population', {}).get('avg_energy', 0),
                'capability_expansion': data.get('capability_expansion', 0),
                'novel_capabilities': data.get('novel_capabilities', 0),
                'timestamp': file.stat().st_mtime
            })
            
        except Exception as e:
            print(f"读取 {file} 失败：{e}")
    
    # 按代数排序
    checkpoints.sort(key=lambda x: x['generation'])
    return checkpoints


def generate_summary(checkpoints):
    """生成数据摘要"""
    if not checkpoints:
        return {}
    
    generations = [c['generation'] for c in checkpoints]
    fitness_scores = [c['avg_fitness'] for c in checkpoints]
    
    summary = {
        'total_checkpoints': len(checkpoints),
        'generation_range': {
            'min': min(generations),
            'max': max(generations)
        },
        'fitness_stats': {
            'initial': fitness_scores[0] if fitness_scores else 0,
            'final': fitness_scores[-1] if fitness_scores else 0,
            'max': max(fitness_scores) if fitness_scores else 0,
            'min': min(fitness_scores) if fitness_scores else 0,
            'avg': sum(fitness_scores) / len(fitness_scores) if fitness_scores else 0,
            'improvement_rate': ((fitness_scores[-1] / fitness_scores[0]) - 1) * 100 if fitness_scores and fitness_scores[0] > 0 else 0
        },
        'population_stats': {
            'avg_size': sum(c['population_size'] for c in checkpoints) / len(checkpoints),
            'avg_health': sum(c['health_score'] for c in checkpoints) / len(checkpoints),
            'avg_energy': sum(c['avg_energy'] for c in checkpoints) / len(checkpoints)
        },
        'diversity_stats': {
            'avg': sum(c['diversity'] for c in checkpoints) / len(checkpoints) if checkpoints else 0,
            'final': checkpoints[-1]['diversity'] if checkpoints else 0
        },
        'extraction_timestamp': datetime.now().isoformat()
    }
    
    return summary


def save_to_csv(checkpoints, output_file: str = "analysis/dataset_clean.csv"):
    """保存为 CSV 格式"""
    if not checkpoints:
        return
    
    Path(output_file).parent.mkdir(exist_ok=True)
    
    fieldnames = [
        'generation', 'population_size', 'avg_fitness', 'best_fitness',
        'diversity', 'complexity', 'health_score', 'avg_energy',
        'capability_expansion', 'novel_capabilities'
    ]
    
    # 移除不需要的字段
    clean_checkpoints = [{k: v for k, v in c.items() if k in fieldnames} for c in checkpoints]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(clean_checkpoints)
    
    print(f"✓ CSV 数据已保存：{output_file}")


def save_summary(summary, output_file: str = "analysis/dataset_summary.json"):
    """保存摘要"""
    Path(output_file).parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"✓ 数据摘要已保存：{output_file}")


def print_summary_table(summary):
    """打印摘要表格"""
    print("\n" + "="*60)
    print("Phase 4a - 数据提取完成")
    print("="*60)
    
    print(f"\n检查点总数：{summary.get('total_checkpoints', 0)}")
    print(f"代数范围：{summary['generation_range']['min']} - {summary['generation_range']['max']}")
    
    fitness = summary.get('fitness_stats', {})
    print(f"\n适应度统计:")
    print(f"  初始值：{fitness.get('initial', 0):.4f}")
    print(f"  最终值：{fitness.get('final', 0):.4f}")
    print(f"  最大值：{fitness.get('max', 0):.4f}")
    print(f"  提升率：{fitness.get('improvement_rate', 0):.1f}%")
    
    pop_stats = summary.get('population_stats', {})
    print(f"\n种群统计:")
    print(f"  平均大小：{pop_stats.get('avg_size', 0):.1f}")
    print(f"  平均健康：{pop_stats.get('avg_health', 0):.3f}")
    print(f"  平均能量：{pop_stats.get('avg_energy', 0):.1f}")
    
    div_stats = summary.get('diversity_stats', {})
    print(f"\n多样性统计:")
    print(f"  平均值：{div_stats.get('avg', 0):.3f}")
    print(f"  最终值：{div_stats.get('final', 0):.3f}")
    
    print("\n" + "="*60)


def main():
    """主函数"""
    print("🔍 Phase 4a - 数据提取与清洗")
    print("="*60)
    
    # 加载检查点
    print("\n加载检查点数据...")
    checkpoints = load_all_checkpoints()
    print(f"✓ 加载 {len(checkpoints)} 个检查点")
    
    # 生成摘要
    print("\n生成数据摘要...")
    summary = generate_summary(checkpoints)
    
    # 保存数据
    save_to_csv(checkpoints)
    save_summary(summary)
    
    # 打印摘要
    print_summary_table(summary)
    
    print("\n✅ Phase 4a 完成！")
    print("下一步：运行 Phase 4b - 统计分析")


if __name__ == "__main__":
    main()
