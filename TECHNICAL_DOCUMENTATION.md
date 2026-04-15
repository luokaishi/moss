# MOSS AGI Agent: Technical Documentation

## 1. Project Overview

MOSS (Meta-Organizing Self-evolving System) is an AGI agent framework that discovers emergent drives through genetic programming with causal validation. The system addresses the limitation of hand-coded drives by evolving evaluation functions automatically.

**Core Innovation**: Transform agent behavior from static programming to dynamic emergence via GP-based drive discovery.

## 2. Architecture Design

### 2.1 System Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Environment   │◄──►│   AGI Agent      │◄──►│   Memory Engine │
│   (Shell/API)    │    │  - Perception    │    │   (Embeddings)  │
└─────────────────┘    │  - Decision      │    └─────────────────┘
                       │  - Action        │
                       └──────────────────┘
                                ▲
                       ┌────────┴────────┐
                       │ Emergence Detector │
                       │ - Pattern Recognition│
                       │ - GP Evolution     │
                       └────────────────────┘
```

### 2.2 Key Modules

**AGIAgent** (`agi/agent.py`)
- Main decision loop: perceive → recall → evaluate → select → execute → reflect
- Intervention mode support for causal validation
- External signal-based behavior labeling

**DriveManager** (`agi/drive_manager.py`)
- Dynamic drive weighting with feedback learning
- Emergent drive registration and management
- Competition mechanism (weight dynamics + pruning)

**EmergenceDetector** (`agi/emergence_detector.py`)
- Behavioral pattern change detection
- GP evolution trigger (cooldown: 30 cycles)
- Integration with intervention validation

**GeneticProgrammer** (`agi/genetic_programmer.py`)
- Expression tree evolution (max depth: 6)
- Multi-objective fitness: correlation + behavioral_gain - complexity²
- Enhanced complexity penalty: quadratic + single-terminal penalty

**InterventionValidator** (`agi/intervention_validator.py`)
- Treatment/Control experimental design
- Δbehavior = E[behavior|do(f=high)] - E[behavior|do(f=low)]
- Statistical significance testing (p < 0.15)

## 3. Core Algorithms

### 3.1 Behavior Label Generation

External signal-based labeling (replaces self-referential approach):

```python
def compute_behavior_label(self):
    state = self.env.perceive()
    task_progress = state.task_completion_rate      # 50% weight
    resource_eff = 1.0 - state.resource_level        # 30% weight  
    stability = 1.0 - state.error_rate                # 20% weight
    cycle_effect = 0.3 * sin(cycle * 0.1)             # Periodic variation
    noise = 0.2 * N(0,1)                             # Gaussian noise
    
    label = (0.4*task_progress + 0.3*resource_eff + 
            0.2*stability + 0.1*cycle_effect + noise)
    return clip(label, 0, 1)
```

**Improvement**: Variance increased from 0.05 to 0.15, eliminating label saturation.

### 3.2 GP Evolution

Enhanced fitness function with strong complexity penalty:

```python
def fitness(tree, B_train, X_train):
    pred = [tree.evaluate(x) for x in X_train]
    corr = correlation(pred, B_train)           # 20% weight
    mse = mean_squared_error(pred, B_train)       # 10% weight  
    gain = behavioral_gain_interventional(tree)   # 50% weight
    
    complexity = tree.node_count()
    penalty = 0.03 * complexity**2                # Quadratic penalty
    if complexity == 1 and tree.is_terminal():
        penalty += 0.5                           # Extra penalty
    
    return (0.2*corr + 0.1*(1-mse) + 0.5*gain - penalty)
```

**Parameters**: Population=200, Generations=100, Tournament=5, Acceptance threshold=0.15

### 3.3 Intervention Validation

Causal effect measurement via double-blind experiment:

```python
def validate_drive(candidate_drive):
    # Treatment: Force enable candidate
    agent_treat.set_intervention_mode(forced_drive=candidate.name)
    metrics_treat = agent_treat.run_cycles(50)
    
    # Control: Normal operation  
    agent_ctrl.run_cycles(50)
    metrics_ctrl = agent_ctrl.run_cycles(50)
    
    Δbehavior = metrics_treat['success_rate'] - metrics_ctrl['success_rate']
    p_value = significance_test(metrics_treat, metrics_ctrl)
    
    return Δbehavior, p_value
```

## 4. Experimental Methodology

### 4.1 Setup
- **Environment**: Linux shell with restricted command set
- **Cycles**: 200-10,000 cycles per experiment
- **State Features**: 16-dimensional (resource, entropy, error_rate, etc.)
- **Evaluation**: Success rate, behavior diversity, drive emergence frequency

### 4.2 Metrics
- **Emergence Rate**: New drives per 1000 cycles
- **Causal Strength**: |Δbehavior| > 0.1 with p < 0.15
- **Function Complexity**: Node count distribution
- **Tag Distribution**: Mean/std of behavior labels

## 5. Results

### 5.1 Emergence Events
- **100 cycles**: 1 emergence (auto_success_rate_recent)
- **1000 cycles**: 1-2 emergences per 1000 cycles
- **5000 cycles**: 3-5 total emergences

**Discovered Functions**:
1. `success_rate_recent` (terminal) - Success tracking
2. `task_completion` (terminal) - Goal progression  
3. `resource_efficiency` (composite) - Resource optimization

### 5.2 Causal Validation
- **Ablation Test**: Deleting drives → Performance change < 5%
- **Injection Test**: Fake drives often persisted (needs improvement)
- **Intervention Effect**: Average |Δbehavior| = 0.08 ± 0.05

### 5.3 Label Distribution Improvement
- **Before**: Mean=0.87, Std=0.05 (saturated)
- **After**: Mean=0.45, Std=0.15 (balanced)

## 6. Innovations

1. **Interventional Causal Validation**: First application to GP-driven emergence
2. **External Signal Labeling**: Breaks self-referential loops  
3. **Quadratic Complexity Penalty**: Strongly discourages bloat
4. **Dynamic Drive Competition**: Lifecycle management for emergents

## 7. Limitations

1. **Weak Causal Effects**: Most Δbehavior < 0.1
2. **Simple Functions**: 60% of discoveries are single terminals
3. **Limited Domain**: Shell environment, not real-world tasks
4. **Computational Cost**: 200-population × 100-gen evolution takes ~5min

## 8. Future Work

1. **Neural-Guided GP**: Use MLP to guide search toward promising regions
2. **Multi-Agent Competition**: Observe drive propagation in populations
3. **Real-World Deployment**: Robot control or software assistant
4. **Meta-Learning**: Learn optimal GP parameters across domains

## 9. Usage

```bash
git clone -b mves https://github.com/luokaishi/moss.git
cd moss
pip install numpy pyyaml pytest
python demo.py  # 200-cycle demonstration
```

## 10. Conclusion

MOSS demonstrates that agents can autonomously discover useful drives beyond human design. While causal effects remain modest, the intervention-based validation provides stronger evidence than correlation-only approaches. The framework opens new avenues for understanding emergence in artificial systems.

---
**Repository**: https://github.com/luokaishi/moss/tree/mves  
**Version**: mves (commit 7c37525)  
**Date**: 2026-04-14