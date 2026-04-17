"""
MOSS Phase 2: Statistical Validation — N-repeated Experiments
==============================================================

对 v6.1 ~ v7.0 的核心实验结果进行 N 次独立重复验证，
通过统计检验（Welch's t-test, Cohen's d, bootstrap CI）确认结论的鲁棒性。

实验矩阵：
  E1: v6.1(随机变异) vs v6.2(语义引导) — Δfitness, Δacceptance_rate
  E2: v6.2(标量)   vs v6.3(Pareto)   — Δfitness, HV
  E3: v7.0 Meta-SME                      — Meta-fitness 提升稳定性

运行方式：
  # 快速验证（N=2, 20代）
  $env:PYTHONUTF8=1; python experiments/run_statistical_validation.py --quick

  # 完整验证（N=5, 30代）
  $env:PYTHONUTF8=1; python experiments/run_statistical_validation.py

  # 单独跑某个实验
  $env:PYTHONUTF8=1; python experiments/run_statistical_validation.py --exp v62 --trials 5

Author: MOSS Project
Date: 2026-04-16
"""

import sys
import json
import time
import logging
import argparse
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 统计工具函数
# ═══════════════════════════════════════════════════════════════

def welch_ttest(a: np.ndarray, b: np.ndarray) -> Dict:
    """
    Welch's t-test (不假设等方差) + Cohen's d

    Returns: {t_stat, df, p_value, cohens_d, significant_005, significant_01}
    """
    n_a, n_b = len(a), len(b)
    mean_a, mean_b = np.mean(a), np.mean(b)
    var_a, var_b = np.var(a, ddof=1), np.var(b, ddof=1)

    se = np.sqrt(var_a / n_a + var_b / n_b)
    t_stat = (mean_a - mean_b) / (se + 1e-15)

    # Welch–Satterthwaite degrees of freedom
    num = (var_a / n_a + var_b / n_b) ** 2
    den = (var_a / n_a) ** 2 / (n_a - 1) + (var_b / n_b) ** 2 / (n_b - 1)
    df = num / (den + 1e-15)

    # 近似 p-value (双侧)
    from math import erfc, sqrt
    p_value = erfc(abs(t_stat) / sqrt(2))  # 近似

    # Cohen's d (pooled std)
    pooled_std = sqrt(((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2 + 1e-15))
    cohens_d = (mean_a - mean_b) / (pooled_std + 1e-15)

    return {
        "t_stat": float(t_stat),
        "df": float(df),
        "p_value": float(p_value),
        "cohens_d": float(cohens_d),
        "mean_a": float(mean_a),
        "mean_b": float(mean_b),
        "std_a": float(np.std(a, ddof=1)),
        "std_b": float(np.std(b, ddof=1)),
        "n_a": n_a,
        "n_b": n_b,
        "significant_005": p_value < 0.05,
        "significant_01": p_value < 0.01,
    }


def bootstrap_ci(values: np.ndarray, n_bootstrap: int = 10000, alpha: float = 0.05) -> Dict:
    """Bootstrap 95% confidence interval"""
    np.random.seed(42)
    boot_means = []
    for _ in range(n_bootstrap):
        sample = np.random.choice(values, size=len(values), replace=True)
        boot_means.append(np.mean(sample))
    boot_means = np.array(boot_means)
    lo = np.percentile(boot_means, 100 * alpha / 2)
    hi = np.percentile(boot_means, 100 * (1 - alpha / 2))
    return {
        "mean": float(np.mean(values)),
        "std": float(np.std(values, ddof=1)),
        "ci_lower": float(lo),
        "ci_upper": float(hi),
        "median": float(np.median(values)),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "n": len(values),
    }


def descriptive_stats(values: List[float]) -> Dict:
    """快速描述性统计"""
    arr = np.array(values)
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0,
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "n": len(arr),
    }


# ═══════════════════════════════════════════════════════════════
# 通用 trial runner (复用现有 v6.2/v6.3 脚本逻辑)
# ═══════════════════════════════════════════════════════════════

