#!/bin/bash
# 等待实验完成并生成摘要

echo "等待实验完成..."
echo "开始时间: $(date)"
echo ""

# 等待多样性实验
DIV_DIR=$(ls -td logs/experiment_v5_diversity_*v550_diversity_run1 2>/dev/null | head -1)
MULTI_DIR=$(ls -td logs/experiment_v5_multiagent_*v550_multiagent_run1 2>/dev/null | head -1)

echo "多样性实验目录: $(basename $DIV_DIR)"
echo "多Agent实验目录: $(basename $MULTI_DIR)"
echo ""

# 循环检查
for i in {1..60}; do
    sleep 30
    
    # 检查多样性实验
    if [ -f "$DIV_DIR/final_report.json" ]; then
        echo "✅ 多样性实验完成! ($(date))"
        echo "---"
        cat "$DIV_DIR/final_report.json" | python3 -m json.tool 2>/dev/null | head -30
        break
    fi
    
    # 检查多Agent实验
    if [ -f "$MULTI_DIR/final_report.json" ]; then
        echo "✅ 多Agent实验完成! ($(date))"
        echo "---"
        cat "$MULTI_DIR/final_report.json" | python3 -m json.tool 2>/dev/null | head -30
        break
    fi
    
    # 显示进度
    if [ $((i % 2)) -eq 0 ]; then
        echo "[$((i/2)) min] 等待中... $(date +%H:%M:%S)"
    fi
done

echo ""
echo "监控结束: $(date)"
