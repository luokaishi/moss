# Autonomous Agent (v9.5)

MOSS v9.5 introduces a true **self-driven learning loop**, transforming MOSS from a sophisticated random number generator into an agent that actually learns from its environment.

## Core Concepts

### Environment Interface

The `Environment` abstract base class defines how agents interact with the world:

```python
from moss.core.autonomous_loop import Environment, Observation, Action, Reward

class MyEnvironment(Environment):
    def reset(self) -> Observation:
        # Return initial state
        return Observation(state={}, available_actions=["act1", "act2"])
    
    def step(self, action: Action) -> Tuple[Observation, Reward, bool]:
        # Execute action, return next state, reward, done flag
        reward = self.compute_reward(action)
        return next_obs, reward, done
```

### Learning Loop

The closed feedback loop: **Observe → Decide → Act → Reward → Learn → Reflect**

```python
from moss.core.autonomous_loop import (
    CodeEnvironment, LinearPolicy, LearningLoop
)

# Create environment
env = CodeEnvironment(project_path="./src", max_steps=100)

# Create policy (9-dimension compatible)
policy = LinearPolicy(
    weights=[0.1, 0.3, 0.1, 0.3, 0.05, 0.05, 0.05, 0.05, 0.1],
    learning_rate=0.01
)

# Run learning loop
loop = LearningLoop(env, policy, max_steps=100)
summary = loop.run()

print(f"Total reward: {summary['total_reward']}")
print(f"Action distribution: {summary['action_distribution']}")
```

### Policy Interface

Pluggable decision strategies:

- **RandomPolicy**: Baseline for comparison
- **EpsilonGreedyPolicy**: Classic RL with ε-decay
- **LinearPolicy**: 9-dimension weighted selection
- **UnifiedAgentPolicy**: Wraps UnifiedMOSSAgent

## Integrated System

The `IntegratedMOSSSystem` combines the 9-dimension UnifiedMOSSAgent with the LearningLoop:

```python
from moss.core.agent_bridge import IntegratedMOSSSystem

system = IntegratedMOSSSystem(
    project_path="./src",
    max_steps=100
)

summary = system.run()

print(f"Final weights: {summary['agent_state']['final_weights']}")
```

## CodeEnvironment

MOSS's core environment for code operations:

**Actions:**
- `analyze`: Analyze code quality
- `refactor`: Perform refactoring
- `test`: Run tests
- `commit`: Commit changes
- `learn`: Improve strategy
- `observe`: Monitor state

**Rewards:**
- Based on real code quality metrics
- Test pass rates
- Safety violations

## Experiment Runner

Statistical validation with N=30 standard:

```python
from moss.core.autonomous_loop import ExperimentRunner

runner = ExperimentRunner(seed=42)

# A/B test
results = runner.run_ab_test(
    env_factory=lambda: CodeEnvironment("./src", max_steps=50),
    policy_a_factory=lambda: EpsilonGreedyPolicy(epsilon=0.2),
    policy_b_factory=lambda: RandomPolicy(),
    n_runs=30,
)

print(f"Significant: {results['validation']['comparison']['hypothesis_test']['significant']}")
```

## CLI Usage

```bash
# Run autonomous agent
moss agent --task system_monitor

# Watch files and auto-analyze
moss watch ./src --pattern "*.py"
```

## Architecture

```
┌─────────────────────────────────────────┐
│         IntegratedMOSSSystem            │
├─────────────────────────────────────────┤
│  UnifiedMOSSAgent (9-dim)               │
│  ├─ UnifiedAgentEnvironment             │
│  └─ UnifiedAgentPolicy                  │
├─────────────────────────────────────────┤
│  LearningLoop                           │
│  ├─ CodeEnvironment                     │
│  ├─ Policy (Linear/EpsilonGreedy)       │
│  └─ ExperimentRunner                    │
└─────────────────────────────────────────┘
```

## Key Improvements

| Aspect | v9.4 | v9.5 |
|--------|------|------|
| Rewards | Random `np.random()` | Environment-calculated |
| Actions | 4 hardcoded strings | Dynamic feature vectors |
| Learning | None (weights fixed) | Gradient ascent update |
| 9-dim usage | D1-D4 only | All D1-D9 participate |
| Architecture | Parallel universes | Integrated via Bridge |