def restore_baseline(project_root: Path):
    """恢复unified_agent.py到最早备份（gen1）"""
    target = project_root / "moss" / "core" / "unified_agent.py"

    # 尝试多个可能的备份路径（Phase 1归档后路径变化）
    search_paths = [
        project_root / "experiments" / "self_modification",  # 原始路径
        project_root / "experiments" / "_archive" / "backups",  # 归档后路径
    ]

    # glob 模式也要匹配归档后的重命名格式
    patterns = ["backup_gen1_*.py", "experiments_self_modification_backup_gen1_*.py"]

    backups = []
    for d in search_paths:
        if d.exists():
            for p in patterns:
                backups.extend(d.glob(p))

    if backups:
        backups.sort()
        src = backups[0].read_text(encoding="utf-8")
        target.write_text(src, encoding="utf-8")
        logger.info(f"  [Restore] unified_agent.py from {backups[0].name}")
    else:
        logger.warning(f"  [Restore] 未找到 backup_gen1_*.py，跳过恢复")


def run_v62_trial(seed: int, enable_semantic: bool, max_gen: int = 30) -> Dict:
    """v6.1/v6.2 单次 trial"""
    from moss.core.self_modification_engine import SelfModificationEngine, SMEConfig

    mode = "semantic" if enable_semantic else "random"
    logger.info(f"  [{mode}] seed={seed}")
    np.random.seed(seed)

    pv = np.array([0.25, 0.35, 0.15, 0.25]) if enable_semantic else None

    config = SMEConfig(
        population_size=6,
        max_generations=max_gen,
        acceptance_threshold=-0.002,
        enable_structural_mutations=True,
        mutation_intensity=0.3,
        enable_semantic_guidance=enable_semantic,
        semantic_temperature=1.5,
        semantic_exploration_bonus=0.1,
        use_pareto=False,
        enable_hot_reload=False,
    )
    sme = SelfModificationEngine(config=config, project_root=str(PROJECT_ROOT))
    sme.mutator.rng.seed(seed)
    sme.mutator.np_rng = np.random.default_rng(seed)

    t0 = time.time()
    result = sme.run(max_generations=max_gen, purpose_vector=pv, early_stop_fitness=0.95)
    elapsed = time.time() - t0

    fitness_traj = [g.get("best_fitness", 0.0) for g in result.get("generations", [])]

    return {
        "mode": mode,
        "seed": seed,
        "initial_fitness": result.get("initial_fitness", 0.0),
        "final_fitness": result.get("final_fitness", 0.0),
        "fitness_improvement": result.get("fitness_improvement", 0.0),
        "acceptance_rate": result.get("total_mutations_accepted", 0) / max_gen,
        "fitness_trajectory": fitness_traj,
        "elapsed_seconds": elapsed,
    }


def run_v63_trial(seed: int, use_pareto: bool, max_gen: int = 30) -> Dict:
    """v6.2/v6.3 单次 trial"""
    from moss.core.self_modification_engine import SelfModificationEngine, SMEConfig

    mode = "pareto" if use_pareto else "scalar"
    logger.info(f"  [{mode}] seed={seed}")
    np.random.seed(seed)

    config = SMEConfig(
        population_size=6,
        max_generations=max_gen,
        acceptance_threshold=-0.002,
        enable_structural_mutations=True,
        mutation_intensity=0.3,
        enable_semantic_guidance=True,
        semantic_temperature=1.5,
        semantic_exploration_bonus=0.1,
        use_pareto=use_pareto,
        pareto_archive_size=50,
        enable_hot_reload=False,
    )
    sme = SelfModificationEngine(config=config, project_root=str(PROJECT_ROOT))
    sme.mutator.rng.seed(seed)
    sme.mutator.np_rng = np.random.default_rng(seed)

    pv = np.array([0.25, 0.35, 0.15, 0.25])

    t0 = time.time()
    result = sme.run(max_generations=max_gen, purpose_vector=pv, early_stop_fitness=0.95)
    elapsed = time.time() - t0

    fitness_traj = [g.get("best_fitness", 0.0) for g in result.get("generations", [])]

    out = {
        "mode": mode,
        "seed": seed,
        "initial_fitness": result.get("initial_fitness", 0.0),
        "final_fitness": result.get("final_fitness", 0.0),
        "fitness_improvement": result.get("fitness_improvement", 0.0),
        "acceptance_rate": result.get("total_mutations_accepted", 0) / max_gen,
        "fitness_trajectory": fitness_traj,
        "elapsed_seconds": elapsed,
    }

    if use_pareto:
        # 提取 Pareto HV 轨迹
        hv_traj = [
            g.get("pareto_archive_stats", {}).get("hypervolume", 0.0)
            for g in result.get("generations", [])
            if g.get("pareto_archive_stats")
        ]
        final_stats = None
        for g in reversed(result.get("generations", [])):
            if g.get("pareto_archive_stats"):
                final_stats = g["pareto_archive_stats"]
                break
        out["pareto"] = {
            "hypervolume_trajectory": hv_traj,
            "final_hv": final_stats.get("hypervolume", 0.0) if final_stats else 0.0,
            "final_archive_size": final_stats.get("size", 0) if final_stats else 0,
        }

    return out


