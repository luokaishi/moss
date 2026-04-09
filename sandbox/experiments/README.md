# MOSS Experiments

This directory contains all experiments for the MOSS (Multi-Objective Self-Driven System) project.

## Quick Start

```bash
# Install dependencies
pip install -r ../requirements.txt

# Run all experiments
python run_all_experiments.py

# Run specific experiment
python run_experiments.py --strategies moss random --seeds 10 --steps 1000
```

## Experiment Overview

### 1. Controlled Experiments (Core Validation)
**Directory**: `controlled/`
**Purpose**: Validate MOSS vs baseline strategies

| Experiment | Description | Command | Expected Time |
|------------|-------------|---------|---------------|
| Baseline Comparison | MOSS vs Random/CuriosityOnly/SurvivalOnly/FixedWeights | `python run_experiments.py --quick` | ~5s |
| Full Matrix | 5 strategies × 3 environments × 10 seeds | `python run_experiments.py` | ~10s |
| Influence Fix Validation | Test reward hacking prevention | `python validate_influence_fix.py` | ~2s |

**Key Results** (from `results/summary.json`):
- MOSS achieves optimal balance: 4.0 knowledge + 43.1 survival (1000-step simulation)
- vs CuriosityOnly (5.07 knowledge, 19.6 survival - burns out)
- vs SurvivalOnly (0.0 knowledge, 191.1 survival - stagnates)

### 2. LLM Verification
**Purpose**: Test real LLM adaptive behavior

| Model | Status | Command |
|-------|--------|---------|
| DeepSeek-V3 | ✅ Verified (100 steps) | See `multi_model_verification.py` |
| Doubao-Seed-2.0-pro | ✅ Verified (20 steps) | See `multi_model_verification.py` |
| ark-model-3 | ⏸️ Timeout issues | Connection successful but slow |

**Verification Result**: Both models show resource-aware adaptive behavior

### 3. Web Navigation (Complex Environment)
**Purpose**: Test MOSS in realistic web browsing scenario

```bash
python web_navigation_experiment.py --quick    # 1 seed, 50 steps
python web_navigation_experiment.py            # 3 seeds, 100 steps
```

**Environment Features**:
- 5-depth web graph with variable information value
- 4 action types: explore, extract, backtrack, wait
- Resource constraints and costs

**Results**: MOSS maintains balance in complex environment (3.94 info + 100 survival + 3.3 pages)

### 4. Multi-Modal Verification
**Purpose**: Visualize MOSS states using image generation

```bash
python multimodal_moss.py --steps 5
```

**Output**: 5 images representing agent states (stored locally, not in git)

## Configuration

### Experiment Parameters

Edit `config.yaml` or use command-line arguments:

```yaml
# config.yaml example
experiments:
  controlled:
    strategies: [moss, random, curiosity_only, survival_only, fixed_weights]
    environments: [simple, moderate, complex]
    seeds: 10
    max_steps: 1000
  
  llm_verification:
    models: [deepseek-v3, doubao-seed-2.0-pro]
    steps: 20
  
  web_navigation:
    seeds: [42, 123, 456]
    max_steps: 100
```

### Random Seeds

All experiments use fixed seeds for reproducibility:
- Default seeds: 42, 123, 456
- Results should be identical across runs with same seeds

## Output Structure

```
results/
├── all_results.json              # Complete experimental data
├── summary.json                  # Aggregated statistics
├── statistical_analysis_report.txt  # Detailed analysis
└── intermediate_results_*.json   # Checkpoints (every 10 runs)
```

## Reproducibility Checklist

- [x] All code in repository
- [x] Requirements.txt with dependencies
- [x] Fixed random seeds documented
- [x] Example outputs provided
- [x] Configuration files available
- [ ] CI/CD pipeline (pending)
- [ ] Docker image (available in main project)

## Metrics and Evaluation

### Primary Metrics

| Metric | Description | Formula |
|--------|-------------|---------|
| Knowledge Acquisition | Total information gained | Σ(knowledge_units) |
| Resource Efficiency | Knowledge per resource | Knowledge / Tokens |
| Survival Time | Steps until termination | step_count |
| Exploration Ratio | Proportion of exploration actions | explore / total |

### Statistical Tests

- T-test for significance (p < 0.05)
- Cohen's d for effect size
- Mean ± SD across n=10 seeds

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'scipy'`
**Solution**: `pip install scipy`

**Issue**: API timeout for LLM verification
**Solution**: Models may respond slowly; use `--steps 10` for quick test

**Issue**: Out of memory for large experiments
**Solution**: Reduce `max_steps` or number of seeds

## Contributing

To add a new experiment:

1. Create experiment script in `sandbox/experiments/`
2. Add entry to this README
3. Include in `run_all_experiments.py`
4. Provide example output

## References

- Main Project: [github.com/luokaishi/moss](https://github.com/luokaishi/moss)
- Documentation: `../docs/`
- Issues: [github.com/luokaishi/moss/issues](https://github.com/luokaishi/moss/issues)

---

**Last Updated**: 2026-03-10  
**Version**: v0.2.0
