#!/usr/bin/env python3
"""
MOSS Run 4.x Series Analysis Tool
分析Run 4.2/4.3/4.4实验结果，对比不同初始条件和参数的影响
"""

import json
import sys
from pathlib import Path
from collections import Counter
import statistics

def load_actions(filepath):
    """加载actions.jsonl文件"""
    actions = []
    with open(filepath) as f:
        for line in f:
            actions.append(json.loads(line))
    return actions

def load_status(filepath):
    """加载status.json文件"""
    with open(filepath) as f:
        return json.load(f)

def analyze_purpose_distribution(actions):
    """分析Purpose分布"""
    purposes = [a.get('purpose', 'Unknown') for a in actions if 'purpose' in a]
    return Counter(purposes)

def analyze_action_diversity(actions):
    """分析行动多样性"""
    action_types = [a['action'] for a in actions]
    unique_actions = len(set(action_types))
    total_actions = len(action_types)
    diversity_ratio = unique_actions / total_actions if total_actions > 0 else 0
    return {
        'unique_actions': unique_actions,
        'total_actions': total_actions,
        'diversity_ratio': diversity_ratio,
        'top_actions': Counter(action_types).most_common(10)
    }

def analyze_success_rate(actions):
    """分析成功率"""
    successes = sum(1 for a in actions if a.get('success', False))
    total = len(actions)
    return {
        'successes': successes,
        'total': total,
        'success_rate': successes / total if total > 0 else 0
    }

def analyze_run(run_dir, run_name):
    """分析单个Run"""
    run_path = Path(run_dir)
    
    # 找到actions文件
    actions_files = list(run_path.glob('*actions*.jsonl'))
    if not actions_files:
        print(f"❌ {run_name}: No actions file found")
        return None
    
    actions_file = actions_files[0]
    status_files = list(run_path.glob('*status*.jsonl')) + list(run_path.glob('*status*.json'))
    
    print(f"\n📊 Analyzing {run_name}...")
    print(f"   Actions file: {actions_file.name}")
    
    actions = load_actions(actions_file)
    
    result = {
        'run_name': run_name,
        'total_records': len(actions),
        'purpose_distribution': analyze_purpose_distribution(actions),
        'action_diversity': analyze_action_diversity(actions),
        'success_rate': analyze_success_rate(actions)
    }
    
    # 如果有status文件，加载最终状态
    if status_files:
        status = load_status(status_files[0])
        result['final_status'] = status
    
    return result

def print_analysis(result):
    """打印分析结果"""
    if not result:
        return
    
    print(f"\n{'='*60}")
    print(f"📈 {result['run_name']} Analysis Results")
    print(f"{'='*60}")
    
    print(f"\n📝 Basic Statistics:")
    print(f"   Total Records: {result['total_records']:,}")
    
    print(f"\n🎯 Purpose Distribution:")
    for purpose, count in result['purpose_distribution'].most_common():
        pct = count / result['total_records'] * 100
        print(f"   {purpose}: {count:,} ({pct:.1f}%)")
    
    print(f"\n🔀 Action Diversity:")
    div = result['action_diversity']
    print(f"   Unique Actions: {div['unique_actions']}")
    print(f"   Total Actions: {div['total_actions']:,}")
    print(f"   Diversity Ratio: {div['diversity_ratio']:.3f}")
    print(f"   Top 5 Actions:")
    for action, count in div['top_actions'][:5]:
        print(f"      - {action}: {count:,}")
    
    print(f"\n✅ Success Rate:")
    sr = result['success_rate']
    print(f"   {sr['successes']:,} / {sr['total']:,} ({sr['success_rate']*100:.1f}%)")
    
    if 'final_status' in result:
        status = result['final_status']
        print(f"\n🏁 Final Status:")
        print(f"   Step: {status.get('step', 'N/A'):,}")
        print(f"   Progress: {status.get('progress', 0)*100:.1f}%")
        print(f"   Dominant Purpose: {status.get('purpose', {}).get('dominant', 'N/A')}")
        metrics = status.get('metrics', {})
        print(f"   Success Rate: {metrics.get('success_rate', 0):.2f}")
        print(f"   Diversity: {metrics.get('diversity', 0):.2f}")

def compare_runs(results):
    """对比多个Run"""
    print(f"\n{'='*60}")
    print(f"📊 Cross-Run Comparison")
    print(f"{'='*60}")
    
    print(f"\n{'Run':<15} {'Records':>10} {'Diversity':>10} {'Success%':>10} {'Final Purpose':<15}")
    print("-" * 65)
    
    for result in results:
        if not result:
            continue
        name = result['run_name']
        records = result['total_records']
        diversity = result['action_diversity']['diversity_ratio']
        success = result['success_rate']['success_rate'] * 100
        final_purpose = result.get('final_status', {}).get('purpose', {}).get('dominant', 'N/A')
        
        print(f"{name:<15} {records:>10,} {diversity:>10.3f} {success:>10.1f} {final_purpose:<15}")

def main():
    """主函数"""
    base_dir = Path(__file__).parent.parent / 'run_4_series'
    
    if not base_dir.exists():
        print(f"❌ Directory not found: {base_dir}")
        sys.exit(1)
    
    runs = ['run_4_2', 'run_4_3', 'run_4_4']
    results = []
    
    print("="*60)
    print("MOSS Run 4.x Series Analysis")
    print("="*60)
    
    for run_name in runs:
        run_dir = base_dir / run_name
        if run_dir.exists():
            result = analyze_run(run_dir, run_name)
            if result:
                results.append(result)
                print_analysis(result)
        else:
            print(f"⚠️ {run_name} directory not found")
    
    if len(results) > 1:
        compare_runs(results)
    
    print(f"\n{'='*60}")
    print("✅ Analysis Complete")
    print("="*60)

if __name__ == '__main__':
    main()
