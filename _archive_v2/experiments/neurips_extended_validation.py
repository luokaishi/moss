#!/usr/bin/env python3
"""
Extended Statistical Validation for NeurIPS 2026 Submission
Runs additional N=10 experiments to reach N=25 total
Same setup as original N=15 validation
"""

import subprocess
import sys
import time
import json
import os
from datetime import datetime

# Configuration
INITIAL_WEIGHTS = [0.2, 0.4, 0.3, 0.1]
DURATION = 6.0  # hours
MAX_STEPS = 50000  # approximately 6 hours
NUM_INSTANCES = 10
START_INDEX = 16  # Continue from instance_16

# Seeds for additional runs (different from first 15)
SEEDS = [
    2026, 3015, 4096, 5182, 6273,
    7384, 8495, 9506, 10617, 11728
]

def run_instance(instance_id, seed):
    """Run a single experiment instance."""
    print(f"\n{'='*60}")
    print(f"Starting Instance {instance_id:02d} (Seed: {seed})")
    print(f"{'='*60}\n")
    
    # Create log file
    log_file = f"instance_{instance_id:02d}_seed{seed}.log"
    
    # Build command
    cmd = [
        sys.executable,
        "phase1_single_agent.py",
        "--duration", str(DURATION),
        "--initial-weights", ",".join(map(str, INITIAL_WEIGHTS)),
        "--seed", str(seed),
        "--experiment-id", f"neurips_val_{instance_id:02d}",
        "--output-dir", "neurips_validation"
    ]
    
    print(f"Command: {' '.join(cmd)}")
    print(f"Log file: {log_file}")
    
    # Run with output redirection
    with open(log_file, 'w') as f:
        process = subprocess.Popen(
            cmd,
            stdout=f,
            stderr=subprocess.STDOUT,
            cwd="/workspace/projects/moss/v2/experiments"
        )
    
    return process, log_file

def main():
    """Main execution."""
    print("="*60)
    print("MOSS NeurIPS 2026 Extended Statistical Validation")
    print("="*60)
    print(f"Start time: {datetime.now()}")
    print(f"Initial weights: {INITIAL_WEIGHTS}")
    print(f"Duration: {DURATION}h per instance")
    print(f"Number of instances: {NUM_INSTANCES}")
    print(f"Total estimated time: {NUM_INSTANCES * DURATION}h")
    print("="*60)
    
    # Create output directory
    output_dir = "/workspace/projects/moss/v2/experiments/neurips_validation"
    os.makedirs(output_dir, exist_ok=True)
    
    # Run all instances in parallel using tmux
    print("\nCreating tmux sessions for parallel execution...")
    
    sessions = []
    for i, seed in enumerate(SEEDS):
        instance_id = START_INDEX + i
        session_name = f"neurips_{instance_id:02d}"
        log_file = f"{output_dir}/instance_{instance_id:02d}_seed{seed}.log"
        
        cmd = (
            f"cd /workspace/projects/moss/v2/experiments && "
            f"MOSS_SEED={seed} MOSS_INITIAL_WEIGHTS='{','.join(map(str, INITIAL_WEIGHTS))}' "
            f"python3 phase1_single_agent.py "
            f"--duration {DURATION} "
            f"--id neurips_val_{instance_id:02d} "
            f"2>&1 | tee {log_file}"
        )
        
        # Create tmux session
        subprocess.run([
            "tmux", "new-session", "-d", "-s", session_name, cmd
        ])
        
        sessions.append({
            'id': instance_id,
            'seed': seed,
            'session': session_name,
            'log': log_file
        })
        
        print(f"  [{instance_id:02d}] tmux session: {session_name}, seed: {seed}")
        time.sleep(1)  # Small delay to avoid resource spike
    
    # Save metadata
    metadata = {
        'start_time': datetime.now().isoformat(),
        'initial_weights': INITIAL_WEIGHTS,
        'duration_hours': DURATION,
        'num_instances': NUM_INSTANCES,
        'instances': sessions
    }
    
    with open(f"{output_dir}/metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n{'='*60}")
    print("All instances started!")
    print(f"{'='*60}")
    print(f"\nMonitor progress:")
    print(f"  tmux ls                    # List all sessions")
    print(f"  tmux attach -t neurips_16  # Attach to specific session")
    print(f"  tail -f {output_dir}/instance_*.log  # Monitor logs")
    print(f"\nEstimated completion: ~{DURATION} hours")
    print(f"Metadata saved to: {output_dir}/metadata.json")

if __name__ == "__main__":
    main()
