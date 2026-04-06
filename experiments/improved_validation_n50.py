"""
改进版批量验证实验 - 测试词汇扩展效果

改进内容：
1. 使用VocabularySynthesizer（58词汇）
2. 支持4+词组合（45%占比）
3. 统计合成词汇使用率

作者: OEF Team
版本: 2.0.0
日期: 2026-04-05
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.vocabulary_synthesizer import EnhancedGoalDiscoverer
import random
import json
from datetime import datetime


def run_improved_validation(n_runs=50, n_cycles=500):
    """
    运行改进版验证实验
    
    Args:
        n_runs: 实验运行次数
        n_cycles: 每轮实验周期数
    """
    print(f"=== 改进版批量验证实验 (N={n_runs}) ===\n")
    print(f"配置: {n_runs}次运行 x {n_cycles}周期")
    print(f"改进: 58词汇 + 4+词组合\n")
    
    # 创建增强版目标发现器
    discoverer = EnhancedGoalDiscoverer()
    all_behaviors = discoverer.vocab_synthesizer.get_all_vocabularies()
    
    print(f"可用行为: {len(all_behaviors)}个")
    print(f"基础行为: 10个")
    print(f"合成词汇: {len(all_behaviors) - 10}个\n")
    
    results = {
        'n_runs': n_runs,
        'n_cycles': n_cycles,
        'start_time': datetime.now().isoformat(),
        'vocabulary_size': len(all_behaviors),
        'runs': []
    }
    
    # 统计指标
    total_goals = 0
    synthesized_goals = 0
    word_count_dist = {2: 0, 3: 0, 4: 0, 5: 0}
    unique_goals = set()
    
    for run_idx in range(n_runs):
        print(f"运行 {run_idx + 1}/{n_runs}...", end=' ')
        
        run_goals = []
        run_synthesized = 0
        
        # 模拟n_cycles周期
        for cycle in range(n_cycles):
            # 每100周期生成一个新目标（模拟涌现）
            if cycle % 100 == 0 and cycle > 0:
                # 从所有可用行为中选择上下文
                context = random.sample(all_behaviors, min(8, len(all_behaviors)))
                goal = discoverer.discover_goal(context)
                
                run_goals.append({
                    'cycle': cycle,
                    'name': goal['name'],
                    'is_synthesized': goal['is_synthesized'],
                    'word_count': goal['word_count'],
                    'source_behaviors': goal['source_behaviors']
                })
                
                total_goals += 1
                unique_goals.add(goal['name'])
                
                if goal['is_synthesized']:
                    synthesized_goals += 1
                    run_synthesized += 1
                
                word_count_dist[goal['word_count']] = word_count_dist.get(goal['word_count'], 0) + 1
        
        results['runs'].append({
            'run_idx': run_idx,
            'n_goals': len(run_goals),
            'n_synthesized': run_synthesized,
            'goals': run_goals
        })
        
        print(f"生成 {len(run_goals)} 个目标 ({run_synthesized} 个合成)")
    
    # 汇总统计
    results['end_time'] = datetime.now().isoformat()
    results['summary'] = {
        'total_goals': total_goals,
        'unique_goals': len(unique_goals),
        'synthesized_goals': synthesized_goals,
        'synthesis_rate': synthesized_goals / total_goals if total_goals > 0 else 0,
        'word_count_distribution': word_count_dist,
        'four_plus_rate': (word_count_dist.get(4, 0) + word_count_dist.get(5, 0)) / total_goals if total_goals > 0 else 0
    }
    
    # 打印汇总
    print(f"\n=== 实验结果汇总 ===")
    print(f"总目标数: {total_goals}")
    print(f"唯一目标: {len(unique_goals)}")
    print(f"合成目标: {synthesized_goals} ({synthesized_goals/total_goals*100:.1f}%)")
    print(f"\n词数分布:")
    for wc, count in sorted(word_count_dist.items()):
        print(f"  {wc}词: {count} ({count/total_goals*100:.1f}%)")
    print(f"\n4+词占比: {(word_count_dist.get(4, 0) + word_count_dist.get(5, 0))/total_goals*100:.1f}%")
    
    # 保存结果
    output_dir = 'oef_real_data/improved_validation_n50'
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, 'improved_validation_report.json')
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n结果已保存: {output_file}")
    
    return results


if __name__ == "__main__":
    # 运行改进版验证实验
    results = run_improved_validation(n_runs=50, n_cycles=500)
    
    print("\n=== 改进效果对比 ===")
    print("旧版本 (N=50):")
    print("  - 词汇空间: 10个")
    print("  - 3词占比: 95.2%")
    print("  - 唯一目标: 129个")
    print("\n新版本 (N=50):")
    print(f"  - 词汇空间: {results['vocabulary_size']}个")
    print(f"  - 4+词占比: {results['summary']['four_plus_rate']*100:.1f}%")
    print(f"  - 唯一目标: {results['summary']['unique_goals']}个")
