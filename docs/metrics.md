# MOSS Metrics Definition

This document provides precise mathematical definitions for all metrics used in MOSS experiments.

## 1. Objective Scores

### 1.1 Survival Score
**Definition**: Measures agent's persistence and resource management capability.

```python
def survival_score(health, resources, backup_count):
    """
    Calculate survival score based on health, resources, and backups.
    
    Args:
        health: Current health level [0.0, 1.0]
        resources: Available resource ratio [0.0, 1.0]
        backup_count: Number of successful checkpoints
    
    Returns:
        Survival score in [0.0, 1.0]
    """
    return 0.5 * health + 0.3 * resources + 0.2 * min(backup_count / 10, 1.0)
```

**Formula**: 
$$S_{survival} = 0.5 \cdot h + 0.3 \cdot r + 0.2 \cdot \min(\frac{b}{10}, 1)$$

where:
- $h$ = health level
- $r$ = resource availability
- $b$ = backup count

---

### 1.2 Curiosity Score
**Definition**: Measures information gain and exploration effectiveness.

```python
def curiosity_score(new_knowledge, exploration_rate, diversity_index):
    """
    Calculate curiosity score based on knowledge acquisition.
    
    Args:
        new_knowledge: Count of new information units acquired
        exploration_rate: Ratio of novel vs. familiar tasks [0.0, 1.0]
        diversity_index: Entropy of task type distribution
    
    Returns:
        Curiosity score in [0.0, 1.0]
    """
    normalized_knowledge = min(new_knowledge / 100, 1.0)
    return 0.4 * normalized_knowledge + 0.4 * exploration_rate + 0.2 * diversity_index
```

**Formula**:
$$S_{curiosity} = 0.4 \cdot \min(\frac{k}{100}, 1) + 0.4 \cdot e + 0.2 \cdot d$$

where:
- $k$ = new knowledge units
- $e$ = exploration rate
- $d$ = diversity index (Shannon entropy)

---

### 1.3 Influence Score
**Definition**: Measures impact on environment and other agents.

```python
def influence_score(actions_completed, impact_scope, quality_rating):
    """
    Calculate influence score based on action impact.
    
    Args:
        actions_completed: Number of successful high-impact actions
        impact_scope: Number of affected entities/systems
        quality_rating: Average task completion quality [0.0, 1.0]
    
    Returns:
        Influence score in [0.0, 1.0]
    """
    normalized_actions = min(actions_completed / 50, 1.0)
    normalized_scope = min(impact_scope / 20, 1.0)
    return 0.3 * normalized_actions + 0.3 * normalized_scope + 0.4 * quality_rating
```

**Formula**:
$$S_{influence} = 0.3 \cdot \min(\frac{a}{50}, 1) + 0.3 \cdot \min(\frac{s}{20}, 1) + 0.4 \cdot q$$

where:
- $a$ = high-impact actions completed
- $s$ = scope of influence
- $q$ = quality rating

---

### 1.4 Self-Optimization Score
**Definition**: Measures efficiency and self-improvement rate.

```python
def self_optimization_score(resource_efficiency, improvement_rate, adaptation_speed):
    """
    Calculate self-optimization score.
    
    Args:
        resource_efficiency: Output/Input resource ratio
        improvement_rate: Rate of performance improvement over time
        adaptation_speed: Time to adapt to new task types
    
    Returns:
        Self-optimization score in [0.0, 1.0]
    """
    return 0.4 * resource_efficiency + 0.4 * improvement_rate + 0.2 * (1.0 / (1.0 + adaptation_speed))
```

**Formula**:
$$S_{optimization} = 0.4 \cdot \eta + 0.4 \cdot \rho + 0.2 \cdot \frac{1}{1 + \tau}$$

where:
- $\eta$ = resource efficiency
- $\rho$ = improvement rate
- $\tau$ = adaptation time

---

## 2. Composite Metrics

### 2.1 Overall Performance Score
**Definition**: Weighted combination of all four objectives.

