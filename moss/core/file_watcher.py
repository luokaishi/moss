"""
MOSS File Watcher
文件监控实时重分析系统

功能：
- 监控文件系统变化 (创建、修改、删除、移动)
- 智能防抖处理
- 增量分析集成
- 实时反馈 (控制台、IDE、通知)
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union

logger = logging.getLogger(__name__)

# 可选导入 watchdog
try:
    from watchdog.observers import Observer
    from watchdog.events import (
        FileSystemEventHandler,
        FileCreatedEvent,
        FileModifiedEvent,
        FileDeletedEvent,
        FileMovedEvent,
        DirCreatedEvent,
        DirModifiedEvent,
        DirDeletedEvent,
        DirMovedEvent,
    )
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    logger.warning("watchdog not installed, file watching disabled")
    # 创建占位类避免导入错误
    class FileSystemEventHandler:
        pass
    class FileCreatedEvent:
        pass
    class FileModifiedEvent:
        pass
    class FileDeletedEvent:
        pass
    class FileMovedEvent:
        pass


class WatchEventType(Enum):
    """监控事件类型"""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"


@dataclass
class WatchConfig:
    """监控配置"""
    paths: List[Path] = field(default_factory=lambda: [Path(".")])
    patterns: List[str] = field(default_factory=lambda: ["*.py"])
    ignore_patterns: List[str] = field(default_factory=lambda: [
        "*.pyc", "__pycache__/*", ".git/*", ".moss/*",
        "*.tmp", "*.temp", ".DS_Store", "*.swp"
    ])
    recursive: bool = True
    debounce_seconds: float = 1.0  # 防抖时间
    auto_analyze: bool = True  # 自动分析
    auto_refactor: bool = False  # 自动重构 (谨慎开启)

    def validate(self) -> List[str]:
        """验证配置"""
        errors = []
        for path in self.paths:
            if not path.exists():
                errors.append(f"Path does not exist: {path}")
        if self.debounce_seconds < 0:
            errors.append("debounce_seconds must be >= 0")
        return errors


@dataclass
class FileChangeEvent:
    """文件变更事件"""
    event_type: WatchEventType
    src_path: Path
    dest_path: Optional[Path] = None  # 用于移动事件
    timestamp: float = field(default_factory=time.time)
    is_directory: bool = False

    def __str__(self) -> str:
        if self.event_type == WatchEventType.MOVED:
            return f"{self.event_type.value}: {self.src_path} -> {self.dest_path}"
        return f"{self.event_type.value}: {self.src_path}"


class ChangeBatch:
    """变更批处理 - 防抖机制"""

    def __init__(self, debounce_seconds: float = 1.0):
        self.debounce_seconds = debounce_seconds
        self._pending_changes: Dict[Path, FileChangeEvent] = {}
        self._last_change_time: float = 0
        self._timer: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    async def add_change(self, event: FileChangeEvent,
                        callback: Callable[[List[FileChangeEvent]], None]) -> None:
        """添加变更事件"""
        async with self._lock:
            # 合并同一文件的多次变更
            self._pending_changes[event.src_path] = event
            self._last_change_time = time.time()

            # 取消之前的定时器
            if self._timer and not self._timer.done():
                self._timer.cancel()

            # 创建新的定时器
            self._timer = asyncio.create_task(
                self._trigger_after_delay(callback)
            )

    async def _trigger_after_delay(self,
                                   callback: Callable[[List[FileChangeEvent]], None]) -> None:
        """延迟后触发回调"""
        await asyncio.sleep(self.debounce_seconds)

        async with self._lock:
            if self._pending_changes:
                changes = list(self._pending_changes.values())
                self._pending_changes.clear()
                try:
                    callback(changes)
                except Exception as e:
                    logger.error(f"Error processing change batch: {e}")

    def flush(self) -> List[FileChangeEvent]:
        """立即刷新所有待处理变更"""
        changes = list(self._pending_changes.values())
        self._pending_changes.clear()
        return changes


class MossFileEventHandler(FileSystemEventHandler):
    """MOSS 文件事件处理器"""

    def __init__(self,
                 config: WatchConfig,
                 on_change: Callable[[FileChangeEvent], None]):
        self.config = config
        self.on_change = on_change

    def _should_process(self, path: Path) -> bool:
        """检查是否应该处理该路径"""
        path_str = str(path)

        # 检查忽略模式
        for pattern in self.config.ignore_patterns:
            if self._match_pattern(path_str, pattern):
                return False

        # 检查包含模式
        if self.config.patterns:
            for pattern in self.config.patterns:
                if self._match_pattern(path_str, pattern):
                    return True
            return False

        return True

    def _match_pattern(self, path: str, pattern: str) -> bool:
        """简单的模式匹配"""
        import fnmatch
        return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(Path(path).name, pattern)

    def on_created(self, event):
        if isinstance(event, (FileCreatedEvent, DirCreatedEvent)):
            path = Path(event.src_path)
            if self._should_process(path):
                self.on_change(FileChangeEvent(
                    event_type=WatchEventType.CREATED,
                    src_path=path,
                    is_directory=event.is_directory
                ))

    def on_modified(self, event):
        if isinstance(event, (FileModifiedEvent, DirModifiedEvent)):
            path = Path(event.src_path)
            if self._should_process(path):
                self.on_change(FileChangeEvent(
                    event_type=WatchEventType.MODIFIED,
                    src_path=path,
                    is_directory=event.is_directory
                ))

    def on_deleted(self, event):
        if isinstance(event, (FileDeletedEvent, DirDeletedEvent)):
            path = Path(event.src_path)
            if self._should_process(path):
                self.on_change(FileChangeEvent(
                    event_type=WatchEventType.DELETED,
                    src_path=path,
                    is_directory=event.is_directory
                ))

    def on_moved(self, event):
        if isinstance(event, (FileMovedEvent, DirMovedEvent)):
            src_path = Path(event.src_path)
            dest_path = Path(event.dest_path)
            if self._should_process(src_path) or self._should_process(dest_path):
                self.on_change(FileChangeEvent(
                    event_type=WatchEventType.MOVED,
                    src_path=src_path,
                    dest_path=dest_path,
                    is_directory=event.is_directory
                ))


class FileWatcher:
    """
    MOSS 文件监控器

    基于 watchdog 实现跨平台文件监控，支持：
    - 多路径监控
    - 模式过滤
    - 防抖批处理
    - 异步回调
    """

    def __init__(self, config: Optional[WatchConfig] = None):
        if not WATCHDOG_AVAILABLE:
            raise RuntimeError(
                "watchdog is required for file watching. "
                "Install with: pip install watchdog"
            )

        self.config = config or WatchConfig()
        errors = self.config.validate()
        if errors:
            raise ValueError(f"Invalid config: {', '.join(errors)}")

        self._observer: Optional[Observer] = None
        self._batch = ChangeBatch(self.config.debounce_seconds)
        self._running = False
        self._change_callback: Optional[Callable[[List[FileChangeEvent]], None]] = None
        self._analyze_callback: Optional[Callable[[Path], None]] = None

    def on_changes(self,
                   callback: Callable[[List[FileChangeEvent]], None]) -> "FileWatcher":
        """设置变更回调"""
        self._change_callback = callback
        return self

    def on_analyze(self, callback: Callable[[Path], None]) -> "FileWatcher":
        """设置分析回调"""
        self._analyze_callback = callback
        return self

    def _handle_change(self, event: FileChangeEvent) -> None:
        """处理单个变更事件"""
        logger.debug(f"File change: {event}")

        # 添加到批处理
        if self._change_callback:
            asyncio.create_task(
                self._batch.add_change(event, self._change_callback)
            )

        # 立即分析 (如果启用)
        if self.config.auto_analyze and self._analyze_callback:
            if not event.is_directory and event.event_type in (
                WatchEventType.CREATED, WatchEventType.MODIFIED
            ):
                asyncio.create_task(self._analyze_with_delay(event.src_path))

    async def _analyze_with_delay(self, path: Path, delay: float = 0.5) -> None:
        """延迟后分析文件"""
        await asyncio.sleep(delay)
        if self._analyze_callback:
            try:
                self._analyze_callback(path)
            except Exception as e:
                logger.error(f"Error analyzing {path}: {e}")

    def start(self) -> None:
        """启动监控"""
        if self._running:
            logger.warning("File watcher already running")
            return

        self._observer = Observer()
        handler = MossFileEventHandler(self.config, self._handle_change)

        for path in self.config.paths:
            self._observer.schedule(
                handler,
                str(path),
                recursive=self.config.recursive
            )
            logger.info(f"Watching: {path} (recursive={self.config.recursive})")

        self._observer.start()
        self._running = True
        logger.info("File watcher started")

    def stop(self) -> None:
        """停止监控"""
        if not self._running:
            return

        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None

        self._running = False
        logger.info("File watcher stopped")

    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self._running

    async def run_forever(self) -> None:
        """保持运行直到被取消"""
        self.start()
        try:
            while self._running:
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
        finally:
            self.stop()


class AnalysisOrchestrator:
    """
    分析编排器

    协调文件变更与增量分析：
    - 收集变更文件
    - 批量分析
    - 结果聚合
    - 通知发送
    """

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self._pending_files: Set[Path] = set()
        self._lock = asyncio.Lock()
        self._analyzer: Optional[Any] = None

    async def initialize(self) -> None:
        """初始化分析器"""
        try:
            from moss.core.incremental_analyzer import IncrementalAnalyzer
            self._analyzer = IncrementalAnalyzer(str(self.project_path))
            logger.info("Analysis orchestrator initialized")
        except ImportError as e:
            logger.warning(f"Could not load analyzer: {e}")

    async def handle_changes(self, changes: List[FileChangeEvent]) -> Dict[str, Any]:
        """处理一批变更"""
        # 收集需要分析的文件
        files_to_analyze: Set[Path] = set()

        for change in changes:
            if change.is_directory:
                continue

            if change.event_type in (WatchEventType.CREATED, WatchEventType.MODIFIED):
                files_to_analyze.add(change.src_path)
            elif change.event_type == WatchEventType.MOVED and change.dest_path:
                files_to_analyze.add(change.dest_path)

        if not files_to_analyze:
            return {"status": "no_files_to_analyze"}

        # 执行分析
        results = await self._analyze_files(files_to_analyze)

        return {
            "status": "analyzed",
            "files_analyzed": len(files_to_analyze),
            "results": results,
        }

    async def _analyze_files(self, files: Set[Path]) -> Dict[str, Any]:
        """分析文件集合"""
        if not self._analyzer:
            return {"error": "Analyzer not initialized"}

        results = {}
        for file_path in files:
            try:
                # 这里调用实际的增量分析
                result = await self._analyze_single_file(file_path)
                results[str(file_path)] = result
            except Exception as e:
                logger.error(f"Error analyzing {file_path}: {e}")
                results[str(file_path)] = {"error": str(e)}

        return results

    async def _analyze_single_file(self, file_path: Path) -> Dict[str, Any]:
        """分析单个文件"""
        # 优先使用 IncrementalAnalyzer 进行真实分析
        if self._analyzer:
            try:
                # 使用增量分析器
                import hashlib
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                checksum = hashlib.sha256(content.encode()).hexdigest()

                # 尝试从缓存获取
                cached = self._analyzer.cache.get_file_analysis(str(file_path), checksum)
                if cached:
                    return {
                        'source': 'cache',
                        'lines': len(content.split('\n')),
                        'cached_result': True,
                        'issues': cached.get('issues', []),
                        'issue_count': len(cached.get('issues', [])),
                    }

                # 执行分析
                result = self._analyzer.analyze_file(str(file_path))

                # 缓存结果
                self._analyzer.cache.set_file_analysis(str(file_path), checksum, result)

                return {
                    'source': 'incremental_analyzer',
                    'lines': len(content.split('\n')),
                    'issues': result.get('issues', []),
                    'issue_count': len(result.get('issues', [])),
                    'metrics': result.get('metrics', {}),
                }
            except Exception as e:
                logger.warning(f"IncrementalAnalyzer failed for {file_path}: {e}, falling back")

        # 降级到简化版分析
        return await self._fallback_analyze(file_path)

    async def _fallback_analyze(self, file_path: Path) -> Dict[str, Any]:
        """降级分析 - 当 IncrementalAnalyzer 不可用时"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 简单的代码质量检查
            issues = []
            lines = content.split('\n')

            for i, line in enumerate(lines, 1):
                # 检查行长度
                if len(line) > 100:
                    issues.append({
                        'line': i,
                        'type': 'line_too_long',
                        'message': f'Line {i} is too long ({len(line)} chars)'
                    })

                # 检查尾随空格
                if line != line.rstrip():
                    issues.append({
                        'line': i,
                        'type': 'trailing_whitespace',
                        'message': f'Line {i} has trailing whitespace'
                    })

            return {
                'source': 'fallback',
                'lines': len(lines),
                'chars': len(content),
                'issues': issues,
                'issue_count': len(issues),
            }
        except Exception as e:
            return {'error': str(e)}


