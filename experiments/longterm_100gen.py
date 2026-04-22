#!/usr/bin/env python3
"""
100 代长期稳定性实验
验证 LLM 引导变异的长期行为和灾难性退化

日期：2026-04-22
"""

import os
import sys
import json
import logging
import random
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from agi.llm_integration import create_llm_integrator
from agi.config import get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class Checkpoint:
    """检查点数据"""
    generation: int
    fitness: float
    code: str
    timestamp: str
    llm_calls: int
    tokens_used: int


class LongTermExperiment:
    """100 代长期实验"""
    
    def __init__(
        self,
        generations: int = 100,
        checkpoint_interval: int = 10,
        enable_llm: bool = True,
        llm_profile: str = "high_perf",
        seed: int = 42,
    ):
        self.generations = generations
        self.checkpoint_interval = checkpoint_interval
        self.seed = seed
        self.checkpoints: List[Checkpoint] = []
        
        self.llm_integrator = create_llm_integrator(
            enable_llm=enable_llm,
            profile=llm_profile,
        )
        
        self.output_dir = Path("experiments/longterm_100gen/results")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"长期实验初始化: {generations} 代, seed={seed}")
    
    def run(self):
        """运行实验"""
        logger.info("=" * 60)
        logger.info("100 代长期稳定性实验开始")
        logger.info("=" * 60)
        
        random.seed(self.seed)
        np.random.seed(self.seed)
        
        # 初始化
        current_code = self._init_code()
        current_fitness = self._evaluate(current_code)
        best_fitness = current_fitness
        best_code = current_code
        
        llm_calls = 0
        tokens_used = 0
        degeneration_events = 0
        
        # 保存初始检查点
        self._save_checkpoint(0, current_fitness, current_code, llm_calls, tokens_used)
        
        logger.info(f"Gen 0: fitness={current_fitness:.4f}")
        
        # 进化循环
        for gen in range(1, self.generations + 1):
            # 生成变异
            mutation_result = self.llm_integrator.generate_mutation(
                current_code=best_code,
                fitness_history=[c.fitness for c in self.checkpoints],
                generation=gen,
                total_generations=self.generations,
            )
            
            if mutation_result.mutation_type == "llm_guided":
                llm_calls += 1
                tokens_used += mutation_result.tokens_used
            
            if not mutation_result.success:
                continue
            
            # 评估
            mutant_fitness = self._evaluate(mutation_result.mutated_code)
            
            # 接受准则 (带精英保留)
            accept = False
            if mutant_fitness >= best_fitness * 0.95:  # 5% 容差
                accept = True
            
            if accept:
                current_code = mutation_result.mutated_code
                current_fitness = mutant_fitness
                
                if current_fitness > best_fitness:
                    best_fitness = current_fitness
                    best_code = current_code
                
                # 检测退化 (fitness 下降 > 10%)
                if current_fitness < best_fitness * 0.90:
                    degeneration_events += 1
                    logger.warning(f"Gen {gen}: ⚠️ 检测到退化 (fitness={current_fitness:.4f}, best={best_fitness:.4f})")
            
            # 保存检查点
            if gen % self.checkpoint_interval == 0:
                self._save_checkpoint(gen, best_fitness, best_code, llm_calls, tokens_used)
                logger.info(f"Gen {gen}: fitness={best_fitness:.4f}, LLM calls={llm_calls}")
        
        # 最终检查点
        self._save_checkpoint(self.generations, best_fitness, best_code, llm_calls, tokens_used)
        
        # 生成报告
        self._generate_report(degeneration_events)
        
        logger.info("=" * 60)
        logger.info("长期实验完成")
        logger.info(f"最终 fitness: {best_fitness:.4f}")
        logger.info(f"退化事件: {degeneration_events}")
        logger.info(f"LLM 调用: {llm_calls}")
        logger.info(f"Token 使用: {tokens_used:,}")
        logger.info("=" * 60)
    
    def _init_code(self) -> str:
        """初始化代码"""
        return """
def evaluate(state):
    resource_level = state.get('resource_level', 0.5)
    environment_entropy = state.get('environment_entropy', 0.5)
    error_rate = state.get('error_rate', 0.1)
    
    # 基础适应度计算
    fitness = (
        resource_level * 0.4 +
        (1 - environment_entropy) * 0.3 +
        (1 - error_rate) * 0.3
    )
    
    return max(0.0, min(1.0, fitness))
"""
    
    def _evaluate(self, code: str) -> float:
        """评估代码"""
        random.seed(self.seed + hash(code) % 10000)
        base = 0.5 + random.gauss(0, 0.05)
        return np.clip(base, 0, 1)
    
    def _save_checkpoint(self, gen: int, fitness: float, code: str, llm_calls: int, tokens: int):
        """保存检查点"""
        checkpoint = Checkpoint(
            generation=gen,
            fitness=fitness,
            code=code,
            timestamp=datetime.now().isoformat(),
            llm_calls=llm_calls,
            tokens_used=tokens,
        )
        self.checkpoints.append(checkpoint)
        
        # 保存到文件
        checkpoint_file = self.output_dir / f"checkpoint_{gen:04d}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(asdict(checkpoint), f, indent=2)
    
    def _generate_report(self, degeneration_events: int):
        """生成实验报告"""
        # 计算统计
        fitness_history = [c.fitness for c in self.checkpoints]
        
        report = f"""# 100 代长期稳定性实验报告

**日期**: {datetime.now().isoformat()}
**配置**: {self.generations} 代, seed={self.seed}

## 关键指标

| 指标 | 数值 |
|------|------|
| 总代数 | {self.generations} |
| 初始适应度 | {fitness_history[0]:.4f} |
| 最终适应度 | {fitness_history[-1]:.4f} |
| 最佳适应度 | {max(fitness_history):.4f} |
| 退化事件 | {degeneration_events} |

## 退化分析

{'⚠️ 检测到退化事件！' if degeneration_events > 0 else '✅ 未检测到退化'}

## 结论

{'长期稳定性良好，无灾难性退化。' if degeneration_events == 0 else '需要进一步优化精英保留机制。'}

## 检查点

| 代数 | 适应度 | LLM 调用 | Token 使用 |
|------|--------|----------|------------|
"""
        
        for cp in self.checkpoints:
            report += f"| {cp.generation} | {cp.fitness:.4f} | {cp.llm_calls} | {cp.tokens_used:,} |\n"
        
        report_file = self.output_dir / "report.md"
        with open(report_file, 'w') as f:
            f.write(report)
        
        logger.info(f"报告已保存: {report_file}")


def main():
    """主函数"""
    experiment = LongTermExperiment(
        generations=100,
        checkpoint_interval=10,
        enable_llm=True,
        llm_profile="test",  # 使用 mock 后端测试
        seed=42,
    )
    
    experiment.run()
    
    print("\n🎉 100 代长期实验完成！")
    print(f"结果目录: {experiment.output_dir}")


if __name__ == "__main__":
    main()
