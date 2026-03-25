# Phase 2 Multi-Agent System - Preparation Document

**Phase**: 2 (Multi-Agent Social Dynamics)  
**Goal**: Deploy 10-20 agents to study multi-stability in social contexts  
**Purpose**: Serve as "killer experiment" for multi-stability validation  
**Timeline**: Start after 72h experiment completion (~46 hours remaining)

---

## 1. Phase 2 Objectives

### Primary Objectives
1. **Social Multi-Stability**: Do groups of agents exhibit collective attractor states?
2. **Norm Emergence**: Do social norms emerge as stable configurations?
3. **Phase Transition**: Can social pressure induce Purpose transitions?

### Secondary Objectives
1. Test PurposeDynamics in multi-agent setting
2. Validate attractor basin theory with social coupling
3. Generate real social interaction data

---

## 2. Architecture Design

### 2.1 Multi-Agent Configuration

**Agent Count**: 10-20 instances
**Recommendation**: Start with 10, scale to 20 if stable

**Each Agent**:
- UnifiedMOSSAgent with CausalPurposeGenerator
- PurposeDynamics module enabled
- Unique initial Purpose (varied distribution)

### 2.2 Initial Purpose Distribution

To test multi-stability, initialize agents with diverse Purpose configurations:

| Agent ID | Initial Purpose | Rationale |
|----------|----------------|-----------|
| Agent 1-3 | Survival-dominant | Test Survival attractor |
| Agent 4-6 | Curiosity-dominant | Test Curiosity attractor |
| Agent 7-8 | Balanced | Test instability hypothesis |
| Agent 9-10 | Random | Test convergence patterns |

### 2.3 Social Interaction Model

**Communication Topology**: 
- Option A: Fully connected (all-to-all)
- Option B: Small-world network (more realistic)
- Option C: Hierarchical (leader-follower)

**Recommendation**: Start with fully connected for simplicity

**Interaction Frequency**:
- Every 100 steps: Share Purpose state
- Every 500 steps: Collective decision
- Every 1000 steps: Norm evaluation

**Social Influence Mechanism**:
```python
# Agent i updates based on neighbors
social_influence_i = sum(
    w_ij * (P_j - P_i) 
    for j in neighbors(i)
)
P_i_new = P_i + gamma * social_influence_i + other_terms
```

Where `w_ij` is interaction strength between agents i and j.

---

## 3. Experimental Protocol

### 3.1 Phase 2a: Baseline (1-7 days)

**Setup**:
- 10 agents, fully connected
- No external pressure
- Observe spontaneous dynamics

**Measurements**:
- Purpose trajectory for each agent
- Clustering of Purpose configurations
- Transition events

**Expected Outcomes**:
- Agents maintain initial Purpose (Survival/Curiosity stable)
- Balanced agents collapse to Survival or Curiosity
- No convergence to single global optimum

### 3.2 Phase 2b: Social Pressure (7-14 days)

**Setup**:
- Introduce collective tasks requiring cooperation
- Reward alignment with group performance
- Measure Purpose adaptation

**Collective Tasks**:
- Shared resource management
- Collaborative problem solving
- Consensus decision making

**Research Question**: Does social pressure create new attractors or shift existing ones?

### 3.3 Phase 2c: Network Structure (14-21 days, Optional)

**Setup**:
- Change topology to small-world or hierarchical
- Measure impact on norm emergence

**Research Question**: How does network structure affect multi-stability?

---

## 4. Data Collection

### 4.1 Per-Agent Metrics (Every Step)
- Purpose vector [S, C, I, O]
- Attractor basin classification
- Local interaction count

### 4.2 Group Metrics (Every 100 Steps)
- Purpose distribution histogram
- Clustering coefficient
- Norm alignment score

### 4.3 Event Logging
- Purpose transitions (with cause)
- Collective decisions
- Conflict/resolution events

### 4.4 Storage
```
phase2_data/
├── agent_logs/
│   ├── agent_001.jsonl
│   ├── agent_002.jsonl
│   └── ...
├── collective_metrics.jsonl
├── transition_events.jsonl
└── summary_report.json
```

---

## 5. Implementation Plan

### 5.1 Core Components to Develop

