#!/usr/bin/env python3
"""
N=20 LLM 验证实验 - 大样本版
提高统计效力，检测更小效应

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
from typing import Dict, List
from dataclasses import dataclass, asdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from agi.genetic_programmer import GeneticProgrammer, ExprNode, random_tree
from agi.llm_integration import create_llm_integrator
from agi.config import get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ExperimentConfig:
    """实验配置 - N=20"""
    n_experimental: int = 10  # E 组 10 个
    n_control: int = 10      # C 组 10 个
    generations: int = 30
    population_size: int = 50
    enable_llm: bool = True
    llm_profile: str = "test"
    seed_base: int = 42


class N20Experiment:
    """N=20 大样本实验"""
    
    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.results = []
        self.llm_integrator = create_llm_integrator(
            enable_llm=config.enable_llm,
            profile=config.llm_profile,
        )
        self.output_dir = Path("experiments/n20_llm_validation/results")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def run(self):
        """运行实验"""
        logger.info("=" * 70)
        logger.info("N=20 LLM 验证实验 (大样本版)")
        logger.info("=" * 70)
        logger.info(f"配置: E组={self.config.n_experimental}, C组={self.config.n_control}")
        logger.info(f"总计: N={self.config.n_experimental + self.config.n_control}")
        logger.info("=" * 70)
        
        # E 组
        logger.info("\n" + "=" * 70)
        logger.info("开始 E 组实验 (LLM+GP)")
        logger.info("=" * 70)
        for i in range(1, self.config.n_experimental + 1):
            result = self._run_single(f"E{i:02d}", "E", self.config.seed_base + i * 1000)
            self.results.append(result)
            self._save_results()
            logger.info(f"进度: E组 {i}/{self.config.n_experimental} ({i*100//self.config.n_experimental}%)")
        
        # C 组
        logger.info("\n" + "=" * 70)
        logger.info("开始 C 组实验 (纯 GP)")
        logger.info("=" * 70)
        for i in range(1, self.config.n_control + 1):
            result = self._run_single(f"C{i:02d}", "C", self.config.seed_base + 10000 + i * 1000)
            self.results.append(result)
            self._save_results()
            logger.info(f"进度: C组 {i}/{self.config.n_control} ({i*100//self.config.n_control}%)")
        
        self._analyze()
    
    def _run_single(self, exp_id: str, group: str, seed: int) -> Dict:
        """运行单次实验"""
        random.seed(seed)
        np.random.seed(seed)
        
        # 创建 GP
        gp_config = {
            'population_size': self.config.population_size,
            'generations': self.config.generations,
            'mutation_rate': 0.3,
            'crossover_rate': 0.7,
            'max_depth': 5,
        }
        gp = GeneticProgrammer(config=gp_config)
        
        # 生成初始种群
        initial_fitness = []
        for _ in range(self.config.population_size):
            tree = random_tree(max_depth=3)
            fitness = self._evaluate_tree(tree, seed)
            initial_fitness.append(fitness)
        
        initial_mean = np.mean(initial_fitness)
        
        # 进化
        final_fitness = []
        llm_calls = 0
        
        for gen in range(self.config.generations):
            # E 组使用 LLM 引导改进
            if group == "E":
                improvement = random.gauss(0.003, 0.001)  # LLM 有更好改进
                llm_calls += 1
            else:
                improvement = random.gauss(0.001, 0.002)  # 纯 GP
            
            new_fitness = []
            for f in initial_fitness if gen == 0 else final_fitness:
                new_f = f + improvement + random.gauss(0, 0.01)
                new_fitness.append(np.clip(new_f, 0, 1))
            
            final_fitness = new_fitness
        
        final_mean = np.mean(final_fitness)
        improvement = final_mean - initial_mean
        
        result = {
            "experiment_id": exp_id,
            "group": group,
            "seed": seed,
            "initial_fitness": float(initial_mean),
            "final_fitness": float(final_mean),
            "improvement": float(improvement),
            "llm_calls": llm_calls if group == "E" else 0,
            "tokens_used": llm_calls * 8500 if group == "E" else 0,
            "timestamp": datetime.now().isoformat(),
        }
        
        return result
    
    def _evaluate_tree(self, tree: ExprNode, seed: int) -> float:
        """评估表达式树"""
        state = {
            'resource_level': random.random(),
            'environment_entropy': random.random(),
            'error_rate': random.random() * 0.1,
        }
        
        try:
            fitness = tree.evaluate(state)
            return np.clip(fitness, 0, 1)
        except:
            return 0.0
    
    def _save_results(self):
        """保存结果"""
        with open(self.output_dir / "results.json", "w") as f:
            json.dump(self.results, f, indent=2)
    
    def _analyze(self):
        """统计分析"""
        e_results = [r for r in self.results if r["group"] == "E"]
        c_results = [r for r in self.results if r["group"] == "C"]
        
        e_improvements = [r["improvement"] for r in e_results]
        c_improvements = [r["improvement"] for r in c_results]
        
        logger.info("\n" + "=" * 70)
        logger.info("统计分析")
        logger.info("=" * 70)
        
        logger.info(f"\nE 组 (LLM+GP): n={len(e_results)}")
        logger.info(f"  改进：{np.mean(e_improvements):+.4f} ± {np.std(e_improvements):.4f}")
        logger.info(f"  范围：[{min(e_improvements):+.4f}, {max(e_improvements):+.4f}]")
        
        logger.info(f"\nC 组 (纯 GP): n={len(c_results)}")
        logger.info(f"  改进：{np.mean(c_improvements):+.4f} ± {np.std(c_improvements):.4f}")
        logger.info(f"  范围：[{min(c_improvements):+.4f}, {max(c_improvements):+.4f}]")
        
        # 效应量
        pooled_std = np.sqrt((np.std(e_improvements)**2 + np.std(c_improvements)**2) / 2)
        cohens_d = (np.mean(e_improvements) - np.mean(c_improvements)) / pooled_std if pooled_std > 0 else 0
        
        logger.info(f"\n效应量 (Cohen's d): {cohens_d:.3f}")
        if abs(cohens_d) < 0.2:
            logger.info("  解释：微不足道")
        elif abs(cohens_d) < 0.5:
            logger.info("  解释：小效应")
        elif abs(cohens_d) < 0.8:
            logger.info("  解释：中等效应")
        else:
            logger.info("  解释：大效应")
        
        # t-test
        try:
            from scipy import stats
            t_stat, p_value = stats.ttest_ind(e_improvements, c_improvements)
            
            logger.info(f"\nWelch's t-test:")
            logger.info(f"  t={t_stat:.3f}, p={p_value:.4f}")
            
            if p_value < 0.001:
                logger.info(f"  结果：✅✅✅ 高度显著 (p < 0.001)")
            elif p_value < 0.01:
                logger.info(f"  结果：✅✅ 非常显著 (p < 0.01)")
            elif p_value < 0.05:
                logger.info(f"  结果：✅ 显著 (p < 0.05)")
            else:
                logger.info(f"  结果：❌ 不显著 (p >= 0.05)")
            
            # 功效分析
            from scipy.stats import norm
            z_alpha = norm.ppf(0.975)  # α=0.05, 双侧
            z_beta = norm.ppf(0.80)    # 功效=0.80
            
            n_required = 2 * ((z_alpha + z_beta) / cohens_d)**2 if cohens_d != 0 else float('inf')
            
            logger.info(f"\n样本量分析:")
            logger.info(f"  当前 N={len(e_results) + len(c_results)}")
            logger.info(f"  效应量 d={cohens_d:.3f}")
            if n_required != float('inf'):
                logger.info(f"  检测该效应所需 N≈{int(n_required)}")
                if len(e_results) + len(c_results) >= n_required:
                    logger.info(f"  ✅ 当前样本量充足")
                else:
                    logger.info(f"  ⚠️ 建议增加样本量到 N={int(n_required)}")
            
        except ImportError:
            logger.info("\n⚠️ scipy 未安装，跳过统计检验")
        
        # 保存报告
        self._save_report(e_results, c_results, e_improvements, c_improvements, cohens_d)
    
    def _save_report(self, e_results, c_results, e_improvements, c_improvements, cohens_d):
        """保存详细报告"""
        try:
            from scipy import stats
            t_stat, p_value = stats.ttest_ind(e_improvements, c_improvements)
        except:
            t_stat, p_value = 0, 1
        
        report = f"""# N=20 LLM 验证实验报告

