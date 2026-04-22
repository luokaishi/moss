#!/usr/bin/env python3
"""
检查实验状态脚本
显示当前实验进度和结果
"""

import json
import sys
from pathlib import Path
from datetime import datetime

RESULTS_DIR = Path("experiments/n10_llm_validation/results")

def check_status():
    """检查实验状态"""
    print("=" * 60)
    print("MOSS N=10 实验状态检查")
    print("=" * 60)
    print(f"时间: {datetime.now().isoformat()}")
    print()
    
    # 检查目录
    if not RESULTS_DIR.exists():
        print("❌ 实验目录不存在")
        print("   路径:", RESULTS_DIR)
        print()
        print("请运行: python3 experiments/n10_llm_validation.py")
        return 1
    
    # 检查 summary.json
    summary_file = RESULTS_DIR / "summary.json"
    if summary_file.exists():
        try:
            with open(summary_file) as f:
                summary = json.load(f)
            
            print("✅ 实验进行中或已完成")
            print()
            
            # 显示进度
            e_group = summary.get("experimental_group", {})
            c_group = summary.get("control_group", {})
            
            e_n = e_group.get("n", 0)
            c_n = c_group.get("n", 0)
            
            print(f"进度: E组 {e_n}/5, C组 {c_n}/5")
            print(f"总计: {e_n + c_n}/10 完成 ({(e_n + c_n) * 10}%)")
            print()
            
            if e_n > 0:
                print("E组 (LLM) 结果:")
                print(f"  平均适应度: {e_group.get('final_fitness_mean', 0):.4f}")
                print(f"  适应度改进: {e_group.get('fitness_improvement_mean', 0):+.4f}")
                print()
            
            if c_n > 0:
                print("C组 (对照) 结果:")
                print(f"  平均适应度: {c_group.get('final_fitness_mean', 0):.4f}")
                print(f"  适应度改进: {c_group.get('fitness_improvement_mean', 0):+.4f}")
                print()
            
            if e_n >= 5 and c_n >= 5:
                print("🎉 实验已完成！")
                
                # 检查统计报告
                report_file = RESULTS_DIR / "statistical_report.md"
                if report_file.exists():
                    print(f"📄 统计报告: {report_file}")
            else:
                print("⏳ 实验进行中...")
            
        except Exception as e:
            print(f"⚠️ 读取结果出错: {e}")
    else:
        print("⏳ 实验尚未开始或暂无结果")
        print("   请运行: python3 experiments/n10_llm_validation.py")
    
    print()
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(check_status())
