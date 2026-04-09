#!/bin/bash
# MOSS 72h Local Experiment Monitor (ISOLATED VERSION)
# 使用方法: ./scripts/monitor_local_72h_isolated.sh

PID_FILE="/tmp/moss_local_72h.pid"
EXPERIMENT_ID="local_72h_20260325"
LOG_DIR="/workspace/projects/moss/experiments/${EXPERIMENT_ID}"
LOG_FILE="${LOG_DIR}/experiment.log"
STATUS_FILE="/workspace/projects/moss/experiments/local_72h_isolated_status.json"

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
    echo "🟢 MOSS 72h Local Experiment (ISOLATED)"
    echo "=========================================="
    echo "Experiment ID: $EXPERIMENT_ID"
    echo "PID:           $PID"
    echo "CPU:           ${CPU}%"
    echo "Memory:        ${MEM}%"
    echo "Elapsed:       $ELAPSED"
    echo "------------------------------------------"
    echo "Last Update:   $LAST_LOG"
    echo "Last Log:      $LAST_LINE"
    echo "------------------------------------------"
    echo "Log Directory: $LOG_DIR"
    echo "查看完整日志:  tail -f $LOG_FILE"
    echo "检查状态:      cat $STATUS_FILE"
    echo "=========================================="
    echo ""
    echo "🛡️ ISOLATION FEATURES:"
    echo "  ✓ Independent action log"
    echo "  ✓ Git push disabled"
    echo "  ✓ No shared resources with external experiment"
    echo "=========================================="
    
else
    echo "=========================================="
    echo "🔴 MOSS 72h Local Experiment - STOPPED"
    echo "=========================================="
    echo "PID $PID 不存在"
    echo ""
    echo "最后日志:"
    tail -20 "$LOG_FILE" 2>/dev/null || echo "无法读取日志"
    echo "=========================================="
fi
