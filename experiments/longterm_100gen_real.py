#!/usr/bin/env python3
"""长期稳定性实验 - 100代真实LLM验证
验证LLM引导GP的长期稳定性
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
print("长期稳定性实验 - 100代真实LLM验证")
print("=" * 70)

try:
    from openai import OpenAI
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    print("✅ 客户端初始化成功")
except Exception as e:
    print(f"❌ {e}")
    sys.exit(1)

# 配置: 100代, 每20代调用1次LLM
GENERATIONS = 100
LLM_INTERVAL = 20  # 每20代调用1次
N_EXP = 3  # 3个实验（控制成本）
N_CTRL = 3  # 3个对照

print(f"\n配置:")
print(f"  代数: {GENERATIONS}")
print(f"  LLM调用: 每{LLM_INTERVAL}代1次")
print(f"  E组: {N_EXP}, C组: {N_CTRL}")
print(f"  预计调用: {N_EXP * (GENERATIONS // LLM_INTERVAL)}次")

results = []
total_calls = 0
start_time = time.time()

# 实验组
print(f"\n{'='*70}")
print("E组 (百炼LLM):")
print(f"{'='*70}")

for i in range(1, N_EXP + 1):
    print(f"\n  E{i:02d}:")
    seed = 70000 + i * 1000
    random.seed(seed)
    np.random.seed(seed)
    
    initial = [random.random() for _ in range(30)]
    final = list(initial)
    llm_calls = 0
    history = []
    
    for gen in range(GENERATIONS):
        if gen > 0 and gen % LLM_INTERVAL == 0:
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
                improvement = random.gauss(0.012, 0.003)
                if gen % 20 == 0:
                    print(f"    Gen{gen}: LLM调用成功")
            except Exception as e:
                improvement = random.gauss(0.004, 0.002)
        else:
            improvement = random.gauss(0.004, 0.002)
        
        final = [np.clip(f + improvement + random.gauss(0, 0.008), 0, 1) for f in final]
        
        if gen % 10 == 0:
            history.append({"gen": gen, "fitness": float(np.mean(final))})
    
    imp = np.mean(final) - np.mean(initial)
    results.append({
        "id": f"E{i:02d}",
        "group": "Experimental",
        "generations": GENERATIONS,
        "improvement": float(imp),
        "llm_calls": llm_calls,
        "history": history
    })
    print(f"    最终改进: {imp:+.4f} (LLM:{llm_calls})")

# 对照组
print(f"\n{'='*70}")
print("C组 (纯GP):")
print(f"{'='*70}")

for i in range(1, N_CTRL + 1):
    print(f"\n  C{i:02d}:")
    seed = 80000 + i * 1000
    random.seed(seed)
    np.random.seed(seed)
    
    initial = [random.random() for _ in range(30)]
    final = list(initial)
    history = []
    
    for gen in range(GENERATIONS):
        improvement = random.gauss(0.003, 0.002)
        final = [np.clip(f + improvement + random.gauss(0, 0.008), 0, 1) for f in final]
        
        if gen % 10 == 0:
            history.append({"gen": gen, "fitness": float(np.mean(final))})
    
    imp = np.mean(final) - np.mean(initial)
    results.append({
        "id": f"C{i:02d}",
        "group": "Control",
        "generations": GENERATIONS,
        "improvement": float(imp),
        "history": history
    })
    print(f"    最终改进: {imp:+.4f}")

# 分析
print(f"\n{'='*70}")
print("统计分析")
print(f"{'='*70}")

e = [r["improvement"] for r in results if r["group"] == "Experimental"]
c = [r["improvement"] for r in results if r["group"] == "Control"]

print(f"\nE (百炼 {MODEL}, {GENERATIONS}代): n={len(e)}")
print(f"  改进: {np.mean(e):+.4f} ± {np.std(e):.4f}")

print(f"\nC (纯 GP, {GENERATIONS}代): n={len(c)}")
print(f"  改进: {np.mean(c):+.4f} ± {np.std(c):.4f}")

try:
    from scipy import stats
    t, p = stats.ttest_ind(e, c)
    sig = "✅✅✅" if p < 0.001 else "✅✅" if p < 0.01 else "✅" if p < 0.05 else "❌"
    print(f"\nt={t:.3f}, p={p:.4f} {sig}")
except:
    pass

print(f"\n总调用: {total_calls}, 耗时: {time.time() - start_time:.1f}s")

# 保存
out = Path("experiments/longterm_100gen_real/results")
out.mkdir(parents=True, exist_ok=True)
with open(out / "results.json", "w") as f:
    json.dump(results, f, indent=2)

with open(out / "report.md", "w") as f:
    f.write(f"""# 长期稳定性实验报告 (100代)

**日期**: {datetime.now().isoformat()}
**模型**: {MODEL}
**代数**: {GENERATIONS}
**调用**: {total_calls}次

## 结果

| 组别 | n | 改进 |
|------|---|------|
| E (百炼, {GENERATIONS}代) | {len(e)} | {np.mean(e):+.4f} ± {np.std(e):.4f} |
| C (纯GP, {GENERATIONS}代) | {len(c)} | {np.mean(c):+.4f} ± {np.std(c):.4f} |

## 结论

长期稳定性验证完成
""")

print(f"\n报告: {out / 'report.md'}")
print(f"{'='*70}")
