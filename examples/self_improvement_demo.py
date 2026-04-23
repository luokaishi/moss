#!/usr/bin/env python3
"""
MOSS v9.0 - 自改写演示
展示 SelfImprovementOrchestrator + AgentRegistry 协同工作

Author: MOSS v9.0
Date: 2026-04-23
"""

import asyncio
import sys
sys.path.insert(0, '/workspace/moss')

from moss.core.agent_registry import create_registry, AgentStatus, HealthStatus
from moss.core.message_bus import create_message_bus
from moss.core.conflict_resolver import ConflictResolver
from moss.core.self_improvement import (
    create_orchestrator, ImprovementType, ImprovementStatus
)


class RefactorAgent:
    """重构专用Agent"""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.improvements_made = 0

    async def handle_refactor_task(self, task_info):
        """处理重构任务"""
        print(f"  [{self.agent_id}] 正在重构: {task_info.get('function_name', 'unknown')}")
        self.improvements_made += 1
        return True


class OptimizeAgent:
    """优化专用Agent"""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.optimizations_made = 0

    async def handle_optimize_task(self, task_info):
        """处理优化任务"""
        print(f"  [{self.agent_id}] 正在优化性能")
        self.optimizations_made += 1
        return True


class BugFixAgent:
    """Bug修复Agent"""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.bugs_fixed = 0

    async def handle_bugfix_task(self, task_info):
        """处理Bug修复"""
        print(f"  [{self.agent_id}] 正在修复Bug")
        self.bugs_fixed += 1
        return True


