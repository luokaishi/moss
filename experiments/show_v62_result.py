"""打印v6.2实验结果"""
import json
from pathlib import Path

data_dir = Path(__file__).parent / "self_modification"
files = sorted(data_dir.glob("v62_comparison_*.json"))
latest = files[-1]
with open(latest, "r", encoding="utf-8") as f:
    data = json.load(f)

a = data["analysis"]
print("=== v6.2 语义引导变异 vs v6.1随机变异 实验结果 ===")
print()

for group, label in [
    ("v61_random", "v6.1随机"),
    ("v62_semantic_uniform", "v6.2均匀目的"),
    ("v62_semantic_diversity", "v6.2多样性偏向"),
]:
    g = a[group]
    fi = g["fitness_improvement"]
    fp = g["fitness_improvement_pct"]
    ar = g["acceptance_rate"]
    md = g["mutation_diversity"]
    print(f"{label}:")
    print(f"  delta_fitness: {fi['mean']:.4f} +/- {fi['std']:.4f}")
    print(f"  percent_up:    {fp['mean']:.1f}% +/- {fp['std']:.1f}%")
    print(f"  accept_rate:   {ar['mean']:.1%} +/- {ar['std']:.1%}")
    print(f"  mut_diversity: {md['mean']:.3f}")
    if "relative_improvement_vs_random_pct" in g:
        print(f"  vs_v61_gain:   {g['relative_improvement_vs_random_pct']:+.1f}%")
    print()

print(f"Result file: {latest}")

# 详细打印每次trial
print()
print("=== 各组3次trial详情 ===")
for group_key, label in [
    ("results_random", "v6.1随机"),
    ("results_semantic_uniform", "v6.2均匀"),
    ("results_semantic_diversity", "v6.2多样性"),
]:
    print(f"\n{label}:")
    for r in data[group_key]:
        print(f"  Trial {r['trial_id']}: "
              f"fitness {r['initial_fitness']:.4f}->{r['final_fitness']:.4f} "
              f"(+{r['fitness_improvement']:.4f}) "
              f"accept={r['acceptance_rate']:.0%}")
