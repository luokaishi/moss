#!/bin/bash
# Start both experiments with correct PYTHONPATH

cd /workspace/projects/moss
export PYTHONPATH="/workspace/projects/moss:/workspace/projects/moss/v4/core:/workspace/projects/moss/v4/integration:/workspace/projects/moss/v3/core"

# Kill existing
pkill -f "run_4_3_optimized\|run_4_4_optimized" 2>/dev/null
sleep 1

# Start Run 4.3
nohup python3 -u experiments/run_4_3_optimized.py > experiments/run_4_3_local.out 2>&1 &
echo "Run 4.3 PID: $!"

sleep 2

# Start Run 4.4
nohup python3 -u experiments/run_4_4_optimized.py > experiments/run_4_4_local.out 2>&1 &
echo "Run 4.4 PID: $!"

echo ""
echo "Waiting 5 seconds..."
sleep 5

echo ""
echo "Process status:"
ps aux | grep "run_4_" | grep -v grep

echo ""
echo "Memory status:"
free -h
