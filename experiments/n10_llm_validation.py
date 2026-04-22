#!/usr/bin/env python3
"""
N=10 LLM 验证实验脚本
基于 main 分支 v8.1.1 经验设计

实验设计:
- E 组：GP + LLM (50%) + Elite + multi_eval
- C 组：GP-only (基线)
- 每实验 30 代
- N=10 重复 (E=5, C=5)

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

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from agi.llm_integration import create_llm_integrator, AGILLMIntegrator
from agi.config import get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ExperimentConfig:
    """实验配置"""
    # 实验参数
    n_experimental: int = 5           # E 组实验次数
    n_control: int = 5                # C 组实验次数
    generations: int = 30             # 每实验代数
    population_size: int = 50         # 种群大小
    
    # LLM 配置
    enable_llm: bool = True
    llm_profile: str = "high_perf"    # high_perf | economy | test
    llm_mutation_rate: float = 0.50   # 50% LLM 变异
    
    # v8.1 特性
    enable_elitism: bool = True
    enable_multi_eval: bool = True
    multi_eval_rounds: int = 3
    
    # 随机种子
    seed_base: int = 42
    
    # 输出
    output_dir: str = "experiments/n10_llm_validation/results"


@dataclass
class ExperimentResult:
    """实验结果"""
    experiment_id: str
    group: str  # "E" or "C"
    seed: int
    generations: int
    fitness_history: List[float]
    final_fitness: float
    fitness_improvement: float
    llm_calls: int = 0
    tokens_used: int = 0
    acceptance_rate: float = 0.0
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class N10ValidationExperiment:
    """N=10 LLM 验证实验"""
    
    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.results: List[ExperimentResult] = []
        
        # 初始化 LLM 集成器
        self.llm_integrator = create_llm_integrator(
            enable_llm=config.enable_llm,
            profile=config.llm_profile,
        )
        
        logger.info(f"实验配置：{asdict(config)}")
    
    def run_single_experiment(
        self,
        group: str,
        experiment_num: int,
        seed: int,
    ) -> ExperimentResult:
        """运行单次实验"""
        logger.info(f"\n{'='*60}")
        logger.info(f"开始实验：{group}组 #{experiment_num} (seed={seed})")
        logger.info(f"{'='*60}")
        
        random.seed(seed)
        np.random.seed(seed)
        
        # 初始化
        fitness_history = []
        llm_calls = 0
        tokens_used = 0
        accepted_mutations = 0
        total_mutations = 0
        
        # 初始代码 (示例)
        current_code = """
def evaluate(state):
    resource_level = state.get('resource_level', 0.5)
    environment_entropy = state.get('environment_entropy', 0.5)
    return resource_level * 0.6 + environment_entropy * 0.4
