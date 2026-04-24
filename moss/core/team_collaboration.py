#!/usr/bin/env python3
"""
MOSS v9.3 - Team Collaboration System
团队协作系统

企业级功能:
1. 共享配置管理
2. 团队级重构策略
3. 代码质量仪表盘数据
4. 重构操作审计日志
5. 团队知识库

Author: MOSS v9.3
Date: 2026-04-24
"""

import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import hashlib


# ──────────────────────────────────────────────────────────────
# Data Structures
# ──────────────────────────────────────────────────────────────

@dataclass
class TeamConfig:
    """团队共享配置"""
    team_id: str
    team_name: str
    created_at: float
    updated_at: float

    # 分析配置
    analysis_threshold: int = 50
    complexity_threshold: int = 10
    enable_incremental: bool = True
    enable_parallel: bool = True

    # 重构策略
    auto_refactor_enabled: bool = False
    require_approval: bool = True
    preview_changes: bool = True

    # 质量门禁
    quality_gate_enabled: bool = True
    max_issues_per_pr: int = 10
    block_on_critical: bool = True

    # 通知设置
    notify_on_failure: bool = True
    notify_channel: str = "email"  # email, slack, webhook

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'TeamConfig':
        return cls(**data)


@dataclass
class RefactoringAuditLog:
    """重构审计日志"""
    log_id: str
    timestamp: float
    user_id: str
    user_name: str
    action_type: str
    target_file: str
    target_symbol: str
    before_hash: str
    after_hash: str
    success: bool
    message: str = ""
    duration_ms: int = 0


@dataclass
class QualityMetrics:
    """代码质量指标"""
    timestamp: float
    total_files: int
    total_lines: int
    total_issues: int
    issues_by_severity: Dict[str, int]
    issues_by_type: Dict[str, int]
    complexity_distribution: Dict[str, int]
    top_issues: List[Dict]
    trend: str = "stable"  # improving, stable, degrading


@dataclass
class TeamKnowledge:
    """团队知识库条目"""
    entry_id: str
    entry_type: str  # 'best_practice', 'anti_pattern', 'refactoring_guide'
    title: str
    content: str
    author: str
    created_at: float
    updated_at: float
    tags: List[str] = field(default_factory=list)
    related_files: List[str] = field(default_factory=list)
    vote_count: int = 0


# ──────────────────────────────────────────────────────────────
# Team Manager
# ──────────────────────────────────────────────────────────────

