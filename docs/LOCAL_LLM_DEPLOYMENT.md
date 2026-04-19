# 本地大模型部署指南

在本地部署开源大模型，实现完全离线、零成本的 MOSS 进化。

## 优势

- ✅ **零 API 成本** - 一次性下载，永久使用
- ✅ **完全离线** - 无需网络，适合长期实验
- ✅ **数据隐私** - 代码不出本地
- ✅ **国内可用** - 无需代理， HuggingFace 镜像加速

## 支持的模型

| 模型 | 大小 | 磁盘 | 内存 | 速度 | 推荐度 |
|------|------|------|------|------|--------|
| **Qwen2.5-Coder-1.5B** | 1.5B | ~3GB | ~4GB | 快 | ⭐⭐⭐ 测试首选 |
| **Qwen2.5-Coder-7B** | 7B | ~15GB | ~16GB | 中 | ⭐⭐⭐⭐⭐ 生产推荐 |
| **DeepSeek-Coder-6.7B** | 6.7B | ~13GB | ~14GB | 中 | ⭐⭐⭐⭐ 代码能力强 |
| **CodeLlama-7B** | 7B | ~13GB | ~14GB | 中 | ⭐⭐⭐⭐ Meta 出品 |
| **Phi-4** | 14B | ~28GB | ~30GB | 慢 | ⭐⭐⭐ 质量高但慢 |

## 快速开始

### 1. 安装依赖

```bash
pip install transformers accelerate sentencepiece protobuf torch
```

### 2. 测试部署（1.5B 快速版）

```python
from moss.core.local_llm_backend import create_local_backend_for_moss
from moss.core.llm_mutator import LLMMutator

# 创建本地后端（首次自动下载 ~3GB）
backend = create_local_backend_for_moss("qwen2.5-coder-1.5b")
mutator = LLMMutator(backend)

# 测试变异
source = '''
def calculate_weights(x):
    return x * 0.5 + 0.1
'''

result, info = mutator.mutate(
    source=source,
    target_functions=['calculate_weights'],
)

print(f"Generated: {info.change_description}")
```

### 3. 生产部署（7B 完整版）

```python
from moss.core.self_modification_engine import SelfModificationEngine, SMEConfig

config = SMEConfig(
    enable_llm_mutation=True,
    llm_provider='local',  # 使用 LocalBackend
    llm_model='qwen2.5-coder-7b',  # 指定模型
    llm_mutation_strategy='adaptive',
    enable_hot_reload=False,
)

sme = SelfModificationEngine(config=config)
report = sme.run(max_generations=30)
```

## 硬件要求

### 最小配置（1.5B 模型）
- CPU: 4 核+
- 内存: 8GB+
- 磁盘: 10GB

### 推荐配置（7B 模型）
- CPU: 8 核+（支持 AVX2）
- 内存: 16GB+
- 磁盘: 50GB
- 当前环境（32核/123GB）完全满足 ✅

## 模型下载加速

国内用户建议设置镜像源：

```bash
# 使用 HuggingFace 镜像
export HF_ENDPOINT=https://hf-mirror.com

# 或在 Python 中设置
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
```

## 性能优化

### 1. 量化（节省 50-75% 内存）

```python
from moss.core.local_llm_backend import LocalLLMBackend, LocalModelConfig

config = LocalModelConfig(
    model_name="Qwen/Qwen2.5-Coder-7B-Instruct",
    load_in_8bit=True,  # 8-bit 量化
    # load_in_4bit=True,  # 4-bit 量化 (更省内存)
)
backend = LocalLLMBackend(config)
```

### 2. 多线程优化

```python
import torch
torch.set_num_threads(16)  # 使用 16 线程
```

### 3. 模型预热

首次加载模型较慢（需要下载），后续从缓存加载快很多。

```bash
# 预下载模型
python -c "from moss.core.local_llm_backend import LocalLLMBackend; 
LocalLLMBackend.from_preset('qwen2.5-coder-7b')._load_model()"
```

## 故障排查

### 下载速度慢

```bash
# 使用国内镜像
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_ENABLE_HF_TRANSFER=1
```

### 内存不足 (OOM)

```python
# 改用更小模型
backend = create_local_backend_for_moss("qwen2.5-coder-1.5b")

# 或启用 8-bit 量化
config = LocalModelConfig(load_in_8bit=True)
```

### 模型加载失败

```bash
# 清理缓存重新下载
rm -rf ~/.cache/huggingface/hub/
```

### 生成速度慢

- 正常现象：7B 模型在 CPU 上生成 2048 tokens 约需 30-120 秒
- 优化：减少 `max_tokens`，使用更小模型，或启用量化

## 与 API 方案对比

| 特性 | 本地部署 | OpenAI API | 阿里百炼 |
|------|----------|------------|----------|
| 成本 | 免费 | $$$ | ¥ |
| 网络依赖 | ❌ 无 | ✅ 需要 | ✅ 需要 |
| 速度 | 较慢 | 快 | 快 |
| 隐私 | ✅ 最好 | ⚠️ 上传代码 | ⚠️ 上传代码 |
| 国内可用 | ✅ 是 | ❌ 需代理 | ✅ 是 |
| 适合场景 | 长期实验 | 快速测试 | 生产部署 |

## 推荐工作流

1. **开发测试** → 使用 `qwen2.5-coder-1.5b`（快速）
2. **中期验证** → 使用 阿里百炼（平衡）
3. **长期进化** → 使用 `qwen2.5-coder-7b` 本地部署（零成本长期运行）

## 下一步

运行测试脚本验证部署：

```bash
cd /workspace/moss
python test_local_model.py
```

首次运行会下载 1.5B 模型（约 3GB，根据网络需 5-30 分钟）。
