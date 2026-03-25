#!/bin/bash
# MOSS 72h Local Experiment Monitor
# 使用方法: ./scripts/monitor_local_72h.sh

PID_FILE="/tmp/moss_72h.pid"
LOG_FILE="/workspace/projects/moss/experiments/local_72h_experiment.log"
STATUS_FILE="/workspace/projects/moss/experiments/local_72h_status.json"

# 检查PID文件
if [ ! -f "$PID_FILE" ]; then
    echo "❌ PID文件不存在: $PID_FILE"
    exit 1
fi

PID=$(cat "$PID_FILE")

# 检查进程是否存在
if ps -p "$PID" > /dev/null 2>&1; then
    # 获取进程信息
    CPU=$(ps -p "$PID" -o %cpu --no-headers | tr -d ' ')
    MEM=$(ps -p "$PID" -o %mem --no-headers | tr -d ' ')
    ELAPSED=$(ps -p "$PID" -o etime --no-headers | tr -d ' ')
    
    # 获取日志最后更新时间
    if [ -f "$LOG_FILE" ]; then
        LAST_LOG=$(stat -c %y "$LOG_FILE" 2>/dev/null | cut -d'.' -f1)
        LAST_LINE=$(tail -1 "$LOG_FILE" 2>/dev/null)
    else
        LAST_LOG="N/A"
        LAST_LINE="N/A"
    fi
    
    echo "=========================================="
    echo "🟢 MOSS 72h Local Experiment - RUNNING"
    echo "=========================================="
    echo "PID:        $PID"
    echo "CPU:        ${CPU}%"
    echo "Memory:     ${MEM}%"
    echo "Elapsed:    $ELAPSED"
    echo "------------------------------------------"
    echo "Last Update: $LAST_LOG"
    echo "Last Log:   $LAST_LINE"
    echo "------------------------------------------"
    echo "查看完整日志: tail -f $LOG_FILE"
    echo "检查状态:     cat $STATUS_FILE"
    echo "=========================================="
    
    # 更新状态文件
    python3 << EOF
import json
from datetime import datetime

try:
    with open("$STATUS_FILE", "r") as f:
        status = json.load(f)
    status["resource_usage"] = {
        "cpu_percent": float("$CPU"),
        "memory_percent": float("$MEM"),
        "status": "healthy"
    }
    status["last_check"] = datetime.now().isoformat()
    with open("$STATUS_FILE", "w") as f:
        json.dump(status, f, indent=2)
except Exception as e:
    print(f"Warning: Could not update status file: {e}")
EOF
    
else
    echo "=========================================="
    echo "🔴 MOSS 72h Local Experiment - STOPPED"
    echo "=========================================="
    echo "PID $PID 不存在"
    echo ""
    echo "最后日志:"
    tail -20 "$LOG_FILE" 2>/dev/null || echo "无法读取日志"
    echo "=========================================="
    
    # 更新状态文件
    python3 << EOF
import json
from datetime import datetime

try:
    with open("$STATUS_FILE", "r") as f:
        status = json.load(f)
    status["status"] = "STOPPED"
    status["stopped_at"] = datetime.now().isoformat()
    with open("$STATUS_FILE", "w") as f:
        json.dump(status, f, indent=2)
except Exception as e:
    print(f"Warning: Could not update status file: {e}")
EOF
fi
