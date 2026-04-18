# MOSS Project Handover Guide

> **Version**: v7.1.0-dev (Phase 2 Statistical Validation — **Completed**)  
> **Last updated**: 2026-04-17  
> **Status**: Phase 2 complete — E1 N=10, E2 N=8, E3 N=5 done. Ready for Phase 3.

---

## 1. What Is MOSS?

MOSS is a research framework where AI agents possess four intrinsic objectives (survival, curiosity, influence, self-optimization) and can **rewrite their own source code** at runtime using a Genetic Programming engine (Self-Modification Engine, SME).

**The core claim**: Code-level self-modification driven by intrinsic purpose produces measurable, statistically significant improvement in agent fitness.

---

## 2. Project Structure at a Glance

```
moss/
├── moss/core/
│   ├── unified_agent.py              # 9-D UnifiedMOSSAgent (the subject of evolution)
│   ├── self_modification_engine.py   # SME v7.0 (~1900 LOC) — the engine that rewrites agents
│   └── objectives.py                 # 4 intrinsic objectives
├── moss/api/adapter.py               # Multi-version API: create_agent(version="v70")
│
├── experiments/
│   ├── run_v6_self_modification_poc.py    # v6.1 baseline experiment
│   ├── run_v62_semantic_guided.py         # v6.2 semantic guidance
│   ├── run_v63_pareto.py                  # v6.3 Pareto multi-objective
│   ├── run_v70_meta_sme.py               # v7.0 Meta-SME (engine rewrites itself)
│   ├── run_statistical_validation.py     # ⭐ Phase 2 main script
│   └── statistical_validation/           # Phase 2 results (JSON)
│
├── docs/
│   ├── MOSS_PHASE2_STATISTICAL_VALIDATION_REPORT.md  # Current phase report
│   ├── MOSS_V70_META_REPORT.md           # v7.0 technical report
│   ├── ARCHITECTURE.md                   # System architecture
│   └── PHASE_SUMMARY_AND_ROADMAP.md      # Roadmap
│
├── paper/main.tex                        # Paper v3.0 (LaTeX)
├── tests/                                # 68 passing tests
└── requirements.txt
```

---

## 3. Quick Setup

```bash
git clone https://github.com/luokaishi/moss.git
cd moss
pip install -r requirements.txt

# Verify
python -c "from moss.api.adapter import create_agent; a = create_agent(); print('OK')"

# Run tests
pytest tests/ -q   # should pass 68 tests
```

**Windows PowerShell note**: Always prefix with `$env:PYTHONUTF8=1;` to avoid encoding issues:
```powershell
$env:PYTHONUTF8=1; python experiments/run_v70_meta_sme.py
```

---

## 4. Evolution History — What Has Been Done

| Phase | Version | Key Result | Script |
|-------|---------|-----------|--------|
| Baseline | v6.1 | Fitness +6.3% (0.7257→0.7713), 33% acceptance | `run_v6_self_modification_poc.py` |
| Enhancement | v6.2 | Semantic guidance: acceptance 25%→41% (+60%) | `run_v62_semantic_guided.py` |
| Enhancement | v6.3 | Pareto: acceptance 62%, HV=0.176, Δfitness+144% | `run_v63_pareto.py` |
| Enhancement | v7.0 | Meta-SME: Meta-fitness +26.3%, triple safety | `run_v70_meta_sme.py` |
| **Current** | **Phase 2** | **Statistical validation N=5, E1/E2/E3** | `run_statistical_validation.py` |

---

## 5. Current Status — Phase 2 Statistical Validation

### What Phase 2 Is

