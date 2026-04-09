#!/bin/bash
#===============================================================================
# MOSS Experiment Monitor - Comprehensive Monitoring
# 多维度监控：本地 + 远程服务器 + 通知
#===============================================================================

# Configuration
SERVER1_HOST="${SERVER1_HOST:-admin@47.77.234.152}"
SERVER2_HOST="${SERVER2_HOST:-root@43.156.104.179}"
FEISHU_WEBHOOK="${FEISHU_WEBHOOK:-}"  # 可选：飞书机器人Webhook

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

#===============================================================================
# 1. 实时监控面板 (Live Dashboard)
#===============================================================================
live_dashboard() {
    clear
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║         MOSS Experiment Live Monitor                         ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    while true; do
        # 移动到顶部
        tput cup 3 0
        
        # 当前时间
        echo -e "${BLUE}Last Update: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
        echo ""
        
        # Run 4.2 (本地)
        echo -e "${GREEN}▶ Run 4.2 (Current Server)${NC}"
        if pgrep -f "run_4_2_resume" > /dev/null 2>&1; then
            local step=$(jq -r '.step' /workspace/projects/moss/experiments/run_4_2_status.json 2>/dev/null || echo "N/A")
            local progress=$(jq -r '.progress' /workspace/projects/moss/experiments/run_4_2_status.json 2>/dev/null | awk '{print $1*100}' || echo "N/A")
            local purpose=$(jq -r '.purpose.dominant' /workspace/projects/moss/experiments/run_4_2_status.json 2>/dev/null || echo "N/A")
            printf "  Status: ${GREEN}● Running${NC}  Step: %s  Progress: %.1f%%  Purpose: %s\n" "$step" "$progress" "$purpose"
        else
            echo -e "  Status: ${RED}● Stopped${NC}"
        fi
        echo ""
        
        # Run 4.3 (服务器1)
        echo -e "${GREEN}▶ Run 4.3 (Server 1 - Curiosity Initial)${NC}"
        local s1_status=$(ssh -o ConnectTimeout=3 "$SERVER1_HOST" '
            if pgrep -f "run_4_3_optimized" > /dev/null; then
                cat ~/moss/experiments/run_4_3_status.json 2>/dev/null | python3 -c "import json,sys;d=json.load(sys.stdin);print(f\"Running|{d[\"step\"]}|{d[\"progress\"]*100:.1f}|{d[\"purpose\"][\"dominant\"]}\")" 2>/dev/null || echo "Running|N/A|N/A|N/A"
            else
                echo "Stopped|N/A|N/A|N/A"
            fi
        ' 2>/dev/null || echo "Offline|N/A|N/A|N/A")
        
        IFS='|' read -r status step progress purpose <<< "$s1_status"
        if [ "$status" = "Running" ]; then
            printf "  Status: ${GREEN}● Running${NC}  Step: %s  Progress: %.1f%%  Purpose: %s\n" "$step" "$progress" "$purpose"
        elif [ "$status" = "Stopped" ]; then
            echo -e "  Status: ${RED}● Stopped${NC}"
        else
            echo -e "  Status: ${YELLOW}● Offline${NC}"
        fi
        echo ""
        
        # Run 4.4 (服务器2)
        echo -e "${GREEN}▶ Run 4.4 (Server 2 - High Exploration)${NC}"
        local s2_status=$(ssh -o ConnectTimeout=3 "$SERVER2_HOST" '
            if pgrep -f "run_4_4_optimized" > /dev/null; then
                cat /opt/moss/experiments/run_4_4_status.json 2>/dev/null | python3 -c "import json,sys;d=json.load(sys.stdin);print(f\"Running|{d[\"step\"]}|{d[\"progress\"]*100:.1f}|{d[\"purpose\"][\"dominant\"]}|{d[\"metrics\"][\"exp_rate\"]}\")" 2>/dev/null || echo "Running|N/A|N/A|N/A|N/A"
            else
                echo "Stopped|N/A|N/A|N/A|N/A"
            fi
        ' 2>/dev/null || echo "Offline|N/A|N/A|N/A|N/A")
        
        IFS='|' read -r status step progress purpose exp_rate <<< "$s2_status"
        if [ "$status" = "Running" ]; then
            printf "  Status: ${GREEN}● Running${NC}  Step: %s  Progress: %.1f%%  Purpose: %s  ExpRate: %.1f%%\n" "$step" "$progress" "$purpose" "$(echo "$exp_rate * 100" | bc 2>/dev/null || echo "N/A")"
        elif [ "$status" = "Stopped" ]; then
            echo -e "  Status: ${RED}● Stopped${NC}"
        else
            echo -e "  Status: ${YELLOW}● Offline${NC}"
        fi
        
        echo ""
        echo -e "${CYAN}Press Ctrl+C to exit. Refreshing every 30 seconds...${NC}"
        
        sleep 30
    done
}

#===============================================================================
# 2. 飞书通知 (Feishu Notification)
#===============================================================================
feishu_notify() {
    if [ -z "$FEISHU_WEBHOOK" ]; then
        echo "Error: FEISHU_WEBHOOK not set"
        return 1
    fi
    
    local message="$1"
    local title="${2:-MOSS Experiment Alert}"
    
    curl -s -X POST "$FEISHU_WEBHOOK" \
        -H 'Content-Type: application/json' \
        -d "{
            \"msg_type\": \"interactive\",
            \"card\": {
                \"header\": {
                    \"title\": {\"tag\": \"plain_text\", \"content\": \"$title\"},
                    \"template\": \"blue\"
                },
                \"elements\": [
                    {\"tag\": \"div\", \"text\": {\"tag\": \"lark_md\", \"content\": \"$message\"}}
                ]
            }
        }" > /dev/null 2>&1
}

