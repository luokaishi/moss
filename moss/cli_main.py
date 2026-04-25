#!/usr/bin/env python3
"""
MOSS v9.3 - Command Line Interface
统一命令行入口

子命令:
  moss analyze    - 分析代码质量
  moss refactor   - 执行重构操作
  moss server     - 启动 LSP 服务器
  moss cache      - 管理缓存
  moss benchmark  - 性能基准测试
  moss init       - 初始化项目配置

Author: MOSS v9.3
Date: 2026-04-24
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Optional


def create_parser() -> argparse.ArgumentParser:
    """创建命令行解析器"""
    parser = argparse.ArgumentParser(
        prog="moss",
        description="MOSS v9.6.0 - Multi-Objective Self-Driven System",
        epilog="Example: moss analyze ./src --format json --output report.json"
    )
    parser.add_argument("--version", action="version", version="MOSS v9.6.0")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--quiet", "-q", action="store_true", help="静默模式")

    subparsers = parser.add_subparsers(dest="command", help="可用子命令")

    # ── analyze ──
    analyze_parser = subparsers.add_parser("analyze", help="分析代码质量")
    analyze_parser.add_argument("path", nargs="?", default=".", help="项目路径")
    analyze_parser.add_argument("--format", "-f", choices=["text", "json", "junit", "github"], default="text", help="输出格式")
    analyze_parser.add_argument("--output", "-o", help="输出文件路径")
    analyze_parser.add_argument("--threshold", type=int, default=50, help="函数行数阈值")
    analyze_parser.add_argument("--complexity", type=int, default=10, help="复杂度阈值")
    analyze_parser.add_argument("--no-cache", action="store_true", help="禁用缓存")
    analyze_parser.add_argument("--parallel", "-p", type=int, default=0, help="并行工作进程数 (0=自动)")
    analyze_parser.add_argument("--incremental", action="store_true", default=True, help="增量分析")
    analyze_parser.add_argument("--fail-on-error", action="store_true", help="有错误时返回非零退出码")

    # ── refactor ──
    refactor_parser = subparsers.add_parser("refactor", help="执行重构操作")
    refactor_parser.add_argument("path", nargs="?", default=".", help="项目路径")
    refactor_sub = refactor_parser.add_subparsers(dest="refactor_type", help="重构类型")

    # refactor move
    move_parser = refactor_sub.add_parser("move", help="移动符号")
    move_parser.add_argument("--symbol", required=True, help="符号名")
    move_parser.add_argument("--source", required=True, help="源模块")
    move_parser.add_argument("--target", required=True, help="目标模块")
    move_parser.add_argument("--dry-run", action="store_true", help="预览模式")

    # refactor extract
    extract_parser = refactor_sub.add_parser("extract", help="提取函数")
    extract_parser.add_argument("--file", required=True, help="文件路径")
    extract_parser.add_argument("--start-line", type=int, required=True, help="起始行")
    extract_parser.add_argument("--end-line", type=int, required=True, help="结束行")
    extract_parser.add_argument("--name", required=True, help="新函数名")

    # refactor imports
    imports_parser = refactor_sub.add_parser("imports", help="整理导入")
    imports_parser.add_argument("--file", required=True, help="文件路径")

    # ── server ──
    server_parser = subparsers.add_parser("server", help="启动 LSP 服务器")
    server_parser.add_argument("--mode", choices=["stdio", "tcp"], default="stdio", help="传输模式")
    server_parser.add_argument("--host", default="127.0.0.1", help="TCP 监听地址")
    server_parser.add_argument("--port", type=int, default=2087, help="TCP 监听端口")

    # ── cache ──
    cache_parser = subparsers.add_parser("cache", help="管理缓存")
    cache_sub = cache_parser.add_subparsers(dest="cache_action", help="缓存操作")
    cache_sub.add_parser("status", help="查看缓存状态")
    cache_sub.add_parser("clear", help="清除所有缓存")
    cache_sub.add_parser("warm", help="预热缓存")
    cache_parser.add_argument("path", nargs="?", default=".", help="项目路径")

    # ── agent ──
    agent_parser = subparsers.add_parser("agent", help="运行自主任务 Agent")
    agent_parser.add_argument("--task", "-t",
                              choices=["file_organization", "log_analysis", "system_monitor",
                                       "code_review", "backup_cleanup"],
                              help="任务类型")
    agent_parser.add_argument("--path", "-p", default=".", help="工作目录")
    agent_parser.add_argument("--max-cycles", "-c", type=int, default=100, help="最大执行周期")
    agent_parser.add_argument("--list", "-l", action="store_true", help="列出可用任务")

    # ── report ──
    report_parser = subparsers.add_parser("report", help="生成报告")
    report_sub = report_parser.add_subparsers(dest="report_type", help="报告类型")

    # report cost
    cost_report_parser = report_sub.add_parser("cost", help="LLM 成本报告")
    cost_report_parser.add_argument("--history", help="历史成本数据文件路径")
    cost_report_parser.add_argument("--budget", "-b", type=float, help="显示预算对比 (USD)")

    # ── validate ──
    validate_parser = subparsers.add_parser("validate", help="统计验证实验")
    validate_parser.add_argument("--experiment", "-e", required=True, help="实验数据 JSON 文件")
    validate_parser.add_argument("--control", "-c", required=True, help="对照组数据 JSON 文件")
    validate_parser.add_argument("--name", "-n", default="Experiment", help="实验名称")
    validate_parser.add_argument("--alpha", type=float, default=0.05, help="显著性水平")
    validate_parser.add_argument("--output", "-o", help="输出报告路径")

    # ── watch ──
    watch_parser = subparsers.add_parser("watch", help="监控文件变更并实时分析")
    watch_parser.add_argument("path", nargs="?", default=".", help="监控路径")
    watch_parser.add_argument("--pattern", "-p", action="append",
                              help="文件模式 (可多次指定，如: *.py)")
    watch_parser.add_argument("--no-analyze", action="store_true",
                              help="禁用自动分析")
    watch_parser.add_argument("--auto-refactor", action="store_true",
                              help="自动重构 (谨慎使用)")
    watch_parser.add_argument("--debounce", "-d", type=float, default=1.0,
                              help="防抖时间 (秒)")

    # ── benchmark ──
    bench_parser = subparsers.add_parser("benchmark", help="性能基准测试")
    bench_parser.add_argument("path", nargs="?", default=".", help="项目路径")
    bench_parser.add_argument("--iterations", type=int, default=3, help="迭代次数")
    bench_parser.add_argument("--compare", action="store_true", help="对比串行 vs 并行")

    # ── init ──
    init_parser = subparsers.add_parser("init", help="初始化项目配置")
    init_parser.add_argument("path", nargs="?", default=".", help="项目路径")
    init_parser.add_argument("--force", action="store_true", help="覆盖现有配置")

    return parser


# ──────────────────────────────────────────────────────────────
# Analyze Command
# ──────────────────────────────────────────────────────────────

async def cmd_analyze(args: argparse.Namespace) -> int:
    """执行代码分析"""
    from moss.core.incremental_analyzer import IncrementalAnalyzer, MultiLevelCache
    from moss.core.parallel_analyzer import ParallelAnalyzer
    import ast

    project_path = Path(args.path).resolve()
    if not project_path.exists():
        print(f"错误: 路径不存在 - {project_path}")
        return 1

    print(f"MOSS v9.3 - 分析项目: {project_path}")

    # 收集 Python 文件
    python_files = []
    for py_file in project_path.rglob("*.py"):
        if '__pycache__' not in str(py_file) and '.moss' not in str(py_file):
            python_files.append(py_file)

    if not python_files:
        print("未找到 Python 文件")
        return 0

    print(f"找到 {len(python_files)} 个 Python 文件")

    # 分析
    start_time = time.time()
    results = []
    errors = 0
    warnings = 0
    info = 0

    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))
            file_issues = []

            # 检查长函数
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    lines = (node.end_lineno or node.lineno) - node.lineno
                    if lines > args.threshold:
                        file_issues.append({
                            'type': 'long_function',
                            'severity': 'warning',
                            'line': node.lineno,
                            'message': f"函数 '{node.name}' 过长 ({lines} 行)",
                            'function': node.name,
                        })
                        warnings += 1

                    # 复杂度检查
                    complexity = 1
                    for child in ast.walk(node):
                        if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                            complexity += 1
                    if complexity > args.complexity:
                        file_issues.append({
                            'type': 'high_complexity',
                            'severity': 'info',
                            'line': node.lineno,
                            'message': f"函数 '{node.name}' 复杂度高 ({complexity})",
                            'function': node.name,
                        })
                        info += 1

            # 未使用的导入
            imported = set()
            used = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported.add((alias.asname or alias.name, node.lineno))
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        imported.add((alias.asname or alias.name, node.lineno))
                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    used.add(node.id)

            for name, line_no in imported:
                if name not in used:
                    file_issues.append({
                        'type': 'unused_import',
                        'severity': 'info',
                        'line': line_no,
                        'message': f"未使用的导入: {name}",
                    })
                    info += 1

            if file_issues:
                results.append({
                    'file': str(file_path.relative_to(project_path)),
                    'issues': file_issues,
                })

        except SyntaxError as e:
            results.append({
                'file': str(file_path.relative_to(project_path)),
                'issues': [{
                    'type': 'syntax_error',
                    'severity': 'error',
                    'line': e.lineno or 1,
                    'message': f"语法错误: {e.msg}",
                }],
            })
            errors += 1
        except Exception as e:
            errors += 1

    duration = time.time() - start_time
    total_issues = errors + warnings + info

    # 输出结果
    if args.format == 'json':
        output = {
            'version': '9.3.0',
            'project': str(project_path),
            'duration': round(duration, 3),
            'summary': {
                'total_files': len(python_files),
                'files_with_issues': len(results),
                'total_issues': total_issues,
                'errors': errors,
                'warnings': warnings,
                'info': info,
            },
            'results': results,
        }
        output_str = json.dumps(output, indent=2, ensure_ascii=False)

    elif args.format == 'github':
        # GitHub Actions 注解格式
        lines = []
        for result in results:
            rel_path = result['file']
            for issue in result['issues']:
                severity_map = {'error': 'error', 'warning': 'warning', 'info': 'notice'}
                gh_severity = severity_map.get(issue['severity'], 'notice')
                lines.append(
                    f"::{gh_severity} file={rel_path},line={issue['line']}::"
                    f"[MOSS] {issue['message']}"
                )
        output_str = '\n'.join(lines) if lines else '::notice ::[MOSS] No issues found'

    else:
        # text 格式
        lines = []
        lines.append(f"\n{'='*60}")
        lines.append(f"MOSS v9.3.0 分析报告")
        lines.append(f"{'='*60}")
        lines.append(f"项目: {project_path}")
        lines.append(f"文件: {len(python_files)}")
        lines.append(f"耗时: {duration:.2f}s")
        lines.append(f"{'─'*60}")
        lines.append(f"问题: {total_issues} (错误: {errors}, 警告: {warnings}, 信息: {info})")
        lines.append(f"{'─'*60}")

        for result in results:
            for issue in result['issues']:
                icon = {'error': '✗', 'warning': '⚠', 'info': 'ℹ'}.get(issue['severity'], '•')
                lines.append(
                    f"  {icon} {result['file']}:{issue['line']} - {issue['message']}"
                )

        lines.append(f"{'='*60}")
        output_str = '\n'.join(lines)

    # 写入文件或输出
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_str)
        print(f"报告已写入: {args.output}")
    else:
        print(output_str)

    # 退出码
    if args.fail_on_error and errors > 0:
        return 1
    return 0


# ──────────────────────────────────────────────────────────────
# Refactor Command
# ──────────────────────────────────────────────────────────────

async def cmd_refactor(args: argparse.Namespace) -> int:
    """执行重构"""
    from moss.core.cross_file_refactor import CrossFileRefactorEngine

    project_path = Path(args.path).resolve()
    print(f"MOSS v9.3 - 重构: {args.refactor_type}")

    if args.refactor_type == 'move':
        engine = CrossFileRefactorEngine(str(project_path))
        await engine.initialize()

        result = await engine.move_symbol(
            args.symbol,
            args.source,
            args.target,
            dry_run=args.dry_run
        )

        if result.success:
            print(f"✓ 移动成功: {args.symbol} → {args.target}")
            print(f"  修改文件: {len(result.files_modified)}")
            for f in result.files_modified:
                print(f"    - {f}")
        else:
            print(f"✗ 移动失败: {result.message}")
            return 1

    elif args.refactor_type == 'imports':
        from moss.core.refactor_engine import CodeRefactorer, ImportOrganizer
        organizer = ImportOrganizer()

        with open(args.file, 'r') as f:
            content = f.read()

        result = organizer.organize(content)

        with open(args.file, 'w') as f:
            f.write(result)

        print(f"✓ 导入整理完成: {args.file}")

    else:
        print(f"未知重构类型: {args.refactor_type}")
        return 1

    return 0


# ──────────────────────────────────────────────────────────────
# Server Command
# ──────────────────────────────────────────────────────────────

async def cmd_server(args: argparse.Namespace) -> int:
    """启动 LSP 服务器"""
    from moss.core.lsp_server import MossAnalysisProvider, LSPProtocolHandler

    provider = MossAnalysisProvider(".")
    handler = LSPProtocolHandler(provider)

    if args.mode == 'stdio':
        print("MOSS LSP Server starting (stdio mode)...", file=sys.stderr)
        handler.start_stdio()
    elif args.mode == 'tcp':
        handler.start_tcp(args.host, args.port)

    return 0


# ──────────────────────────────────────────────────────────────
# Cache Command
# ──────────────────────────────────────────────────────────────

async def cmd_cache(args: argparse.Namespace) -> int:
    """管理缓存"""
    from moss.core.incremental_analyzer import MultiLevelCache

    project_path = Path(args.path).resolve()
    cache = MultiLevelCache(str(project_path))

    if args.cache_action == 'status':
        stats = cache.get_stats()
        print("MOSS 缓存状态:")
        print(f"  L1 缓存: {stats.get('l1_size', 0)} 条目")
        print(f"  L2 缓存: {stats.get('l2_entries', 0)} 条目")
        print(f"  L3 缓存: {stats.get('l3_files', 0)} 文件")
        print(f"  提升次数: {stats.get('promotions', 0)}")
        print(f"  驱逐次数: {stats.get('evictions', 0)}")

    elif args.cache_action == 'clear':
        cache.l1.cache.clear()
        cache.l2.cleanup(max_age=0)
        print("✓ 缓存已清除")

    elif args.cache_action == 'warm':
        # 预热缓存：分析所有文件并缓存结果
        python_files = list(project_path.rglob("*.py"))
        print(f"预热缓存: {len(python_files)} 个文件")
        for f in python_files:
            try:
                with open(f, 'r') as fh:
                    content = fh.read()
                import hashlib
                checksum = hashlib.sha256(content.encode()).hexdigest()
                cache.set_file_analysis(str(f), checksum, {'analyzed': True})
            except Exception:
                pass
        print("✓ 缓存预热完成")

    return 0


# ──────────────────────────────────────────────────────────────
# Agent Command
# ──────────────────────────────────────────────────────────────

async def cmd_agent(args: argparse.Namespace) -> int:
    """运行自主任务 Agent"""
    from moss.plugins.task_agent_plugin import TaskAgentPlugin, run_task_cli

    if args.list:
        plugin = TaskAgentPlugin()
        tasks = plugin.list_tasks()
        print("\n可用任务:")
        print("-" * 60)
        for task in tasks:
            print(f"  {task['type']:20s} - {task['name']}")
            print(f"    {task['description']}")
        print()
        return 0

    return run_task_cli(args.task, args.path, args.max_cycles)


# ──────────────────────────────────────────────────────────────
# Report Command
# ──────────────────────────────────────────────────────────────

async def cmd_report(args: argparse.Namespace) -> int:
    """生成报告"""
    try:
        from moss.core.llm_cost_controller import LLMCostController, CostBudget, print_cost_report
    except ImportError:
        # Fallback for running from moss directory
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from moss.core.llm_cost_controller import LLMCostController, CostBudget, print_cost_report

    if args.report_type == 'cost':
        budget_usd = args.budget if args.budget else 10.0
        controller = LLMCostController(budget=CostBudget(budget_usd=budget_usd))

        if args.history and Path(args.history).exists():
            controller.load_history(Path(args.history))

        report = controller.generate_report()
        print_cost_report(report)
        return 0

    print(f"未知报告类型: {args.report_type}")
    return 1


# ──────────────────────────────────────────────────────────────
# Validate Command
# ──────────────────────────────────────────────────────────────

async def cmd_validate(args: argparse.Namespace) -> int:
    """统计验证实验"""
    try:
        from moss.core.statistical_validator import StatisticalValidator, ValidationConfig
    except ImportError:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from moss.core.statistical_validator import StatisticalValidator, ValidationConfig

    import json

    # 加载实验数据
    try:
        with open(args.experiment, 'r') as f:
            exp_data = json.load(f)
    except FileNotFoundError:
        print(f"错误: 实验数据文件不存在 - {args.experiment}")
        return 1
    except json.JSONDecodeError:
        print(f"错误: 实验数据文件格式错误 - {args.experiment}")
        return 1

    # 加载对照组数据
    try:
        with open(args.control, 'r') as f:
            ctrl_data = json.load(f)
    except FileNotFoundError:
        print(f"错误: 对照组数据文件不存在 - {args.control}")
        return 1
    except json.JSONDecodeError:
        print(f"错误: 对照组数据文件格式错误 - {args.control}")
        return 1

    # 创建验证器
    config = ValidationConfig(alpha=args.alpha)
    validator = StatisticalValidator(config)

    # 添加数据
    validator.add_experiment(
        args.name,
        exp_data if isinstance(exp_data, list) else exp_data.get('values', []),
        unit=exp_data.get('unit', '') if isinstance(exp_data, dict) else ''
    )
    validator.add_experiment(
        "Control",
        ctrl_data if isinstance(ctrl_data, list) else ctrl_data.get('values', []),
        unit=ctrl_data.get('unit', '') if isinstance(ctrl_data, dict) else ''
    )

    # 执行验证
    report = validator.validate_experiment(args.name, "Control")

    # 输出报告
    print(report.to_markdown())

    # 保存报告
    if args.output:
        validator.save_report(report, Path(args.output))
        print(f"\n✓ 报告已保存到: {args.output}.json 和 {args.output}.md")

    return 0


# ──────────────────────────────────────────────────────────────
# Watch Command
# ──────────────────────────────────────────────────────────────

async def cmd_watch(args: argparse.Namespace) -> int:
    """监控文件变更"""
    from moss.core.file_watcher import run_watch_cli

    project_path = Path(args.path).resolve()
    if not project_path.exists():
        print(f"错误: 路径不存在 - {project_path}")
        return 1

    patterns = args.pattern if args.pattern else None

    return await run_watch_cli(
        path=project_path,
        patterns=patterns,
        auto_analyze=not args.no_analyze,
        auto_refactor=args.auto_refactor,
        debounce=args.debounce,
    )


# ──────────────────────────────────────────────────────────────
# Benchmark Command
# ──────────────────────────────────────────────────────────────

async def cmd_benchmark(args: argparse.Namespace) -> int:
    """性能基准测试"""
    from moss.core.performance_engine import PerformanceEngine, PerformanceConfig

    project_path = Path(args.path).resolve()
    config = PerformanceConfig(max_workers=4)

    engine = PerformanceEngine(project_path, config)
    results = await engine.run_performance_benchmark()

    return 0


# ──────────────────────────────────────────────────────────────
# Init Command
# ──────────────────────────────────────────────────────────────

async def cmd_init(args: argparse.Namespace) -> int:
    """初始化项目配置"""
    project_path = Path(args.path).resolve()
    config_dir = project_path / '.moss'
    config_file = config_dir / 'config.json'

    if config_file.exists() and not args.force:
        print(f"配置已存在: {config_file}")
        print("使用 --force 覆盖")
        return 1

    config_dir.mkdir(exist_ok=True)

    default_config = {
        "version": "9.3.0",
        "project": str(project_path),
        "analysis": {
            "threshold": 50,
            "complexity_threshold": 10,
            "enable_incremental": True,
            "enable_parallel": True,
            "max_workers": 0,
        },
        "cache": {
            "l1_size": 1000,
            "l2_ttl": 3600,
            "l3_enabled": True,
        },
        "diagnostics": {
            "enabled": True,
            "show_unused_imports": True,
            "show_long_functions": True,
        },
        "refactoring": {
            "preview_changes": True,
            "auto_update_imports": True,
        },
    }

    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=2, ensure_ascii=False)

    print(f"✓ 项目配置已创建: {config_file}")

    # 创建 .mossignore
    mossignore = config_dir.parent / '.mossignore'
    if not mossignore.exists():
        with open(mossignore, 'w') as f:
            f.write("# MOSS ignore file\n")
            f.write("__pycache__/\n")
            f.write(".git/\n")
            f.write("*.pyc\n")
            f.write("venv/\n")
            f.write("node_modules/\n")
        print(f"✓ .mossignore 已创建")

    return 0


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────

async def async_main():
    """异步主入口"""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    command_map = {
        'analyze': cmd_analyze,
        'refactor': cmd_refactor,
        'server': cmd_server,
        'cache': cmd_cache,
        'agent': cmd_agent,
        'report': cmd_report,
        'validate': cmd_validate,
        'watch': cmd_watch,
        'benchmark': cmd_benchmark,
        'init': cmd_init,
    }

    handler = command_map.get(args.command)
    if handler:
        return await handler(args)
    else:
        parser.print_help()
        return 1


def main():
    """主入口"""
    try:
        exit_code = asyncio.run(async_main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
