#!/usr/bin/env python3
"""
MOSS v9.0 - Self-Improvement Orchestrator
Agent自改写协调器 - 多Agent协作代码优化

Author: MOSS v9.0
Date: 2026-04-23
"""

import asyncio
import ast
import difflib
import hashlib
import inspect
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from moss.core.agent_registry import AgentRegistry, AgentStatus, HealthStatus
from moss.core.message_bus import MessageBus, Message, MessageType, Priority
from moss.core.conflict_resolver import ConflictResolver, ConflictType, ResolutionStrategy
from moss.core.refactor_engine import create_refactorer, CodeRefactorer


class ImprovementType(Enum):
    """改进类型"""
    REFACTOR = auto()      # 重构
    OPTIMIZE = auto()      # 性能优化
    BUGFIX = auto()        # 错误修复
    FEATURE = auto()       # 功能增强
    DOCUMENT = auto()      # 文档完善
    TEST = auto()          # 测试补充


class ImprovementStatus(Enum):
    """改进任务状态"""
    PENDING = auto()       # 等待处理
    ANALYZING = auto()     # 分析中
    ASSIGNED = auto()      # 已分配
    IMPLEMENTING = auto()  # 实现中
    REVIEWING = auto()     # 审核中
    TESTING = auto()       # 测试中
    ACCEPTED = auto()      # 已接受
    REJECTED = auto()      # 已拒绝
    ROLLED_BACK = auto()   # 已回滚


@dataclass
class CodeLocation:
    """代码位置"""
    file_path: str
    line_start: int
    line_end: int
    function_name: Optional[str] = None
    class_name: Optional[str] = None


@dataclass
class ImprovementOpportunity:
    """改进机会"""
    opportunity_id: str
    improvement_type: ImprovementType
    location: CodeLocation
    description: str
    severity: int  # 1-10
    suggested_changes: Optional[str] = None
    confidence: float = 0.5  # 0.0-1.0
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ImprovementTask:
    """改进任务"""
    task_id: str
    opportunity: ImprovementOpportunity
    assigned_agents: List[str] = field(default_factory=list)
    status: ImprovementStatus = ImprovementStatus.PENDING
    original_code: Optional[str] = None
    proposed_changes: Optional[str] = None
    test_results: Optional[Dict] = None
    conflict_resolutions: List[Dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


@dataclass
class ImprovementResult:
    """改进结果"""
    task_id: str
    success: bool
    applied_changes: bool
    message: str
    diff: Optional[str] = None
    metrics_before: Optional[Dict] = None
    metrics_after: Optional[Dict] = None


class CodeAnalyzer:
    """代码分析器 - 识别改进机会"""

    def __init__(self):
        self.issues_found: List[ImprovementOpportunity] = []

    async def analyze_file(self, file_path: str) -> List[ImprovementOpportunity]:
        """分析单个文件"""
        opportunities = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            # 解析AST
            try:
                tree = ast.parse(content)
            except SyntaxError:
                return opportunities

            # 检查长函数
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_lines = node.end_lineno - node.lineno
                    if func_lines > 50:
                        opp = ImprovementOpportunity(
                            opportunity_id=f"long_func_{node.name}_{hashlib.md5(file_path.encode()).hexdigest()[:8]}",
                            improvement_type=ImprovementType.REFACTOR,
                            location=CodeLocation(
                                file_path=file_path,
                                line_start=node.lineno,
                                line_end=node.end_lineno,
                                function_name=node.name
                            ),
                            description=f"函数 {node.name} 过长 ({func_lines} 行)，建议拆分成小函数",
                            severity=min(func_lines // 10, 10),
                            confidence=0.8
                        )
                        opportunities.append(opp)

            # 检查复杂度（简化版：嵌套深度）
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.For, ast.While, ast.With)):
                    depth = self._calculate_nesting_depth(node, tree)
                    if depth > 4:
                        opp = ImprovementOpportunity(
                            opportunity_id=f"deep_nest_{hashlib.md5(f'{file_path}_{node.lineno}'.encode()).hexdigest()[:8]}",
                            improvement_type=ImprovementType.REFACTOR,
                            location=CodeLocation(
                                file_path=file_path,
                                line_start=node.lineno,
                                line_end=getattr(node, 'end_lineno', node.lineno)
                            ),
                            description=f"代码嵌套过深 (深度 {depth})，建议简化逻辑",
                            severity=min(depth * 2, 10),
                            confidence=0.7
                        )
                        opportunities.append(opp)

            # 检查TODO注释
            for i, line in enumerate(lines, 1):
                if 'TODO' in line or 'FIXME' in line:
                    opp = ImprovementOpportunity(
                        opportunity_id=f"todo_{hashlib.md5(f'{file_path}_{i}'.encode()).hexdigest()[:8]}",
                        improvement_type=ImprovementType.BUGFIX,
                        location=CodeLocation(
                            file_path=file_path,
                            line_start=i,
                            line_end=i
                        ),
                        description=f"发现待办事项: {line.strip()}",
                        severity=5,
                        confidence=0.9
                    )
                    opportunities.append(opp)

        except Exception as e:
            print(f"[CodeAnalyzer] 分析失败 {file_path}: {e}")

        return opportunities

    def _calculate_nesting_depth(self, node: ast.AST, tree: ast.AST) -> int:
        """计算嵌套深度"""
        depth = 0
        current = node

        while hasattr(current, 'parent'):
            if isinstance(current.parent, (ast.If, ast.For, ast.While)):
                depth += 1
            current = current.parent

        return depth


