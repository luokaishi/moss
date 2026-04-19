"""
MOSS v8.0 - LLM Backend Abstraction Layer
==========================================

统一LLM调用接口，支持5种后端：
- OpenAI (GPT-4o / GPT-4o-mini)
- Anthropic (Claude)
- ARK (火山引擎)
- Local (Ollama / vLLM)
- Mock (测试/CI)

特性：
- 日 token/请求预算自动降级
- 指数退避重试 + jitter
- 使用统计追踪

Author: MOSS v8.0 Auto-Build
Version: 8.0.0-dev
"""

import ast
import hashlib
import json
import logging
import os
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────

@dataclass
class LLMConfig:
    """LLM后端配置"""
    provider: str = "mock"                # openai | anthropic | ark | local | mock
    model: str = ""                       # e.g. gpt-4o, claude-sonnet-4-20250514
    api_key_env: str = ""                 # 环境变量名（留空自动推断）
    base_url: str = ""                    # 自定义API端点
    max_tokens: int = 2048                # 单次最大输出token
    temperature: float = 0.3              # 生成温度（低=确定性，高=创意）
    timeout: int = 60                     # 请求超时（秒）
    max_retries: int = 3                  # 重试次数
    retry_delay: float = 2.0              # 基础重试延迟（秒，指数退避）
    # 预算控制
    daily_token_budget: int = 100000      # 每日token预算
    daily_request_budget: int = 200       # 每日请求预算
    cost_per_1k_input: float = 0.0        # USD / 1K input tokens
    cost_per_1k_output: float = 0.0       # USD / 1K output tokens

    def __post_init__(self):
        # 自动推断 api_key_env
        if not self.api_key_env:
            env_map = {
                "openai": "OPENAI_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
                "ark": "ARK_API_KEY",
                "bailian": "DASHSCOPE_API_KEY",
            }
            self.api_key_env = env_map.get(self.provider, "")
        # 自动推断 model
        if not self.model:
            model_map = {
                "openai": "gpt-4o-mini",
                "anthropic": "claude-sonnet-4-20250514",
                "ark": "doubao-pro-32k",
                "bailian": "qwen-coder-plus",  # 代码生成模型
                "local": "llama3",
                "mock": "mock-v1",
            }
            self.model = model_map.get(self.provider, "unknown")


@dataclass
class LLMResponse:
    """LLM响应"""
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    cost_usd: float
    provider: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class _UsageTracker:
    """日使用量追踪"""
    date: str = field(default_factory=lambda: date.today().isoformat())
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_requests: int = 0
    total_cost_usd: float = 0.0

    def reset_if_new_day(self):
        today = date.today().isoformat()
        if self.date != today:
            self.date = today
            self.total_input_tokens = 0
            self.total_output_tokens = 0
            self.total_requests = 0
            self.total_cost_usd = 0.0


# ─────────────────────────────────────────────
# LLMBackend 抽象基类
# ─────────────────────────────────────────────

