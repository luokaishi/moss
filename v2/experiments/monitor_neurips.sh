#!/bin/bash
# monitor_neurips_experiments.sh - Monitor NeurIPS validation experiments

echo "=== NeurIPS 2026 Extended Validation Monitor ==="
echo "Timestamp: $(date)"
echo ""

# Check tmux sessions
echo "Active tmux sessions:"
tmux ls 2>/dev/null || echo "  No active sessions"
echo ""

# Check output directory
OUTPUT_DIR="/workspace/projects/moss/v2/experiments/neurips_validation"
echo "Output directory: $OUTPUT_DIR"
if [ -d "$OUTPUT_DIR" ]; then
    echo "Files created:"
    ls -lh "$OUTPUT_DIR" 2>/dev/null | tail -20
    echo ""
    
    # Count completed results
    RESULT_COUNT=$(ls "$OUTPUT_DIR"/instance_*_result.json 2>/dev/null | wc -l)
    echo "Completed experiments: $RESULT_COUNT / 10"
else
    echo "  Directory not created yet"
fi

echo ""
echo "=== Recent logs (last 5 lines of each) ==="
for log in "$OUTPUT_DIR"/*.log; do
    if [ -f "$log" ]; then
        echo "--- $(basename $log) ---"
        tail -5 "$log" 2>/dev/null
        echo ""
    fi
done

echo ""
echo "=== Quick commands ==="
echo "Attach to session: tmux attach -t neurips_16"
echo "List all sessions: tmux ls"
echo "Kill session: tmux kill-session -t neurips_16"
echo "View full log: tail -f $OUTPUT_DIR/instance_16_seed2026.log"
