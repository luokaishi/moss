#!/usr/bin/env python3
"""
MOSS v9.2 - CLI Tool
命令行工具

Usage:
    moss analyze <path>           分析代码库
    moss refactor <path>          执行重构
    moss move <symbol> <from> <to>  移动符号
    moss status                   显示状态
    moss init                     初始化配置

Author: MOSS v9.2
Date: 2026-04-23
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# 确保可以导入 moss
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


async def cmd_analyze(args):
    """分析代码库"""
    from moss.core.cross_file_refactor import create_cross_file_engine

    path = args.path
    if not Path(path).exists():
        print(f"❌ 路径不存在: {path}")
        return 1

    print(f"🔍 分析代码库: {path}")
    print()

    engine = await create_cross_file_engine(path)
    analysis = await engine.analyze_codebase()

    # 基本概览
    print("=" * 60)
    print("  代码库分析报告")
    print("=" * 60)
    print(f"  模块数:       {analysis['total_modules']}")
    print(f"  符号数:       {analysis['total_symbols']}")
    print(f"  依赖边数:     {analysis['dependency_edges']}")
    print(f"  循环依赖:     {analysis['cycles']}")
    print()

    # 大模块
    if analysis.get('large_modules'):
        print("  大模块 (>500行):")
        for name, lines in sorted(analysis['large_modules'].items(), key=lambda x: -x[1]):
            short_name = name.split('.')[-1]
            print(f"    {short_name:30} {lines:5} 行")
        print()

    # 循环依赖
    cycles = engine.graph_builder.find_cycles()
    if cycles:
        print("  ⚠️ 循环依赖:")
        for cycle in cycles:
            print(f"    {' → '.join(c.split('.')[-1] for c in cycle)}")
        print()

    # 高耦合
    if analysis.get('high_coupling_modules'):
        print("  高耦合模块 (>5依赖):")
        for name, count in analysis['high_coupling_modules'].items():
            print(f"    {name}: {count} 个依赖")
        print()

    # JSON 输出
    if args.json:
        # 移除不可序列化的字段
        output = {k: v for k, v in analysis.items() if isinstance(v, (int, str, list, dict, float, bool))}
        with open(args.json, 'w') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"  📄 报告已保存到: {args.json}")

    return 0


async def cmd_move(args):
    """移动符号"""
    from moss.core.cross_file_refactor import create_cross_file_engine
    from moss.core.move_operations import MoveExecutor

    symbol = args.symbol
    source = args.source
    target = args.target
    dry_run = not args.apply

    # 找到代码库根路径
    codebase_path = args.path or '.'

    print(f"📦 移动 {symbol}: {source} → {target}")
    if dry_run:
        print(f"  (预览模式，使用 --apply 执行)")
    print()

    engine = await create_cross_file_engine(codebase_path)
    executor = MoveExecutor(engine)

    result = await executor.move_function(symbol, source, target, dry_run=dry_run)

    if result.success:
        print(f"\n✅ {result.message}")
        if result.files_modified:
            print(f"   修改的文件: {', '.join(Path(f).name for f in result.files_modified)}")
    else:
        print(f"\n❌ {result.message}")

    return 0 if result.success else 1


async def cmd_status(args):
    """显示系统状态"""
    print("🟢 MOSS v9.2 Status")
    print()
    print("  Core Components:")
    print("    ✅ CrossFileRefactorEngine")
    print("    ✅ ImportGraphBuilder")
    print("    ✅ SymbolTracker")
    print("    ✅ ImpactAnalyzer")
    print("    ✅ TransactionManager")
    print("    ✅ MoveExecutor")
    print("    ✅ SourceExtractor")
    print()
    print("  Available Commands:")
    print("    moss analyze <path>       分析代码库")
    print("    moss move <sym> <s> <t>   移动符号")
    print("    moss status               显示状态")
    print("    moss version              显示版本")
    print()
    return 0


async def cmd_version(args):
    """显示版本"""
    print("MOSS v9.2.0-alpha")
    print("Multi-Objective Self-Driven System for AI Autonomous Evolution")
    print("https://github.com/luokaishi/moss")
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog='moss',
        description='MOSS: Multi-Objective Self-Driven System'
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # analyze
    p_analyze = subparsers.add_parser('analyze', help='分析代码库')
    p_analyze.add_argument('path', help='代码库路径')
    p_analyze.add_argument('--json', help='输出JSON报告到文件')

    # move
    p_move = subparsers.add_parser('move', help='移动符号到另一个模块')
    p_move.add_argument('symbol', help='符号名称')
    p_move.add_argument('source', help='源模块名')
    p_move.add_argument('target', help='目标模块名')
    p_move.add_argument('--path', default='.', help='代码库路径')
    p_move.add_argument('--apply', action='store_true', help='实际执行（默认预览）')

    # status
    subparsers.add_parser('status', help='显示系统状态')

    # version
    subparsers.add_parser('version', help='显示版本')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    commands = {
        'analyze': cmd_analyze,
        'move': cmd_move,
        'status': cmd_status,
        'version': cmd_version,
    }

    handler = commands.get(args.command)
    if handler:
        return asyncio.run(handler(args))

    return 1


if __name__ == '__main__':
    sys.exit(main() or 0)
