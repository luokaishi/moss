#!/usr/bin/env python3
"""
实验结果可视化
生成图表展示实验结果

日期：2026-04-22
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np


def load_results(exp_dir: str) -> List[Dict]:
    """加载实验结果"""
    results_file = Path(exp_dir) / "results.json"
    if not results_file.exists():
        print(f"❌ 结果文件不存在: {results_file}")
        return []
    
    with open(results_file) as f:
        return json.load(f)


def print_summary(exp_name: str, results: List[Dict]):
    """打印实验摘要"""
    print(f"\n{'='*60}")
    print(f"实验: {exp_name}")
    print(f"{'='*60}")
    
    if not results:
        print("❌ 无结果数据")
        return
    
    e_results = [r for r in results if r.get("group") == "E"]
    c_results = [r for r in results if r.get("group") == "C"]
    
    print(f"\n样本量: E组={len(e_results)}, C组={len(c_results)}")
    
    if e_results:
        e_improvements = [r.get("improvement", 0) for r in e_results]
        print(f"\nE 组 (LLM):")
        print(f"  改进: {np.mean(e_improvements):+.4f} ± {np.std(e_improvements):.4f}")
        print(f"  范围: [{min(e_improvements):+.4f}, {max(e_improvements):+.4f}]")
    
    if c_results:
        c_improvements = [r.get("improvement", 0) for r in c_results]
        print(f"\nC 组 (对照):")
        print(f"  改进: {np.mean(c_improvements):+.4f} ± {np.std(c_improvements):.4f}")
        print(f"  范围: [{min(c_improvements):+.4f}, {max(c_improvements):+.4f}]")
    
    if e_results and c_results:
        try:
            from scipy import stats
            e_improvements = [r.get("improvement", 0) for r in e_results]
            c_improvements = [r.get("improvement", 0) for r in c_results]
            t_stat, p_value = stats.ttest_ind(e_improvements, c_improvements)
            print(f"\n统计检验:")
            print(f"  t={t_stat:.3f}, p={p_value:.4f}")
            print(f"  结果: {'✅ 显著' if p_value < 0.05 else '❌ 不显著'} (α=0.05)")
        except ImportError:
            print("\n⚠️ scipy 未安装，跳过统计检验")


def compare_experiments():
    """比较多个实验"""
    experiments = [
        ("N=10 v1 (原始)", "experiments/n10_llm_validation/results"),
        ("N=10 v2 (改进)", "experiments/n10_llm_validation/results_v2"),
        ("N=10 真实 GP", "experiments/n10_real_gp/results"),
    ]
    
    print("\n" + "="*60)
    print("实验对比")
    print("="*60)
    
    for name, path in experiments:
        results = load_results(path)
        if results:
            e_results = [r for r in results if r.get("group") == "E"]
            if e_results:
                improvements = [r.get("improvement", 0) for r in e_results]
                print(f"\n{name}:")
                print(f"  E组改进: {np.mean(improvements):+.4f} ± {np.std(improvements):.4f}")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("MOSS 实验结果可视化")
    print("="*60)
    
    # 显示各个实验结果
    experiments = [
        ("N=10 v1 (原始)", "experiments/n10_llm_validation/results"),
        ("N=10 v2 (改进)", "experiments/n10_llm_validation/results_v2"),
        ("N=10 真实 GP", "experiments/n10_real_gp/results"),
    ]
    
    for name, path in experiments:
        results = load_results(path)
        if results:
            print_summary(name, results)
    
    # 对比实验
    compare_experiments()
    
    print("\n" + "="*60)
    print("可视化完成")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
