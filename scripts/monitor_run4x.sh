#!/bin/bash
# Monitor Run 4.x Extended Progress

echo "📊 Run 4.x Extended - Progress Monitor"
echo "========================================"
echo ""

LOG_FILE="/workspace/projects/moss/experiments/run_4_x_extended.log"
RESULTS_DIR="/workspace/projects/moss/experiments/run_4_x_extended"

# 检查进程
if pgrep -f "run_4_x_extended.py" > /dev/null; then
    echo "✅ Process is RUNNING"
    echo "   PID: $(pgrep -f "run_4_x_extended.py")"
else
    echo "⏹️  Process is NOT RUNNING"
fi

echo ""

# 显示最后几行日志
if [ -f "$LOG_FILE" ]; then
    echo "📄 Last 10 lines of log:"
    echo "----------------------------------------"
    tail -10 "$LOG_FILE"
    echo ""
fi

# 检查结果文件
if [ -d "$RESULTS_DIR" ]; then
    echo "📁 Results directory: $RESULTS_DIR"
    
    if [ -f "$RESULTS_DIR/analysis.json" ]; then
        echo ""
        echo "✅ Analysis file exists"
        
        # 解析关键指标
        echo ""
        echo "📈 Key Results:"
        python3 << EOF
import json
try:
    with open('$RESULTS_DIR/analysis.json') as f:
        data = json.load(f)
    print(f"  Total Runs: {data.get('total_runs', 'N/A')}")
    print(f"  Influence Rate: {data.get('influence_rate', 0):.1%}")
    print(f"  95% CI: [{data.get('ci_95_lower', 0):.1%}, {data.get('ci_95_upper', 0):.1%}]")
    if data.get('influence_rate', 0) > 0.7:
        print("  ✅ INFLUENCE ATTRACTOR VALIDATED")
    else:
        print("  ⏳ Still collecting data...")
except Exception as e:
    print(f"  Error reading analysis: {e}")
EOF
    else
        echo "⏳ Results not yet available"
    fi
fi

echo ""
echo "========================================"
echo "Monitor command: ./scripts/monitor_run4x.sh"
