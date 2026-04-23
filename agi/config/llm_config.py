"""
MOSS mves - LLM 配置文件
基于 main 分支 v8.1.1 经验优化

日期：2026-04-22
"""

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class LLMConfig:
    """LLM 后端配置"""
    
    # ========== 后端选择 ==========
    provider: str = "bailian"           # bailian | openai | anthropic | local | mock
    model: str = "qwen3-coder-plus"     # 最强代码能力
    
    # ========== API 配置 ==========
    api_key_env: str = "DASHSCOPE_API_KEY"
    base_url: Optional[str] = None      # 留空使用默认
    max_tokens: int = 2048
    temperature: float = 0.3            # 低温度=确定性代码
    timeout: int = 60
    max_retries: int = 3
    
    # ========== Token 预算 (关键！) ==========
    # 基于 main 分支 V81 实验经验：
    # - 100K 仅支持 7 代
    # - 500K 支持完整 30 代
    llm_daily_token_budget: int = 500000      # 500K tokens/天
    llm_daily_request_budget: int = 500       # 请求次数
    llm_budget_fraction: float = 0.50         # 50% 预算用于 LLM
    
    # ========== 变异策略 ==========
    llm_mutation_rate: float = 0.50           # 50% 变异使用 LLM
    llm_pattern: List[str] = None             # scheduled 模式
    
    def __post_init__(self):
        if self.llm_pattern is None:
            # 默认：每 3 次变异中 1 次 LLM
            self.llm_pattern = ["ast", "ast", "llm"]
    
    # ========== v8.1 特性 ==========
    enable_elitism: bool = True               # 精英保留
    enable_adaptive_threshold: bool = True    # 动态阈值
    elite_protection_threshold: float = 0.95  # 精英阈值
    adaptive_threshold_start: float = -0.01   # 早期宽松
    adaptive_threshold_end: float = -0.005    # 晚期严格
    
    # ========== multi_eval ==========
    enable_multi_eval: bool = True            # 多轮评估
    multi_eval_rounds: int = 3                # 3 轮评估
    eval_seed_base: int = 42                  # 评估随机种子基准


# ========== 预设配置 ==========

# 高性能配置 (推荐)
LLM_CONFIG_HIGH_PERF = LLMConfig(
    model="qwen3-coder-plus",
    llm_mutation_rate=0.50,
    llm_daily_token_budget=500000,
    enable_elitism=True,
    enable_multi_eval=True,
)

# 经济配置 (快速测试)
LLM_CONFIG_ECONOMY = LLMConfig(
    model="qwen3-coder-plus",
    llm_mutation_rate=0.33,
    llm_daily_token_budget=200000,
    enable_elitism=True,
    enable_multi_eval=False,
)

# 测试配置 (mock)
LLM_CONFIG_TEST = LLMConfig(
    provider="mock",
    model="mock",
    llm_mutation_rate=0.50,
    enable_elitism=False,
    enable_multi_eval=False,
)


def get_config(profile: str = "high_perf") -> LLMConfig:
    """获取预设配置"""
    configs = {
        "high_perf": LLM_CONFIG_HIGH_PERF,
        "economy": LLM_CONFIG_ECONOMY,
        "test": LLM_CONFIG_TEST,
    }
    return configs.get(profile, LLM_CONFIG_HIGH_PERF)
