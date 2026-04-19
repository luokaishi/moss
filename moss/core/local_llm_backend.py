"""
MOSS v8.0 - Local LLM Backend (HuggingFace Transformers)
=========================================================

本地部署开源大模型，无需 API Key，完全离线运行。

支持模型:
- Qwen2.5-Coder-7B-Instruct (推荐，代码生成专用)
- DeepSeek-Coder-6.7B-Instruct
- CodeLlama-7B-Instruct

硬件要求:
- 7B 模型: ~15GB 磁盘, ~16GB 内存, 8+ 核 CPU

Author: MOSS v8.0 Auto-Build
"""

import logging
import os
from dataclasses import dataclass
from typing import Dict, Optional

import torch

logger = logging.getLogger(__name__)


@dataclass
class LocalModelConfig:
    """本地模型配置"""
    model_name: str = "Qwen/Qwen2.5-Coder-7B-Instruct"  # HuggingFace 模型名
    device: str = "auto"  # auto | cpu | cuda
    max_length: int = 4096
    temperature: float = 0.3
    top_p: float = 0.9
    # 量化配置 (节省内存)
    load_in_8bit: bool = False  # 8-bit 量化 (需要 bitsandbytes)
    load_in_4bit: bool = False  # 4-bit 量化 (需要 bitsandbytes)
    # 推理优化
    use_cache: bool = True
    do_sample: bool = True


class LocalLLMBackend:
    """
    本地大模型后端 (HuggingFace Transformers)

    首次使用会自动下载模型到 ~/.cache/huggingface/
    """

    SUPPORTED_MODELS = {
        "qwen2.5-coder-7b": "Qwen/Qwen2.5-Coder-7B-Instruct",
        "qwen2.5-coder-1.5b": "Qwen/Qwen2.5-Coder-1.5B-Instruct",
        "deepseek-coder-6.7b": "deepseek-ai/deepseek-coder-6.7b-instruct",
        "codellama-7b": "codellama/CodeLlama-7b-Instruct-hf",
        "phi-4": "microsoft/Phi-4",
    }

    def __init__(self, config: LocalModelConfig = None):
        self.config = config or LocalModelConfig()
        self._model = None
        self._tokenizer = None
        self._is_loaded = False

    def _load_model(self):
        """延迟加载模型"""
        if self._is_loaded:
            return

        from transformers import AutoModelForCausalLM, AutoTokenizer

        model_name = self.config.model_name
        logger.info(f"[LocalLLM] Loading model: {model_name}")
        logger.info(f"[LocalLLM] This may take a few minutes on first run (downloading ~15GB)")

        # 设备选择
        if self.config.device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            device = self.config.device

        logger.info(f"[LocalLLM] Using device: {device}")

        # 加载配置
        load_kwargs = {
            "torch_dtype": torch.float16 if device == "cuda" else torch.float32,
            "device_map": "auto" if device == "cuda" else None,
            "trust_remote_code": True,
        }

        if self.config.load_in_8bit:
            load_kwargs["load_in_8bit"] = True
        if self.config.load_in_4bit:
            load_kwargs["load_in_4bit"] = True

        # 加载 tokenizer
        self._tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True,
            padding_side="left"
        )

        # 加载模型
        self._model = AutoModelForCausalLM.from_pretrained(
            model_name,
            **load_kwargs
        )

        if device == "cpu":
            self._model = self._model.to("cpu")

        self._is_loaded = True
        logger.info(f"[LocalLLM] Model loaded successfully")

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """
        生成代码变异

        Args:
            system_prompt: 系统提示
            user_prompt: 用户提示

        Returns:
            生成的代码
        """
        self._load_model()

        # 构建对话格式 (Qwen2.5 格式)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # 应用聊天模板
        text = self._tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        # 编码输入
        model_inputs = self._tokenizer([text], return_tensors="pt")
        if self._model.device.type != "cpu":
            model_inputs = model_inputs.to(self._model.device)

        # 生成
        logger.info(f"[LocalLLM] Generating (max_length={self.config.max_length})...")

        with torch.no_grad():
            generated_ids = self._model.generate(
                **model_inputs,
                max_new_tokens=self.config.max_length,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                do_sample=self.config.do_sample,
                use_cache=self.config.use_cache,
                pad_token_id=self._tokenizer.eos_token_id,
            )

        # 解码输出 (只取生成的新部分)
        generated_ids = [
            output_ids[len(input_ids):]
            for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]

        output = self._tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

        logger.info(f"[LocalLLM] Generated {len(output)} chars")
        return output

    def get_model_info(self) -> Dict:
        """获取模型信息"""
        return {
            "model_name": self.config.model_name,
            "loaded": self._is_loaded,
            "device": str(self._model.device) if self._model else "not loaded",
            "supports": list(self.SUPPORTED_MODELS.keys()),
        }

    @classmethod
    def from_preset(cls, preset_name: str) -> "LocalLLMBackend":
        """
        从预设创建后端

        Args:
            preset_name: qwen2.5-coder-7b | qwen2.5-coder-1.5b | deepseek-coder-6.7b | codellama-7b | phi-4
        """
        if preset_name not in cls.SUPPORTED_MODELS:
            raise ValueError(f"Unknown preset: {preset_name}. Supported: {list(cls.SUPPORTED_MODELS.keys())}")

        config = LocalModelConfig(model_name=cls.SUPPORTED_MODELS[preset_name])
        return cls(config)


# 兼容性：适配 LLMBackend 接口
def create_local_backend_for_moss(preset: str = "qwen2.5-coder-7b"):
    """
    创建适配 MOSS LLMBackend 接口的本地后端

    Usage:
        from moss.core.local_llm_backend import create_local_backend_for_moss
        from moss.core.llm_mutator import LLMMutator

        backend = create_local_backend_for_moss("qwen2.5-coder-7b")
        mutator = LLMMutator(backend)
    """
    from .llm_backend import LLMConfig

    class LocalBackendWrapper:
        """包装器，使 LocalLLMBackend 兼容 LLMBackend 接口"""

        def __init__(self, local_backend: LocalLLMBackend):
            self.local = local_backend
            self.config = LLMConfig(provider="local", model=preset)

        def complete(self, system_prompt: str, user_prompt: str):
            from .llm_backend import LLMResponse
            import time

            t0 = time.time()
            content = self.local.complete(system_prompt, user_prompt)
            latency = (time.time() - t0) * 1000

            # 估算 token 数
            input_tokens = len(user_prompt) // 4
            output_tokens = len(content) // 4

            return LLMResponse(
                content=content,
                model=preset,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency,
                cost_usd=0.0,  # 本地运行无成本
                provider="local",
            )

        def check_budget(self) -> bool:
            return True  # 本地运行无预算限制

        def get_usage_stats(self) -> Dict:
            return {
                "provider": "local",
                "model": preset,
                "loaded": self.local._is_loaded,
            }

    backend = LocalLLMBackend.from_preset(preset)
    return LocalBackendWrapper(backend)
