#!/usr/bin/env python3
"""
MOSS v9.4 - Task Agent Plugin Tests
任务感知 Agent 插件测试
"""

import tempfile
from pathlib import Path

import pytest

from moss.plugins.task_agent_plugin import (
    TaskAgentPlugin,
    TaskResult,
    TASK_SCENARIOS,
    run_task_cli,
)
from moss.core.plugin_system import PluginContext


class TestTaskAgentPlugin:
    """Test Task Agent Plugin"""

    def test_plugin_metadata(self):
        """测试插件元数据"""
        plugin = TaskAgentPlugin()
        assert plugin.name == "moss-task-agent"
        assert plugin.version == "1.0.0"
        assert "Task-aware" in plugin.description

    def test_list_tasks(self):
        """测试列出任务"""
        plugin = TaskAgentPlugin()
        tasks = plugin.list_tasks()
        assert len(tasks) == 5

        task_types = {t['type'] for t in tasks}
        assert 'file_organization' in task_types
        assert 'log_analysis' in task_types
        assert 'system_monitor' in task_types
        assert 'code_review' in task_types
        assert 'backup_cleanup' in task_types

    def test_plugin_lifecycle(self):
        """测试插件生命周期"""
        plugin = TaskAgentPlugin()
        assert not plugin.is_loaded

        context = PluginContext(project_path=Path('.'))
        plugin.on_load(context)
        assert plugin.is_loaded

        plugin.on_unload()
        assert not plugin.is_loaded

    def test_execute_system_monitor(self):
        """测试执行系统监控任务"""
        plugin = TaskAgentPlugin()
        context = PluginContext(project_path=Path('.'))
        plugin.on_load(context)

        result = plugin.execute_task('system_monitor', max_cycles=5)

        assert isinstance(result, TaskResult)
        assert result.task_type == 'system_monitor'
        assert result.success is True
        assert result.cycles <= 5
        assert result.duration >= 0
        assert len(result.actions_executed) > 0

    def test_execute_code_review(self):
        """测试执行代码审查任务"""
        plugin = TaskAgentPlugin()
        context = PluginContext(project_path=Path('.'))
        plugin.on_load(context)

        result = plugin.execute_task('code_review', max_cycles=5)

        assert isinstance(result, TaskResult)
        assert result.task_type == 'code_review'
        assert result.success is True

    def test_execute_unknown_task(self):
        """测试执行未知任务"""
        plugin = TaskAgentPlugin()
        context = PluginContext(project_path=Path('.'))
        plugin.on_load(context)

        result = plugin.execute_task('unknown_task')

        assert result.success is False
        assert 'Unknown task type' in result.error

    def test_statistics(self):
        """测试统计功能"""
        plugin = TaskAgentPlugin()
        context = PluginContext(project_path=Path('.'))
        plugin.on_load(context)

        # 初始统计为空
        stats = plugin.get_statistics()
        assert stats['total_tasks'] == 0
        assert stats['success_rate'] == 0.0

        # 执行任务
        plugin.execute_task('system_monitor', max_cycles=3)

        # 检查统计
        stats = plugin.get_statistics()
        assert stats['total_tasks'] == 1
        assert stats['success_rate'] == 1.0
        assert stats['avg_cycles'] > 0

    def test_clear_history(self):
        """测试清空历史"""
        plugin = TaskAgentPlugin()
        context = PluginContext(project_path=Path('.'))
        plugin.on_load(context)

        plugin.execute_task('system_monitor', max_cycles=3)
        assert plugin.get_statistics()['total_tasks'] == 1

        plugin.clear_history()
        assert plugin.get_statistics()['total_tasks'] == 0

    def test_register_custom_task(self):
        """测试注册自定义任务"""
        plugin = TaskAgentPlugin()

        custom_task = {
            'name': 'Custom Task',
            'description': 'A custom task for testing',
            'actions': [
                {'cmd': 'echo "custom"', 'desc': 'custom action'},
            ],
            'success_check': lambda path: True,
        }

        plugin.register_task('custom_test', custom_task)

        tasks = plugin.list_tasks()
        task_types = {t['type'] for t in tasks}
        assert 'custom_test' in task_types

    def test_task_scenarios_structure(self):
        """测试任务场景结构"""
        for task_type, config in TASK_SCENARIOS.items():
            assert 'name' in config
            assert 'description' in config
            assert 'actions' in config
            assert isinstance(config['actions'], list)
            assert len(config['actions']) > 0

            for action in config['actions']:
                assert 'cmd' in action
                assert 'desc' in action


class TestTaskResult:
    """Test TaskResult dataclass"""

    def test_task_result_creation(self):
        """测试创建 TaskResult"""
        result = TaskResult(
            task_type='test',
            success=True,
            cycles=10,
            duration=5.5,
            actions_executed=[{'cycle': 0, 'action': 'test'}],
        )

        assert result.task_type == 'test'
        assert result.success is True
        assert result.cycles == 10
        assert result.duration == 5.5

    def test_task_result_to_dict(self):
        """测试转换为字典"""
        result = TaskResult(
            task_type='test',
            success=True,
            cycles=10,
            duration=5.5,
            actions_executed=[{'cycle': 0, 'action': 'test'}],
            output='test output',
        )

        d = result.to_dict()
        assert d['task_type'] == 'test'
        assert d['success'] is True
        assert d['cycles'] == 10
        assert 'actions_executed' in d


class TestRunTaskCLI:
    """Test CLI helper"""

    def test_cli_list_tasks(self, capsys):
        """测试 CLI 列出任务"""
        # This would need to be tested via subprocess or mocked
        pass

    def test_cli_success_exit_code(self):
        """测试成功退出码"""
        exit_code = run_task_cli('system_monitor', '.', 5)
        assert exit_code == 0

    def test_cli_failure_exit_code(self):
        """测试失败退出码"""
        exit_code = run_task_cli('unknown_task', '.', 5)
        assert exit_code == 1