#===============================================================================
# 3. 自动告警检查 (Auto Alert)
#===============================================================================
check_alerts() {
    local alerts=()
    
    # 检查Run 4.2
    if ! pgrep -f "run_4_2_resume" > /dev/null 2>&1; then
        alerts+=("⚠️ Run 4.2 STOPPED on current server")
    fi
    
    # 检查服务器1
    if ! ssh -o ConnectTimeout=3 "$SERVER1_HOST" "pgrep -f run_4_3_optimized" > /dev/null 2>&1; then
        alerts+=("⚠️ Run 4.3 STOPPED on Server 1")
    fi
    
    # 检查服务器2
    if ! ssh -o ConnectTimeout=3 "$SERVER2_HOST" "pgrep -f run_4_4_optimized" > /dev/null 2>&1; then
        alerts+=("⚠️ Run 4.4 STOPPED on Server 2")
    fi
    
    # 如果有告警，发送通知
    if [ ${#alerts[@]} -gt 0 ]; then
        local message="$(printf '%s\\n' "${alerts[@]}")"
        echo "$message"
        
        if [ -n "$FEISHU_WEBHOOK" ]; then
            feishu_notify "$message" "🚨 MOSS Experiment Alert"
        fi
        
        return 1
    fi
    
    echo "✅ All experiments running normally"
    return 0
}

#===============================================================================
# 4. 定时报告 (Scheduled Report)
#===============================================================================
generate_report() {
    local report_file="/tmp/moss_report_$(date +%Y%m%d_%H%M).txt"
    
    {
        echo "MOSS Experiment Report - $(date)"
        echo "================================"
        echo ""
        
        # Run 4.2
        echo "Run 4.2 (Current Server):"
        if [ -f /workspace/projects/moss/experiments/run_4_2_status.json ]; then
            cat /workspace/projects/moss/experiments/run_4_2_status.json | python3 -m json.tool 2>/dev/null || cat /workspace/projects/moss/experiments/run_4_2_status.json
        fi
        echo ""
        
        # Run 4.3
        echo "Run 4.3 (Server 1):"
        ssh -o ConnectTimeout=5 "$SERVER1_HOST" "cat ~/moss/experiments/run_4_3_status.json 2>/dev/null | python3 -m json.tool" 2>/dev/null || echo "  Unable to fetch"
        echo ""
        
        # Run 4.4
        echo "Run 4.4 (Server 2):"
        ssh -o ConnectTimeout=5 "$SERVER2_HOST" "cat /opt/moss/experiments/run_4_4_status.json 2>/dev/null | python3 -m json.tool" 2>/dev/null || echo "  Unable to fetch"
        
    } > "$report_file"
    
    echo "Report saved to: $report_file"
    cat "$report_file"
}

#===============================================================================
# 5. 数据同步 (Data Sync)
#===============================================================================
sync_data() {
    local sync_dir="${1:-/workspace/projects/moss/remote_results}"
    mkdir -p "$sync_dir"
    
    echo "Syncing experiment data..."
    
    # Server 1
    scp "$SERVER1_HOST:~/moss/experiments/run_4_3_status.json" "$sync_dir/" 2>/dev/null && echo "✅ Server 1 status synced"
    scp "$SERVER1_HOST:~/moss/experiments/run_4_3_actions.jsonl" "$sync_dir/" 2>/dev/null && echo "✅ Server 1 actions synced"
    
    # Server 2
    scp "$SERVER2_HOST:/opt/moss/experiments/run_4_4_status.json" "$sync_dir/" 2>/dev/null && echo "✅ Server 2 status synced"
    scp "$SERVER2_HOST:/opt/moss/experiments/run_4_4_actions.jsonl" "$sync_dir/" 2>/dev/null && echo "✅ Server 2 actions synced"
    
    echo "Sync complete. Data in: $sync_dir"
}

#===============================================================================
# 6. 设置定时监控 (Cron Setup)
#===============================================================================
setup_cron() {
    local script_path="$(realpath "$0")"
    
    # 添加每30分钟检查
    (crontab -l 2>/dev/null; echo "*/30 * * * * $script_path alert >> /var/log/moss_monitor.log 2>&1") | crontab -
    
    # 添加每小时报告
    (crontab -l 2>/dev/null; echo "0 * * * * $script_path report >> /var/log/moss_report.log 2>&1") | crontab -
    
    echo "Cron jobs added:"
    crontab -l | grep moss_monitor
}

#===============================================================================
# Main
#===============================================================================
show_help() {
    cat << EOF
MOSS Experiment Monitor - Advanced Monitoring Tool

Usage:
  ./monitor_advanced.sh [command]

Commands:
  dashboard     - Live real-time dashboard (Ctrl+C to exit)
  alert         - Check for alerts and send notifications
  report        - Generate full status report
  sync [dir]    - Sync remote data to local directory
  cron          - Setup automatic monitoring (cron)
  notify "msg"  - Send test notification to Feishu
  help          - Show this help

Environment:
  FEISHU_WEBHOOK  - Feishu bot webhook URL for notifications
  SERVER1_HOST    - SSH host for Server 1
  SERVER2_HOST    - SSH host for Server 2

Examples:
  # Live dashboard
  ./monitor_advanced.sh dashboard

  # Check alerts (for cron)
  ./monitor_advanced.sh alert

  # Sync data every hour
  0 * * * * /path/to/monitor_advanced.sh sync

  # Setup automatic monitoring
  ./monitor_advanced.sh cron
EOF
}

case "${1:-dashboard}" in
    dashboard|live)
        live_dashboard
        ;;
    alert|check)
        check_alerts
        ;;
    report)
        generate_report
        ;;
    sync|download)
        sync_data "$2"
        ;;
    cron|schedule)
        setup_cron
        ;;
    notify|test)
        feishu_notify "Test notification from MOSS Monitor" "🧪 Test"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
