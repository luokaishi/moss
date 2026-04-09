# Supplementary Materials for MOSS v3.1.0 Paper

**Paper**: From Society to Self: Self-Generated Purpose in Autonomous Systems  
**Authors**: Cash, Fuxi  
**Target Venue**: NeurIPS 2027

---

## Contents

### /code - Implementation Files

Core implementation files for reproducing the experiments:

| File | Description |
|------|-------------|
| `goal_evolution_test.py` | D9 validation experiment (Goal Evolution Under Meta-Constraint) |
| `purpose_society.py` | H1: Purpose Divergence experiment |
| `purpose_stability.py` | H2: Purpose Stability experiment |
| `purpose_fulfillment.py` | H4: Purpose Fulfillment experiment |
| `purpose.py` | D9: Purpose Generator implementation |
| `agent_9d.py` | Full 9D Agent implementation |

**Full Repository**: https://github.com/luokaishi/moss

### /data - Experimental Results

JSON data files from key experiments:

| File | Description |
|------|-------------|
| `goal_evolution_results.json` | D9 validation results (+632% adaptation) |
| `final_results.json` | 10,000-step long-term simulation results |

### /figures - Publication Figures

PDF versions of all figures in the paper:

| File | Description |
|------|-------------|
| `figure1_architecture.pdf` | MOSS v3.1 9D architecture diagram |
| `figure2_divergence.pdf` | Purpose divergence results (H1) |
| `figure3_stability.pdf` | Purpose stability analysis (H2) |
| `figure4_fulfillment.pdf` | Fulfillment comparison (H4) |
| `figure5_competition.pdf` | Faction formation under scarcity (H3) |

---

## Reproducibility

### System Requirements
- Python 3.8+
- NumPy, Matplotlib, SciPy
- See `requirements.txt` in main repository

### Running Experiments

```bash
# Clone repository
git clone https://github.com/luokaishi/moss.git
cd moss

# Run D9 validation
python experiments/goal_evolution_test.py

# Run purpose experiments
python v3/experiments/purpose_society.py
python v3/experiments/purpose_stability.py
python v3/experiments/purpose_fulfillment.py

# Run demo
python demo_v31_master.py
```

### Expected Runtime
- D9 Validation: ~5 minutes
- Purpose Society: ~10 minutes
- Purpose Stability: ~15 minutes
- Purpose Fulfillment: ~20 minutes
- Long-term (10k steps): ~60 minutes

---

## Key Results Summary

### D9 Validation Experiment
- **Baseline (no D9)**: -0.250 reward → COLLAPSED
- **MOSS v3.1**: +1.331 reward → ADAPTED
- **Improvement**: +632%
- **M structure mutation**: Deleted C/I, added Stability

### Hypothesis Validation
| Hypothesis | Result | Metric |
|------------|--------|--------|
| H1: Divergence | ✅ Validated | 4 types from 6 agents |
| H2: Stability | ✅ Validated | 0.9977 (1k), 100% (10k) |
| H3: Society | 🔄 Partial | Unity under pressure |
| H4: Fulfillment | ✅ Validated | +26.66% satisfaction |

---

## License

MIT License - See main repository for details.

---

**Contact**: moss-project@github.com
