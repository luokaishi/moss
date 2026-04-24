#!/usr/bin/env python3
"""
MOSS v9.4 - Test Suite
Phase 1: Exception Hierarchy, Plugin System, Config Manager
"""

import json
import tempfile
from pathlib import Path

import pytest

# ═══════════════════════════════════════════════════════════
# Exception Hierarchy Tests
# ═══════════════════════════════════════════════════════════


class TestExceptionHierarchy:
    """Test unified exception hierarchy"""

    def test_base_error(self):
        from moss.core.exceptions import MossError
        err = MossError("test error", code="TEST.001")
        assert str(err) == "[TEST.001] test error"
        assert err.code == "TEST.001"
        assert err.message == "test error"

    def test_error_with_context(self):
        from moss.core.exceptions import MossError
        err = MossError("test", code="X.001", context={"file": "foo.py"}, suggestion="fix it")
        formatted = err.format()
        assert "file: foo.py" in formatted
        assert "Suggestion: fix it" in formatted

    def test_error_to_dict(self):
        from moss.core.exceptions import MossError
        err = MossError("test", code="X.001", context={"key": "val"})
        d = err.to_dict()
        assert d["error"] == "MossError"
        assert d["code"] == "X.001"
        assert d["context"]["key"] == "val"

    def test_parse_error(self):
        from moss.core.exceptions import ParseError, MossError
        err = ParseError(filepath="test.py", line=42)
        assert isinstance(err, MossError)
        assert err.code == "ANALYSIS.001"
        assert "test.py" in err.format()
        assert "42" in err.format()

    def test_dependency_error(self):
        from moss.core.exceptions import DependencyError
        err = DependencyError(module="missing_module")
        assert err.code == "ANALYSIS.002"
        assert "missing_module" in err.format()

    def test_cache_error(self):
        from moss.core.exceptions import CacheError
        err = CacheError(cache_path="/tmp/cache.db")
        assert err.code == "ANALYSIS.003"

    def test_unsafe_refactoring_error(self):
        from moss.core.exceptions import UnsafeRefactoringError
        err = UnsafeRefactoringError(reason="breaks imports")
        assert err.code == "REFACTOR.001"
        assert "breaks imports" in err.format()

    def test_impact_analysis_error(self):
        from moss.core.exceptions import ImpactAnalysisError
        err = ImpactAnalysisError(symbol="MyClass")
        assert err.code == "REFACTOR.002"

    def test_rollback_error(self):
        from moss.core.exceptions import RollbackError
        err = RollbackError()
        assert err.code == "REFACTOR.003"

    def test_protocol_error(self):
        from moss.core.exceptions import ProtocolError
        err = ProtocolError(method="textDocument/hover", code=-32601)
        assert err.code == "LSP.001"

    def test_transport_error(self):
        from moss.core.exceptions import TransportError
        err = TransportError(transport="tcp")
        assert err.code == "LSP.002"

    def test_validation_error(self):
        from moss.core.exceptions import ValidationError
        err = ValidationError(field="threshold", value=-1, expected="positive integer")
        assert err.code == "CONFIG.001"
        assert "threshold" in err.format()

    def test_migration_error(self):
        from moss.core.exceptions import MigrationError
        err = MigrationError(from_version="9.2.0", to_version="9.4.0")
        assert err.code == "CONFIG.002"

    def test_plugin_load_error(self):
        from moss.core.exceptions import PluginLoadError
        err = PluginLoadError(plugin_name="bad-plugin")
        assert err.code == "PLUGIN.001"

    def test_plugin_conflict_error(self):
        from moss.core.exceptions import PluginConflictError
        err = PluginConflictError(plugin_name="p1", conflicting="p2")
        assert err.code == "PLUGIN.002"

    def test_error_code_registry(self):
        from moss.core.exceptions import ERROR_CODES, get_error_description
        assert len(ERROR_CODES) > 10
        assert "Parse error" in get_error_description("ANALYSIS.001")
        assert "Unknown" in get_error_description("NONEXISTENT.999")


# ═══════════════════════════════════════════════════════════
# Plugin System Tests
# ═══════════════════════════════════════════════════════════


