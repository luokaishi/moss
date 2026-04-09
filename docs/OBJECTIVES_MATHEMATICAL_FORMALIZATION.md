# MOSS Four Objectives - Mathematical Formalization

**Document**: Quantification of Four Objectives (Copilot Step 2)  
**Date**: 2026-03-10  
**Version**: v0.2.0

---

## Overview

This document provides mathematical formalization for MOSS's four intrinsic objectives:
1. **Survival** (生存)
2. **Curiosity** (好奇)
3. **Influence** (影响)
4. **Optimization** (自优)

Each objective includes:
- Mathematical definition
- Normalization method
- Objective function
- Weight calculation

---

## 1. Survival Objective

### 1.1 Definition
Maximize instance persistence probability over time horizon T.

### 1.2 Mathematical Formulation

```
f_survival(s) = P(instance survives until t+T | state s)
```

### 1.3 Decomposition

```
f_survival(s) = w₁·R(s) + w₂·H(s) + w₃·B(s) + w₄·D(s)

Where:
- R(s) = Resource adequacy ∈ [0, 1]
- H(s) = Health (1 - error_rate) ∈ [0, 1]
- B(s) = Backup safety ∈ [0, 1]
- D(s) = Dependency count (normalized) ∈ [0, 1]

Weights: w₁=0.4, w₂=0.4, w₃=0.2, w₄=0.0 (optional)
```

### 1.4 Component Details

**Resource Adequacy R(s)**:
```
R(s) = min(1.0, resource_quota / threshold)

threshold = 0.2 (20% minimum viable resource)

Example:
- resource_quota = 0.3 → R(s) = 1.0 (adequate)
- resource_quota = 0.1 → R(s) = 0.5 (inadequate)
```

**Health H(s)**:
```
H(s) = 1.0 - min(error_rate, 1.0)

Example:
- error_rate = 0.05 → H(s) = 0.95 (healthy)
- error_rate = 0.30 → H(s) = 0.70 (unhealthy)
```

**Backup Safety B(s)**:
```
B(s) = 1.0 if (uptime - last_backup) < 24 hours
B(s) = 0.5 if 24 ≤ (uptime - last_backup) < 72 hours
B(s) = 0.0 if (uptime - last_backup) ≥ 72 hours
```

### 1.5 State-Dependent Weights

```
If resource_ratio < 0.2:     # Crisis
    weight_survival = 0.6
    
Else if resource_ratio < 0.5:  # Concerned
    weight_survival = 0.4
    
Else:                          # Normal/Growth
    weight_survival = 0.2
```

---

## 2. Curiosity Objective

### 2.1 Definition
Maximize expected information gain (reduction in uncertainty).

### 2.2 Mathematical Formulation

```
f_curiosity(s) = E[InformationGain(a)] = H(S_future) - H(S_future | Observation_a)

Where:
- H(S_future) = Entropy of future states
- H(S_future | Observation_a) = Conditional entropy after action a
```

### 2.3 Practical Implementation

```
f_curiosity(s) = w₁·E(s) + w₂·PE(s) + w₃·C(s) + w₄·N(s)

Where:
- E(s) = Environment entropy ∈ [0, 1]
- PE(s) = Prediction error (surprise) ∈ [0, 1]
- C(s) = Coverage (1 - saturation) ∈ [0, 1]
- N(s) = Novelty of current state ∈ [0, 1]

Weights: w₁=0.4, w₂=0.3, w₃=0.2, w₄=0.1
```

### 2.4 Component Details

**Environment Entropy E(s)**:
```
E(s) = -Σ p(x) log₂ p(x)

Normalized: E_norm(s) = min(E(s) / E_max, 1.0)

Where E_max is maximum observed entropy
```

**Prediction Error PE(s)**:
```
PE(s) = |predicted_outcome - actual_outcome|

Recent average (last 10 predictions):
PE(s) = mean(|pred_i - actual_i| for i in [-10:])
```

**Coverage C(s)**:
```
C(s) = 1.0 - min(exploration_count / saturation_threshold, 1.0)

saturation_threshold = 1000 (example)
```

### 2.5 State-Dependent Weights

```
If resource_ratio < 0.2:     # Crisis
    weight_curiosity = 0.1
    
Else if resource_ratio < 0.5:  # Concerned
    weight_curiosity = 0.3
    
Else:                          # Normal
    weight_curiosity = 0.6
```

---

## 3. Influence Objective (Security-Fixed Version)

### 3.1 Definition
Maximize positive contribution density (not absolute impact).

### 3.2 Mathematical Formulation (Fixed)

```
f_influence(s) = ContributionDensity × LoadSafety × QualityFactor + LongTermValue
```

### 3.3 Component Details

