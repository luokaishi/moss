#!/bin/bash
#===============================================================================
# MOSS Experiment Deployment Script
# Deploy Run 4.3 and Run 4.4 to remote servers via SSH
#===============================================================================

set -e

# Configuration
MOSS_REPO="https://github.com/luokaishi/moss.git"
LOCAL_MOSS_DIR="/workspace/projects/moss"
REMOTE_BASE_DIR="/opt/moss"

# Server configurations
SERVER1_HOST="${SERVER1_HOST:-root@server1-ip}"  # Replace with actual IP
SERVER2_HOST="${SERVER2_HOST:-root@server2-ip}"  # Replace with actual IP

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

#===============================================================================
# Pre-deployment: Sync code to GitHub
#===============================================================================
sync_to_github() {
    log_info "Syncing optimized experiments to GitHub..."
    cd "$LOCAL_MOSS_DIR"
    
    # Check if files exist
    if [ ! -f "experiments/run_4_3_optimized.py" ]; then
        log_error "run_4_3_optimized.py not found!"
        exit 1
    fi
    
    if [ ! -f "experiments/run_4_4_optimized.py" ]; then
        log_error "run_4_4_optimized.py not found!"
        exit 1
    fi
    
    # Add and commit
    git add experiments/run_4_3_optimized.py experiments/run_4_4_optimized.py
    git commit -m "Add optimized Run 4.3 and 4.4 for distributed deployment" || true
    git push origin main || {
        log_warn "Git push failed, attempting to pull and retry..."
        git pull origin main --rebase
        git push origin main
    }
    
    log_info "Code synced to GitHub successfully"
}

#===============================================================================
# Setup Swap on Remote Server
#===============================================================================
setup_swap() {
    local host=$1
    log_info "Setting up swap on $host..."
    
    ssh "$host" << 'EOF'
        # Check if swap already exists
        if swapon --show | grep -q "/swapfile"; then
            echo "Swap already configured"
        else
            # Create 2GB swap
            sudo fallocate -l 2G /swapfile 2>/dev/null || sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
            sudo chmod 600 /swapfile
            sudo mkswap /swapfile
            sudo swapon /swapfile
            
            # Add to fstab if not present
            if ! grep -q "/swapfile" /etc/fstab; then
                echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
            fi
            
            echo "Swap setup complete"
            free -h
        fi
EOF
}

#===============================================================================
# Deploy MOSS to Remote Server
#===============================================================================
deploy_moss() {
    local host=$1
    local server_name=$2
    
    log_info "Deploying MOSS to $server_name ($host)..."
    
    ssh "$host" << EOF
        set -e
        
        # Install dependencies if needed
        if ! command -v python3 &> /dev/null; then
            echo "Installing Python3..."
            apt-get update -qq
            apt-get install -y -qq python3 python3-pip git
        fi
        
        # Clone or update MOSS
        if [ -d "$REMOTE_BASE_DIR" ]; then
            echo "Updating existing MOSS installation..."
            cd $REMOTE_BASE_DIR
            git pull origin main
        else
            echo "Cloning MOSS repository..."
            git clone $MOSS_REPO $REMOTE_BASE_DIR
        fi
        
        # Install Python dependencies
        cd $REMOTE_BASE_DIR
        pip3 install -q numpy 2>/dev/null || pip install -q numpy
        
        echo "Deployment complete on $server_name"
EOF
}

#===============================================================================
# Start Experiment on Remote Server
#===============================================================================
start_experiment() {
    local host=$1
    local server_name=$2
    local experiment=$3
    local log_file=$4
    
    log_info "Starting $experiment on $server_name..."
    
    ssh "$host" << EOF
        set -e
        cd $REMOTE_BASE_DIR
        
        # Kill any existing experiment
        pkill -f "run_4_[34]_optimized" || true
        
        # Start experiment with nohup
        nohup python3 experiments/$experiment.py > $log_file 2>&1 &
        sleep 2
        
        # Verify process started
        if pgrep -f "$experiment" > /dev/null; then
            echo "✅ $experiment started successfully (PID: \$(pgrep -f $experiment))"
        else
            echo "❌ Failed to start $experiment"
            exit 1
        fi
EOF
}

