#!/bin/bash
#===============================================================================
# MOSS Remote Experiment Monitor
# 监控远程服务器上的Run 4.3和Run 4.4实验状态
#===============================================================================

set -e

# Server configuration
SERVER1_HOST="${SERVER1_HOST:-root@47.77.234.152}"
SERVER2_HOST="${SERVER2_HOST:-root@43.156.104.179}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

#===============================================================================
# Check Server 1 (Run 4.3)
#===============================================================================
check_server1() {
    log_header "🖥️  Server 1: Run 4.3 (Curiosity-dominant)"
    
    ssh -o ConnectTimeout=5 "$SERVER1_HOST" '
        cd /opt/moss 2>/dev/null || exit 1
        
        # Check process
        echo "📊 Process Status:"
        ps aux | grep "run_4_3" | grep -v grep | awk "{printf \"  PID: %s, CPU: %s%%, MEM: %s%%\n\", \$2, \$3, \$4}" || echo "  ⚠️ Process not running!"
        
        # Check memory
        echo ""
        echo "💾 Memory:"
        free -h | grep -E "(Mem|Swap)" | awk "{printf \"  %s: Total %s, Used %s, Free %s\n\", \$1, \$2, \$3, \$4}"
        
        # Check status file
        echo ""
        echo "📈 Experiment Status:"
        if [ -f experiments/run_4_3_status.json ]; then
            python3 -c "
import json
with open('experiments/run_4_3_status.json') as f:
    d = json.load(f)
    print(f\"  Step: {d[\"step\"]:,}\")
    print(f\"  Progress: {d[\"progress\"]*100:.1f}%\")
    print(f\"  Purpose: {d[\"purpose\"][\"dominant\"]}\")
    print(f\"  Success Rate: {d[\"metrics\"][\"success_rate\"]:.1%}\")
    print(f\"  Elapsed: {d[\"elapsed_hours\"]:.1f} hours\")
" 2>/dev/null || cat experiments/run_4_3_status.json | grep -E "(step|progress|dominant)" | head -5
        else
            echo "  ⏳ Status file not created yet"
        fi
        
        # Recent log
        echo ""
        echo "📝 Recent Log:"
        tail -3 experiments/run_4_3.out 2>/dev/null || echo "  No log yet"
    '
}

#===============================================================================
# Check Server 2 (Run 4.4)
#===============================================================================
check_server2() {
    log_header "🖥️  Server 2: Run 4.4 (High Exploration)"
    
    ssh -o ConnectTimeout=5 "$SERVER2_HOST" '
        cd /opt/moss 2>/dev/null || exit 1
        
        # Check process
        echo "📊 Process Status:"
        ps aux | grep "run_4_4" | grep -v grep | awk "{printf \"  PID: %s, CPU: %s%%, MEM: %s%%\n\", \$2, \$3, \$4}" || echo "  ⚠️ Process not running!"
        
        # Check memory
        echo ""
        echo "💾 Memory:"
        free -h | grep -E "(Mem|Swap)" | awk "{printf \"  %s: Total %s, Used %s, Free %s\n\", \$1, \$2, \$3, \$4}"
        
        # Check status file
        echo ""
        echo "📈 Experiment Status:"
        if [ -f experiments/run_4_4_status.json ]; then
            python3 -c "
import json
with open('experiments/run_4_4_status.json') as f:
    d = json.load(f)
    print(f\"  Step: {d[\"step\"]:,}\")
    print(f\"  Progress: {d[\"progress\"]*100:.1f}%\")
    print(f\"  Purpose: {d[\"purpose\"][\"dominant\"]}\")
    print(f\"  Exp Rate: {d[\"metrics\"][\"exp_rate\"]:.1%}\")
    print(f\"  Success Rate: {d[\"metrics\"][\"success_rate\"]:.1%}\")
    print(f\"  Elapsed: {d[\"elapsed_hours\"]:.1f} hours\")
" 2>/dev/null || cat experiments/run_4_4_status.json | grep -E "(step|progress|dominant)" | head -5
        else
            echo "  ⏳ Status file not created yet"
        fi
        
        # Recent log
        echo ""
        echo "📝 Recent Log:"
        tail -3 experiments/run_4_4.out 2>/dev/null || echo "  No log yet"
    '
}

#===============================================================================
# Quick Status (single line per server)
#===============================================================================
quick_status() {
    echo "Quick Status:"
    echo "-------------"
    
    # Server 1
    local s1_status=$(ssh -o ConnectTimeout=3 "$SERVER1_HOST" '
        cd /opt/moss 2>/dev/null || echo "NOT_DEPLOYED"
        if [ -f experiments/run_4_3_status.json ]; then
            python3 -c "import json; d=json.load(open(\"experiments/run_4_3_status.json\")); print(f\"{d[\"step\"]:,}|{d[\"progress\"]*100:.0f}%|{d[\"purpose\"][\"dominant\"][:4]}\")" 2>/dev/null
        else
            ps aux | grep -q "run_4_3" && echo "STARTING" || echo "NOT_RUNNING"
        fi
    ' 2>/dev/null || echo "OFFLINE")
    
    # Server 2
    local s2_status=$(ssh -o ConnectTimeout=3 "$SERVER2_HOST" '
        cd /opt/moss 2>/dev/null || echo "NOT_DEPLOYED"
        if [ -f experiments/run_4_4_status.json ]; then
            python3 -c "import json; d=json.load(open(\"experiments/run_4_4_status.json\")); print(f\"{d[\"step\"]:,}|{d[\"progress\"]*100:.0f}%|{d[\"purpose\"][\"dominant\"][:4]}\")" 2>/dev/null
        else
            ps aux | grep -q "run_4_4" && echo "STARTING" || echo "NOT_RUNNING"
        fi
    ' 2>/dev/null || echo "OFFLINE")
    
    printf "%-15s %s\n" "Server 1 (4.3):" "$s1_status"
    printf "%-15s %s\n" "Server 2 (4.4):" "$s2_status"
}

#===============================================================================
# Download Results
#===============================================================================
download_results() {
    log_info "Downloading experiment results..."
    
    mkdir -p /workspace/projects/moss/remote_results
    
    # Server 1
    log_info "Downloading from Server 1..."
    scp "$SERVER1_HOST:/opt/moss/experiments/run_4_3_status.json" \
        /workspace/projects/moss/remote_results/ 2>/dev/null || log_warn "Server 1 status.json not available"
    scp "$SERVER1_HOST:/opt/moss/experiments/run_4_3_actions.jsonl" \
        /workspace/projects/moss/remote_results/ 2>/dev/null || log_warn "Server 1 actions.jsonl not available"
    
    # Server 2
    log_info "Downloading from Server 2..."
    scp "$SERVER2_HOST:/opt/moss/experiments/run_4_4_status.json" \
        /workspace/projects/moss/remote_results/ 2>/dev/null || log_warn "Server 2 status.json not available"
    scp "$SERVER2_HOST:/opt/moss/experiments/run_4_4_actions.jsonl" \
        /workspace/projects/moss/remote_results/ 2>/dev/null || log_warn "Server 2 actions.jsonl not available"
    
    log_info "Download complete. Results in: /workspace/projects/moss/remote_results/"
}

#===============================================================================
# Main
#===============================================================================
show_help() {
    cat << EOF
MOSS Remote Monitor

Usage:
  ./monitor_remote.sh [command]

Commands:
  status      - Full status check of both servers [default]
  quick       - Quick one-line status
  download    - Download experiment results
  help        - Show this help

Environment:
  SERVER1_HOST - SSH host for Server 1 (default: root@47.77.234.152)
  SERVER2_HOST - SSH host for Server 2 (default: root@43.156.104.179)

Examples:
  ./monitor_remote.sh              # Full status
  ./monitor_remote.sh quick        # Quick check
  ./monitor_remote.sh download     # Download results
EOF
}

case "${1:-status}" in
    status|full)
        echo "MOSS Remote Experiment Monitor"
        echo "=============================="
        echo ""
        check_server1
        echo ""
        check_server2
        echo ""
        log_header "📋 Summary"
        quick_status
        ;;
    quick|q)
        quick_status
        ;;
    download|pull)
        download_results
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
