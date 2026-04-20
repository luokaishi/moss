#!/usr/bin/env python3
"""检查实验状态"""

import json
import os
from pathlib import Path

def check_status():
    print("="*70)
    print("MOSS v8.0 - Experiment Status Check")
    print("="*70)

    # 检查进程
    import subprocess
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    running = [line for line in result.stdout.split('\n') if 'experiment_100gen' in line and 'grep' not in line]

    if running:
        print(f"\n🔄 Experiment running: {len(running)} process(es)")
        for line in running[:2]:
            parts = line.split()
            if len(parts) > 10:
                print(f"   PID {parts[1]}: {parts[10]}")
    else:
        print("\n⏹️  No experiment process running")

    # 检查实验 1 结果
    e1_file = Path("experiments/e3_ast_100gen/sme_run_20260419_155521.json")
    if e1_file.exists():
        with open(e1_file) as f:
            data = json.load(f)
        print(f"\n✅ Experiment 1: AST-only 100gen")
        print(f"   Generations: {data['total_generations']}")
        print(f"   Fitness: {data['initial_fitness']:.4f} → {data['final_fitness']:.4f}")
        print(f"   Improvement: {data['fitness_improvement']:+.4f}")
        print(f"   Accepted: {data['total_mutations_accepted']}")
        print(f"   Time: {data['elapsed_seconds']/60:.1f} min")

    # 检查实验 2 进度
    e4_dir = Path("experiments/e4_scheduled_100gen")
    if e4_dir.exists():
        log_file = e4_dir / "evolution_log.jsonl"
        if log_file.exists():
            with open(log_file) as f:
                lines = f.readlines()
            if lines:
                last = json.loads(lines[-1])
                print(f"\n🔄 Experiment 2: Scheduled LLM 100gen")
                print(f"   Current generation: {last['generation']}")
                print(f"   Current fitness: {last['baseline_fitness']:.4f}")
                print(f"   Progress: {last['generation']}/100")

    # 检查日志
    log_file = Path("experiments/experiment_100gen.log")
    if log_file.exists():
        content = log_file.read_text()
        lines = content.split('\n')
        print(f"\n📝 Latest log lines:")
        for line in lines[-5:]:
            if line.strip():
                print(f"   {line}")

if __name__ == "__main__":
    check_status()