# ═══════════════════════════════════════════════════════════════
# E1: v6.1 vs v6.2 对比
# ═══════════════════════════════════════════════════════════════

def run_e1_v62_comparison(n_trials: int, max_gen: int, base_seed: int) -> Dict:
    """E1: 语义引导 vs 随机变异"""
    logger.info(f"\n{'='*70}")
    logger.info("E1: v6.1(随机) vs v6.2(语义引导) — N={n_trials}, gen={max_gen}")
    logger.info(f"{'='*70}")

    seeds = [base_seed + i * 17 for i in range(n_trials)]
    results_random, results_semantic = [], []

    for i, seed in enumerate(seeds):
        logger.info(f"\n--- Trial {i+1}/{n_trials} ---")

        # Random (v6.1)
        r1 = run_v62_trial(seed=seed, enable_semantic=False, max_gen=max_gen)
        results_random.append(r1)
        logger.info(f"  Random: Δfit={r1['fitness_improvement']:.4f}, accept={r1['acceptance_rate']:.0%}")
        restore_baseline(PROJECT_ROOT)

        # Semantic (v6.2)
        r2 = run_v62_trial(seed=seed, enable_semantic=True, max_gen=max_gen)
        results_semantic.append(r2)
        logger.info(f"  Semantic: Δfit={r2['fitness_improvement']:.4f}, accept={r2['acceptance_rate']:.0%}")
        restore_baseline(PROJECT_ROOT)

    # 统计分析
    fit_random = np.array([r["fitness_improvement"] for r in results_random])
    fit_semantic = np.array([r["fitness_improvement"] for r in results_semantic])
    acc_random = np.array([r["acceptance_rate"] for r in results_random])
    acc_semantic = np.array([r["acceptance_rate"] for r in results_semantic])

    fit_test = welch_ttest(fit_semantic, fit_random)
    acc_test = welch_ttest(acc_semantic, acc_random)

    fit_ci = bootstrap_ci(fit_semantic)
    acc_ci = bootstrap_ci(acc_semantic)

    result = {
        "experiment": "E1_v62_semantic_vs_random",
        "n_trials": n_trials,
        "max_gen": max_gen,
        "base_seed": base_seed,
        "results_random": results_random,
        "results_semantic": results_semantic,
        "analysis": {
            "fitness": {
                "random": descriptive_stats(fit_random.tolist()),
                "semantic": descriptive_stats(fit_semantic.tolist()),
                "relative_improvement_pct": float(
                    (fit_semantic.mean() - fit_random.mean()) / (abs(fit_random.mean()) + 1e-8) * 100
                ),
                "welch_ttest": fit_test,
                "bootstrap_ci": fit_ci,
            },
            "acceptance_rate": {
                "random": descriptive_stats(acc_random.tolist()),
                "semantic": descriptive_stats(acc_semantic.tolist()),
                "welch_ttest": acc_test,
                "bootstrap_ci": acc_ci,
            },
        },
    }

    _print_e1_summary(result)
    return result


