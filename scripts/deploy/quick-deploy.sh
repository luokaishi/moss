#!/bin/bash
# MOSS Quick Local Deploy Script
# Run this in your local moss directory

echo "=========================================="
echo "MOSS Quick Local Deploy"
echo "=========================================="

# Check directory
if [ ! -f "moss/agents/moss_agent.py" ]; then
    echo "Error: Please run from moss project root"
    exit 1
fi

# Install dependencies
echo "[1/3] Installing dependencies..."
pip install -q numpy flask requests psutil 2>/dev/null || pip install numpy flask requests psutil

# Create directories
echo "[2/3] Setting up directories..."
mkdir -p logs data results

# Test
echo "[3/3] Testing MOSS..."
python3 -c "
import sys
sys.path.insert(0, '.')
from moss.agents.moss_agent import MOSSAgent
agent = MOSSAgent(agent_id='quick_test')
result = agent.step()
print(f'✓ MOSS ready: {result[\"state\"]} state')
"

echo ""
echo "=========================================="
echo "MOSS Ready!"
echo "=========================================="
echo ""
echo "Quick start:"
echo "  python sandbox/experiment1.py"
echo ""
echo "Long-term:"
echo "  bash start_longterm_experiment.sh"
echo ""
echo "=========================================="
