#!/bin/bash
# MOSS Run 4.x 实验完成监控脚本
# 当Run 4.3和Run 4.4完成时自动通知用户

PROJECT_DIR="/workspace/projects/moss"
LOG_FILE="/workspace/backup/moss/logs/completion_monitor.log"
NOTIFICATION_SENT_43="/tmp/moss_run4_3_complete"
NOTIFICATION_SENT_44="/tmp/moss_run4_4_complete"

echo "[$(date)] 实验完成监控启动" > $LOG_FILE

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # 检查Run 4.3状态
    if [ -f "$PROJECT_DIR/experiments/run_4_3_status.json" ]; then
        PROGRESS_43=$(cat $PROJECT_DIR/experiments/run_4_3_status.json | grep '"progress"' | head -1 | grep -o '[0-9.]*' | head -1)
        STEP_43=$(cat $PROJECT_DIR/experiments/run_4_3_status.json | grep '"step"' | head -1 | grep -o '[0-9]*' | head -1)
        
        # 检查是否完成（progress >= 1.0 或 step >= 2,880,000）
        if (( $(echo "$PROGRESS_43 >= 1.0" | bc -l 2>/dev/null || echo "0") )) || [ "$STEP_43" -ge 2880000 ] 2>/dev/null; then
            if [ ! -f "$NOTIFICATION_SENT_43" ]; then
                echo "[$TIMESTAMP] 🎉 Run 4.3 实验已完成！" >> $LOG_FILE
                echo "[$TIMESTAMP] Progress: $PROGRESS_43 | Step: $STEP_43" >> $LOG_FILE
                # 创建标记文件，防止重复通知
                touch $NOTIFICATION_SENT_43
                # 输出到控制台（便于OpenClaw捕获）
                echo "======================================"
                echo "🎉 MOSS Run 4.3 实验已完成！"
                echo "完成时间: $TIMESTAMP"
                echo "Progress: $PROGRESS_43"
                echo "Step: $STEP_43"
                echo "======================================"
            fi
        fi
    fi
    
    # 检查Run 4.4状态
    if [ -f "$PROJECT_DIR/experiments/run_4_4_status.json" ]; then
        PROGRESS_44=$(cat $PROJECT_DIR/experiments/run_4_4_status.json | grep '"progress"' | head -1 | grep -o '[0-9.]*' | head -1)
        STEP_44=$(cat $PROJECT_DIR/experiments/run_4_4_status.json | grep '"step"' | head -1 | grep -o '[0-9]*' | head -1)
        
        if (( $(echo "$PROGRESS_44 >= 1.0" | bc -l 2>/dev/null || echo "0") )) || [ "$STEP_44" -ge 2880000 ] 2>/dev/null; then
            if [ ! -f "$NOTIFICATION_SENT_44" ]; then
                echo "[$TIMESTAMP] 🎉 Run 4.4 实验已完成！" >> $LOG_FILE
                echo "[$TIMESTAMP] Progress: $PROGRESS_44 | Step: $STEP_44" >> $LOG_FILE
                touch $NOTIFICATION_SENT_44
                echo "======================================"
                echo "🎉 MOSS Run 4.4 实验已完成！"
                echo "完成时间: $TIMESTAMP"
                echo "Progress: $PROGRESS_44"
                echo "Step: $STEP_44"
                echo "======================================"
            fi
        fi
    fi
    
    # 如果两个实验都完成，退出监控
    if [ -f "$NOTIFICATION_SENT_43" ] && [ -f "$NOTIFICATION_SENT_44" ]; then
        echo "[$TIMESTAMP] ✅ 两个实验均已完成，监控结束" >> $LOG_FILE
        echo "======================================"
        echo "✅ Run 4.3 和 Run 4.4 实验全部完成！"
        echo "======================================"
        exit 0
    fi
    
    # 每30秒检查一次
    sleep 30
done