class LLMBackend(ABC):
    """LLM后端抽象接口"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self._usage = _UsageTracker()
        self._request_history: List[Dict] = []

    @abstractmethod
    def _call_api(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """子类实现：实际API调用"""
        ...

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """
        发送聊天完成请求（带预算检查、重试、使用量追踪）

        Args:
            system_prompt: 系统提示
            user_prompt: 用户提示

        Returns:
            LLMResponse

        Raises:
            RuntimeError: 预算耗尽或所有重试失败
        """
        # 日预算检查
        self._usage.reset_if_new_day()
        if not self.check_budget():
            raise RuntimeError(
                f"LLM daily budget exhausted: "
                f"tokens={self._usage.total_input_tokens + self._usage.total_output_tokens}/{self.config.daily_token_budget}, "
                f"requests={self._usage.total_requests}/{self.config.daily_request_budget}"
            )

        # 重试循环
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                t0 = time.time()
                response = self._call_api(system_prompt, user_prompt)
                latency = (time.time() - t0) * 1000
                response.latency_ms = latency

                # 更新使用量
                self._usage.total_input_tokens += response.input_tokens
                self._usage.total_output_tokens += response.output_tokens
                self._usage.total_requests += 1
                self._usage.total_cost_usd += response.cost_usd

                # 记录历史
                self._request_history.append({
                    'timestamp': response.timestamp,
                    'provider': response.provider,
                    'model': response.model,
                    'input_tokens': response.input_tokens,
                    'output_tokens': response.output_tokens,
                    'cost_usd': response.cost_usd,
                    'latency_ms': latency,
                })

                return response

            except RuntimeError:
                raise  # 预算错误不重试
            except Exception as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    # 指数退避 + jitter
                    delay = self.config.retry_delay * (2 ** attempt)
                    jitter = random.uniform(0, delay * 0.5)
                    time.sleep(delay + jitter)
                    logger.debug(
                        f"[LLMBackend] Retry {attempt + 1}/{self.config.max_retries} "
                        f"after {delay + jitter:.1f}s: {e}"
                    )

        raise RuntimeError(
            f"LLM request failed after {self.config.max_retries} retries: {last_error}"
        )

    def check_budget(self) -> bool:
        """检查日预算是否充足"""
        self._usage.reset_if_new_day()
        tokens_ok = (self._usage.total_input_tokens + self._usage.total_output_tokens
                     < self.config.daily_token_budget)
        requests_ok = self._usage.total_requests < self.config.daily_request_budget
        return tokens_ok and requests_ok

    def get_usage_stats(self) -> Dict:
        """获取使用统计"""
        self._usage.reset_if_new_day()
        return {
            'provider': self.config.provider,
            'model': self.config.model,
            'date': self._usage.date,
            'total_input_tokens': self._usage.total_input_tokens,
            'total_output_tokens': self._usage.total_output_tokens,
            'total_requests': self._usage.total_requests,
            'total_cost_usd': round(self._usage.total_cost_usd, 4),
            'budget_remaining_tokens': max(0, self.config.daily_token_budget -
                                           self._usage.total_input_tokens -
                                           self._usage.total_output_tokens),
            'budget_remaining_requests': max(0, self.config.daily_request_budget -
                                             self._usage.total_requests),
        }


# ─────────────────────────────────────────────
# Mock Backend（测试/CI用）
# ─────────────────────────────────────────────

class MockBackend(LLMBackend):
    """
    模拟LLM后端（确定性，基于输入hash）

    用于CI测试和开发调试，不调用任何真实API。
    生成策略：对输入做微小数值扰动（模拟参数级变异）。
    """

    def __init__(self, config: LLMConfig = None):
        super().__init__(config or LLMConfig(provider="mock", model="mock-v1"))

    def _call_api(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """基于输入hash生成确定性模拟变异

        使用AST操作替代正则替换，避免在字符串字面量内误替换。
        """
        # 从用户提示中提取源码
        source_code = user_prompt
        marker = "=== CURRENT SOURCE CODE ==="
        if marker in user_prompt:
            parts = user_prompt.split(marker)
            if len(parts) >= 2:
                after_marker = parts[1]
                # 按行查找下一个 === 标记行（行首的 ===，非字符串内的 ===）
                lines = after_marker.split('\n')
                end_line = len(lines)
                for i, line in enumerate(lines):
                    if i > 0 and line.strip().startswith('===') and 'FUNCTIONS' in line.upper():
                        end_line = i
                        break
                source_code = '\n'.join(lines[:end_line]).strip()

        # 使用AST做安全的常量微调
        mutated = self._mock_mutate_source(source_code, system_prompt + user_prompt)

        input_tokens = len(user_prompt) // 4
        output_tokens = len(mutated) // 4

        return LLMResponse(
            content=mutated,
            model="mock-v1",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=0.0,
            cost_usd=0.0,
            provider="mock",
        )

    def _mock_mutate_source(self, source: str, seed_str: str) -> str:
        """用AST安全地微调数值常量"""
        hash_val = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)

        # 34%概率返回no_op
        if hash_val % 3 == 0:
            info = {
                "strategy": "no_op",
                "target_function": "",
                "description": "Mock: no mutation applied",
                "confidence": 0.0,
            }
            return source + f'\n# MUTATION_INFO: {json.dumps(info)}'

        try:
            tree = ast.parse(source)
        except SyntaxError:
            return source  # 解析失败则原样返回

        # 收集所有数值常量节点
        constants = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                # 跳过0、1、-1和过大/过小的数
                if abs(node.value) > 0.001 and abs(node.value) < 1000 and node.value not in (0, 1, -1):
                    constants.append(node)

        if not constants:
            return source

        # 选择一个常量微调
        target = constants[hash_val % len(constants)]
        old_val = target.value
        factor = 1.0 + ((hash_val % 100 - 50) / 500.0)  # ±10%
        new_val = round(old_val * factor, 4)

        # 保持类型一致
        if isinstance(old_val, int) and abs(new_val - round(new_val)) < 0.01:
            new_val = int(round(new_val))
        target.value = new_val

        ast.fix_missing_locations(tree)

        try:
            mutated_source = ast.unparse(tree)
        except Exception:
            return source

        info = {
            "strategy": "parameter_tune",
            "target_function": "_apply_state_weights",
            "description": f"Mock: adjusted constant {old_val} -> {new_val} (factor={factor:.3f})",
            "confidence": 0.5,
        }
        mutated_source += f'\n# MUTATION_INFO: {json.dumps(info)}'
        return mutated_source


# ─────────────────────────────────────────────
# OpenAI Backend
# ─────────────────────────────────────────────

class OpenAIBackend(LLMBackend):
    """OpenAI API后端（GPT-4o / GPT-4o-mini）"""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        api_key = os.getenv(self.config.api_key_env, "")
        if not api_key:
            raise ValueError(
                f"OpenAI API key not found. Set {self.config.api_key_env} environment variable."
            )
        self._api_key = api_key
        self._client = None  # 延迟初始化

    def _get_client(self):
        """延迟初始化 OpenAI 客户端"""
        if self._client is None:
            try:
                from openai import OpenAI
                kwargs = {"api_key": self._api_key}
                if self.config.base_url:
                    kwargs["base_url"] = self.config.base_url
                self._client = OpenAI(**kwargs)
            except ImportError:
                raise ImportError(
                    "openai package not installed. Run: pip install openai"
                )
        return self._client

    def _call_api(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        client = self._get_client()
        response = client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            timeout=self.config.timeout,
        )

        content = response.choices[0].message.content or ""
        usage = response.usage

        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        cost = (input_tokens / 1000 * self.config.cost_per_1k_input +
                output_tokens / 1000 * self.config.cost_per_1k_output)

        return LLMResponse(
            content=content,
            model=self.config.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=0.0,  # 由 complete() 填充
            cost_usd=cost,
            provider="openai",
        )


# ─────────────────────────────────────────────
# Anthropic Backend
# ─────────────────────────────────────────────

class AnthropicBackend(LLMBackend):
    """Anthropic Claude API后端"""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        api_key = os.getenv(self.config.api_key_env, "")
        if not api_key:
            raise ValueError(
                f"Anthropic API key not found. Set {self.config.api_key_env} environment variable."
            )
        self._api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self._api_key)
            except ImportError:
                raise ImportError(
                    "anthropic package not installed. Run: pip install anthropic"
                )
        return self._client

    def _call_api(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        client = self._get_client()
        response = client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt},
            ],
            timeout=self.config.timeout,
        )

        content = response.content[0].text if response.content else ""
        input_tokens = response.usage.input_tokens if response.usage else 0
        output_tokens = response.usage.output_tokens if response.usage else 0
        cost = (input_tokens / 1000 * self.config.cost_per_1k_input +
                output_tokens / 1000 * self.config.cost_per_1k_output)

        return LLMResponse(
            content=content,
            model=self.config.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=0.0,
            cost_usd=cost,
            provider="anthropic",
        )


# ─────────────────────────────────────────────
# Local Backend (Ollama / vLLM)
# ─────────────────────────────────────────────

class LocalBackend(LLMBackend):
    """本地LLM后端（Ollama兼容）"""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._base_url = config.base_url or "http://localhost:11434"

    def _call_api(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        import requests as http_requests

        url = f"{self._base_url}/api/chat"
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            },
        }

        resp = http_requests.post(
            url, json=payload, timeout=self.config.timeout
        )
        resp.raise_for_status()
        data = resp.json()

        content = data.get("message", {}).get("content", "")
        # Ollama 不总是返回 token 统计
        eval_count = data.get("eval_count", len(content) // 4)
        prompt_eval_count = data.get("prompt_eval_count", len(user_prompt) // 4)

        return LLMResponse(
            content=content,
            model=self.config.model,
            input_tokens=prompt_eval_count,
            output_tokens=eval_count,
            latency_ms=0.0,
            cost_usd=0.0,  # 本地推理无成本
            provider="local",
        )


# ─────────────────────────────────────────────
# ARK Backend (火山引擎)
# ─────────────────────────────────────────────

class ARKBackend(LLMBackend):
    """火山引擎 ARK 后端（占位实现）"""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        api_key = os.getenv(self.config.api_key_env, "")
        if not api_key:
            raise ValueError(
                f"ARK API key not found. Set {self.config.api_key_env} environment variable."
            )

    def _call_api(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        # ARK SDK 暂未安装，降级到 OpenAI 兼容接口
        logger.warning("[ARKBackend] ARK SDK not available, falling back to OpenAI-compatible API")
        fallback_config = LLMConfig(
            provider="openai",
            model=self.config.model or "doubao-pro-32k",
            base_url=self.config.base_url or "https://ark.cn-beijing.volces.com/api/v3",
            api_key_env=self.config.api_key_env,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )
        return OpenAIBackend(fallback_config)._call_api(system_prompt, user_prompt)


# ─────────────────────────────────────────────
# Bailian Backend (阿里云百炼 / DashScope)
# ─────────────────────────────────────────────

class BailianBackend(LLMBackend):
    """
    阿里云百炼 (DashScope) 后端

    支持模型:
    - qwen-max (最强性能)
    - qwen-plus (平衡)
    - qwen-turbo (快速)
    - qwen-coder-plus (代码生成)
    - qwen-long (长文本)

    环境变量: DASHSCOPE_API_KEY (从 https://dashscope.aliyun.com 获取)

    国内访问稳定，适合 MOSS 在国内部署场景。
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        api_key = os.getenv(self.config.api_key_env, "")
        if not api_key:
            raise ValueError(
                f"DashScope API key not found. Set {self.config.api_key_env} environment variable. "
                f"Get your key from: https://dashscope.aliyun.com"
            )
        self._api_key = api_key
        # 百炼兼容 OpenAI 接口
        self._base_url = config.base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def _get_client(self):
        """延迟初始化 OpenAI 客户端（百炼兼容模式）"""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self._api_key,
                    base_url=self._base_url,
                )
            except ImportError:
                raise ImportError(
                    "openai package not installed. Run: pip install openai"
                )
        return self._client

    def _call_api(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        client = self._get_client()
        response = client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            timeout=self.config.timeout,
        )

        content = response.choices[0].message.content or ""
        usage = response.usage

        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        # 百炼价格参考（以 qwen-plus 为例，实际请以官网为准）
        # 输入: ¥0.004/1K tokens, 输出: ¥0.012/1K tokens
        # 转换为 USD (约 7.2 汇率)
        cost = (input_tokens / 1000 * 0.004 +
                output_tokens / 1000 * 0.012) / 7.2

        return LLMResponse(
            content=content,
            model=self.config.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=0.0,
            cost_usd=cost,
            provider="bailian",
        )


# ─────────────────────────────────────────────
# 工厂函数
# ─────────────────────────────────────────────

def create_llm_backend(config: LLMConfig) -> LLMBackend:
    """
    根据配置创建LLM后端实例

    Args:
        config: LLM配置

    Returns:
        LLMBackend 实例

    Raises:
        ValueError: 不支持的 provider
    """
    backends = {
        "mock": MockBackend,
        "openai": OpenAIBackend,
        "anthropic": AnthropicBackend,
        "local": LocalBackend,
        "ark": ARKBackend,
        "bailian": BailianBackend,
    }

    provider = config.provider.lower()
    if provider not in backends:
        raise ValueError(
            f"Unknown LLM provider: {provider}. "
            f"Supported: {list(backends.keys())}"
        )

    backend_cls = backends[provider]
    logger.info(f"[LLMBackend] Creating {provider} backend (model={config.model})")
    return backend_cls(config)
