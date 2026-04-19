# 阿里百炼 (DashScope) 配置指南

MOSS v8.0 现已支持阿里云百炼平台的代码生成模型，国内访问稳定。

## 支持的模型

| 模型名 | 说明 | 适用场景 |
|--------|------|----------|
| `qwen-coder-plus` | 代码生成专用 (推荐) | 代码变异、逻辑优化 |
| `qwen-max` | 最强性能 | 复杂推理 |
| `qwen-plus` | 平衡型 | 通用任务 |
| `qwen-turbo` | 快速响应 | 简单任务 |

## 配置步骤

### 1. 获取 API Key

1. 访问 [阿里云百炼控制台](https://dashscope.aliyun.com)
2. 注册/登录阿里云账号
3. 创建 API Key（格式：`sk-xxxx`）
4. 领取免费额度（新用户有赠送）

### 2. 配置环境变量

```bash
export DASHSCOPE_API_KEY="sk-your-api-key-here"
```

或添加到 `~/.bashrc` / `~/.zshrc`：

```bash
echo 'export DASHSCOPE_API_KEY="sk-your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### 3. 使用百炼运行 MOSS

```python
from moss.core.self_modification_engine import SelfModificationEngine, SMEConfig

config = SMEConfig(
    enable_llm_mutation=True,
    llm_provider='bailian',           # 使用阿里百炼
    llm_model='qwen-coder-plus',      # 代码生成模型
    llm_max_tokens=2048,
    llm_temperature=0.3,
    llm_mutation_strategy='adaptive', # 自适应 AST+LLM
    enable_hot_reload=False,
)

sme = SelfModificationEngine(config=config)
report = sme.run(max_generations=10)
```

## 成本估算

以 `qwen-coder-plus` 为例（价格可能有变动，请以官网为准）：

| 项目 | 价格 |
|------|------|
| 输入 | ¥0.004 / 1K tokens |
| 输出 | ¥0.012 / 1K tokens |

**MOSS 一代估算**（population_size=6, max_tokens=2048）：
- 假设平均 1K input + 1K output per LLM 调用
- 假设 2 个 LLM 候选/代（adaptive 模式 30% 预算）
- 每代成本：2 × (¥0.004 + ¥0.012) = ¥0.032
- 30 代成本：约 ¥1.0

## 故障排查

### 错误：`DashScope API key not found`

```bash
# 检查环境变量是否设置
echo $DASHSCOPE_API_KEY

# 未设置则重新配置
export DASHSCOPE_API_KEY="sk-xxxx"
```

### 错误：`openai package not installed`

```bash
pip install openai
```

### 错误：网络连接超时

百炼国内访问通常稳定，如遇问题可尝试：

```python
# 增加超时时间
config = SMEConfig(
    # ...
    llm_timeout=120,  # 默认 60 秒
)
```

## 与其他提供商对比

| 特性 | 阿里百炼 | OpenAI | Anthropic |
|------|----------|--------|-----------|
| 国内访问 | ✅ 稳定 | ⚠️ 需代理 | ⚠️ 需代理 |
| 代码生成 | ✅ qwen-coder-plus | gpt-4o | claude-sonnet |
| 价格 | ¥较低 | $较高 | $较高 |
| 中文支持 | ✅ 原生 | 一般 | 一般 |

## 推荐配置

**国内部署首选**：
```python
SMEConfig(
    enable_llm_mutation=True,
    llm_provider='bailian',
    llm_model='qwen-coder-plus',
    llm_mutation_strategy='adaptive',
    llm_budget_fraction=0.3,      # 30% 预算给 LLM
    llm_daily_request_budget=200, # 每日最多 200 次 LLM 调用
)
```
