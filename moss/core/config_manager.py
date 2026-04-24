#!/usr/bin/env python3
"""
MOSS v9.4 - Configuration Manager
配置验证与管理

功能：
- Schema-based 配置验证
- 自动迁移旧版本配置
- 配置文件热重载
- 环境变量覆盖
"""

import json
import logging
import os
from copy import deepcopy
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type, get_type_hints

from .exceptions import ConfigError, ValidationError, MigrationError

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Configuration Schema
# ═══════════════════════════════════════════════════════════

@dataclass
class AnalysisConfig:
    """分析配置"""
    long_function_threshold: int = 50
    high_complexity_threshold: int = 10
    max_nesting_depth: int = 4
    enable_unused_import_detection: bool = True
    enable_type_hint_check: bool = True

    def validate(self) -> List[str]:
        errors = []
        if self.long_function_threshold < 1:
            errors.append("long_function_threshold must be >= 1")
        if self.high_complexity_threshold < 1:
            errors.append("high_complexity_threshold must be >= 1")
        if self.max_nesting_depth < 1:
            errors.append("max_nesting_depth must be >= 1")
        return errors


@dataclass
class PerformanceConfig:
    """性能配置"""
    enable_l1_cache: bool = True
    enable_l2_cache: bool = True
    enable_l3_cache: bool = False
    l1_max_size: int = 1000
    l2_db_path: str = ".moss/cache/analysis_cache.db"
    max_workers: int = 0  # 0 = auto
    incremental: bool = True
    parallel: bool = True

    def validate(self) -> List[str]:
        errors = []
        if self.l1_max_size < 10:
            errors.append("l1_max_size must be >= 10")
        if self.max_workers < 0:
            errors.append("max_workers must be >= 0")
        return errors


@dataclass
class LSPConfig:
    """LSP 服务器配置"""
    host: str = "127.0.0.1"
    port: int = 8990
    transport: str = "stdio"  # stdio | tcp
    log_level: str = "info"
    trace: str = "off"  # off | messages | verbose

    def validate(self) -> List[str]:
        errors = []
        if self.port < 1 or self.port > 65535:
            errors.append(f"port must be between 1-65535, got {self.port}")
        if self.transport not in ("stdio", "tcp"):
            errors.append(f"transport must be 'stdio' or 'tcp', got '{self.transport}'")
        if self.log_level not in ("debug", "info", "warning", "error"):
            errors.append(f"Invalid log_level: {self.log_level}")
        if self.trace not in ("off", "messages", "verbose"):
            errors.append(f"Invalid trace: {self.trace}")
        return errors


@dataclass
class MLConfig:
    """ML 推荐配置"""
    enable_recommendations: bool = True
    confidence_threshold: float = 0.6
    max_recommendations: int = 10
    enable_pattern_learning: bool = True
    history_db_path: str = ".moss/history/refactoring_history.json"

    def validate(self) -> List[str]:
        errors = []
        if not 0.0 <= self.confidence_threshold <= 1.0:
            errors.append(f"confidence_threshold must be 0.0-1.0, got {self.confidence_threshold}")
        if self.max_recommendations < 1:
            errors.append("max_recommendations must be >= 1")
        return errors


@dataclass
class TeamConfig:
    """团队协作配置"""
    enabled: bool = False
    shared_config_path: str = ""
    audit_log_path: str = ".moss/audit/audit_log.json"
    enable_knowledge_base: bool = True
    enable_quality_dashboard: bool = True

    def validate(self) -> List[str]:
        errors = []
        if self.enabled and not self.shared_config_path:
            errors.append("shared_config_path is required when team mode is enabled")
        return errors


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "info"
    format: str = "text"  # text | json
    file: str = ""  # empty = stderr only
    module_levels: Dict[str, str] = field(default_factory=dict)

    def validate(self) -> List[str]:
        errors = []
        valid_levels = ("debug", "info", "warning", "error", "critical")
        if self.level not in valid_levels:
            errors.append(f"Invalid log level: {self.level}")
        if self.format not in ("text", "json"):
            errors.append(f"Invalid log format: {self.format}")
        for module, level in self.module_levels.items():
            if level not in valid_levels:
                errors.append(f"Invalid log level for {module}: {level}")
        return errors


