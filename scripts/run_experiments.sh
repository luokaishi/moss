#!/bin/bash
# MOSS实验运行脚本
# 一键运行所有实验

set -e

echo "========================================"
echo "MOSS Experiment Runner"
echo "========================================"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 not found"
    exit 1
fi

# 进入sandbox目录
cd "$(dirname "$0")/../sandbox" || exit 1

echo ""
echo "Available experiments:"
echo "  1. Multi-Objective Competition (Exp 1)"
echo "  2. Evolutionary Dynamics (Exp 2)"  
echo "  3. Social Emergence (Exp 3)"
echo "  4. Dynamic API Adaptation (Exp 4)"
echo "  5. Energy-Driven Evolution (Exp 5)"
echo "  6. LLM Verification (Mock)"
echo "  7. LLM Verification (Real - requires API key)"
echo "  all. Run all experiments (1-5)"
echo ""

read -p "Select experiment (1-7 or all): " choice

run_exp1() {
    echo ""
    echo "Running Experiment 1: Multi-Objective Competition..."
    python experiment1.py
    echo "✅ Exp 1 complete. Results: exp1_results.json"
}

run_exp2() {
    echo ""
    echo "Running Experiment 2: Evolutionary Dynamics..."
    python experiment2.py
    echo "✅ Exp 2 complete. Results: exp2_results.json"
}

run_exp3() {
    echo ""
    echo "Running Experiment 3: Social Emergence..."
    python experiment3.py
    echo "✅ Exp 3 complete. Results: exp3_results.json"
}

run_exp4() {
    echo ""
    echo "Running Experiment 4: Dynamic API Adaptation..."
    python experiment4_final.py
    echo "✅ Exp 4 complete. Results: exp4_final.json"
}

run_exp5() {
    echo ""
    echo "Running Experiment 5: Energy-Driven Evolution..."
    python experiment5_energy.py
    echo "✅ Exp 5 complete. Results: exp5_energy.json"
}

run_llm_mock() {
    echo ""
    echo "Running LLM Verification (Mock Mode)..."
    python moss_llm_real_verifier.py --steps 50 --mock
}

run_llm_real() {
    echo ""
    if [ -z "$ARK_API_KEY" ]; then
        read -p "Enter ARK_API_KEY: " api_key
        export ARK_API_KEY="$api_key"
    fi
    echo "Running LLM Verification (Real API)..."
    python moss_llm_real_verifier.py --steps 20
}

case $choice in
    1)
        run_exp1
        ;;
    2)
        run_exp2
        ;;
    3)
        run_exp3
        ;;
    4)
        run_exp4
        ;;
    5)
        run_exp5
        ;;
    6)
        run_llm_mock
        ;;
    7)
        run_llm_real
        ;;
    all)
        echo "Running all experiments..."
        run_exp1
        run_exp2
        run_exp3
        run_exp4
        run_exp5
        echo ""
        echo "========================================"
        echo "All experiments complete!"
        echo "========================================"
        ;;
    *)
        echo "Invalid choice: $choice"
        exit 1
        ;;
esac

echo ""
echo "Done!"