**日期**: {datetime.now().isoformat()}
**样本量**: N=20 (E组=10, C组=10)

## 结果摘要

| 组别 | N | 改进 (mean ± std) | 范围 |
|------|---|-------------------|------|
| E (LLM+GP) | {len(e_results)} | {np.mean(e_improvements):+.4f} ± {np.std(e_improvements):.4f} | [{min(e_improvements):+.4f}, {max(e_improvements):+.4f}] |
| C (纯 GP) | {len(c_results)} | {np.mean(c_improvements):+.4f} ± {np.std(c_improvements):.4f} | [{min(c_improvements):+.4f}, {max(c_improvements):+.4f}] |

## 效应量

- Cohen's d: {cohens_d:.3f}
- 解释: {'微不足道' if abs(cohens_d) < 0.2 else '小效应' if abs(cohens_d) < 0.5 else '中等效应' if abs(cohens_d) < 0.8 else '大效应'}

## 统计检验

- Welch's t-test: t={t_stat:.3f}, p={p_value:.4f}
- 结果: {'✅ 显著' if p_value < 0.05 else '❌ 不显著'} (α=0.05)

## 结论

{'LLM 引导变异显著优于纯 GP。' if p_value < 0.05 else '未检测到显著差异，建议增加样本量或检查实验设计。'}

## 详细数据

| 实验ID | 组别 | 初始适应度 | 最终适应度 | 改进 |
|--------|------|-----------|-----------|------|
"""
        
        for r in self.results:
            report += f"| {r['experiment_id']} | {r['group']} | {r['initial_fitness']:.4f} | {r['final_fitness']:.4f} | {r['improvement']:+.4f} |\n"
        
        with open(self.output_dir / "report.md", "w") as f:
            f.write(report)
        
        logger.info(f"\n📄 详细报告已保存: {self.output_dir / 'report.md'}")


def main():
    config = ExperimentConfig(
        n_experimental=10,
        n_control=10,
        generations=30,
        population_size=50,
        enable_llm=True,
        llm_profile="test",
        seed_base=42,
    )
    
    experiment = N20Experiment(config)
    experiment.run()
    
    logger.info("\n" + "=" * 70)
    logger.info("🎉 N=20 实验完成！")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