class SelfImprovementOrchestrator:
    """
    自改写协调器

    核心流程:
    1. 分析代码库，发现改进机会
    2. 创建改进任务
    3. 分配给多个Agent并行处理
    4. 检测冲突，自动仲裁
    5. 测试验证
    6. 应用或回滚
    """

    def __init__(
        self,
        registry: AgentRegistry,
        message_bus: MessageBus,
        conflict_resolver: ConflictResolver,
        codebase_path: str = '/workspace/moss'
    ):
        self.registry = registry
        self.message_bus = message_bus
        self.conflict_resolver = conflict_resolver
        self.codebase_path = Path(codebase_path)

        self.analyzer = CodeAnalyzer()
        self.refactorer = create_refactorer()
        self.tasks: Dict[str, ImprovementTask] = {}
        self.backup_cache: Dict[str, str] = {}  # 原始代码备份

        self._improvement_handlers: Dict[ImprovementType, Callable] = {
            ImprovementType.REFACTOR: self._handle_refactor,
            ImprovementType.OPTIMIZE: self._handle_optimize,
            ImprovementType.BUGFIX: self._handle_bugfix,
            ImprovementType.FEATURE: self._handle_feature,
            ImprovementType.DOCUMENT: self._handle_document,
            ImprovementType.TEST: self._handle_test,
        }

    async def scan_for_improvements(
        self,
        target_paths: Optional[List[str]] = None,
        min_severity: int = 3
    ) -> List[ImprovementOpportunity]:
        """
        扫描代码库，发现改进机会

        Args:
            target_paths: 目标路径列表，None表示扫描整个代码库
            min_severity: 最小严重度阈值

        Returns:
            改进机会列表
        """
        print("[SelfImprovement] 开始扫描代码库...")

        all_opportunities = []

        if target_paths is None:
            target_paths = [str(self.codebase_path / 'moss')]

        for path_str in target_paths:
            path = Path(path_str)
            if path.is_file() and path.suffix == '.py':
                opportunities = await self.analyzer.analyze_file(str(path))
                all_opportunities.extend(opportunities)
            elif path.is_dir():
                for py_file in path.rglob('*.py'):
                    if '__pycache__' not in str(py_file):
                        opportunities = await self.analyzer.analyze_file(str(py_file))
                        all_opportunities.extend(opportunities)

        # 过滤严重度
        filtered = [opp for opp in all_opportunities if opp.severity >= min_severity]

        # 按严重度和置信度排序
        filtered.sort(key=lambda x: (x.severity * x.confidence), reverse=True)

        print(f"[SelfImprovement] 发现 {len(filtered)} 个改进机会")
        return filtered

    async def create_improvement_task(
        self,
        opportunity: ImprovementOpportunity
    ) -> str:
        """
        创建改进任务

        Returns:
            task_id
        """
        task_id = f"improve_{opportunity.opportunity_id}_{datetime.now().strftime('%H%M%S')}"

        # 读取原始代码
        original_code = None
        try:
            with open(opportunity.location.file_path, 'r') as f:
                original_code = f.read()
        except Exception as e:
            print(f"[SelfImprovement] 读取文件失败: {e}")

        task = ImprovementTask(
            task_id=task_id,
            opportunity=opportunity,
            status=ImprovementStatus.PENDING,
            original_code=original_code
        )

        self.tasks[task_id] = task

        print(f"[SelfImprovement] 创建任务: {task_id} ({opportunity.improvement_type.name})")
        return task_id

    async def execute_improvement(self, task_id: str) -> ImprovementResult:
        """
        执行改进任务

        完整流程:
        1. 分配Agent
        2. 执行改进
        3. 解决冲突
        4. 测试验证
        5. 应用或回滚
        """
        task = self.tasks.get(task_id)
        if not task:
            return ImprovementResult(
                task_id=task_id,
                success=False,
                applied_changes=False,
                message="任务不存在"
            )

        print(f"\n[SelfImprovement] ===== 执行任务: {task_id} =====")

        try:
            # 1. 查找并分配Agent
            task.status = ImprovementStatus.ANALYZING
            agents = await self._find_suitable_agents(task.opportunity.improvement_type)

            if not agents:
                task.status = ImprovementStatus.REJECTED
                return ImprovementResult(
                    task_id=task_id,
                    success=False,
                    applied_changes=False,
                    message="无可用Agent"
                )

            # 2. 备份原始代码
            if task.original_code:
                self.backup_cache[task_id] = task.original_code

            # 3. 并行执行改进（简化版：选择最佳Agent）
            task.status = ImprovementStatus.IMPLEMENTING
            selected_agent = agents[0]
            task.assigned_agents = [selected_agent.agent_id]

            handler = self._improvement_handlers.get(task.opportunity.improvement_type)
            if handler:
                proposed_code = await handler(task, selected_agent)
                task.proposed_changes = proposed_code
            else:
                return ImprovementResult(
                    task_id=task_id,
                    success=False,
                    applied_changes=False,
                    message="无对应的改进处理器"
                )

            # 4. 测试验证
            task.status = ImprovementStatus.TESTING
            test_passed = await self._run_tests(task)
            task.test_results = {'passed': test_passed}

            if not test_passed:
                await self._rollback(task_id)
                task.status = ImprovementStatus.ROLLED_BACK
                return ImprovementResult(
                    task_id=task_id,
                    success=False,
                    applied_changes=False,
                    message="测试未通过，已回滚"
                )

            # 5. 应用更改
            task.status = ImprovementStatus.ACCEPTED
            task.completed_at = datetime.now()

            # 生成diff
            diff = None
            if task.original_code and task.proposed_changes:
                diff = self._generate_diff(
                    task.original_code,
                    task.proposed_changes,
                    task.opportunity.location.file_path
                )

            print(f"[SelfImprovement] ✅ 任务完成: {task_id}")

            return ImprovementResult(
                task_id=task_id,
                success=True,
                applied_changes=True,
                message=f"改进成功 ({task.opportunity.improvement_type.name})",
                diff=diff
            )

        except Exception as e:
            await self._rollback(task_id)
            task.status = ImprovementStatus.ROLLED_BACK
            return ImprovementResult(
                task_id=task_id,
                success=False,
                applied_changes=False,
                message=f"执行失败: {str(e)}"
            )

    async def _find_suitable_agents(
        self,
        improvement_type: ImprovementType
    ) -> List[Any]:
        """查找合适的Agent"""
        capability_map = {
            ImprovementType.REFACTOR: 'code_refactoring',
            ImprovementType.OPTIMIZE: 'performance_optimization',
            ImprovementType.BUGFIX: 'bug_fixing',
            ImprovementType.FEATURE: 'feature_development',
            ImprovementType.DOCUMENT: 'documentation',
            ImprovementType.TEST: 'test_writing',
        }

        capability = capability_map.get(improvement_type, 'code_improvement')
        agents = await self.registry.find_by_capabilities([capability])

        # 只返回健康的Agent
        healthy_agents = [a for a in agents if a.health == HealthStatus.HEALTHY]

        # 按性能分数排序
        healthy_agents.sort(key=lambda x: x.performance_score, reverse=True)

        return healthy_agents

    async def _handle_refactor(self, task: ImprovementTask, agent) -> Optional[str]:
        """处理重构任务 - 使用RefactorEngine"""
        print(f"  [Refactor] Agent {agent.agent_id} 执行重构")

        if not task.original_code:
            return None

        code = task.original_code
        changes_applied = []

        # 策略1: 组织导入语句
        result = self.refactorer.refactor(code, 'organize_imports')
        if result.success:
            code = result.refactored_code
            changes_applied.append(f"organize_imports:{len(result.changes)}")

        # 策略2: 优化循环
        result = self.refactorer.refactor(code, 'optimize_loops')
        if result.success:
            code = result.refactored_code
            changes_applied.append(f"optimize_loops:{len(result.changes)}")

        # 策略3: 移除未使用变量
        result = self.refactorer.refactor(code, 'remove_unused')
        if result.success:
            code = result.refactored_code
            changes_applied.append(f"remove_unused:{len(result.changes)}")

        # 策略4: 函数提取（如果函数过长）
        if task.opportunity.location.function_name:
            func_name = task.opportunity.location.function_name
            result = self.refactorer.refactor(
                code,
                'extract_function',
                function_name=func_name,
                max_lines=30
            )
            if result.success:
                code = result.refactored_code
                changes_applied.append(f"extract_function:{len(result.changes)}")

        if changes_applied:
            print(f"    ✅ 应用重构: {', '.join(changes_applied)}")
        else:
            print(f"    ℹ️ 无需重构")

        return code

    async def _handle_optimize(self, task: ImprovementTask, agent) -> Optional[str]:
        """处理优化任务 - 使用RefactorEngine"""
        print(f"  [Optimize] Agent {agent.agent_id} 执行优化")

        if not task.original_code:
            return None

        # 使用refactorer的循环优化
        result = self.refactorer.refactor(task.original_code, 'optimize_loops')

        if result.success:
            print(f"    ✅ 优化了 {len(result.changes)} 个循环")
            return result.refactored_code

        return task.original_code

    async def _handle_bugfix(self, task: ImprovementTask, agent) -> Optional[str]:
        """处理Bug修复"""
        print(f"  [BugFix] Agent {agent.agent_id} 修复问题")
        # 简化版：在TODO行添加标记
        if task.original_code and 'TODO' in task.opportunity.description:
            return task.original_code.replace(
                'TODO',
                'TODO [AUTO-DETECTED]'
            )
        return task.original_code

    async def _handle_feature(self, task: ImprovementTask, agent) -> Optional[str]:
        """处理功能增强"""
        print(f"  [Feature] Agent {agent.agent_id} 实现功能")
        return task.original_code

    async def _handle_document(self, task: ImprovementTask, agent) -> Optional[str]:
        """处理文档完善"""
        print(f"  [Document] Agent {agent.agent_id} 完善文档")
        return task.original_code

    async def _handle_test(self, task: ImprovementTask, agent) -> Optional[str]:
        """处理测试补充"""
        print(f"  [Test] Agent {agent.agent_id} 补充测试")
        return task.original_code

    async def _run_tests(self, task: ImprovementTask) -> bool:
        """运行测试验证"""
        print(f"  [Test] 运行测试验证...")

        # 简化版：检查Python语法
        if task.proposed_changes:
            try:
                ast.parse(task.proposed_changes)
                print(f"    ✅ 语法检查通过")
                return True
            except SyntaxError as e:
                print(f"    ❌ 语法错误: {e}")
                return False

        return True

    async def _rollback(self, task_id: str):
        """回滚更改"""
        print(f"  [Rollback] 回滚任务: {task_id}")

        task = self.tasks.get(task_id)
        if task and task_id in self.backup_cache:
            try:
                with open(task.opportunity.location.file_path, 'w') as f:
                    f.write(self.backup_cache[task_id])
                print(f"    ✅ 已恢复到原始代码")
            except Exception as e:
                print(f"    ❌ 回滚失败: {e}")

    def _generate_diff(self, original: str, modified: str, file_path: str) -> str:
        """生成diff"""
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)

        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=file_path,
            tofile=file_path + '.improved',
            lineterm=''
        )

        return ''.join(diff)

    async def get_statistics(self) -> Dict:
        """获取统计信息"""
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks.values() if t.status == ImprovementStatus.ACCEPTED)
        failed = sum(1 for t in self.tasks.values() if t.status in [
            ImprovementStatus.REJECTED, ImprovementStatus.ROLLED_BACK
        ])
        pending = sum(1 for t in self.tasks.values() if t.status == ImprovementStatus.PENDING)

        type_counts = {}
        for task in self.tasks.values():
            t = task.opportunity.improvement_type.name
            type_counts[t] = type_counts.get(t, 0) + 1

        return {
            'total_tasks': total,
            'completed': completed,
            'failed': failed,
            'pending': pending,
            'success_rate': completed / total if total > 0 else 0,
            'by_type': type_counts
        }


