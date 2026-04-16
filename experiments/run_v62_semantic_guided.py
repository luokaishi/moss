"""
MOSS v6.2 语义引导变异 vs v6.1随机变异 对比实验
=====================================================

实验设计：
- 控制组 (A)：v6.1随机变异（enable_semantic_guidance=False）
- 实验组 (B)：v6.2语义引导变异（enable_semantic_guidance=True）
- 各组进化30代，相同seed确保公平对比
- 重复3次取平均，计算统计显著性

关键指标：
- fitness提升幅度（Δfitness）
- 变异接受率（acceptance_rate）
- 变异类型分布（entropy of mutation_type distribution）
- 各代fitness轨迹

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
from copy import deepcopy

# ── 路径修复 ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ── 设置日志 ──
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def run_single_trial(
    trial_id: int,
    seed: int,
    enable_semantic: bool,
    max_generations: int = 30,
    purpose_vector: Optional[np.ndarray] = None
) -> Dict:
    """
    运行单次进化实验

    Args:
        trial_id: 实验序号
        seed: 随机种子
        enable_semantic: 是否启用语义引导（True=v6.2，False=v6.1）
        max_generations: 最大进化代数
        purpose_vector: 目的向量（用于语义引导）

    Returns:
        实验结果字典
    """
    from moss.core.self_modification_engine import (
        SelfModificationEngine, SMEConfig
    )

    mode = "semantic" if enable_semantic else "random"
    logger.info(f"\n{'='*60}")
    logger.info(f"Trial {trial_id} | Mode={mode} | Seed={seed}")
    logger.info(f"{'='*60}")

    # 设置随机种子
    np.random.seed(seed)

    config = SMEConfig(
        target_module="moss.core.unified_agent",
        population_size=6,
        max_generations=max_generations,
        acceptance_threshold=-0.002,
        enable_structural_mutations=True,
        mutation_intensity=0.3,
        use_real_emergence=True,
        # v6.2 语义引导开关
        enable_semantic_guidance=enable_semantic,
        semantic_temperature=1.5,
        semantic_exploration_bonus=0.1,
        # 禁用热重载（实验环境保持稳定）
        enable_hot_reload=False,
        output_dir="experiments/self_modification"
    )

    sme = SelfModificationEngine(
        config=config,
        project_root=str(PROJECT_ROOT)
    )

    # 设置mutator的随机种子
    sme.mutator.rng.seed(seed)
    sme.mutator.np_rng = np.random.default_rng(seed)

    start_time = time.time()

    # 运行进化
    result = sme.run(
        max_generations=max_generations,
        purpose_vector=purpose_vector,
        early_stop_fitness=0.95
    )

    elapsed = time.time() - start_time

    # 统计变异类型分布
    mutation_types_all = []
    for summary in result.get('generations', []):
        mtype = summary.get('mutation_type', 'no_op')
        if mtype != 'no_op':
            mutation_types_all.append(mtype)

    # 计算类型分布熵（多样性指标）
    if mutation_types_all:
        from collections import Counter
        counts = Counter(mutation_types_all)
        total = sum(counts.values())
        probs = np.array([c / total for c in counts.values()])
        mutation_diversity = float(-np.sum(probs * np.log2(probs + 1e-10)))
    else:
        mutation_diversity = 0.0

    trial_result = {
        'trial_id': trial_id,
        'mode': mode,
        'seed': seed,
        'enable_semantic_guidance': enable_semantic,
        'initial_fitness': result.get('initial_fitness', 0.0),
        'final_fitness': result.get('final_fitness', 0.0),
        'fitness_improvement': result.get('fitness_improvement', 0.0),
        'fitness_improvement_pct': result.get('fitness_improvement', 0.0) / max(result.get('initial_fitness', 1.0), 1e-6) * 100,
        'total_mutations_accepted': result.get('total_mutations_accepted', 0),
        'total_generations': result.get('total_generations', max_generations),
        'acceptance_rate': result.get('total_mutations_accepted', 0) / max_generations,
        'elapsed_seconds': elapsed,
        'mutation_type_distribution': mutation_types_all,
        'mutation_diversity_entropy': mutation_diversity,
        'fitness_trajectory': [
            g.get('best_fitness', 0.0) for g in result.get('generations', [])
        ]
    }

    logger.info(f"Trial {trial_id} [{mode}] 完成:")
    logger.info(f"  fitness: {trial_result['initial_fitness']:.4f} → {trial_result['final_fitness']:.4f} "
                f"(+{trial_result['fitness_improvement']:.4f}, {trial_result['fitness_improvement_pct']:.1f}%)")
    logger.info(f"  接受率: {trial_result['acceptance_rate']:.1%} "
                f"({trial_result['total_mutations_accepted']}/{max_generations})")
    logger.info(f"  变异多样性熵: {mutation_diversity:.3f}")
    logger.info(f"  耗时: {elapsed:.1f}s")

    return trial_result


def run_comparison_experiment(
    n_trials: int = 3,
    max_generations: int = 30,
    base_seed: int = 42
) -> Dict:
    """
    运行v6.1 vs v6.2完整对比实验

    Args:
        n_trials: 每组重复次数
        max_generations: 每次运行的最大代数
        base_seed: 基础随机种子

    Returns:
        完整实验结果
    """
    logger.info(f"\n{'#'*70}")
    logger.info("MOSS v6.2 语义引导变异 vs v6.1随机变异 对比实验")
    logger.info(f"  trials={n_trials}, max_generations={max_generations}, base_seed={base_seed}")
    logger.info(f"{'#'*70}")

    # 目的向量：均匀权重（代表中性偏好）
    # 在实际中可用agent的purpose_vector，这里用均匀向量模拟
    purpose_vector_uniform = np.array([0.25, 0.25, 0.25, 0.25])
    # 偏向多样性+涌现的目的向量（期望语义引导能更好利用）
    purpose_vector_diversity = np.array([0.15, 0.40, 0.20, 0.35])

    results_random = []    # v6.1 随机组
    results_semantic = []  # v6.2 语义引导组（均匀目的）
    results_guided = []    # v6.2 语义引导组（多样性偏向目的）

    seeds = [base_seed + i * 7 for i in range(n_trials)]

    for i, seed in enumerate(seeds):
        logger.info(f"\n--- 实验轮次 {i+1}/{n_trials} (seed={seed}) ---")

        # A组：v6.1随机（purpose_vector=None → 退化为随机）
        logger.info("运行 A组 [v6.1随机]...")
        r_random = run_single_trial(
            trial_id=i * 3 + 1,
            seed=seed,
            enable_semantic=False,
            max_generations=max_generations,
            purpose_vector=None
        )
        results_random.append(r_random)

        # 恢复原始文件（基于backup_gen0_xxx.py恢复，或不写入）
        # 注意：SME会备份+写入，为了公平对比需要在每次trial前重置
        # 实际上每次都从磁盘读取最新文件，所以如果A组改写了文件，B组会在新基础上跑
        # 为了独立性，我们让每次trial都在相同baseline上运行
        # → 使用enable_hot_reload=False并恢复备份
        _restore_backup_if_needed(PROJECT_ROOT, seed, i * 3 + 1)

        # B组：v6.2语义引导（均匀目的向量）
        logger.info("运行 B组 [v6.2语义引导-均匀目的]...")
        r_semantic = run_single_trial(
            trial_id=i * 3 + 2,
            seed=seed,
            enable_semantic=True,
            max_generations=max_generations,
            purpose_vector=purpose_vector_uniform
        )
        results_semantic.append(r_semantic)
        _restore_backup_if_needed(PROJECT_ROOT, seed, i * 3 + 2)

        # C组：v6.2语义引导（多样性偏向目的向量）
        logger.info("运行 C组 [v6.2语义引导-多样性偏向目的]...")
        r_guided = run_single_trial(
            trial_id=i * 3 + 3,
            seed=seed,
            enable_semantic=True,
            max_generations=max_generations,
            purpose_vector=purpose_vector_diversity
        )
        results_guided.append(r_guided)
        _restore_backup_if_needed(PROJECT_ROOT, seed, i * 3 + 3)

    # ── 统计分析 ──
    logger.info(f"\n{'='*70}")
    logger.info("统计分析结果")
    logger.info(f"{'='*70}")

    def stats(results: List[Dict], key: str) -> Dict:
        vals = [r[key] for r in results]
        return {
            'mean': float(np.mean(vals)),
            'std': float(np.std(vals)),
            'min': float(np.min(vals)),
            'max': float(np.max(vals)),
            'values': vals
        }

    analysis = {
        'v61_random': {
            'fitness_improvement': stats(results_random, 'fitness_improvement'),
            'fitness_improvement_pct': stats(results_random, 'fitness_improvement_pct'),
            'acceptance_rate': stats(results_random, 'acceptance_rate'),
            'mutation_diversity': stats(results_random, 'mutation_diversity_entropy'),
        },
        'v62_semantic_uniform': {
            'fitness_improvement': stats(results_semantic, 'fitness_improvement'),
            'fitness_improvement_pct': stats(results_semantic, 'fitness_improvement_pct'),
            'acceptance_rate': stats(results_semantic, 'acceptance_rate'),
            'mutation_diversity': stats(results_semantic, 'mutation_diversity_entropy'),
        },
        'v62_semantic_diversity': {
            'fitness_improvement': stats(results_guided, 'fitness_improvement'),
            'fitness_improvement_pct': stats(results_guided, 'fitness_improvement_pct'),
            'acceptance_rate': stats(results_guided, 'acceptance_rate'),
            'mutation_diversity': stats(results_guided, 'mutation_diversity_entropy'),
        }
    }

    # 计算相对提升（语义引导 vs 随机）
    base_fitness = analysis['v61_random']['fitness_improvement']['mean']
    for group_name, group_key in [
        ('v62_semantic_uniform', 'uniform'),
        ('v62_semantic_diversity', 'diversity')
    ]:
        group_fitness = analysis[group_name]['fitness_improvement']['mean']
        if base_fitness > 1e-6:
            relative_improvement = (group_fitness - base_fitness) / base_fitness * 100
        else:
            relative_improvement = 0.0
        analysis[group_name]['relative_improvement_vs_random_pct'] = relative_improvement

    # 打印摘要
    _print_summary(analysis)

    # 汇总结果
    full_result = {
        'experiment_id': f"v62_comparison_{datetime.now():%Y%m%d_%H%M%S}",
        'config': {
            'n_trials': n_trials,
            'max_generations': max_generations,
            'base_seed': base_seed,
            'purpose_vector_uniform': purpose_vector_uniform.tolist(),
            'purpose_vector_diversity': purpose_vector_diversity.tolist(),
        },
        'results_random': results_random,
        'results_semantic_uniform': results_semantic,
        'results_semantic_diversity': results_guided,
        'analysis': analysis,
    }

    return full_result


def _restore_backup_if_needed(project_root: Path, seed: int, trial_id: int):
    """
    在每次trial结束后恢复unified_agent.py到最早的备份（gen0备份或gen1备份）
    以确保每次trial从相同baseline开始
    """
    backup_dir = project_root / "experiments" / "self_modification"
    target_file = project_root / "moss" / "core" / "unified_agent.py"

    # 找最早的备份（gen1最接近原始）
    backups = sorted(backup_dir.glob("backup_gen1_*.py"))
    if backups:
        earliest = backups[0]
        original_source = earliest.read_text(encoding='utf-8')
        target_file.write_text(original_source, encoding='utf-8')
        logger.info(f"  [Restore] unified_agent.py 已从 {earliest.name} 恢复")
    else:
        logger.warning("  [Restore] 未找到gen1备份，无法恢复，继续使用当前文件")


def _print_summary(analysis: Dict):
    """打印实验摘要表格"""
    print("\n" + "=" * 80)
    print("MOSS v6.2 语义引导变异实验 - 结果摘要")
    print("=" * 80)
    print(f"{'指标':<30} {'v6.1随机':>15} {'v6.2均匀目的':>15} {'v6.2多样性目的':>16}")
    print("-" * 80)

    metrics = [
        ('Δfitness (均值)', 'fitness_improvement', 'mean', '.4f'),
        ('Δfitness (标准差)', 'fitness_improvement', 'std', '.4f'),
        ('fitness提升% (均值)', 'fitness_improvement_pct', 'mean', '.1f'),
        ('接受率 (均值)', 'acceptance_rate', 'mean', '.1%'),
        ('变异多样性熵 (均值)', 'mutation_diversity', 'mean', '.3f'),
    ]

    for metric_name, key, stat, fmt in metrics:
        v_random = analysis['v61_random'][key][stat]
        v_uniform = analysis['v62_semantic_uniform'][key][stat]
        v_diversity = analysis['v62_semantic_diversity'][key][stat]
        if fmt == '.1%':
            print(f"{metric_name:<30} {v_random:>15.1%} {v_uniform:>15.1%} {v_diversity:>16.1%}")
        elif fmt == '.1f':
            print(f"{metric_name:<30} {v_random:>15.1f}% {v_uniform:>14.1f}% {v_diversity:>15.1f}%")
        else:
            print(f"{metric_name:<30} {v_random:>15{fmt}} {v_uniform:>15{fmt}} {v_diversity:>16{fmt}}")

    print("-" * 80)

    if 'relative_improvement_vs_random_pct' in analysis.get('v62_semantic_uniform', {}):
        rel_u = analysis['v62_semantic_uniform']['relative_improvement_vs_random_pct']
        rel_d = analysis['v62_semantic_diversity']['relative_improvement_vs_random_pct']
        print(f"{'vs v6.1相对提升':<30} {'baseline':>15} {rel_u:>+14.1f}% {rel_d:>+15.1f}%")
    print("=" * 80)


def save_results(result: Dict, output_dir: Path) -> Path:
    """保存实验结果到JSON"""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"v62_comparison_{timestamp}.json"
    filepath = output_dir / filename

    def default_serializer(obj):
        if isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, default=default_serializer, ensure_ascii=False)

    logger.info(f"\n[Save] 实验结果已保存: {filepath}")
    return filepath


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='MOSS v6.2 语义引导变异对比实验')
    parser.add_argument('--trials', type=int, default=3, help='每组重复次数（默认3）')
    parser.add_argument('--generations', type=int, default=30, help='每次最大进化代数（默认30）')
    parser.add_argument('--seed', type=int, default=42, help='基础随机种子（默认42）')
    parser.add_argument('--quick', action='store_true', help='快速模式（1次trial，20代）')
    args = parser.parse_args()

    if args.quick:
        logger.info("快速模式启动（1次trial，20代）")
        n_trials = 1
        max_gen = 20
    else:
        n_trials = args.trials
        max_gen = args.generations

    try:
        result = run_comparison_experiment(
            n_trials=n_trials,
            max_generations=max_gen,
            base_seed=args.seed
        )

        output_dir = PROJECT_ROOT / "experiments" / "self_modification"
        saved_path = save_results(result, output_dir)

        print(f"\n✅ 实验完成！结果保存至: {saved_path}")

    except KeyboardInterrupt:
        logger.warning("用户中断实验")
        sys.exit(1)
    except Exception as e:
        logger.error(f"实验失败: {e}", exc_info=True)
        sys.exit(1)