class TestPluginSystem:
    """Test plugin architecture"""

    def test_plugin_base(self):
        from moss.core.plugin_system import MossPlugin
        # Can't instantiate abstract class directly for some methods
        # but the concrete plugins should work

    def test_git_plugin(self):
        from moss.core.plugin_system import GitPlugin
        plugin = GitPlugin()
        assert plugin.name == "moss-git"
        assert plugin.version == "1.0.0"
        assert not plugin.is_loaded

    def test_plugin_manager_register(self):
        from moss.core.plugin_system import PluginManager, GitPlugin
        manager = PluginManager()
        plugin = GitPlugin()
        manager.register(plugin)
        plugins = manager.list_plugins()
        assert len(plugins) == 1
        assert plugins[0].name == "moss-git"

    def test_plugin_manager_conflict(self):
        from moss.core.plugin_system import PluginManager, GitPlugin
        from moss.core.exceptions import PluginConflictError
        manager = PluginManager()
        manager.register(GitPlugin())
        with pytest.raises(PluginConflictError):
            manager.register(GitPlugin())

    def test_plugin_manager_unregister(self):
        from moss.core.plugin_system import PluginManager, GitPlugin
        manager = PluginManager()
        manager.register(GitPlugin())
        manager.unregister("moss-git")
        assert len(manager.list_plugins()) == 0

    def test_plugin_load_unload(self):
        from moss.core.plugin_system import PluginManager, PluginContext, GitPlugin
        manager = PluginManager()
        plugin = GitPlugin()
        manager.register(plugin)

        context = PluginContext(project_path=Path("/tmp"))
        manager.load_all(context)

        assert plugin.is_loaded

        manager.unregister("moss-git")
        assert not plugin.is_loaded

    def test_plugin_emit_hook(self):
        from moss.core.plugin_system import PluginManager, PluginContext, HookType, CoveragePlugin
        manager = PluginManager()
        manager.register(CoveragePlugin())

        context = PluginContext()
        manager.load_all(context)

        # Should not raise
        manager.emit(HookType.ANALYSIS_START, project_path=Path("."))

    def test_multiple_plugins(self):
        from moss.core.plugin_system import PluginManager, PluginContext, GitPlugin, CoveragePlugin
        manager = PluginManager()
        manager.register(GitPlugin())
        manager.register(CoveragePlugin())

        context = PluginContext()
        manager.load_all(context)

        plugins = manager.list_plugins()
        assert len(plugins) == 2
        names = {p.name for p in plugins}
        assert "moss-git" in names
        assert "moss-coverage" in names

    def test_plugin_get(self):
        from moss.core.plugin_system import PluginManager, GitPlugin
        manager = PluginManager()
        manager.register(GitPlugin())

        plugin = manager.get_plugin("moss-git")
        assert plugin is not None
        assert plugin.name == "moss-git"

        assert manager.get_plugin("nonexistent") is None


# ═══════════════════════════════════════════════════════════
# Config Manager Tests
# ═══════════════════════════════════════════════════════════


class TestConfigManager:
    """Test configuration management"""

    def test_default_config(self):
        from moss.core.config_manager import MossProjectConfig
        config = MossProjectConfig()
        assert config.version == "9.4.0"
        assert config.analysis.long_function_threshold == 50
        assert config.performance.enable_l1_cache is True
        assert config.lsp.port == 8990

    def test_config_validation_valid(self):
        from moss.core.config_manager import MossProjectConfig
        config = MossProjectConfig()
        errors = config.validate()
        assert len(errors) == 0

    def test_config_validation_invalid(self):
        from moss.core.config_manager import AnalysisConfig, LSPConfig
        # Invalid analysis config
        analysis = AnalysisConfig(long_function_threshold=-1)
        errors = analysis.validate()
        assert len(errors) > 0

        # Invalid LSP config
        lsp = LSPConfig(port=99999, transport="invalid")
        errors = lsp.validate()
        assert len(errors) > 0

    def test_config_manager_load_no_file(self):
        from moss.core.config_manager import ConfigManager
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigManager(Path(tmpdir))
            config = manager.load()
            assert config.version == "9.4.0"

    def test_config_manager_save_and_load(self):
        from moss.core.config_manager import ConfigManager
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save
            manager = ConfigManager(Path(tmpdir))
            manager.config.analysis.long_function_threshold = 100
            manager.save()

            # Load
            manager2 = ConfigManager(Path(tmpdir))
            config = manager2.load()
            assert config.analysis.long_function_threshold == 100

    def test_config_migration(self):
        from moss.core.config_manager import ConfigManager
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write v9.2 config
            config_path = Path(tmpdir) / ".moss" / "config.json"
            config_path.parent.mkdir(parents=True)
            old_config = {
                "version": "9.2.0",
                "project_name": "test",
                "analysis": {"long_function_threshold": 80},
            }
            with open(config_path, "w") as f:
                json.dump(old_config, f)

            # Load - should migrate to 9.4.0
            manager = ConfigManager(Path(tmpdir))
            config = manager.load()
            assert config.version == "9.4.0"
            assert config.analysis.long_function_threshold == 80
            assert "logging" in manager._serialize_config(config)

    def test_config_env_override(self):
        import os
        from moss.core.config_manager import ConfigManager

        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["MOSS_LSP_PORT"] = "9999"
            try:
                manager = ConfigManager(Path(tmpdir))
                config = manager.load()
                assert config.lsp.port == 9999
            finally:
                del os.environ["MOSS_LSP_PORT"]

    def test_config_reset(self):
        from moss.core.config_manager import ConfigManager
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigManager(Path(tmpdir))
            manager.config.analysis.long_function_threshold = 200
            manager.save()

            config = manager.reset()
            assert config.analysis.long_function_threshold == 50

    def test_invalid_json_config(self):
        from moss.core.config_manager import ConfigManager
        from moss.core.exceptions import ConfigError
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".moss" / "config.json"
            config_path.parent.mkdir(parents=True)
            with open(config_path, "w") as f:
                f.write("{invalid json}")

            manager = ConfigManager(Path(tmpdir))
            with pytest.raises(ConfigError):
                manager.load()

    def test_ml_config_validation(self):
        from moss.core.config_manager import MLConfig
        # Valid
        config = MLConfig()
        assert len(config.validate()) == 0

        # Invalid confidence
        config = MLConfig(confidence_threshold=1.5)
        errors = config.validate()
        assert len(errors) > 0

    def test_logging_config(self):
        from moss.core.config_manager import LoggingConfig
        config = LoggingConfig(level="debug", format="json")
        assert len(config.validate()) == 0

        config = LoggingConfig(level="invalid")
        errors = config.validate()
        assert len(errors) > 0
