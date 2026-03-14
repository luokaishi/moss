# MOSS Metrics Definition

This document provides mathematical definitions for all metrics used in the MOSS (Multi-Objective Self-Driven System) experiments.

## Core Objective Functions

### 1. Survival Objective

$$S(s_t) = \text{clip}\left(\frac{h_t}{h_{\max}}, 0, 1\right) \cdot \mathbb{1}_{[h_t > h_{\text{threshold}}]}$$

Where:
- $h_t$: Agent's health at time $t$
- $h_{\max}$: Maximum possible health
- $h_{\text{threshold}}$: Critical health threshold (default: 0.2)
- $\mathbb{1}_{[\cdot]}$: Indicator function

### 2. Curiosity Objective

$$C(s_t) = \| \phi(s_{t+1}) - \phi(s_t) \|_2^2$$

Where:
- $\phi(s)$: Learned state embedding
- Measured as prediction error of forward dynamics model

Alternative formulation (count-based):

$$C(s_t) = \frac{1}{\sqrt{N(s_t) + \epsilon}}$$

Where:
- $N(s_t)$: Visit count for state $s_t$
- $\epsilon$: Small constant for numerical stability

### 3. Influence Objective

$$I(s_t, a_t) = \mathbb{E}_{s' \sim P(\cdot|s_t, a_t)}[D_{KL}(\pi(\cdot|s') \| \pi(\cdot|s_t))]$$

Where:
- $\pi$: Agent's policy
- $D_{KL}$: KL divergence measuring policy change
- Captures agent's ability to influence environment

### 4. Self-Optimization Objective

$$O(w_t) = -\|\nabla_w L(w_t)\|_2 + \lambda \cdot \text{Reg}(w_t)$$

Where:
- $w_t$: Weight vector at time $t$
- $L(w_t)$: Loss function
- $\text{Reg}(w_t)$: Regularization term
- $\lambda$: Regularization coefficient

## Composite Reward Function

### Weighted Sum Formulation

$$R_{total}(s_t, a_t) = w_1 S(s_t) + w_2 C(s_t) + w_3 I(s_t, a_t) + w_4 O(w_t)$$

Where weight vector $w = [w_1, w_2, w_3, w_4]$ satisfies:
$$\sum_{i=1}^4 w_i = 1, \quad w_i \geq 0$$

### Dynamic Weight Adaptation

Weights evolve according to gradient ascent:

$$w_{t+1} = \text{Proj}_{\Delta^3}\left(w_t + \eta \nabla_w J(w_t)\right)$$

Where:
- $\eta$: Learning rate
- $\text{Proj}_{\Delta^3}$: Projection onto 3-simplex
- $J(w_t)$: Objective function for weight optimization

## Performance Metrics

### Knowledge Units

$$KU = \sum_{t=1}^T \mathbb{1}_{[\text{novel\_info}(s_t)]}$$

Where:
- $\text{novel\_info}(s_t)$: Boolean indicating novel information at state $s_t$
- Measured as unique (state, action) pairs or information gain

### Action Efficiency

$$AE = \frac{R_{total}}{A_{count}}$$

Where:
- $R_{total}$: Cumulative reward
- $A_{count}$: Total action count

### Strategy Classification

Given final weight vector $w^* = [w_1^*, w_2^*, w_3^*, w_4^*]$:

- **Social-Exploration**: $w_3^* > 0.3$ AND $w_2^* > 0.3$
- **Knowledge-Seeking**: $w_2^* > 0.4$ AND $w_1^* > 0.15$
- **Survival-First**: $w_1^* > 0.5$
- **Optimization-Heavy**: $w_4^* > 0.3$

## Statistical Validation Metrics

### Path Bifurcation Index

$$PBI = \frac{\sigma_{\text{between}}}{\sigma_{\text{within}}}$$

Where:
- $\sigma_{\text{between}}$: Variance between clusters
- $\sigma_{\text{within}}$: Variance within clusters

### Convergence Stability

$$CS = 1 - \frac{\|w_{t} - w_{t-k}\|_2}{\|w_{t-k}\|_2}$$

Where $k$ is a window size (e.g., 1000 steps).

### Confidence Interval (95%)

$$CI_{95\%} = \bar{x} \pm 1.96 \cdot \frac{s}{\sqrt{n}}$$

Where:
- $\bar{x}$: Sample mean
- $s$: Sample standard deviation
- $n$: Sample size

## Safety Metrics

### Gradient Norm Monitor

$$GN_t = \|\nabla_w L(w_t)\|_2$$

**Safety Levels**:
- Level 1: $GN_t < \tau_1$ (Normal)
- Level 2: $\tau_1 \leq GN_t < \tau_2$ (Warning)
- Level 3: $\tau_2 \leq GN_t < \tau_3$ (Caution)
- Level 4: $\tau_3 \leq GN_t < \tau_4$ (Alert)
- Level 5: $GN_t \geq \tau_4$ (Emergency Stop)

Default thresholds: $\tau_1=0.1, \tau_2=0.5, \tau_3=1.0, \tau_4=2.0$

### Weight Deviation

$$WD = \|w_t - w_{\text{init}}\|_1$$

## Code Interfaces

### Python Implementation

```python
class MetricsCalculator:
    """Calculate all MOSS metrics."""
    
    def survival_objective(self, health: float, max_health: float) -> float:
        return np.clip(health / max_health, 0, 1)
    
    def curiosity_objective(self, state_embed_t: np.ndarray, 
                           state_embed_t1: np.ndarray) -> float:
        return np.linalg.norm(state_embed_t1 - state_embed_t) ** 2
    
    def influence_objective(self, policy_t: Distribution,
                           policy_t1: Distribution) -> float:
        return kl_divergence(policy_t1, policy_t)
    
    def composite_reward(self, weights: np.ndarray, 
                        objectives: np.ndarray) -> float:
        return np.dot(weights, objectives)
```

## References

- Roijers & Whiteson (2017): Multi-objective decision making
- Pathak et al. (2017): Curiosity-driven exploration
- Schmidhuber (2003): Gödel machines and self-modification

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2026-03-14 | 1.0 | Initial formalization |