def _print_e1_summary(result: Dict):
    a = result["analysis"]
    print(f"\n{'='*75}")
    print("E1: v6.1 vs v6.2 统计验证结果")
    print(f"{'='*75}")

    fi = a["fitness"]
    print(f"\n  Δfitness:")
    print(f"    Random:    {fi['random']['mean']:.4f} ± {fi['random']['std']:.4f}")
    print(f"    Semantic:  {fi['semantic']['mean']:.4f} ± {fi['semantic']['std']:.4f}")
    print(f"    相对提升:  {fi['relative_improvement_pct']:+.1f}%")
    t = fi["welch_ttest"]
    print(f"    Welch t:   t={t['t_stat']:.3f}, p={t['p_value']:.4f}, d={t['cohens_d']:.3f}"
          f"  {'✅ p<0.05' if t['significant_005'] else '❌'}")
    ci = fi["bootstrap_ci"]
    print(f"    Bootstrap 95% CI: [{ci['ci_lower']:.4f}, {ci['ci_upper']:.4f}]")

    ai = a["acceptance_rate"]
    print(f"\n  Acceptance Rate:")
    print(f"    Random:    {ai['random']['mean']:.1%} ± {ai['random']['std']:.1%}")
    print(f"    Semantic:  {ai['semantic']['mean']:.1%} ± {ai['semantic']['std']:.1%}")
    t2 = ai["welch_ttest"]
    print(f"    Welch t:   t={t2['t_stat']:.3f}, p={t2['p_value']:.4f}"
          f"  {'✅ p<0.05' if t2['significant_005'] else '❌'}")

    print(f"{'='*75}")


# ═══════════════════════════════════════════════════════════════
# E2: v6.2 vs v6.3 对比
# ═══════════════════════════════════════════════════════════════

def run_e2_v63_comparison(n_trials: int, max_gen: int, base_seed: int) -> Dict:
    """E2: 标量 vs Pareto 多目标"""
    logger.info(f"\n{'='*70}")
    logger.info("E2: v6.2(标量) vs v6.3(Pareto) — N={n_trials}, gen={max_gen}")
    logger.info(f"{'='*70}")

    seeds = [base_seed + i * 23 for i in range(n_trials)]
    results_scalar, results_pareto = [], []

    for i, seed in enumerate(seeds):
        logger.info(f"\n--- Trial {i+1}/{n_trials} ---")

        # Scalar (v6.2)
        r1 = run_v63_trial(seed=seed, use_pareto=False, max_gen=max_gen)
        results_scalar.append(r1)
        logger.info(f"  Scalar: Δfit={r1['fitness_improvement']:.4f}, accept={r1['acceptance_rate']:.0%}")
        restore_baseline(PROJECT_ROOT)

        # Pareto (v6.3)
        r2 = run_v63_trial(seed=seed, use_pareto=True, max_gen=max_gen)
        results_pareto.append(r2)
        pareto_info = r2.get("pareto", {})
        logger.info(f"  Pareto: Δfit={r2['fitness_improvement']:.4f}, accept={r2['acceptance_rate']:.0%}"
                    f", HV={pareto_info.get('final_hv', 0):.4f}")
        restore_baseline(PROJECT_ROOT)

    # 统计分析
    fit_scalar = np.array([r["fitness_improvement"] for r in results_scalar])
    fit_pareto = np.array([r["fitness_improvement"] for r in results_pareto])
    acc_scalar = np.array([r["acceptance_rate"] for r in results_scalar])
    acc_pareto = np.array([r["acceptance_rate"] for r in results_pareto])
    hv_values = np.array([r.get("pareto", {}).get("final_hv", 0.0) for r in results_pareto])

    fit_test = welch_ttest(fit_pareto, fit_scalar)
    acc_test = welch_ttest(acc_pareto, acc_scalar)
    hv_ci = bootstrap_ci(hv_values.tolist())

    result = {
        "experiment": "E2_v63_pareto_vs_scalar",
        "n_trials": n_trials,
        "max_gen": max_gen,
        "base_seed": base_seed,
        "results_scalar": results_scalar,
        "results_pareto": results_pareto,
        "analysis": {
            "fitness": {
                "scalar": descriptive_stats(fit_scalar.tolist()),
                "pareto": descriptive_stats(fit_pareto.tolist()),
                "relative_improvement_pct": float(
                    (fit_pareto.mean() - fit_scalar.mean()) / (abs(fit_scalar.mean()) + 1e-8) * 100
                ),
                "welch_ttest": fit_test,
            },
            "acceptance_rate": {
                "scalar": descriptive_stats(acc_scalar.tolist()),
                "pareto": descriptive_stats(acc_pareto.tolist()),
                "welch_ttest": acc_test,
            },
            "hypervolume": {
                "stats": descriptive_stats(hv_values.tolist()),
                "bootstrap_ci": hv_ci,
            },
        },
    }

    _print_e2_summary(result)
    return result


