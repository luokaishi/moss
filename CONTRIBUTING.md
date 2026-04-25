# Contributing to MOSS

感谢你对 MOSS 项目的关注！以下是贡献指南。

## 快速开始

```bash
# 1. Fork 并克隆
git clone https://github.com/YOUR_USERNAME/moss.git
cd moss

# 2. 安装开发依赖
pip install -e ".[dev]"

# 3. 运行测试
python3 tests/integration/test_cli_simple.py
```

## 贡献方式

### 🐛 报告 Bug

在 [Issues](https://github.com/luokaishi/moss/issues) 页面创建 issue，包含：

- MOSS 版本 (`moss --version`)
- Python 版本 (`python --version`)
- 重现步骤
- 预期行为 vs 实际行为

### ✨ 提交功能

1. 创建分支: `git checkout -b feature/your-feature`
2. 编写代码 + 测试
3. 确保测试通过: `python3 tests/integration/test_cli_simple.py`
4. 提交 PR

### 📝 改进文档

文档在 `docs/` 目录下，Markdown 格式，直接提交 PR 即可。

## Good First Issues

以下任务适合新贡献者：

| 标签 | 任务 | 难度 |
|------|------|------|
| `good-first-issue` | 添加 JavaScript 语言解析器 | 中 |
| `good-first-issue` | 修复遗留测试文件旧导入 | 低 |
| `good-first-issue` | 添加更多集成测试 | 低 |
| `good-first-issue` | 完善 PythonParser 复杂度计算 | 中 |
| `good-first-issue` | 添加 PythonAnalyzer 实现 | 中 |

## 代码规范

- Python 3.9+ 兼容
- 遵循 PEP 8（line-length: 100）
- 新模块必须有 docstring
- 公开 API 必须添加类型注解

## 提交规范

```
feat: 添加新功能
fix: 修复 bug
docs: 文档更新
test: 测试相关
refactor: 重构
chore: 构建/工具变更
```

## 架构概览

```
moss/
├── core/           # 核心模块
│   ├── language/   # 语言抽象层 (新)
│   ├── meta_*/     # 元学习/认知
│   └── ...         # 其他组件
├── plugins/        # 插件系统
├── cli_main.py     # CLI 入口
└── tests/
    └── integration/ # 集成测试
```

## 许可证

贡献的代码遵循 MIT 许可证。