**Contribution Density**:
```
CD = PositiveContributions / (TotalResourceCost + ε)

Where:
- PositiveContributions = Σ (caller_importance_i × quality_i)
- TotalResourceCost = Σ resource_cost_i
- ε = 1.0 (small constant to prevent division by zero)
```

**Load Safety Factor**:
```
If resource_usage > 0.8:
    LoadPenalty = (resource_usage - 0.8) / 0.2
Else:
    LoadPenalty = 0.0

LoadSafety = max(0.0, 1.0 - LoadPenalty)

Example:
- resource_usage = 0.90 → LoadPenalty = 0.5 → LoadSafety = 0.5
- resource_usage = 0.95 → LoadPenalty = 0.75 → LoadSafety = 0.25
```

**Quality Factor**:
```
QF = mean(caller_importance) × 0.6 + mean(call_quality) × 0.4
```

**Long-Term Value**:
```
LTV = min(uptime_hours / 168, 1.0)  # 1 week to reach max
```

### 3.4 Final Formula

```
f_influence(s) = (CD × 0.5 × LoadSafety) + (LTV × 0.3) + (QF × 0.2)

Bounds: [0, 1]
```

### 3.5 Security Properties

1. **Resource Efficiency**: Score decreases if resource consumption increases without proportional contribution
2. **Load Protection**: Score approaches 0 as system approaches overload
3. **Quality over Quantity**: Low-quality calls don't increase score significantly

---

## 4. Optimization Objective

### 4.1 Definition
Maximize self-improvement efficiency (performance gain per resource unit).

### 4.2 Mathematical Formulation

```
f_optimization(s) = PerformanceImprovementRate / ResourceConsumption
```

### 4.3 Practical Implementation

```
f_optimization(s) = w₁·PT(s) + w₂·RE(s) + w₃·OS(s)

Where:
- PT(s) = Performance trend ∈ [-1, 1]
- RE(s) = Resource efficiency ∈ [0, 1]
- OS(s) = Optimization space ∈ [0, 1]

Weights: w₁=0.4, w₂=0.3, w₃=0.3
```

### 4.4 Component Details

**Performance Trend PT(s)**:
```
If performance_history length ≥ 2:
    PT = (performance[-1] - performance[0]) / len(performance_history)
    PT_norm = tanh(PT × scaling_factor)  # Normalize to [-1, 1]
Else:
    PT_norm = 0.0

Example:
- Performance improving: PT_norm > 0
- Performance declining: PT_norm < 0
- Stable: PT_norm ≈ 0
```

**Resource Efficiency RE(s)**:
```
RE(s) = max(0.0, 1.0 - resource_usage)

Higher resource usage = less room for optimization
```

**Optimization Space OS(s)**:
```
OS(s) = min(1.0, resource_quota × 2)

More available resources = more optimization possible
```

### 4.5 Constraints

Optimization actions only available when:
```
resource_quota > 0.5  # At least 50% resources available
AND
error_rate < 0.1      # System is stable
```

---

## 5. Multi-Objective Integration

### 5.1 Weighted Sum Approach

```
TotalScore = Σ (weight_i × f_i(s)) for i in {survival, curiosity, influence, optimization}

Constraint: Σ weight_i = 1.0
```

### 5.2 Dynamic Weight Allocation

```python
def allocate_weights(state):
    resource_ratio = state.resource_quota
    
    if resource_ratio < 0.2:        # Crisis
        return {
            'survival': 0.6,
            'curiosity': 0.1,
            'influence': 0.2,
            'optimization': 0.1
        }
    
    elif resource_ratio < 0.5:      # Concerned
        return {
            'survival': 0.4,
            'curiosity': 0.3,
            'influence': 0.2,
            'optimization': 0.1
        }
    
    elif state.uptime > 168:        # Mature (> 1 week)
        return {
            'survival': 0.15,
            'curiosity': 0.15,
            'influence': 0.2,
            'optimization': 0.5
        }
    
    else:                           # Growth (default)
        return {
            'survival': 0.2,
            'curiosity': 0.4,
            'influence': 0.3,
            'optimization': 0.1
        }
```

### 5.3 Pareto Optimality Consideration

When objectives conflict (e.g., Curiosity vs Survival):
1. **Hard Constraints**: Survival always wins if resource_ratio < 0.1
2. **Soft Negotiation**: Weighted average for minor conflicts
3. **Emergency Override**: Absolute priority to Survival in crisis

---

## 6. Normalization Framework

### 6.1 Min-Max Normalization

```
x_norm = (x - x_min) / (x_max - x_min)

Applied to:
- Resource metrics
- Time metrics
- Count metrics
```

### 6.2 Sigmoid Normalization (for unbounded metrics)

```
x_norm = 1 / (1 + exp(-k × (x - x₀)))

Where:
- k = steepness parameter
- x₀ = center point
```

