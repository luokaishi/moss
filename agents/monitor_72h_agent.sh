#!/bin/bash
# MOSS 72h Experiment Monitor - Sub-Agent Task
# 部署在阿里云OpenClaw上持续监控72h真实世界实验

PROJECT_DIR="/home/admin/moss"
LOG_DIR="/home/admin/moss/logs"
REPORT_FILE="/home/admin/moss/experiments/72h_monitor_report.json"
STATUS_HISTORY="/home/admin/moss/experiments/72h_status_history.jsonl"

# 创建日志目录
mkdir -p $LOG_DIR

echo "========================================"
echo "MOSS 72h Experiment Monitor"
echo "Started: $(date)"
echo "Target: Monitor PID 11788 (72h real-world experiment)"
echo "Duration: 68 hours remaining"
echo "========================================"

# 初始化报告文件
cat > $REPORT_FILE << EOF
{
  "monitor_started": "$(date -Iseconds)",
  "target_pid": 11788,
  "target_experiment": "72h_real_world",
  "status": "RUNNING",
  "checks": []
}
EOF

# 监控循环
CHECK_COUNT=0
while true; do
    TIMESTAMP=$(date -Iseconds)
    CHECK_COUNT=$((CHECK_COUNT + 1))
    
    # 检查进程状态
    if ps -p 11788 > /dev/null 2>&1; then
        PROCESS_STATUS="RUNNING"
        CPU_TIME=$(ps -o cputime= -p 11788 2>/dev/null || echo "N/A")
        
        # 读取实验日志进度
        if [ -f "$PROJECT_DIR/experiments/real_world_72h.log" ]; then
            LAST_LOG=$(tail -1 $PROJECT_DIR/experiments/real_world_72h.log 2>/dev/null)
            echo "[$TIMESTAMP] Process RUNNING - CPU: $CPU_TIME" >> $LOG_DIR/monitor.log
        fi
        
        # 每小时记录一次详细状态
        if [ $((CHECK_COUNT % 2)) -eq 0 ]; then
            echo "{\"timestamp\": \"$TIMESTAMP\", \"check\": $CHECK_COUNT, \"status\": \"RUNNING\", \"cpu_time\": \"$CPU_TIME\"}" >> $STATUS_HISTORY
        fi
        
    else
        PROCESS_STATUS="STOPPED"
        echo "🚨 ALERT: Process 11788 not found at $TIMESTAMP"
        echo "[$TIMESTAMP] 🚨 Process STOPPED" >> $LOG_DIR/monitor.log
        
        # 更新报告文件
        cat > $REPORT_FILE << EOF
{
  "alert": "PROCESS_STOPPED",
  "timestamp": "$TIMESTAMP",
  "target_pid": 11788,
  "check_count": $CHECK_COUNT,
  "action_required": "Check experiment status immediately"
}
EOF
        
        # 发送紧急通知（通过文件标记，主会话可检测）
        touch /tmp/moss_72h_emergency_alert
        echo "$(date): EMERGENCY - 72h experiment stopped" >> /tmp/moss_alerts.log
        
        exit 1
    fi
    
    # 检查是否收到停止信号
    if [ -f "/tmp/moss_monitor_stop" ]; then
        echo "[$TIMESTAMP] Monitor stopped by signal"
        exit 0
    fi
    
    # 每30分钟记录一次（sleep 1800秒）
    sleep 1800
done