class TeamManager:
    """团队管理器"""

    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.team_dir = self.project_path / ".moss" / "team"
        self.team_dir.mkdir(parents=True, exist_ok=True)

        self.config_file = self.team_dir / "config.json"
        self.audit_log_file = self.team_dir / "audit.log"
        self.knowledge_file = self.team_dir / "knowledge.json"

        self.config: Optional[TeamConfig] = None
        self._load_config()

    def _load_config(self):
        """加载团队配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.config = TeamConfig.from_dict(data)
            except Exception:
                pass

        if self.config is None:
            self.config = TeamConfig(
                team_id=self._generate_id(),
                team_name="Default Team",
                created_at=time.time(),
                updated_at=time.time(),
            )
            self._save_config()

    def _save_config(self):
        """保存团队配置"""
        self.config.updated_at = time.time()
        with open(self.config_file, 'w') as f:
            json.dump(self.config.to_dict(), f, indent=2)

    def _generate_id(self) -> str:
        """生成唯一 ID"""
        return hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]

    def update_config(self, **kwargs):
        """更新团队配置"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self._save_config()

    def get_config(self) -> TeamConfig:
        """获取团队配置"""
        return self.config

    # ──────────────────────────────────────────────────────────
    # Audit Logging
    # ──────────────────────────────────────────────────────────

    def log_refactoring(self, log: RefactoringAuditLog):
        """记录重构操作"""
        log_entry = {
            'log_id': log.log_id,
            'timestamp': log.timestamp,
            'user_id': log.user_id,
            'user_name': log.user_name,
            'action_type': log.action_type,
            'target_file': log.target_file,
            'target_symbol': log.target_symbol,
            'before_hash': log.before_hash,
            'after_hash': log.after_hash,
            'success': log.success,
            'message': log.message,
            'duration_ms': log.duration_ms,
        }

        with open(self.audit_log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

    def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        action_type: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: int = 100
    ) -> List[RefactoringAuditLog]:
        """查询审计日志"""
        logs = []

        if not self.audit_log_file.exists():
            return logs

        with open(self.audit_log_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())

                    # 过滤条件
                    if user_id and data.get('user_id') != user_id:
                        continue
                    if action_type and data.get('action_type') != action_type:
                        continue
                    if start_time and data.get('timestamp', 0) < start_time:
                        continue
                    if end_time and data.get('timestamp', 0) > end_time:
                        continue

                    logs.append(RefactoringAuditLog(**data))

                    if len(logs) >= limit:
                        break

                except json.JSONDecodeError:
                    continue

        return logs

    def get_refactoring_stats(self, days: int = 30) -> Dict:
        """获取重构统计"""
        cutoff = time.time() - days * 86400
        logs = self.get_audit_logs(start_time=cutoff, limit=10000)

        total = len(logs)
        successful = sum(1 for log in logs if log.success)
        failed = total - successful

        action_counts = {}
        user_counts = {}
        for log in logs:
            action_counts[log.action_type] = action_counts.get(log.action_type, 0) + 1
            user_counts[log.user_name] = user_counts.get(log.user_name, 0) + 1

        return {
            'total_refactorings': total,
            'successful': successful,
            'failed': failed,
            'success_rate': successful / total if total > 0 else 0,
            'action_breakdown': action_counts,
            'top_contributors': sorted(user_counts.items(), key=lambda x: -x[1])[:5],
        }

    # ──────────────────────────────────────────────────────────
    # Knowledge Base
    # ──────────────────────────────────────────────────────────

    def add_knowledge(self, entry: TeamKnowledge) -> str:
        """添加知识库条目"""
        entry.entry_id = self._generate_id()
        entry.created_at = time.time()
        entry.updated_at = time.time()

        entries = self._load_knowledge()
        entries.append(entry.to_dict() if hasattr(entry, 'to_dict') else asdict(entry))

        with open(self.knowledge_file, 'w') as f:
            json.dump(entries, f, indent=2)

        return entry.entry_id

    def _load_knowledge(self) -> List[Dict]:
        """加载知识库"""
        if self.knowledge_file.exists():
            try:
                with open(self.knowledge_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def get_knowledge(
        self,
        entry_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None
    ) -> List[TeamKnowledge]:
        """查询知识库"""
        entries = self._load_knowledge()
        results = []

        for data in entries:
            # 类型过滤
            if entry_type and data.get('entry_type') != entry_type:
                continue

            # 标签过滤
            if tags:
                entry_tags = set(data.get('tags', []))
                if not entry_tags.intersection(set(tags)):
                    continue

            # 搜索过滤
            if search:
                search_lower = search.lower()
                if (search_lower not in data.get('title', '').lower() and
                    search_lower not in data.get('content', '').lower()):
                    continue

            results.append(TeamKnowledge(**data))

        return sorted(results, key=lambda x: (-x.vote_count, -x.created_at))

    def vote_knowledge(self, entry_id: str, up: bool = True):
        """为知识库条目投票"""
        entries = self._load_knowledge()

        for entry in entries:
            if entry.get('entry_id') == entry_id:
                entry['vote_count'] = entry.get('vote_count', 0) + (1 if up else -1)
                entry['updated_at'] = time.time()
                break

        with open(self.knowledge_file, 'w') as f:
            json.dump(entries, f, indent=2)


# ──────────────────────────────────────────────────────────────
# Quality Dashboard
# ──────────────────────────────────────────────────────────────

class QualityDashboard:
    """代码质量仪表盘"""

    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.metrics_dir = self.project_path / ".moss" / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

    def record_metrics(self, metrics: QualityMetrics):
        """记录质量指标"""
        date_str = datetime.fromtimestamp(metrics.timestamp).strftime('%Y-%m-%d')
        metrics_file = self.metrics_dir / f"{date_str}.json"

        # 加载现有数据
        daily_metrics = []
        if metrics_file.exists():
            try:
                with open(metrics_file, 'r') as f:
                    daily_metrics = json.load(f)
            except Exception:
                pass

        # 添加新指标
        daily_metrics.append({
            'timestamp': metrics.timestamp,
            'total_files': metrics.total_files,
            'total_lines': metrics.total_lines,
            'total_issues': metrics.total_issues,
            'issues_by_severity': metrics.issues_by_severity,
            'issues_by_type': metrics.issues_by_type,
            'complexity_distribution': metrics.complexity_distribution,
        })

        with open(metrics_file, 'w') as f:
            json.dump(daily_metrics, f, indent=2)

    def get_trend(self, days: int = 7) -> Dict:
        """获取质量趋势"""
        trend_data = []

        for i in range(days):
            date = datetime.now() - __import__('datetime').timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            metrics_file = self.metrics_dir / f"{date_str}.json"

            if metrics_file.exists():
                try:
                    with open(metrics_file, 'r') as f:
                        data = json.load(f)
                        if data:
                            latest = data[-1]
                            trend_data.append({
                                'date': date_str,
                                'total_issues': latest.get('total_issues', 0),
                                'total_files': latest.get('total_files', 0),
                            })
                except Exception:
                    pass

        trend_data.reverse()

        # 计算趋势
        if len(trend_data) >= 2:
            first = trend_data[0]['total_issues']
            last = trend_data[-1]['total_issues']
            change = last - first

            if change < -5:
                trend = "improving"
            elif change > 5:
                trend = "degrading"
            else:
                trend = "stable"
        else:
            trend = "stable"

        return {
            'trend': trend,
            'data': trend_data,
            'change': change if len(trend_data) >= 2 else 0,
        }

    def generate_report(self) -> str:
        """生成仪表盘报告"""
        trend = self.get_trend(7)

        lines = []
        lines.append("=" * 60)
        lines.append("MOSS v9.3 - Code Quality Dashboard")
        lines.append("=" * 60)
        lines.append(f"\nTrend: {trend['trend'].upper()}")
        lines.append(f"Change (7d): {trend['change']} issues")

        if trend['data']:
            latest = trend['data'][-1]
            lines.append(f"\nCurrent Status:")
            lines.append(f"  Files: {latest['total_files']}")
            lines.append(f"  Issues: {latest['total_issues']}")

        lines.append("\n" + "=" * 60)

        return '\n'.join(lines)


# ──────────────────────────────────────────────────────────────
# Demo
# ──────────────────────────────────────────────────────────────

def demo():
    """演示团队协作功能"""
    print("\n" + "="*60)
    print("MOSS v9.3 - Team Collaboration Demo")
    print("="*60)

    # 创建团队管理器
    manager = TeamManager("/tmp/moss_team_demo")

    # 1. 配置管理
    print("\n[1] 团队配置管理")
    config = manager.get_config()
    print(f"  团队: {config.team_name} (ID: {config.team_id})")

    manager.update_config(
        team_name="Awesome Team",
        analysis_threshold=40,
        quality_gate_enabled=True
    )
    print("  ✓ 配置已更新")

    # 2. 审计日志
    print("\n[2] 重构审计日志")
    log = RefactoringAuditLog(
        log_id="log_001",
        timestamp=time.time(),
        user_id="user_123",
        user_name="Alice",
        action_type="extract_function",
        target_file="main.py",
        target_symbol="long_function",
        before_hash="abc123",
        after_hash="def456",
        success=True,
        message="Extracted helper function",
        duration_ms=150,
    )
    manager.log_refactoring(log)
    print("  ✓ 重构操作已记录")

    stats = manager.get_refactoring_stats(days=7)
    print(f"  统计: {stats['total_refactorings']} 次重构, 成功率 {stats['success_rate']:.0%}")

    # 3. 知识库
    print("\n[3] 团队知识库")
    entry = TeamKnowledge(
        entry_id="",
        entry_type="best_practice",
        title="函数长度限制",
        content="建议函数长度不超过 50 行，超过时应考虑拆分。",
        author="Bob",
        created_at=0,
        updated_at=0,
        tags=["refactoring", "clean-code"],
        vote_count=5,
    )
    entry_id = manager.add_knowledge(entry)
    print(f"  ✓ 知识库条目已添加 (ID: {entry_id})")

    knowledge = manager.get_knowledge(entry_type="best_practice")
    print(f"  知识库中有 {len(knowledge)} 条最佳实践")

    # 4. 质量仪表盘
    print("\n[4] 质量仪表盘")
    dashboard = QualityDashboard("/tmp/moss_team_demo")

    metrics = QualityMetrics(
        timestamp=time.time(),
        total_files=100,
        total_lines=5000,
        total_issues=25,
        issues_by_severity={'error': 2, 'warning': 10, 'info': 13},
        issues_by_type={'long_function': 5, 'unused_import': 8, 'complexity': 12},
        complexity_distribution={'low': 50, 'medium': 30, 'high': 5},
        top_issues=[],
    )
    dashboard.record_metrics(metrics)
    print("  ✓ 质量指标已记录")

    print(dashboard.generate_report())

    print("\n" + "="*60)
    print("Demo 完成!")
    print("="*60)


if __name__ == "__main__":
    demo()
