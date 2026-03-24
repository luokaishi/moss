#!/bin/bash
# MOSS Background Monitor - Runs continuously with 30min intervals

LOG_FILE="/workspace/projects/moss/monitoring.log"
STATUS_DIR="/workspace/projects/moss/status_snapshots"

mkdir -p "$STATUS_DIR"

echo "Starting MOSS Background Monitor..."
echo "Log file: $LOG_FILE"
echo "Monitoring interval: 30 minutes"
echo "Press Ctrl+C to stop"
echo ""

while true; do
    {
        echo "========================================"
        echo "MOSS Monitor - $(date '+%Y-%m-%d %H:%M:%S')"
        echo "========================================"
        
        cd /workspace/projects/moss
        
        # Check processes
        echo "【进程状态】"
        ps aux | grep "run_4_" | grep -v grep || echo "No processes found"
        
        # Check Run 4.3
        echo ""
        echo "【Run 4.3 状态】"
        if [ -f experiments/run_4_3_status.json ]; then
            python3 << 'PYEOF' 2>/dev/null
import json, time
try:
    with open('experiments/run_4_3_status.json') as f:
        d = json.load(f)
    print(f"Step: {d['step']:,} / 2,880,000 ({d['progress']*100:.1f}%)")
    print(f"Purpose: {d['purpose']['dominant']}")
    print(f"Runtime: {d['elapsed_hours']:.1f} hours")
    
    # Save snapshot
    with open(f'status_snapshots/run_4_3_{int(time.time())}.json', 'w') as f:
        json.dump(d, f)
        
    if d['progress'] >= 1.0:
        print("🎉 RUN 4.3 COMPLETED!")
except Exception as e:
    print(f"Error: {e}")
PYEOF
        else
            echo "Status file not found"
        fi
        
        # Check Run 4.4
        echo ""
        echo "【Run 4.4 状态】"
        if [ -f experiments/run_4_4_status.json ]; then
            python3 << 'PYEOF' 2>/dev/null
import json, time
try:
    with open('experiments/run_4_4_status.json') as f:
        d = json.load(f)
    print(f"Step: {d['step']:,} / 2,880,000 ({d['progress']*100:.1f}%)")
    print(f"Purpose: {d['purpose']['dominant']}")
    print(f"Exp Rate: {d['metrics']['exp_rate']:.1%}")
    print(f"Runtime: {d['elapsed_hours']:.1f} hours")
    
    # Save snapshot
    with open(f'status_snapshots/run_4_4_{int(time.time())}.json', 'w') as f:
        json.dump(d, f)
        
    if d['progress'] >= 1.0:
        print("🎉 RUN 4.4 COMPLETED!")
except Exception as e:
    print(f"Error: {e}")
PYEOF
        else
            echo "Status file not found"
        fi
        
        # Memory check
        echo ""
        echo "【系统资源】"
        free -h | grep -E "(Mem|Swap)"
        
        echo ""
        echo "Next check in 30 minutes..."
        echo ""
    } >> "$LOG_FILE" 2>&1
    
    # Also print to console
    tail -20 "$LOG_FILE"
    
    # Sleep 30 minutes
    sleep 1800
done
