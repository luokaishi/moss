"""
MOSS mves - LLM 集成模块
轻量级集成 main 分支 v8.1.1 LLM 能力到 mves AGI 架构

日期：2026-04-22
版本：v1.0 (轻量集成方案 A)
"""

import logging
import random
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    from agi.llm_backend import LLMBackend, LLMConfig
    from agi.hybrid_mutation import HybridMutationStrategy
    LLM_AVAILABLE = True
except ImportError as e:
    logger.warning(f"LLM 模块导入失败：{e}，将使用纯 AST 变异")
    LLM_AVAILABLE = False
    LLMBackend = None
    LLMConfig = None
    HybridMutationStrategy = None


@dataclass
class LLMMutationResult:
    """LLM 变异结果"""
    success: bool
    mutated_code: Optional[str]
    mutation_type: Optional[str]
    tokens_used: int = 0
    llm_response: Optional[str] = None
    error_message: Optional[str] = None


class AGILLMIntegrator:
    """
    AGI LLM 集成器
    
    将 LLM 引导变异能力注入到 mves 现有 GP 系统
    """
    
    def __init__(
        self,
        enable_llm: bool = True,
        llm_config: Optional[LLMConfig] = None,
        gp_system: Optional[Any] = None,
    ):
        """
        初始化 LLM 集成器
        
        Args:
            enable_llm: 是否启用 LLM 变异
            llm_config: LLM 配置 (默认使用 high_perf)
            gp_system: 遗传编程系统实例 (用于获取当前代码)
        """
        self.enable_llm = enable_llm and LLM_AVAILABLE
        self.gp_system = gp_system
        
        if self.enable_llm and llm_config:
            self.llm_backend = LLMBackend(llm_config)
            self.hybrid_strategy = HybridMutationStrategy(llm_config)
            logger.info(f"✅ LLM 集成已启用 (provider={llm_config.provider}, model={llm_config.model})")
        else:
            self.llm_backend = None
            self.hybrid_strategy = None
            if not LLM_AVAILABLE:
                logger.warning("⚠️ LLM 模块不可用，将使用纯 AST 变异")
            else:
                logger.info("ℹ️ LLM 已禁用，将使用纯 AST 变异")
    
    def generate_mutation(
        self,
        current_code: str,
        fitness_history: List[float],
        generation: int,
        total_generations: int,
    ) -> LLMMutationResult:
        """
        生成变异（LLM 或 AST）
        
        Args:
            current_code: 当前代码
            fitness_history: 适应度历史
            generation: 当前代数
            total_generations: 总代数
        
        Returns:
            LLMMutationResult: 变异结果
        """
        if not self.enable_llm:
            return self._ast_fallback(current_code)
        
        # 使用 hybrid 策略决定是否使用 LLM
        use_llm = self.hybrid_strategy.should_use_llm(
            generation=generation,
            total_generations=total_generations,
            fitness_history=fitness_history,
        )
        
        if use_llm:
            return self._llm_mutation(current_code, fitness_history, generation)
        else:
            return self._ast_fallback(current_code)
    
    def _llm_mutation(
        self,
        current_code: str,
        fitness_history: List[float],
        generation: int,
    ) -> LLMMutationResult:
        """LLM 引导变异"""
        try:
            # 构建 prompt
            prompt = self._build_mutation_prompt(current_code, fitness_history, generation)
            
            # 调用 LLM
            response = self.llm_backend.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            
            # 解析响应
            mutated_code = self._parse_llm_response(response)
            
            if mutated_code:
                logger.info(f"✅ LLM 变异成功 (gen={generation}, tokens={response.get('tokens_used', 0)})")
                return LLMMutationResult(
                    success=True,
                    mutated_code=mutated_code,
                    mutation_type="llm_guided",
                    tokens_used=response.get('tokens_used', 0),
                    llm_response=response.get('content', ''),
                )
            else:
                logger.warning(f"⚠️ LLM 响应解析失败 (gen={generation})")
                return self._ast_fallback(current_code)
        
        except Exception as e:
            logger.error(f"❌ LLM 变异失败：{e}")
            return LLMMutationResult(
                success=False,
                mutated_code=None,
                mutation_type=None,
                error_message=str(e),
            )
    
    def _ast_fallback(self, current_code: str) -> LLMMutationResult:
        """AST 变异回退"""
        if self.gp_system and hasattr(self.gp_system, 'mutate_code'):
            try:
                mutated = self.gp_system.mutate_code(current_code)
                return LLMMutationResult(
                    success=True,
                    mutated_code=mutated,
                    mutation_type="ast_mutation",
                )
            except Exception as e:
                logger.error(f"❌ AST 变异失败：{e}")
                return LLMMutationResult(
                    success=False,
                    mutated_code=None,
                    mutation_type=None,
                    error_message=str(e),
                )
        else:
            return LLMMutationResult(
                success=False,
                mutated_code=None,
                mutation_type=None,
                error_message="GP system not available",
            )
    
    def _build_mutation_prompt(
        self,
        current_code: str,
        fitness_history: List[float],
        generation: int,
    ) -> str:
        """构建 LLM 变异 prompt"""
        fitness_trend = "↑" if len(fitness_history) > 1 and fitness_history[-1] > fitness_history[-2] else "↓"
        
        prompt = f"""你是一个 AI 代码进化系统的变异引擎。请对以下代码进行改进变异。

## 当前状态
- 代数：{generation}
- 适应度趋势：{fitness_trend}
- 最近适应度：{fitness_history[-1]:.4f} (如果 history 非空)

## 当前代码
```python
{current_code[:5000]}  # 限制长度避免 token 超限
```

## 任务
请对代码进行小幅改进变异，目标是提高适应度。可以：
1. 调整参数或阈值
2. 优化条件判断
3. 改进计算公式
4. 添加有益的启发式规则

## 要求
1. 保持代码结构基本不变
2. 只修改 1-3 处关键位置
3. 确保语法正确
4. 输出完整代码（不要省略）

## 输出格式
直接输出改进后的完整 Python 代码，不要解释。"""
        
        return prompt
    
    def _parse_llm_response(self, response: Dict[str, Any]) -> Optional[str]:
        """解析 LLM 响应，提取代码"""
        content = response.get('content', '')
        
        # 尝试提取代码块
        if '```python' in content:
            start = content.find('```python') + len('```python')
            end = content.find('```', start)
            if end > start:
                return content[start:end].strip()
        elif '```' in content:
            start = content.find('```') + 3
            end = content.find('```', start)
            if end > start:
                return content[start:end].strip()
        
        # 如果没有代码块，尝试直接使用响应
        if content.strip():
            return content.strip()
        
        return None
    
    def evaluate_with_multi_eval(
        self,
        code: str,
        eval_fn,
        n_rounds: int = 3,
    ) -> Dict[str, float]:
        """
        多轮评估（减少随机性）
        
        Args:
            code: 待评估代码
            eval_fn: 评估函数
            n_rounds: 评估轮数
        
        Returns:
            评估结果统计
        """
        if not self.enable_llm or not hasattr(self, 'llm_backend'):
            # 回退到单次评估
            fitness = eval_fn(code)
            return {"mean": fitness, "std": 0.0, "rounds": 1}
        
        fitness_scores = []
        for i in range(n_rounds):
            # 每轮使用不同随机种子
            random.seed(42 + i)
            try:
                fitness = eval_fn(code)
                fitness_scores.append(fitness)
            except Exception as e:
                logger.warning(f"评估轮次 {i+1}/{n_rounds} 失败：{e}")
                continue
        
        if not fitness_scores:
            return {"mean": 0.0, "std": 0.0, "rounds": 0}
        
        import numpy as np
        return {
            "mean": float(np.mean(fitness_scores)),
            "std": float(np.std(fitness_scores)),
            "min": float(np.min(fitness_scores)),
            "max": float(np.max(fitness_scores)),
            "rounds": len(fitness_scores),
        }


# ========== 便捷函数 ==========

def create_llm_integrator(
    enable_llm: bool = True,
    profile: str = "high_perf",
    gp_system=None,
) -> AGILLMIntegrator:
    """
    创建 LLM 集成器（使用预设配置）
    
    Args:
        enable_llm: 是否启用
        profile: 配置模板 (high_perf | economy | test)
        gp_system: GP 系统实例
    
    Returns:
        AGILLMIntegrator
    """
    if not LLM_AVAILABLE:
        logger.warning("LLM 模块不可用，返回禁用 LLM 的集成器")
        return AGILLMIntegrator(enable_llm=False, gp_system=gp_system)
    
    from agi.config import get_config
    config = get_config(profile)
    
    return AGILLMIntegrator(
        enable_llm=enable_llm,
        llm_config=config,
        gp_system=gp_system,
    )
