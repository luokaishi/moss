# MOSS - Multi-Objective Self-Driven Agent

> An autonomous AI agent that operates without external tasks, discovering and evolving its own drive functions through genetic programming.

## What is MOSS?

MOSS is a research prototype exploring whether AI systems can develop **intrinsic motivations** without task-specific reward signals. It combines multi-objective drive systems with genetic programming (GP) to discover and validate emergent behavioral patterns.

**Key idea**: Instead of optimizing for externally defined rewards, the agent uses internal drive evaluations (survival, curiosity, influence, optimization) and autonomously discovers new drive functions when behavioral patterns shift.

## Architecture

```
agi/
├── agent.py                 # Main agent loop: perceive → evaluate → select → execute → reflect
├── drive_manager.py         # Multi-drive weight management with dynamic updates
├── emergence_detector.py    # Behavior change detection → triggers GP evolution
├── genetic_programmer.py    # GP core: evolves eval functions from behavior data
├── environment.py           # Shell environment interaction
├── memory_engine.py         # Experience storage and retrieval
└── behavior_tracker.py      # Action logging and pattern detection
```

### Drive System

The agent starts with 4 built-in drives:

| Drive | Weight | What it evaluates |
|-------|--------|------------------|
| **survival** | 0.25 → 0.60 | Resource level, health, uptime |
| **curiosity** | 0.25 → 0.14 | Environment entropy, exploration novelty |
| **influence** | 0.25 → 0.14 | External interactions, task completion |
| **optimization** | 0.25 → 0.11 | Efficiency, improvement space |

Weights update dynamically based on feedback: `delta = lr × (reward - 0.5)`

### GP-Based Emergence

When behavior patterns shift significantly, the system triggers genetic programming to discover a new eval function `f(env_state) → [0, 1]`:

1. **Data collection**: Buffer recent environment states + behavior labels
2. **GP evolution**: 100 individuals × 50 generations, optimizing:
   ```
   fitness = 0.3×correlation + 0.2×(1-MSE) + 0.3×behavioral_gain - 0.01×complexity
   ```
3. **Triple validation**: correlation > 0.3, behavioral_gain > 0.1, null model p < 0.05
4. **Integration**: Evolved function becomes the emergent drive's eval_fn

**Result from test**: The system discovered `file_count_norm²` with correlation=0.87, behavioral_gain=1.0

### Feature Space (16 dimensions)

**Static (8)**: resource_level, environment_entropy, error_rate, file_count_norm, visited_ratio, uptime_norm, interaction_norm, task_completion

**Dynamic (8)**: entropy_delta, entropy_moving_avg, entropy_variance, error_rate_delta, resource_delta, behavior_diversity, novel_command_rate, success_rate_recent

## Quick Start

```bash
pip install -e .
python demo.py                  # Run 200-cycle demo
python examples/run_experiment.py --cycles 5000  # Full experiment
python examples/causal_experiments.py --type all  # Causal verification
```

## Experiments & Results

### 57K+ Cycles Analysis

134 checkpoints across 7 independent experiments analyzed:

| Metric | Value |
|--------|-------|
| Total cycles | 57,474 |
| Unique commands | 536 |
| Survival drive dominance | 0.30 → 0.60 (doubled) |
| Emergence detection rate | 6/7 experiments (86%) |

### Causal Verification (4 experiments × 5,000 cycles)

Responding to external review criticism about causality:

| Experiment | Operation | Emergence? | Evidence |
|-----------|-----------|------------|----------|
| Drive Ablation | Disable emergent drives | Still detected | Partial |
| Drive Amplification | Amplify weight to 0.5 | Different drive emerged | Behavioral change confirmed |
| Command Restriction | Remove python3/find | **CM still emerged** | Not command-dependent |
| Random Baseline | Random action selection | **Zero emergence** | Excludes statistical artifact |

### Survival Dominance

The most scientifically valuable finding: survival drive naturally becomes the dominant attractor (weight 0.60) even without any explicit survival pressure — consistent with evolutionary theory, self-organization, and Friston's active inference framework.

## External Evaluation Response

The project underwent scientific peer review (ChatGPT-based) focusing on:

| Review Criticism | Status | Response |
|-----------------|--------|----------|
| "Emergence is just behavior clustering" | ✅ Addressed | Random baseline proves emergence requires drive system |
| "eval functions are constants" | ✅ Addressed | GP now evolves state-dependent functions |
| "Semantic labels are human-injected" | ✅ Addressed | Removed BEHAVIOR_SEMANTICS, auto-naming from function structure |
| "Causality not proven" | ✅ Addressed | Behavioral gain metric + causal experiments |
| "Feature space too human-defined" | ⚠️ Partial | 8 dynamic features added; latent space planned for v6 |

### Scientific Honesty

What we claim vs. don't claim:

| Claim | Validity |
|-------|----------|
| "Drive system runs without external tasks" | ✅ Verified (57K+ cycles) |
| "Survival becomes dominant attractor" | ✅ Verified |
| "Emergence is not a statistical artifact" | ✅ Verified (random baseline) |
| "System discovers its own eval functions" | ✅ Verified (GP) |
| "True intrinsic motivation emergence" | ❌ Not yet proven (feature space is human-defined) |
| "AGI" | ❌ Not claimed |

## Development Roadmap

- [x] Core agent framework with 4 drives
- [x] 57K+ cycle experiment with analysis
- [x] Causal verification experiments
- [x] GP-based self-generated eval functions
- [ ] Online drive competition (candidate functions compete in real-time)
- [ ] Latent state space (encoder for feature discovery)
- [ ] MLP-based drive discovery (v6)
- [ ] Drive ecosystem (multiple evolved functions competing)

## Documentation

| Document | Description |
|----------|-------------|
| `MOSS_Final_Report.md` | Comprehensive project report |
| `causal_verification_report.md` | Causal experiment results |
| `gp_implementation_report.md` | GP emergence implementation details |
| `proposal_gp_emergence.md` | GP design proposal (reviewed) |
| `response_to_chatgpt_evaluation.md` | Response to external review |
| `response_to_gp_review.md` | Response to GP proposal review |

## Requirements

- Python 3.8+
- numpy
- pyyaml
- No external ML frameworks required (pure numpy GP)

## License

MIT
