#!/bin/bash
# MOSS Auto-Deploy Script for Server 43.156.104.179
# This script automates the deployment process
# Usage: Save this as deploy_moss.sh and run on the target server

set -e

echo "=============================================="
echo "MOSS Auto-Deploy Script"
echo "Target: 43.156.104.179"
echo "=============================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Update system
echo "[1/8] Updating system packages..."
apt-get update -qq > /dev/null 2>&1

# Install Python and dependencies
echo "[2/8] Installing Python and dependencies..."
apt-get install -y -qq python3 python3-pip python3-venv git curl > /dev/null 2>&1

# Create MOSS directory
echo "[3/8] Creating MOSS directory structure..."
MOSS_DIR="/opt/moss"
mkdir -p $MOSS_DIR/{core,integration,agents,sandbox,docs,tests}
cd $MOSS_DIR

# Create virtual environment
echo "[4/8] Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python packages
echo "[5/8] Installing Python packages..."
pip install -q numpy flask requests psutil 2>&1 | grep -v "already satisfied" || true

# Create __init__ files
touch $MOSS_DIR/moss/__init__.py
touch $MOSS_DIR/moss/core/__init__.py
touch $MOSS_DIR/moss/integration/__init__.py
touch $MOSS_DIR/moss/agents/__init__.py

# Create placeholder files (to be filled with actual code)
echo "[6/8] Creating placeholder files..."

# Note: The actual code files need to be uploaded separately
cat > $MOSS_DIR/README.txt << 'EOF'
MOSS Deployment - Action Required
=================================

The deployment structure is ready. Now you need to upload the actual code files:

1. Upload these files from your local machine:
   - moss/core/objectives.py
   - moss/integration/allocator.py
   - moss/agents/moss_agent.py
   - moss/tests/test_basic.py

2. Or use git to clone the repository (when available):
   git clone https://github.com/yourusername/moss.git

3. Then start the agent:
   cd /opt/moss
   source venv/bin/activate
   python moss/agents/moss_agent.py
EOF

# Create monitoring script
cat > $MOSS_DIR/monitor.py << 'EOF'
#!/usr/bin/env python3
"""MOSS Monitoring Script"""
import sys
import time
sys.path.insert(0, '/opt/moss')

try:
    from moss.agents.moss_agent import MOSSAgent
    
    agent = MOSSAgent(agent_id="moss_server_001")
    print(f"MOSS Agent started: {agent.agent_id}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    while True:
        try:
            result = agent.step()
            report = agent.get_report()
            state = report['allocator_stats']['current_state']
            decisions = report['stats']['total_decisions']
            
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{timestamp}] State: {state}, Decisions: {decisions}")
            
            # Save state every 100 decisions
            if decisions % 100 == 0:
                agent.save_state('/opt/moss/state.json')
                print(f"[{timestamp}] State saved")
            
            time.sleep(60)  # Run every 60 seconds
            
        except KeyboardInterrupt:
            print("\nShutting down...")
            agent.save_state('/opt/moss/state.json')
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)
            
except ImportError as e:
    print(f"Error: MOSS code not found. Please upload the code files first.")
    print(f"Details: {e}")
    sys.exit(1)
EOF

chmod +x $MOSS_DIR/monitor.py

# Create systemd service
echo "[7/8] Creating systemd service..."
cat > /etc/systemd/system/moss.service << 'EOF'
[Unit]
Description=MOSS Multi-Objective Self-Driven System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/moss
Environment=PYTHONPATH=/opt/moss
Environment=MOSS_AGENT_ID=moss_server_001
ExecStart=/opt/moss/venv/bin/python /opt/moss/monitor.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/moss.log
StandardError=append:/var/log/moss.log

[Install]
WantedBy=multi-user.target
EOF

# Create log directory
touch /var/log/moss.log
chmod 644 /var/log/moss.log

# Create status check script
cat > $MOSS_DIR/check.sh << 'EOF'
#!/bin/bash
echo "MOSS Status Check"
echo "================="
echo ""
echo "Service status:"
systemctl is-active moss 2>/dev/null && echo "  ✓ Running" || echo "  ✗ Not running"
echo ""
echo "Recent logs:"
tail -n 20 /var/log/moss.log 2>/dev/null || echo "  No logs yet"
echo ""
echo "Process:"
ps aux | grep moss | grep -v grep || echo "  No process found"
echo ""
echo "To start: sudo systemctl start moss"
echo "To stop:  sudo systemctl stop moss"
echo "To view logs: sudo tail -f /var/log/moss.log"
EOF

chmod +x $MOSS_DIR/check.sh

# Enable service (but don't start yet - need code first)
echo "[8/8] Configuring systemd..."
systemctl daemon-reload
systemctl enable moss

echo ""
echo "=============================================="
echo "MOSS Deployment Structure Ready!"
echo "=============================================="
echo ""
echo "Next steps:"
echo "1. Upload MOSS code files to $MOSS_DIR/moss/"
echo "2. Start the service: sudo systemctl start moss"
echo "3. Check status: sudo /opt/moss/check.sh"
echo "4. View logs: sudo tail -f /var/log/moss.log"
echo ""
echo "Directory structure:"
echo "  $MOSS_DIR/"
echo "  ├── moss/          (upload code here)"
echo "  ├── venv/          (Python environment)"
echo "  ├── monitor.py     (monitoring script)"
echo "  ├── check.sh       (status checker)"
echo "  └── state.json     (saved state)"
echo ""
echo "=============================================="
