# Changelog

All notable changes to MOSS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [9.5.0] - 2026-04-24

### Added

#### Autonomous Agent Loop
- **Environment Interface**: Abstract base class for agent-world interaction
- **Learning Loop**: Closed feedback: Observe → Decide → Act → Reward → Learn → Reflect
- **Policy Interface**: Pluggable strategies (Random, EpsilonGreedy, Linear)
- **CodeEnvironment**: Real reward signals from code quality metrics
- **ExperimentRunner**: N=30 statistical validation, A/B testing
- **Agent Bridge**: Connects UnifiedMOSSAgent (9-dim) with LearningLoop
  - `UnifiedAgentEnvironment`: Wraps Agent as Environment
  - `UnifiedAgentPolicy`: Wraps Agent as Policy
  - `IntegratedMOSSSystem`: Full integration

#### 9-Dimension Action Selection
- `UnifiedMOSSAgent.select_action()` now uses all 9 dimensions (D1-D9)
- `_update_extended_dimensions()`: Updates D5-D8 based on history
- `_get_nine_dim_weights()`: Returns normalized 9-dim weight vector
- Added `purpose_history` attribute to track D5-D8 state

### Changed

- **File Watcher**: `AnalysisOrchestrator` now calls real `IncrementalAnalyzer`
- **CodeEnvironment**: `_estimate_quality()` uses real code analysis (samples 10 files)
- **CLI**: Fixed import paths (6 locations) to use full package names

### Fixed

- CLI import errors (bare module names → full package paths)
- Missing `moss/plugins/__init__.py`
- Version number inconsistency (6 locations now all 9.5.0)
- Incomplete `requirements.txt` (added watchdog, scipy, networkx, flask)

## [9.4.0] - 2026-04-24

### Added

#### Foundation Layer
- **Exception Hierarchy**: Unified error handling with `MossError` base class
  - `AnalysisError`, `RefactoringError`, `LSPError`, `ConfigError`, etc.
  - Error codes, context, and suggestions
- **Plugin System**: Extensible architecture for custom analyzers
  - `MossPlugin` base class
  - `PluginManager` with hook dispatch
  - Built-in plugins: GitPlugin, CoveragePlugin, TypeCheckPlugin
- **Config Manager**: Schema-based validation with auto-migration
  - Auto-migration: 9.2 → 9.3 → 9.4
  - Environment variable overrides
  - Hot-reload support

#### Agent Integration
- **Task-Aware Agent Plugin**: 5 autonomous task scenarios
  - file_organization, log_analysis, system_monitor, code_review, backup_cleanup
  - 80% forced task-action selection
  - 100% task completion rate
- **LLM Cost Controller**: Token budget management
  - Every-N-generations strategy (n=20 default)
  - Cost tracking and reporting
  - `CostAwareLLMBackend` wrapper

#### Validation & Monitoring
- **Statistical Validator**: Academic-grade validation
  - N=30 sample validation (mves standard)
  - t-test and Mann-Whitney U tests
  - Cohen's d effect size calculation
  - Automatic conclusion generation
- **File Watcher**: Real-time file monitoring
  - watchdog-based monitoring
  - Intelligent debounce batching
  - Incremental analysis integration

#### CLI Commands
- `moss agent`: Run autonomous task agent
- `moss report cost`: LLM cost report
- `moss validate`: Statistical validation
- `moss watch`: Real-time file monitoring

## [9.3.0] - 2026-04-24

### Added

#### Performance Engine
- **Incremental Analyzer**: Change detection with multi-level cache
  - L1: In-memory LRU cache
  - L2: Disk-based TTL cache
  - L3: Persistent file cache
  - Dependency invalidation
- **Parallel Analyzer**: Multi-core CPU acceleration
  - Dynamic load balancing
  - 6-12x speedup target
- **Performance Engine**: Integrates incremental + parallel + caching

#### ML Features
- **Refactoring Recommender**: History-based recommendations
  - Confidence scoring
  - Effect prediction
- **Pattern Learning Engine**: Code pattern recognition
  - Anti-pattern detection
  - Project-specific best practices

#### IDE Integration
- **LSP Server**: Language Server Protocol 3.17
  - Diagnostics, code actions, completion
  - Hover, rename, go-to-definition
- **VSCode Extension**: Full LSP client
- **PyCharm Plugin**: Inspections and quick fixes

#### Team Collaboration
- **TeamManager**: Shared configuration
- **Audit Logging**: Change tracking
- **Knowledge Base**: Pattern sharing

## [9.2.0] - 2026-04-20

### Added

#### Cross-File Refactoring
- **CrossFileRefactorEngine**: Multi-file refactoring with safety
  - Import graph analysis
  - Symbol tracking
  - Impact analysis
  - Transaction management (rollback)
- **Move Operations**: Function/class movement across files
- **Split Operations**: Module splitting into sub-modules

## [9.1.0] - 2026-04-18

### Added

- **Semantic Refactor Engine**: LLM-driven semantic refactoring
  - AST + LLM dual-engine
  - Safety sandbox

## [9.0.0] - 2026-04-15

### Added

- **Unified Agent Architecture**: 9-dimensional system
  - D1-D4: Survival, Curiosity, Influence, Optimization
  - D5-D8: Coherence, Valence, Other, Norm
  - D9: Purpose
- **Multi-Agent System**: Registry, Message Bus, Conflict Resolver
- **Self-Modification Engine**: AST-level code mutation
- **LLM Backend**: Unified interface for 5 backends

## [8.x] - 2026-04-01 to 2026-04-14

### Added

- Hybrid mutation strategy (AST + LLM)
- Meta-SME (Self-Modifying the Self-Modifier)
- Elite preservation mechanism
- Statistical validation experiments (N=30)

## [7.x] - 2026-03-15 to 2026-03-31

### Added

- Multi-agent collaboration
- Real-world bridge (GitHub, browser, filesystem)
- Purpose dynamics (D9 formalization)

## [6.x] - 2026-03-01 to 2026-03-14

### Added

- Self-improvement orchestrator
- Gradient safety guard
- Conflict resolution system

## [5.x] - 2026-02-15 to 2026-02-28

### Added

- Causal purpose architecture
- State decision model
- MOSS mathematical framework

## [4.x] - 2026-02-01 to 2026-02-14

### Added

- Extended dimensions (D5-D8)
- Valence and coherence modules
- Other-modeling and norm internalization

## [3.x] - 2026-01-15 to 2026-01-31

### Added

- Unified agent architecture
- Four intrinsic objectives (D1-D4)
- Purpose generator (D9 initial)

## [2.x] - 2026-01-01 to 2026-01-14

### Added

- Core agent framework
- Basic objective modules
- Safety mechanisms

## [1.0.0] - 2025-12-25

### Added

- Initial release
- Basic code analysis
- Simple refactoring

---

[9.5.0]: https://github.com/luokaishi/moss/releases/tag/v9.5.0
[9.4.0]: https://github.com/luokaishi/moss/releases/tag/v9.4.0
[9.3.0]: https://github.com/luokaishi/moss/releases/tag/v9.3.0
[9.2.0]: https://github.com/luokaishi/moss/releases/tag/v9.2.0
[9.1.0]: https://github.com/luokaishi/moss/releases/tag/v9.1.0
[9.0.0]: https://github.com/luokaishi/moss/releases/tag/v9.0.0
