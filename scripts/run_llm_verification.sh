#!/bin/bash
# MOSS真实LLM验证运行脚本
# 使用ARK API进行真实LLM自驱行为验证

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "MOSS Real LLM Verification Runner"
echo "========================================"

# 检查API密钥
if [ -z "$ARK_API_KEY" ]; then
    echo -e "${RED}Error: ARK_API_KEY not set${NC}"
    echo ""
    echo "Please set your ARK API key:"
    echo "  export ARK_API_KEY=your_api_key_here"
    echo ""
    echo "Or run in mock mode:"
    echo "  ./run_llm_verification.sh --mock"
    exit 1
fi

# 默认参数
MODE="real"
STEPS=20
MODEL="qwen2.5-1.5b"

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --mock)
            MODE="mock"
            shift
            ;;
        --steps)
            STEPS="$2"
            shift 2
            ;;
        --model)
            MODEL="$2"
            shift 2
            ;;
        --help)
            echo "Usage: ./run_llm_verification.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --mock          Run in mock mode (no API calls)"
            echo "  --steps N       Number of steps (default: 20)"
            echo "  --model MODEL   Model name (default: qwen2.5-1.5b)"
            echo "  --help          Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# 进入sandbox目录
cd "$(dirname "$0")/../sandbox" || exit 1

echo ""
echo "Configuration:"
echo "  Mode: $MODE"
echo "  Steps: $STEPS"
echo "  Model: $MODEL"
echo "  API Key: ${ARK_API_KEY:0:8}..."
echo ""

if [ "$MODE" = "mock" ]; then
    echo -e "${YELLOW}Running in MOCK mode (no real API calls)${NC}"
    python moss_llm_real_verifier.py --steps "$STEPS" --mock
else
    echo -e "${GREEN}Running with REAL LLM API${NC}"
    echo "This will consume API credits. Continue? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        python moss_llm_real_verifier.py --steps "$STEPS" --model "$MODEL"
    else
        echo "Aborted."
        exit 0
    fi
fi

echo ""
echo "========================================"
echo "Verification complete!"
echo "========================================"
echo ""
echo "Check the generated report file for detailed results."
