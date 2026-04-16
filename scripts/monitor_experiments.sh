#!/bin/bash
# MOSS v5.5.0 实验监控脚本

LOG_DIR="/home/admin/.openclaw/workspace/logs"

echo "========================================"
echo "MOSS v5.5.0 实验监控"
echo "时间: $(date)"
echo "========================================"
echo ""

# 检查进程
echo "运行中的实验进程:"
ps aux | grep -E "experiment_v5_(diversity|multiagent|longrun)" | grep -v grep | awk '{print $2, $11, $12}'
echo ""

# 检查多样性实验
echo "--- 多样性实验 ---"
DIV_DIR=$(ls -td $LOG_DIR/experiment_v5_diversity_* 2>/dev/null | head -1)
if [ -n "$DIV_DIR" ]; then
    echo "目录: $(basename $DIV_DIR)"
    if [ -f "$DIV_DIR/diversity_report_*.json" ]; then
        LATEST_REPORT=$(ls -t $DIV_DIR/diversity_report_*.json 2>/dev/null | head -1)
        if [ -n "$LATEST_REPORT" ]; then
            echo "最新报告: $(basename $LATEST_REPORT)"
            cat $LATEST_REPORT | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'周期: {d[\"cycle\"]} | shell: {d[\"diversity_metrics\"][\"shell_percentage\"]}% | 类型: {d[\"diversity_metrics\"][\"total_types_used\"]}')" 2>/dev/null
        fi
    fi
    echo "日志 tail:"
    tail -5 $DIV_DIR/experiment.log 2>/dev/null || echo "  等待日志..."
else
    echo "未找到多样性实验目录"
fi
echo ""

# 检查多Agent实验
echo "--- 多Agent实验 ---"
MULTI_DIR=$(ls -td $LOG_DIR/experiment_v5_multiagent_* 2>/dev/null | head -1)
if [ -n "$MULTI_DIR" ]; then
    echo "目录: $(basename $MULTI_DIR)"
    echo "日志 tail:"
    tail -5 $MULTI_DIR/experiment.log 2>/dev/null || echo "  等待日志..."
else
    echo "未找到多Agent实验目录"
fi
echo ""

# 检查长周期实验
echo "--- 长周期实验 ---"
LONG_DIR=$(ls -td $LOG_DIR/experiment_v5_20* 2>/dev/null | head -1)
if [ -n "$LONG_DIR" ] && [ -f "$LONG_DIR/checkpoint_*.json" ]; then
    echo "目录: $(basename $LONG_DIR)"
    LATEST_CP=$(ls -t $LONG_DIR/checkpoint_*.json 2>/dev/null | head -1)
    if [ -n "$LATEST_CP" ]; then
        echo "最新检查点: $(basename $LATEST_CP)"
        cat $LATEST_CP | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'周期: {d[\"cycle\"]} | 内存: {d[\"memory_mb\"]}MB | 涌现: {d[\"emerged_drives\"]}')" 2>/dev/null
    fi
    echo "日志 tail:"
    tail -5 $LONG_DIR/experiment.log 2>/dev/null || echo "  等待日志..."
else
    echo "未找到长周期实验目录"
fi
echo ""

echo "========================================"
echo "监控完成: $(date)"
echo "========================================"
