# MOSS GP Emergence: Next Steps Proposal

## Current State

| Metric | Value |
|--------|-------|
| Code | 1,908 lines (agi/*.py) |
| Tests | 67 passed |
| GP Trigger | ✅ Works in 200 cycles |
| Emerged Function | `entropy_moving_avg` (single terminal) |
| Behavioral Gain | 0.00 (weak causality) |
| Drive Competition | None (direct inclusion) |

## Problem Diagnosis

### 1. Evolved Functions Are Too Simple

The GP currently discovers `entropy_moving_avg` — a single terminal, not a composite pattern. This happens because:

- **Complexity penalty** (`-0.01 × node_count`) disproportionately penalizes deep trees
- **Constant penalty** only applies to pure constants, not single terminals
- **Fitness landscape** favors simple correlations over complex behavioral patterns

**Expected behavior**: GP should discover composite functions like `sigmoid(mul(entropy_variance, file_count_norm))` that capture non-obvious patterns.

### 2. Behavioral Gain Always Zero

Current fitness function:
```
fitness = 0.3×correlation + 0.2×(1-MSE) + 0.3×behavioral_gain - 0.01×complexity
```

`behavioral_gain` measures: "When f(state) is high, is the target behavior more likely?"

With single-terminal functions, the prediction variance is too low to split samples meaningfully. The `high_mask = P > 0.5` condition creates an imbalanced split.

### 3. Self-Referential Labels

Behavior labels come from agent's own actions:
```python
label = 0.3 * diversity + 0.4 * new_ratio + 0.3 * trend
```

This creates circularity: agent's behavior → label → GP learns to predict behavior → new drive influences behavior → label changes.

**Not necessarily wrong**, but weakens causal claims.

### 4. No Competition Mechanism

Emergent drives are added with fixed weight (0.15) and never removed. In true emergence, drives should compete — poorly performing ones should decay or be eliminated.

## Proposed Improvements

### Direction A: Strengthen GP Quality (Recommended First)

**Goal**: Force GP to discover composite functions with real predictive power.

**Changes**:

1. **Increase population and generations**
   ```python
   population_size = 200  # was 100
   generations = 100      # was 50
   ```

2. **Penalize single-terminal functions**
   ```python
   if tree.node_count() == 1 and tree.is_terminal():
       return -0.5  # penalty, not -1.0 (allow but discourage)
   ```

3. **Require minimum behavioral_gain**
   ```python
   if gain < 0.1:
       return None  # reject even if fitness > threshold
   ```

4. **Adjust fitness weights**
   ```python
   fitness = 0.2×corr + 0.1×(1-MSE) + 0.5×behavioral_gain - 0.02×complexity
   ```

5. **Multi-objective evolution**: Evolve pareto front of (corr, gain, complexity) instead of single scalar.

**Expected outcome**: Composite functions like `mul(sigmoid(entropy_variance), file_count_norm)` with gain > 0.1.

**Effort**: Medium (modify `genetic_programmer.py`, ~100 lines)

---

### Direction B: Long-Run Validation

**Goal**: Verify that emergence persists and influences behavior over extended periods.

**Changes**:

1. Run 2000-cycle experiment (vs current 200)
2. Track:
   - Number of emergence events over time
   - Whether emergent drives survive (weight changes)
   - Correlation between emergence and behavior shifts
3. Compare: agent with GP vs agent without GP (control)

**Expected outcome**: 5+ emergence events, emergent drives account for 20%+ of action selection.

**Effort**: Low (just run experiment, analyze results)

---

### Direction C: Drive Competition Mechanism

**Goal**: Make emergent drives compete with initial drives — adapt or die.

**Changes**:

1. **Probation period**: New drives start with weight 0.05, not 0.15
2. **Performance tracking**: Monitor `avg_reward` when drive is selected
3. **Weight dynamics**:
   ```python
   if avg_reward < 0.3:
       weight *= 0.95  # decay
   elif avg_reward > 0.7:
       weight = min(weight * 1.05, 0.3)  # grow, cap at 0.3
   ```
4. **Elimination**: If weight < 0.02, remove drive entirely
5. **Replacement**: When one drive eliminated, GP can try again

**Expected outcome**: Only drives with real predictive value survive.

**Effort**: Medium (modify `drive_manager.py`, `agent.py`, ~80 lines)

---

### Direction D: Replace GP with MLP (Future)

**Goal**: Use neural networks instead of expression trees for stronger function approximation.

**Changes**:

1. Encode state as 16-dim vector
2. Train small MLP (16 → 8 → 1) via gradient descent
3. Use behavioral_gain as loss function directly
4. Prune network to extract interpretable rules

**Advantages**: Better expressiveness, can learn non-linear patterns.
**Disadvantages**: Less interpretable, harder to validate scientifically.

**Effort**: High (new module, ~300 lines)

---

### Direction E: Causal Intervention Experiments

**Goal**: Prove emergence is causal, not correlational.

**Changes**:

1. **Action restriction**: Disable certain commands (e.g., `python3`, `find`)
2. **Observe**: Does emergence still occur? Does function change?
3. **Drive ablation**: Remove emerged drive, see if behavior regresses
4. **Injection**: Force-add a "fake" drive with random eval, see if it's rejected

**Expected outcome**: Emergence adapts to constraints; removing drive hurts performance.

**Effort**: Medium (experimental design + analysis)

---

## Recommended Sequence

```
Phase 1 (Now):     A → Strengthen GP quality
Phase 2 (Week 2): B → Long-run validation (2000 cycles)
Phase 3 (Week 3): C → Drive competition mechanism
Phase 4 (Month 2): E → Causal intervention experiments
Phase 5 (Future): D → MLP replacement (if GP hits ceiling)
```

## Questions for Reviewer

1. Is the fitness function design sound? Should behavioral_gain be weighted higher?
2. Are single-terminal functions a real problem, or is simplicity acceptable?
3. Is the self-referential label issue fatal for causal claims?
4. Should drives compete with each other, or just against a performance threshold?
5. Is MLP replacement worth the interpretability cost?

## Appendix: Key Code Locations

| Component | File | Lines |
|-----------|------|-------|
| Fitness function | `genetic_programmer.py` | 408-417 |
| Behavioral gain | `genetic_programmer.py` | 431-441 |
| State recording | `agent.py` | 172-186 |
| Label computation | `agent.py` | 188-207 |
| GP trigger conditions | `emergence_detector.py` | 69-115 |