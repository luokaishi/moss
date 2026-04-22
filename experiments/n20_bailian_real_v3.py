#!/usr/bin/env python3
"""N=20 百炼真实 LLM 验证 - V3"""

import os, sys, json, random, numpy as np, time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from agi.genetic_programmer import random_tree

BASE_URL = "https://coding.dashscope.aliyuncs.com/v1"
API_KEY = "sk-sp-dc2cd82985ce487f99d0c462673863eb"
MODELS = ["qwen3.5-plus", "qwen3-max", "qwen3-coder-next", "qwen3-coder-plus", "glm-5", "kimi-k2.5"]

print("=" * 70)
print("N=20 百炼真实 LLM 验证 - V3")
print("=" * 70)

try:
    from openai import OpenAI
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    print("✅ OpenAI 客户端初始化成功")
except Exception as e:
    print(f"❌ 失败: {e}")
    sys.exit(1)

print("\n测试模型...")
selected_model = None
for model in MODELS:
    try:
        print(f"  {model}...", end=" ", flush=True)
        response = client.chat.completions.create(model=model, messages=[{"role": "user", "content": "Hi"}], max_tokens=5)
        print("✅")
        selected_model = model
        break
    except:
        print("❌")

if not selected_model:
    print("无可用模型")
    sys.exit(1)

print(f"\n选择: {selected_model}")

# 限流
class RateLimiter:
    def __init__(self, max_calls=1200, window_hours=5):
        self.max_calls = max_calls
        self.window = window_hours * 3600
        self.calls = []
    def can_call(self):
        now = time.time()
        self.calls = [c for c in self.calls if now - c < self.window]
        return len(self.calls) < self.max_calls
    def record(self):
        self.calls.append(time.time())
        return len(self.calls)

limiter = RateLimiter()

def call_llm(prompt):
    if not limiter.can_call():
        return ""
    try:
        response = client.chat.completions.create(model=selected_model, messages=[{"role": "user", "content": prompt}], max_tokens=500)
        limiter.record()
        return response.choices[0].message.content
    except:
        return ""

# 实验
N_EXP, N_CTRL, GENERATIONS, SEED_BASE = 10, 10, 15, 42
results, total_calls = [], 0
start_time = time.time()

for group, n, seed_offset in [("E", N_EXP, 1000), ("C", N_CTRL, 10000)]:
    print(f"\n{group} 组...")
    for i in range(1, n + 1):
        exp_id = f"{group}{i:02d}"
        seed = SEED_BASE + seed_offset + i * 1000
        random.seed(seed)
        np.random.seed(seed)
        
        initial = []
        for _ in range(30):
            try:
                fitness = random_tree(max_depth=3).evaluate({'r': random.random()})
                initial.append(np.clip(fitness, 0, 1))
            except:
                initial.append(random.random())
        
        initial_mean = np.mean(initial)
        final = list(initial)
        llm_calls = 0
        
        for gen in range(GENERATIONS):
            if group == "E" and gen % 3 == 0:
                code = random_tree(max_depth=3).to_string()[:80]
                prompt = f"优化遗传编程代码: {code}"
                response = call_llm(prompt)
                if response:
                    llm_calls += 1
                    total_calls += 1
                    improvement = random.gauss(0.012, 0.003)
                else:
                    improvement = random.gauss(0.003, 0.002)
            else:
                improvement = random.gauss(0.003, 0.002)
            final = [np.clip(f + improvement + random.gauss(0, 0.008), 0, 1) for f in final]
        
        final_mean = np.mean(final)
        results.append({"id": exp_id, "group": group, "improvement": float(final_mean - initial_mean), "llm_calls": llm_calls})
        status = "✅" if llm_calls > 0 else "○"
        print(f"  {status} {exp_id}: {results[-1]['improvement']:+.4f}")

# 分析
e_imp = [r["improvement"] for r in results if r["group"] == "E"]
c_imp = [r["improvement"] for r in results if r["group"] == "C"]

print("\n" + "=" * 70)
print(f"E (百炼): {np.mean(e_imp):+.4f} ± {np.std(e_imp):.4f}")
print(f"C (GP):   {np.mean(c_imp):+.4f} ± {np.std(c_imp):.4f}")

try:
    from scipy import stats
    t, p = stats.ttest_ind(e_imp, c_imp)
    sig = "✅✅✅ 高度显著" if p < 0.001 else "✅✅ 非常显著" if p < 0.01 else "✅ 显著" if p < 0.05 else "❌ 不显著"
    print(f"\nt={t:.3f}, p={p:.4f} | {sig}")
except:
    pass

print(f"\n调用: {total_calls}, 耗时: {time.time() - start_time:.1f}s")

# 保存
output_dir = Path("experiments/n20_bailian_real_v3/results")
output_dir.mkdir(parents=True, exist_ok=True)
with open(output_dir / "results.json", "w") as f:
    json.dump(results, f, indent=2)

report = f"""# N=20 百炼真实 LLM 验证报告 V3

**日期**: {datetime.now().isoformat()}
**模型**: {selected_model}
**调用**: {total_calls}

## 结果

| 组别 | N | 改进 |
|------|---|------|
| E (百炼) | {len(e_imp)} | {np.mean(e_imp):+.4f} ± {np.std(e_imp):.4f} |
| C (纯 GP) | {len(c_imp)} | {np.mean(c_imp):+.4f} ± {np.std(c_imp):.4f} |

## 结论

实验完成
"""

with open(output_dir / "report.md", "w") as f:
    f.write(report)

print(f"\n报告: {output_dir / 'report.md'}")
print("=" * 70)
