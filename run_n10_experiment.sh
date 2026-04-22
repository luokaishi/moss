#!/bin/bash
# N=10 LLM 验证实验运行脚本
# 使用方法: ./run_n10_experiment.sh [mock|real]

set -e

MODE=${1:-mock}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="experiments/n10_llm_validation/logs/n10_${MODE}_${TIMESTAMP}.log"

echo "=========================================="
echo "MOSS N=10 LLM 验证实验"
echo "模式: $MODE"
echo "时间: $(date)"
echo "=========================================="

# 创建日志目录
mkdir -p experiments/n10_llm_validation/logs

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: Python3 未安装"
    exit 1
fi

echo "✅ Python3 检查通过"

# 检查依赖
echo "检查依赖..."
python3 -c "import numpy" 2>/dev/null || {
    echo "安装依赖..."
    pip3 install numpy -q
}
echo "✅ 依赖检查通过"

# 运行实验
echo ""
echo "启动 N=10 实验..."
echo "日志文件: $LOG_FILE"
echo ""

if [ "$MODE" = "real" ]; then
    # 真实 LLM 模式
    if [ -z "$DASHSCOPE_API_KEY" ]; then
        echo "⚠️ 警告: DASHSCOPE_API_KEY 未设置"
        echo "请设置: export DASHSCOPE_API_KEY='your-key'"
        exit 1
    fi
    echo "使用真实 LLM 后端 (成本: ~¥40)"
else
    echo "使用 Mock 后端 (零成本，快速测试)"
fi

# 后台运行
nohup python3 experiments/n10_llm_validation.py > "$LOG_FILE" 2>&1 &
PID=$!

echo ""
echo "✅ 实验已启动 (PID: $PID)"
echo ""
echo "查看进度:"
echo "  tail -f $LOG_FILE"
echo ""
echo "查看结果:"
echo "  cat experiments/n10_llm_validation/results/summary.json"
echo ""
echo "停止实验:"
echo "  kill $PID"
