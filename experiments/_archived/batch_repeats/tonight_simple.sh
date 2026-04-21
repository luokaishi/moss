#!/bin/bash
# tonight_simple.sh - 最简单的双机实验方案
# 在阿里云和腾讯云上分别执行此脚本

echo "=================================="
echo "MOSS 重复实验 - 简化版"
echo "服务器: $(hostname)"
echo "时间: $(date)"
echo "=================================="

# 停止OpenClaw
echo "停止OpenClaw..."
sh /workspace/projects/scripts/stop.sh 2>/dev/null || true
sleep 5

# 进入实验目录
cd /workspace/projects/moss/v2/experiments

TIMESTAMP=$(date +%Y%m%d_%H%M)
SERVER=$(hostname | cut -d'-' -f1)  # 区分腾讯云/阿里云

echo ""
echo "启动第1个实验..."
nohup python3 phase1_single_agent.py \
    --duration 6.0 \
    --id ${SERVER}_1_${TIMESTAMP} \
    > /tmp/exp1_${SERVER}.log 2>&1 &
PID1=$!
echo "PID: $PID1"

echo "等待60秒..."
sleep 60

echo ""
echo "启动第2个实验..."
nohup python3 phase1_single_agent.py \
    --duration 6.0 \
    --id ${SERVER}_2_${TIMESTAMP} \
    > /tmp/exp2_${SERVER}.log 2>&1 &
PID2=$!
echo "PID: $PID2"

echo ""
echo "=================================="
echo "2个实验已启动！"
echo "预计6小时后完成 ($(date -d '+6 hours' '+%H:%M'))"
echo ""
echo "检查状态: ps aux | grep phase1"
echo "查看日志: tail -f /tmp/exp1_${SERVER}.log"
echo "=================================="

# 保存PID
echo "$PID1 $PID2" > /tmp/experiment_pids.txt

# 等待完成
wait $PID1
wait $PID2

echo ""
echo "=================================="
echo "实验完成！$(date)"
echo "=================================="

# 重启OpenClaw
echo "重启OpenClaw..."
sh /workspace/projects/scripts/start.sh 2>/dev/null || true