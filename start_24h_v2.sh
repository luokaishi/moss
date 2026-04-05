#!/bin/bash
cd /home/admin/.openclaw/workspace
mkdir -p oef_real_data/oef_24h_validation_v2
python3 experiments/oef_24h_validation.py > oef_real_data/oef_24h_validation_v2/experiment.log 2>&1 &
echo $! > /tmp/oef_24h_v2.pid
echo "24小时验证实验已启动，PID: $(cat /tmp/oef_24h_v2.pid)"
echo "预计完成时间: $(date -d '+24 hours' '+%Y-%m-%d %H:%M')"
