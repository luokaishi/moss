# MOSS Multi-Objective Formalization

**Version**: v2.0.0  
**Last Updated**: 2026-03-18  
**Purpose**: Mathematical formalization of MOSS multi-objective optimization framework

---

## 1. Problem Formulation

### 1.1 Agent-Environment Interface

The MOSS agent operates in a continuous environment with the following components:

- **State space**: $\mathcal{S} \subseteq \mathbb{R}^n$ - agent's internal state
- **Action space**: $\mathcal{A}$ - available actions
- **Observation space**: $\mathcal{O}$ - environment observations
- **Time horizon**: $T \in \{6h, 24h, 72h\}$ (experiment duration)

At each timestep $t$, the agent:
1. Observes $o_t \in \mathcal{O}$
2. Selects action $a_t \in \mathcal{A}$ based on policy $\pi$
3. Transitions to new state $s_{t+1} = f(s_t, a_t)$
4. Receives feedback from environment

### 1.2 Multi-Objective Vector

MOSS defines a four-dimensional objective vector:

$$
\mathbf{M}(t) = \begin{bmatrix} S(t) \\ C(t) \\ I(t) \\ O(t) \end{bmatrix} \in \mathbb{R}^4
$$

Where each component is defined in `docs/metrics.md`.

---

## 2. Unified Objective Function

### 2.1 Scalarization Approach

MOSS uses **dynamic linear scalarization** with time-varying weights:

$$
J(\mathbf{w}, t) = \mathbf{w}(t)^T \mathbf{M}(t) = \sum_{i=1}^{4} w_i(t) \cdot M_i(t)
$$

Subject to constraints:
- $\sum_{i=1}^{4} w_i(t) = 1$ (normalization)
- $w_i(t) \geq w_{min} = 0.05$ (minimum weight floor)
- $\mathbf{w}(t) \in \Delta^3$ (3-simplex)

### 2.2 Cumulative Objective

Over horizon $T$:

$$
J_{cumulative}(\mathbf{w}) = \int_{0}^{T} \mathbf{w}(t)^T \mathbf{M}(t) \, dt \approx \sum_{t=0}^{T} \mathbf{w}(t)^T \mathbf{M}(t) \cdot \Delta t
$$

### 2.3 State-Dependent Weight Adaptation

Weights evolve according to state $z(t) \in \{\text{Crisis, Concerned, Normal, Growth}\}$:

$$
\mathbf{w}(t) = g(z(t), \mathbf{w}(t-1), \Delta J)
$$

Where $g$ is the weight update function (see Section 4).

---

## 3. Pareto Optimality Analysis

### 3.1 Pareto Dominance

For two weight configurations $\mathbf{w}_A$ and $\mathbf{w}_B$:

$$
\mathbf{w}_A \succ_P \mathbf{w}_B \iff \forall i: M_i(\mathbf{w}_A) \geq M_i(\mathbf{w}_B) \land \exists j: M_j(\mathbf{w}_A) > M_j(\mathbf{w}_B)
$$

### 3.2 Pareto Front

The Pareto-optimal set $\mathcal{P}^*$:

$$
\mathcal{P}^* = \{\mathbf{w} \in \Delta^3 \mid \nexists \mathbf{w}' \in \Delta^3: \mathbf{w}' \succ_P \mathbf{w}\}
$$

### 3.3 MOSS Path Bifurcation as Pareto Exploration

**Theorem (Path Bifurcation)**: Given identical initial conditions $\mathbf{w}(0) = \mathbf{w}_0$, MOSS discovers multiple Pareto-optimal points $\{\mathbf{w}_1^*, \mathbf{w}_2^*, ...\}$ corresponding to different strategy specializations.

**Empirical Evidence** (N=25 validation):
- Cluster 1 (48%): Curiosity-dominant specialization
- Cluster 2 (24%): Mixed/balanced strategy
- Cluster 3 (28%): Survival-Influence trade-off

Each cluster represents a local Pareto optimum under different environmental conditions.

### 3.4 Hypervolume Indicator

Pareto front quality measured by hypervolume:

$$
HV(\mathcal{P}, \mathbf{r}) = \Lambda\left(\bigcup_{\mathbf{w} \in \mathcal{P}} [\mathbf{M}(\mathbf{w}), \mathbf{r}]\right)
$$

Where:
- $\mathbf{r}$ is reference point (nadir)
- $\Lambda$ is Lebesgue measure

