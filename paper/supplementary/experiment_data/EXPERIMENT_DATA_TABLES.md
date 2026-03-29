# MOSS Paper Supplementary Data

**Document**: Experimental Data Summary  
**Version**: v5.0 Integration  
**Date**: 2026-03-29  

---

## Table S1: Experiment Overview

| Experiment ID | Duration (h) | Steps | Actions | Initial Purpose | Final Purpose | Convergence |
|---------------|--------------|-------|---------|-----------------|---------------|-------------|
| Run 4.1 | 3.5 | 1,090,000 | 33,240 | Survival | Influence | ✓ |
| Run 4.2 | 4.9 | 4,320,000 | 44,159 | Survival | Influence | ✓ |
| Run 4.3 | 3.3 | 2,880,000 | 14,449 | Curiosity | Influence | ✓ |
| Run 4.4 | 3.3 | 2,880,000 | 14,549 | Survival | Influence | ✓ |
| 72h Real World | 72.1 | 2,594,231 | 33,359 | Balanced | Curiosity | ✓ |
| **Total** | **87.1** | **13,764,231** | **139,756** | — | — | — |

---

## Table S2: Purpose Distribution Comparison

| Experiment | Survival (%) | Curiosity (%) | Influence (%) | Optimization (%) |
|------------|--------------|---------------|---------------|------------------|
| Run 4.2 | 51.1 | 24.5 | 24.5 | 0.0 |
| 72h Real World | 10.2 | 73.7 | 5.2 | 10.9 |

---

## Table S3: Tool Usage (72h Real World)

| Tool | Count | Percentage |
|------|-------|------------|
| Shell | 24,965 | 74.8% |
| GitHub | 5,561 | 16.7% |
| Filesystem | 2,833 | 8.5% |

---

## Table S4: Ablation Study Results

| Condition | Avg Reward | Success Rate | vs Causal |
|-----------|------------|--------------|-----------|
| No Purpose | 0.217 | 90.3% | -42.8% |
| Static Purpose | 0.221 | 89.4% | -40.2% |
| Random Purpose | 0.218 | 90.0% | -42.1% |
| Old Purpose (v5.0) | 0.215 | 90.2% | -44.3% |
| **Causal Purpose** | **0.310** | **68.3%** | — |

---

## Table S5: Key Metrics Validation

| Hypothesis | Test | Result | Evidence |
|------------|------|--------|----------|
| H1: Phase感知 | Run 4.2 | ✓ Pass | 4 Phase全部识别 |
| H2: Purpose适配 | Run 4.2 | ✓ Pass | 3次Purpose切换符合预期 |
| H3: 自我连续性 | Run 4.2 | ✓ Pass | D5 Coherence=0.97 |
| H4: 长期稳定性 | 72h | ✓ Pass | 72小时无故障运行 |
| H5: 必要性 | Ablation | ✓ Pass | Causal > No Purpose (+42.8%) |

---

## Data Availability

All raw data files are available at:
- `experiments/run_4_*_actions.jsonl`
- `experiments/local_72h_20260325/actions.jsonl`
- `experiments/ablation_results.json`

---

*Generated: 2026-03-29*
