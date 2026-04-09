#!/bin/bash
# MOSS 72小时实验监控脚本
# 定期报告实验进度

LOG_FILE="/workspace/projects/moss/experiments/real_world_72h.log"
REPORT_FILE="/workspace/projects/moss/experiments/real_world_72h_report.json"
ACTION_LOG="/workspace/projects/moss/experiments/real_world_actions.jsonl"
PID_FILE="/tmp/moss_72h_monitor.pid"

# 检查实验是否在运行
check_experiment() {
    if pgrep -f "real_world_72h.py" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# 生成进度报告
generate_report() {
    echo "=== MOSS 72h Experiment Status ==="
    echo "Time: $(date)"
    echo ""
    
    if [ -f "$LOG_FILE" ]; then
        echo "📊 Latest Progress:"
        tail -10 "$LOG_FILE" | grep -E "Progress|Step|Real-world task"
        echo ""
    fi
    
    if [ -f "$ACTION_LOG" ]; then
        echo "🔧 Actions executed: $(wc -l < "$ACTION_LOG")"
        echo ""
        echo "Recent actions:"
        tail -3 "$ACTION_LOG" | python3 -c "import sys,json; [print(f'  - {json.loads(l)[\"task\"]}') for l in sys.stdin]"
    fi
    
    if [ -f "$REPORT_FILE" ]; then
        echo ""
        echo "📈 Final Report available: $REPORT_FILE"
    fi
}

# 主循环
main() {
    echo $$ > "$PID_FILE"
    
    while true; do
        if check_experiment; then
            echo "$(date): Experiment running..."
            generate_report > /tmp/moss_72h_status.txt
            # 这里可以添加发送报告的逻辑
        else
            echo "$(date): Experiment not running"
            if [ -f "$REPORT_FILE" ]; then
                echo "Final report generated"
                generate_report
                break
            fi
        fi
        
        # 每5分钟检查一次
        sleep 300
    done
    
    rm -f "$PID_FILE"
}

main