**MOSS Result**: HV = 0.73 (normalized to [0,1] across four objectives)

---

## 4. Weight Evolution Dynamics

### 4.1 General Update Rule

Weight evolution follows:

$$
\mathbf{w}(t+1) = \Pi_{\Delta^3}\left(\mathbf{w}(t) + \eta \cdot \nabla_{\mathbf{w}} J + \epsilon\right)
$$

Where:
- $\Pi_{\Delta^3}$: Projection onto 3-simplex (normalization + clipping)
- $\eta$: Learning rate (typically 0.1)
- $\nabla_{\mathbf{w}} J$: Gradient of objective w.r.t. weights
- $\epsilon$: Exploration noise (strategy-dependent)

### 4.2 Evolution Strategies

| Strategy | Update Rule | Use Case |
|----------|-------------|----------|
| **Gradient Ascent** | $\Delta \mathbf{w} = \eta \cdot \frac{\partial J}{\partial \mathbf{w}}$ | Local refinement |
| **Random Exploration** | $\Delta \mathbf{w} \sim \mathcal{U}(-0.1, 0.1)$ | Escaping local optima |
| **Weighted Random** | $\Delta \mathbf{w} \sim \mathcal{N}(0, \sigma \cdot \mathbf{w})$ | Prior-aware mutation |
| **Adaptive Greedy** | $\Delta \mathbf{w} = \arg\max_{\Delta} [J(\mathbf{w} + \Delta) - J(\mathbf{w})]$ | Rapid improvement |
| **Population-Inspired** | $\mathbf{w}_{child} = \text{crossover}(\mathbf{w}_{parent1}, \mathbf{w}_{parent2}) + \text{mutation}$ | Diversity maintenance |

### 4.3 Convergence Conditions

**Definition (Stability)**: Weight configuration $\mathbf{w}^*$ is stable if:

$$
\exists \delta > 0: \|\mathbf{w}(0) - \mathbf{w}^*\| < \delta \Rightarrow \lim_{t \to \infty} \mathbf{w}(t) = \mathbf{w}^*
$$

**Empirical Stability** (N=25):
- 92% of runs converge within 72h
- Average time to convergence: 18.3h
- Weight fluctuation post-convergence: $\sigma_w < 0.05$

### 4.4 Cooling Period

To prevent oscillation, weight updates respect:

$$
\Delta t_{update} \geq \tau_{cool} = 10 \text{ minutes}
$$

---

## 5. Comparison with Existing Methods

### 5.1 vs. NSGA-II (Non-dominated Sorting Genetic Algorithm II)

| Aspect | NSGA-II | MOSS |
|--------|---------|------|
| **Search Space** | Discrete population | Continuous simplex |
| **Selection** | Pareto ranking + crowding | State-dependent adaptation |
| **Update** | Genetic operators | Gradient + exploration |
| **Environment** | Static fitness function | Dynamic, stateful |
| **Convergence** | Generational (G_max) | Continuous, adaptive |

**Key Difference**: NSGA-II maintains a population of solutions; MOSS maintains a single agent with time-varying weights adapting to runtime context.

### 5.2 vs. Multi-Objective RL (MORL)

| Aspect | MORL (e.g., MODQN) | MOSS |
|--------|-------------------|------|
| **Policy** | Multiple policies / one per objective | Single policy, weighted objectives |
| **Scalarization** | Fixed or envelope | Dynamic, self-modifying |
| **Objective Weights** | Fixed or hand-designed | Autonomously evolved |
| **Adaptation** | Task-switching | Continuous specialization |

**Key Difference**: MORL typically assumes fixed objective weights; MOSS treats weight evolution as part of the learning problem.

### 5.3 vs. Intrinsic Motivation (ICM, RND)

| Aspect | ICM/RND | MOSS Curiosity |
|--------|---------|----------------|
| **Signal** | Prediction error | Information gain |
| **Integration** | Added to reward | Separate objective with weight |
| **Balance** | Fixed coefficient | Dynamically adjusted |

### 5.4 Mathematical Equivalence

Under specific conditions, MOSS subsumes other approaches:

1. **Fixed weights** $\mathbf{w} = [0.6, 0.1, 0.2, 0.1]$: Equivalent to traditional multi-objective scalarization
2. **Crisis mode** $w_s = 0.9$: Reduces to survival-only optimization
3. **Greedy strategy**: Equivalent to hill-climbing on Pareto front

