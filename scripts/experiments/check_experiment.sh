#!/bin/bash
# MOSS长期实验监控脚本

LOG_DIR="/workspace/projects/moss/logs"
PID_FILE="$LOG_DIR/moss_experiment.pid"

echo "=========================================="
echo "MOSS长期实验状态监控"
echo "=========================================="
echo ""

# 检查PID文件
if [ ! -f "$PID_FILE" ]; then
    echo "⚠️  未找到实验PID文件"
    echo ""
    echo "可能原因："
    echo "  1. 实验尚未启动"
    echo "  2. PID文件被删除"
    echo ""
    echo "启动实验："
    echo "  bash /workspace/projects/moss/start_longterm_experiment.sh"
    exit 1
fi

PID=$(cat $PID_FILE)

# 检查进程是否存在
if ! ps -p $PID > /dev/null 2>&1; then
    echo "❌ 实验进程已停止 (PID: $PID)"
    echo ""
    
    # 显示最后日志
    LATEST_LOG=$(ls -t $LOG_DIR/moss_longterm_*.log 2>/dev/null | head -1)
    if [ -n "$LATEST_LOG" ]; then
        echo "最后日志 ($LATEST_LOG):"
        echo "----------------------------------------"
        tail -n 30 "$LATEST_LOG"
        echo "----------------------------------------"
        
        # 检查结果文件
        RESULTS_FILE=$(ls -t $LOG_DIR/results_*.json 2>/dev/null | head -1)
        if [ -n "$RESULTS_FILE" ]; then
            echo ""
            echo "✅ 结果文件已生成:"
            echo "  $RESULTS_FILE"
        fi
    fi
    
    exit 0
fi

# 进程运行中
echo "✅ MOSS长期实验运行中"
echo ""
echo "进程信息:"
echo "  PID: $PID"
echo "  运行时间: $(ps -o etime= -p $PID)"
echo "  CPU使用率: $(ps -o %cpu= -p $PID)%"
echo "  内存使用率: $(ps -o %mem= -p $PID)%"
echo ""

# 显示最新日志
LATEST_LOG=$(ls -t $LOG_DIR/moss_longterm_*.log 2>/dev/null | head -1)
if [ -n "$LATEST_LOG" ]; then
    echo "最新日志 ($LATEST_LOG):"
    echo "----------------------------------------"
    tail -n 20 "$LATEST_LOG"
    echo "----------------------------------------"
fi

echo ""
echo "操作选项:"
echo "  1. 查看完整日志: tail -f $LATEST_LOG"
echo "  2. 停止实验: kill $PID"
echo "  3. 查看结果: ls -la $LOG_DIR/results_*.json"
echo "=========================================="
