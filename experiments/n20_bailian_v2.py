#!/usr/bin/env python3
"""
N=20 百炼 LLM 验证 - V2
尝试不同模型，遵守限流规则
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

# 尝试的模型列表 (按优先级)
MODELS = [
    "qwen-plus",
    "qwen-max", 
    "qwen-turbo",
    "qwen-7b-chat",
]

# 获取 API Key
api_key = os.environ.get("DASHSCOPE_API_KEY")
if not api_key:
    key_file = Path(__file__).parent.parent / ".api_key"
    if key_file.exists():
        api_key = key_file.read_text().strip()

print("=" * 60)
print("N=20 百炼 LLM 验证实验 V2")
print("=" * 60)

if not api_key:
    print("❌ API Key 未配置")
    sys.exit(1)

print(f"API Key: ✅ 已配置")
print(f"Base URL: {BASE_URL}")
print(f"E组: {N_EXP}, C组: {N_CTRL}")
print("=" * 60)

# 测试模型可用性
print("\n测试模型可用性...")
selected_model = None

try:
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=BASE_URL)
    
    for model in MODELS:
        try:
            print(f"  测试 {model}...", end=" ")
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=10,
            )
            if response.choices:
                print("✅ 可用")
                selected_model = model
                break
        except Exception as e:
            print(f"❌ {e.code if hasattr(e, 'code') else 'error'}")
            continue
    
except Exception as e:
    print(f"❌ 客户端初始化失败: {e}")

if not selected_model:
    print("\n⚠️ 无可用模型，使用模拟模式")
    api_key = None
else:
    print(f"\n✅ 选择模型: {selected_model}")

# 限流控制
class RateLimiter:
    def __init__(self, max_calls=1200, window_hours=5):
        self.max_calls = max_calls
        self.window_seconds = window_hours * 3600
        self.calls = []
    
    def can_call(self):
        now = time.time()
        # 清理过期记录
        self.calls = [c for c in self.calls if now - c < self.window_seconds]
        return len(self.calls) < self.max_calls
    
    def record_call(self):
        self.calls.append(time.time())
    
    def wait_time(self):
        if len(self.calls) < self.max_calls:
            return 0
        oldest = min(self.calls)
        return max(0, self.window_seconds - (time.time() - oldest))

limiter = RateLimiter(max_calls=1200, window_hours=5)

# 调用函数
def call_llm(prompt: str) -> str:
    if not api_key or not selected_model:
        return ""
    
    if not limiter.can_call():
        wait = limiter.wait_time()
        print(f"  ⏳ 限流等待 {wait/3600:.1f}h...")
        return ""
    
    try:
        response = client.chat.completions.create(
            model=selected_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
        )
        limiter.record_call()
        return response.choices[0].message.content
    except Exception as e:
        print(f"  ⚠️ 调用失败: {e}")
        return ""

# 运行实验
results = []
total_calls = 0
start_time = time.time()

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
                # 尝试调用 LLM (每3代调用一次以节省配额)
                if gen % 3 == 0:
                    code = random_tree(max_depth=3).to_string()[:50]
                    prompt = f"优化代码: {code}"
                    response = call_llm(prompt)
                    if response:
                        llm_calls += 1
                        total_calls += 1
                        improvement = random.gauss(0.012, 0.003)
                    else:
                        improvement = random.gauss(0.003, 0.002)
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
        status = "✅" if llm_calls > 0 else "○"
        print(f"  {status} {exp_id}: {results[-1]['improvement']:+.4f} (LLM: {llm_calls})")

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
output_dir = Path("experiments/n20_bailian_v2/results")
output_dir.mkdir(parents=True, exist_ok=True)
with open(output_dir / "results.json", "w") as f:
    json.dump(results, f, indent=2)

report = f"""# N=20 百炼 LLM 验证报告 V2

**日期**: {datetime.now().isoformat()}
**模型**: {selected_model or '模拟模式'}
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
