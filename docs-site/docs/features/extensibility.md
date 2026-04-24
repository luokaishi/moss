# Extensibility (v9.4)

MOSS v9.4 introduces a comprehensive extensibility framework: Plugin System, Task-Aware Agent, LLM Cost Controller, Statistical Validator, and File Watcher.

## Plugin System

### Creating a Plugin

```python
from moss.core.plugin_system import MossPlugin, HookType

class MyPlugin(MossPlugin):
    @property
    def name(self) -> str:
        return "my_plugin"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def on_load(self) -> None:
        print("MyPlugin loaded")
    
    def on_unload(self) -> None:
        print("MyPlugin unloaded")
    
    @MossPlugin.hook(HookType.PRE_ANALYSIS)
    def before_analysis(self, context: Dict) -> Dict:
        # Modify analysis context
        return context
```

### Registering Plugins

```python
from moss.core.plugin_system import PluginManager

manager = PluginManager()
manager.register(MyPlugin())
manager.load_all()
```

### Built-in Plugins

- **GitPlugin**: Git integration for version tracking
- **CoveragePlugin**: Code coverage analysis
- **TypeCheckPlugin**: Type checking integration

## Task-Aware Agent

5 autonomous task scenarios:

```python
from moss.plugins.task_agent_plugin import TaskAgentPlugin

plugin = TaskAgentPlugin()

# List available tasks
for task in plugin.list_tasks():
    print(f"{task['type']}: {task['name']}")

# Execute a task
result = plugin.execute_task("file_organization", "/path/to/dir")
print(f"Success: {result.success}")
```

### Task Scenarios

1. **file_organization**: Organize files by type and date
2. **log_analysis**: Analyze logs for patterns and errors
3. **system_monitor**: Monitor system resources
4. **code_review**: Automated code review
5. **backup_cleanup**: Manage backup files

## LLM Cost Controller

Token budget management for LLM calls:

```python
from moss.core.llm_cost_controller import (
    LLMCostController, CostBudget, CallStrategy
)

# Configure budget
budget = CostBudget(
    budget_usd=10.0,
    max_tokens_per_run=100000,
    call_strategy=CallStrategy.EVERY_N_GENERATIONS,
    n_generations=20,  # Call LLM every 20 generations
)

controller = LLMCostController(budget)

# Check if should call LLM
if controller.should_call(current_generation=100):
    result = call_llm(...)
    controller.record_call(tokens_input=1000, tokens_output=500, success=True)

# Generate report
report = controller.generate_report()
controller.print_report(report)
```

### CLI Usage

```bash
moss report cost --budget 5.0
moss report cost --history ./cost_history.json
```

## Statistical Validator

Academic-grade statistical validation:

```python
from moss.core.statistical_validator import (
    StatisticalValidator, ValidationConfig
)

validator = StatisticalValidator(
    ValidationConfig(n_samples=30, alpha=0.05)
)

# Add experiment data
validator.add_experiment("NewFeature", [0.9, 0.85, 0.92, ...])
validator.add_experiment("Baseline", [0.7, 0.72, 0.68, ...])

# Validate
report = validator.validate_experiment("NewFeature", "Baseline")

print(report.to_markdown())
# Includes: t-test, p-value, Cohen's d, confidence intervals, conclusions
```

### A/B Testing

```python
from moss.core.autonomous_loop import ExperimentRunner

runner = ExperimentRunner(seed=42)
results = runner.run_ab_test(
    env_factory=lambda: CodeEnvironment("./src"),
    policy_a_factory=lambda: EpsilonGreedyPolicy(),
    policy_b_factory=lambda: RandomPolicy(),
    n_runs=30,
)
```

### CLI Usage

```bash
moss validate --experiment exp_data.json --control ctrl_data.json
```

## File Watcher

Real-time file monitoring with intelligent debounce:

```python
from moss.core.file_watcher import FileWatcher, WatchConfig

config = WatchConfig(
    paths=["./src"],
    patterns=["*.py"],
    debounce_seconds=1.0,
    auto_analyze=True,
)

watcher = FileWatcher(config)

@watcher.on_changes
def on_changes(changes):
    print(f"Detected {len(changes)} changes")
    for change in changes:
        print(f"  {change}")

watcher.start()
```

### CLI Usage

```bash
# Watch Python files
moss watch ./src --pattern "*.py"

# Watch multiple patterns
moss watch . --pattern "*.py" --pattern "*.js" --debounce 2.0

# Watch with auto-refactor (use with caution)
moss watch ./src --pattern "*.py" --auto-refactor
```

## Architecture

```
┌─────────────────────────────────────────┐
│         Extensibility Layer (v9.4)      │
├─────────────────────────────────────────┤
│  Plugin System                          │
│  ├─ MossPlugin (base class)             │
│  ├─ PluginManager                       │
│  └─ Hook dispatch                       │
├─────────────────────────────────────────┤
│  Task-Aware Agent                       │
│  ├─ 5 task scenarios                    │
│  └─ TaskAgentPlugin                     │
├─────────────────────────────────────────┤
│  LLM Cost Controller                    │
│  ├─ Token budget management             │
│  ├─ Every-N-generations strategy        │
│  └─ Cost tracking & reporting           │
├─────────────────────────────────────────┤
│  Statistical Validator                  │
│  ├─ N=30 validation                     │
│  ├─ t-test / Mann-Whitney U             │
│  ├─ Cohen's d effect size               │
│  └─ A/B testing framework               │
├─────────────────────────────────────────┤
│  File Watcher                           │
│  ├─ watchdog-based monitoring           │
│  ├─ Debounce batching                   │
│  └─ IncrementalAnalyzer integration     │
└─────────────────────────────────────────┘
```
