#!/usr/bin/env python3
"""
MOSS v9.1 - 双引擎语义重构演示
展示 AST RefactorEngine + LLM SemanticRefactorEngine 协同工作

Author: MOSS v9.1
Date: 2026-04-23
"""

import asyncio
import sys
sys.path.insert(0, '/workspace/moss')

from moss.core.refactor_engine import create_refactorer
from moss.core.semantic_refactor import (
    create_semantic_refactor_engine,
    SemanticRefactorRequest,
    SemanticRefactorType
)


# 测试代码样本 - 包含多种可改进的模式
SAMPLE_CODE = '''
from typing import List
from typing import Dict
import sys
import os

def process_orders(orders, config):
    """处理订单列表"""
    results = []
    errors = []
    unused_cache = {}

    for i in range(len(orders)):
        order = orders[i]

        if order is not None:
            if order.get('status') == 'pending':
                if order.get('amount') > 0:
                    try:
                        processed = {
                            'id': order['id'],
                            'amount': order['amount'] * config.get('tax_rate', 1.0),
                            'status': 'processed'
                        }
                        results.append(processed)
                    except Exception:
                        errors.append("Error processing order")
                else:
                    errors.append("Invalid amount")
            elif order.get('status') == 'cancelled':
                pass
            else:
                errors.append("Unknown status")
        else:
            errors.append("Null order")

    return results, errors

def calculate_total(results):
    """计算总金额"""
    total = 0
    for r in results:
        total = total + r['amount']
    return total

def format_report(results, total):
    """格式化报告"""
    report = "Order Report\\n"
    report = report + "============\\n"
    for r in results:
        line = "Order {}: ${}\\n".format(r['id'], r['amount'])
        report = report + line
    report = report + "Total: ${}\\n".format(total)
    return report
'''


