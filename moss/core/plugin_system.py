#!/usr/bin/env python3
"""
MOSS v9.4 - Plugin System
可扩展插件架构

允许第三方扩展 MOSS 功能：
- 自定义分析器
- 自定义重构建议
- 自定义报告格式
- 集成外部工具

Usage:
    from moss.core.plugin_system import MossPlugin, PluginManager

    class MyPlugin(MossPlugin):
        name = "my-plugin"
        version = "1.0.0"

        def on_analysis_complete(self, results):
            # 自定义处理
            pass

    manager = PluginManager()
    manager.register(MyPlugin())
"""

import importlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type

from .exceptions import PluginLoadError, PluginConflictError

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Plugin Hooks
# ═══════════════════════════════════════════════════════════

class HookPriority(Enum):
    """Hook 优先级"""
    LOWEST = 0
    LOW = 25
    NORMAL = 50
    HIGH = 75
    HIGHEST = 100


@dataclass
class HookCallback:
    """Hook 回调注册"""
    callback: Callable
    priority: HookPriority = HookPriority.NORMAL
    plugin_name: str = ""


class HookType(Enum):
    """Hook 类型"""
    # 分析生命周期
    ANALYSIS_START = "analysis_start"
    ANALYSIS_COMPLETE = "analysis_complete"
    ANALYSIS_ERROR = "analysis_error"

    # 重构生命周期
    REFACTORING_PROPOSED = "refactoring_proposed"
    REFACTORING_APPLIED = "refactoring_applied"
    REFACTORING_ROLLED_BACK = "refactoring_rolled_back"

    # 文件变更
    FILE_CHANGED = "file_changed"
    FILE_ADDED = "file_added"
    FILE_REMOVED = "file_removed"

    # 服务器
    SERVER_START = "server_start"
    SERVER_STOP = "server_stop"

    # 自定义
    CUSTOM = "custom"


# ═══════════════════════════════════════════════════════════
# Plugin Context
# ═══════════════════════════════════════════════════════════

@dataclass
class PluginContext:
    """
    插件上下文

    提供插件与 MOSS 核心交互的接口。
    """
    project_path: Path = Path(".")
    config: Dict[str, Any] = field(default_factory=dict)
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger("moss.plugin"))

    # 核心组件引用（延迟设置）
    _analyzer: Any = None
    _engine: Any = None

    def get_analyzer(self):
        """获取分析器实例"""
        return self._analyzer

    def get_engine(self):
        """获取性能引擎实例"""
        return self._engine

    def register_command(self, name: str, handler: Callable):
        """注册自定义 CLI 命令"""
        logger.info(f"Plugin registered command: {name}")

    def register_diagnostic(self, diagnostic_type: str, handler: Callable):
        """注册自定义诊断"""
        logger.info(f"Plugin registered diagnostic: {diagnostic_type}")


# ═══════════════════════════════════════════════════════════
# Base Plugin
# ═══════════════════════════════════════════════════════════

class MossPlugin(ABC):
    """
    MOSS 插件基类

    所有插件必须继承此类并实现必要的方法。

    Example:
        class MyPlugin(MossPlugin):
            name = "my-plugin"
            version = "1.0.0"
            description = "My custom MOSS plugin"

            def on_load(self, context):
                self.context = context

            def on_analysis_complete(self, results):
                self.context.logger.info(f"Analysis done: {len(results)} results")
    """

    # 插件元数据（子类必须设置）
    name: str = "unnamed-plugin"
    version: str = "0.0.0"
    description: str = ""
    author: str = ""
    dependencies: List[str] = field(default_factory=list)

    # 插件状态
    _loaded: bool = False
    _context: Optional[PluginContext] = None

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    # ── 生命周期 ──

    def on_load(self, context: PluginContext) -> None:
        """插件加载时调用。子类可覆盖以初始化资源。"""
        self._context = context
        self._loaded = True

    def on_unload(self) -> None:
        """插件卸载时调用。子类可覆盖以清理资源。"""
        self._loaded = False
        self._context = None

    # ── Hook 方法（可选覆盖）──

    def on_analysis_start(self, project_path: Path) -> None:
        """分析开始时的 Hook"""
        pass

    def on_analysis_complete(self, results: Any) -> None:
        """分析完成时的 Hook"""
        pass

    def on_analysis_error(self, error: Exception) -> None:
        """分析出错时的 Hook"""
        pass

    def on_refactoring_proposed(self, suggestion: Any) -> Optional[Any]:
        """重构建议提出时的 Hook，可修改或否决建议"""
        return suggestion

    def on_refactoring_applied(self, result: Any) -> None:
        """重构应用完成时的 Hook"""
        pass

    def on_refactoring_rolled_back(self, result: Any) -> None:
        """重构回滚时的 Hook"""
        pass

    def on_file_changed(self, filepath: Path, change_type: str) -> None:
        """文件变更时的 Hook"""
        pass

    def on_server_start(self, port: int) -> None:
        """LSP 服务器启动时的 Hook"""
        pass

    def on_server_stop(self) -> None:
        """LSP 服务器停止时的 Hook"""
        pass

    def __repr__(self) -> str:
        return f"<MossPlugin {self.name}@{self.version}>"


