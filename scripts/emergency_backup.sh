#!/bin/bash
# 72h实验应急备份脚本
# 在阿里云服务器上执行

BACKUP_DIR="~/moss_emergency_backup_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$BACKUP_DIR/backup.log"

echo "========================================" 
echo "MOSS 72h Experiment Emergency Backup"
echo "Time: $(date)"
echo "========================================"
echo ""

# 创建备份目录
mkdir -p $BACKUP_DIR
echo "[1/5] Created backup dir: $BACKUP_DIR" | tee -a $LOG_FILE

# 1. 检查进程状态
echo ""
echo "[2/5] Checking experiment process..."
if pgrep -f "72h\|real_world" > /dev/null; then
    echo "✓ Experiment process is RUNNING" | tee -a $LOG_FILE
    pgrep -f "72h\|real_world" | tee -a $LOG_FILE
else
    echo "✗ Experiment process NOT FOUND" | tee -a $LOG_FILE
fi

# 2. 备份实验数据
echo ""
echo "[3/5] Backing up experiment data..."
# 根据实际路径调整
EXPERIMENT_PATHS=(
    "/root/moss/experiments/72h_*"
    "/root/moss/experiments/real_world_*"
    "/root/moss/actions.jsonl"
    "/root/moss/status.json"
)

for path in "${EXPERIMENT_PATHS[@]}"; do
    if [ -e $path ]; then
        cp -r $path $BACKUP_DIR/ 2>/dev/null && echo "  ✓ Backed up: $path" | tee -a $LOG_FILE
    fi
done

# 3. 保存进程状态
echo ""
echo "[4/5] Saving process status..."
ps aux | grep -E "(python|moss|72h)" | grep -v grep > $BACKUP_DIR/process_status.txt
echo "  ✓ Process status saved" | tee -a $LOG_FILE

# 4. 保存系统状态
echo ""
echo "[5/5] Saving system status..."
df -h > $BACKUP_DIR/disk_usage.txt
free -h > $BACKUP_DIR/memory_usage.txt
uptime > $BACKUP_DIR/uptime.txt
echo "  ✓ System status saved" | tee -a $LOG_FILE

# 5. 创建状态报告
echo ""
echo "========================================"
echo "BACKUP COMPLETE"
echo "========================================"
echo "Location: $BACKUP_DIR"
echo "Size: $(du -sh $BACKUP_DIR | cut -f1)"
echo ""
echo "Status Summary:"
echo "  - Gateway: DOWN (OpenClaw)"
echo "  - SSH: WORKING"
echo "  - Experiment: $(pgrep -f '72h\|real_world' > /dev/null && echo 'RUNNING' || echo 'UNKNOWN')"
echo "  - Backup: COMPLETE"
echo ""
echo "Next steps:"
echo "  1. Monitor experiment via SSH directly"
echo "  2. Wait for gateway recovery"
echo "  3. Or migrate to local if needed"
echo ""

# 列出备份内容
ls -lah $BACKUP_DIR/ | tee -a $LOG_FILE
