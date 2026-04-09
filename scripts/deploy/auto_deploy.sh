#!/bin/bash
# MOSS Auto-Deploy Script for Local Environment
# Run this in the moss project directory

set -e

echo "=============================================="
echo "MOSS Local Auto-Deploy Script"
echo "=============================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required"
    exit 1
fi

# Check if in correct directory
if [ ! -f "moss/agents/moss_agent.py" ]; then
    echo "Error: Please run from moss project root"
    exit 1
fi

# Install dependencies
echo "[1/3] Installing dependencies..."
pip install -q numpy flask requests psutil 2>&1 | grep -v "already satisfied" || true

# Create directories
echo "[2/3] Creating directory structure..."
mkdir -p logs
mkdir -p data
mkdir -p results

# Run basic test
echo "[3/3] Running basic test..."
python3 -c "
import sys
sys.path.insert(0, '.')
from moss.agents.moss_agent import MOSSAgent
print('Testing MOSS agent...')
agent = MOSSAgent(agent_id='deploy_test')
result = agent.step()
print(f'✓ Agent created: {agent.agent_id}')
print(f'✓ First action: {result[\"action\"]}')
print('✓ All systems operational')
"

echo ""
echo "=============================================="
echo "MOSS Local Setup Complete!"
echo "=============================================="
echo ""
echo "Available experiments:"
echo "  python sandbox/experiment1.py    # Multi-objective competition"
echo "  python sandbox/experiment2.py    # Evolutionary dynamics"
echo "  python sandbox/experiment3.py    # Social emergence"
echo "  python sandbox/experiment4_final.py  # Dynamic API adaptation"
echo "  python sandbox/experiment5_energy.py # Energy-driven evolution"
echo ""
echo "Long-term experiment:"
echo "  bash start_longterm_experiment.sh"
echo ""
echo "=============================================="
