#!/bin/bash
# MVES One-Click Experiment Runner
# MVES 一键实验运行脚本

set -e

echo "============================================"
echo "MVES 一键实验运行"
echo "============================================"

# Create results directory
mkdir -p experiments/results

# Run performance benchmark
echo ""
echo "1. 运行性能基准测试..."
python3 experiments/benchmarks/performance_benchmark.py

# Run AGI benchmark
echo ""
echo "2. 运行 AGI 基准测试..."
python3 experiments/benchmarks/agi_benchmark.py

# Run 100-agent collaboration
echo ""
echo "3. 运行 100 Agent 协作实验..."
python3 experiments/collab_100agents.py --agents 100 --cycles 10

# Run stress test (simulated)
echo ""
echo "4. 运行稳定性测试 (模拟)..."
python3 experiments/stress_test_168h.py --iterations 50

echo ""
echo "============================================"
echo "✅ 所有实验完成!"
echo "============================================"
echo ""
echo "结果保存在：experiments/results/"
echo ""
