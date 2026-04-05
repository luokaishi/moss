#!/bin/bash
cd /home/admin/.openclaw/workspace
python3 experiments/batch_validation_n50.py > oef_real_data/batch_validation_n50/experiment.log 2>&1 &
echo $! > /tmp/batch_validation.pid
echo "批量验证实验已启动，PID: $(cat /tmp/batch_validation.pid)"
