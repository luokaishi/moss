#!/usr/bin/env python3
"""
MOSS v9.4 - Exception Hierarchy
统一异常体系

提供一致的错误处理和诊断信息：
- MossError: 基础异常
- AnalysisError: 分析相关
- RefactoringError: 重构相关
- LSPError: LSP协议相关
- ConfigError: 配置相关
"""

from typing import Any, Dict, Optional


class MossError(Exception):
    """
    MOSS 基础异常类

    所有 MOSS 异常的基类，提供统一的错误信息格式和上下文。

    Attributes:
        message: 人类可读的错误描述
        code: 错误代码 (如 "ANALYSIS.001")
        context: 附加上下文信息
        suggestion: 修复建议
    """

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        suggestion: Optional[str] = None,
    ):
        self.message = message
        self.code = code or self._default_code()
        self.context = context or {}
        self.suggestion = suggestion
        super().__init__(self.format())

    def _default_code(self) -> str:
        return "MOSS.000"

    def format(self) -> str:
        """格式化错误信息，包含代码、上下文和建议"""
        parts = [f"[{self.code}] {self.message}"]
        if self.context:
            for key, value in self.context.items():
                parts.append(f"  {key}: {value}")
        if self.suggestion:
            parts.append(f"  Suggestion: {self.suggestion}")
        return "\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，用于 JSON 输出"""
        return {
            "error": self.__class__.__name__,
            "code": self.code,
            "message": self.message,
            "context": self.context,
            "suggestion": self.suggestion,
        }


# ═══════════════════════════════════════════════════════════
# Analysis Errors
# ═══════════════════════════════════════════════════════════

class AnalysisError(MossError):
    """分析相关错误基类"""

    def _default_code(self) -> str:
        return "ANALYSIS.000"


class ParseError(AnalysisError):
    """AST 解析错误"""

    def __init__(
        self,
        message: str = "Failed to parse Python source",
        filepath: Optional[str] = None,
        line: Optional[int] = None,
        **kwargs,
    ):
        context = kwargs.pop("context", {})
        if filepath:
            context["file"] = filepath
        if line:
            context["line"] = line
        suggestion = kwargs.pop("suggestion", "Check for syntax errors in the file")
        super().__init__(message, code="ANALYSIS.001", context=context, suggestion=suggestion, **kwargs)


class DependencyError(AnalysisError):
    """依赖分析错误"""

    def __init__(
        self,
        message: str = "Dependency analysis failed",
        module: Optional[str] = None,
        **kwargs,
    ):
        context = kwargs.pop("context", {})
        if module:
            context["module"] = module
        suggestion = kwargs.pop("suggestion", "Check import paths and module availability")
        super().__init__(message, code="ANALYSIS.002", context=context, suggestion=suggestion, **kwargs)


class CacheError(AnalysisError):
    """缓存操作错误"""

    def __init__(
        self,
        message: str = "Cache operation failed",
        cache_path: Optional[str] = None,
        **kwargs,
    ):
        context = kwargs.pop("context", {})
        if cache_path:
            context["cache_path"] = cache_path
        suggestion = kwargs.pop("suggestion", "Clear cache with: moss cache --clear")
        super().__init__(message, code="ANALYSIS.003", context=context, suggestion=suggestion, **kwargs)


class FileWatchError(AnalysisError):
    """文件监视错误"""

    def __init__(
        self,
        message: str = "File watching failed",
        path: Optional[str] = None,
        **kwargs,
    ):
        context = kwargs.pop("context", {})
        if path:
            context["path"] = path
        suggestion = kwargs.pop("suggestion", "Ensure the path exists and is readable")
        super().__init__(message, code="ANALYSIS.004", context=context, suggestion=suggestion, **kwargs)


# ═══════════════════════════════════════════════════════════
# Refactoring Errors
# ═══════════════════════════════════════════════════════════