# ═══════════════════════════════════════════════════════════
# CLI Helper
# ═══════════════════════════════════════════════════════════

async def run_watch_cli(
    path: Path,
    patterns: List[str],
    auto_analyze: bool = True,
    auto_refactor: bool = False,
    debounce: float = 1.0,
) -> int:
    """
    CLI 入口：运行文件监控

    Args:
        path: 监控路径
        patterns: 文件模式列表
        auto_analyze: 自动分析变更文件
        auto_refactor: 自动重构 (谨慎使用)
        debounce: 防抖时间 (秒)

    Returns:
        退出码
    """
    if not WATCHDOG_AVAILABLE:
        print("错误: watchdog 未安装")
        print("安装命令: pip install watchdog")
        return 1

    config = WatchConfig(
        paths=[path],
        patterns=patterns if patterns else ["*.py"],
        auto_analyze=auto_analyze,
        auto_refactor=auto_refactor,
        debounce_seconds=debounce,
    )

    try:
        watcher = FileWatcher(config)
        orchestrator = AnalysisOrchestrator(path)
        await orchestrator.initialize()

        # 设置变更回调
        def on_changes(changes: List[FileChangeEvent]) -> None:
            print(f"\n📁 Detected {len(changes)} file change(s):")
            for change in changes:
                icon = {
                    WatchEventType.CREATED: "✚",
                    WatchEventType.MODIFIED: "✎",
                    WatchEventType.DELETED: "✖",
                    WatchEventType.MOVED: "➜",
                }.get(change.event_type, "•")
                print(f"  {icon} {change}")

            # 触发分析
            if auto_analyze:
                asyncio.create_task(handle_analysis(changes))

        async def handle_analysis(changes: List[FileChangeEvent]) -> None:
            result = await orchestrator.handle_changes(changes)
            if result.get("status") == "analyzed":
                print(f"\n📊 Analyzed {result['files_analyzed']} file(s)")
                for path_str, file_result in result.get("results", {}).items():
                    if "error" in file_result:
                        print(f"  ✗ {path_str}: {file_result['error']}")
                    elif file_result.get("issue_count", 0) > 0:
                        print(f"  ⚠ {path_str}: {file_result['issue_count']} issue(s)")
                    else:
                        print(f"  ✓ {path_str}: OK")

        watcher.on_changes(on_changes)

        print(f"👁️  Watching {path} for changes...")
        print(f"   Patterns: {', '.join(config.patterns)}")
        print(f"   Auto-analyze: {auto_analyze}")
        print(f"   Debounce: {debounce}s")
        print("\nPress Ctrl+C to stop\n")

        await watcher.run_forever()
        return 0

    except KeyboardInterrupt:
        print("\n\n👋 Stopped by user")
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


