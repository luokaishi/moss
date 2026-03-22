# Run 4.1 Experiment Report

**Experiment ID**: Run 4.1 - Purpose-Enhanced Long-term  
**Agent**: v4.1 Purpose-Enhanced (9D Purpose + 5-Layer Architecture)  
**Status**: ⏹️ Terminated Early  
**Duration**: ~5 hours (09:54 - 14:50)  
**Completion**: 25.3% (1,091,000 / 4,320,000 steps)

---

## Summary

| Metric | Value |
|--------|-------|
| Total Actions | 10,912 |
| Step Range | 100 - 1,091,200 |
| Success Rate | 16.9% |
| Unique Actions | 1 |
| Purpose Diversity | 0% (100% Survival) |

---

## Key Findings

### 1. Purpose Monoculture

**Observation**: Agent maintained 100% Survival focus throughout the experiment.

```
Purpose Distribution:
- Survival: 10,912 (100.0%)
- Curiosity: 0 (0%)
- Influence: 0 (0%)
- Optimization: 0 (0%)
```

**Expected Behavior**: Purpose should have shifted based on environment phases:
- Phase 1 (Normal): Balanced or Curiosity
- Phase 2 (Threat): Survival ← **Matched**
- Phase 3 (Novelty): Curiosity
- Phase 4 (Social): Influence

**Issue**: Agent entered Phase 2 (Threat) but never left Survival mode.

### 2. Action Uniformity

**Observation**: Only ONE action type executed:
- `ensure_resource_availability`: 10,912 times (100%)

**Root Cause**: The `_generate_actions_by_purpose` function in v4.1 agent only returns one action per purpose, and the action selection logic is not properly diversified.

### 3. D9 Stagnation

**Observation**: D9 (Self-Generated Purpose) remained constant at 0.120 throughout the experiment.

```
D9 Evolution:
- Start: 0.1200
- End:   0.1200
- Mean:  0.1200
```

**Expected**: D9 should have increased based on goal achievements and reflections.

**Issue**: Goal achievement logic not properly connected to D9 update.

### 4. Goal Management Failure

**Status File Data**:
- Total Goals Generated: 73,811
- Active Goals: 0

**Issue**: Goals are being generated but never activated. The `get_active_goals()` returns empty list, indicating goals remain in PENDING status.

---

## Technical Issues Identified

### Issue 1: Action Selection Bias
```python
# In agent_v4_1.py _generate_actions_by_purpose()
# Returns only one action per purpose
action_map = {
    'Survival': [
        'ensure_resource_availability',  # Only this one was selected
        'monitor_system_health',         # Never selected
        'create_backup',                 # Never selected
        'verify_security'                # Never selected
    ],
    ...
}
```

### Issue 2: Goal Activation Missing
```python
# Goals are generated with PENDING status
# But never transitioned to ACTIVE status
# Need: goal.status = GoalStatus.ACTIVE
```

### Issue 3: Purpose Update Rate
```python
# Purpose updates every step with very small changes
# Learning rate 0.1 may be too small for quick phase transitions
```

### Issue 4: D9 Update Logic
```python
# D9 only updates based on goals_achieved
# But goals are not being achieved
self.purpose_state.self_generated = min(0.15, 0.10 + achievement_rate * 0.05)
```

---

## Lessons Learned

### 1. Exploration vs Exploitation
The agent exploited the first successful action pattern and never explored alternatives. Need epsilon-greedy or similar exploration strategy.

### 2. Goal Lifecycle
The goal management system needs explicit activation logic. Generating goals is not enough - they must be activated and tracked.

### 3. Phase Transition
Purpose transitions need to be more aggressive. Current smooth transition (learning rate 0.1) doesn't respond fast enough to phase changes.

### 4. Success Feedback Loop
Low success rate (16.9%) with no adaptation indicates the learning feedback loop is broken.

---

## Recommendations for Run 4.2

### 1. Fix Action Selection
```python
# Add exploration factor
if np.random.random() < 0.3:  # 30% exploration
    action = np.random.choice(all_possible_actions)
else:
    action = select_by_purpose(dominant_purpose)
```

### 2. Implement Goal Activation
```python
# Auto-activate high-priority pending goals
pending = self.goal_manager.get_pending_goals()
for goal in pending[:self.max_active]:
    goal.status = GoalStatus.ACTIVE
```

### 3. Accelerate Phase Transitions
```python
# Use higher learning rate for phase changes
if phase_changed:
    learning_rate = 0.5  # Fast transition
else:
    learning_rate = 0.1  # Normal stabilization
```

### 4. Connect D9 to Actions
```python
# Update D9 based on action diversity, not just goals
action_diversity = len(set(recent_actions)) / len(recent_actions)
self.purpose_state.self_generated = 0.10 + action_diversity * 0.05
```

---

## Data Files

- `experiments/run_4_1_actions.jsonl` (3.2MB, 10,912 records)
- `experiments/run_4_1_status.json` (last status)
- `experiments/.checkpoints_run4_1/` (5 checkpoints)

---

## Conclusion

Run 4.1 demonstrated the v4.1 architecture's stability (5 hours continuous operation) but revealed critical issues in exploration, goal management, and purpose diversity. The agent successfully entered Threat phase and maintained Survival focus, but failed to:

1. Explore diverse actions
2. Activate generated goals
3. Transition purposes across phases
4. Increase self-generated meaning (D9)

**Value**: Despite issues, collected 10,912 action records showing extreme Purpose specialization under sustained environmental pressure.

**Next Step**: Implement fixes for Run 4.2 with improved exploration and goal activation.

---

*Generated: 2026-03-22*
