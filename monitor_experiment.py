#!/usr/bin/env python3
"""实时监控实验进度"""

import json
import time
import os
from pathlib import Path

def monitor():
    log_file = Path("experiments/experiment_100gen.log")
    json_pattern = "experiments/experiment_100gen_forced_*.json"

    print("="*70)
    print("MOSS v8.0 - Experiment Monitor")
    print("="*70)
    print(f"Log file: {log_file}")
    print("Press Ctrl+C to stop monitoring\n")

    while True:
        # 检查日志
        if log_file.exists():
            lines = log_file.read_text().split('\n')
            # 显示最后 20 行
            print("\033[2J\033[H")  # 清屏
            print("="*70)
            print("Last 20 lines of log:")
            print("="*70)
            for line in lines[-20:]:
                if line.strip():
                    print(line)

        # 检查是否有结果文件
        import glob
        result_files = glob.glob(json_pattern)
        if result_files:
            latest = max(result_files, key=os.path.getmtime)
            try:
                with open(latest) as f:
                    data = json.load(f)
                print(f"\n{'='*70}")
                print(f"Latest results: {latest}")
                print(f"{'='*70}")
                for exp in data:
                    print(f"\n{exp['name']}:")
                    print(f"  Generations: {exp.get('generations', 'N/A')}")
                    print(f"  Fitness: {exp.get('initial_fitness', 0):.4f} → {exp.get('final_fitness', 0):.4f}")
                    print(f"  Improvement: {exp.get('improvement', 0):+.4f}")
                    print(f"  LLM calls: {exp.get('llm_calls', 0)}")
                    print(f"  Time: {exp.get('elapsed_seconds', 0)/60:.1f} min")
            except Exception as e:
                pass

        time.sleep(10)

if __name__ == "__main__":
    try:
        monitor()
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")
