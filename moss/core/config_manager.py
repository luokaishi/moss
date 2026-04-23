#!/usr/bin/env python3
"""
MOSS v9.2 - Configuration Manager
配置管理系统

Author: MOSS v9.2
Date: 2026-04-23
"""

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class RefactorConfig:
    """重构配置"""
    ast_enabled: bool = True
    ast_strategies: List[str] = field(default_factory=lambda: [
        'organize_imports', 'optimize_loops', 'remove_unused', 'extract_function'
    ])
    semantic_enabled: bool = True
    llm_backend: str = "mock"           # mock / bailian / openai / local
    llm_model: str = "qwen-coder-plus"
    daily_budget: int = 100000          # tokens
    semantic_strategies: List[str] = field(default_factory=lambda: [
        'function_split', 'code_simplify', 'error_handling', 'api_modernize'
    ])
    cross_file_enabled: bool = True
    max_files_per_batch: int = 10


@dataclass
class SafetyConfig:
    """安全配置"""
    validation_layers: List[str] = field(default_factory=lambda: [
        'syntax', 'structure', 'safety', 'imports'
    ])
    auto_rollback: bool = True
    require_tests: bool = False
    forbidden_patterns: List[str] = field(default_factory=lambda: [
        'eval(', 'exec(', '__import__(', 'subprocess.', 'os.system('
    ])


@dataclass
class MonitorConfig:
    """监控配置"""
    enabled: bool = True
    log_level: str = "INFO"
    metrics_export: str = ""            # prometheus / json / none
    report_path: str = ".moss/reports"


@dataclass
class MOSSConfig:
    """MOSS 完整配置"""
    project_name: str = "unnamed"
    codebase_path: str = "."
    exclude_patterns: List[str] = field(default_factory=lambda: [
        "**/test_*", "**/node_modules/**", "**/__pycache__/**"
    ])
    refactor: RefactorConfig = field(default_factory=RefactorConfig)
    safety: SafetyConfig = field(default_factory=SafetyConfig)
    monitor: MonitorConfig = field(default_factory=MonitorConfig)


