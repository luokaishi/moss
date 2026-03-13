#!/bin/bash
# run_ali_server.sh - 阿里云服务器执行方案（2个6h实验串行）

set -e

LOG_DIR="/workspace/projects/moss/experiments/batch_repeats/ali_results"
mkdir -p $LOG_DIR

cd /workspace/projects/moss/v2/experiments

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=================================="
echo "阿里云服务器实验方案"
echo "配置: 2核2G独占"
echo "开始时间: $(date)"
echo "预计完成: $(date -d '+12 hours' '+%Y-%m-%d %H:%M:%S')"
echo "=================================="

# ========== 实验1（6小时）==========
echo ""
echo "[$(date)] ===== 启动实验1 ====="
nohup python3 phase1_single_agent.py \
    --duration 6.0 \
    --id ali_repeat_1_${TIMESTAMP} \
    > ${LOG_DIR}/log_1.txt 2>&1 &
PID1=$!
echo "实验1 PID: $PID1"
echo "预计完成: $(date -d '+6 hours' '+%Y-%m-%d %H:%M:%S')"

# 等待实验1完成
echo "等待实验1完成（6小时）..."
wait $PID1
echo "[$(date)] 实验1完成！"

# 休息5分钟，释放资源
echo "休息5分钟，清理资源..."
sleep 300

# ========== 实验2（6小时）==========
echo ""
echo "[$(date)] ===== 启动实验2 ====="
nohup python3 phase1_single_agent.py \
    --duration 6.0 \
    --id ali_repeat_2_${TIMESTAMP} \
    > ${LOG_DIR}/log_2.txt 2>&1 &
PID2=$!
echo "实验2 PID: $PID2"
echo "预计完成: $(date -d '+6 hours' '+%Y-%m-%d %H:%M:%S')"

# 等待实验2完成
echo "等待实验2完成（6小时）..."
wait $PID2
echo "[$(date)] 实验2完成！"

# ========== 完成 ==========
echo ""
echo "=================================="
echo "全部实验完成！"
echo "完成时间: $(date)"
echo ""
echo "结果文件:"
ls -lh /workspace/projects/moss/v2/experiments/*ali_repeat*results*.json 2>/dev/null || echo "结果文件可能在其他目录"
echo ""
echo "日志文件:"
ls -lh ${LOG_DIR}/
echo ""
echo "查看结果:"
echo "  python3 /workspace/projects/moss/experiments/batch_repeats/analyze_ali.py"
echo "=================================="