def _print_e2_summary(result: Dict):
    a = result["analysis"]
    print(f"\n{'='*75}")
    print("E2: v6.2 vs v6.3 统计验证结果")
    print(f"{'='*75}")

    fi = a["fitness"]
    print(f"\n  Δfitness:")
    print(f"    Scalar:  {fi['scalar']['mean']:.4f} ± {fi['scalar']['std']:.4f}")
    print(f"    Pareto:  {fi['pareto']['mean']:.4f} ± {fi['pareto']['std']:.4f}")
    print(f"    相对提升: {fi['relative_improvement_pct']:+.1f}%")
    t = fi["welch_ttest"]
    print(f"    Welch t:  t={t['t_stat']:.3f}, p={t['p_value']:.4f}, d={t['cohens_d']:.3f}"
          f"  {'✅ p<0.05' if t['significant_005'] else '❌'}")

    ai = a["acceptance_rate"]
    t2 = ai["welch_ttest"]
    print(f"\n  Acceptance Rate:")
    print(f"    Scalar:  {ai['scalar']['mean']:.1%} ± {ai['scalar']['std']:.1%}")
    print(f"    Pareto:  {ai['pareto']['mean']:.1%} ± {ai['pareto']['std']:.1%}")
    print(f"    Welch t:  t={t2['t_stat']:.3f}, p={t2['p_value']:.4f}"
          f"  {'✅ p<0.05' if t2['significant_005'] else '❌'}")

    hv = a["hypervolume"]
    if hv["stats"]["n"] > 0:
        ci = hv["bootstrap_ci"]
        print(f"\n  Hypervolume (Pareto only):")
        print(f"    Mean: {hv['stats']['mean']:.4f} ± {hv['stats']['std']:.4f}")
        print(f"    95% CI: [{ci['ci_lower']:.4f}, {ci['ci_upper']:.4f}]")

    print(f"{'='*75}")


# ═══════════════════════════════════════════════════════════════
# E3: v7.0 Meta-SME 稳定性
# ═══════════════════════════════════════════════════════════════

def restore_sme_from_backup(project_root: Path):
    """恢复SME到最早备份"""
    backup_dir = project_root / "experiments" / "meta_sme" / "backups"
    sme_path = project_root / "moss" / "core" / "self_modification_engine.py"
    backups = sorted(backup_dir.glob("sme_gen1_*.py"))
    if backups:
        original = backups[0].read_text(encoding="utf-8")
        sme_path.write_text(original, encoding="utf-8")
        logger.info(f"  [Restore] SME from {backups[0].name}")


def run_e3_meta_sme_stability(n_trials: int, max_gen: int, base_seed: int) -> Dict:
    """E3: Meta-SME 重复验证"""
    logger.info(f"\n{'='*70}")
    logger.info(f"E3: v7.0 Meta-SME 稳定性 — N={n_trials}, gen={max_gen}")
    logger.info(f"{'='*70}")

    seeds = [base_seed + i * 31 for i in range(n_trials)]
    results = []

    for i, seed in enumerate(seeds):
        logger.info(f"\n--- Trial {i+1}/{n_trials} (seed={seed}) ---")

        np.random.seed(seed)
        from moss.core.self_modification_engine import MetaSME

        meta_sme = MetaSME(project_root=str(PROJECT_ROOT))
        meta_sme.meta_mutator.rng = __import__("random").Random(seed)

        t0 = time.time()
        result = meta_sme.run_meta_evolution(max_generations=max_gen)
        elapsed = time.time() - t0

        r = {
            "seed": seed,
            "initial_meta_fitness": result.get("initial_meta_fitness", 0.0),
            "final_meta_fitness": result.get("final_meta_fitness", 0.0),
            "meta_fitness_improvement": result.get("meta_fitness_improvement", 0.0),
            "meta_acceptance_rate": result.get("meta_acceptance_rate", 0.0),
            "meta_mutations_accepted": result.get("total_meta_mutations_accepted", 0),
            "elapsed_seconds": elapsed,
        }
        results.append(r)
        logger.info(f"  Meta-fitness: {r['initial_meta_fitness']:.4f} → {r['final_meta_fitness']:.4f}"
                    f" (+{r['meta_fitness_improvement']:.4f})")
        logger.info(f"  Accept rate: {r['meta_acceptance_rate']:.0%}, time: {elapsed:.1f}s")

        # 恢复SME
        restore_sme_from_backup(PROJECT_ROOT)

    # 统计分析
    improvements = np.array([r["meta_fitness_improvement"] for r in results])
    accept_rates = np.array([r["meta_acceptance_rate"] for r in results])

    imp_ci = bootstrap_ci(improvements.tolist())
    acc_ci = bootstrap_ci(accept_rates.tolist())

    # 检验：Meta-fitness提升是否显著大于0
    # One-sample t-test: H0: μ=0
    if len(improvements) >= 2:
        t_stat = np.mean(improvements) / (np.std(improvements, ddof=1) / np.sqrt(len(improvements)))
        from math import erfc, sqrt
        p_value = erfc(abs(t_stat) / sqrt(2))
        one_sample_test = {
            "t_stat": float(t_stat),
            "p_value": float(p_value),
            "significant_005": p_value < 0.05,
        }
    else:
        one_sample_test = {"t_stat": 0.0, "p_value": 1.0, "significant_005": False}

    result = {
        "experiment": "E3_meta_sme_stability",
        "n_trials": n_trials,
        "max_gen": max_gen,
        "base_seed": base_seed,
        "results": results,
        "analysis": {
            "meta_fitness_improvement": {
                "stats": descriptive_stats(improvements.tolist()),
                "bootstrap_ci": imp_ci,
                "one_sample_ttest": one_sample_test,
                "positive_rate": float(np.mean(improvements > 0)),
            },
            "meta_acceptance_rate": {
                "stats": descriptive_stats(accept_rates.tolist()),
                "bootstrap_ci": acc_ci,
            },
        },
    }

    _print_e3_summary(result)
    return result


