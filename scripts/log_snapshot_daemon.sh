#!/bin/bash
# MOSS实时日志快照守护进程
# 每5分钟自动截取最新20行日志存档
# 用法: ./log_snapshot_daemon.sh [日志文件路径] [输出目录]

LOG_FILE="${1:-/workspace/projects/moss/experiments/moss_72h_experiment.log}"
OUTPUT_DIR="${2:-/workspace/projects/moss/logs/snapshots}"
INTERVAL=300  # 5分钟 = 300秒
LINES=20      # 每次截取20行

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 日志文件检查
if [ ! -f "$LOG_FILE" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 警告: 日志文件不存在: $LOG_FILE" | tee -a "$OUTPUT_DIR/daemon.log"
    echo "等待日志文件创建..."
fi

# 启动守护进程
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 日志快照守护进程启动"
echo "监控文件: $LOG_FILE"
echo "输出目录: $OUTPUT_DIR"
echo "快照间隔: ${INTERVAL}秒"
echo "每次行数: ${LINES}行"
echo "PID: $$"
echo "----------------------------------------"

# 保存PID
 echo $$ > "$OUTPUT_DIR/snapshot_daemon.pid"

# 主循环
while true; do
    TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
    SNAPSHOT_FILE="$OUTPUT_DIR/snapshot_${TIMESTAMP}.log"
    
    if [ -f "$LOG_FILE" ]; then
        # 截取最新20行
        tail -n "$LINES" "$LOG_FILE" > "$SNAPSHOT_FILE"
        # 添加元数据
        {
            echo "--- SNAPSHOT METADATA ---"
            echo "timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
            echo "source: $LOG_FILE"
            echo "lines: $LINES"
            echo "pid: $$"
            echo "========================="
        } >> "$SNAPSHOT_FILE"
        
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 已保存快照: $SNAPSHOT_FILE"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 等待日志文件..."
    fi
    
    # 清理旧快照（保留最近288个 = 24小时）
    ls -t "$OUTPUT_DIR"/snapshot_*.log 2>/dev/null | tail -n +289 | xargs -r rm -f
    
    sleep "$INTERVAL"
done
