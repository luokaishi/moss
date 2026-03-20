# MOSS v4.0 Directory Structure

**Status**: Development  
**Start Date**: 2026-03-21  
**Target**: AGI architecture with World Model + LLM + Open-ended Goal Space

---

## Directory Layout

```
moss/v4/
├── README.md                           # v4.0 overview and quick start
├── core/                               # Core v4.0 modules
│   ├── __init__.py
│   ├── world_model.py                  # ✅ World Model (Layer 4)
│   ├── llm_reasoning.py                # LLM Meta-Cognition (Layer 5) [TODO]
│   ├── open_goal_space.py              # Open-ended Goal Space (Layer 3) [TODO]
│   ├── cost_evaluator.py               # Cost-Benefit Evaluation (Layer 2) [TODO]
│   └── counterfactual.py               # Counterfactual Reasoning [TODO]
├── integration/                        # Integration with v3.1
│   ├── __init__.py
│   ├── agent_v4.py                     # Full v4.0 agent (v3.1 + v4.0 addons)
│   └── bridge_v3_v4.py                 # Compatibility layer
├── experiments/                        # v4.0 experiments
│   ├── world_model_72h.py              # 72h experiment with World Model
│   ├── chaos_test.py                   # Chaos and phase transition tests
│   └── llm_integration.py              # LLM reasoning experiments
├── tests/                              # Unit tests
│   ├── test_world_model.py
│   ├── test_llm_reasoning.py
│   └── test_goal_space.py
└── examples/                           # Usage examples
    ├── basic_world_model.py
    ├── counterfactual_reasoning.py
    └── full_v4_agent.py

moss/docs/v4.0/
├── ARCHITECTURE_BLUEPRINT.md           # ✅ Complete architecture design
├── IMPLEMENTATION_PLAN.md              # Phase-by-phase implementation [TODO]
├── API_REFERENCE.md                    # API documentation [TODO]
└── MIGRATION_GUIDE.md                  # v3.1 → v4.0 migration [TODO]
```

---

## Current Status

### ✅ Completed
- [x] World Model core module (`core/world_model.py`)
- [x] World Model integration demo (`demo_world_model_integration.py`)
- [x] Architecture blueprint (`docs/v4.0_ARCHITECTURE_BLUEPRINT.md`)
- [x] v3.1 archival report (`docs/v3.1_ARCHIVAL_REPORT.md`)

### 🔄 In Progress
- [ ] LLM Reasoning Layer
- [ ] Open-ended Goal Space
- [ ] Cost-Benefit Evaluator
- [ ] Full v4.0 Agent integration

### ⏸️ Planned
- [ ] Chaos/Phase transition experiments
- [ ] 72h experiment with v4.0 features
- [ ] NeurIPS paper v2 (incorporating v4.0)

---

## Quick Start

### Test World Model
```bash
cd /workspace/projects/moss
python v4/core/world_model.py
```

### Run Integration Demo
```bash
python v4/demo_world_model_integration.py
```

### Import in Your Code
```python
from v4.core.world_model import WorldModel

wm = WorldModel(state_dim=8)
prediction = wm.predict(state, action)
```

---

## Design Principles

1. **Modularity**: Each layer can be used independently
2. **Compatibility**: v4.0 extends v3.1, doesn't replace it
3. **Testability**: Every module has standalone tests
4. **Observability**: Full logging and metrics

---

## Next Steps

See `docs/v4.0_ARCHITECTURE_BLUEPRINT.md` for detailed design.

Priority order:
1. ✅ World Model (DONE)
2. LLM Reasoning Layer (Week 3-4)
3. Open-ended Goal Space (Week 5-6)
4. Chaos experiments (Week 7-8)
5. Full integration (Week 9-10)

---

**Last Updated**: 2026-03-21  
**Maintainer**: Cash + Fuxi
