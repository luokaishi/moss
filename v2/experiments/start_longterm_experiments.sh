#!/bin/bash
# MOSS v2.0.0 - 长期验证实验启动脚本
# 6小时和24小时验证

LOG_DIR="/workspace/projects/moss/logs"
EXP_DIR="/workspace/projects/moss/v2/experiments"

echo "=========================================="
echo "MOSS v2.0.0 长期验证实验"
echo "=========================================="
echo ""

# 6小时实验
echo "[1/2] 启动6小时长期验证实验..."
nohup python ${EXP_DIR}/phase1_single_agent.py \
    --duration 6.0 \
    --id longterm_6h_$(date +%m%d_%H%M) \
    > ${LOG_DIR}/longterm_6h.log 2>&1 &
PID_6H=$!
echo "✅ 6小时实验已启动，PID: $PID_6H"
echo "    预计完成: $(date -d '+6 hours' '+%Y-%m-%d %H:%M')"
echo ""

# 24小时实验
echo "[2/2] 启动24小时长期验证实验..."
nohup python ${EXP_DIR}/phase1_single_agent.py \
    --duration 24.0 \
    --id longterm_24h_$(date +%m%d_%H%M) \
    > ${LOG_DIR}/longterm_24h.log 2>&1 &
PID_24H=$!
echo "✅ 24小时实验已启动，PID: $PID_24H"
echo "    预计完成: $(date -d '+24 hours' '+%Y-%m-%d %H:%M')"
echo ""

echo "=========================================="
echo "实验监控命令:"
echo "  6h:  tail -f ${LOG_DIR}/longterm_6h.log"
echo "  24h: tail -f ${LOG_DIR}/longterm_24h.log"
echo "=========================================="

# 保存PID
echo "$PID_6H" > ${LOG_DIR}/longterm_6h.pid
echo "$PID_24H" > ${LOG_DIR}/longterm_24h.pid
