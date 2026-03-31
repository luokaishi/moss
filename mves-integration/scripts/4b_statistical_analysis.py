#!/usr/bin/env python3
"""
Phase 4b - 统计分析

对提取的数据进行统计分析，拟合模型，计算相关性
"""

import json
import csv
from pathlib import Path
from datetime import datetime
import math


def load_data(csv_file: str = "analysis/dataset_clean.csv"):
    """加载 CSV 数据"""
    data = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 转换为数值
            for key in row:
                try:
                    row[key] = float(row[key])
                except (ValueError, TypeError):
                    pass
            data.append(row)
    return data


def fit_exponential_model(generations, fitness_scores):
    """拟合指数增长模型 y = a * e^(bx)"""
    if len(generations) < 2:
        return None
    
    # 简单线性回归拟合 log(y)
    n = len(generations)
    sum_x = sum(generations)
    sum_y = sum(math.log(f) for f in fitness_scores if f > 0)
    sum_xy = sum(x * math.log(f) for x, f in zip(generations, fitness_scores) if f > 0)
    sum_xx = sum(x*x for x in generations)
    
    # 计算斜率和截距
    denom = n * sum_xx - sum_x * sum_x
    if denom == 0:
        return None
    
    b = (n * sum_xy - sum_x * sum_y) / denom
    a = math.exp((sum_y - b * sum_x) / n)
    
    return {'a': a, 'b': b, 'model': f'y = {a:.4f} * e^({b:.6f} * x)'}


def calculate_correlation(x_values, y_values):
    """计算皮尔逊相关系数"""
    n = len(x_values)
    if n < 2:
        return 0
    
    mean_x = sum(x_values) / n
    mean_y = sum(y_values) / n
    
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, y_values))
    denom_x = math.sqrt(sum((x - mean_x)**2 for x in x_values))
    denom_y = math.sqrt(sum((y - mean_y)**2 for y in y_values))
    
    if denom_x == 0 or denom_y == 0:
        return 0
    
    return numerator / (denom_x * denom_y)


def calculate_growth_rate(fitness_scores):
    """计算增长率"""
    if len(fitness_scores) < 2:
        return []
    
    rates = []
    for i in range(1, len(fitness_scores)):
        if fitness_scores[i-1] > 0:
            rate = (fitness_scores[i] - fitness_scores[i-1]) / fitness_scores[i-1]
            rates.append(rate)
    
    return rates


def identify_phase_transitions(generations, fitness_scores, window_size=5):
    """识别相变点（增长率显著变化）"""
    if len(fitness_scores) < window_size * 2:
        return []
    
    transitions = []
    
    for i in range(window_size, len(fitness_scores) - window_size):
        # 前窗口平均增长率
        before_rates = calculate_growth_rate(fitness_scores[i-window_size:i])
        avg_before = sum(before_rates) / len(before_rates) if before_rates else 0
        
        # 后窗口平均增长率
        after_rates = calculate_growth_rate(fitness_scores[i:i+window_size])
        avg_after = sum(after_rates) / len(after_rates) if after_rates else 0
        
        # 检测显著变化（>50%）
        if abs(avg_after - avg_before) > 0.5:
            transitions.append({
                'generation': generations[i],
                'fitness': fitness_scores[i],
                'rate_change': avg_after - avg_before,
                'type': 'acceleration' if avg_after > avg_before else 'deceleration'
            })
    
    return transitions


def statistical_tests(fitness_scores):
    """基础统计检验"""
    n = len(fitness_scores)
    if n < 2:
        return {}
    
    mean = sum(fitness_scores) / n
    variance = sum((x - mean)**2 for x in fitness_scores) / (n - 1)
    std_dev = math.sqrt(variance)
    
    # 变异系数
    cv = (std_dev / mean) * 100 if mean > 0 else 0
    
    # 偏度（简化版）
    skewness = sum((x - mean)**3 for x in fitness_scores) / ((n - 1) * std_dev**3) if std_dev > 0 else 0
    
    return {
        'mean': mean,
        'variance': variance,
        'std_dev': std_dev,
        'coefficient_of_variation': cv,
        'skewness': skewness
    }


def analyze_data(data):
    """主分析函数"""
    generations = [d['generation'] for d in data]
    fitness_scores = [d['avg_fitness'] for d in data]
    
    # 1. 指数模型拟合
    exp_model = fit_exponential_model(generations, fitness_scores)
    
    # 2. 相关性分析
    correlations = {
        'generation_fitness': calculate_correlation(generations, fitness_scores),
    }
    
    # 3. 增长率分析
    growth_rates = calculate_growth_rate(fitness_scores)
    avg_growth_rate = sum(growth_rates) / len(growth_rates) if growth_rates else 0
    
    # 4. 相变点检测
    transitions = identify_phase_transitions(generations, fitness_scores)
    
    # 5. 统计检验
    stats = statistical_tests(fitness_scores)
    
    # 6. 关键里程碑
    milestones = []
    thresholds = [1, 2, 5, 10]
    for threshold in thresholds:
        for i, score in enumerate(fitness_scores):
            if score >= threshold:
                milestones.append({
                    'threshold': threshold,
                    'generation': int(generations[i]),
                    'fitness': score
                })
                break
    
    return {
        'exponential_model': exp_model,
        'correlations': correlations,
        'growth_rates': {
            'average': avg_growth_rate,
            'series': growth_rates
        },
        'phase_transitions': transitions,
        'statistics': stats,
        'milestones': milestones,
        'analysis_timestamp': datetime.now().isoformat()
    }


