"""
MOSS v6.3 Pareto多目标优化 vs v6.2标量优化 对比实验
=====================================================

实验设计：
- 控制组 (A)：v6.2标量fitness（use_pareto=False）
- 实验组 (B)：v6.3 Pareto多目标（use_pareto=True）
- 各组进化30代，分析：
  - 标量fitness提升（可比性）
  - Pareto前沿大小（多样性）
  - 超体积指标（HV）
  - 各维度极值策略

Author: MOSS Project
Date: 2026-04-16
"""

import json
import sys
import os
import time
import logging
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
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


def restore_baseline(project_root: Path):
    """恢复unified_agent.py到最早备份"""
    backup_dir = project_root / "experiments" / "self_modification"
    target = project_root / "moss" / "core" / "unified_agent.py"
    backups = sorted(backup_dir.glob("backup_gen1_*.py"))
    if backups:
        src = backups[0].read_text(encoding="utf-8")
        target.write_text(src, encoding="utf-8")
        logger.info(f"  [Restore] unified_agent.py from {backups[0].name}")
    else:
        logger.warning("  [Restore] No gen1 backup found")


def run_scalar_trial(seed: int, max_gen: int = 30) -> Dict:
    """v6.2标量模式（含语义引导，不含Pareto）"""
    from moss.core.self_modification_engine import SelfModificationEngine, SMEConfig

    logger.info(f"\n[Scalar] seed={seed}, max_gen={max_gen}")
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
        use_pareto=False,
        enable_hot_reload=False,
    )
    sme = SelfModificationEngine(config=config, project_root=str(PROJECT_ROOT))
    sme.mutator.rng.seed(seed)

    pv = np.array([0.25, 0.35, 0.15, 0.25])  # 偏多样性+涌现

    t0 = time.time()
    result = sme.run(max_generations=max_gen, purpose_vector=pv, early_stop_fitness=0.95)
    elapsed = time.time() - t0

    fitness_traj = [g.get("best_fitness", 0.0) for g in result.get("generations", [])]

    return {
        "mode": "scalar",
        "seed": seed,
        "initial_fitness": result.get("initial_fitness", 0.0),
        "final_fitness": result.get("final_fitness", 0.0),
        "fitness_improvement": result.get("fitness_improvement", 0.0),
        "total_mutations_accepted": result.get("total_mutations_accepted", 0),
        "acceptance_rate": result.get("total_mutations_accepted", 0) / max_gen,
        "fitness_trajectory": fitness_traj,
        "elapsed_seconds": elapsed,
        "pareto_stats": None,
    }


def run_pareto_trial(seed: int, max_gen: int = 30) -> Dict:
    """v6.3 Pareto多目标模式"""
    from moss.core.self_modification_engine import SelfModificationEngine, SMEConfig

    logger.info(f"\n[Pareto] seed={seed}, max_gen={max_gen}")
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
        use_pareto=True,
        pareto_archive_size=50,
        enable_hot_reload=False,
    )
    sme = SelfModificationEngine(config=config, project_root=str(PROJECT_ROOT))
    sme.mutator.rng.seed(seed)

    pv = np.array([0.25, 0.35, 0.15, 0.25])

    t0 = time.time()
    result = sme.run(max_generations=max_gen, purpose_vector=pv, early_stop_fitness=0.95)
    elapsed = time.time() - t0

    fitness_traj = [g.get("best_fitness", 0.0) for g in result.get("generations", [])]

    # 收集Pareto档案统计
    pareto_stats_per_gen = [
        g.get("pareto_archive_stats") for g in result.get("generations", [])
        if g.get("pareto_archive_stats") is not None
    ]
    final_pareto_stats = pareto_stats_per_gen[-1] if pareto_stats_per_gen else {}
    hv_trajectory = [
        s.get("hypervolume", 0.0) for s in pareto_stats_per_gen
    ]

    return {
        "mode": "pareto",
        "seed": seed,
        "initial_fitness": result.get("initial_fitness", 0.0),
        "final_fitness": result.get("final_fitness", 0.0),
        "fitness_improvement": result.get("fitness_improvement", 0.0),
        "total_mutations_accepted": result.get("total_mutations_accepted", 0),
        "acceptance_rate": result.get("total_mutations_accepted", 0) / max_gen,
        "fitness_trajectory": fitness_traj,
        "elapsed_seconds": elapsed,
        "pareto_stats": {
            "final_archive_size": final_pareto_stats.get("size", 0),
            "final_hypervolume": final_pareto_stats.get("hypervolume", 0.0),
            "hypervolume_trajectory": hv_trajectory,
            "final_stats": final_pareto_stats,
            "dimension_maxes": final_pareto_stats.get("dimension_maxes", {}),
        },
    }


