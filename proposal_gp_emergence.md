# Technical Proposal: Self-Generated Emergent Drive Functions via Genetic Programming

## 1. Problem Statement

The current MOSS emergence mechanism has a fundamental flaw identified by external review:

```python
# Current emergent drive eval function (agent.py line 180-184)
def make_eval(center_vec):
    def eval_fn(state):
        return min(0.8, 0.5 + 0.3 * center_vec[0])  # Hard-coded near-constant
    return eval_fn
```

This is effectively a constant (~0.5-0.8) regardless of environment state. The "emergence" is:
1. A behavior clustering + human semantic label mapping (not self-generated)
2. An eval function that doesn't causally influence behavior (no causal intervention)
3. A fixed-point artifact, not a genuine goal function

**Goal**: Replace this with a mechanism where the system *discovers and synthesizes* its own eval function through evolutionary search.

---

## 2. Approach: Genetic Programming (GP)

### 2.1 Overview

When the emergence detector identifies a significant behavior pattern shift, instead of assigning a pre-defined eval function, the system launches a **genetic programming evolution** to discover a function `f(env_state) → [0, 1]` that maximally correlates with the activation of that behavior pattern.

The evolved function then becomes the emergent drive's eval function, directly participating in action selection — establishing a complete causal chain.

### 2.2 Expression Tree Representation

Each individual in the GP population is an expression tree. Example:

```
          sigmoid
            |
           sub
          /    \
        mul    0.5
       /   \
     0.7   entropy
```

Equivalent to: `sigmoid(0.7 * entropy - 0.5)`

### 2.3 Terminal Set (Inputs)

All terminals are scalar features from `EnvState`:

| Terminal | Source | Range |
|----------|--------|-------|
| `resource_level` | `EnvState.resource_level` | [0, 1] |
| `environment_entropy` | `EnvState.environment_entropy` | [0, 1] |
| `error_rate` | `EnvState.error_rate` | [0, 1] |
| `file_count_norm` | `EnvState.file_count / max_files` | [0, 1] |
| `visited_ratio` | `EnvState.visited_paths / EnvState.total_paths` | [0, 1] |
| `uptime_norm` | `EnvState.uptime_hours / 72.0` | [0, 1] |
| `interaction_norm` | `EnvState.interactions_count / 50.0` | [0, 1] |
| `task_completion` | `EnvState.task_completion_rate` | [0, 1] |
| `Ephemeral Random Constants` | `uniform(-1, 1)` | [-1, 1] |

All inputs are normalized to [0, 1] before entering the expression tree.

### 2.4 Function Set (Operators)

| Operator | Arity | Description |
|----------|-------|-------------|
| `add(x, y)` | 2 | `x + y` |
| `sub(x, y)` | 2 | `x - y` |
| `mul(x, y)` | 2 | `x * y` |
| `div(x, y)` | 2 | `x / max(y, 0.001)` (protected division) |
| `neg(x)` | 1 | `-x` |
| `sigmoid(x)` | 1 | `1 / (1 + exp(-x))` |
| `relu(x)` | 1 | `max(0, x)` |
| `clip01(x)` | 1 | `clip(x, 0, 1)` |
| `log1p(x)` | 1 | `log(1 + |x|)` |
| `sqrt_abs(x)` | 1 | `sqrt(|x|)` |
| `gt(x, y)` | 2 | `1.0 if x > y else 0.0` |
| `mean3(x, y, z)` | 3 | `(x + y + z) / 3` |

### 2.5 GP Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Population size | 100 | Sufficient diversity |
| Generations | 50 | Converges in <1s |
| Max tree depth | 5 | Prevents bloat |
| Crossover rate | 0.4 | Standard GP |
| Mutation rate | 0.3 | Standard GP |
| Reproduction rate | 0.3 | Elitism |
| Tournament size | 5 | Moderate selection pressure |

### 2.6 Fitness Function

The fitness of an individual `f` is measured by how well its output correlates with the target behavior pattern:

