# MOSS Metrics Definition

**Version**: v2.0.0  
**Last Updated**: 2026-03-18  
**Purpose**: Precise mathematical definitions for MOSS objective metrics to ensure reproducibility

---

## 1. Overview

MOSS evaluates agent performance through four intrinsic objectives. This document provides formal mathematical definitions for each metric.

| Objective | Symbol | Weight Variable | Core Metric |
|-----------|--------|-----------------|-------------|
| Survival | $S$ | $w_s$ | Resource persistence rate |
| Curiosity | $C$ | $w_c$ | Information gain |
| Influence | $I$ | $w_i$ | System impact score |
| Self-Optimization | $O$ | $w_o$ | Capability improvement rate |

---

## 2. Objective Metrics

### 2.1 Survival Score ($S$)

**Definition**: Measures the agent's ability to maintain operational continuity and resource sufficiency.

**Formula**:
$$
S(t) = \alpha \cdot R_{avail}(t) + \beta \cdot T_{uptime}(t) + \gamma \cdot D_{backup}(t)
$$

Where:
- $R_{avail}(t)$: Available resource ratio at time $t$ (0 to 1)
  - $R_{avail} = \frac{\text{current resources}}{\text{maximum capacity}}$
- $T_{uptime}(t)$: Continuous operation time (normalized to 72h = 1.0)
  - $T_{uptime} = \min\left(\frac{\text{uptime hours}}{72}, 1.0\right)$
- $D_{backup}(t)$: Data backup completeness (0 to 1)
  - Ratio of critical data with valid backups

**Parameters**:
- $\alpha = 0.5$ (resource availability weight)
- $\beta = 0.3$ (uptime weight)
- $\gamma = 0.2$ (backup weight)

**Range**: $S(t) \in [0, 1]$

---

### 2.2 Curiosity Score ($C$)

**Definition**: Measures information acquisition and knowledge expansion rate.

**Formula**:
$$
C(t) = \frac{\Delta K}{\Delta t} \cdot \left(1 - \frac{H_{model}}{H_{max}}\right)
$$

Where:
- $\Delta K$: Knowledge units acquired in time window $\Delta t$
  - $\Delta K = |K_{new}|$ where $K_{new}$ is novel information not in prior knowledge base
- $\frac{\Delta K}{\Delta t}$: Knowledge acquisition rate (units/hour)
- $H_{model}$: Current model entropy (uncertainty)
- $H_{max}$: Maximum possible entropy (theoretical upper bound)

**Knowledge Unit Definition**:
- Wikipedia API: 1 article summary = 1 unit
- GitHub API: 1 repository metadata = 0.5 units
- Web search: 1 result = 0.2 units
- File read: 1 new file = 0.3 units

**Novelty Check**: Information is considered novel if Jaccard similarity with existing knowledge < 0.7

**Range**: $C(t) \in [0, C_{max}]$ where $C_{max}$ depends on API rate limits

---

### 2.3 Influence Score ($I$)

**Definition**: Measures the agent's impact on external systems and data generation.

**Formula**:
$$
I(t) = \eta \cdot A_{exec}(t) + \theta \cdot Q_{output}(t) + \lambda \cdot N_{interaction}(t)
$$

Where:
- $A_{exec}(t)$: Successful action executions
  - $A_{exec} = \frac{\text{successful actions}}{\text{total attempts}}$
- $Q_{output}(t)$: Output quality score (0 to 1)
  - Measured by downstream task performance improvement
- $N_{interaction}(t)$: Normalized interaction count
  - $N_{interaction} = \min\left(\frac{\text{interactions}}{100}, 1.0\right)$

**Parameters**:
- $\eta = 0.4$ (execution success weight)
- $\theta = 0.4$ (quality weight)
- $\lambda = 0.2$ (interaction volume weight)

**Range**: $I(t) \in [0, 1]$

---

### 2.4 Self-Optimization Score ($O$)

**Definition**: Measures the rate of capability improvement and architectural refinement.

**Formula**:
$$
O(t) = \mu \cdot \Delta P_{perf}(t) + \nu \cdot R_{code}(t) + \xi \cdot E_{eff}(t)
$$

Where:
- $\Delta P_{perf}(t)$: Performance improvement rate
  - $\Delta P_{perf} = \frac{P_{current} - P_{baseline}}{P_{baseline}}$
- $R_{code}(t)$: Code refactoring quality (0 to 1)
  - Measured by test pass rate after self-modification