---

## 6. Theoretical Properties

### 6.1 Boundedness

**Proposition**: Given $w_{min} = 0.05$ and metric bounds $M_i \in [M_{min}, M_{max}]$, the cumulative reward is bounded:

$$
J_{cumulative} \in [T \cdot w_{min} \cdot M_{min}, T \cdot M_{max}]
$$

### 6.2 No-Regret Property (Weak)

For static optimal weights $\mathbf{w}^*$:

$$
\frac{1}{T} \sum_{t=1}^{T} J(\mathbf{w}(t)) \geq J(\mathbf{w}^*) - O(T^{-1/2})
$$

*Note: Strict no-regret requires convexity assumptions not guaranteed in MOSS environment.*

### 6.3 Emergent Specialization

**Observation**: Under long-term operation ($T \geq 24h$), agents spontaneously specialize:

$$
\exists i: w_i(T) \gg w_j(T) \text{ for } j \neq i
$$

**Intuition**: Diminishing returns on balanced strategies vs. compounding gains on specialized ones.

---

## 7. Implementation Details

### 7.1 Weight Projection

Simplex projection algorithm:

```python
def project_simplex(w, w_min=0.05):
    """Project weights onto simplex with minimum floor."""
    # Clip to minimum
    w = np.maximum(w, w_min)
    # Normalize
    w = w / np.sum(w)
    return w
```

### 7.2 Gradient Estimation

Finite difference approximation:

$$
\frac{\partial J}{\partial w_i} \approx \frac{J(\mathbf{w} + \delta \mathbf{e}_i) - J(\mathbf{w} - \delta \mathbf{e}_i)}{2\delta}
$$

With $\delta = 0.01$.

### 7.3 State Transition

State machine transitions based on survival score $S(t)$:

$$
z(t+1) = \begin{cases}
\text{Crisis} & S(t) < 0.3 \\
\text{Concerned} & 0.3 \leq S(t) < 0.6 \\
\text{Normal} & 0.6 \leq S(t) < 0.8 \\
\text{Growth} & S(t) \geq 0.8
\end{cases}
$$

---

## 8. Experimental Validation

### 8.1 Baseline Comparisons

Equal compute budget comparisons:

| Method | Mean Reward | Std | Pareto Coverage |
|--------|-------------|-----|-----------------|
| **MOSS** | 765.30 | 120.30 | 3 clusters |
| NSGA-II | 642.15 | 89.40 | 2 clusters |
| Fixed Optimal | 589.42 | 45.20 | 1 cluster |
| Random Search | 312.78 | 156.90 | Scattered |

### 8.2 Ablation Study

Impact of self-modification vs. fixed weights:

| Configuration | 6h Reward | 24h Reward | Strategy Diversity |
|---------------|-----------|------------|-------------------|
| Self-modifying | 528.42 | 841.47 | 5 types |
| Fixed [0.2,0.4,0.3,0.1] | 312.15 | 445.23 | 1 type |
| Fixed [0.6,0.1,0.2,0.1] | 428.91 | 598.74 | 1 type |

---

## 9. Limitations and Future Work

### 9.1 Current Limitations

1. **No convergence proof** for non-convex objective landscape
2. **Local optima** may trap agents (mitigated by exploration strategies)
3. **Computational cost** of gradient estimation

### 9.2 Future Directions

1. **Neural weight predictor**: $\mathbf{w}(t+1) = f_\theta(\mathbf{M}(t), z(t))$
2. **Multi-agent Pareto**: Distributed Pareto front exploration
3. **Meta-learning**: Fast adaptation to new environments

---

## 10. References

1. Deb, K., et al. (2002). A fast and elitist multiobjective genetic algorithm: NSGA-II. *IEEE Transactions on Evolutionary Computation*.
2. Roijers, D. M., & Whiteson, S. (2017). Multi-objective decision making. *Foundations and Trends in Machine Learning*.
3. Hayes, C. F., et al. (2022). A practical guide to multi-objective reinforcement learning and planning. *Autonomous Agents and Multi-Agent Systems*.
4. MOSS Paper: "Self-Modifying Multi-Objective Optimization: State-Dependent Specialization in Autonomous Agents"

---

**Maintainer**: MOSS Project Team  
**Contact**: moss-project@github.com
