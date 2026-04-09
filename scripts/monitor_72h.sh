#!/bin/bash
# 72h实验监控脚本
# 每5分钟记录一次状态

LOG_FILE="/workspace/projects/moss/experiments/monitor_72h_$(date +%Y%m%d).log"
DATA_DIR="/workspace/projects/moss/experiments/local_72h_20260326"

# 创建数据目录（如果不存在）
mkdir -p $DATA_DIR

echo "========================================" >> $LOG_FILE
echo "72h Experiment Monitor Started" >> $LOG_FILE
echo "Time: $(date)" >> $LOG_FILE
echo "PID: 2411" >> $LOG_FILE
echo "========================================" >> $LOG_FILE

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # 检查进程
    if ps -p 2411 > /dev/null; then
        STATUS="RUNNING"
        CPU_MEM=$(ps -p 2411 -o %cpu,%mem | tail -1)
    else
        STATUS="STOPPED"
        CPU_MEM="N/A"
    fi
    
    # 检查actions.jsonl
    if [ -f "$DATA_DIR/actions.jsonl" ]; then
        ACTIONS=$(wc -l < "$DATA_DIR/actions.jsonl")
    else
        ACTIONS="0"
    fi
    
    # 记录状态
    echo "[$TIMESTAMP] Status: $STATUS | Actions: $ACTIONS | CPU/MEM: $CPU_MEM" >> $LOG_FILE
    
    # 每小时输出到控制台
    if [ $(date +%M) -eq "00" ]; then
        echo "[$TIMESTAMP] Hourly check: $STATUS, $ACTIONS actions"
    fi
    
    sleep 300  # 5分钟
done