# ═══════════════════════════════════════════════════════════
# Plugin Info
# ═══════════════════════════════════════════════════════════

@dataclass
class PluginInfo:
    """插件信息"""
    name: str
    version: str
    description: str
    author: str
    is_loaded: bool = False
    plugin: Optional[MossPlugin] = None


# ═══════════════════════════════════════════════════════════
# Plugin Manager
# ═══════════════════════════════════════════════════════════

class PluginManager:
    """
    插件管理器

    管理插件的注册、加载、卸载和 Hook 调度。

    Example:
        manager = PluginManager()
        manager.register(MyPlugin())
        manager.load_all(context)

        # 调用 Hook
        manager.emit(HookType.ANALYSIS_COMPLETE, results=analysis_results)
    """

    def __init__(self):
        self._plugins: Dict[str, MossPlugin] = {}
        self._hooks: Dict[HookType, List[HookCallback]] = {
            hook: [] for hook in HookType
        }
        self._context: Optional[PluginContext] = None
        self.logger = logging.getLogger(f"{__name__}.PluginManager")

    # ── 插件管理 ──

    def register(self, plugin: MossPlugin) -> None:
        """
        注册插件

        Args:
            plugin: 插件实例

        Raises:
            PluginConflictError: 如果同名插件已注册
        """
        if plugin.name in self._plugins:
            existing = self._plugins[plugin.name]
            raise PluginConflictError(
                f"Plugin '{plugin.name}' is already registered",
                plugin_name=plugin.name,
                conflicting=existing.name,
            )

        self._plugins[plugin.name] = plugin
        self._register_hooks(plugin)
        self.logger.info(f"Registered plugin: {plugin.name}@{plugin.version}")

    def unregister(self, name: str) -> None:
        """
        卸载并注销插件

        Args:
            name: 插件名称
        """
        if name not in self._plugins:
            self.logger.warning(f"Plugin '{name}' not found")
            return

        plugin = self._plugins[name]
        if plugin.is_loaded:
            plugin.on_unload()

        self._unregister_hooks(plugin)
        del self._plugins[name]
        self.logger.info(f"Unregistered plugin: {name}")

    def load_all(self, context: PluginContext) -> None:
        """
        加载所有已注册的插件

        Args:
            context: 插件上下文
        """
        self._context = context
        for name, plugin in self._plugins.items():
            if not plugin.is_loaded:
                try:
                    plugin.on_load(context)
                    self.logger.info(f"Loaded plugin: {name}@{plugin.version}")
                except Exception as e:
                    raise PluginLoadError(
                        f"Failed to load plugin '{name}': {e}",
                        plugin_name=name,
                    ) from e

    def unload_all(self) -> None:
        """卸载所有插件"""
        for name in list(self._plugins.keys()):
            self.unregister(name)

    def get_plugin(self, name: str) -> Optional[MossPlugin]:
        """获取插件实例"""
        return self._plugins.get(name)

    def list_plugins(self) -> List[PluginInfo]:
        """列出所有插件信息"""
        return [
            PluginInfo(
                name=p.name,
                version=p.version,
                description=p.description,
                author=p.author,
                is_loaded=p.is_loaded,
                plugin=p,
            )
            for p in self._plugins.values()
        ]

    # ── Hook 系统 ──

    def _register_hooks(self, plugin: MossPlugin) -> None:
        """注册插件的所有 Hook"""
        hook_map = {
            HookType.ANALYSIS_START: plugin.on_analysis_start,
            HookType.ANALYSIS_COMPLETE: plugin.on_analysis_complete,
            HookType.ANALYSIS_ERROR: plugin.on_analysis_error,
            HookType.REFACTORING_PROPOSED: plugin.on_refactoring_proposed,
            HookType.REFACTORING_APPLIED: plugin.on_refactoring_applied,
            HookType.REFACTORING_ROLLED_BACK: plugin.on_refactoring_rolled_back,
            HookType.FILE_CHANGED: plugin.on_file_changed,
            HookType.SERVER_START: plugin.on_server_start,
            HookType.SERVER_STOP: plugin.on_server_stop,
        }

        for hook_type, callback in hook_map.items():
            # 检查方法是否被子类覆盖（不是基类的空实现）
            base_method = getattr(MossPlugin, callback.__name__, None)
            if callback.__func__ is not base_method:
                self._hooks[hook_type].append(
                    HookCallback(
                        callback=callback,
                        plugin_name=plugin.name,
                    )
                )

    def _unregister_hooks(self, plugin: MossPlugin) -> None:
        """注销插件的所有 Hook"""
        for hook_type in self._hooks:
            self._hooks[hook_type] = [
                cb for cb in self._hooks[hook_type]
                if cb.plugin_name != plugin.name
            ]

    def emit(self, hook_type: HookType, **kwargs: Any) -> List[Any]:
        """
        触发 Hook

        Args:
            hook_type: Hook 类型
            **kwargs: Hook 参数

        Returns:
            所有 Hook 的返回值列表
        """
        results = []
        callbacks = sorted(
            self._hooks.get(hook_type, []),
            key=lambda cb: cb.priority.value,
            reverse=True,
        )

        for cb in callbacks:
            try:
                result = cb.callback(**kwargs)
                results.append(result)
            except Exception as e:
                self.logger.error(
                    f"Hook error in plugin '{cb.plugin_name}' "
                    f"for {hook_type.value}: {e}"
                )

        return results

    # ── 插件发现 ──

    def discover_plugins(self, plugin_dir: Optional[Path] = None) -> List[str]:
        """
        发现可用插件

        Args:
            plugin_dir: 插件目录，默认为 ~/.moss/plugins/

        Returns:
            发现的插件模块列表
        """
        if plugin_dir is None:
            plugin_dir = Path.home() / ".moss" / "plugins"

        if not plugin_dir.exists():
            return []

        discovered = []
        for path in plugin_dir.iterdir():
            if path.is_dir() and (path / "__init__.py").exists():
                discovered.append(path.name)
            elif path.suffix == ".py" and path.name != "__init__.py":
                discovered.append(path.stem)

        self.logger.info(f"Discovered {len(discovered)} plugins in {plugin_dir}")
        return discovered

    def load_plugin_from_module(self, module_name: str) -> Optional[MossPlugin]:
        """
        从模块加载插件

        Args:
            module_name: Python 模块名

        Returns:
            加载的插件实例，如果模块没有插件则返回 None
        """
        try:
            module = importlib.import_module(module_name)
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, MossPlugin)
                    and attr is not MossPlugin
                ):
                    plugin = attr()
                    self.register(plugin)
                    return plugin
        except Exception as e:
            raise PluginLoadError(
                f"Failed to load plugin from module '{module_name}': {e}",
                plugin_name=module_name,
            ) from e

        return None


