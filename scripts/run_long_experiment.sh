#!/bin/bash
# MOSS 长周期实验自动化脚本 v5.5.0
# 支持自动续跑、错误恢复、资源监控

set -e

# 配置
MAX_CYCLES=${MAX_CYCLES:-100000}
EXPERIMENT_LABEL=${EXPERIMENT_LABEL:-"longrun_v1"}
MOSS_ROOT=$(cd "$(dirname "$0")/.." && pwd)
LOG_DIR="$MOSS_ROOT/logs"
PYTHON="${PYTHON:-python3}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查环境
check_env() {
    log_info "检查环境..."
    
    if ! command -v $PYTHON &> /dev/null; then
        log_error "Python 未找到: $PYTHON"
        exit 1
    fi
    
    if [ ! -f "$MOSS_ROOT/examples/experiment_v5_longrun.py" ]; then
        log_error "实验脚本未找到"
        exit 1
    fi
    
    # 检查磁盘空间
    AVAILABLE=$(df "$LOG_DIR" | tail -1 | awk '{print $4}')
    if [ "$AVAILABLE" -lt 1048576 ]; then  # 1GB = 1048576 KB
        log_warn "磁盘空间不足 1GB，可能影响长周期实验"
    fi
    
    log_info "环境检查通过"
}

# 查找最新的实验目录
find_latest_experiment() {
    local latest_dir=$(ls -td "$LOG_DIR"/experiment_v5_* 2>/dev/null | head -1)
    if [ -z "$latest_dir" ]; then
        latest_dir=$(ls -td "$LOG_DIR"/experiment_v3_* 2>/dev/null | head -1)
    fi
    echo "$latest_dir"
}

# 检查是否需要续跑
check_resume() {
    local latest_dir=$(find_latest_experiment)
    
    if [ -n "$latest_dir" ]; then
        local final_report="$latest_dir/final_report.json"
        
        if [ ! -f "$final_report" ]; then
            log_warn "发现未完成的实验: $(basename "$latest_dir")"
            read -p "是否续跑? (y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                return 0  # 需要续跑
            fi
        fi
    fi
    
    return 1  # 不需要续跑
}

# 运行实验
run_experiment() {
    local resume_flag=""
    
    if check_resume; then
        resume_flag="--resume latest"
        log_info "续跑模式"
    else
        log_info "新实验: $EXPERIMENT_LABEL"
    fi
    
    log_info "启动实验 (目标: $MAX_CYCLES 周期)..."
    log_info "日志目录: $LOG_DIR"
    
    # 运行实验
    cd "$MOSS_ROOT"
    $PYTHON examples/experiment_v5_longrun.py \
        --cycles $MAX_CYCLES \
        --label "$EXPERIMENT_LABEL" \
        $resume_flag \
        --cp-cycle 1000 \
        --cp-time 30 \
        --gc-threshold 50 \
        --gc-interval 500 \
        --report-interval 5000
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log_info "实验正常完成"
        return 0
    else
        log_error "实验异常退出 (code: $exit_code)"
        return 1
    fi
}

# 监控循环 (自动续跑)
monitor_loop() {
    local max_retries=${MAX_RETRIES:-3}
    local retry_count=0
    
    while [ $retry_count -lt $max_retries ]; do
        if run_experiment; then
            log_info "实验成功完成！"
            break
        fi
        
        retry_count=$((retry_count + 1))
        
        if [ $retry_count -lt $max_retries ]; then
            log_warn "将在 10 秒后尝试续跑 (重试 $retry_count/$max_retries)..."
            sleep 10
        fi
    done
    
    if [ $retry_count -eq $max_retries ]; then
        log_error "达到最大重试次数，实验失败"
        exit 1
    fi
}

# 生成实验摘要
generate_summary() {
    local latest_dir=$(find_latest_experiment)
    
    if [ -z "$latest_dir" ]; then
        log_error "找不到实验目录"
        return 1
    fi
    
    local report_file="$latest_dir/final_report.json"
    
    if [ ! -f "$report_file" ]; then
        log_warn "实验尚未完成"
        return 1
    fi
    
    log_info "实验摘要:"
    echo "========================================"
    cat "$report_file" | $PYTHON -m json.tool 2>/dev/null || cat "$report_file"
    echo "========================================"
    echo "完整报告: $report_file"
}

# 主函数
main() {
    case "${1:-run}" in
        run)
            check_env
            monitor_loop
            generate_summary
            ;;
        resume)
            check_env
            export MAX_CYCLES=${2:-$MAX_CYCLES}
            run_experiment
            ;;
        summary)
            generate_summary
            ;;
        clean)
            log_warn "将清理所有实验日志 (保留最近3个)"
            read -p "确认? (yes/no): " confirm
            if [ "$confirm" = "yes" ]; then
                ls -td "$LOG_DIR"/experiment_v* 2>/dev/null | tail -n +4 | xargs rm -rf
                log_info "清理完成"
            fi
            ;;
        help|--help|-h)
            echo "MOSS 长周期实验自动化脚本 v5.5.0"
            echo ""
            echo "用法: $0 [命令] [选项]"
            echo ""
            echo "命令:"
            echo "  run              运行实验 (默认，支持自动续跑)"
            echo "  resume [cycles]  强制续跑最新实验"
            echo "  summary          显示最新实验摘要"
            echo "  clean            清理旧实验日志 (保留最近3个)"
            echo "  help             显示此帮助"
            echo ""
            echo "环境变量:"
            echo "  MAX_CYCLES       最大周期数 (默认: 100000)"
            echo "  EXPERIMENT_LABEL 实验标签 (默认: longrun_v1)"
            echo "  PYTHON           Python 解释器路径 (默认: python3)"
            echo "  MAX_RETRIES      最大重试次数 (默认: 3)"
            echo ""
            echo "示例:"
            echo "  MAX_CYCLES=50000 EXPERIMENT_LABEL=test $0 run"
            echo "  $0 resume 100000"
            ;;
        *)
            log_error "未知命令: $1"
            echo "使用 '$0 help' 查看帮助"
            exit 1
            ;;
    esac
}

main "$@"
