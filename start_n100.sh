#!/bin/bash
cd /home/admin/.openclaw/workspace
python3 experiments/batch_validation_n50.py 2>&1 | sed 's/50/100/g' > oef_real_data/batch_validation_n100/experiment.log 2>&1 &
echo $! > /tmp/batch_n100.pid
echo "N=100验证实验已启动，PID: $(cat /tmp/batch_n100.pid)"
