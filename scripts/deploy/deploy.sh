#!/bin/bash
# MOSS Deploy Script for Ubuntu/Debian
# Run on target server as root or with sudo

set -e

echo "=========================================="
echo "MOSS Deployment Script"
echo "=========================================="

# Update system
echo "[1/6] Updating system packages..."
apt-get update -qq

# Install dependencies
echo "[2/6] Installing dependencies..."
apt-get install -y -qq python3 python3-pip python3-venv git curl

# Create moss user (optional but recommended)
if ! id -u moss &>/dev/null; then
    echo "[3/6] Creating moss user..."
    useradd -m -s /bin/bash moss
fi

# Setup directory
MOSS_DIR="/opt/moss"
echo "[4/6] Setting up MOSS directory at $MOSS_DIR..."
mkdir -p $MOSS_DIR
cd $MOSS_DIR

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -q numpy flask requests psutil

# Create MOSS structure
echo "[5/6] Creating MOSS structure..."
mkdir -p moss/{core,integration,agents,sandbox,docs,tests}

# Note: The actual code files need to be copied from your workspace
# For now, we'll create placeholder instructions
cat > $MOSS_DIR/README.txt << 'EOF'
MOSS Deployment
===============

1. Copy the following files from your workspace to this server:
   - moss/core/objectives.py
   - moss/integration/allocator.py
   - moss/agents/moss_agent.py
   - moss/tests/test_basic.py
   - moss/sandbox/experiment*.py

2. Start the MOSS agent:
   cd /opt/moss
   source venv/bin/activate
   python moss/agents/moss_agent.py

3. For continuous running, use systemd service (see moss.service)
EOF

# Create systemd service file
cat > /etc/systemd/system/moss.service << 'EOF'
[Unit]
Description=MOSS Multi-Objective Self-Driven System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/moss
Environment=PYTHONPATH=/opt/moss
ExecStart=/opt/moss/venv/bin/python /opt/moss/moss/agents/moss_agent.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create monitoring script
cat > $MOSS_DIR/monitor.py << 'EOF'
#!/usr/bin/env python3
"""Simple MOSS monitoring script"""
import json
import time
import sys
sys.path.insert(0, '/opt/moss')

from moss.agents.moss_agent import MOSSAgent

if __name__ == "__main__":
    agent = MOSSAgent(agent_id="moss_server_001")
    print(f"MOSS Agent started: {agent.agent_id}")
    
    try:
        while True:
            result = agent.step()
            report = agent.get_report()
            
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
                  f"State: {report['allocator_stats']['current_state']}, "
                  f"Decisions: {report['stats']['total_decisions']}")
            
            # Save state periodically
            if report['stats']['total_decisions'] % 100 == 0:
                agent.save_state('/opt/moss/state.json')
            
            time.sleep(60)  # Run decision loop every 60 seconds
            
    except KeyboardInterrupt:
        print("\nShutting down...")
        agent.save_state('/opt/moss/state.json')
EOF

chmod +x $MOSS_DIR/monitor.py

echo "[6/6] Setup complete!"
echo ""
echo "Next steps:"
echo "1. Copy MOSS code files to $MOSS_DIR/moss/"
echo "2. Start with: python3 /opt/moss/monitor.py"
echo "3. Or enable service: systemctl enable --now moss"
echo ""
echo "=========================================="
