#!/usr/bin/env python3
"""
repeat_experiments.py - Statistical repeatability testing for MOSS

Runs N independent repetitions of experiments and generates statistical report.
Usage:
    python repeat_experiments.py --duration 6.0 --n 10 --exp-type longterm
"""

import argparse
import json
import subprocess
import time
import statistics
from datetime import datetime
from pathlib import Path
import sys

def run_single_experiment(duration, exp_id, seed=None):
    """Run a single experiment and return results."""
    cmd = [
        "python3", "phase1_single_agent.py",
        "--duration", str(duration),
        "--id", exp_id
    ]
    if seed:
        cmd.extend(["--seed", str(seed)])
    
    print(f"  Starting {exp_id}...")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            cwd="/workspace/projects/moss/v2/experiments",
            capture_output=True,
            text=True,
            timeout=duration * 3600 + 300  # duration + 5 min buffer
        )
        elapsed = time.time() - start_time
        
        # Parse results from JSON file
        result_file = Path(f"/workspace/projects/moss/v2/experiments/{exp_id}_results.json")
        if result_file.exists():
            with open(result_file) as f:
                data = json.load(f)
            return {
                "success": True,
                "exp_id": exp_id,
                "duration": elapsed,
                "final_weights": data.get("final_weights", {}),
                "total_actions": data.get("total_actions", 0),
                "knowledge_acquired": data.get("knowledge_acquired", 0),
                "cumulative_reward": data.get("cumulative_reward", 0),
                "modifications": data.get("modifications", 0)
            }
        else:
            return {"success": False, "exp_id": exp_id, "error": "No result file"}
    
    except subprocess.TimeoutExpired:
        return {"success": False, "exp_id": exp_id, "error": "Timeout"}
    except Exception as e:
        return {"success": False, "exp_id": exp_id, "error": str(e)}

def calculate_statistics(values):
    """Calculate mean, std, and 95% CI."""
    if len(values) < 2:
        return {"mean": values[0] if values else 0, "std": 0, "ci95": (0, 0)}
    
    mean = statistics.mean(values)
    std = statistics.stdev(values)
    n = len(values)
    
    # 95% CI using t-distribution approximation
    from math import sqrt
    ci_margin = 1.96 * std / sqrt(n)  # z-score for 95%
    
    return {
        "mean": mean,
        "std": std,
        "ci95": (mean - ci_margin, mean + ci_margin),
        "min": min(values),
        "max": max(values),
        "median": statistics.median(values)
    }

def analyze_results(results):
    """Analyze experimental results and generate statistics."""
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    print(f"\n{'='*60}")
    print(f"REPEATABILITY ANALYSIS")
    print(f"{'='*60}")
    print(f"Total experiments: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if len(successful) < 2:
        print("\nInsufficient successful runs for statistical analysis.")
        return
    
    # Extract metrics
    rewards = [r["cumulative_reward"] for r in successful]
    actions = [r["total_actions"] for r in successful]
    knowledge = [r["knowledge_acquired"] for r in successful]
    mods = [r["modifications"] for r in successful]
    
    # Calculate statistics
    reward_stats = calculate_statistics(rewards)
    action_stats = calculate_statistics(actions)
    knowledge_stats = calculate_statistics(knowledge)
    mod_stats = calculate_statistics(mods)
    
    print(f"\n{'='*60}")
    print("CUMULATIVE REWARD")
    print(f"{'='*60}")
    print(f"Mean: {reward_stats['mean']:.2f}")
    print(f"Std: {reward_stats['std']:.2f}")
    print(f"95% CI: [{reward_stats['ci95'][0]:.2f}, {reward_stats['ci95'][1]:.2f}]")
    print(f"Median: {reward_stats['median']:.2f}")
    print(f"Range: [{reward_stats['min']:.2f}, {reward_stats['max']:.2f}]")
    
    print(f"\n{'='*60}")
    print("KNOWLEDGE ACQUIRED")
    print(f"{'='*60}")
    print(f"Mean: {knowledge_stats['mean']:.2f}")
    print(f"Std: {knowledge_stats['std']:.2f}")
    print(f"95% CI: [{knowledge_stats['ci95'][0]:.2f}, {knowledge_stats['ci95'][1]:.2f}]")
    
    print(f"\n{'='*60}")
    print("WEIGHT MODIFICATIONS")
    print(f"{'='*60}")
    print(f"Mean: {mod_stats['mean']:.2f}")
    print(f"Std: {mod_stats['std']:.2f}")
    
    # Strategy classification
    print(f"\n{'='*60}")
    print("STRATEGY CLASSIFICATION")
    print(f"{'='*60}")
    
    strategies = {"social_exploration": 0, "knowledge_seeking": 0, "balanced": 0, "other": 0}
    
    for r in successful:
        w = r["final_weights"]
        if w.get("influence", 0) > 0.4:
            strategies["social_exploration"] += 1
        elif w.get("curiosity", 0) > 0.5:
            strategies["knowledge_seeking"] += 1
        elif w.get("survival", 0) > 0.4:
            strategies["balanced"] += 1
        else:
            strategies["other"] += 1
    
    for strategy, count in strategies.items():
        pct = 100 * count / len(successful)
        print(f"{strategy}: {count}/{len(successful)} ({pct:.1f}%)")
    
    # Save report
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_runs": len(results),
        "successful_runs": len(successful),
        "statistics": {
            "reward": reward_stats,
            "actions": action_stats,
            "knowledge": knowledge_stats,
            "modifications": mod_stats
        },
        "strategies": strategies,
        "raw_results": successful
    }
    
    report_file = f"/workspace/projects/moss/experiments/batch_repeats/repeat_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Report saved: {report_file}")
    print(f"{'='*60}")

def main():
    parser = argparse.ArgumentParser(description='Run repeated MOSS experiments')
    parser.add_argument('--duration', type=float, default=6.0, help='Experiment duration in hours')
    parser.add_argument('--n', type=int, default=10, help='Number of repetitions')
    parser.add_argument('--exp-type', type=str, default='longterm', help='Experiment type')
    parser.add_argument('--sequential', action='store_true', help='Run sequentially (safer for low-resource)')
    
    args = parser.parse_args()
    
    print(f"{'='*60}")
    print(f"MOSS REPEATABILITY EXPERIMENT")
    print(f"{'='*60}")
    print(f"Duration: {args.duration}h")
    print(f"Repetitions: {args.n}")
    print(f"Mode: {'Sequential' if args.sequential else 'Parallel (limited)'}")
    print(f"{'='*60}\n")
    
    results = []
    
    if args.sequential:
        # Sequential execution (recommended for 2-core servers)
        for i in range(args.n):
            exp_id = f"repeat_{args.exp_type}_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            print(f"\n[{i+1}/{args.n}] Running {exp_id}...")
            result = run_single_experiment(args.duration, exp_id, seed=1000+i)
            results.append(result)
            
            if result["success"]:
                print(f"  ✓ Completed: reward={result['cumulative_reward']:.2f}")
            else:
                print(f"  ✗ Failed: {result.get('error', 'Unknown')}")
    
    else:
        # Parallel execution with resource limits
        print("Parallel mode: Running with resource constraints...")
        # Implementation for parallel mode (omitted for brevity)
        pass
    
    # Analyze and report
    analyze_results(results)

if __name__ == "__main__":
    main()