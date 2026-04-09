#!/bin/bash
# launch_neurips_validation.sh - Launch 10 parallel experiments for NeurIPS 2026

cd /workspace/projects/moss/v2/experiments
mkdir -p neurips_validation

echo "=== Launching NeurIPS 2026 Extended Validation ==="
echo "Start time: $(date)"
echo ""

# Define seeds (different from first 15)
SEEDS=(2026 3015 4096 5182 6273 7384 8495 9506 10617 11728)
START_INDEX=16

for i in {0..9}; do
    IDX=$((START_INDEX + i))
    SEED=${SEEDS[$i]}
    ID="neurips_val_$(printf "%02d" $IDX)"
    LOG="neurips_validation/instance_$(printf "%02d" $IDX)_seed${SEED}.log"
    
    echo "Starting instance $IDX (seed: $SEED)"
    
    nohup python3 phase1_single_agent.py \
        --duration 6.0 \
        --id "$ID" \
        > "$LOG" 2>&1 &
    
    echo "  PID: $!"
    echo "  Log: $LOG"
    
    sleep 2  # Small delay to avoid resource spike
done

echo ""
echo "=== All instances launched ==="
echo "Monitor with: ps aux | grep phase1_single_agent"
echo "View logs: tail -f neurips_validation/instance_*.log"
echo ""
echo "Estimated completion: ~6 hours"