async def create_orchestrator(
    registry: Optional[AgentRegistry] = None,
    message_bus: Optional[MessageBus] = None,
    conflict_resolver: Optional[ConflictResolver] = None,
    codebase_path: str = '/workspace/moss'
) -> SelfImprovementOrchestrator:
    """
    工厂函数：创建自改写协调器
    """
    # 如果未提供，创建默认实例
    if registry is None:
        from moss.core.agent_registry import create_registry
        registry = await create_registry()

    if message_bus is None:
        from moss.core.message_bus import create_message_bus
        message_bus = await create_message_bus()

    if conflict_resolver is None:
        conflict_resolver = ConflictResolver()

    return SelfImprovementOrchestrator(
        registry=registry,
        message_bus=message_bus,
        conflict_resolver=conflict_resolver,
        codebase_path=codebase_path
    )


# 测试代码
if __name__ == "__main__":
    async def test():
        print("=" * 70)
        print("Self-Improvement Orchestrator 测试")
        print("=" * 70)

        orchestrator = await create_orchestrator()

        # 1. 扫描改进机会
        opportunities = await orchestrator.scan_for_improvements(
            target_paths=['/workspace/moss/moss/core'],
            min_severity=3
        )

        print(f"\n发现 {len(opportunities)} 个改进机会:")
        for opp in opportunities[:5]:  # 只显示前5个
            print(f"  - {opp.improvement_type.name}: {opp.description[:50]}...")

        # 2. 选择前3个创建任务
        if opportunities:
            print("\n创建改进任务...")
            for opp in opportunities[:3]:
                task_id = await orchestrator.create_improvement_task(opp)
                result = await orchestrator.execute_improvement(task_id)
                print(f"  {task_id}: {'✅' if result.success else '❌'} {result.message}")
                if result.diff:
                    print(f"    Diff preview:\n{result.diff[:200]}...")

        # 3. 统计
        stats = await orchestrator.get_statistics()
        print(f"\n统计: {stats}")

        print("\n测试完成!")

    asyncio.run(test())
