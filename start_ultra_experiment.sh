#!/bin/bash
# MOSS超长期实验 - 1000代
# Ultra-long-term evolution experiment

set -e

echo "=========================================="
echo "MOSS Ultra-Long-Term Experiment (1000 Gen)"
echo "=========================================="

EXPERIMENT_DIR="/workspace/projects/moss/sandbox"
LOG_DIR="/workspace/projects/moss/logs"
mkdir -p $LOG_DIR

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/moss_ultra_${TIMESTAMP}.log"

echo ""
echo "[1/4] 配置环境..."
cd /workspace/projects
export PYTHONPATH=/workspace/projects:$PYTHONPATH

echo "✓ 环境就绪"

echo ""
echo "[2/4] 启动1000代超长期实验..."
echo "日志: $LOG_FILE"
echo ""

nohup python3 -c "
import sys
sys.path.insert(0, '/workspace/projects')

from moss.sandbox.experiment5_energy import run_energy_evolution
import json
import time

print('='*60)
print('MOSS ULTRA-LONG-TERM EXPERIMENT')
print('1000 Generations')
print('='*60)
print(f'Started: {time.strftime(\"%Y-%m-%d %H:%M:%S\")}')
print()

# 1000代超长期实验
results = run_energy_evolution(
    generations=1000,
    initial_pop=20,
    max_pop=150  # 提高上限观察扩展性
)

with open('$LOG_DIR/ultra_results_${TIMESTAMP}.json', 'w') as f:
    json.dump(results, f, indent=2)

print()
print('='*60)
print(f'Completed: {time.strftime(\"%Y-%m-%d %H:%M:%S\")}')
print('='*60)
print(f'Final Population: {results[\"final_alive\"]}')
print(f'Total Knowledge: {results[\"total_knowledge\"]:,}')
" > $LOG_FILE 2>&1 &

echo "✓ 实验已启动 (PID: $!)"
echo $! > $LOG_DIR/moss_ultra.pid

echo ""
echo "[3/4] 设置监控..."
cat > $LOG_DIR/check_ultra.sh << 'EOF'
#!/bin/bash
PID=$(cat /workspace/projects/moss/logs/moss_ultra.pid 2>/dev/null)
if ps -p $PID > /dev/null 2>&1; then
    echo "🔄 Ultra experiment running (PID: $PID)"
    tail -n 10 /workspace/projects/moss/logs/moss_ultra_*.log 2>/dev/null | tail -n 5
else
    echo "✅ Ultra experiment completed"
    ls -lh /workspace/projects/moss/logs/ultra_results_*.json 2>/dev/null
fi
EOF
chmod +x $LOG_DIR/check_ultra.sh

echo "✓ 监控已设置"
echo ""
echo "=========================================="
echo "🚀 1000代超长期实验已启动！"
echo "=========================================="
echo ""
echo "预计运行时间: 4-8小时"
echo "监控状态: bash $LOG_DIR/check_ultra.sh"
echo "查看日志: tail -f $LOG_FILE"
echo ""
