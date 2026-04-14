"""
MOSS v6.0 — Self-Modification POC Experiment (v6.1 强化版)
=============================================

验证Agent自写自身代码能力的概念验证实验

升级内容（v6.1）：
- 30代进化（原10代）
- 结构级变异（epsilon_tune, weight_hardcode, action_shuffle, branch_inject）
- 真实涌现率检测（相变/自组织/协同效应三信号）
- 更大变异强度（intensity=0.35）
- 允许轻微退步探索（acceptance_threshold=-0.002）

运行方式：
    $env:PYTHONUTF8=1; & python experiments/run_v6_self_modification_poc.py

Author: MOSS v6.0 Auto-Build
Date: 2026-04-13
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

# ── 路径设置 ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── 日志 ──
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("MOSS_v6_POC")


def run_poc():
    """运行自改写POC验证实验"""

    print("\n" + "═" * 65)
    print("  MOSS v6.0 — Self-Modification POC")
    print("  Agent自写自身代码概念验证")
    print("═" * 65)
    print(f"  时间: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"  项目根目录: {PROJECT_ROOT}")
    print()

    # ── Step 1: 导入自改写引擎 ──
    print("[1/5] 加载 SelfModificationEngine...")
    try:
        from moss.core.self_modification_engine import (
            SelfModificationEngine, SMEConfig, EmergenceGuidedFitness
        )
        print("  ✅ SME导入成功")
    except ImportError as e:
        print(f"  ❌ SME导入失败: {e}")
        return None

    # ── Step 2: 加载基准Agent，测量baseline fitness ──
    print("\n[2/5] 测量基准fitness...")
    try:
        import importlib.util
        module_path = PROJECT_ROOT / "moss" / "core" / "unified_agent.py"
        spec = importlib.util.spec_from_file_location("moss.core.unified_agent", module_path)
        base_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(base_module)

        evaluator = EmergenceGuidedFitness()
        baseline_fitness = evaluator.evaluate(base_module, steps=300)
        print(f"  ✅ 基准fitness: {baseline_fitness:.4f}")
    except Exception as e:
        print(f"  ❌ 基准评估失败: {e}")
        import traceback
        traceback.print_exc()
        return None

    # ── Step 3: 构建SME配置（v6.1 强化版）──
    print("\n[3/5] 配置自改写引擎（v6.1 强化版）...")
    sme_config = SMEConfig(
        target_module="moss.core.unified_agent",
        # 使用经验证的富集度高函数（step=54, _apply_state_weights=30）
        target_functions=[
            "step", "_apply_state_weights",
            "_random_action", "select_action", "_update_state"
        ],
        population_size=6,              # 增大搜索空间
        max_generations=30,             # 30代充分进化
        acceptance_threshold=-0.002,    # 允许轻微退步（模拟退火）
        sandbox_timeout=25,
        enable_hot_reload=False,        # POC阶段不热重载
        enable_structural_mutations=True,  # 开启结构级变异
        mutation_intensity=0.35,        # 中等强度
        use_real_emergence=True,        # 真实涌现检测
        output_dir="experiments/self_modification"
    )

    sme = SelfModificationEngine(
        config=sme_config,
        project_root=str(PROJECT_ROOT)
    )
    print(f"  ✅ SME v6.1初始化成功")
    print(f"     目标函数: {sme_config.target_functions}")
    print(f"     每代候选: {sme_config.population_size}")
    print(f"     最大代数: {sme_config.max_generations}")
    print(f"     变异强度: {sme_config.mutation_intensity}")
    print(f"     结构级变异: {'开启' if sme_config.enable_structural_mutations else '关闭'}")

    # ── Step 4: 获取Purpose向量（模拟D9输出）──
    print("\n[4/5] 获取目的向量 (D9 Purpose)...")
    try:
        from moss.core.unified_agent import UnifiedMOSSAgent, MOSSConfig
        config = MOSSConfig(
            agent_id="poc_purpose_agent",
            enable_purpose=True
        )
        agent = UnifiedMOSSAgent(config=config)
        # 运行100步让Purpose稳定
        for _ in range(100):
            agent.step({})
        purpose_vector = agent._get_purpose_vector()
        if purpose_vector is not None:
            print(f"  ✅ 目的向量获取成功: shape={purpose_vector.shape}, "
                  f"norm={np.linalg.norm(purpose_vector):.4f}")
        else:
            print("  ⚠️  Purpose向量为None，使用均匀向量代替")
            purpose_vector = np.ones(4) / 4
    except Exception as e:
        print(f"  ⚠️  Purpose获取失败({e})，使用均匀向量")
        purpose_vector = np.ones(4) / 4

    # ── Step 5: 运行进化 ──
    print("\n[5/5] 🧬 启动自改写进化循环...")
    print(f"  目标模块: {sme_config.target_module}")
    print(f"  进化代数: {sme_config.max_generations}")
    print()

    t_start = time.time()
    report = sme.run(
        max_generations=sme_config.max_generations,
        purpose_vector=purpose_vector,
        early_stop_fitness=0.94      # 提高早停阈值，让进化充分展开
    )
    elapsed = time.time() - t_start

    # ── 结果分析 ──
    print("\n" + "═" * 65)
    print("  自改写实验结果分析")
    print("═" * 65)

    improvement = report['fitness_improvement']
    improvement_pct = (improvement / max(report['initial_fitness'], 1e-6)) * 100

    print(f"  初始fitness       : {report['initial_fitness']:.4f}")
    print(f"  最终fitness       : {report['final_fitness']:.4f}")
    print(f"  fitness提升       : {improvement:+.4f} ({improvement_pct:+.1f}%)")
    print(f"  接受的变异次数     : {report['total_mutations_accepted']}/{report['total_generations']} 代")
    print(f"  总耗时            : {elapsed:.1f}s")

    # 变异类型分布
    mut_types = [h['mutation_type'] for h in report['mutation_history'] if h['mutation_type'] != 'no_op']
    if mut_types:
        print(f"\n  变异类型分布:")
        from collections import Counter
        for typ, cnt in Counter(mut_types).most_common():
            print(f"    {typ:<25} {cnt} 次")

    # 关键判断
    print("\n  实验结论:")
    if report['total_mutations_accepted'] > 0:
        print(f"  ✅ 自改写成功！Agent在{report['total_mutations_accepted']}个代中改写了自身代码")
        if improvement > 0:
            print(f"  ✅ 改写后性能提升: {improvement_pct:+.1f}%")
        else:
            print(f"  ℹ️  性能无明显变化（进化正在探索）")
    else:
        print(f"  ℹ️  本轮进化未接受任何变异（当前代码已接近最优或需更多代数）")

    # 保存完整实验记录
    final_report = {
        **report,
        'poc_metadata': {
            'baseline_fitness': baseline_fitness,
            'purpose_vector': purpose_vector.tolist() if purpose_vector is not None else None,
            'total_elapsed_seconds': elapsed,
            'experiment_date': datetime.now().isoformat(),
            'moss_version': '6.0.0-dev',
            'experiment_type': 'self_modification_poc'
        }
    }

    report_dir = PROJECT_ROOT / "experiments" / "self_modification"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"poc_result_{datetime.now():%Y%m%d_%H%M%S}.json"

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)

    print(f"\n  📄 完整报告已保存: {report_path.name}")
    print("═" * 65)

    return final_report


def run_ast_demo():
    """单独演示AST变异器功能（无需运行完整实验）"""
    print("\n" + "─" * 50)
    print("  AST变异器快速演示")
    print("─" * 50)

    from moss.core.self_modification_engine import ASTMutator

    # 示例代码片段（完整可解析的类）
    sample_code = (
        "class Agent:\n"
        "    def select_action(self, observation):\n"
        "        actions = ['explore', 'survive', 'influence', 'optimize']\n"
        "        if observation.get('critical', False):\n"
        "            weights = [0.6, 0.1, 0.2, 0.1]\n"
        "        else:\n"
        "            weights = [0.25, 0.25, 0.25, 0.25]\n"
        "        idx = weights.index(max(weights))\n"
        "        return actions[idx]\n"
    )

    mutator = ASTMutator(rng_seed=42)

    # 演示各种变异类型
    for mut_type in ['constant_tweak', 'weight_shift', 'action_insert', 'condition_flip']:
        mutated, applied = mutator.mutate(
            sample_code,
            target_functions=['select_action'],
            mutation_type=mut_type
        )
        status = "✅" if applied != "no_op" else "⚠️ no_op"
        print(f"  {status} {mut_type:<20} → 变异{'成功' if applied != 'no_op' else '无效'}")

    print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MOSS v6.0 Self-Modification POC")
    parser.add_argument("--demo-only", action="store_true",
                        help="仅演示AST变异器，不运行完整实验")
    parser.add_argument("--generations", type=int, default=10,
                        help="进化代数（默认10）")
    args = parser.parse_args()

    if args.demo_only:
        run_ast_demo()
    else:
        run_ast_demo()  # 先演示
        report = run_poc()
        if report:
            print("\n  🎉 MOSS v6.0 自改写验证完成！")
        else:
            print("\n  ❌ 实验未能完成，请检查日志")
            sys.exit(1)
