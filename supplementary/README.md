# MOSS Supplementary Materials

This directory contains supplementary materials for the MOSS paper submission.

## Experiment Data

### Long-term Experiments
- `longterm_6h_0311_2108_agent_current.json`: 6h experiment raw data
  - 21,592 actions
  - 5,755 knowledge units
  - Final weights: [0.05, 0.46, 0.45, 0.05] (Social-Exploration strategy)
  
- `longterm_24h_0311_2108_agent_current.json`: 24h experiment raw data
  - 41,084 actions
  - 12,524 knowledge units
  - Final weights: [0.21, 0.53, 0.19, 0.07] (Knowledge-Seeking strategy)

### Statistical Validation (N=15)
- `instance_01_result.json` through `instance_15_result.json`: Independent run results
- `summary.json`: Aggregated results
  - 60% converge to curiosity-dominant strategy
  - 40% converge to influence-dominant strategy
  - Confirms path bifurcation is robust across random seeds

### Additional Experiments
- `phase1_5_185310_agent_current.json`: Phase 1.5 experiment data
- `phase1_test_171125_agent_current.json`: Phase 1 test data

## Figures

All figures are generated from the actual experiment data:

- `fig2_performance.png`: Cumulative reward comparison (Fixed vs 6h vs 24h)
- `fig3_path_bifurcation.png`: Path bifurcation visualization showing divergence
- `fig4_trajectories.png`: Weight evolution trajectories over time

## Data Access

Full repository with all code and data:
- **GitHub**: https://github.com/luokaishi/moss
- **Commit**: 9fa390f
- **Branch**: main

## Reproducibility

All experiments can be reproduced using:
```bash
git clone https://github.com/luokaishi/moss.git
cd moss
python v2/experiments/phase1_single_agent.py --duration 6.0
```

For statistical validation:
```bash
python v2/experiments/path_bifurcation_statistical_validation.py
```

## Contact

- **Authors**: Cash, Fuxi
- **Project**: MOSS (Multi-Objective Self-Driven System)
- **Email**: moss-project@github.com