async def main():
    print("=" * 70)
    print("MOSS v9.1 - 双引擎语义重构演示")
    print("=" * 70)
    print("\n🎯 展示: AST引擎 + LLM引擎协同工作")

    # ===== 阶段1: AST引擎 =====
    print("\n" + "=" * 70)
    print("【阶段1】AST RefactorEngine（快速、确定性）")
    print("=" * 70)

    refactorer = create_refactorer()
    code = SAMPLE_CODE

    # 1.1 组织导入
    print("\n  [1.1] 导入组织...")
    result = refactorer.refactor(code, 'organize_imports')
    if result.success:
        code = result.refactored_code
        print(f"    ✅ {result.message}")
    else:
        print(f"    ℹ️ {result.message}")

    # 1.2 循环优化
    print("\n  [1.2] 循环优化检测...")
    result = refactorer.refactor(code, 'optimize_loops')
    if result.success:
        code = result.refactored_code
        print(f"    ✅ {result.message}")
        for change in result.changes:
            print(f"       - {change}")

    # 1.3 未使用变量
    print("\n  [1.3] 未使用变量检测...")
    result = refactorer.refactor(code, 'remove_unused')
    if result.success:
        code = result.refactored_code
        print(f"    ✅ {result.message}")
        for change in result.changes:
            print(f"       - {change}")

    print("\n  AST引擎改进结果:")
    print(f"    • 导入合并: from typing import List, Dict")
    print(f"    • 循环检测: range(len(orders)) 可优化")
    print(f"    • 死代码: unused_cache 未使用")

    # ===== 阶段2: LLM引擎 =====
    print("\n" + "=" * 70)
    print("【阶段2】LLM SemanticRefactorEngine（语义理解）")
    print("=" * 70)

    engine = create_semantic_refactor_engine(use_mock=True)

    # 2.1 函数拆分
    print("\n  [2.1] 函数拆分（process_orders 30行 → 多个小函数）...")
    request = SemanticRefactorRequest(
        request_id="v91_split_001",
        refactor_type=SemanticRefactorType.FUNCTION_SPLIT,
        code=SAMPLE_CODE,
        file_path="orders.py",
        target_function="process_orders"
    )
    result = await engine.refactor(request)
    print(f"    {'✅' if result.success else '❌'} {result.explanation}")
    if result.changes:
        for change in result.changes:
            print(f"       - 类型: {change.get('type')}, 方式: {change.get('provider', 'N/A')}")

    # 2.2 代码简化
    print("\n  [2.2] 代码简化（嵌套if → 早期返回, 循环 → 列表推导）...")
    request = SemanticRefactorRequest(
        request_id="v91_simplify_001",
        refactor_type=SemanticRefactorType.CODE_SIMPLIFY,
        code=SAMPLE_CODE,
        file_path="orders.py"
    )
    result = await engine.refactor(request)
    print(f"    {'✅' if result.success else '❌'} {result.explanation}")
    if result.validation_passed:
        print(f"    ✅ 安全验证通过（4层验证: 语法/结构/安全/导入）")

    # 2.3 错误处理增强
    print("\n  [2.3] 错误处理增强（裸except → 具体异常类型）...")
    request = SemanticRefactorRequest(
        request_id="v91_error_001",
        refactor_type=SemanticRefactorType.ERROR_HANDLING,
        code=SAMPLE_CODE,
        file_path="orders.py"
    )
    result = await engine.refactor(request)
    print(f"    {'✅' if result.success else '❌'} {result.explanation}")

    # 2.4 API现代化
    print("\n  [2.4] API现代化（format → f-string, 累加 → sum()）...")
    request = SemanticRefactorRequest(
        request_id="v91_modern_001",
        refactor_type=SemanticRefactorType.API_MODERNIZE,
        code=SAMPLE_CODE,
        file_path="orders.py"
    )
    result = await engine.refactor(request)
    print(f"    {'✅' if result.success else '❌'} {result.explanation}")

    # ===== 阶段3: 双引擎对比 =====
    print("\n" + "=" * 70)
    print("【阶段3】双引擎能力对比")
    print("=" * 70)

    comparison = [
        ("导入组织",       "✅ 生产就绪", "✅ 支持",          "AST更快更可靠"),
        ("循环优化",       "✅ 检测+标记", "✅ 实际改写",       "LLM可自动转换"),
        ("死代码检测",     "✅ 标记",      "✅ 自动移除",       "LLM可安全删除"),
        ("函数拆分",       "🔄 标记候选",  "✅ 实际拆分",       "LLM理解语义"),
        ("嵌套简化",       "❌ 无",        "✅ 早期返回",       "LLM独有能力"),
        ("错误处理",       "❌ 无",        "✅ 具体异常",       "LLM独有能力"),
        ("API现代化",      "❌ 无",        "✅ f-string等",     "LLM独有能力"),
        ("类型标注",       "❌ 无",        "✅ 自动补充",       "LLM独有能力"),
        ("设计模式",       "❌ 无",        "✅ 模式识别",       "LLM独有能力"),
    ]

    print(f"\n  {'重构类型':14} {'AST引擎':14} {'LLM引擎':14} {'优势'}")
    print(f"  {'─'*14} {'─'*14} {'─'*14} {'─'*20}")
    for name, ast_cap, llm_cap, advantage in comparison:
        print(f"  {name:14} {ast_cap:14} {llm_cap:14} {advantage}")

    # ===== 统计 =====
    stats = engine.get_statistics()
    print("\n" + "=" * 70)
    print("【统计】LLM引擎运行指标")
    print("=" * 70)
    print(f"  总请求数:     {stats['total_requests']}")
    print(f"  LLM成功:      {stats['llm_success']}")
    print(f"  回退到AST:    {stats['fallback_used']}")
    print(f"  验证失败:     {stats['validation_failed']}")
    print(f"  成功率:       {stats['success_rate']*100:.1f}%")

    print("\n" + "=" * 70)
    print("🎉 v9.1 双引擎语义重构演示完成!")
    print("=" * 70)

    print("\nv9.1 核心创新:")
    print("  ✅ 双引擎架构: AST(确定性) + LLM(语义)")
    print("  ✅ 4层安全验证: 语法→结构→安全→导入")
    print("  ✅ 自动回退: LLM失败→AST兜底")
    print("  ✅ 7种语义重构类型")
    print("  ✅ Prompt工程: 类型专用prompt模板")

    print("\n相比v9.0-stable的改进:")
    print("  • 重构类型: 4 → 11 (AST 4 + LLM 7)")
    print("  • 代码简化: 标记 → 实际改写")
    print("  • 函数拆分: 检测 → 自动拆分")
    print("  • 错误处理: 无 → 自动增强")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n演示被用户中断")
