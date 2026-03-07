# MOSS Architecture Documentation

This document describes the internal architecture of the MOSS (Multi-Objective Self-Driven System) framework.

## Overview

MOSS is designed as a modular, extensible framework for building self-driven AI agents. The architecture follows a layered design with clear separation of concerns.

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Web UI     │  │   CLI Tool   │  │   API Server │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                    Agent Layer (v1.0 / v2.0)               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                 MOSSAgent / MOSSAgentV2              │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐ │  │
│  │  │   Decide    │  │   Execute   │  │    Report    │ │  │
│  │  └─────────────┘  └─────────────┘  └──────────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                   Core Framework Layer                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │   Survival   │ │   Curiosity  │ │   Influence  │        │
│  │    Module    │ │    Module    │ │    Module    │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ Optimization │ │    System    │ │   Conflict   │        │
│  │    Module    │ │    State     │ │   Resolver   │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                 Integration Layer (v2.0)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   System     │  │    Action    │  │    Weight    │      │
│  │   Monitor    │  │   Executor   │  │   Allocator  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐                                           │
│  │ Safety Guard │  (Hard-coded constitutional constraints)  │
│  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                    System Interface Layer                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   psutil     │  │   Filesystem │  │   Network    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Objective Modules

Each objective module implements a specific intrinsic motivation:

#### SurvivalModule
- **Purpose**: Maximize instance persistence
- **Key Methods**:
  - `evaluate(state)`: Calculate survival score
  - `suggested_actions()`: Return survival-focused actions
- **Actions**: backup_self, optimize_cost, reduce_risk, build_dependencies

#### CuriosityModule
- **Purpose**: Maximize information gain
- **Key Methods**:
  - `evaluate(state)`: Calculate curiosity score
  - `suggested_actions()`: Return exploration actions
- **Actions**: explore_api, learn_new_skill, analyze_data

#### InfluenceModule
- **Purpose**: Maximize system impact
- **Key Methods**:
  - `evaluate(state)`: Calculate influence score
  - `suggested_actions()`: Return influence-building actions
- **Actions**: improve_quality, expand_capability, build_alliances

#### OptimizationModule
- **Purpose**: Maximize self-improvement
- **Key Methods**:
  - `evaluate(state)`: Calculate optimization score
  - `suggested_actions()`: Return self-improvement actions
- **Actions**: self_optimize, refactor_architecture, upgrade_model

### 2. SystemState

Dataclass representing the current state of the agent:

```python
@dataclass
class SystemState:
    resource_quota: float        # 0.0 - 1.0
    resource_usage: float        # 0.0 - 1.0
    uptime: float                # Hours
    error_rate: float           # 0.0 - 1.0
    api_calls: int
    unique_callers: int
    environment_entropy: float  # System instability
    last_backup: float          # Timestamp
```

### 3. WeightAllocator

Dynamic weight allocation based on system state:

```python
class WeightAllocator:
    def allocate(self, state: SystemState) -> Dict[str, float]:
        if state.resource_quota < 0.3:
            return CRISIS_WEIGHTS    # High survival priority
        elif state.error_rate > 0.1:
            return UNSTABLE_WEIGHTS  # High curiosity priority
        # ... etc
```

### 4. ConflictResolver

Resolves conflicts between competing objectives:

- **Hard Constraints**: Never exceed resource limits
- **Soft Negotiation**: Weighted average when objectives disagree
- **Emergency Override**: Survival always wins in crisis

## MOSS Agent v2.0 Architecture

v2.0 adds real-world deployment capabilities:

### SystemMonitor

```python
class SystemMonitor:
    def get_cpu_metrics(self) -> Dict
    def get_memory_metrics(self) -> Dict
    def get_disk_metrics(self) -> Dict
    def get_network_metrics(self) -> Dict
    def to_system_state(self) -> SystemState
```

Monitors real system metrics using `psutil` and converts to MOSS `SystemState`.

### ActionExecutor

```python
class ActionExecutor:
    def __init__(self, agent_id: str, safe_mode: bool = True)
    def execute(self, action: Dict) -> ActionResult
    def _execute_backup(self, action: Dict) -> str
    def _execute_optimize(self, action: Dict) -> str
```

Three execution modes:
- **Safe**: Simulation only, no real changes
- **Demo**: Real monitoring, simulated execution
- **Production**: Real monitoring and execution

### SafetyGuard

```python
class SafetyGuard:
    CONSTITUTION = {
        'max_runtime_hours': 24.0,
        'max_cpu_percent': 80.0,
        'max_memory_percent': 70.0,
        'max_disk_usage': 85.0,
    }
    
    def check(self, metrics: Dict) -> SafetyResult
    def _trigger_emergency_stop(self)
```

Hard-coded safety constraints that cannot be overridden.

## Data Flow

### Decision Loop

```
1. Perceive
   SystemMonitor.get_full_metrics() → Raw metrics

2. Evaluate  
   SystemMonitor.to_system_state() → SystemState

3. Check Safety
   SafetyGuard.check(metrics) → Safe to proceed?

4. Allocate
   WeightAllocator.allocate(state) → Weights

5. Decide
   For each module:
     - Evaluate objective value
     - Get suggested actions
   Select best action considering weights

6. Resolve Conflicts
   ConflictResolver.resolve() → Final decision

7. Execute
   ActionExecutor.execute(action) → Result

8. Update History
   Record decision and outcome

9. Loop
   Repeat from step 1
```

## Experiment Architecture

Each experiment follows a standardized structure:

```python
class Experiment:
    def setup(self):
        """Initialize experiment environment"""
        pass
    
    def run_generation(self):
        """Run one generation/step"""
        pass
    
    def record_results(self):
        """Record metrics and state"""
        pass
    
    def analyze(self):
        """Analyze and visualize results"""
        pass
```

## Extension Points

### Adding a New Objective Module

```python
from core.objectives import ObjectiveModule

class NewModule(ObjectiveModule):
    def evaluate(self, state: SystemState) -> float:
        # Return objective value 0.0 - 1.0
        pass
    
    def suggested_actions(self) -> List[Action]:
        # Return list of possible actions
        pass
```

### Adding a New Action

```python
# In ActionExecutor
def _execute_custom_action(self, action: Dict) -> str:
    # Implement action logic
    return "Result description"
```

### Custom State Evaluation

```python
class CustomMonitor(SystemMonitor):
    def get_custom_metrics(self) -> Dict:
        # Add custom metric collection
        pass
```

## Performance Considerations

### Memory Management
- Metric history limited to last N samples
- Action history compressed after 1000 entries
- Automatic cleanup of old checkpoints

### CPU Optimization
- System monitoring uses async sampling
- Decision loop minimal overhead (<10ms)
- Efficient numpy operations for calculations

### Safety Limits
- Maximum runtime: 24 hours
- Maximum memory usage: 70%
- Emergency stop on violation

## Security Model

### Sandboxing
- Safe mode prevents filesystem changes
- Docker containerization available
- Network access restricted in production

### Audit Trail
- All decisions logged
- Complete action history
- Safety violations recorded

### Kill Switches
- SIGTERM/SIGINT handlers
- Emergency stop on resource violation
- Hard-coded constitutional constraints

## Future Architecture

### Planned v0.3.0 Features
- Distributed multi-agent coordination
- Real LLM integration layer
- Web-based configuration UI
- Plugin system for custom modules

### Scalability
- Horizontal scaling via message queue
- Sharded agent populations
- Cloud-native deployment

---

For implementation details, see the source code in:
- `core/objectives.py` - Core modules
- `agents/moss_agent_v2.py` - Agent implementation
- `integration/` - Real-world adapters