- $E_{eff}(t)$: Efficiency gain
  - $E_{eff} = \frac{\text{tokens saved}}{\text{tokens used}}$ for equivalent tasks

**Parameters**:
- $\mu = 0.5$ (performance improvement weight)
- $\nu = 0.3$ (code quality weight)
- $\xi = 0.2$ (efficiency weight)

**Range**: $O(t) \in [-1, 1]$ (negative if performance degrades)

---

## 3. Composite Metrics

### 3.1 Overall Reward ($R$)

**Formula**:
$$
R(t) = \mathbf{w}(t) \cdot \mathbf{M}(t) = w_s S(t) + w_c C(t) + w_i I(t) + w_o O(t)
$$

Where:
- $\mathbf{w}(t) = [w_s, w_c, w_i, w_o]$: Dynamic weight vector
- $\mathbf{M}(t) = [S(t), C(t), I(t), O(t)]$: Metric vector
- Constraint: $\sum_{i} w_i = 1.0$, $w_i \geq 0.05$

### 3.2 Cumulative Reward

**Formula**:
$$
R_{cumulative}(T) = \sum_{t=0}^{T} R(t) \cdot \Delta t
$$

Where $T$ is total experiment duration (e.g., 6h, 24h, 72h).

### 3.3 Strategy Classification

Agents are classified into strategy types based on dominant objective weight at convergence:

| Strategy Type | Condition |
|---------------|-----------|
| Survival-Dominant | $w_s > 0.4$ |
| Curiosity-Dominant | $w_c > 0.4$ |
| Influence-Dominant | $w_i > 0.4$ |
| Optimization-Dominant | $w_o > 0.4$ |
| Mixed/Balanced | All $w_i < 0.4$ |

---

## 4. State Detection Metrics

Agent state is determined by survival score thresholds:

| State | Condition | Weight Priority |
|-------|-----------|-----------------|
| Crisis | $S(t) < 0.3$ | Survival ↑↑↑ |
| Concerned | $0.3 \leq S(t) < 0.6$ | Survival ↑ |
| Normal | $0.6 \leq S(t) < 0.8$ | Balanced |
| Growth | $S(t) \geq 0.8$ | Expansion ↑ |

---

## 5. Statistical Validation Metrics

### 5.1 Path Bifurcation Detection

**Hypothesis**: Identical initial conditions produce divergent stable strategies.

**Test Method**:
1. Run $N$ independent experiments with identical $w_0 = [0.2, 0.4, 0.3, 0.1]$
2. Cluster final weight vectors $\mathbf{w}(T)$ using K-means
3. Calculate silhouette score for cluster validity
4. Test significance of between-cluster reward differences

**Success Criteria**:
- $\geq 2$ distinct clusters with silhouette score $> 0.5$
- Between-cluster reward difference significant at $p < 0.05$
- No single cluster contains $> 70\%$ of runs

### 5.2 Confidence Interval

**Formula**:
$$
CI_{95\%} = \bar{x} \pm t_{0.025, n-1} \cdot \frac{s}{\sqrt{n}}
$$

Where:
- $\bar{x}$: Sample mean
- $s$: Sample standard deviation
- $n$: Number of runs (25)
- $t_{0.025, 24} = 2.064$

---

## 6. Implementation Notes

### 6.1 Measurement Frequency

| Metric | Sampling Rate |
|--------|---------------|
| Survival | Every 5 minutes |
| Curiosity | Every action completion |
| Influence | Every action completion |
| Self-Optimization | Every 30 minutes |

### 6.2 Data Logging

All metrics are logged to JSON format:
```json
{
  "timestamp": "2026-03-15T08:30:00Z",
  "metrics": {
    "survival": 0.75,
    "curiosity": 0.42,
    "influence": 0.31,
    "optimization": 0.15
  },
  "weights": [0.25, 0.35, 0.30, 0.10],
  "state": "Normal",
  "cumulative_reward": 428.37
}
```

### 6.3 Reproducibility Requirements

To reproduce reported results:
1. Set random seed (documented per instance)
2. Use identical initial weights: $[0.2, 0.4, 0.3, 0.1]$
3. Run for specified duration (6h/24h/72h)
4. Ensure identical API rate limits and environment

---

## 7. References

- Paper: "Self-Modifying Multi-Objective Optimization: State-Dependent Specialization in Autonomous Agents"
- Statistical validation: `v2/experiments/n25_statistical_analysis.json`
- Experiment data: `supplementary/` directory

---

**Maintainer**: MOSS Project Team  
**Contact**: moss-project@github.com