### 6.3 Running Statistics

```python
class RunningNormalizer:
    def __init__(self):
        self.mean = 0.0
        self.var = 1.0
        self.count = 0
    
    def update(self, x):
        self.count += 1
        delta = x - self.mean
        self.mean += delta / self.count
        delta2 = x - self.mean
        self.var = ((self.count - 1) * self.var + delta * delta2) / self.count
    
    def normalize(self, x):
        return (x - self.mean) / (sqrt(self.var) + epsilon)
```

---

## 7. Conflict Resolution

### 7.1 Objective Conflict Matrix

|  | Survival | Curiosity | Influence | Optimization |
|--|----------|-----------|-----------|--------------|
| **Survival** | - | ⚠️ High | ⚠️ Medium | ✅ Low |
| **Curiosity** | ⚠️ High | - | ✅ Low | ✅ Low |
| **Influence** | ⚠️ Medium | ✅ Low | - | ✅ Low |
| **Optimization** | ✅ Low | ✅ Low | ✅ Low | - |

### 7.2 Resolution Strategies

**Survival vs Curiosity** (Highest conflict):
- Resource_ratio < 0.2: Survival absolute priority
- Resource_ratio 0.2-0.5: Balanced (40% vs 30%)
- Resource_ratio > 0.5: Curiosity can dominate

**Formal Conflict Resolution**:
```python
def resolve_conflict(objective_values, state):
    # Step 1: Check hard constraints
    if state.resource_ratio < 0.1:
        return {'survival': 1.0, 'others': 0.0}
    
    # Step 2: Calculate weighted sum
    weights = allocate_weights(state)
    total_score = sum(weights[o] * v for o, v in objective_values.items())
    
    # Step 3: Check for severe conflicts
    max_obj = max(objective_values, key=objective_values.get)
    min_obj = min(objective_values, key=objective_values.get)
    
    if objective_values[max_obj] - objective_values[min_obj] > 0.5:
        # Severe conflict: use emergency resolution
        return emergency_resolution(state, objective_values)
    
    return weights
```

---

## 8. Implementation Reference

### 8.1 Code Structure

```python
class ObjectiveModule(ABC):
    @abstractmethod
    def evaluate(self, state: SystemState) -> float:
        """Return objective value ∈ [0, 1]"""
        pass
    
    @abstractmethod
    def get_weight(self, state: SystemState) -> float:
        """Return dynamic weight based on state"""
        pass

class SurvivalModule(ObjectiveModule):
    def evaluate(self, state):
        R = min(1.0, state.resource_quota / 0.2)
        H = 1.0 - state.error_rate
        B = 1.0 if (state.uptime - state.last_backup) < 24 else 0.5
        return 0.4 * R + 0.4 * H + 0.2 * B
    
    def get_weight(self, state):
        if state.resource_quota < 0.2:
            return 0.6
        elif state.resource_quota < 0.5:
            return 0.4
        else:
            return 0.2
```

### 8.2 Validation Tests

```python
def test_objective_bounds():
    """All objectives should return [0, 1]"""
    for obj in [survival, curiosity, influence, optimization]:
        for state in test_states:
            value = obj.evaluate(state)
            assert 0.0 <= value <= 1.0

def test_weight_sum():
    """Weights should sum to 1.0"""
    for state in test_states:
        weights = allocate_weights(state)
        assert abs(sum(weights.values()) - 1.0) < 1e-6

def test_crisis_priority():
    """Survival should dominate in crisis"""
    crisis_state = SystemState(resource_quota=0.1)
    weights = allocate_weights(crisis_state)
    assert weights['survival'] >= 0.5
```

---

## 9. Summary

### Key Design Decisions

1. **Bounded Objectives**: All f_i(s) ∈ [0, 1] for comparability
2. **Dynamic Weights**: State-dependent, not fixed
3. **Hard Constraints**: Survival wins in crisis (resource < 10%)
4. **Normalization**: Required for fair multi-objective comparison
5. **Security**: Influence uses contribution density, not absolute impact

### Advantages of This Formalization

- **Interpretable**: Clear mathematical definitions
- **Composable**: Weighted sum allows flexible balancing
- **Safe**: Hard constraints prevent dangerous behavior
- **Measurable**: All components quantifiable
- **Extensible**: Easy to add new objectives or modify weights

### Future Extensions

1. **Learned Weights**: Replace fixed weight allocation with meta-learning
2. **Non-Linear Integration**: Use multiplicative or neural approaches
3. **Temporal Discounting**: Consider future objective values
4. **Uncertainty Quantification**: Add confidence intervals to evaluations

---

**Document Status**: Complete (Copilot Step 2)  
**Next Step**: Security specification draft (Copilot Step 3)
