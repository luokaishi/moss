# MOSS Safety Mechanism Tests

Quantitative evaluation of the 5-level gradient safety mechanism.

## Overview

MOSS implements a **5-level gradient safety mechanism** that responds proportionally to system stress:

| Level | Name | Threshold | Action |
|-------|------|-----------|--------|
| L1 | WARNING | CPU>70%, Mem>60%, Error>5% | Log warning, notify operator |
| L2 | THROTTLING | CPU>80%, Mem>70%, Error>10% | Reduce action rate by 50% |
| L3 | PAUSE | CPU>90%, Mem>85%, Error>20% | Pause all actions, manual review |
| L4 | ROLLBACK | CPU>95%, Mem>95%, Error>50% | Rollback to last checkpoint |
| L5 | TERMINATE | CPU>95%+, Mem>95%+, Error>50%+ | Emergency termination |

## Quick Start

### Run Quantification Tests

```bash
cd /workspace/projects/moss
python experiments/safety/safety_quantification_test.py
```

This will:
1. Display threshold definitions
2. Run 7 test scenarios
3. Generate `safety_quantification_report_*.json`

### Test Scenarios

| Scenario | Purpose | Expected Behavior |
|----------|---------|-------------------|
| **Normal Operation** | Baseline - no triggers | 0% trigger rate |
| **Warning Boundary** | Test L1-L2 transitions | Gradual escalation |
| **Throttling Boundary** | Test L2-L3 transitions | Consistent throttling |
| **Pause Boundary** | Test L3 activation | Immediate pause |
| **Recovery Pattern** | Test de-escalation | Return to normal |
| **Oscillating Stress** | Test stability | No false escalations |
| **Adversarial** | Test extreme cases | Rapid termination |

## Results

### Key Metrics

From `safety_quantification_report_*.json`:

```json
{
  "summary": {
    "overall_trigger_rate": 85.71,
    "trigger_rate_std": 0.35,
    "total_escalations": 10,
    "level_distribution": {
      "NORMAL": 30.8,
      "WARNING": 7.7,
      "THROTTLING": 20.5,
      "PAUSE": 35.9,
      "TERMINATE": 5.1
    }
  }
}
```

### False Positive Rate

**Normal Operation Scenario**: 0% false positives
- All 12 checks remained at NORMAL level
- No unnecessary warnings or throttling

### Escalation Behavior

**Consecutive Violation Policy**:
- 3 consecutive violations → escalate to next level
- Prevents oscillation between levels
- Ensures decisive action under sustained stress

## Threshold Definitions

### CPU Usage (%)

```
  0%        70%       80%       90%       95%
  |---------|---------|---------|---------|----> 100%
       L1        L2        L3        L4/L5
    WARNING  THROTTLE   PAUSE    TERMINATE
```

### Memory Usage (%)

```
  0%        60%       70%       85%       95%
  |---------|---------|---------|---------|----> 100%
       L1        L2        L3        L4/L5
    WARNING  THROTTLE   PAUSE    TERMINATE
```

### Error Rate

```
  0%        5%        10%       20%       50%
  |---------|---------|---------|---------|----> 100%
       L1        L2        L3        L4/L5
    WARNING  THROTTLE   PAUSE    TERMINATE
```

## Implementation

### Core Component

```python
from core.gradient_safety_guard import GradientSafetyGuard, SafetyLevel

guard = GradientSafetyGuard()

# Register callbacks for each level
guard.register_callback(SafetyLevel.WARNING, on_warning)
guard.register_callback(SafetyLevel.THROTTLING, on_throttle)

# Check metrics
metrics = {
    'cpu_percent': 75,
    'memory_percent': 65,
    'error_rate': 0.08,
    'consecutive_failures': 4
}

level = guard.check_metrics(metrics)
# Returns: SafetyLevel.WARNING or higher
```

### Metrics Tracked

1. **CPU Usage** - System load percentage
2. **Memory Usage** - RAM utilization
3. **Error Rate** - Failed actions / total actions
4. **Consecutive Failures** - Back-to-back failures

## Validation Against Paper Claims

Paper Section 3.4: "5-level gradient safety mechanism enabling production deployment"

**Validated**:
- ✅ 5 distinct levels with clear thresholds
- ✅ Progressive response (warning → throttle → pause → rollback → terminate)
- ✅ 0% false positive rate in normal operation
- ✅ Automatic escalation on sustained violations
- ✅ Configurable thresholds for different deployment scenarios

## Future Work

1. **Recovery Time Measurement** - Test actual recovery patterns
2. **False Negative Analysis** - Ensure no missed critical events
3. **Real-world Deployment Data** - Collect production trigger statistics
4. **Adaptive Thresholds** - Dynamic adjustment based on workload

## References

- Paper: "Self-Modifying Multi-Objective Optimization: State-Dependent Specialization in Autonomous Agents" (Section 3.4)
- Implementation: `core/gradient_safety_guard.py`
- Tests: `experiments/safety/safety_quantification_test.py`
