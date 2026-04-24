"""
Tests for File Watcher
文件监控系统测试
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from moss.core.file_watcher import (
    WatchConfig,
    WatchEventType,
    FileChangeEvent,
    ChangeBatch,
    MossFileEventHandler,
    FileWatcher,
    AnalysisOrchestrator,
)

# 标记是否可用 watchdog
try:
    from watchdog.events import FileCreatedEvent, FileModifiedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False


class TestWatchConfig:
    """测试监控配置"""

    def test_default_config(self):
        config = WatchConfig()
        assert config.paths == [Path(".")]
        assert "*.py" in config.patterns
        assert "*.pyc" in config.ignore_patterns
        assert config.recursive is True
        assert config.debounce_seconds == 1.0

    def test_custom_config(self):
        config = WatchConfig(
            paths=[Path("/tmp")],
            patterns=["*.js"],
            debounce_seconds=2.0,
            auto_analyze=False,
        )
        assert config.paths == [Path("/tmp")]
        assert config.patterns == ["*.js"]
        assert config.debounce_seconds == 2.0
        assert config.auto_analyze is False

    def test_validate_invalid_path(self):
        config = WatchConfig(paths=[Path("/nonexistent_path_12345")])
        errors = config.validate()
        assert len(errors) > 0

    def test_validate_negative_debounce(self):
        config = WatchConfig(debounce_seconds=-1.0)
        errors = config.validate()
        assert len(errors) > 0


class TestFileChangeEvent:
    """测试文件变更事件"""

    def test_creation(self):
        event = FileChangeEvent(
            event_type=WatchEventType.CREATED,
            src_path=Path("/tmp/test.py"),
        )
        assert event.event_type == WatchEventType.CREATED
        assert event.src_path == Path("/tmp/test.py")
        assert event.dest_path is None

    def test_move_event(self):
        event = FileChangeEvent(
            event_type=WatchEventType.MOVED,
            src_path=Path("/tmp/old.py"),
            dest_path=Path("/tmp/new.py"),
        )
        assert str(event) == "moved: /tmp/old.py -> /tmp/new.py"

    def test_other_event(self):
        event = FileChangeEvent(
            event_type=WatchEventType.MODIFIED,
            src_path=Path("/tmp/test.py"),
        )
        assert str(event) == "modified: /tmp/test.py"


class TestChangeBatch:
    """测试变更批处理"""

    @pytest.mark.asyncio
    async def test_add_single_change(self):
        batch = ChangeBatch(debounce_seconds=0.1)
        callback_called = asyncio.Event()
        received_changes = []

        def callback(changes):
            received_changes.extend(changes)
            callback_called.set()

        event = FileChangeEvent(
            event_type=WatchEventType.CREATED,
            src_path=Path("/tmp/test.py"),
        )

        await batch.add_change(event, callback)

        # 等待防抖触发
        await asyncio.wait_for(callback_called.wait(), timeout=0.5)

        assert len(received_changes) == 1
        assert received_changes[0].src_path == Path("/tmp/test.py")

    @pytest.mark.asyncio
    async def test_merge_same_file_changes(self):
        batch = ChangeBatch(debounce_seconds=0.1)
        callback_called = asyncio.Event()
        received_changes = []

        def callback(changes):
            received_changes.extend(changes)
            callback_called.set()

        # 同一文件的多次变更应该合并
        event1 = FileChangeEvent(
            event_type=WatchEventType.CREATED,
            src_path=Path("/tmp/test.py"),
        )
        event2 = FileChangeEvent(
            event_type=WatchEventType.MODIFIED,
            src_path=Path("/tmp/test.py"),
        )

        await batch.add_change(event1, callback)
        await asyncio.sleep(0.02)  # 短暂延迟
        await batch.add_change(event2, callback)

        await asyncio.wait_for(callback_called.wait(), timeout=0.5)

        # 应该只有一个变更 (最后一次)
        assert len(received_changes) == 1
        assert received_changes[0].event_type == WatchEventType.MODIFIED

    @pytest.mark.asyncio
    async def test_multiple_files(self):
        batch = ChangeBatch(debounce_seconds=0.1)
        callback_called = asyncio.Event()
        received_changes = []

        def callback(changes):
            received_changes.extend(changes)
            callback_called.set()

        # 不同文件的变更
        events = [
            FileChangeEvent(WatchEventType.CREATED, Path("/tmp/a.py")),
            FileChangeEvent(WatchEventType.CREATED, Path("/tmp/b.py")),
            FileChangeEvent(WatchEventType.MODIFIED, Path("/tmp/c.py")),
        ]

        for event in events:
            await batch.add_change(event, callback)

        await asyncio.wait_for(callback_called.wait(), timeout=0.5)

        assert len(received_changes) == 3

    def test_flush(self):
        batch = ChangeBatch()
        event = FileChangeEvent(
            event_type=WatchEventType.CREATED,
            src_path=Path("/tmp/test.py"),
        )

        # 手动添加 (不通过异步方法)
        batch._pending_changes[event.src_path] = event

        changes = batch.flush()
        assert len(changes) == 1
        assert len(batch._pending_changes) == 0


@pytest.mark.skipif(not WATCHDOG_AVAILABLE, reason="watchdog not installed")
class TestMossFileEventHandler:
    """测试文件事件处理器"""

    def test_should_process_py_file(self):
        config = WatchConfig(patterns=["*.py"])
        handler = MossFileEventHandler(config, Mock())

        assert handler._should_process(Path("/tmp/test.py")) is True
        assert handler._should_process(Path("/tmp/test.js")) is False

    def test_should_ignore_pycache(self):
        config = WatchConfig(patterns=["*.py"])
        handler = MossFileEventHandler(config, Mock())

        # 测试 __pycache__ 目录被忽略
        assert handler._should_process(Path("/tmp/__pycache__/")) is False
        # 测试 .git 目录被忽略
        assert handler._should_process(Path("/tmp/.git/config")) is False

    def test_on_created(self):
        config = WatchConfig(patterns=["*.py"])
        callback = Mock()
        handler = MossFileEventHandler(config, callback)

        event = FileCreatedEvent(src_path="/tmp/test.py")
        event.is_directory = False
        handler.on_created(event)

        callback.assert_called_once()
        call_arg = callback.call_args[0][0]
        assert call_arg.event_type == WatchEventType.CREATED
        assert call_arg.src_path == Path("/tmp/test.py")

    def test_on_modified(self):
        config = WatchConfig(patterns=["*.py"])
        callback = Mock()
        handler = MossFileEventHandler(config, callback)

        event = FileModifiedEvent(src_path="/tmp/test.py")
        event.is_directory = False
        handler.on_modified(event)

        callback.assert_called_once()
        call_arg = callback.call_args[0][0]
        assert call_arg.event_type == WatchEventType.MODIFIED


@pytest.mark.skipif(not WATCHDOG_AVAILABLE, reason="watchdog not installed")
class TestFileWatcher:
    """测试文件监控器"""

    def test_creation(self):
        config = WatchConfig()
        watcher = FileWatcher(config)
        assert watcher.config == config
        assert watcher.is_running() is False

    def test_on_changes(self):
        config = WatchConfig()
        watcher = FileWatcher(config)
        callback = Mock()

        result = watcher.on_changes(callback)
        assert result == watcher  # 链式调用
        assert watcher._change_callback == callback

    def test_on_analyze(self):
        config = WatchConfig()
        watcher = FileWatcher(config)
        callback = Mock()

        result = watcher.on_analyze(callback)
        assert result == watcher
        assert watcher._analyze_callback == callback

    def test_start_stop(self):
        import tempfile
        import time

        with tempfile.TemporaryDirectory() as tmpdir:
            config = WatchConfig(paths=[Path(tmpdir)])
            watcher = FileWatcher(config)

            watcher.start()
            assert watcher.is_running() is True

            time.sleep(0.1)  # 给observer启动时间

            watcher.stop()
            assert watcher.is_running() is False


class TestAnalysisOrchestrator:
    """测试分析编排器"""

    @pytest.mark.asyncio
    async def test_handle_empty_changes(self):
        orchestrator = AnalysisOrchestrator(Path("/tmp"))
        result = await orchestrator.handle_changes([])
        assert result["status"] == "no_files_to_analyze"

    @pytest.mark.asyncio
    async def test_handle_directory_changes(self):
        orchestrator = AnalysisOrchestrator(Path("/tmp"))
        changes = [
            FileChangeEvent(
                event_type=WatchEventType.CREATED,
                src_path=Path("/tmp/newdir"),
                is_directory=True,
            ),
        ]
        result = await orchestrator.handle_changes(changes)
        assert result["status"] == "no_files_to_analyze"

    @pytest.mark.asyncio
    async def test_handle_file_changes(self, tmp_path):
        orchestrator = AnalysisOrchestrator(tmp_path)
        await orchestrator.initialize()

        # 创建测试文件
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")

        changes = [
            FileChangeEvent(
                event_type=WatchEventType.CREATED,
                src_path=test_file,
            ),
        ]

        result = await orchestrator.handle_changes(changes)
        assert result["status"] == "analyzed"
        assert result["files_analyzed"] == 1
        assert str(test_file) in result["results"]

    @pytest.mark.asyncio
    async def test_analyze_single_file_not_found(self, tmp_path):
        orchestrator = AnalysisOrchestrator(tmp_path)
        result = await orchestrator._analyze_single_file(tmp_path / "nonexistent.py")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_analyze_single_file_with_issues(self, tmp_path):
        orchestrator = AnalysisOrchestrator(tmp_path)

        # 创建包含长行的文件
        test_file = tmp_path / "test.py"
        test_file.write_text("x = '" + "a" * 150 + "'\n")

        result = await orchestrator._analyze_single_file(test_file)
        assert "issues" in result
        assert result["issue_count"] > 0

    @pytest.mark.asyncio
    async def test_analyze_single_file_ok(self, tmp_path):
        orchestrator = AnalysisOrchestrator(tmp_path)

        # 创建正常文件
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\ny = 2")  # 无末尾换行符

        result = await orchestrator._analyze_single_file(test_file)
        assert result["issue_count"] == 0
        assert result["lines"] == 2


@pytest.mark.skipif(not WATCHDOG_AVAILABLE, reason="watchdog not installed")
class TestWatchdogNotInstalled:
    """测试 watchdog 未安装时的行为"""

    def test_import_error(self):
        with patch("moss.core.file_watcher.WATCHDOG_AVAILABLE", False):
            with pytest.raises(RuntimeError, match="watchdog is required"):
                FileWatcher()


class TestWatchEventType:
    """测试事件类型枚举"""

    def test_event_types(self):
        assert WatchEventType.CREATED.value == "created"
        assert WatchEventType.MODIFIED.value == "modified"
        assert WatchEventType.DELETED.value == "deleted"
        assert WatchEventType.MOVED.value == "moved"
