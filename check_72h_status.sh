#!/bin/bash
# 72小时实验状态检查脚本

echo "=================================="
echo "72小时实验状态检查"
echo "=================================="
echo "检查时间: $(date)"
echo ""

# 检查实验PID
if [ -f /tmp/mves_72h_full/experiment.pid ]; then
    EXP_PID=$(cat /tmp/mves_72h_full/experiment.pid)
    echo "实验PID: $EXP_PID"
    
    # 检查进程状态
    if ps -p $EXP_PID > /dev/null 2>&1; then
        echo "实验状态: ✅ 运行中"
        ps -p $EXP_PID -o pid,%cpu,%mem,etime,comm --no-headers
    else
        echo "实验状态: ❌ 已停止"
    fi
else
    echo "实验PID: 未找到"
fi

echo ""

# 检查监控PID
if [ -f /tmp/mves_72h_full/monitor.pid ]; then
    MON_PID=$(cat /tmp/mves_72h_full/monitor.pid)
    echo "监控PID: $MON_PID"
    
    if ps -p $MON_PID > /dev/null 2>&1; then
        echo "监控状态: ✅ 运行中"
    else
        echo "监控状态: ❌ 已停止"
    fi
else
    echo "监控PID: 未找到"
fi

echo ""

# 检查日志
if [ -f /tmp/mves_72h_logs/experiment.log ]; then
    echo "实验日志: ✅ 存在"
    echo "  大小: $(du -h /tmp/mves_72h_logs/experiment.log | cut -f1)"
    echo "  最后更新: $(stat -c %y /tmp/mves_72h_logs/experiment.log | cut -d'.' -f1)"
else
    echo "实验日志: ❌ 不存在"
fi

echo ""

# 检查检查点
if [ -d /tmp/mves_72h_checkpoints ]; then
    CHECKPOINT_COUNT=$(ls /tmp/mves_72h_checkpoints/checkpoint_*.json 2>/dev/null | wc -l)
    echo "检查点: $CHECKPOINT_COUNT 个"
    if [ $CHECKPOINT_COUNT -gt 0 ]; then
        echo "  最新: $(ls -t /tmp/mves_72h_checkpoints/checkpoint_*.json 2>/dev/null | head -1 | xargs basename)"
    fi
else
    echo "检查点: ❌ 目录不存在"
fi

echo ""

# 检查监控状态
if [ -f /tmp/mves_72h_full/monitor_status.json ]; then
    echo "监控状态: ✅ 存在"
    echo "  检查次数: $(cat /tmp/mves_72h_full/monitor_status.json | grep check_count | cut -d':' -f2 | tr -d ' ,')"
else
    echo "监控状态: ❌ 不存在"
fi

echo ""
echo "=================================="
echo "监控命令:"
echo "  tail -f /tmp/mves_72h_logs/experiment.log"
echo "  tail -f /tmp/mves_72h_logs/monitor.log"
echo "=================================="