def print_analysis_report(analysis):
    """打印分析报告"""
    print("\n" + "="*60)
    print("Phase 4b - 统计分析结果")
    print("="*60)
    
    if analysis['exponential_model']:
        model = analysis['exponential_model']
        print(f"\n指数增长模型:")
        print(f"  {model['model']}")
    
    print(f"\n相关性分析:")
    for key, value in analysis['correlations'].items():
        print(f"  {key}: {value:.4f}")
    
    print(f"\n增长率:")
    print(f"  平均：{analysis['growth_rates']['average']*100:.2f}%")
    
    if analysis['phase_transitions']:
        print(f"\n相变点 ({len(analysis['phase_transitions'])} 个):")
        for t in analysis['phase_transitions'][:5]:  # 显示前 5 个
            print(f"  Gen {t['generation']}: {t['type']} (Δ={t['rate_change']:.2f})")
    
    print(f"\n统计特征:")
    stats = analysis['statistics']
    print(f"  均值：{stats['mean']:.4f}")
    print(f"  标准差：{stats['std_dev']:.4f}")
    print(f"  变异系数：{stats['coefficient_of_variation']:.2f}%")
    print(f"  偏度：{stats['skewness']:.4f}")
    
    print(f"\n关键里程碑:")
    for m in analysis['milestones']:
        print(f"  适应度≥{m['threshold']}: Gen {m['generation']} (fitness={m['fitness']:.3f})")
    
    print("\n" + "="*60)


def main():
    """主函数"""
    print("📊 Phase 4b - 统计分析")
    print("="*60)
    
    # 加载数据
    print("\n加载数据...")
    data = load_data()
    print(f"✓ 加载 {len(data)} 条记录")
    
    # 执行分析
    print("\n执行统计分析...")
    analysis = analyze_data(data)
    
    # 保存结果
    output_file = "analysis/statistical_analysis.json"
    Path(output_file).parent.mkdir(exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    print(f"✓ 分析结果已保存：{output_file}")
    
    # 打印报告
    print_analysis_report(analysis)
    
    # 生成 Markdown 摘要
    generate_markdown_summary(analysis)
    
    print("\n✅ Phase 4b 完成！")
    print("下一步：运行 Phase 4c - 可视化生成")


def generate_markdown_summary(analysis):
    """生成 Markdown 摘要"""
    output_file = "analysis/statistical_analysis.md"
    
    md = []
    md.append("# MVES v5 统计分析摘要")
    md.append(f"\n**分析时间**: {analysis['analysis_timestamp']}")
    
    if analysis['exponential_model']:
        model = analysis['exponential_model']
        md.append(f"\n## 指数增长模型")
        md.append(f"\n```")
        md.append(f"{model['model']}")
        md.append(f"```")
    
    md.append(f"\n## 相关性分析")
    for key, value in analysis['correlations'].items():
        md.append(f"- **{key}**: {value:.4f}")
    
    md.append(f"\n## 增长率")
    md.append(f"- 平均增长率：{analysis['growth_rates']['average']*100:.2f}%")
    
    if analysis['phase_transitions']:
        md.append(f"\n## 相变点")
        md.append(f"共检测到 {len(analysis['phase_transitions'])} 个相变点：\n")
        md.append("| 代数 | 适应度 | 类型 | 变化率 |")
        md.append("|------|--------|------|--------|")
        for t in analysis['phase_transitions'][:10]:
            md.append(f"| {t['generation']} | {t['fitness']:.3f} | {t['type']} | {t['rate_change']:.2f} |")
    
    md.append(f"\n## 统计特征")
    stats = analysis['statistics']
    md.append(f"- 均值：{stats['mean']:.4f}")
    md.append(f"- 标准差：{stats['std_dev']:.4f}")
    md.append(f"- 变异系数：{stats['coefficient_of_variation']:.2f}%")
    md.append(f"- 偏度：{stats['skewness']:.4f}")
    
    md.append(f"\n## 关键里程碑")
    for m in analysis['milestones']:
        md.append(f"- 适应度≥{m['threshold']}: 第 {m['generation']} 代 (fitness={m['fitness']:.3f})")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
    
    print(f"✓ Markdown 摘要已保存：{output_file}")


if __name__ == "__main__":
    main()