def _print_e3_summary(result: Dict):
    a = result["analysis"]
    print(f"\n{'='*75}")
    print("E3: v7.0 Meta-SME 稳定性验证结果")
    print(f"{'='*75}")

    mi = a["meta_fitness_improvement"]
    ci = mi["bootstrap_ci"]
    t = mi["one_sample_ttest"]
    print(f"\n  Meta-fitness Δ:")
    print(f"    Mean:  {mi['stats']['mean']:.4f} ± {mi['stats']['std']:.4f}")
    print(f"    Range: [{mi['stats']['min']:.4f}, {mi['stats']['max']:.4f}]")
    print(f"    95% CI: [{ci['ci_lower']:.4f}, {ci['ci_upper']:.4f}]")
    print(f"    Positive rate: {mi['positive_rate']:.0%}")
    print(f"    One-sample t: t={t['t_stat']:.3f}, p={t['p_value']:.4f}"
          f"  {'✅ 显著>0' if t['significant_005'] else '❌'}")

    ar = a["meta_acceptance_rate"]
    print(f"\n  Meta Accept Rate:")
    print(f"    Mean:  {ar['stats']['mean']:.1%} ± {ar['stats']['std']:.1%}")

    print(f"{'='*75}")


# ═══════════════════════════════════════════════════════════════
# 综合报告
# ═══════════════════════════════════════════════════════════════

