#!/bin/bash
cd /home/admin/.openclaw/workspace
mkdir -p oef_real_data/batch_validation_n100
python3 experiments/batch_validation_n100.py > oef_real_data/batch_validation_n100/experiment.log 2>&1 &
echo $! > /tmp/batch_n100.pid
echo "N=100验证实验已重新启动，PID: $(cat /tmp/batch_n100.pid)"
