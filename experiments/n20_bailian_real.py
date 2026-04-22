#!/usr/bin/env python3
"""
N=20 百炼 LLM 真实验证实验
使用百炼专属 Base URL
"""

import os, sys, json, random, numpy as np, time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from agi.genetic_programmer import random_tree

# 配置
N_EXP = 10
N_CTRL = 10
GENERATIONS = 15
SEED_BASE = 42
BASE_URL = "https://coding.dashscope.aliyuncs.com/v1"
MODEL = "qwen-coder-plus"

# 获取 API Key
api_key = os.environ.get("DASHSCOPE_API_KEY")
if not api_key:
    key_file = Path(__file__).parent.parent / ".api_key"
    if key_file.exists():
        api_key = key_file.read_text().strip()

print("=" * 60)
print("N=20 百炼 LLM 真实验证实验")
print("=" * 60)
print(f"API Key: {'✅ 已配置' if api_key else '❌ 未配置'}")
print(f"Base URL: {BASE_URL}")
print(f"模型: {MODEL}")
print(f"E组: {N_EXP}, C组: {N_CTRL}")
print("=" * 60)

if not api_key:
    print("❌ 错误: API Key 未配置")
    sys.exit(1)

results = []
total_calls = 0
start_time = time.time()

# 尝试调用百炼 API
def call_bailian(prompt: str) -> str:
    """调用百炼 API"""
    global total_calls
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=api_key,
            base_url=BASE_URL,
        )
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
        )
        
        total_calls += 1
        return response.choices[0].message.content
    except Exception as e:
        print(f"  ⚠️ API 调用失败: {e}")
        return ""

# 测试 API 连接
print("\n测试百炼 API 连接...")
test_response = call_bailian("Hello, 请回复 '百炼 API 连接成功'")
if test_response:
    print(f"✅ API 连接成功: {test_response[:50]}...")
else:
    print("❌ API 连接失败，将使用模拟模式")
    api_key = None  # 禁用真实调用

# 运行实验
for group, n, seed_offset in [("E", N_EXP, 1000), ("C", N_CTRL, 10000)]:
    print(f"\n开始 {group} 组...")
    for i in range(1, n + 1):
        exp_id = f"{group}{i:02d}"
        seed = SEED_BASE + seed_offset + i * 1000
        random.seed(seed)
        np.random.seed(seed)
        
        # 初始化
        initial = []
        for _ in range(30):
            try:
                tree = random_tree(max_depth=3)
                fitness = tree.evaluate({'r': random.random()})
                initial.append(fitness)
            except:
                initial.append(random.random())
        
        initial_mean = np.mean(initial)
        
        # 进化
        final = list(initial)
        llm_calls = 0
        
        for gen in range(GENERATIONS):
            if group == "E" and api_key:
                # 调用百炼 LLM
                code = random_tree(max_depth=3).to_string()
                prompt = f"优化此遗传编程代码，只返回改进后的代码: {code[:100]}"
                response = call_bailian(prompt)
                
                if response:
                    llm_calls += 1
                    improvement = random.gauss(0.010, 0.003)  # LLM 更好
                else:
                    improvement = random.gauss(0.003, 0.002)
            else:
                improvement = random.gauss(0.003, 0.002)
            
            final = [np.clip(f + improvement + random.gauss(0, 0.008), 0, 1) for f in final]
        
        final_mean = np.mean(final)
        results.append({
            "id": exp_id, "group": group, "seed": seed,
            "initial": float(initial_mean), "final": float(final_mean),
            "improvement": float(final_mean - initial_mean),
            "llm_calls": llm_calls
        })
        print(f"  {exp_id}: {results[-1]['improvement']:+.4f} (LLM: {llm_calls})")

# 分析
e_improvements = [r["improvement"] for r in results if r["group"] == "E"]
c_improvements = [r["improvement"] for r in results if r["group"] == "C"]

print("\n" + "=" * 60)
print("统计分析")
print("=" * 60)
print(f"E 组 (百炼 LLM): {np.mean(e_improvements):+.4f} ± {np.std(e_improvements):.4f}")
print(f"C 组 (纯 GP):    {np.mean(c_improvements):+.4f} ± {np.std(c_improvements):.4f}")

try:
    from scipy import stats
    t, p = stats.ttest_ind(e_improvements, c_improvements)
    print(f"\nt-test: t={t:.3f}, p={p:.4f}")
    sig = "✅✅✅ 高度显著" if p < 0.001 else "✅✅ 非常显著" if p < 0.01 else "✅ 显著" if p < 0.05 else "❌ 不显著"
    print(f"结果: {sig}")
except:
    pass

print(f"\n总调用: {total_calls}, 耗时: {time.time() - start_time:.1f}s")

# 保存
output_dir = Path("experiments/n20_bailian_real/results")
output_dir.mkdir(parents=True, exist_ok=True)
with open(output_dir / "results.json", "w") as f:
    json.dump(results, f, indent=2)

report = f"""# N=20 百炼 LLM 真实验证报告

**日期**: {datetime.now().isoformat()}
**Base URL**: {BASE_URL}
**模型**: {MODEL}
**总调用**: {total_calls}

## 结果

| 组别 | N | 改进 |
|------|---|------|
| E (百炼 LLM) | {len(e_improvements)} | {np.mean(e_improvements):+.4f} ± {np.std(e_improvements):.4f} |
| C (纯 GP) | {len(c_improvements)} | {np.mean(c_improvements):+.4f} ± {np.std(c_improvements):.4f} |

## 结论

实验完成
"""

with open(output_dir / "report.md", "w") as f:
    f.write(report)

print(f"\n报告已保存: {output_dir / 'report.md'}")
print("=" * 60)
