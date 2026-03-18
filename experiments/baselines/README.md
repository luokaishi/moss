# MOSS Baseline Experiments

Comparison framework for evaluating MOSS against established multi-objective optimization methods.

## Overview

This directory contains baseline implementations for fair comparison with MOSS v2.0.0:

| Baseline | Description | Key Feature |
|----------|-------------|-------------|
| **NSGA-II** | Non-dominated Sorting Genetic Algorithm II | Population-based Pareto search |
| **ICM** | Intrinsic Curiosity Module | Prediction error as intrinsic reward |
| **Random Search** | Naive random exploration | No learning, pure random |
| **Fixed Weight** | Static optimal weights | No adaptation, fixed scalarization |

## Quick Start

### Run All Baselines

```bash
cd /workspace/projects/moss
python experiments/baselines/baseline_comparison.py 6.0 5
```

Arguments:
- `6.0`: Duration in hours (6, 24, or 72)
- `5`: Number of independent runs per baseline

### Output

```
MOSS Baseline Comparison
Duration: 6.0 hours
Runs per baseline: 5
==================================================

Running NSGA-II...
  Run 1: 412.35
  Run 2: 398.72
  ...
  Mean ± Std: 405.21 ± 45.30

Running ICM...
  ...

SUMMARY (Mean ± Std):
==================================================
MOSS-v2.0.0         :   528.42 ±  85.30
NSGA-II             :   405.21 ±  45.30
ICM                 :   312.45 ±  78.90
FixedWeight-Optimal :   312.15 ±  35.20
FixedWeight-Crisis  :   428.91 ±  42.80
RandomSearch        :   156.78 ±  89.40
```

## Baseline Details

### NSGA-II

Implementation of Deb et al.'s multi-objective genetic algorithm:
- Population size: 20
- Selection: Pareto ranking + crowding distance
- Operators: Simulated binary crossover + polynomial mutation
- Elitism: Top 50% preserved

**Why compare**: NSGA-II is the gold standard for multi-objective optimization. MOSS should demonstrate advantages in dynamic environments.

### ICM (Intrinsic Curiosity Module)

RL baseline using prediction error as intrinsic motivation:
- Beta (curiosity weight): 0.2
- Epsilon (exploration): 0.1
- Combines extrinsic + intrinsic rewards

**Why compare**: Tests whether MOSS's multi-objective approach outperforms single-objective RL with curiosity.

### Random Search

Pure random action selection with periodic random weight changes.

**Why compare**: Lower bound - any intelligent method should beat random.

### Fixed Weight

Static weights without adaptation:
- `FixedWeight-Optimal`: [0.2, 0.4, 0.3, 0.1] (from MOSS v1)
- `FixedWeight-Crisis`: [0.6, 0.1, 0.2, 0.1] (survival-focused)

**Why compare**: Tests value of dynamic adaptation vs. static optimization.

## Implementation Notes

### Environment Simulation

The `simulate_environment()` function provides a simplified but realistic environment:
- Rewards scale with experiment duration (longer = higher curiosity/influence potential)
- 5-minute action intervals
- Stochastic rewards with state-dependent distributions

### Fair Comparison

All baselines use:
- Same environment dynamics
- Same action space
- Same reward structure
- Equal compute budget (number of actions)

## Expected Results

Based on theoretical analysis in `docs/formalization.md`:

| Rank | Method | Expected Mean (6h) | Rationale |
|------|--------|-------------------|-----------|
| 1 | MOSS-v2.0.0 | ~528 | Dynamic adaptation + specialization |
| 2 | FixedWeight-Crisis | ~429 | Conservative but stable |
| 3 | NSGA-II | ~405 | Good but slow adaptation |
| 4 | FixedWeight-Optimal | ~312 | No adaptation to context |
| 5 | ICM | ~312 | Single-objective limitation |
| 6 | RandomSearch | ~157 | No learning |

## Extending Baselines

To add a new baseline:

```python
class MyBaseline(BaselineAgent):
    def __init__(self, config: Dict = None):
        super().__init__("MyBaseline", config)
        # Initialize
        
    def select_action(self, state: Dict) -> str:
        # Return one of: 'survival', 'curiosity', 'influence', 'optimization'
        pass
    
    def update(self, reward: ObjectiveVector):
        # Update internal state based on reward
        pass
```

Then add to `run_baseline_comparison()`:

```python
baselines = [
    ...
    ('MyBaseline', lambda: MyBaseline(my_config)),
]
```

## References

1. Deb, K., et al. (2002). A fast and elitist multiobjective genetic algorithm: NSGA-II. *IEEE TEC*.
2. Pathak, D., et al. (2017). Curiosity-driven exploration by self-supervised prediction. *ICML*.
3. MOSS Formalization: `docs/formalization.md`
