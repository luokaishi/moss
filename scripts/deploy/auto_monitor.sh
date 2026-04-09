#!/bin/bash
# MOSS Local Experiment Auto-Monitor
# 每30分钟自动检查并记录状态

LOG_FILE="/workspace/projects/moss/monitoring.log"
STATUS_DIR="/workspace/projects/moss/status_snapshots"

mkdir -p "$STATUS_DIR"

echo "========================================" >> "$LOG_FILE"
echo "MOSS Monitor - $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

cd /workspace/projects/moss

# Check processes
echo "【进程状态】" >> "$LOG_FILE"
ps aux | grep "run_4_" | grep -v grep >> "$LOG_FILE" 2>&1 || echo "No processes found" >> "$LOG_FILE"

# Check Run 4.3
echo "" >> "$LOG_FILE"
echo "【Run 4.3 状态】" >> "$LOG_FILE"
if [ -f experiments/run_4_3_status.json ]; then
    python3 << 'PYEOF' >> "$LOG_FILE" 2>&1
import json
try:
    with open('experiments/run_4_3_status.json') as f:
        d = json.load(f)
    print(f"Step: {d['step']:,} / 2,880,000 ({d['progress']*100:.1f}%)")
    print(f"Phase: Normal/Threat/Novelty/Social")
    print(f"Purpose: {d['purpose']['dominant']}")
    print(f"Runtime: {d['elapsed_hours']:.1f} hours")
    print(f"Success Rate: {d['metrics']['success_rate']:.1%}")
    
    # Save snapshot
    import time
    with open(f'status_snapshots/run_4_3_{int(time.time())}.json', 'w') as f:
        json.dump(d, f)
        
    # Check completion
    if d['progress'] >= 1.0:
        print("🎉 RUN 4.3 COMPLETED!")
except Exception as e:
    print(f"Error: {e}")
PYEOF
else
    echo "Status file not found" >> "$LOG_FILE"
fi

# Check Run 4.4
echo "" >> "$LOG_FILE"
echo "【Run 4.4 状态】" >> "$LOG_FILE"
if [ -f experiments/run_4_4_status.json ]; then
    python3 << 'PYEOF' >> "$LOG_FILE" 2>&1
import json
try:
    with open('experiments/run_4_4_status.json') as f:
        d = json.load(f)
    print(f"Step: {d['step']:,} / 2,880,000 ({d['progress']*100:.1f}%)")
    print(f"Purpose: {d['purpose']['dominant']}")
    print(f"Exp Rate: {d['metrics']['exp_rate']:.1%}")
    print(f"Runtime: {d['elapsed_hours']:.1f} hours")
    
    # Save snapshot
    import time
    with open(f'status_snapshots/run_4_4_{int(time.time())}.json', 'w') as f:
        json.dump(d, f)
        
    # Check completion
    if d['progress'] >= 1.0:
        print("🎉 RUN 4.4 COMPLETED!")
except Exception as e:
    print(f"Error: {e}")
PYEOF
else
    echo "Status file not found" >> "$LOG_FILE"
fi

# Memory check
echo "" >> "$LOG_FILE"
echo "【系统资源】" >> "$LOG_FILE"
free -h >> "$LOG_FILE"

echo "" >> "$LOG_FILE"
echo "----------------------------------------" >> "$LOG_FILE"