def demo_file_watcher():
    """演示文件监控"""
    if not WATCHDOG_AVAILABLE:
        print("watchdog not installed, skipping demo")
        return

    print("=" * 70)
    print("MOSS File Watcher Demo")
    print("=" * 70)
    print()

    # 创建临时目录进行演示
    import tempfile
    import shutil

    temp_dir = Path(tempfile.mkdtemp(prefix="moss_watch_demo_"))
    print(f"Demo directory: {temp_dir}")
    print("Try creating/modifying Python files in this directory...")
    print()

    async def demo():
        config = WatchConfig(
            paths=[temp_dir],
            patterns=["*.py"],
            debounce_seconds=0.5,
        )

        watcher = FileWatcher(config)

        change_count = [0]

        def on_changes(changes: List[FileChangeEvent]) -> None:
            change_count[0] += len(changes)
            print(f"[{change_count[0]}] Changes detected:")
            for change in changes:
                print(f"   {change}")

        watcher.on_changes(on_changes)

        # 启动监控
        watcher.start()

        # 模拟一些文件操作
        await asyncio.sleep(0.5)

        test_file = temp_dir / "test.py"
        test_file.write_text("print('hello')\n")
        print(f"Created: {test_file}")

        await asyncio.sleep(0.6)

        test_file.write_text("print('hello world')\n")
        print(f"Modified: {test_file}")

        await asyncio.sleep(0.6)

        test_file.unlink()
        print(f"Deleted: {test_file}")

        await asyncio.sleep(0.6)

        watcher.stop()

        # 清理
        shutil.rmtree(temp_dir)
        print(f"\nCleaned up: {temp_dir}")

    asyncio.run(demo())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo_file_watcher()