def generate_summary(all_results: List[Dict]) -> Dict:
    """生成 Phase 2 综合报告"""
    print(f"\n\n{'#'*80}")
    print("  Phase 2 统计验证 — 综合报告")
    print(f"{'#'*80}")

    summary = {
        "phase": "Phase 2 Statistical Validation",
        "timestamp": datetime.now().isoformat(),
        "experiments": {},
        "conclusions": [],
    }

    for r in all_results:
        exp_name = r["experiment"]
        summary["experiments"][exp_name] = {
            "n_trials": r["n_trials"],
            "max_gen": r["max_gen"],
            "analysis": r["analysis"],
        }

        # 提取关键结论
        if "E1" in exp_name:
            fit_test = r["analysis"]["fitness"]["welch_ttest"]
            acc_test = r["analysis"]["acceptance_rate"]["welch_ttest"]
            if fit_test["significant_005"] and acc_test["significant_005"]:
                summary["conclusions"].append(
                    f"✅ E1: 语义引导变异在fitness和接受率上均显著优于随机(p<0.05, d={fit_test['cohens_d']:.2f})"
                )
            else:
                summary["conclusions"].append(
                    f"⚠️ E1: 语义引导变异部分显著 (fitness p={fit_test['p_value']:.3f}, accept p={acc_test['p_value']:.3f})"
                )

        elif "E2" in exp_name:
            fit_test = r["analysis"]["fitness"]["welch_ttest"]
            if fit_test["significant_005"]:
                summary["conclusions"].append(
                    f"✅ E2: Pareto多目标显著优于标量(p<0.05, d={fit_test['cohens_d']:.2f})"
                )
            else:
                summary["conclusions"].append(
                    f"⚠️ E2: Pareto vs 标量差异不显著 (p={fit_test['p_value']:.3f})"
                )

        elif "E3" in exp_name:
            t = r["analysis"]["meta_fitness_improvement"]["one_sample_ttest"]
            pr = r["analysis"]["meta_fitness_improvement"]["positive_rate"]
            if t["significant_005"]:
                summary["conclusions"].append(
                    f"✅ E3: Meta-SME的Meta-fitness提升显著>0(p<0.05), {pr:.0%}次为正"
                )
            else:
                summary["conclusions"].append(
                    f"⚠️ E3: Meta-fitness提升不稳定 (p={t['p_value']:.3f}, positive rate={pr:.0%})"
                )

    print("\n关键结论:")
    for i, c in enumerate(summary["conclusions"], 1):
        print(f"  {i}. {c}")

    n_sig = sum(1 for c in summary["conclusions"] if c.startswith("✅"))
    n_total = len(summary["conclusions"])
    print(f"\n  总计: {n_sig}/{n_total} 项实验达到统计显著(p<0.05)")

    return summary


# ═══════════════════════════════════════════════════════════════
# JSON 序列化 & 保存
# ═══════════════════════════════════════════════════════════════

def json_encoder(obj):
    if isinstance(obj, (np.integer, np.floating)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, np.bool_):
        return bool(obj)
    raise TypeError(type(obj))


def save_results(all_results: List[Dict], summary: Dict) -> Path:
    output_dir = PROJECT_ROOT / "experiments" / "statistical_validation"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 保存完整数据
    data_path = output_dir / f"validation_data_{timestamp}.json"
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, default=json_encoder, ensure_ascii=False)
    logger.info(f"[Save] 完整数据: {data_path}")

    # 保存综合报告
    report_path = output_dir / f"validation_report_{timestamp}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=json_encoder, ensure_ascii=False)
    logger.info(f"[Save] 综合报告: {report_path}")

    return report_path


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MOSS Phase 2: 统计验证")
    parser.add_argument("--trials", type=int, default=5, help="每组重复次数（默认5）")
    parser.add_argument("--generations", type=int, default=30, help="每trial代数（默认30）")
    parser.add_argument("--seed", type=int, default=42, help="基础种子")
    parser.add_argument("--quick", action="store_true", help="快速模式（N=2, 20代）")
    parser.add_argument("--exp", choices=["e1", "e2", "e3", "all"], default="all",
                        help="运行哪个实验（默认全部）")
    args = parser.parse_args()

    n_trials = 2 if args.quick else args.trials
    max_gen = 20 if args.quick else args.generations
    e3_gen = 10 if args.quick else max_gen  # E3 用更少代数节省时间

    logger.info(f"\n{'#'*70}")
    logger.info("MOSS Phase 2: 统计验证")
    logger.info(f"  trials={n_trials}, generations={max_gen}, seed={args.seed}, exp={args.exp}")
    logger.info(f"{'#'*70}")

    all_results = []

    try:
        if args.exp in ("e1", "all"):
            r = run_e1_v62_comparison(n_trials=n_trials, max_gen=max_gen, base_seed=args.seed)
            all_results.append(r)

        if args.exp in ("e2", "all"):
            r = run_e2_v63_comparison(n_trials=n_trials, max_gen=max_gen, base_seed=args.seed + 100)
            all_results.append(r)

        if args.exp in ("e3", "all"):
            r = run_e3_meta_sme_stability(n_trials=n_trials, max_gen=e3_gen,
                                           base_seed=args.seed + 200)
            all_results.append(r)

        # 生成综合报告
        summary = generate_summary(all_results)
        report_path = save_results(all_results, summary)

        print(f"\n\n✅ Phase 2 统计验证完成！")
        print(f"   报告: {report_path.name}")

    except KeyboardInterrupt:
        logger.warning("用户中断实验")
        sys.exit(1)
    except Exception as e:
        logger.error(f"实验失败: {e}", exc_info=True)
        sys.exit(1)
