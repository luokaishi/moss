#!/bin/bash
# 复现脚本

echo "复现实验: 7层架构5000周期"
echo "=========================="

# 检查环境
python3 -c "import numpy; import yaml; print('✓ 依赖检查通过')"

# 运行实验
echo "运行实验..."
python3 experiment_7layer_v2_5000.py

echo "实验完成"
echo "结果保存在: experiments/7layer_v2_5000/"
