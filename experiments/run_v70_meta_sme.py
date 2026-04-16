"""
MOSS v7.0 Meta-SME 自改写引擎实验脚本
========================================

让 self_modification_engine.py 改写自己（Meta层级自改写）。

实验设计：
- MetaSME运行50代，每代尝试4个保守变异
- 安全保障：元不可变清单 + 双重沙箱 + 自动回滚
- 观察SME引擎参数如何自适应优化

Author: MOSS Project
Date: 2026-04-16
"""

import sys
import json
import logging
import time
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


def restore_sme_from_backup(project_root: Path):
    """
    实验前/后恢复SME引擎到git最新版本（通过最早meta备份）

    如果没有meta备份，使用git checkout恢复
    """
    backup_dir = project_root / "experiments" / "meta_sme" / "backups"
    sme_path = project_root / "moss" / "core" / "self_modification_engine.py"

    backups = sorted(backup_dir.glob("sme_gen1_*.py"))
    if backups:
        original = backups[0].read_text(encoding="utf-8")
        sme_path.write_text(original, encoding="utf-8")
        logger.info(f"[Restore] SME engine restored from {backups[0].name}")
    else:
        logger.info("[Restore] No backup found - using current SME version")


def run_meta_experiment(max_gen: int = 50, quick: bool = False) -> dict:
    """
    运行Meta-SME进化实验

    Args:
        max_gen: 最大代数（推荐50）
        quick: 快速模式（10代，验证流程）
    """
    if quick:
        max_gen = 10
        logger.info("快速模式：10代Meta进化")

    logger.info(f"\n{'#'*70}")
    logger.info("MOSS v7.0 Meta-SME 自改写引擎实验")
    logger.info(f"  目标: self_modification_engine.py 自改写自己")
    logger.info(f"  max_generations={max_gen}")
    logger.info(f"{'#'*70}")

    # 导入MetaSME
    from moss.core.self_modification_engine import MetaSME

    meta_sme = MetaSME(project_root=str(PROJECT_ROOT))

    # 运行Meta进化
    t0 = time.time()
    result = meta_sme.run_meta_evolution(max_generations=max_gen)
    elapsed = time.time() - t0

    logger.info(f"\n实验完成，总耗时: {elapsed:.1f}s")
    logger.info(
        f"Meta-fitness: {result.get('initial_meta_fitness', 0):.4f} → "
        f"{result.get('final_meta_fitness', 0):.4f} "
        f"(+{result.get('meta_fitness_improvement', 0):.4f})"
    )
    logger.info(
        f"Meta接受率: {result.get('total_meta_mutations_accepted', 0)}/{max_gen} "
        f"({result.get('meta_acceptance_rate', 0):.1%})"
    )

    return result


def analyze_meta_result(result: dict):
    """分析Meta-SME实验结果"""
    print("\n" + "=" * 70)
    print("Meta-SME 实验结果深度分析")
    print("=" * 70)

    gens = result.get("meta_generations", [])
    if not gens:
        print("无代数数据")
        return

    # 提取接受轨迹
    accepted_gens = [g for g in gens if g.get("accepted")]
    rejected_gens = [g for g in gens if not g.get("accepted")]

    print(f"总代数: {len(gens)}")
    print(f"接受: {len(accepted_gens)} ({len(accepted_gens)/len(gens):.1%})")
    print(f"拒绝: {len(rejected_gens)} ({len(rejected_gens)/len(gens):.1%})")
    print()

    # 接受的变异类型分布
    accepted_types = [g.get("mutation_type", "?") for g in accepted_gens]
    if accepted_types:
        from collections import Counter
        type_dist = Counter(accepted_types)
        print("接受变异类型分布:")
        for t, c in type_dist.most_common():
            print(f"  {t}: {c}次 ({c/len(accepted_gens):.1%})")
        print()

    # Meta-fitness提升轨迹
    fitness_traj = [g.get("baseline_meta_fitness", 0) for g in gens]
    if fitness_traj:
        print(f"Meta-fitness轨迹:")
        print(f"  起始: {fitness_traj[0]:.4f}")
        print(f"  最终: {fitness_traj[-1]:.4f}")
        print(f"  最高: {max(fitness_traj):.4f} (代{fitness_traj.index(max(fitness_traj))+1})")
        print(f"  改善代次: {sum(1 for i in range(1,len(fitness_traj)) if fitness_traj[i] > fitness_traj[i-1])}")
        print()

    print(f"总体Meta-fitness提升: {result.get('meta_fitness_improvement', 0):+.4f}")
    print("=" * 70)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MOSS v7.0 Meta-SME实验")
    parser.add_argument("--generations", type=int, default=50, help="Meta进化代数（默认50）")
    parser.add_argument("--quick", action="store_true", help="快速模式（10代）")
    args = parser.parse_args()

    try:
        result = run_meta_experiment(max_gen=args.generations, quick=args.quick)
        analyze_meta_result(result)

        # 恢复SME到原始状态（实验后）
        logger.info("\n实验后恢复SME到备份版本...")
        restore_sme_from_backup(PROJECT_ROOT)

        print(f"\n✅ Meta-SME实验完成！")

    except KeyboardInterrupt:
        logger.warning("用户中断，尝试恢复SME...")
        restore_sme_from_backup(PROJECT_ROOT)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Meta-SME实验失败: {e}", exc_info=True)
        restore_sme_from_backup(PROJECT_ROOT)
        sys.exit(1)