# ═══════════════════════════════════════════════════════════
# Built-in Plugins
# ═══════════════════════════════════════════════════════════

class GitPlugin(MossPlugin):
    """Git 集成插件 - 提供 Git 感知的分析"""

    name = "moss-git"
    version = "1.0.0"
    description = "Git integration for MOSS - blame-aware analysis"
    author = "MOSS Team"

    def on_analysis_start(self, project_path: Path) -> None:
        """检查 Git 状态"""
        git_dir = project_path / ".git"
        if git_dir.exists():
            self.logger.info(f"Git repository detected at {project_path}")
        else:
            self.logger.info(f"No Git repository at {project_path}")

    def on_refactoring_proposed(self, suggestion: Any) -> Any:
        """检查建议是否影响未提交的更改"""
        # 可以在这里添加 git diff 检查
        return suggestion


class CoveragePlugin(MossPlugin):
    """覆盖率集成插件 - 基于 coverage.py 数据"""

    name = "moss-coverage"
    version = "1.0.0"
    description = "Coverage.py integration - prioritize uncovered code"
    author = "MOSS Team"

    def on_analysis_start(self, project_path: Path) -> None:
        """查找覆盖率数据"""
        coverage_file = project_path / ".coverage"
        if coverage_file.exists():
            self.logger.info(f"Coverage data found at {coverage_file}")


class TypeCheckPlugin(MossPlugin):
    """类型检查集成插件"""

    name = "moss-typecheck"
    version = "1.0.0"
    description = "Type checker integration - mypy/pyright support"
    author = "MOSS Team"

    def on_analysis_complete(self, results: Any) -> None:
        """分析完成后运行类型检查"""
        self.logger.debug("Type check plugin: analysis complete hook")
