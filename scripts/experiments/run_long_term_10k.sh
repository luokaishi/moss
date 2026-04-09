#!/bin/bash
# Run 10,000 step long-term simulation in background

cd /workspace/projects/moss
nohup python -c "
import sys
sys.path.insert(0, 'v3')
from experiments.long_term_simulation import LongTermSimulation
import json
from datetime import datetime

print('='*70)
print('🚀 MOSS v3.1 - 10,000 Step Long-term Simulation')
print('='*70)
print(f'Started: {datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")}')
print('This will take approximately 30-60 minutes...')
print('='*70)

sim = LongTermSimulation(n_agents=10)
results = sim.run_long_term(
    n_steps=10000,
    checkpoint_dir='v3/experiments/long_term_10k_checkpoints'
)

print('\n' + '='*70)
print('✅ 10,000 STEP SIMULATION COMPLETE')
print('='*70)
" > v3/experiments/long_term_10k_full.log 2>&1 &

echo "Background process started!"
echo "PID: $!"
echo "Monitor with: tail -f v3/experiments/long_term_10k_full.log"
