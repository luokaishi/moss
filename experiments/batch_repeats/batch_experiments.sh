#!/bin/bash
# batch_experiments.sh - Run N=10 parallel 6h experiments

# Create experiment directory
mkdir -p /workspace/projects/moss/experiments/batch_repeats
cd /workspace/projects/moss/v2/experiments

# Run 5 experiments in parallel (round 1)
echo "Starting Round 1 (1-5)..."
for i in {1..5}; do
    nohup python3 phase1_single_agent.py \
        --duration 6.0 \
        --id repeat_6h_${i}_$(date +%Y%m%d_%H%M%S) \
        > /workspace/projects/moss/experiments/batch_repeats/log_${i}.txt 2>&1 &
    echo "Started experiment $i, PID: $!"
    sleep 10  # Stagger starts to avoid resource conflict
done

echo "Round 1 started. 5 experiments running in parallel."
echo "Check status: ps aux | grep phase1_single_agent"
echo "Logs: tail -f /workspace/projects/moss/experiments/batch_repeats/log_*.txt"

# After 6 hours, run round 2 (6-10)
echo ""
echo "To start Round 2 (6-10) after 6 hours, run:"
echo "  for i in {6..10}; do nohup python3 phase1_single_agent.py --duration 6.0 --id repeat_6h_\${i}_\$(date +%Y%m%d_%H%M%S) > /workspace/projects/moss/experiments/batch_repeats/log_\${i}.txt 2>&1 & sleep 10; done"