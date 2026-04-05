"""
语义合成验证实验 - 验证方案C效果

目标：
1. 验证语义合成的实际效果
2. 对比新旧版本的差异
3. 统计语义概念使用率

作者: OEF Team
版本: 1.0.0
日期: 2026-04-06
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.semantic_synthesizer import SemanticGoalDiscoverer
import random
import json
from datetime import datetime


def run_semantic_validation(n_runs=50, n_cycles=500):
    """
    运行语义合成验证实验
    
    Args:
        n_runs: 实验运行次数
        n_cycles: 每轮实验周期数
    """
    print(f"=== 语义合成验证实验 (N={n_runs}) ===\n")
    print(f"配置: {n_runs}次运行 x {n_cycles}周期")
    print(f"改进: 45语义概念 + 真正创新\n")
    
    # 创建语义目标发现器
    discoverer = SemanticGoalDiscoverer()
    all_behaviors = discoverer.semantic_synthesizer.base_behaviors
    
    print(f"基础行为: {len(all_behaviors)}个")
    print(f"语义规则: {len(discoverer.semantic_synthesizer.semantic_rules)}个\n")
    
    results = {
        'n_runs': n_runs,
        'n_cycles': n_cycles,
        'start_time': datetime.now().isoformat(),
        'semantic_rules': len(discoverer.semantic_synthesizer.semantic_rules),
        'runs': []
    }
    
    # 统计指标
    total_goals = 0
    semantic_goals = 0
    word_count_dist = {2: 0, 3: 0, 4: 0, 5: 0}
    unique_concepts = set()
    novelty_scores = []
    
    for run_idx in range(n_runs):
        print(f"运行 {run_idx + 1}/{n_runs}...", end=' ')
        
        run_goals = []
        run_semantic = 0
        
        # 模拟n_cycles周期
        for cycle in range(n_cycles):
            # 每100周期生成一个新目标
            if cycle % 100 == 0 and cycle > 0:
                # 从基础行为中选择上下文
                context = random.sample(all_behaviors, min(5, len(all_behaviors)))
                goal = discoverer.discover_goal(context)
                
                run_goals.append({
                    'cycle': cycle,
                    'name': goal['name'],
                    'meaning': goal['meaning'],
                    'novelty_score': goal['novelty_score'],
                    'word_count': goal['word_count'],
                    'is_semantic': goal['is_semantic']
                })
                
                total_goals += 1
                unique_concepts.add(goal['name'])
                novelty_scores.append(goal['novelty_score'])
                
                if goal['is_semantic']:
                    semantic_goals += 1
                    run_semantic += 1
                
                word_count_dist[goal['word_count']] = word_count_dist.get(goal['word_count'], 0) + 1
        
        results['runs'].append({
            'run_idx': run_idx,
            'n_goals': len(run_goals),
            'n_semantic': run_semantic,
            'goals': run_goals
        })
        
        print(f"生成 {len(run_goals)} 个目标 ({run_semantic} 个语义)")
    
    # 汇总统计
    results['end_time'] = datetime.now().isoformat()
    results['summary'] = {
        'total_goals': total_goals,
        'unique_concepts': len(unique_concepts),
        'semantic_goals': semantic_goals,
        'semantic_rate': semantic_goals / total_goals if total_goals > 0 else 0,
        'word_count_distribution': word_count_dist,
        'avg_novelty': sum(novelty_scores) / len(novelty_scores) if novelty_scores else 0,
        'four_plus_rate': (word_count_dist.get(4, 0) + word_count_dist.get(5, 0)) / total_goals if total_goals > 0 else 0
    }
    
    # 打印汇总
    print(f"\n=== 实验结果汇总 ===")
    print(f"总目标数: {total_goals}")
    print(f"唯一概念: {len(unique_concepts)}")
    print(f"语义目标: {semantic_goals} ({semantic_goals/total_goals*100:.1f}%)")
    print(f"平均新颖性: {results['summary']['avg_novelty']:.3f}")
    print(f"\n词数分布:")
    for wc, count in sorted(word_count_dist.items()):
        print(f"  {wc}词: {count} ({count/total_goals*100:.1f}%)")
    print(f"\n4+词占比: {(word_count_dist.get(4, 0) + word_count_dist.get(5, 0))/total_goals*100:.1f}%")
    
    # 保存结果
    output_dir = 'oef_real_data/semantic_validation_n50'
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, 'semantic_validation_report.json')
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n结果已保存: {output_file}")
    
    return results


if __name__ == "__main__":
    # 运行语义合成验证实验
    results = run_semantic_validation(n_runs=50, n_cycles=500)
    
    print("\n=== 改进效果对比 ===")
    print("旧版本 (N=50):")
    print("  - 词汇空间: 10个")
    print("  - 语义创新: 0%")
    print("  - 平均新颖性: 0.00")
    print("\n改进版A+B (N=50):")
    print("  - 词汇空间: 58个")
    print("  - 4+词占比: 49.0%")
    print("  - 唯一目标: 199个")
    print("\n语义合成版C (N=50):")
    print(f"  - 语义规则: {results['semantic_rules']}个")
    print(f"  - 语义目标: {results['summary']['semantic_rate']*100:.1f}%")
    print(f"  - 平均新颖性: {results['summary']['avg_novelty']:.3f}")
    print(f"  - 唯一概念: {results['summary']['unique_concepts']}个")
