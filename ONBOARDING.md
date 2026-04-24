# MOSS Onboarding Guide

快速上手指南，帮助新开发者接手 MOSS v9.5.0 项目。

## 项目概述

**MOSS** (Multi-Objective Self-Driven System) 是一个智能代码重构和分析系统，融合了：
- 9维自主 Agent 架构 (D1-D9)
- 代码重构引擎 (跨文件重构、语义重构)
- 机器学习推荐系统
- 自主学习和实验框架

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/luokaishi/moss.git
cd moss
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 验证安装

```bash
# 运行测试
python -m pytest tests/ --ignore=tests/legacy -q

# 验证 CLI
python -m moss.cli_main --version
```

### 4. 快速体验

```bash
# 分析当前目录
python -m moss.cli_main analyze . --format text

# 运行自主 Agent
python -m moss.cli_main agent --task system_monitor

# 监控文件变更
python -m moss.cli_main watch . --pattern "*.py"
```

## 项目结构

```
moss/
├── moss/                       # 主包
│   ├── core/                   # 核心模块 (47个文件)
│   │   ├── autonomous_loop.py  # v9.5 自主循环
│   │   ├── agent_bridge.py     # v9.5 Agent桥接
│   │   ├── unified_agent.py    # 9维Agent核心
│   │   ├── plugin_system.py    # v9.4 插件系统
│   │   ├── llm_cost_controller.py  # v9.4 成本控制器
│   │   ├── statistical_validator.py # v9.4 统计验证
│   │   ├── file_watcher.py     # v9.4 文件监控
│   │   └── ...                 # 其他核心模块
│   ├── plugins/                # 插件目录
│   │   ├── __init__.py
│   │   └── task_agent_plugin.py
│   ├── cli_main.py             # CLI入口
│   └── __init__.py
├── tests/                      # 测试套件 (314个测试)
│   ├── test_v95_*.py           # v9.5测试
│   ├── test_v94_*.py           # v9.4测试
│   └── ...
├── docs-site/                  # 文档站点
│   ├── docs/
│   │   ├── features/
│   │   │   ├── autonomous-agent.md
│   │   │   └── extensibility.md
│   │   └── ...
│   └── mkdocs.yml
├── README.md                   # 项目说明
├── CHANGELOG.md                # 版本历史
├── requirements.txt            # 依赖列表
├── setup.py                    # 安装脚本
└── pyproject.toml              # 项目配置
```

## 核心概念

### 9维架构 (D1-D9)

| 维度 | 名称 | 功能 |
|------|------|------|
| D1 | Survival | 生存目标 |
| D2 | Curiosity | 好奇心 |
| D3 | Influence | 影响力 |
| D4 | Optimization | 优化 |
| D5 | Coherence | 一致性 |
| D6 | Valence | 情感效价 |
| D7 | Other | 他者建模 |
| D8 | Norm | 规范内化 |
| D9 | Purpose | 目的生成 |

### 关键模块

#### v9.5 自主循环
```python
from moss.core.autonomous_loop import (
    CodeEnvironment, LinearPolicy, LearningLoop
)

env = CodeEnvironment("./src")
policy = LinearPolicy()
loop = LearningLoop(env, policy)
summary = loop.run()
```

#### v9.5 Agent桥接
```python
from moss.core.agent_bridge import IntegratedMOSSSystem

system = IntegratedMOSSSystem("./src")
summary = system.run()
```

#### v9.4 插件系统
```python
from moss.core.plugin_system import MossPlugin, PluginManager

class MyPlugin(MossPlugin):
    @property
    def name(self): return "my_plugin"

manager = PluginManager()
manager.register(MyPlugin())
```

## 开发工作流

### 运行测试

```bash
# 全部测试
python -m pytest tests/ --ignore=tests/legacy

# 特定版本测试
python -m pytest tests/test_v95_*.py -v

# 覆盖率
python -m pytest tests/ --cov=moss --cov-report=html
```

### 代码质量

```bash
# 格式化
black moss/ tests/

# 类型检查
mypy moss/

# 代码风格
flake8 moss/
```

### 构建文档

```bash
cd docs-site
mkdocs serve    # 本地预览
mkdocs build    # 构建
mkdocs gh-deploy # 部署到GitHub Pages
```

## 关键文件说明

| 文件 | 作用 |
|------|------|
| `moss/core/autonomous_loop.py` | v9.5核心：Environment、Policy、LearningLoop |
| `moss/core/agent_bridge.py` | v9.5桥接：UnifiedAgentEnvironment/Policy |
| `moss/core/unified_agent.py` | 9维Agent核心 |
| `moss/core/plugin_system.py` | v9.4插件系统 |
| `moss/core/llm_cost_controller.py` | v9.4LLM成本控制器 |
| `moss/core/statistical_validator.py` | v9.4统计验证 |
| `moss/core/file_watcher.py` | v9.4文件监控 |
| `moss/cli_main.py` | CLI入口 |

## 版本历史

- **v9.5.0** (2026-04-24): 自主循环、Agent桥接、9维决策
- **v9.4.0** (2026-04-24): 插件系统、Task Agent、成本控制器、统计验证、文件监控
- **v9.3.0** (2026-04-24): 性能引擎、增量分析、ML推荐
- **v9.2.0** (2026-04-20): 跨文件重构
- **v9.1.0** (2026-04-18): 语义重构
- **v9.0.0** (2026-04-15): 9维Agent架构

详见 [CHANGELOG.md](CHANGELOG.md)

## 常见问题

### Q: 导入错误？
A: 确保使用完整包路径，如 `from moss.core.xxx import ...`

### Q: 测试失败？
A: 检查是否安装了所有依赖：`pip install -r requirements.txt`

### Q: CLI命令找不到？
A: 使用 `python -m moss.cli_main` 运行

## 资源链接

- **GitHub**: https://github.com/luokaishi/moss
- **文档**: https://moss-devtools.github.io/moss
- **Issues**: https://github.com/luokaishi/moss/issues
- **Releases**: https://github.com/luokaishi/moss/releases

## 联系方式

- 项目维护者: MOSS Team
- 邮箱: support@moss-devtools.com

---

**当前版本**: v9.5.0
**测试状态**: 314/314 通过
**最后更新**: 2026-04-24