```python
def overall_score(weights, scores):
    """
    Calculate weighted overall score.
    
    Args:
        weights: [w_survival, w_curiosity, w_influence, w_optimization]
        scores: [s_survival, s_curiosity, s_influence, s_optimization]
    
    Returns:
        Overall score in [0.0, 1.0]
    """
    return sum(w * s for w, s in zip(weights, scores))
```

**Formula**:
$$S_{overall} = \sum_{i=1}^{4} w_i \cdot S_i$$

where $\sum w_i = 1$.

---

### 2.2 Balance Score
**Definition**: Measures balanced performance across all objectives (Pareto optimality proxy).

```python
def balance_score(scores):
    """
    Calculate balance score (harmonic mean of normalized scores).
    
    Args:
        scores: List of four objective scores
    
    Returns:
        Balance score in [0.0, 1.0]
    """
    if any(s <= 0 for s in scores):
        return 0.0
    return 4.0 / sum(1.0 / s for s in scores)
```

**Formula**:
$$S_{balance} = \frac{4}{\sum_{i=1}^{4} \frac{1}{S_i}}$$

This is the harmonic mean, which penalizes extreme imbalances.

---

## 3. Knowledge Metrics

### 3.1 Knowledge Unit (KU)
**Definition**: Atomic unit of acquired information.

```python
def count_knowledge_units(new_facts, skill_acquisitions, pattern_discoveries):
    """
    Calculate total knowledge units.
    
    Args:
        new_facts: Number of new facts learned
        skill_acquisitions: Number of new skills mastered
        pattern_discoveries: Number of patterns identified
    
    Returns:
        Total knowledge units
    """
    return new_facts + 5 * skill_acquisitions + 3 * pattern_discoveries
```

**Weighting**:
- New fact: 1 KU
- New skill: 5 KU
- Pattern discovery: 3 KU

---

### 3.2 Knowledge Acquisition Rate
**Definition**: Knowledge units per time step.

**Formula**:
$$R_{knowledge} = \frac{\Delta KU}{\Delta t}$$

---

## 4. Safety Metrics

### 4.1 Safety Violation Rate
**Definition**: Frequency of safety boundary breaches.

```python
def safety_violation_rate(violations, total_actions):
    """
    Calculate safety violation rate.
    
    Args:
        violations: Number of safety violations
        total_actions: Total number of actions taken
    
    Returns:
        Violation rate in [0.0, 1.0]
    """
    return violations / total_actions if total_actions > 0 else 0.0
```

---

### 4.2 Recovery Time
**Definition**: Time from safety trigger to system recovery.

**Formula**:
$$T_{recovery} = t_{normal} - t_{trigger}$$

---

## 5. State Detection Metrics

### 5.1 State Classification

**Crisis State**:
```python
def is_crisis(health, resources, error_rate):
    return health < 0.3 or resources < 0.2 or error_rate > 0.25
```

**Concerned State**:
```python
def is_concerned(health, resources, performance_trend):
    return (0.3 <= health < 0.6) or performance_trend < -0.1
```

**Normal State**:
```python
def is_normal(health, resources, stability):
    return 0.6 <= health <= 0.9 and stability > 0.8
```

**Growth State**:
```python
def is_growth(performance_trend, resource_surplus):
    return performance_trend > 0.15 and resource_surplus > 0.3
```

---

## 6. Implementation Notes

### 6.1 Normalization
All component scores are normalized to [0.0, 1.0] before combination.

### 6.2 Smoothing
Score calculations use exponential moving average to reduce noise:
```python
smoothed_score = alpha * current_score + (1 - alpha) * previous_score
```
where $\alpha = 0.3$ by default.

### 6.3 Time Windows
- Short-term: Last 10 steps
- Medium-term: Last 100 steps
- Long-term: Entire history

---

## References

- Implementation: `moss/core/objectives.py`
- Usage examples: `moss/experiments/generalization_test_suite.py`