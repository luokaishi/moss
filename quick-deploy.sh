#!/bin/bash
# MOSS One-Line Deploy Script
# Run this on your server (43.156.104.179)

echo "=========================================="
echo "MOSS Quick Deploy"
echo "=========================================="

# Create temp directory
TEMP_DIR=$(mktemp -d)
cd $TEMP_DIR

# Download MOSS package
echo "[1/5] Downloading MOSS..."
if command -v wget &> /dev/null; then
    wget -q https://raw.githubusercontent.com/moss-ai/moss/main/moss-deploy.tar.gz -O moss-deploy.tar.gz || \
    echo "Note: Download URL placeholder - please upload moss-deploy.tar.gz manually"
elif command -v curl &> /dev/null; then
    curl -sL https://raw.githubusercontent.com/moss-ai/moss/main/moss-deploy.tar.gz -o moss-deploy.tar.gz || \
    echo "Note: Download URL placeholder - please upload moss-deploy.tar.gz manually"
fi

# Check if file exists
if [ ! -f "moss-deploy.tar.gz" ]; then
    echo "Please upload moss-deploy.tar.gz to this directory first"
    echo "Then run: tar -xzf moss-deploy.tar.gz && cd moss && bash deploy.sh"
    exit 1
fi

# Extract
echo "[2/5] Extracting..."
tar -xzf moss-deploy.tar.gz

# Install
echo "[3/5] Installing dependencies..."
cd moss
chmod +x deploy.sh
bash deploy.sh

# Start
echo "[4/5] Starting MOSS..."
if [ -f "/opt/moss/monitor.py" ]; then
    nohup python3 /opt/moss/monitor.py > /opt/moss/moss.log 2>&1 &
    echo "MOSS started with PID: $!"
fi

# Cleanup
echo "[5/5] Cleaning up..."
cd /
rm -rf $TEMP_DIR

echo ""
echo "=========================================="
echo "MOSS Deployment Complete!"
echo "=========================================="
echo "Logs: tail -f /opt/moss/moss.log"
echo "Status: ps aux | grep moss"
echo "Config: /opt/moss/"
