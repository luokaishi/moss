#!/bin/bash
# 72小时实验监控和通知脚本
# 每30分钟检查一次状态，实验完成时发送通知

EXPERIMENT_DIR="/workspace/projects/moss/experiments"
LOG_FILE="/tmp/72h_full_experiment.log"
REPORT_FILE="$EXPERIMENT_DIR/real_world_72h_report.json"
STATUS_FILE="$EXPERIMENT_DIR/72h_experiment_status.json"
PID=581

# 检查实验是否仍在运行
check_running() {
    if ps -p $PID > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# 获取当前进度
get_progress() {
    if [ -f "$LOG_FILE" ]; then
        tail -1 "$LOG_FILE" | grep -o "Progress: [0-9.]*%" || echo "Progress: unknown"
    else
        echo "Progress: log not found"
    fi
}

# 获取操作数量
get_action_count() {
    if [ -f "$EXPERIMENT_DIR/real_world_actions.jsonl" ]; then
        wc -l < "$EXPERIMENT_DIR/real_world_actions.jsonl"
    else
        echo "0"
    fi
}

# 发送完成通知（这里可以扩展为发送邮件/飞书等）
send_completion_notice() {
    echo "========================================"
    echo "🎉 72小时实验已完成！"
    echo "========================================"
    echo "时间: $(date)"
    echo "报告: $REPORT_FILE"
    echo "操作数: $(get_action_count)"
    echo ""
    
    if [ -f "$REPORT_FILE" ]; then
        echo "实验结果:"
        cat "$REPORT_FILE"
    fi
    
    # 更新状态文件
    cat > "$STATUS_FILE" << EOF
{
  "experiment": "72h Real World Full",
  "status": "COMPLETED",
  "pid": $PID,
  "start_time": "2026-03-20T18:30:02",
  "end_time": "$(date -Iseconds)",
  "duration_hours": 72,
  "action_count": $(get_action_count),
  "report_file": "$REPORT_FILE"
}
EOF
}

# 更新状态
update_status() {
    cat > "$STATUS_FILE" << EOF
{
  "experiment": "72h Real World Full",
  "status": "RUNNING",
  "pid": $PID,
  "progress": "$(get_progress)",
  "actions": $(get_action_count),
  "last_update": "$(date -Iseconds)"
}
EOF
}

# 主监控循环
main() {
    echo "Starting 72h experiment monitor..."
    echo "PID: $PID"
    echo "Start time: $(date)"
    
    while true; do
        if check_running; then
            echo "[$(date)] Experiment running... $(get_progress) | Actions: $(get_action_count)"
            update_status
        else
            echo "[$(date)] Experiment finished!"
            send_completion_notice
            break
        fi
        
        # 每30分钟检查一次
        sleep 1800
    done
}

main