class ConfigManager:
    """配置管理器"""

    DEFAULT_CONFIG_FILENAME = "moss_config.yaml"

    def __init__(self):
        self.config: Optional[MOSSConfig] = None

    def load_config(self, path: Optional[str] = None) -> MOSSConfig:
        """加载配置文件"""
        if path is None:
            path = self._find_config_file()

        if path and Path(path).exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            self.config = self._dict_to_config(data)
        else:
            self.config = MOSSConfig()

        # 环境变量覆盖
        self._apply_env_overrides()

        return self.config

    def save_config(self, config: MOSSConfig, path: Optional[str] = None) -> str:
        """保存配置文件"""
        if path is None:
            path = self.DEFAULT_CONFIG_FILENAME

        data = self._config_to_dict(config)

        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

        return path

    def create_default_config(self, project_path: str = ".") -> str:
        """创建默认配置文件"""
        config = MOSSConfig(
            project_name=Path(project_path).resolve().name,
            codebase_path=project_path
        )
        return self.save_config(config)

    def validate_config(self, config: MOSSConfig) -> List[str]:
        """验证配置"""
        errors = []

        if not Path(config.codebase_path).exists():
            errors.append(f"代码库路径不存在: {config.codebase_path}")

        valid_backends = ['mock', 'bailian', 'openai', 'local', 'anthropic', 'ark']
        if config.refactor.llm_backend not in valid_backends:
            errors.append(f"无效的LLM后端: {config.refactor.llm_backend}")

        valid_strategies = [
            'organize_imports', 'optimize_loops', 'remove_unused', 'extract_function',
            'function_split', 'code_simplify', 'error_handling', 'api_modernize',
            'type_annotation', 'pattern_refactor', 'algorithm_optimize'
        ]
        for s in config.refactor.ast_strategies + config.refactor.semantic_strategies:
            if s not in valid_strategies:
                errors.append(f"未知的重构策略: {s}")

        if config.refactor.daily_budget < 0:
            errors.append("日预算不能为负数")

        return errors

    def _find_config_file(self) -> Optional[str]:
        """查找配置文件"""
        candidates = [
            self.DEFAULT_CONFIG_FILENAME,
            ".moss/config.yaml",
            "moss.yaml",
        ]

        for candidate in candidates:
            if Path(candidate).exists():
                return candidate

        return None

    def _apply_env_overrides(self):
        """应用环境变量覆盖"""
        if not self.config:
            return

        env_map = {
            'MOSS_LLM_BACKEND': ('refactor', 'llm_backend'),
            'MOSS_LLM_MODEL': ('refactor', 'llm_model'),
            'MOSS_DAILY_BUDGET': ('refactor', 'daily_budget'),
            'MOSS_LOG_LEVEL': ('monitor', 'log_level'),
            'DASHSCOPE_API_KEY': None,  # 仅环境变量，不存配置
        }

        for env_key, path in env_map.items():
            value = os.environ.get(env_key)
            if value and path:
                section, key = path
                section_obj = getattr(self.config, section)
                if key == 'daily_budget':
                    value = int(value)
                setattr(section_obj, key, value)

    def _dict_to_config(self, data: Dict) -> MOSSConfig:
        """字典转配置对象"""
        refactor_data = data.get('refactor', {})
        safety_data = data.get('safety', {})
        monitor_data = data.get('monitor', {})

        _default_ast = ['organize_imports', 'optimize_loops', 'remove_unused', 'extract_function']
        _default_semantic = ['function_split', 'code_simplify', 'error_handling', 'api_modernize']
        _default_validation = ['syntax', 'structure', 'safety', 'imports']
        _default_forbidden = ['eval(', 'exec(', '__import__(', 'subprocess.', 'os.system(']

        return MOSSConfig(
            project_name=data.get('project_name', 'unnamed'),
            codebase_path=data.get('codebase_path', '.'),
            exclude_patterns=data.get('exclude_patterns', []),
            refactor=RefactorConfig(
                ast_enabled=refactor_data.get('ast_enabled', True),
                ast_strategies=refactor_data.get('ast_strategies', _default_ast),
                semantic_enabled=refactor_data.get('semantic_enabled', True),
                llm_backend=refactor_data.get('llm_backend', 'mock'),
                llm_model=refactor_data.get('llm_model', 'qwen-coder-plus'),
                daily_budget=refactor_data.get('daily_budget', 100000),
                semantic_strategies=refactor_data.get('semantic_strategies', _default_semantic),
                cross_file_enabled=refactor_data.get('cross_file_enabled', True),
                max_files_per_batch=refactor_data.get('max_files_per_batch', 10),
            ),
            safety=SafetyConfig(
                validation_layers=safety_data.get('validation_layers', _default_validation),
                auto_rollback=safety_data.get('auto_rollback', True),
                require_tests=safety_data.get('require_tests', False),
                forbidden_patterns=safety_data.get('forbidden_patterns', _default_forbidden),
            ),
            monitor=MonitorConfig(
                enabled=monitor_data.get('enabled', True),
                log_level=monitor_data.get('log_level', 'INFO'),
                metrics_export=monitor_data.get('metrics_export', ''),
                report_path=monitor_data.get('report_path', '.moss/reports'),
            ),
        )

    def _config_to_dict(self, config: MOSSConfig) -> Dict:
        """配置对象转字典"""
        return {
            'project_name': config.project_name,
            'codebase_path': config.codebase_path,
            'exclude_patterns': config.exclude_patterns,
            'refactor': {
                'ast_enabled': config.refactor.ast_enabled,
                'ast_strategies': config.refactor.ast_strategies,
                'semantic_enabled': config.refactor.semantic_enabled,
                'llm_backend': config.refactor.llm_backend,
                'llm_model': config.refactor.llm_model,
                'daily_budget': config.refactor.daily_budget,
                'semantic_strategies': config.refactor.semantic_strategies,
                'cross_file_enabled': config.refactor.cross_file_enabled,
                'max_files_per_batch': config.refactor.max_files_per_batch,
            },
            'safety': {
                'validation_layers': config.safety.validation_layers,
                'auto_rollback': config.safety.auto_rollback,
                'require_tests': config.safety.require_tests,
                'forbidden_patterns': config.safety.forbidden_patterns,
            },
            'monitor': {
                'enabled': config.monitor.enabled,
                'log_level': config.monitor.log_level,
                'metrics_export': config.monitor.metrics_export,
                'report_path': config.monitor.report_path,
            },
        }


# 测试
if __name__ == "__main__":
    print("=" * 60)
    print("MOSS v9.2 - Configuration Manager 测试")
    print("=" * 60)

    mgr = ConfigManager()

    # 1. 创建默认配置
    print("\n[1] 创建默认配置...")
    config = MOSSConfig(project_name="moss-test", codebase_path="/workspace/moss")
    path = mgr.save_config(config, "/tmp/moss_test_config.yaml")
    print(f"   ✅ 配置已保存: {path}")

    # 2. 加载配置
    print("\n[2] 加载配置...")
    loaded = mgr.load_config("/tmp/moss_test_config.yaml")
    print(f"   ✅ 项目名: {loaded.project_name}")
    print(f"   ✅ AST策略: {loaded.refactor.ast_strategies}")
    print(f"   ✅ LLM后端: {loaded.refactor.llm_backend}")
    print(f"   ✅ 安全验证: {loaded.safety.validation_layers}")

    # 3. 验证配置
    print("\n[3] 验证配置...")
    errors = mgr.validate_config(loaded)
    if errors:
        for e in errors:
            print(f"   ❌ {e}")
    else:
        print(f"   ✅ 配置验证通过")

    # 4. 显示完整配置
    print("\n[4] 完整配置 (YAML):")
    with open(path, 'r') as f:
        for line in f:
            print(f"   {line.rstrip()}")

    print("\n测试完成!")