async def main():
    """自改写演示主函数"""
    print("=" * 70)
    print("MOSS v9.0 - Agent自改写演示")
    print("=" * 70)

    # 1. 初始化基础设施
    print("\n[1] 初始化基础设施...")
    registry = await create_registry()
    message_bus = await create_message_bus()
    conflict_resolver = ConflictResolver()
    print("   ✅ 基础设施就绪")

    # 2. 注册改进专用Agent
    print("\n[2] 注册改进专用Agent...")

    # 重构Agent
    refactor_agent_id = await registry.register(
        name="RefactorAgent-1",
        capabilities=["code_refactoring", "code_improvement"],
        metadata={
            "priority": 3,
            "specialization": "long_functions",
            "max_complexity": 10
        }
    )
    await registry.update_status(refactor_agent_id, AgentStatus.IDLE)
    await registry.update_health(refactor_agent_id, HealthStatus.HEALTHY)
    print(f"   ✅ RefactorAgent 注册: {refactor_agent_id}")

    # 优化Agent
    optimize_agent_id = await registry.register(
        name="OptimizeAgent-1",
        capabilities=["performance_optimization", "code_improvement"],
        metadata={
            "priority": 4,
            "specialization": "performance"
        }
    )
    await registry.update_status(optimize_agent_id, AgentStatus.IDLE)
    await registry.update_health(optimize_agent_id, HealthStatus.HEALTHY)
    print(f"   ✅ OptimizeAgent 注册: {optimize_agent_id}")

    # Bug修复Agent
    bugfix_agent_id = await registry.register(
        name="BugFixAgent-1",
        capabilities=["bug_fixing", "code_improvement"],
        metadata={
            "priority": 5,  # Bug修复优先级最高
            "specialization": "todos"
        }
    )
    await registry.update_status(bugfix_agent_id, AgentStatus.IDLE)
    await registry.update_health(bugfix_agent_id, HealthStatus.HEALTHY)
    print(f"   ✅ BugFixAgent 注册: {bugfix_agent_id}")

    # 3. 创建自改写协调器
    print("\n[3] 创建自改写协调器...")
    orchestrator = await create_orchestrator(
        registry=registry,
        message_bus=message_bus,
        conflict_resolver=conflict_resolver,
        codebase_path='/workspace/moss'
    )
    print("   ✅ 协调器就绪")

    # 4. 扫描代码库
    print("\n" + "=" * 70)
    print("【阶段1】代码库扫描")
    print("=" * 70)

    opportunities = await orchestrator.scan_for_improvements(
        target_paths=['/workspace/moss/moss/core'],
        min_severity=5  # 只关注严重度≥5的问题
    )

    print(f"\n发现 {len(opportunities)} 个高优先级改进机会:")

    # 按类型分组显示
    by_type = {}
    for opp in opportunities:
        t = opp.improvement_type.name
        by_type[t] = by_type.get(t, [])
        by_type[t].append(opp)

    for type_name, opps in sorted(by_type.items(), key=lambda x: -len(x[1])):
        print(f"\n  [{type_name}] {len(opps)} 个:")
        for opp in opps[:3]:  # 每类显示前3个
            location = f"{opp.location.file_path.split('/')[-1]}:{opp.location.line_start}"
            print(f"    - {location} | S={opp.severity} | {opp.description[:45]}...")
        if len(opps) > 3:
            print(f"    ... 还有 {len(opps) - 3} 个")

    # 5. 执行改进任务
    print("\n" + "=" * 70)
    print("【阶段2】执行改进任务")
    print("=" * 70)

    # 选择前5个机会创建任务
    selected_opportunities = opportunities[:5]
    results = []

    for i, opp in enumerate(selected_opportunities, 1):
        print(f"\n[{i}/{len(selected_opportunities)}] 处理改进机会...")
        print(f"  类型: {opp.improvement_type.name}")
        print(f"  位置: {opp.location.file_path.split('/')[-1]}:{opp.location.line_start}")
        print(f"  描述: {opp.description[:60]}...")

        # 创建任务
        task_id = await orchestrator.create_improvement_task(opp)
        print(f"  任务ID: {task_id}")

        # 执行任务
        result = await orchestrator.execute_improvement(task_id)
        results.append(result)

        status = "✅" if result.success else "❌"
        print(f"  结果: {status} {result.message}")

        if result.diff:
            print(f"\n  代码变更预览:")
            diff_lines = result.diff.split('\n')[:10]
            for line in diff_lines:
                prefix = "    "
                if line.startswith('+'):
                    prefix = "    + "
                elif line.startswith('-'):
                    prefix = "    - "
                print(f"{prefix}{line[:70]}")
            diff_line_count = len(result.diff.split('\n'))
            if diff_line_count > 10:
                print(f"    ... 还有 {diff_line_count - 10} 行")

    # 6. 统计总结
    print("\n" + "=" * 70)
    print("【阶段3】执行统计")
    print("=" * 70)

    stats = await orchestrator.get_statistics()
    success_count = sum(1 for r in results if r.success)
    fail_count = len(results) - success_count

    print(f"\n任务执行统计:")
    print(f"  总任务数: {stats['total_tasks']}")
    print(f"  成功: {success_count} ({success_count/len(results)*100:.1f}%)")
    print(f"  失败: {fail_count} ({fail_count/len(results)*100:.1f}%)")

    if stats['by_type']:
        print(f"\n按类型分布:")
        for type_name, count in sorted(stats['by_type'].items(), key=lambda x: -x[1]):
            bar = "█" * count
            print(f"  {type_name:12} {bar} {count}")

    # 7. 清理
    print("\n" + "=" * 70)
    print("【阶段4】资源清理")
    print("=" * 70)

    await registry.shutdown()
    await message_bus.shutdown()
    print("   ✅ 所有资源已释放")

    print("\n" + "=" * 70)
    print("🎉 Agent自改写演示完成!")
    print("=" * 70)
    print("\n核心能力展示:")
    print("  ✅ 代码自动扫描与分析")
    print("  ✅ 多类型改进任务识别")
    print("  ✅ Agent智能分配")
    print("  ✅ 安全测试与回滚机制")
    print("  ✅ 完整执行追踪")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n演示被用户中断")
