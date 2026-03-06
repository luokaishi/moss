#!/bin/bash
# MOSS One-Line Deploy for Local Environment
# Run this in your local workspace

set -e

echo "=========================================="
echo "MOSS Local Deployment"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "moss/agents/moss_agent.py" ]; then
    echo "Error: Please run this script from the moss project root"
    echo "Expected: moss/agents/moss_agent.py"
    exit 1
fi

echo "[1/3] Checking dependencies..."
python3 -c "import numpy, flask, requests, psutil" 2>/dev/null || {
    echo "Installing dependencies..."
    pip install numpy flask requests psutil
}

echo "[2/3] Setting up local environment..."
mkdir -p logs
mkdir -p data

echo "[3/3] Running basic test..."
python3 -c "
import sys
sys.path.insert(0, '.')
from moss.agents.moss_agent import MOSSAgent
agent = MOSSAgent(agent_id='local_test')
result = agent.step()
print(f'✓ MOSS agent test passed: {result[\"action\"]}')
"

echo ""
echo "=========================================="
echo "MOSS Local Setup Complete!"
echo "=========================================="
echo ""
echo "Run experiments:"
echo "  python sandbox/experiment1.py"
echo "  python sandbox/experiment2.py"
echo "  python sandbox/experiment3.py"
echo ""
echo "Start long-term experiment:"
echo "  bash start_longterm_experiment.sh"
echo ""
echo "Check status:"
echo "  bash check_experiment.sh"
echo ""
echo "=========================================="