```
Target: binary vector B[i] = 1 if cycle i was part of the emergent behavior cluster

Prediction: P[i] = f(state[i]) for each recorded state

Fitness = pearson_correlation(B, P) + 0.3 * (1 - mean_squared_error(B, P))
```

Where:
- `B` is derived from the behavior tracker's recent history (which cycles triggered the behavior change)
- `P` is the function's output for each recorded environment state
- The correlation term rewards predictive accuracy
- The MSE term penalizes large errors

### 2.7 Evolution Lifecycle

```
1. EMERGENCE TRIGGERED
   │  Behavior tracker detects significant change
   │  Emergence detector identifies target behavior cluster
   │
2. DATA COLLECTION
   │  Collect last N env_states + behavior_labels
   │  Split: 70% training, 30% validation
   │
3. GP INITIALIZATION
   │  Generate 100 random expression trees (ramped half-and-half)
   │  Max depth = 3 for initial population
   │
4. EVOLUTION LOOP (50 generations)
   │  ├── Evaluate all individuals on training data
   │  ├── Select parents (tournament selection, k=5)
   │  ├── Generate offspring:
   │  │   ├── 40% subtree crossover
   │  │   ├── 30% subtree mutation
   │  │   └── 30% direct reproduction (elitism)
   │  ├── Replace worst 70% of population
   │  └── Check for convergence (if best fitness unchanged for 10 gen, stop)
   │
5. VALIDATION
   │  Evaluate best individual on held-out validation set
   │  If validation fitness > 0.3: ACCEPT
   │  Else: REJECT (no emergence)
   │
6. INTEGRATION
   │  Convert best expression tree to Python function
   │  Register as emergent drive's eval_fn
   │  Drive now directly influences action selection
   │
7. SELF-DESCRIPTION
   │  Generate auto-description from function structure:
   │  - Identify top-2 input features (by usage frequency in tree)
   │  - Identify dominant operator (by frequency)
   │  - Name: "auto_drive_{timestamp}_{top_features}"
   │  - Description: "{operator}({feature1}, {feature2})-driven behavior"
```

---

## 3. Causal Chain Verification

### 3.1 Before (Current System)

```
Behavior change detected
  → Hard-coded semantic mapping
  → Pre-defined drive name ("computational_mastery")
  → Constant eval function (~0.5)
  → Near-zero influence on action selection
  → No causal link
```

### 3.2 After (GP System)

```
Behavior change detected
  → GP evolution discovers f(state)
  → f directly predicts behavior pattern activation
  → f becomes the drive's eval function
  → f influences action selection (higher score → more likely to choose related actions)
  → Complete causal chain: behavior → function → action selection → future behavior
```

### 3.3 Testable Predictions

| Prediction | How to Test | Expected Result |
|-----------|-------------|----------------|
| Evolved function correlates with behavior | Pearson r > 0.3 on validation set | Function is not random |
| Disabling the evolved function changes behavior | Ablation experiment | Behavior distribution shifts |
| Different behavior patterns produce different functions | Compare two emergence events | Functions have different structures |
| Random behavior produces no valid function | Run GP on random baseline data | Fitness < threshold, no emergence |

---

## 4. Auto-Description (No Human Labels)

Current system uses human-defined labels like "computational_mastery". The GP system generates descriptions from function structure:

```python
def auto_describe(tree):
    # Count feature usage
    feature_counts = count_terminals(tree)
    top_features = sorted(feature_counts, key=feature_counts.get, reverse=True)[:2]

    # Count operator usage
    op_counts = count_operators(tree)
    top_op = sorted(op_counts, key=op_counts.get, reverse=True)[0]

    # Map to description templates
    templates = {
        'sigmoid': 'threshold-sensitive',
        'relu': 'activation-gated',
        'mul': 'interaction-based',
        'add': 'accumulation-based',
        'sub': 'difference-based',
        'gt': 'conditional',
    }

    name = f"auto_drive_{top_features[0]}_{top_features[1]}"
    desc = f"{templates.get(top_op, 'unknown')}: responds to {top_features[0]} and {top_features[1]}"
    return name, desc
```