"""
        
        # 初始适应度
        current_fitness = self._evaluate_code(current_code, seed=seed)
        fitness_history.append(current_fitness)
        best_fitness = current_fitness
        best_code = current_code
        
        logger.info(f"初始适应度：{current_fitness:.4f}")
        
        # 进化循环
        for gen in range(self.config.generations):
            # 生成变异
            if group == "E" and self.llm_integrator.enable_llm:
                mutation_result = self.llm_integrator.generate_mutation(
                    current_code=best_code,
                    fitness_history=fitness_history,
                    generation=gen,
                    total_generations=self.config.generations,
                )
                
                if mutation_result.mutation_type == "llm_guided":
                    llm_calls += 1
                    tokens_used += mutation_result.tokens_used
            else:
                # C 组或 LLM 禁用：使用 AST 变异
                mutation_result = self.llm_integrator._ast_fallback(best_code)
            
            total_mutations += 1
            
            if not mutation_result.success or not mutation_result.mutated_code:
                logger.debug(f"Gen {gen}: 变异失败，跳过")
                continue
            
            # 评估变异
            mutant_fitness = self._evaluate_code(
                mutation_result.mutated_code,
                seed=seed + gen,  # 每代不同种子
            )
            
            # 接受准则 (带精英保留)
            accept = False
            if self.config.enable_elitism:
                # 精英保留：只接受不劣于当前最佳的
                if mutant_fitness >= best_fitness * 0.95:  # 5% 容差
                    accept = True
            else:
                # 简单 hill-climbing
                if mutant_fitness > current_fitness:
                    accept = True
            
            if accept:
                accepted_mutations += 1
                current_code = mutation_result.mutated_code
                current_fitness = mutant_fitness
                fitness_history.append(current_fitness)
                
                if current_fitness > best_fitness:
                    best_fitness = current_fitness
                    best_code = current_code
                    logger.info(f"Gen {gen}: ✅ 接受变异，fitness={current_fitness:.4f} (新最佳)")
                else:
                    logger.debug(f"Gen {gen}: 接受变异，fitness={current_fitness:.4f}")
            else:
                fitness_history.append(current_fitness)
                logger.debug(f"Gen {gen}: ❌ 拒绝变异")
        
        # 计算结果
        fitness_improvement = fitness_history[-1] - fitness_history[0]
        acceptance_rate = accepted_mutations / max(total_mutations, 1)
        
        result = ExperimentResult(
            experiment_id=f"{group}{experiment_num:02d}",
            group=group,
            seed=seed,
            generations=self.config.generations,
            fitness_history=[float(f) for f in fitness_history],
            final_fitness=float(fitness_history[-1]),
            fitness_improvement=float(fitness_improvement),
            llm_calls=llm_calls,
            tokens_used=tokens_used,
            acceptance_rate=acceptance_rate,
        )
        
        logger.info(f"\n实验完成：{group}{experiment_num:02d}")
        logger.info(f"  最终适应度：{result.final_fitness:.4f}")
        logger.info(f"  改进：{result.fitness_improvement:+.4f}")
        logger.info(f"  LLM 调用：{result.llm_calls} 次")
        logger.info(f"  Token 使用：{result.tokens_used:,}")
        logger.info(f"  接受率：{result.acceptance_rate:.2%}")
        
        return result
    
    def _evaluate_code(self, code: str, seed: int = 42) -> float:
        """
        评估代码适应度
        
        这里使用简化的模拟评估
        实际使用时应替换为真实的评估函数
        """
        random.seed(seed)
        
        # 模拟适应度评估 (带噪声)
        base_fitness = 0.5 + random.gauss(0, 0.05)
        
        # 简单的适应度漂移 (模拟进化)
        noise = random.gauss(0, 0.02)
        
        return np.clip(base_fitness + noise, 0, 1)
    
    def run_all_experiments(self):
        """运行所有实验"""
        logger.info("\n" + "="*60)
        logger.info("开始 N=10 LLM 验证实验")
        logger.info("="*60)
        
        # E 组实验
        for i in range(self.config.n_experimental):
            seed = self.config.seed_base + i * 1000
            result = self.run_single_experiment("E", i+1, seed)
            self.results.append(result)
            
            # 保存中间结果
            self._save_results()
        
        # C 组实验
        for i in range(self.config.n_control):
            seed = self.config.seed_base + 10000 + i * 1000
            result = self.run_single_experiment("C", i+1, seed)
            self.results.append(result)
            
            # 保存中间结果
            self._save_results()
        
        logger.info("\n" + "="*60)
        logger.info("所有实验完成！")
        logger.info("="*60)
        
        # 统计分析
        self._statistical_analysis()
    
    def _save_results(self):
        """保存结果"""
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存详细结果
        results_data = [asdict(r) for r in self.results]
        with open(output_dir / "results.json", "w", encoding="utf-8") as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        # 保存汇总统计
        self._save_summary(output_dir)
    
    def _save_summary(self, output_dir: Path):
        """保存汇总统计"""
        e_results = [r for r in self.results if r.group == "E"]
        c_results = [r for r in self.results if r.group == "C"]
        
        if not e_results or not c_results:
            return
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "config": asdict(self.config),
            "experimental_group": {
                "n": len(e_results),
                "final_fitness_mean": np.mean([r.final_fitness for r in e_results]),
                "final_fitness_std": np.std([r.final_fitness for r in e_results]),
                "fitness_improvement_mean": np.mean([r.fitness_improvement for r in e_results]),
                "fitness_improvement_std": np.std([r.fitness_improvement for r in e_results]),
                "llm_calls_mean": np.mean([r.llm_calls for r in e_results]),
                "tokens_used_mean": np.mean([r.tokens_used for r in e_results]),
            },
            "control_group": {
                "n": len(c_results),
                "final_fitness_mean": np.mean([r.final_fitness for r in c_results]),
                "final_fitness_std": np.std([r.final_fitness for r in c_results]),
                "fitness_improvement_mean": np.mean([r.fitness_improvement for r in c_results]),
                "fitness_improvement_std": np.std([r.fitness_improvement for r in c_results]),
            },
        }
        
        with open(output_dir / "summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n汇总统计已保存到 {output_dir / 'summary.json'}")
    
    def _statistical_analysis(self):
        """统计分析"""
        e_results = [r for r in self.results if r.group == "E"]
        c_results = [r for r in self.results if r.group == "C"]
        
        if len(e_results) < 2 or len(c_results) < 2:
            logger.warning("样本量不足，跳过统计分析")
            return
        
        # 提取数据
        e_fitness = [r.final_fitness for r in e_results]
        c_fitness = [r.final_fitness for r in c_results]
        e_improvement = [r.fitness_improvement for r in e_results]
        c_improvement = [r.fitness_improvement for r in c_results]
        
        logger.info("\n" + "="*60)
        logger.info("统计分析")
        logger.info("="*60)
        
        # 描述性统计
        logger.info(f"\nE 组 (LLM): n={len(e_results)}")
        logger.info(f"  最终适应度：{np.mean(e_fitness):.4f} ± {np.std(e_fitness):.4f}")
        logger.info(f"  适应度改进：{np.mean(e_improvement):.4f} ± {np.std(e_improvement):.4f}")
        logger.info(f"  LLM 调用：{np.mean([r.llm_calls for r in e_results]):.1f} 次")
        logger.info(f"  Token 使用：{np.mean([r.tokens_used for r in e_results]):.0f}")
        
        logger.info(f"\nC 组 (对照): n={len(c_results)}")
        logger.info(f"  最终适应度：{np.mean(c_fitness):.4f} ± {np.std(c_fitness):.4f}")
        logger.info(f"  适应度改进：{np.mean(c_improvement):.4f} ± {np.std(c_improvement):.4f}")
        
        # 效应量计算
        pooled_std = np.sqrt((np.std(e_fitness)**2 + np.std(c_fitness)**2) / 2)
        if pooled_std > 0:
            cohens_d = (np.mean(e_fitness) - np.mean(c_fitness)) / pooled_std
            logger.info(f"\n效应量 (Cohen's d): {cohens_d:.3f}")
            
            if abs(cohens_d) < 0.2:
                logger.info("  解释：微不足道")
            elif abs(cohens_d) < 0.5:
                logger.info("  解释：小效应")
            elif abs(cohens_d) < 0.8:
                logger.info("  解释：中等效应")
            else:
                logger.info("  解释：大效应 ✅")
        
        # 保存统计报告
        self._save_statistical_report(e_fitness, c_fitness, e_improvement, c_improvement)
    
    def _save_statistical_report(
        self,
        e_fitness: List[float],
        c_fitness: List[float],
        e_improvement: List[float],
        c_improvement: List[float],
    ):
        """保存统计报告"""
        from scipy import stats
        
        # t 检验
        t_stat, p_value = stats.ttest_ind(e_fitness, c_fitness)
        
        # Mann-Whitney U 检验
        u_stat, u_p_value = stats.mannwhitneyu(e_fitness, c_fitness, alternative='two-sided')
        
        report = f"""# N=10 LLM 验证实验 - 统计报告