**1. MultiAgentEnvironment** (`moss/env/multi_agent.py`)
```python
class MultiAgentEnvironment:
    def __init__(self, n_agents=10, topology='fully_connected'):
        self.agents = [UnifiedMOSSAgent(...) for _ in range(n_agents)]
        self.topology = self._create_topology(topology)
    
    def step(self):
        # 1. Each agent acts
        # 2. Process interactions
        # 3. Update social metrics
        # 4. Log data
```

**2. SocialInteractionModule** (`moss/core/social_interaction.py`)
- Handle agent-to-agent communication
- Compute social influence
- Track trust networks

**3. CollectiveTaskManager** (`moss/tasks/collective.py`)
- Generate collaborative tasks
- Evaluate group performance
- Distribute rewards

**4. NormDetector** (`moss/analysis/norm_detector.py`)
- Identify emerging norms
- Measure norm stability
- Detect norm violations

### 5.2 Integration with Existing Code

**Reuses**:
- `UnifiedMOSSAgent` (unchanged)
- `CausalPurposeGenerator` (unchanged)
- `PurposeDynamics` (unchanged)
- `PurposeDynamicsTracker` (unchanged)

**Extends**:
- Adds social layer
- Adds collective decision making
- Adds group-level metrics

### 5.3 Configuration File

```json
{
  "phase2": {
    "n_agents": 10,
    "topology": "fully_connected",
    "interaction_frequency": 100,
    "purpose_initialization": "diverse",
    "duration_days": 21,
    "logging": {
      "per_step": true,
      "per_100_steps": true,
      "events": true
    }
  }
}
```

---

## 6. Expected Scientific Outcomes

### 6.1 Hypotheses to Test

**H1 (Social Multi-Stability)**:
> Groups of agents will exhibit multiple stable collective configurations, not convergence to single group optimum.

**H2 (Norm as Attractor)**:
> Social norms will emerge as stable attractors in the collective behavior space.

**H3 (Social Induced Transition)**:
> Strong social pressure can induce Purpose transitions that don't occur in isolation.

### 6.2 Validation Criteria

| Hypothesis | Validation Metric | Success Threshold |
|------------|-------------------|-------------------|
| H1 | Number of distinct group Purpose clusters | ≥ 2 stable clusters |
| H2 | Norm stability over time | > 80% retention |
| H3 | Social-induced transitions | > 0 observed |

---

## 7. Risk Mitigation

| Risk | Probability | Mitigation |
|------|-------------|------------|
| Agents converge to single Purpose | Medium | Diverse initialization, weak coupling |
| Communication overhead too high | Low | Async messaging, batched updates |
| Data volume unmanageable | Low | Aggressive downsampling, summary stats |
| Phase 2 delays 72h analysis | None | Parallel execution, separate resources |

---

## 8. Timeline

### Immediate (72h Experiment Running)
- [ ] Develop MultiAgentEnvironment
- [ ] Implement SocialInteractionModule
- [ ] Create test scenarios (3-agent mini test)

### After 72h Completion (Day 1-3)
- [ ] Analyze 72h data
- [ ] Deploy Phase 2a (10 agents)
- [ ] Monitor first 24 hours

### Week 2-3
- [ ] Run Phase 2a to completion
- [ ] Analyze baseline results
- [ ] Deploy Phase 2b (social pressure)

### Week 4
- [ ] Complete Phase 2b
- [ ] Generate final report
- [ ] Update paper with Phase 2 results

---

## 9. Connection to Paper

Phase 2 serves as **killer experiment** for multi-stability:

**Current Evidence** (from Phase 1):
- Single agents show multi-stability
- Survival and Curiosity are attractors

**Phase 2 Contribution**:
- Extend to multi-agent setting
- Show collective multi-stability
- Demonstrate norm emergence

**Paper Impact**:
- Figure 5: Multi-agent Purpose trajectories
- Figure 6: Norm emergence timeline
- Section 5.4: Social multi-stability results

---

## 10. Next Steps

### Today (If Time Permits)
- [ ] Create MultiAgentEnvironment stub
- [ ] Define agent communication protocol
- [ ] Set up data logging infrastructure

### Tomorrow (Mar 26)
- [ ] Implement core multi-agent loop
- [ ] Create 3-agent test case
- [ ] Validate data collection

### This Week
- [ ] Complete Phase 2 implementation
- [ ] Run mini experiments (3-5 agents)
- [ ] Ready for 10-agent deployment

---

**Document Status**: Draft v1.0  
**Created**: 2026-03-25  
**Target Start**: After 72h completion (~46 hours)  
**Owner**: MOSS Project Team
