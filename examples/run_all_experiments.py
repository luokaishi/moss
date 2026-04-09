#!/usr/bin/env python3
"""
Run All MOSS Experiments
一键运行所有实验并生成综合报告
"""

import subprocess
import sys
import time
import json
from pathlib import Path
from datetime import datetime


def run_command(cmd, description):
    """运行命令并打印状态"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print(f"{'='*60}")
    
    start = time.time()
    result = subprocess.run(cmd, shell=True, capture_output=False, text=True)
    elapsed = time.time() - start
    
    print(f"\nCompleted in {elapsed:.1f}s")
    
    return result.returncode == 0


def main():
    """主函数"""
    print("="*60)
    print("MOSS Complete Experiment Suite")
    print("="*60)
    print(f"Start Time: {datetime.now().isoformat()}")
    print("="*60)
    
    results = {}
    
    # 1. Controlled Experiments (Quick Mode)
    results['controlled'] = run_command(
        "cd sandbox/experiments/controlled && python run_experiments.py --quick",
        "Controlled Experiments (Quick Mode)"
    )
    
    # 2. Influence Fix Validation
    results['influence_fix'] = run_command(
        "cd sandbox/experiments/controlled && python validate_influence_fix.py",
        "Influence Module Security Fix Validation"
    )
    
    # 3. Web Navigation (Quick Mode)
    results['web_navigation'] = run_command(
        "cd sandbox/experiments/controlled && python web_navigation_experiment.py --quick",
        "Web Navigation Complex Environment"
    )
    
    # 4. Generate Summary Report
    print(f"\n{'='*60}")
    print("Generating Summary Report")
    print(f"{'='*60}")
    
    summary = {
        'timestamp': datetime.now().isoformat(),
        'results': results,
        'all_passed': all(results.values())
    }
    
    with open('experiment_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Summary saved to: experiment_summary.json")
    
    # Final Report
    print("\n" + "="*60)
    print("FINAL REPORT")
    print("="*60)
    
    for exp, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {exp}")
    
    print("="*60)
    
    if all(results.values()):
        print("✅ ALL EXPERIMENTS PASSED")
        return 0
    else:
        print("❌ SOME EXPERIMENTS FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