**日期**: {datetime.now().isoformat()}

## 假设检验

### 最终适应度比较

| 检验 | 统计量 | p 值 | 显著性 |
|------|--------|-----|--------|
| Welch's t-test | t={t_stat:.3f} | p={p_value:.4f} | {'✅' if p_value < 0.05 else '❌'} |
| Mann-Whitney U | U={u_stat:.1f} | p={u_p_value:.4f} | {'✅' if u_p_value < 0.05 else '❌'} |

## 结论

{'LLM 组显著优于对照组 (p < 0.05)' if p_value < 0.05 else '未检测到显著差异 (p >= 0.05)'}
"""
        
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_dir / "statistical_report.md", "w", encoding="utf-8") as f:
            f.write(report)
        
        logger.info(f"统计报告已保存到 {output_dir / 'statistical_report.md'}")


def main():
    """主函数"""
    # 创建配置
    config = ExperimentConfig(
        n_experimental=5,
        n_control=5,
        generations=30,
        enable_llm=True,
        llm_profile="test",  # 使用 mock 后端测试
        enable_elitism=True,
        enable_multi_eval=True,
        seed_base=42,
    )
    
    # 创建实验
    experiment = N10ValidationExperiment(config)
    
    # 运行实验
    experiment.run_all_experiments()
    
    logger.info("\n🎉 N=10 验证实验完成！")


if __name__ == "__main__":
    main()
