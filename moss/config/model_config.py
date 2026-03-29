"""
MOSS 多模型配置模块

根据任务类型自动选择最优模型，支持降级策略。
"""

import os
from typing import Optional, List
from dotenv import load_dotenv

# 加载 .env.local 配置
load_dotenv('.env.local')


class MOSSModelConfig:
    """MOSS 模型配置管理器"""
    
    # 默认模型配置
    DEFAULT_CORE_MODEL = "qwen-max"
    DEFAULT_EXPERIMENT_MODEL = "qwen3.5-plus"
    DEFAULT_FAST_MODEL = "qwen-turbo"
    DEFAULT_V2_EVOLUTION_MODEL = "qwen-max"
    
    def __init__(self):
        self.core_model = os.getenv("MOSS_CORE_MODEL", self.DEFAULT_CORE_MODEL)
        self.experiment_model = os.getenv("MOSS_EXPERIMENT_MODEL", self.DEFAULT_EXPERIMENT_MODEL)
        self.fast_model = os.getenv("MOSS_FAST_MODEL", self.DEFAULT_FAST_MODEL)
        self.v2_evolution_model = os.getenv("MOSS_V2_EVOLUTION_MODEL", self.DEFAULT_V2_EVOLUTION_MODEL)
        self.fallback_models = self._parse_fallback()
    
    def _parse_fallback(self) -> List[str]:
        """解析降级模型列表"""
        fallback_str = os.getenv("MOSS_MODEL_FALLBACK", "qwen3.5-plus,qwen-turbo")
        return [m.strip() for m in fallback_str.split(",") if m.strip()]
    
    def get_model(self, task_type: str) -> str:
        """
        根据任务类型获取推荐模型
        
        Args:
            task_type: 任务类型
                - "core_decision": 核心决策
                - "experiment": 日常实验
                - "fast": 快速迭代
                - "v2_evolution": V2 自演化
                - "default": 默认模型
        
        Returns:
            推荐的模型名称
        """
        model_map = {
            "core_decision": self.core_model,
            "experiment": self.experiment_model,
            "fast": self.fast_model,
            "v2_evolution": self.v2_evolution_model,
        }
        return model_map.get(task_type, self.experiment_model)
    
    def get_with_fallback(self, task_type: str, primary_model: Optional[str] = None) -> str:
        """
        获取模型（带降级策略）
        
        如果主模型调用失败，自动降级到备用模型
        
        Args:
            task_type: 任务类型
            primary_model: 可选的主模型（覆盖默认）
        
        Returns:
            推荐的模型名称（含降级列表）
        """
        if primary_model:
            return primary_model
        return self.get_model(task_type)
    
    def get_fallback_chain(self, failed_model: str) -> List[str]:
        """
        获取降级模型链
        
        Args:
            failed_model: 失败的模型名称
        
        Returns:
            降级模型列表（按优先级排序）
        """
        # 从降级列表中移除失败的模型
        fallbacks = [m for m in self.fallback_models if m != failed_model]
        return fallbacks
    
    def validate_model(self, model_name: str) -> bool:
        """
        验证模型名称是否有效
        
        Args:
            model_name: 模型名称
        
        Returns:
            是否有效
        """
        valid_models = [
            "qwen-max",
            "qwen-plus",
            "qwen3.5-plus",
            "qwen-turbo",
            "qwen-long",
        ]
        return model_name.lower() in valid_models
    
    def get_model_info(self, model_name: str) -> dict:
        """
        获取模型详细信息
        
        Args:
            model_name: 模型名称
        
        Returns:
            模型信息字典
        """
        model_info = {
            "qwen-max": {
                "reasoning": "⭐⭐⭐⭐⭐",
                "code": "⭐⭐⭐⭐⭐",
                "speed": "🐢",
                "cost": "💰💰💰",
                "context": "128K",
                "best_for": "复杂决策、科研论文、代码演化"
            },
            "qwen-plus": {
                "reasoning": "⭐⭐⭐⭐",
                "code": "⭐⭐⭐⭐",
                "speed": "🐇",
                "cost": "💰💰",
                "context": "128K",
                "best_for": "日常实验、代码生成"
            },
            "qwen3.5-plus": {
                "reasoning": "⭐⭐⭐⭐",
                "code": "⭐⭐⭐⭐",
                "speed": "🐇",
                "cost": "💰💰",
                "context": "128K",
                "best_for": "平衡性价比（当前默认）"
            },
            "qwen-turbo": {
                "reasoning": "⭐⭐⭐",
                "code": "⭐⭐⭐",
                "speed": "🚀",
                "cost": "💰",
                "context": "128K",
                "best_for": "快速迭代、简单任务"
            },
        }
        return model_info.get(model_name.lower(), {
            "reasoning": "❓",
            "code": "❓",
            "speed": "❓",
            "cost": "❓",
            "context": "❓",
            "best_for": "未知模型"
        })
    
    def print_config(self):
        """打印当前配置"""
        print("=" * 50)
        print("MOSS 多模型配置")
        print("=" * 50)
        print(f"核心决策模型：    {self.core_model}")
        print(f"日常实验模型：    {self.experiment_model}")
        print(f"快速迭代模型：    {self.fast_model}")
        print(f"V2 自演化模型：    {self.v2_evolution_model}")
        print(f"降级策略：        {', '.join(self.fallback_models)}")
        print("=" * 50)
        
        # 显示各模型详情
        all_models = set([
            self.core_model,
            self.experiment_model,
            self.fast_model,
            self.v2_evolution_model,
        ])
        
        for model in all_models:
            info = self.get_model_info(model)
            print(f"\n{model}:")
            print(f"  推理能力：{info['reasoning']}")
            print(f"  代码能力：{info['code']}")
            print(f"  速度：    {info['speed']}")
            print(f"  成本：    {info['cost']}")
            print(f"  上下文：  {info['context']}")
            print(f"  适用场景：{info['best_for']}")


# 全局配置实例
config = MOSSModelConfig()


# 便捷函数
def get_model(task_type: str) -> str:
    """快速获取模型"""
    return config.get_model(task_type)


def print_config():
    """打印配置"""
    config.print_config()


if __name__ == "__main__":
    # 测试配置
    print_config()
    
    # 测试模型获取
    print("\n模型获取测试:")
    print(f"核心决策：{get_model('core_decision')}")
    print(f"日常实验：{get_model('experiment')}")
    print(f"快速迭代：{get_model('fast')}")
    print(f"V2 演化：  {get_model('v2_evolution')}")
