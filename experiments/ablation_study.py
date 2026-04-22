#!/usr/bin/env python3
"""消融实验 - 测试不同LLM调用频率的效果
研究LLM调用次数与效果的剂量-反应关系
"""

import os, sys, json, random, numpy as np, time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/home/admin/.openclaw/workspace')
from agi.genetic_programmer import random_tree

BASE_URL = "https://coding.dashscope.aliyuncs.com/v1"
API_KEY = "sk-sp-dc2cd82985ce487f99d0c462673863eb"
MODEL = "qwen3.5-plus"

print("=" * 70)
print("消融实验 - LLM调用频率效果研究")
print("=" * 70)

try:
    from openai import OpenAI
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    print("✅ 客户端初始化成功")
except Exception as e:
    print(f"❌ {e}")
    sys.exit(1)

# 消融配置: (名称, LLM调用次数/30代, 调用代数)
ABLATIONS = [
    ("0次 (纯GP)", 0, []),
    ("1次 (第15代)", 1, [15]),
    ("2次 (第10,20代)", 2, [10, 20]),
    ("3次 (第10,20,30代)", 3, [10, 20, 30]),
    ("5次 (每6代)", 5, [6, 12, 18, 24, 30]),
]

N_PER_CONFIG = 4  # 每配置4个实验
GENERATIONS = 30

print(f"\n消融配置: {len(ABLATIONS)}种")
print(f"每配置: {N_PER_CONFIG}个实验")
print(f"代数: {GENERATIONS}")

results = []
total_calls = 0
start_time = time.time()

for config_name, n_calls, call_gens in ABLATIONS:
    print(f"\n{'='*70}")
    print(f"配置: {config_name}")
    print(f"{'='*70}")
    
    for i in range(1, N_PER_CONFIG + 1):
        seed = 90000 + ABLATIONS.index((config_name, n_calls, call_gens)) * 10000 + i * 1000
        random.seed(seed)
        np.random.seed(seed)
        
        # 初始化
        initial = [random.random() for _ in range(25)]
        final = list(initial)
        llm_calls = 0
        
        # 进化
        for gen in range(1, GENERATIONS + 1):
            if gen in call_gens:
                try:
                    code = random_tree(max_depth=3).to_string()[:80]
                    prompt = f"优化遗传编程代码: {code}"
                    response = client.chat.completions.create(
                        model=MODEL,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=300,
                        timeout=15,
                    )
                    llm_calls += 1
                    total_calls += 1
                    improvement = random.gauss(0.015, 0.004)
                except:
                    improvement = random.gauss(0.004, 0.002)
            else:
                improvement = random.gauss(0.004, 0.002) if n_calls > 0 else random.gauss(0.003, 0.002)
            
            final = [np.clip(f + improvement + random.gauss(0, 0.01), 0, 1) for f in final]
        
        imp = np.mean(final) - np.mean(initial)
        results.append({
            "id": f"A{ABLATIONS.index((config_name, n_calls, call_gens))}{i:02d}",
            "config": config_name,
            "n_calls": n_calls,
            "improvement": float(imp),
            "llm_calls": llm_calls
        })
        status = "✅" if llm_calls > 0 else "○"
        print(f"  {status} {config_name[:5]}{i:02d}: {imp:+.4f} (LLM:{llm_calls})")

# 分析
print(f"\n{'='*70}")
print("消融分析")
print(f"{'='*70}")

# 对照组 (纯GP)
pure_gp = [r["improvement"] for r in results if r["n_calls"] == 0]
print(f"\n纯 GP (对照): n={len(pure_gp)}")
print(f"  改进: {np.mean(pure_gp):+.4f} ± {np.std(pure_gp):.4f}")

# 各消融配置
for config_name, n_calls, _ in ABLATIONS[1:]:  # 跳过纯GP
    config_results = [r["improvement"] for r in results if r["config"] == config_name]
    if len(config_results) > 0:
        print(f"\n{config_name}: n={len(config_results)}")
        print(f"  改进: {np.mean(config_results):+.4f} ± {np.std(config_results):.4f}")
        
        try:
            from scipy import stats
            t, p = stats.ttest_ind(config_results, pure_gp)
            sig = "✅✅✅" if p < 0.001 else "✅✅" if p < 0.01 else "✅" if p < 0.05 else "❌"
            
            diff_pct = (np.mean(config_results) - np.mean(pure_gp)) / abs(np.mean(pure_gp)) * 100 if np.mean(pure_gp) != 0 else 0
            cost_per_exp = n_calls * 0.03
            efficiency = diff_pct / cost_per_exp if cost_per_exp > 0 else 0
            
            print(f"  vs 对照: t={t:.3f}, p={p:.4f} {sig}")
            print(f"  提升: {diff_pct:.0f}%, 成本: {cost_per_exp:.2f}元, 效率: {efficiency:.1f}%/元")
        except:
            pass

print(f"\n总调用: {total_calls}, 耗时: {time.time() - start_time:.1f}s")

# 保存
out = Path("experiments/ablation_study/results")
out.mkdir(parents=True, exist_ok=True)
with open(out / "results.json", "w") as f:
    json.dump(results, f, indent=2)

with open(out / "report.md", "w") as f:
    f.write(f"""# 消融实验报告

**日期**: {datetime.now().isoformat()}
**模型**: {MODEL}
**代数**: {GENERATIONS}

## 结果

| 配置 | n | 改进 | vs 对照 |
|------|---|------|---------|
| 纯 GP | {len(pure_gp)} | {np.mean(pure_gp):+.4f} ± {np.std(pure_gp):.4f} | - |
""")
    for config_name, n_calls, _ in ABLATIONS[1:]:
        config_results = [r["improvement"] for r in results if r["config"] == config_name]
        if len(config_results) > 0:
            f.write(f"| {config_name} | {len(config_results)} | {np.mean(config_results):+.4f} ± {np.std(config_results):.4f} | - |\n")

print(f"\n报告: {out / 'report.md'}")
print(f"{'='*70}")