class RefactoringError(MossError):
    """重构相关错误基类"""

    def _default_code(self) -> str:
        return "REFACTOR.000"


class UnsafeRefactoringError(RefactoringError):
    """不安全的重构操作"""

    def __init__(
        self,
        message: str = "Refactoring is unsafe to apply",
        reason: Optional[str] = None,
        **kwargs,
    ):
        context = kwargs.pop("context", {})
        if reason:
            context["reason"] = reason
        suggestion = kwargs.pop("suggestion", "Review the impact analysis before proceeding")
        super().__init__(message, code="REFACTOR.001", context=context, suggestion=suggestion, **kwargs)


class ImpactAnalysisError(RefactoringError):
    """影响分析错误"""

    def __init__(
        self,
        message: str = "Impact analysis failed",
        symbol: Optional[str] = None,
        **kwargs,
    ):
        context = kwargs.pop("context", {})
        if symbol:
            context["symbol"] = symbol
        suggestion = kwargs.pop("suggestion", "Ensure the symbol exists and is importable")
        super().__init__(message, code="REFACTOR.002", context=context, suggestion=suggestion, **kwargs)


class RollbackError(RefactoringError):
    """回滚失败"""

    def __init__(
        self,
        message: str = "Failed to rollback refactoring",
        **kwargs,
    ):
        suggestion = kwargs.pop("suggestion", "Check git status and manually revert changes")
        super().__init__(message, code="REFACTOR.003", suggestion=suggestion, **kwargs)


class CrossFileError(RefactoringError):
    """跨文件重构错误"""

    def __init__(
        self,
        message: str = "Cross-file refactoring failed",
        files: Optional[list] = None,
        **kwargs,
    ):
        context = kwargs.pop("context", {})
        if files:
            context["affected_files"] = files
        suggestion = kwargs.pop("suggestion", "Review import dependencies across files")
        super().__init__(message, code="REFACTOR.004", context=context, suggestion=suggestion, **kwargs)


# ═══════════════════════════════════════════════════════════
# LSP Errors
# ═══════════════════════════════════════════════════════════

class LSPError(MossError):
    """LSP 协议相关错误基类"""

    def _default_code(self) -> str:
        return "LSP.000"


class ProtocolError(LSPError):
    """JSON-RPC 协议错误"""

    def __init__(
        self,
        message: str = "LSP protocol error",
        method: Optional[str] = None,
        code: Optional[int] = None,
        **kwargs,
    ):
        context = kwargs.pop("context", {})
        if method:
            context["method"] = method
        if code:
            context["jsonrpc_code"] = code
        suggestion = kwargs.pop("suggestion", "Check LSP client compatibility")
        super().__init__(message, code="LSP.001", context=context, suggestion=suggestion, **kwargs)


class TransportError(LSPError):
    """传输层错误"""

    def __init__(
        self,
        message: str = "LSP transport error",
        transport: Optional[str] = None,
        **kwargs,
    ):
        context = kwargs.pop("context", {})
        if transport:
            context["transport"] = transport
        suggestion = kwargs.pop("suggestion", "Check server path and port availability")
        super().__init__(message, code="LSP.002", context=context, suggestion=suggestion, **kwargs)


class ServerStartError(LSPError):
    """服务器启动错误"""

    def __init__(
        self,
        message: str = "Failed to start LSP server",
        port: Optional[int] = None,
        **kwargs,
    ):
        context = kwargs.pop("context", {})
        if port:
            context["port"] = port
        suggestion = kwargs.pop("suggestion", "Check if the port is already in use")
        super().__init__(message, code="LSP.003", context=context, suggestion=suggestion, **kwargs)


# ═══════════════════════════════════════════════════════════
# Config Errors
# ═══════════════════════════════════════════════════════════

class ConfigError(MossError):
    """配置相关错误基类"""

    def _default_code(self) -> str:
        return "CONFIG.000"