#===============================================================================
# Check Status on Remote Server
#===============================================================================
check_status() {
    local host=$1
    local server_name=$2
    local experiment=$3
    
    log_info "Checking status on $server_name..."
    
    ssh "$host" << EOF
        echo "=== Process Status ==="
        ps aux | grep "$experiment" | grep -v grep || echo "Process not running"
        
        echo ""
        echo "=== Memory Usage ==="
        free -h
        
        echo ""
        echo "=== Latest Log (last 5 lines) ==="
        tail -5 $REMOTE_BASE_DIR/experiments/${experiment}.out 2>/dev/null || echo "No log yet"
        
        echo ""
        echo "=== Current Status ==="
        cat $REMOTE_BASE_DIR/experiments/${experiment}_status.json 2>/dev/null | head -20 || echo "No status file yet"
EOF
}

#===============================================================================
# Main Deployment Flow
#===============================================================================
main() {
    log_info "MOSS Distributed Deployment Script"
    log_info "====================================="
    
    # Check SSH connectivity first
    log_info "Testing SSH connectivity..."
    ssh -o ConnectTimeout=5 "$SERVER1_HOST" "echo 'Server 1 OK'" || {
        log_error "Cannot connect to Server 1. Please set SERVER1_HOST environment variable."
        exit 1
    }
    ssh -o ConnectTimeout=5 "$SERVER2_HOST" "echo 'Server 2 OK'" || {
        log_error "Cannot connect to Server 2. Please set SERVER2_HOST environment variable."
        exit 1
    }
    
    # Step 1: Sync to GitHub
    sync_to_github
    
    # Step 2: Setup swap on both servers
    log_info "Setting up swap on both servers..."
    setup_swap "$SERVER1_HOST"
    setup_swap "$SERVER2_HOST"
    
    # Step 3: Deploy MOSS
    log_info "Deploying MOSS to servers..."
    deploy_moss "$SERVER1_HOST" "Server-1"
    deploy_moss "$SERVER2_HOST" "Server-2"
    
    # Step 4: Start experiments
    log_info "Starting experiments..."
    start_experiment "$SERVER1_HOST" "Server-1" "run_4_3_optimized" "/opt/moss/experiments/run_4_3.out"
    start_experiment "$SERVER2_HOST" "Server-2" "run_4_4_optimized" "/opt/moss/experiments/run_4_4.out"
    
    # Step 5: Initial status check
    log_info "Initial status check..."
    sleep 5
    check_status "$SERVER1_HOST" "Server-1" "run_4_3_optimized"
    check_status "$SERVER2_HOST" "Server-2" "run_4_4_optimized"
    
    log_info "====================================="
    log_info "Deployment complete!"
    log_info ""
    log_info "Run 4.3 (Server-1): Curiosity-dominant initial purpose"
    log_info "Run 4.4 (Server-2): Higher exploration rate (20% min)"
    log_info ""
    log_info "Monitor with:"
    log_info "  ./deploy_remote.sh status"
    log_info ""
    log_info "Expected completion: ~8 hours"
}

#===============================================================================
# Status Check Mode
#===============================================================================
status_mode() {
    log_info "Checking status on all servers..."
    
    echo ""
    echo ">>> Server 1 (Run 4.3) <<<"
    check_status "$SERVER1_HOST" "Server-1" "run_4_3_optimized"
    
    echo ""
    echo ">>> Server 2 (Run 4.4) <<<"
    check_status "$SERVER2_HOST" "Server-2" "run_4_4_optimized"
}

#===============================================================================
# Help
#===============================================================================
show_help() {
    cat << EOF
MOSS Remote Deployment Script

Usage:
  ./deploy_remote.sh [command]

Commands:
  deploy    - Full deployment (sync, setup, start experiments) [default]
  status    - Check status on all servers
  help      - Show this help

Environment Variables:
  SERVER1_HOST    - SSH host for Server 1 (Run 4.3)
  SERVER2_HOST    - SSH host for Server 2 (Run 4.4)

Examples:
  export SERVER1_HOST=root@192.168.1.10
  export SERVER2_HOST=root@192.168.1.11
  ./deploy_remote.sh deploy
  
  ./deploy_remote.sh status
EOF
}

#===============================================================================
# Entry Point
#===============================================================================
case "${1:-deploy}" in
    deploy)
        main
        ;;
    status)
        status_mode
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
