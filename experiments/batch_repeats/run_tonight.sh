#!/bin/bash
# run_tonight.sh - 今晚启动2个6h重复实验

set -e

cd /workspace/projects/moss/v2/experiments

# 创建日志目录
mkdir -p /workspace/projects/moss/experiments/batch_repeats/results

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=================================="
echo "Starting 2 parallel 6h experiments"
echo "Timestamp: $TIMESTAMP"
echo "=================================="

# 实验1
echo "[$(date)] Starting Experiment 1..."
nohup python3 phase1_single_agent.py \
    --duration 6.0 \
    --id repeat_6h_1_${TIMESTAMP} \
    > /workspace/projects/moss/experiments/batch_repeats/results/log_1.txt 2>&1 &
PID1=$!
echo "Experiment 1 PID: $PID1"

# 等待30秒避免资源冲突
sleep 30

# 实验2
echo "[$(date)] Starting Experiment 2..."
nohup python3 phase1_single_agent.py \
    --duration 6.0 \
    --id repeat_6h_2_${TIMESTAMP} \
    > /workspace/projects/moss/experiments/batch_repeats/results/log_2.txt 2>&1 &
PID2=$!
echo "Experiment 2 PID: $PID2"

echo ""
echo "=================================="
echo "Both experiments started!"
echo "Expected completion: $(date -d '+6 hours' '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "Monitor commands:"
echo "  Check processes: ps aux | grep phase1_single_agent"
echo "  Check logs: tail -f /workspace/projects/moss/experiments/batch_repeats/results/log_*.txt"
echo "  Check results: ls -la /workspace/projects/moss/v2/experiments/*results*.json"
echo "=================================="

# 保存PID信息
echo "$PID1 $PID2" > /workspace/projects/moss/experiments/batch_repeats/results/pids.txt
echo "$TIMESTAMP" > /workspace/projects/moss/experiments/batch_repeats/results/start_time.txt
