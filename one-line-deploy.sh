#!/bin/bash
# MOSS One-Line Deploy for Server 43.156.104.179
# Run this on the target server as root

set -e

echo "=========================================="
echo "MOSS Deployment - One Line Install"
echo "=========================================="

# Check if moss-deploy-final.tar.gz exists in /root
if [ ! -f "/root/moss-deploy-final.tar.gz" ]; then
    echo "Error: moss-deploy-final.tar.gz not found in /root"
    echo "Please upload the file first:"
    echo "  scp -i ~/.ssh/id_rsa moss-deploy-final.tar.gz root@43.156.104.179:/root/"
    exit 1
fi

cd /root
echo "[1/5] Extracting MOSS..."
tar -xzf moss-deploy-final.tar.gz

cd moss
echo "[2/5] Installing dependencies..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv

echo "[3/5] Setting up environment..."
mkdir -p /opt/moss
cp -r . /opt/moss/
cd /opt/moss

python3 -m venv venv
source venv/bin/activate
pip install -q numpy flask requests psutil

echo "[4/5] Creating systemd service..."
cat > /etc/systemd/system/moss.service << 'EOF'
[Unit]
Description=MOSS Multi-Objective Self-Driven System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/moss
Environment=PYTHONPATH=/opt/moss
ExecStart=/opt/moss/venv/bin/python /opt/moss/agents/moss_agent.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/moss.log
StandardError=append:/var/log/moss.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable moss

echo "[5/5] Starting MOSS..."
touch /var/log/moss.log
systemctl start moss

echo ""
echo "=========================================="
echo "MOSS Deployment Complete!"
echo "=========================================="
echo ""
echo "Status check:"
echo "  systemctl status moss"
echo ""
echo "View logs:"
echo "  tail -f /var/log/moss.log"
echo ""
echo "Stop/Start:"
echo "  systemctl stop moss"
echo "  systemctl start moss"
echo ""
echo "=========================================="
