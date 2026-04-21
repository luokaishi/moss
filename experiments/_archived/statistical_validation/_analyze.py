"""分析已完成的 E1/E2 结果"""
import json
from pathlib import Path

sv_dir = Path(__file__).parent

for fname in sorted(sv_dir.glob("validation_data_*.json")):
    with open(fname, encoding="utf-8") as f:
        data = json.load(f)

    for exp in data:
        name = exp["experiment"]
        print(f"\n{'='*60}")
        print(f"  {name}  (N={exp['n_trials']}, gen={exp['max_gen']})")
        print(f"{'='*60}")

        if "E1" in name:
            for label, key in [("Random", "results_random"), ("Semantic", "results_semantic")]:
                for i, t in enumerate(exp[key]):
                    print(f"  {label} T{i+1}: seed={t['seed']:3d}  "
                          f"\u0394fit={t['fitness_improvement']:+.4f}  "
                          f"accept={t['acceptance_rate']:.1%}  "
                          f"time={t['elapsed_seconds']:.0f}s")

        elif "E2" in name:
            for label, key in [("Scalar", "results_scalar"), ("Pareto", "results_pareto")]:
                for i, t in enumerate(exp[key]):
                    hv = t.get("pareto", {}).get("final_hv", 0.0)
                    hv_str = f"  HV={hv:.4f}" if hv else ""
                    print(f"  {label} T{i+1}: seed={t['seed']:3d}  "
                          f"\u0394fit={t['fitness_improvement']:+.4f}  "
                          f"accept={t['acceptance_rate']:.1%}  "
                          f"time={t['elapsed_seconds']:.0f}s{hv_str}")

        elif "E3" in name:
            for i, t in enumerate(exp["results"]):
                print(f"  Meta T{i+1}: seed={t['seed']:3d}  "
                      f"init={t.get('initial_meta_fitness',0):.4f}  "
                      f"final={t.get('final_meta_fitness',0):.4f}  "
                      f"\u0394={t.get('meta_fitness_improvement',0):+.4f}  "
                      f"accept={t.get('meta_acceptance_rate',0):.0%}  "
                      f"time={t['elapsed_seconds']:.0f}s")