@dataclass
class MossProjectConfig:
    """MOSS 项目完整配置"""
    version: str = "9.4.0"
    project_name: str = ""
    project_path: str = "."

    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    lsp: LSPConfig = field(default_factory=LSPConfig)
    ml: MLConfig = field(default_factory=MLConfig)
    team: TeamConfig = field(default_factory=TeamConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    # 插件
    plugins: List[str] = field(default_factory=list)
    disabled_plugins: List[str] = field(default_factory=list)

    def validate(self) -> List[str]:
        """验证整个配置"""
        errors = []
        errors.extend(self.analysis.validate())
        errors.extend(self.performance.validate())
        errors.extend(self.lsp.validate())
        errors.extend(self.ml.validate())
        errors.extend(self.team.validate())
        errors.extend(self.logging.validate())
        return errors


# ═══════════════════════════════════════════════════════════
# Config Migrations
# ═══════════════════════════════════════════════════════════

CONFIG_MIGRATIONS = {
    "9.2.0": {
        "9.3.0": lambda cfg: _migrate_92_to_93(cfg),
    },
    "9.3.0": {
        "9.4.0": lambda cfg: _migrate_93_to_94(cfg),
    },
}


def _migrate_92_to_93(cfg: dict) -> dict:
    """v9.2 → v9.3 迁移"""
    if "performance" not in cfg:
        cfg["performance"] = {}
    if "lsp" not in cfg:
        cfg["lsp"] = {}
    if "ml" not in cfg:
        cfg["ml"] = {}
    if "team" not in cfg:
        cfg["team"] = {}
    cfg["version"] = "9.3.0"
    return cfg


def _migrate_93_to_94(cfg: dict) -> dict:
    """v9.3 → v9.4 迁移"""
    if "logging" not in cfg:
        cfg["logging"] = {}
    if "plugins" not in cfg:
        cfg["plugins"] = []
    if "disabled_plugins" not in cfg:
        cfg["disabled_plugins"] = []
    cfg["version"] = "9.4.0"
    return cfg


# ═══════════════════════════════════════════════════════════
# Config Manager
# ═══════════════════════════════════════════════════════════

class ConfigManager:
    """
    配置管理器

    功能：
    - 加载/保存配置文件
    - 配置验证
    - 版本迁移
    - 环境变量覆盖

    Example:
        manager = ConfigManager()
        config = manager.load("/path/to/project")
        print(config.analysis.long_function_threshold)

        # 保存
        config.analysis.long_function_threshold = 80
        manager.save()
    """

    CONFIG_FILENAME = ".moss/config.json"
    ENV_PREFIX = "MOSS_"

    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
        self.config = MossProjectConfig()
        self._config_path = self.project_path / self.CONFIG_FILENAME

    def load(self, path: Optional[Path] = None) -> MossProjectConfig:
        """
        加载配置

        Args:
            path: 项目路径，默认使用初始化路径

        Returns:
            验证后的配置对象

        Raises:
            ConfigError: 配置加载失败
            ValidationError: 配置验证失败
            MigrationError: 配置迁移失败
        """
        if path:
            self.project_path = path
            self._config_path = path / self.CONFIG_FILENAME

        if not self._config_path.exists():
            logger.info(f"No config file found at {self._config_path}, using defaults")
            self.config = MossProjectConfig(project_path=str(self.project_path))
            self._apply_env_overrides()
            return self.config

        try:
            with open(self._config_path) as f:
                raw = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigError(
                f"Invalid JSON in config file: {e}",
                context={"path": str(self._config_path)},
                suggestion="Fix JSON syntax or run: moss init --reset",
            ) from e
        except OSError as e:
            raise ConfigError(
                f"Cannot read config file: {e}",
                context={"path": str(self._config_path)},
            ) from e

        # 版本迁移
        raw = self._migrate(raw)

        # 解析为配置对象
        self.config = self._parse_config(raw)

        # 环境变量覆盖
        self._apply_env_overrides()

        # 验证
        errors = self.config.validate()
        if errors:
            raise ValidationError(
                f"Configuration has {len(errors)} error(s)",
                context={"errors": errors},
                suggestion="Fix the errors or run: moss init --reset",
            )

        logger.info(f"Configuration loaded from {self._config_path}")
        return self.config

    def save(self, path: Optional[Path] = None) -> None:
        """
        保存配置

        Args:
            path: 项目路径
        """
        if path:
            self.project_path = path
            self._config_path = path / self.CONFIG_FILENAME

        # 验证
        errors = self.config.validate()
        if errors:
            raise ValidationError(
                f"Cannot save invalid configuration: {errors}",
            )

        # 确保目录存在
        self._config_path.parent.mkdir(parents=True, exist_ok=True)

        # 序列化
        data = self._serialize_config(self.config)

        with open(self._config_path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Configuration saved to {self._config_path}")

    def reset(self) -> MossProjectConfig:
        """重置为默认配置"""
        self.config = MossProjectConfig(project_path=str(self.project_path))
        self.save()
        logger.info("Configuration reset to defaults")
        return self.config

    # ── 内部方法 ──

    def _migrate(self, raw: dict) -> dict:
        """执行配置迁移"""
        current_version = raw.get("version", "9.2.0")
        target_version = "9.4.0"

        if current_version == target_version:
            return raw

        raw = deepcopy(raw)

        while current_version != target_version:
            migrations = CONFIG_MIGRATIONS.get(current_version, {})
            if target_version in migrations:
                try:
                    raw = migrations[target_version](raw)
                    current_version = raw.get("version", current_version)
                    logger.info(f"Migrated config from {current_version} to {raw['version']}")
                except Exception as e:
                    raise MigrationError(
                        f"Failed to migrate config from {current_version} to {target_version}",
                        from_version=current_version,
                        to_version=target_version,
                    ) from e
            else:
                # 尝试逐步迁移
                next_version = None
                for v in sorted(migrations.keys()):
                    next_version = v
                    break
                if next_version:
                    raw = migrations[next_version](raw)
                    current_version = raw.get("version", current_version)
                else:
                    raise MigrationError(
                        f"No migration path from {current_version} to {target_version}",
                        from_version=current_version,
                        to_version=target_version,
                    )

        return raw

    def _parse_config(self, raw: dict) -> MossProjectConfig:
        """解析原始字典为配置对象"""
        config = MossProjectConfig(
            version=raw.get("version", "9.4.0"),
            project_name=raw.get("project_name", ""),
            project_path=str(self.project_path),
            plugins=raw.get("plugins", []),
            disabled_plugins=raw.get("disabled_plugins", []),
        )

        # 解析子配置
        if "analysis" in raw:
            config.analysis = AnalysisConfig(**{
                k: v for k, v in raw["analysis"].items()
                if k in {f.name for f in fields(AnalysisConfig)}
            })

        if "performance" in raw:
            config.performance = PerformanceConfig(**{
                k: v for k, v in raw["performance"].items()
                if k in {f.name for f in fields(PerformanceConfig)}
            })

        if "lsp" in raw:
            config.lsp = LSPConfig(**{
                k: v for k, v in raw["lsp"].items()
                if k in {f.name for f in fields(LSPConfig)}
            })

        if "ml" in raw:
            config.ml = MLConfig(**{
                k: v for k, v in raw["ml"].items()
                if k in {f.name for f in fields(MLConfig)}
            })

        if "team" in raw:
            config.team = TeamConfig(**{
                k: v for k, v in raw["team"].items()
                if k in {f.name for f in fields(TeamConfig)}
            })

        if "logging" in raw:
            config.logging = LoggingConfig(**{
                k: v for k, v in raw["logging"].items()
                if k in {f.name for f in fields(LoggingConfig)}
            })

        return config

    def _serialize_config(self, config: MossProjectConfig) -> dict:
        """序列化配置对象为字典"""
        import dataclasses

        def _to_dict(obj):
            if dataclasses.is_dataclass(obj):
                return {k: _to_dict(v) for k, v in dataclasses.asdict(obj).items()}
            return obj

        return _to_dict(config)

    def _apply_env_overrides(self) -> None:
        """应用环境变量覆盖"""
        env_map = {
            "MOSS_LSP_PORT": ("lsp", "port", int),
            "MOSS_LSP_HOST": ("lsp", "host", str),
            "MOSS_LSP_TRANSPORT": ("lsp", "transport", str),
            "MOSS_LOG_LEVEL": ("logging", "level", str),
            "MOSS_MAX_WORKERS": ("performance", "max_workers", int),
            "MOSS_CACHE_LEVEL": ("performance", "enable_l2_cache", lambda x: x == "full"),
            "MOSS_TEAM_ENABLED": ("team", "enabled", lambda x: x.lower() in ("1", "true", "yes")),
        }

        for env_var, (section, key, converter) in env_map.items():
            value = os.environ.get(env_var)
            if value is not None:
                try:
                    converted = converter(value)
                    section_config = getattr(self.config, section)
                    setattr(section_config, key, converted)
                    logger.debug(f"Env override: {env_var} → {section}.{key} = {converted}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid env override {env_var}={value}: {e}")
