#!/bin/bash
# run_dual_server.sh - 单机并行2个实验方案
# 在腾讯云和阿里云上分别执行

set -e

SERVER_ID=$1  # 传入参数：tencent 或 ali
if [ -z "$SERVER_ID" ]; then
    echo "Usage: ./run_dual_server.sh <tencent|ali>"
    exit 1
fi

LOG_DIR="/workspace/projects/moss/experiments/batch_repeats/${SERVER_ID}_results"
mkdir -p $LOG_DIR

cd /workspace/projects/moss/v2/experiments

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=================================="
echo "服务器: $SERVER_ID"
echo "配置: 2核2G跑2个并行实验"
echo "开始时间: $(date)"
echo "预计完成: $(date -d '+6 hours' '+%Y-%m-%d %H:%M:%S')"
echo "=================================="

# 停止OpenClaw释放资源
echo "停止OpenClaw服务..."
sh /workspace/projects/scripts/stop.sh || true
sleep 10

# 检查资源
echo "可用资源:"
free -h | grep Mem
nproc

# ========== 启动2个并行实验 ==========
echo ""
echo "[$(date)] 启动实验1..."
nohup python3 phase1_single_agent.py \
    --duration 6.0 \
    --id ${SERVER_ID}_repeat_1_${TIMESTAMP} \
    > ${LOG_DIR}/log_1.txt 2>&1 &
PID1=$!
echo "实验1 PID: $PID1"

# 等待60秒避免资源冲突
echo "等待60秒..."
sleep 60

echo "[$(date)] 启动实验2..."
nohup python3 phase1_single_agent.py \
    --duration 6.0 \
    --id ${SERVER_ID}_repeat_2_${TIMESTAMP} \
    > ${LOG_DIR}/log_2.txt 2>&1 &
PID2=$!
echo "实验2 PID: $PID2"

echo ""
echo "=================================="
echo "2个实验已启动！"
echo "服务器: $SERVER_ID"
echo "预计完成: $(date -d '+6 hours' '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "监控命令:"
echo "  ps aux | grep phase1_single_agent"
echo "  tail -f ${LOG_DIR}/log_*.txt"
echo "=================================="

# 保存信息
echo "$PID1 $PID2" > ${LOG_DIR}/pids.txt
echo "$TIMESTAMP" > ${LOG_DIR}/start_time.txt
echo "$SERVER_ID" > ${LOG_DIR}/server_id.txt

# 等待完成
echo "等待实验完成（6小时）..."
wait $PID1
wait $PID2

echo ""
echo "=================================="
echo "[$SERVER_ID] 全部完成！"
echo "完成时间: $(date)"
echo "=================================="

# 重启OpenClaw
echo "重启OpenClaw..."
sh /workspace/projects/scripts/start.sh || true