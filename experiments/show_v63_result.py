"""打印v6.3 Pareto实验结果"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

data_dir = Path(__file__).parent / "self_modification"
files = sorted(data_dir.glob("v63_pareto_2026*.json"))
with open(files[-1]) as f:
    d = json.load(f)

a = d["analysis"]
sc = a["scalar"]
pa = a["pareto"]

print("=== MOSS v6.3 Pareto vs v6.2 标量 实验结果 ===\n")
print(f"v6.2 scalar  : fitness_imp={sc['fitness_improvement']['mean']:.4f}+/-{sc['fitness_improvement']['std']:.4f}  accept={sc['acceptance_rate']['mean']:.1%}")
print(f"v6.3 pareto  : fitness_imp={pa['fitness_improvement']['mean']:.4f}+/-{pa['fitness_improvement']['std']:.4f}  accept={pa['acceptance_rate']['mean']:.1%}  archive={pa['archive_size']['mean']:.1f}  HV={pa['hypervolume']['mean']:.4f}\n")

print("各次Pareto trial详情:")
for r in d["results_pareto"]:
    ps = r["pareto_stats"] or {}
    seed_val = r["seed"]
    fi = r["fitness_improvement"]
    ar = r["acceptance_rate"]
    sz = ps.get("final_archive_size", 0)
    hv = ps.get("final_hypervolume", 0.0)
    dm = ps.get("dimension_maxes", {})
    print(f"  seed={seed_val}: +{fi:.4f}  accept={ar:.0%}  archive_size={sz}  HV={hv:.4f}")
    if dm:
        print(f"    dim_maxes: sr={dm.get('success_rate',0):.3f}  div={dm.get('diversity',0):.3f}  pur={dm.get('purpose_align',0):.3f}  em={dm.get('emergence',0):.3f}")

print()
print(f"Result file: {files[-1]}")
