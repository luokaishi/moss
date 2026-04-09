#!/bin/bash
# MOSS长期实验运行脚本
# 在服务器后台持续运行

set -e

echo "=========================================="
echo "MOSS长期实验启动器"
echo "=========================================="

# 实验配置
EXPERIMENT_DIR="/workspace/projects/moss/sandbox"
LOG_DIR="/workspace/projects/moss/logs"
mkdir -p $LOG_DIR

# 时间戳
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/moss_longterm_$TIMESTAMP.log"

echo ""
echo "[1/4] 配置实验环境..."
cd /workspace/projects
source moss/venv/bin/activate 2>/dev/null || echo "使用系统Python"
export PYTHONPATH=/workspace/projects:$PYTHONPATH

echo "✓ 环境就绪"

echo ""
echo "[2/4] 启动长期实验..."
echo "日志文件: $LOG_FILE"
echo ""

# 运行实验并记录日志
nohup python3 -c "
import sys
sys.path.insert(0, '/workspace/projects')

from moss.sandbox.experiment5_energy import run_energy_evolution
import json
import time

print('='*60)
print('MOSS Long-term Evolution Experiment')
print('='*60)
print(f'Started: {time.strftime(\"%Y-%m-%d %H:%M:%S\")}')
print()

# 运行更长期的实验
results = run_energy_evolution(
    generations=500,  # 500代长期演化
    initial_pop=20,
    max_pop=100
)

# 保存详细结果
with open('$LOG_DIR/results_$TIMESTAMP.json', 'w') as f:
    json.dump(results, f, indent=2)

print()
print('='*60)
print(f'Completed: {time.strftime(\"%Y-%m-%d %H:%M:%S\")}')
print('='*60)
" > $LOG_FILE 2>&1 &

echo "✓ 实验已在后台启动"
echo "  PID: $!"
echo ""

echo "[3/4] 保存进程信息..."
echo $! > $LOG_DIR/moss_experiment.pid
echo "✓ PID已保存"

echo ""
echo "[4/4] 设置监控..."

# 创建监控脚本
cat > $LOG_DIR/check_status.sh << 'EOF'
#!/bin/bash
PID_FILE="/workspace/projects/moss/logs/moss_experiment.pid"
LOG_DIR="/workspace/projects/moss/logs"

if [ -f "$PID_FILE" ]; then
    PID=$(cat $PID_FILE)
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ MOSS实验运行中 (PID: $PID)"
        echo ""
        echo "最新日志:"
        tail -n 20 $LOG_DIR/moss_longterm_*.log 2>/dev/null | tail -n 10
    else
        echo "❌ MOSS实验已停止"
        echo ""
        echo "最后日志:"
        tail -n 30 $LOG_DIR/moss_longterm_*.log 2>/dev/null | tail -n 15
    fi
else
    echo "⚠️ 未找到PID文件"
fi
EOF

chmod +x $LOG_DIR/check_status.sh

echo "✓ 监控脚本已创建"
echo ""
echo "=========================================="
echo "🚀 长期实验已启动！"
echo "=========================================="
echo ""
echo "查看状态:"
echo "  bash $LOG_DIR/check_status.sh"
echo ""
echo "查看日志:"
echo "  tail -f $LOG_FILE"
echo ""
echo "停止实验:"
echo "  kill \$(cat $LOG_DIR/moss_experiment.pid)"
echo ""
echo "预计运行时间: 2-4小时（500代演化）"
echo "=========================================="
