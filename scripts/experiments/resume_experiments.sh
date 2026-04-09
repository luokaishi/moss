#!/bin/bash
# MOSS Run 4.3/4.4 Resume Script
# 恢复并后台运行实验

cd /workspace/projects/moss

echo "========================================"
echo "MOSS Experiment Resume"
echo "Date: $(date)"
echo "========================================"
echo ""

# Check checkpoints
echo "【检查点状态】"
if [ -f "experiments/.checkpoints_run4_3/checkpoint_00700000.json" ]; then
    echo "✅ Run 4.3: Found checkpoint at step 700,000"
else
    echo "⚠️ Run 4.3: No checkpoint found"
fi

if [ -f "experiments/.checkpoints_run4_4/checkpoint_00680000.json" ]; then
    echo "✅ Run 4.4: Found checkpoint at step 680,000"
else
    echo "⚠️ Run 4.4: No checkpoint found"
fi
echo ""

# Kill any existing processes
echo "【清理旧进程】"
pkill -f "run_4_3" 2>/dev/null && echo "Killed old run_4_3 processes"
pkill -f "run_4_4" 2>/dev/null && echo "Killed old run_4_4 processes"
sleep 1
echo ""

# Start Run 4.3
echo "【启动 Run 4.3】"
echo "恢复自 Step 700,000，继续到 2,880,000"
nohup python3 -u experiments/run_4_3_resumed.py > experiments/run_4_3_resumed.out 2>&1 &
PID_43=$!
echo "PID: $PID_43"
echo "Log: experiments/run_4_3_resumed.out"
echo ""

# Start Run 4.4
echo "【启动 Run 4.4】"
echo "恢复自 Step 680,000，继续到 2,880,000"
nohup python3 -u experiments/run_4_4_resumed.py > experiments/run_4_4_resumed.out 2>&1 &
PID_44=$!
echo "PID: $PID_44"
echo "Log: experiments/run_4_4_resumed.out"
echo ""

# Save PIDs
echo "$PID_43" > /tmp/moss_run4_3.pid
echo "$PID_44" > /tmp/moss_run4_4.pid

# Wait a moment and verify
sleep 2
echo "【进程验证】"
ps aux | grep -E "(run_4_3|run_4_4)" | grep -v grep | grep -v resume
echo ""

echo "========================================"
echo "✅ 实验已恢复并后台运行"
echo "========================================"
echo ""
echo "监控命令:"
echo "  tail -f experiments/run_4_3_resumed.out"
echo "  tail -f experiments/run_4_4_resumed.out"
echo ""
echo "状态检查:"
echo "  cat experiments/run_4_3_status.json"
echo "  cat experiments/run_4_4_status.json"
echo ""
echo "停止实验:"
echo "  kill \$(cat /tmp/moss_run4_3.pid)"
echo "  kill \$(cat /tmp/moss_run4_4.pid)"
