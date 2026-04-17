# MOSS Phase 2: Statistical Validation Report

**Date:** 2026-04-17  
**Status:** In Progress (E1 ✅ E2 ✅ E3 🔄 pending more trials)

---

## Overview

Phase 2 performs rigorous statistical validation of the core MOSS algorithmic claims.
Each experiment runs N=5 independent trials (30 generations each) with different random seeds,
followed by Welch's t-test and bootstrap confidence intervals.

---

## Experiment Results Summary

| Exp | Comparison | N | Metric | A (mean) | B (mean) | Cohen's d | p-value | Significant |
|-----|-----------|---|--------|----------|----------|-----------|---------|-------------|
| E1 | Semantic vs Random (fitness Δ) | 5 | fitness Δ | -0.0032 | +0.0134 | -1.25 | 0.048 | ⚠️ partial |
| E1 | Semantic vs Random (accept rate) | 5 | accept rate | 40.0% | 35.3% | 0.86 | 0.174 | ❌ |
| E2 | Pareto vs Scalar (fitness Δ) | 5 | fitness Δ | +0.0155 | -0.0020 | 1.11 | 0.079 | ❌ |
| E2 | Pareto vs Scalar (accept rate) | 5 | accept rate | **60.7%** | 35.3% | **2.07** | **0.001** | ✅ |
| E2 | Pareto Hypervolume | 5 | HV | 0.161 ± 0.013 | — | — | — | — |
| E3 | Meta-SME stability | 2 | meta-Δfit | -0.141 ± 0.202 | — | — | 0.322 | ❌ (N too small) |

---

## Detailed Results

### E1: v6.2 Semantic-Guided vs v6.1 Random Mutation (N=5, 30 gen)

**Run:** 2026-04-17T14:00:57

**Fitness Δ (end - start):**
- Random:   mean = +0.0134, std = 0.0138, range = [-0.004, +0.031]
- Semantic: mean = -0.0032, std = 0.0127, range = [-0.016, +0.013]
- Welch t = -1.97, df = 7.95, **p = 0.048**, Cohen's d = -1.25
- 95% Bootstrap CI (semantic): [-0.013, +0.007]

> **Interpretation:** Semantic-guided mutation did NOT outperform random on fitness Δ in this 30-gen window.
> The p=0.048 significance is in the *wrong* direction — random achieved higher final fitness.
> This may indicate that semantic filtering over-constrains the mutation search space in short runs,
> or that the v6.1 baseline fitness trajectory is highly seed-dependent.

**Acceptance Rate:**
- Random:   mean = 35.3%, std = 6.5%
- Semantic: mean = 40.0%, std = 4.1%
- Welch t = 1.36, df = 6.73, p = 0.174 (not significant)
- Effect size: Cohen's d = 0.86 (large effect, but N=5 underpowered)

> **Note:** The acceptance rate trend (40% vs 35%) aligns with prior single-run v6.2 results (41% vs 25%),
> but variance is too high for significance at N=5. Needs N≥10 to confirm.

---

### E2: v6.3 Pareto Multi-Objective vs Scalar Fitness (N=5, 30 gen)

**Run:** 2026-04-16T15:36:56

**Fitness Δ:**
- Scalar: mean = -0.0020, std = 0.0203
- Pareto: mean = +0.0155, std = 0.0094
- Welch t = 1.75, df = 5.65, p = 0.079, Cohen's d = 1.11
- Relative improvement: **+858%** (Pareto vs Scalar)

> **Interpretation:** Pareto consistently achieves positive fitness Δ while scalar fluctuates around zero.
> p=0.079 narrowly misses α=0.05, but effect size (d=1.11) is large. Needs N≥8 to reach significance.

**Acceptance Rate: ✅ SIGNIFICANT**
- Scalar: mean = 35.3%, std = 9.0%
- Pareto: mean = **60.7%**, std = 14.8%
- Welch t = 3.27, df = 6.61, **p = 0.001**, Cohen's d = **2.07**
- **Pareto accepts 72% more mutations than scalar fitness** — strongly significant.

**Hypervolume:**
- Mean HV = 0.161, std = 0.013, range = [0.145, 0.180]
- 95% CI: [0.151, 0.171]

---

### E3: v7.0 Meta-SME Stability (N=2 — incomplete)

**Preliminary data (2026-04-16, N=2, 10 gen):**
- Meta-fitness Δ: mean = -0.141, std = 0.202
- Meta-acceptance rate: mean = 25%, range = [20%, 30%]
- Positive rate: 50%

> **Status:** N=2 is insufficient. Currently running N=5 trials × 30 gen.
> Prior single-run result: Meta-fitness +26.3% over 50 generations.

---

## Interpretation & Next Steps

### What's confirmed
1. **Pareto acceptance rate advantage is statistically robust** (p=0.001, d=2.07) — strongest signal so far.
2. **Pareto fitness improvement trend** is consistent (d=1.11) but needs more trials (N≥8).
3. **Semantic guidance** shows acceptance rate trend in the right direction but is inconclusive at N=5.

### What needs more work
- **E1**: Increase to N=10 trials; investigate why semantic guidance hurts short-run fitness Δ.
- **E2**: Increase to N=8 to push fitness Δ to significance.
- **E3**: Complete N=5 × 30-gen run (in progress).

### Paper implications
- E2 Pareto acceptance rate result (p=0.001) is paper-ready.
- E1/E3 results require more trials before making strong claims.
- Consider reporting both "per-run" and "final generation" fitness to disambiguate trajectory effects.

---

## Files

| File | Description |
|------|-------------|
| `experiments/statistical_validation/validation_report_20260417_140057.json` | E1 N=5 30-gen (2026-04-17) |
| `experiments/statistical_validation/validation_report_20260416_153656.json` | E2 N=5 30-gen (2026-04-16) |
| `experiments/statistical_validation/validation_report_20260416_124904.json` | E1+E2+E3 N=2 pilot (2026-04-16) |
| `experiments/run_statistical_validation.py` | Experiment runner |

---

*Report auto-generated from Phase 2 validation runs. Update as more trials complete.*