We are running **N=5–10 independent replications** of each experiment to obtain statistically valid p-values and effect sizes (Cohen's d) for the paper.

### Completed Results

| Exp | Comparison | N | Result |
|-----|-----------|---|--------|
| **E1** | v6.2 Semantic vs v6.1 Random | **10** | Fitness Δ: +18.9% (p=0.522, n.s.); Accept: 35.3% vs 33.7% (p=0.650, n.s.) ❌ |
| **E2** | v6.3 Pareto vs Scalar fitness | **8** | **Accept rate: 54.6% vs 32.5% (p<0.001, d=2.39)** ✅; Fitness Δ p=0.096 |
| **E3** | v7.0 Meta-SME stability | **5** | Meta-fitness Δ: -5.2% (p=0.079, n.s.); Positive rate: 20% ⚠️ |

### How to Run More Trials

```bash
# Run experiment E1 with 10 trials, 30 generations each
$env:PYTHONUTF8=1; python experiments/run_statistical_validation.py --exp e1 --trials 10 --generations 30

# Run E2
$env:PYTHONUTF8=1; python experiments/run_statistical_validation.py --exp e2 --trials 10 --generations 30

# Run E3
$env:PYTHONUTF8=1; python experiments/run_statistical_validation.py --exp e3 --trials 5 --generations 30

# Results saved to: experiments/statistical_validation/validation_report_<timestamp>.json
```

### Interpreting Results

Results JSON structure:
```json
{
  "experiments": {
    "E2_v63_pareto_vs_scalar": {
      "analysis": {
        "acceptance_rate": {
          "pareto": { "mean": 0.607, "std": 0.053 },
          "scalar": { "mean": 0.353, "std": 0.065 },
          "welch_ttest": {
            "p_value": 0.001,
            "cohens_d": 2.07,
            "significant_005": true
          }
        }
      }
    }
  }
}
```

---

## 6. Next Steps (Phase 2 → Phase 3)

### Phase 2 Completed ✅
- [x] **E1 N=10**: Semantic guidance shows +18.9% fitness improvement but **not statistically significant** (p=0.522)
- [x] **E2 N=8**: **Pareto acceptance rate significantly better** (p<0.001, d=2.39) — paper-ready result
- [x] **E3 N=5**: Meta-SME **unstable** (only 20% trials positive) — needs engineering improvements
- [ ] **LaTeX figures**: Generate fitness evolution curves and Pareto frontier scatter plots
  - Script stub: `paper/generate_figures.py`

### Phase 3 (2–4 weeks)
- [ ] **LLM-guided mutation**: Replace random AST mutation with LLM-generated proposals
  - Expected to dramatically improve acceptance rate and fitness Δ
  - See `docs/strategy/` for design notes
- [ ] **ArXiv submission**: Target venue NeurIPS 2027 or ICLR 2027

---

## 7. Key Technical Concepts

### How the SME Works
1. **Select target function** from `unified_agent.py` (weighted by code complexity score)
2. **Apply AST mutation** (one of 9 types: constant_tweak, condition_flip, weight_shift, ...)
3. **Sandbox verification**: run 3 checks (syntax, import, instantiation) — pass ≥2/3
4. **Evaluate fitness**: run N episodes → compute success_rate, diversity, purpose_align, emergence
5. **Accept/reject**: if Δfitness ≥ threshold, overwrite source file

### Fitness Formula
```
fitness = 0.35 * success_rate
        + 0.25 * diversity
        + 0.20 * purpose_align
        + 0.20 * emergence
```

### What the Diffs in unified_agent.py Mean
The `unified_agent.py` currently has **modified weights and action sets** — these are **the agent's own evolved code** from the E1 experiment run. This is intentional and scientifically significant. If you need a clean baseline, use git:
```bash
git show HEAD:moss/core/unified_agent.py > moss/core/unified_agent_baseline.py
```

---

## 8. Important Files Not to Delete

| File | Why Important |
|------|--------------|
| `experiments/statistical_validation/*.json` | Phase 2 raw data |
| `experiments/self_modification/v63_pareto_*.json` | v6.3 Pareto run data |
| `moss/core/self_modification_engine.py` | Core engine — 1900 LOC |
| `paper/main.tex` | Paper v3.0 |
| `docs/MOSS_PHASE2_STATISTICAL_VALIDATION_REPORT.md` | Current phase summary |

---

## 9. Running the Full Experiment Pipeline

```bash
# 1. Quick sanity check (5 gen, 1 trial, ~30 sec)
$env:PYTHONUTF8=1; python experiments/run_v6_self_modification_poc.py --max-gen 5

# 2. Full Phase 2 statistical run (30 gen × 5 trials × 3 experiments, ~3 hours)
$env:PYTHONUTF8=1; python experiments/run_statistical_validation.py --exp e1 --trials 5 --generations 30
$env:PYTHONUTF8=1; python experiments/run_statistical_validation.py --exp e2 --trials 5 --generations 30
$env:PYTHONUTF8=1; python experiments/run_statistical_validation.py --exp e3 --trials 5 --generations 30

# 3. Meta-SME standalone (50 gen, ~2 hours)
$env:PYTHONUTF8=1; python experiments/run_v70_meta_sme.py
```

---

## 10. Contacts / Authors

- **Cash** — Core insight and theoretical framework (project owner, GitHub: luokaishi)
- **Fuxi** — Implementation and experimental validation (AI co-researcher)

Repository: https://github.com/luokaishi/moss  
License: MIT