class ValidationError(ConfigError):
    """配置验证错误"""

    def __init__(
        self,
        message: str = "Configuration validation failed",
        field: Optional[str] = None,
        value: Any = None,
        expected: Optional[str] = None,
        **kwargs,
    ):
        context = kwargs.pop("context", {})
        if field:
            context["field"] = field
        if value is not None:
            context["value"] = repr(value)
        if expected:
            context["expected"] = expected
        suggestion = kwargs.pop("suggestion", f"Set '{field}' to a valid value" if field else "Check configuration format")
        super().__init__(message, code="CONFIG.001", context=context, suggestion=suggestion, **kwargs)


class MigrationError(ConfigError):
    """配置迁移错误"""

    def __init__(
        self,
        message: str = "Configuration migration failed",
        from_version: Optional[str] = None,
        to_version: Optional[str] = None,
        **kwargs,
    ):
        context = kwargs.pop("context", {})
        if from_version:
            context["from_version"] = from_version
        if to_version:
            context["to_version"] = to_version
        suggestion = kwargs.pop("suggestion", "Reset config with: moss init --reset")
        super().__init__(message, code="CONFIG.002", context=context, suggestion=suggestion, **kwargs)


class PluginError(MossError):
    """插件相关错误"""

    def _default_code(self) -> str:
        return "PLUGIN.000"

    def __init__(
        self,
        message: str = "Plugin error",
        plugin_name: Optional[str] = None,
        **kwargs,
    ):
        context = kwargs.pop("context", {})
        if plugin_name:
            context["plugin"] = plugin_name
        super().__init__(message, context=context, **kwargs)


class PluginLoadError(PluginError):
    """插件加载错误"""

    def __init__(
        self,
        message: str = "Failed to load plugin",
        plugin_name: Optional[str] = None,
        **kwargs,
    ):
        suggestion = kwargs.pop("suggestion", "Check plugin dependencies and Python version")
        super().__init__(message, code="PLUGIN.001", plugin_name=plugin_name, suggestion=suggestion, **kwargs)


class PluginConflictError(PluginError):
    """插件冲突"""

    def __init__(
        self,
        message: str = "Plugin conflict detected",
        plugin_name: Optional[str] = None,
        conflicting: Optional[str] = None,
        **kwargs,
    ):
        context = kwargs.pop("context", {})
        if conflicting:
            context["conflicting_with"] = conflicting
        suggestion = kwargs.pop("suggestion", "Disable one of the conflicting plugins")
        super().__init__(message, code="PLUGIN.002", plugin_name=plugin_name, context=context, suggestion=suggestion, **kwargs)


# ═══════════════════════════════════════════════════════════
# Error Code Registry
# ═══════════════════════════════════════════════════════════

ERROR_CODES = {
    "MOSS.000": "Unknown error",
    "ANALYSIS.000": "General analysis error",
    "ANALYSIS.001": "Parse error",
    "ANALYSIS.002": "Dependency analysis error",
    "ANALYSIS.003": "Cache error",
    "ANALYSIS.004": "File watch error",
    "REFACTOR.000": "General refactoring error",
    "REFACTOR.001": "Unsafe refactoring",
    "REFACTOR.002": "Impact analysis error",
    "REFACTOR.003": "Rollback error",
    "REFACTOR.004": "Cross-file refactoring error",
    "LSP.000": "General LSP error",
    "LSP.001": "Protocol error",
    "LSP.002": "Transport error",
    "LSP.003": "Server start error",
    "CONFIG.000": "General config error",
    "CONFIG.001": "Validation error",
    "CONFIG.002": "Migration error",
    "PLUGIN.000": "General plugin error",
    "PLUGIN.001": "Plugin load error",
    "PLUGIN.002": "Plugin conflict error",
}


def get_error_description(code: str) -> str:
    """根据错误代码获取描述"""
    return ERROR_CODES.get(code, "Unknown error code")
