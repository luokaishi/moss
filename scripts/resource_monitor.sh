#!/bin/bash
# MOSS 72小时实验资源监控脚本
# 监控内存/CPU使用，超过阈值时报警

LOG_FILE="/workspace/projects/moss/experiments/resource_monitor.log"
ALERT_THRESHOLD_MEM=75  # 内存报警阈值%
ALERT_THRESHOLD_CPU=80  # CPU报警阈值%
PID_FILE="/tmp/moss_resource_monitor.pid"

# 获取MOSS进程资源使用
get_moss_resources() {
    # 查找MOSS相关进程
    moss_pids=$(pgrep -f "real_world_72h.py|MOSSv3Agent")
    
    total_mem=0
    total_cpu=0
    
    for pid in $moss_pids; do
        if [ -f "/proc/$pid/status" ]; then
            # 获取内存使用 (MB)
            mem_kb=$(grep VmRSS /proc/$pid/status | awk '{print $2}')
            if [ ! -z "$mem_kb" ]; then
                mem_mb=$((mem_kb / 1024))
                total_mem=$((total_mem + mem_mb))
            fi
        fi
        
        if [ -f "/proc/$pid/stat" ]; then
            # 获取CPU使用率 (简化计算)
            cpu_time=$(awk '{print $14+$15}' /proc/$pid/stat)
            total_cpu=$((total_cpu + cpu_time))
        fi
    done
    
    # 获取系统总内存
    total_system_mem=$(free -m | awk 'NR==2{print $2}')
    mem_percent=$((total_mem * 100 / total_system_mem))
    
    echo "${mem_percent},${total_mem},${total_cpu}"
}

# 记录资源使用
log_resources() {
    resources=$(get_moss_resources)
    mem_percent=$(echo $resources | cut -d',' -f1)
    mem_mb=$(echo $resources | cut -d',' -f2)
    cpu_time=$(echo $resources | cut -d',' -f3)
    
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] Memory: ${mem_mb}MB (${mem_percent}%), CPU Time: ${cpu_time}" >> $LOG_FILE
    
    # 检查是否超过阈值
    if [ "$mem_percent" -gt "$ALERT_THRESHOLD_MEM" ]; then
        echo "⚠️  ALERT: Memory usage ${mem_percent}% exceeds threshold ${ALERT_THRESHOLD_MEM}%" | tee -a $LOG_FILE
        # 这里可以添加发送通知的逻辑
    fi
}

# 主循环
main() {
    echo $$ > $PID_FILE
    echo "Starting MOSS resource monitor..."
    echo "Log file: $LOG_FILE"
    echo "Memory threshold: ${ALERT_THRESHOLD_MEM}%"
    
    while true; do
        log_resources
        # 每60秒检查一次
        sleep 60
    done
    
    rm -f $PID_FILE
}

# 清理函数
cleanup() {
    rm -f $PID_FILE
    exit 0
}

trap cleanup EXIT INT TERM

main