def run_pareto_experiment(n_trials: int = 3, max_gen: int = 30, base_seed: int = 42) -> Dict:
    """
    v6.2标量 vs v6.3 Pareto 完整对比实验
    """
    logger.info(f"\n{'#'*70}")
    logger.info("MOSS v6.3 Pareto多目标 vs v6.2标量 对比实验")
    logger.info(f"  trials={n_trials}, max_gen={max_gen}, base_seed={base_seed}")
    logger.info(f"{'#'*70}")

    seeds = [base_seed + i * 13 for i in range(n_trials)]
    results_scalar = []
    results_pareto = []

    for i, seed in enumerate(seeds):
        logger.info(f"\n--- 轮次 {i+1}/{n_trials} (seed={seed}) ---")

        # A组：标量
        r_scalar = run_scalar_trial(seed=seed, max_gen=max_gen)
        results_scalar.append(r_scalar)
        logger.info(f"  [Scalar] fitness +{r_scalar['fitness_improvement']:.4f}, "
                    f"accept={r_scalar['acceptance_rate']:.0%}")
        restore_baseline(PROJECT_ROOT)

        # B组：Pareto
        r_pareto = run_pareto_trial(seed=seed, max_gen=max_gen)
        results_pareto.append(r_pareto)
        ps = r_pareto.get("pareto_stats", {}) or {}
        logger.info(f"  [Pareto] fitness +{r_pareto['fitness_improvement']:.4f}, "
                    f"accept={r_pareto['acceptance_rate']:.0%}, "
                    f"archive_size={ps.get('final_archive_size', 0)}, "
                    f"HV={ps.get('final_hypervolume', 0.0):.4f}")
        restore_baseline(PROJECT_ROOT)

    # ── 统计分析 ──
    def stats(results, key, sub=None):
        vals = [r[key] if sub is None else (r[key] or {}).get(sub, 0.0)
                for r in results]
        return {
            "mean": float(np.mean(vals)),
            "std": float(np.std(vals)),
            "values": vals,
        }

    analysis = {
        "scalar": {
            "fitness_improvement": stats(results_scalar, "fitness_improvement"),
            "acceptance_rate": stats(results_scalar, "acceptance_rate"),
        },
        "pareto": {
            "fitness_improvement": stats(results_pareto, "fitness_improvement"),
            "acceptance_rate": stats(results_pareto, "acceptance_rate"),
            "archive_size": stats(results_pareto, "pareto_stats", "final_archive_size"),
            "hypervolume": stats(results_pareto, "pareto_stats", "final_hypervolume"),
        },
    }

    _print_pareto_summary(analysis, results_pareto)

    return {
        "experiment_id": f"v63_pareto_{datetime.now():%Y%m%d_%H%M%S}",
        "config": {"n_trials": n_trials, "max_gen": max_gen, "base_seed": base_seed},
        "results_scalar": results_scalar,
        "results_pareto": results_pareto,
        "analysis": analysis,
    }


def _print_pareto_summary(analysis: Dict, results_pareto: List[Dict]):
    """打印Pareto实验摘要"""
    print("\n" + "=" * 75)
    print("MOSS v6.3 Pareto多目标 vs v6.2标量 实验结果")
    print("=" * 75)

    sc = analysis["scalar"]
    pa = analysis["pareto"]

    rows = [
        ("Δfitness (mean±std)",
         f"{sc['fitness_improvement']['mean']:.4f}±{sc['fitness_improvement']['std']:.4f}",
         f"{pa['fitness_improvement']['mean']:.4f}±{pa['fitness_improvement']['std']:.4f}"),
        ("接受率 (mean±std)",
         f"{sc['acceptance_rate']['mean']:.1%}±{sc['acceptance_rate']['std']:.1%}",
         f"{pa['acceptance_rate']['mean']:.1%}±{pa['acceptance_rate']['std']:.1%}"),
        ("Pareto档案大小 (final)",
         "N/A",
         f"{pa['archive_size']['mean']:.1f}±{pa['archive_size']['std']:.1f}"),
        ("超体积HV (final)",
         "N/A",
         f"{pa['hypervolume']['mean']:.4f}±{pa['hypervolume']['std']:.4f}"),
    ]

    print(f"{'指标':<30} {'v6.2标量':>20} {'v6.3 Pareto':>20}")
    print("-" * 75)
    for name, v_sc, v_pa in rows:
        print(f"{name:<30} {v_sc:>20} {v_pa:>20}")
    print("=" * 75)

    # 打印最后一轮Pareto各维度极值
    if results_pareto:
        last = results_pareto[-1]
        ps = last.get("pareto_stats", {}) or {}
        dm = ps.get("dimension_maxes", {})
        if dm:
            print("\nPareto前沿各维度极值（最后轮次）:")
            for dim, val in dm.items():
                print(f"  max_{dim}: {val:.4f}")
    print()


def save_results(result: Dict, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    fname = f"v63_pareto_{datetime.now():%Y%m%d_%H%M%S}.json"
    fpath = output_dir / fname

    def enc(obj):
        if isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(type(obj))

    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=enc, ensure_ascii=False)
    logger.info(f"[Save] {fpath}")
    return fpath


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MOSS v6.3 Pareto实验")
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--generations", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--quick", action="store_true", help="快速模式：1 trial, 20 gen")
    args = parser.parse_args()

    n_trials = 1 if args.quick else args.trials
    max_gen = 20 if args.quick else args.generations

    result = run_pareto_experiment(
        n_trials=n_trials,
        max_gen=max_gen,
        base_seed=args.seed
    )

    out_dir = PROJECT_ROOT / "experiments" / "self_modification"
    saved = save_results(result, out_dir)
    print(f"\nDone. Saved to: {saved}")
