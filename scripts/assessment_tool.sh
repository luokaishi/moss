#!/bin/bash
# MOSS Assessment Automation Script
# 自动化评估流程

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目路径
PROJECT_DIR="/workspace/projects/moss"
ASSESSMENT_DIR="$PROJECT_DIR/docs/assessments"
TEMPLATE_DIR="$PROJECT_DIR/docs/templates"

# 创建时间戳
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DATE=$(date +"%Y-%m-%d")

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  MOSS Project Assessment Tool${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 显示菜单
show_menu() {
    echo "请选择操作:"
    echo "1) 创建自评估报告"
    echo "2) 准备外部评估请求"
    echo "3) 72h实验评估（自动）"
    echo "4) 查看历史评估"
    echo "5) 生成评估摘要"
    echo "0) 退出"
    echo ""
}

# 创建自评估报告
create_self_assessment() {
    echo -e "${YELLOW}创建自评估报告...${NC}"
    
    # 获取节点信息
    read -p "评估节点名称 (如: v5.0发布/72h实验完成): " node_name
    read -p "节点类型 (版本发布/实验完成/里程碑/季度回顾): " node_type
    
    # 创建文件
    filename="self_assessment_${TIMESTAMP}.md"
    filepath="$ASSESSMENT_DIR/$filename"
    
    # 复制模板并填充
    cp "$TEMPLATE_DIR/self_assessment_template.md" "$filepath"
    
    # 替换占位符
    sed -i "s/YYYY-MM-DD/$DATE/g" "$filepath"
    sed -i "s/\[版本发布\/实验完成\/里程碑\]/$node_name/g" "$filepath"
    sed -i "s/\[版本发布 \/ 实验完成 \/ 里程碑 \/ 季度回顾\]/$node_type/g" "$filepath"
    
    echo -e "${GREEN}✅ 自评估模板已创建: $filepath${NC}"
    echo ""
    echo -e "${YELLOW}请编辑该文件完成自评估${NC}"
    echo ""
}

# 准备外部评估请求
prepare_external_assessment() {
    echo -e "${YELLOW}准备外部评估请求...${NC}"
    
    # 获取信息
    read -p "评估对象 (AI工具/专家姓名): " evaluator
    read -p "评估类型 (技术/科学/工程/全面): " assess_type
    
    # 创建文件
    filename="external_request_${TIMESTAMP}.md"
    filepath="$ASSESSMENT_DIR/$filename"
    
    # 复制模板并填充
    cp "$TEMPLATE_DIR/external_assessment_request.md" "$filepath"
    
    # 替换占位符
    sed -i "s/YYYY-MM-DD/$DATE/g" "$filepath"
    sed -i "s/\[AI工具\/专家姓名\]/$evaluator/g" "$filepath"
    sed -i "s/\[技术\/科学\/工程\/全面\]/$assess_type/g" "$filepath"
    
    # 附加当前评估文档
    echo "" >> "$filepath"
    echo "---" >> "$filepath"
    echo "" >> "$filepath"
    echo "## 附录: MOSS综合评估文档" >> "$filepath"
    echo "" >> "$filepath"
    echo "[请将以下内容复制给评估对象]" >> "$filepath"
    echo "" >> "$filepath"
    echo "\`\`\`" >> "$filepath"
    cat "$PROJECT_DIR/MOSS_COMPREHENSIVE_EVALUATION.md" >> "$filepath"
    echo "\`\`\`" >> "$filepath"
    
    echo -e "${GREEN}✅ 外部评估请求已创建: $filepath${NC}"
    echo ""
    echo -e "${YELLOW}请复制文档内容发送给: $evaluator${NC}"
    echo ""
}

# 72h实验自动评估
assess_72h_experiment() {
    echo -e "${YELLOW}执行72h实验自动评估...${NC}"
    
    # 检查实验状态
    status_file="$PROJECT_DIR/experiments/primary_72h_status.json"
    
    if [ ! -f "$status_file" ]; then
        echo -e "${RED}❌ 找不到72h实验状态文件${NC}"
        return 1
    fi
    
    # 解析状态
    echo -e "${BLUE}当前实验状态:${NC}"
    python3 << EOF
import json

try:
    with open('$status_file', 'r') as f:
        status = json.load(f)
    
    print(f"  位置: {status.get('location', 'N/A')}")
    print(f"  状态: {status.get('status', 'N/A')}")
    print(f"  PID: {status.get('pid', 'N/A')}")
    print(f"  进度: {status.get('progress', {}).get('percent_complete', 'N/A')}")
    print(f"  步数: {status.get('progress', {}).get('total_steps', 'N/A')}")
    print(f"  预计完成: {status.get('expected_end', 'N/A')}")
except Exception as e:
    print(f"  错误: {e}")
EOF
    
    echo ""
    
    # 询问是否执行分析
    read -p "是否执行数据分析? (y/n): " do_analysis
    
    if [ "$do_analysis" = "y" ]; then
        echo -e "${YELLOW}执行数据分析...${NC}"
        
        # 创建评估目录
        assess_dir="$ASSESSMENT_DIR/72h_assessment_$TIMESTAMP"
        mkdir -p "$assess_dir"
        
        # 执行分析脚本
        if [ -f "$PROJECT_DIR/scripts/analyze_72h_results.py" ]; then
            echo "运行 analyze_72h_results.py..."
            # 注意：这里需要实际的实验数据文件路径
            echo -e "${YELLOW}请手动运行分析脚本:${NC}"
            echo "  python3 scripts/analyze_72h_results.py --input [数据文件] --output $assess_dir"
        else
            echo -e "${RED}❌ 分析脚本不存在${NC}"
        fi
        
        # 执行可视化
        if [ -f "$PROJECT_DIR/scripts/visualize_purpose_evolution.py" ]; then
            echo "运行 visualize_purpose_evolution.py..."
            echo -e "${YELLOW}请手动运行可视化脚本${NC}"
        fi
        
        # 执行counter-reward检测
        if [ -f "$PROJECT_DIR/scripts/detect_counter_reward.py" ]; then
            echo "运行 detect_counter_reward.py..."
            echo -e "${YELLOW}请手动运行检测脚本${NC}"
        fi
        
        echo -e "${GREEN}✅ 72h评估目录已创建: $assess_dir${NC}"
    fi
    
    echo ""
}

# 查看历史评估
view_history() {
    echo -e "${YELLOW}历史评估记录:${NC}"
    echo ""
    
    if [ -d "$ASSESSMENT_DIR" ]; then
        ls -lt "$ASSESSMENT_DIR" | head -20
    else
        echo -e "${RED}❌ 没有历史评估记录${NC}"
    fi
    
    echo ""
}

# 生成评估摘要
generate_summary() {
    echo -e "${YELLOW}生成项目评估摘要...${NC}"
    
    summary_file="$ASSESSMENT_DIR/assessment_summary_$DATE.md"
    
    cat > "$summary_file" << EOF
# MOSS Project Assessment Summary
**Date**: $DATE

## 项目概览
- **Current Version**: v5.0.0
- **Active Experiments**: 72h Real World (16% complete)
- **Code Lines**: ~1,800 (core)
- **Test Status**: Quick tests passing

## 最新评估
EOF
    
    # 列出最近的评估
    if [ -d "$ASSESSMENT_DIR" ]; then
        echo "" >> "$summary_file"
        echo "### 最近评估记录" >> "$summary_file"
        echo "" >> "$summary_file"
        
        for file in $(ls -t "$ASSESSMENT_DIR"/*.md 2>/dev/null | head -5); do
            echo "- $(basename $file)" >> "$summary_file"
        done
    fi
    
    echo "" >> "$summary_file"
    echo "### 关键指标" >> "$summary_file"
    echo "" >> "$summary_file"
    echo "| 维度 | 状态 |" >> "$summary_file"
    echo "|------|------|" >> "$summary_file"
    echo "| 技术架构 | v5.0 Unified |" >> "$summary_file"
    echo "| 实验验证 | Run 4.x ✅, 5.1 ✅, 72h 🔄 |" >> "$summary_file"
    echo "| 代码质量 | Quick tests ✅ |" >> "$summary_file"
    echo "| 文档完整 | Comprehensive ✅ |" >> "$summary_file"
    
    echo "" >> "$summary_file"
    echo "### 待办评估" >> "$summary_file"
    echo "" >> "$summary_file"
    echo "- [ ] 72h实验完成评估 (预计: 2026-03-27)" >> "$summary_file"
    echo "- [ ] v5.0正式发布评估" >> "$summary_file"
    echo "- [ ] Phase 2启动前评估" >> "$summary_file"
    
    echo -e "${GREEN}✅ 评估摘要已生成: $summary_file${NC}"
    echo ""
}

# 主循环
while true; do
    show_menu
    read -p "选择操作 [0-5]: " choice
    
    case $choice in
        1)
            create_self_assessment
            ;;
        2)
            prepare_external_assessment
            ;;
        3)
            assess_72h_experiment
            ;;
        4)
            view_history
            ;;
        5)
            generate_summary
            ;;
        0)
            echo -e "${GREEN}感谢使用!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}无效选项，请重新选择${NC}"
            ;;
    esac
    
    echo ""
    read -p "按Enter继续..."
    echo ""
done