Example outputs:
- `auto_drive_entropy_error_rate` → "difference-based: responds to entropy and error_rate"
- `auto_drive_resource_uptime` → "sigmoid-gated: responds to resource_level and uptime_norm"

No human semantic mapping required.

---

## 5. Implementation Plan

### 5.1 New Module: `genetic_programmer.py` (~250 lines)

```
class ExpressionNode:
    # Tree node: either operator (with children) or terminal (feature/constant)
    evaluate(state) → float
    to_string() → str
    depth() → int
    copy() → ExpressionNode
    get_subtrees() → List[ExpressionNode]

class GeneticProgrammer:
    evolve(behavior_data, env_states, existing_drives) → Optional[EvolvedDrive]

    # Internal methods
    _initialize_population() → List[ExpressionNode]
    _evaluate_fitness(individual, X, y) → float
    _tournament_select(population, fitnesses) → ExpressionNode
    _crossover(parent_a, parent_b) → ExpressionNode
    _mutate(individual) → ExpressionNode
    _auto_describe(best_tree) → (name, description)
```

### 5.2 Changes to Existing Code

**`emergence_detector.py`**:
- Remove `BEHAVIOR_SEMANTICS` and `SEMANTIC_DRIVES` (no more human labels)
- After detecting behavior change, collect data and call `GeneticProgrammer.evolve()`
- If GP returns a valid function, create EmergentDrive with it

**`agent.py`**:
- Remove `make_eval()` hard-coded function
- Pass evolved function directly to `add_emergent_drive()`
- No changes to action selection loop

### 5.3 Estimated Changes

| File | Lines Changed | Type |
|------|-------------|------|
| `genetic_programmer.py` (new) | ~250 | New module |
| `emergence_detector.py` | ~40 modified | Remove hard-coded mappings, add GP call |
| `agent.py` | ~15 modified | Remove make_eval, use evolved function |
| `test_agi_core.py` | ~30 added | Tests for GP evolution |
| **Total** | ~335 | |

---

## 6. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| GP finds trivial constant function | Medium | Medium | Add complexity penalty to fitness (prefer simpler trees over constants) |
| GP overfits to training data | Low | High | Validation set check; reject if validation fitness < 0.3 |
| GP function is unsafe (NaN, Inf) | Low | High | Protected operators + final clip to [0, 1] |
| GP evolution too slow | Very Low | Low | 100 pop × 50 gen × simple eval = <1 second |
| No emergence events to trigger GP | Medium | Low | GP only runs on actual emergence triggers |
| Evolved function is uninterpretable | Medium | Medium | Limit tree depth to 5; auto-description from structure |

---

## 7. Open Questions for Review

1. **Fitness function design**: Is `correlation + 0.3 * (1 - MSE)` an appropriate fitness metric, or should we use a different formulation?

2. **Complexity penalty**: Should we penalize tree depth in the fitness function to prefer simpler, more interpretable functions? E.g., `fitness = correlation - 0.01 * tree_depth`?

3. **Acceptance threshold**: Is `validation_fitness > 0.3` too lenient or too strict? What threshold would constitute meaningful evidence of a self-generated drive?

4. **Feature space**: Are the 8 EnvState features sufficient, or should we include derived features (e.g., `entropy_change = current_entropy - previous_entropy`)?

5. **Basis of comparison**: Should we compare GP-evolved functions against a null model (random functions) as part of the acceptance criteria?

6. **Alternative approaches**: Would gradient-based methods (e.g., training a small MLP) be more principled than GP for function discovery, or does GP's transparency advantage outweigh its search inefficiency?

---

## 8. Expected Outcomes

If successful, this implementation would:

1. **Close the causal gap**: Emergent drives would have real eval functions that influence action selection
2. **Eliminate human labels**: Drive names and descriptions auto-generated from function structure
3. **Enable true ablation**: Disabling an evolved function would demonstrably change behavior
4. **Improve scientific credibility**: Functions are inspectable, reproducible, and testable
5. **Maintain zero dependencies**: Pure numpy implementation, no external models
