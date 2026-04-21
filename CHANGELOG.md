# MOSS Changelog

All notable changes to the MOSS project.

## [8.1.0-dev] - 2026-04-21

### 🧬 v8.1: LLM-Guided Mutation Stabilization & Budget Fix

**Critical fixes and stability features ensuring LLM participates in full 30-generation evolution.**

### Added

#### v8.1 Stability Features (`moss/core/self_modification_engine.py`)
- **Elite Protection** (`enable_elitism`): Prevents catastrophic fitness regression by rejecting mutations below `elite_threshold × best_fitness`
- **Adaptive Acceptance Threshold** (`enable_adaptive_threshold`): Linear interpolation from permissive (early) to strict (late) acceptance
- **Multi-Run Evaluation** (`enable_multi_eval`): N-run averaging with std reporting to reduce fitness noise

#### Experiment Results (5 groups, 30 generations each)

| Experiment | LLM Participation | Peak Fitness | Improvement | Stability (σ) |
|-----------|-------------------|-------------|-------------|---------------|
| AST-only | 0% | 0.6881 | -1.08% | 0.0068 |
| v2 (budget exhaust) | 20% (Gen 1-7 only) | 0.6844 | +0.62% | 0.0078 |
| v3 (full LLM) | 43.3% | 0.6954 | +0.86% | 0.0130 |
| v4 (budget fail) | 16.7% (Gen 1-7 only) | 0.6760 | -0.25% | 0.0073 |
| **v4 fixed (v8.1)** | **66.7%** | **0.6910** | **+0.27%** | **0.0081** |

### Fixed

- **Critical: Token budget exhaustion** — `llm_daily_token_budget` default (100K) only supports 7 generations. Increased to 500K for full 30-gen runs.
- **Critical: Scheduled mode cooldown** — Removed cooldown check in scheduled mode, ensuring LLM calls follow `["ast", "ast", "llm"]` pattern for all 30 generations.
- **torch optional import** — `import torch` in `local_llm_backend.py` now gracefully degrades when PyTorch not installed.
- **`__init__.py` LocalLLMBackend import** — Wrapped in try/except for environments without torch/transformers.
- **BailianBackend `_client` attribute** — Added `self._client = None` initialization to prevent AttributeError.
- **Coding Plan model name** — Changed from `qwen-coder-plus` (404) to `qwen3-coder-plus`.

### Changed

- `requirements.txt` updated to v8.1.0-dev with `openai>=1.0.0` dependency
- `local_llm_backend.py`: torch is now optional import with clear error on use
- `__init__.py`: LocalLLMBackend import is optional (graceful degradation)

### Experiment Configuration (v4 fixed)

```python
HybridStrategyConfig(mode="scheduled", schedule_pattern=["ast", "ast", "llm"], llm_budget_fraction=0.50)
SMEConfig(
    enable_llm_mutation=True,
    llm_provider='bailian',
    llm_model='qwen3-coder-plus',
    llm_base_url='https://coding.dashscope.aliyuncs.com/v1',
    llm_daily_token_budget=500000,  # Key fix
    llm_daily_request_budget=500,
    enable_elitism=True,
    enable_adaptive_threshold=True,
)
```

## [8.0.0-dev] - 2026-04-16

### 🔬 Phase 2 Progress: Rigorous Statistical Validation

Running N=5 independent trials per experiment (30 generations, Welch's t-test + bootstrap CI):

**E2: Pareto vs Scalar Fitness — CONFIRMED ✅**
- Acceptance rate: Pareto 60.7% vs Scalar 35.3% — **p=0.001, Cohen's d=2.07** (strongly significant)
- Fitness Δ: Pareto +0.0155 vs Scalar −0.0020 (+858%) — p=0.079 (large effect, needs N≥8)
- Hypervolume: HV=0.161±0.013 (95% CI: [0.151, 0.171])

**E1: Semantic-Guided vs Random Mutation — Partial**
- Acceptance rate: Semantic 40.0% vs Random 35.3% — p=0.174 (d=0.86, needs N≥10)
- Fitness Δ results are mixed at N=5; more trials needed

**E3: Meta-SME Stability — In Progress**
- Preliminary N=2 pilot collected; full N=5×30-gen run in progress

**Infrastructure**
- Added `experiments/statistical_validation/` with runner, reports, and analysis tools
- Updated `.gitignore`: exclude runtime backup/sme_run/jsonl artifacts from version control
- New doc: `docs/MOSS_PHASE2_STATISTICAL_VALIDATION_REPORT.md`

## [7.0.0] - 2026-04-16

### 🧬 Major Release: Meta-SME — Self-Modifying the Self-Modifier

**The ultimate form of code self-modification: the engine rewrites its own code.**

### Added

#### Self-Modification Engine v7.0 (`moss/core/self_modification_engine.py`, ~1900 lines)
Complete code self-modification pipeline with four layers of evolution:

- **v6.1 Code Self-Modification Engine**
  - 9 AST mutation types: constant_tweak, condition_flip, weight_shift, threshold_mutate, action_insert, epsilon_tune, weight_hardcode, action_shuffle, branch_inject
  - Sandboxed execution with 3-stage validation (syntax + import + instantiation, ≥2/3 pass)
  - EmergenceGuidedFitness: success_rate(0.35) + diversity(0.25) + purpose_align(0.20) + emergence(0.20)
  - 30-generation evolution: fitness +6.3% (0.7257→0.7713), 33% acceptance rate

- **v6.2 Semantic-Guided Mutation (PurposeGuidedSelector)**
  - Purpose vector D9 → 4D semantic mapping for 9 mutation types
  - Cosine similarity between mutation intent and current purpose
  - Softmax-weighted mutation selection with temperature control
  - **Acceptance rate: 25% → 41% (+60% improvement)**

- **v6.3 Pareto Multi-Objective Optimization (ParetoArchive)**
  - 4-dimensional non-dominated solution archive (max capacity: 50)
  - Crowding distance for diversity preservation
  - NSGA-II-style non-dominated sorting for acceptance
  - **Δfitness: +144%, acceptance rate: 62%, Hypervolume: 0.176**

- **v7.0 Meta-SME (Meta-Level Self-Rewriting)**
  - Engine modifies its own source code (`self_modification_engine.py`)
  - Three-layer safety mechanism:
    1. Immutable function whitelist (core I/O functions protected)
    2. Dual sandbox verification (syntax + functional test)
    3. Automatic rollback on failure
  - **50-generation Meta evolution: Meta-fitness +26.3%**

#### Experiment Scripts
- `experiments/run_v62_semantic_guided.py` — v6.2 semantic vs random comparison
- `experiments/run_v63_pareto.py` — v6.3 Pareto vs scalar fitness comparison
- `experiments/run_v70_meta_sme.py` — v7.0 Meta-SME self-modification experiment
- `experiments/self_modification/` — Result data directory

#### Technical Reports
- `docs/MOSS_V62_SEMANTIC_REPORT.md` — v6.2 semantic guidance results
- `docs/MOSS_V63_PARETO_REPORT.md` — v6.3 Pareto optimization analysis
- `docs/MOSS_V70_META_REPORT.md` — v7.0 Meta-SME technical report

#### Paper v3.0 (`paper/main.tex`)
- Complete rewrite of abstract covering v6.1-v7.0
- New Section: Self-Modification Engine architecture
- 7 comparison tables (mutation types, semantic vectors, version evolution, etc.)
- Discussion on efficiency-safety tradeoff and open-loop learning

### Changed
- `moss/core/self_modification_engine.py` extended from ~900 to ~1900 lines
- `moss/api/adapter.py` updated for v7.0 compatibility
- All new features backward-compatible via `SMEConfig` flags

---

## [6.3.0] - 2026-04-15

### 📊 Pareto Multi-Objective Optimization

### Added
- `ParetoArchive` class: 4D non-dominated solution maintenance
- Crowding distance calculation for archive pruning
- NSGA-II-style non-dominated sorting replacing scalar fitness comparison
- 3 Pareto-optimal strategies discovered (balanced, explorative, emergent)

### Key Results
- Hypervolume (HV): 0.176
- Archive utilization: 50/50 solutions
- Δfitness vs scalar baseline: +144%
- Acceptance rate: 62%

---

## [6.2.0] - 2026-04-14

### 🎯 Semantic-Guided Mutation

### Added
- `PurposeGuidedSelector` class: purpose-aware mutation direction selection
- 9×4 semantic mapping matrix (mutation types × fitness dimensions)
- Cosine similarity-based alignment scoring
- Softmax temperature parameter for exploration-exploitation balance

### Key Results
- Acceptance rate: 25% → 41% (+60% improvement)
- Fitness: 0.7713 → 0.7930 (+2.8%)
- Optimal temperature: 0.7

---

## [6.1.0] - 2026-04-13

### 🔧 Code Self-Modification Engine (First Implementation)

### Added
- `SelfModificationEngine` class: AST-based code mutation framework
- `ASTMutator` with 9 mutation types for Python AST manipulation
- `CodeSandbox` with 3-stage validation pipeline
- `EmergenceGuidedFitness`: 4-component fitness function
- `SMEConfig` for backward-compatible configuration

### Key Results
- 30 generations of evolution
- 10 accepted mutations (33% acceptance rate)
- Fitness: 0.7257 → 0.7713 (+6.3%)
- Target functions: `step` (score=54), `_apply_state_weights` (score=30)

### Technical Report
- `docs/MOSS_V6_SELF_MODIFICATION_REPORT_V2_20260413.md`

---

## [5.2.0] - 2026-03-29

### 🎯 Major Release: 72-Hour Real-World Autonomous Operation Validated

**Complete Real-World Validation with 72h Continuous Operation + Full Data Integration**

### Added

#### 72-Hour Real-World Experiment (`experiments/local_72h_20260325/`)
- **Duration**: 72.06 hours continuous autonomous operation
- **Actions**: 33,359 total (100% success rate)
- **Environment**: Real-world tools (GitHub API, shell, filesystem)
- **Purpose Stability**: Maintained throughout 72 hours (Curiosity-dominant: 73.7%)
- **Tool Usage Distribution**:
  - Shell: 24,965 actions (74.8%)
  - GitHub: 5,561 actions (16.7%)
  - Filesystem: 2,833 actions (8.5%)

#### Integrated Data Assets (`experiments/integrated_data/`)
- **Experiment Metadata** (`experiment_metadata.json`)
  - Unified index of all 6 experiments
  - 87.1 hours total runtime, 139,756 actions
  
- **Integration Overview** (`DATA_INTEGRATION_OVERVIEW.md`)
  - Complete data asset inventory
  - Quality assessment and validation summary

#### Comprehensive Analysis Reports (`experiments/analysis_72h/`)
- **72h Experiment Analysis** (`72h_experiment_analysis_report.md`)
  - Purpose evolution trajectory analysis
  - Tool usage patterns and task distribution
  - Comparison with Run 4.x series
  
- **Run 4.x vs 72h Comparison** (`run4x_vs_72h_comparison.md`)
  - Cross-experiment analysis
  - Environmental impact on Purpose convergence
  - v5.0 design implications

#### Paper Integration (`paper/v3_extended/`)
- **Updated Paper Draft** (`paper_v31_draft.tex`)
  - New "Real World Validation" section
  - 72h experiment results integrated
  - Combined validation: 87.1h, 139,756 actions

#### v5.0 Design Support (`v5/docs/`)
- **Data Support Document** (`DATA_SUPPORT_DESIGN.md`)
  - Empirical foundation for v5.0 architecture
  - Data-driven design decisions
  - Validation framework based on experimental results

### Changed

- **README.md**: Updated 72h experiment status to "Completed"
- **v5/README.md**: Marked 72h tasks as completed
- **PRIMARY_EXPERIMENT_TRACKING.md**: Archived as historical record
- **DEPLOY_72H_MONITOR.md**: Cleaned up cloud-specific references
- **REMOTE_DEPLOY_GUIDE.md**: Standardized to generic deployment

### Data Assets Summary

| Experiment | Duration | Actions | Status |
|------------|----------|---------|--------|
| Run 4.1 | 3.5h | 33,240 | ✅ Completed |
| Run 4.2 | 4.9h | 44,159 | ✅ Completed |
| Run 4.3 | 3.3h | 14,449 | ✅ Completed |
| Run 4.4 | 3.3h | 14,549 | ✅ Completed |
| Ablation | — | — | ✅ 4/4 tests passed |
| 72h Real World | 72.1h | 33,359 | ✅ Completed |
| **Total** | **87.1h** | **139,756** | — |

### Validation Milestones

- ✅ Purpose Evolution: Validated across 4 independent runs
- ✅ Long-term Stability: 72-hour continuous operation
- ✅ Causal Necessity: Ablation study (+42.8% improvement)
- ✅ Real-world Adaptation: GitHub/shell/filesystem integration
- ✅ Paper Integration: 72h results in NeurIPS submission draft

---

## [4.1.0] - 2026-03-24

### 🎯 Major Release: Purpose Evolution Reproducibility Validated

**Run 4.x Series: Three Independent Experiments Prove Influence is Stable Attractor**

### Added

#### Run 4.x Experimental Series (`experiments/run_4_series/`)
Three independent long-running experiments (2,880,000 steps each) validating Purpose system reproducibility:

- **Run 4.2 (Baseline)**
  - Initial Purpose: Survival, Exploration Rate: 10%
  - Trajectory: Survival → Curiosity → **Influence**
  - Duration: 4.9h, Success Rate: 57.7%
  - Data: 44,159 action records

- **Run 4.3 (Curiosity Initial)**
  - Initial Purpose: Curiosity, Exploration Rate: 10%
  - Trajectory: Curiosity → Survival → **Influence**
  - Duration: 3.3h, Success Rate: 46%
  - Data: 14,449 action records
  - **Key Finding**: Initial Purpose affects path, not endpoint

- **Run 4.4 (High Exploration)**
  - Initial Purpose: Survival, Exploration Rate: 20%
  - Trajectory: Survival → Curiosity → **Influence**
  - Duration: 3.3h, Success Rate: 58%
  - Data: 14,549 action records
  - **Key Finding**: Higher exploration delays but doesn't prevent convergence

#### Analysis Tools
- **Cross-Run Analysis Script** (`experiments/analysis/analyze_run4_series.py`)
  - Automated comparison of Purpose evolution across experiments
  - Purpose distribution analysis
  - Success rate and diversity metrics

- **Comprehensive Report** (`experiments/analysis/RUN_4_SERIES_FINAL_REPORT.md`)
  - Detailed experimental results and findings
  - Hypothesis validation summary
  - Research implications

#### Project Management Framework
- **Management Guidelines** (`docs/PROJECT_MANAGEMENT_FRAMEWORK.md`)
  - Triple-verification mechanism for experiment status reporting
  - Chaos prevention protocols
  - Sub-Agent deployment specifications

### Key Findings

1. **Influence is Stable Attractor in Social Phase**
   - All three experiments (100%) converged to Influence
   - Demonstrates reproducible Purpose evolution
   - Environment Phase determines attractor, not initialization

2. **Path Dependence vs Endpoint Determinism**
   - Initial Purpose affects evolution path
   - Exploration rate affects convergence speed
   - Environment Phase determines final Purpose state

3. **Phase-Locked Adaptation**
   - Threat Phase → Survival Purpose
   - Novelty Phase → Curiosity Purpose
   - Social Phase → Influence Purpose

### Paper Update
- Added "Purpose Evolution Reproducibility (Run 4.x Series)" section to paper
- Updated experimental results in `paper/v3_extended/main.tex`
- Validates robustness of Purpose-driven behavior

## [3.1.0] - 2026-03-19

### 🚀 Major Release: Self-Generated Purpose (9D System)

**From Society to Self: First open-source AI with self-generated meaning**

### Added

#### Dimension 9: Purpose/Meaning
- **Purpose Generator** (`v3/core/purpose.py`)
  - Self-generated answers to "Why do I exist?"
  - Purpose vector construction from history, preferences, social context, coherence
  - Natural language purpose statement generation
  - Meta-reward R_meta driving behavior beyond immediate reward

- **9D Agent** (`v3/core/agent_9d.py`)
  - Full integration of D9 Purpose with D1-D8
  - Purpose-guided weight adjustment
  - Purpose dialogue protocol for agent-to-agent meaning exchange
  - Objective mutation: system changes WHAT it optimizes (not just HOW)

#### Purpose Experiments (4 Hypotheses Validated)
- **H1: Purpose Divergence** (`v3/experiments/purpose_society.py`)
  - 6 identical agents → 4 distinct purpose types
  - Result: 50% Influence, 16.7% each for Optimization/Curiosity/Survival
  
- **H2: Purpose Stability** (`v3/experiments/purpose_stability.py`)
  - 1,000 steps: Stability score 0.9977
  - 10,000 steps: Perfect stability (100% cooperation, trust 1.000)
  
- **H3: Purpose Society** (`v3/experiments/purpose_factions.py`)
  - 12 agents under resource scarcity
  - Result: Unity under pressure (17K conflicts, maintained cohesion)
  
- **H4: Purpose Fulfillment** (`v3/experiments/purpose_fulfillment.py`)
  - Purpose-guided vs Non-Purpose comparison
  - Result: +26.66% higher satisfaction

#### D9 Validation Experiment
- **Goal Evolution Under Meta-Constraint** (`v3/experiments/goal_evolution_test.py`)
  - Unforgeable test recommended by GPT
  - Baseline (no D9): -0.250 reward → COLLAPSED
  - MOSS v3.1: +1.331 reward → ADAPTED (+632%!)
  - M structure mutation: Deleted C/I, added Stability
  - **Status**: D9 FULLY VALIDATED

#### Extended Paper v3.1
- `paper/v3_extended/paper_v31_draft.tex` - Complete manuscript
- D9 validation section with objective mutation results
- 10,000-step long-term stability validation
- 5 publication-quality figures

#### Demos
- `demo_v31_master.py` - Unified showcase of all v3.1 features
- Purpose dialogue demonstrations
- Meta-cognitive interaction examples

### Key Results

| Experiment | Result | Significance |
|------------|--------|--------------|
| Purpose Divergence | 4 types from identical starts | Individuality emerges |
| Purpose Stability | 0.9977 (1k steps), 100% (10k steps) | Identity persistence |
| Purpose Fulfillment | +26.66% satisfaction | Self-alignment works |
| D9 Validation | +632% adaptation | True objective mutation |

### World Firsts
1. First open-source system with self-generated Purpose
2. First 9-dimensional self-driven architecture
3. First empirical validation of artificial meaning emergence
4. First "unforgeable" D9 validation experiment

---

## [3.0.0] - 2026-03-19

### 🎉 Major Release: 8-Dimensional Extension

**From Optimizer to Society: Complete dimensional expansion based on ChatGPT theoretical framework**

### Added

#### Core Dimensions (D5-D8)
- **D5: Coherence Module** (`v3/core/coherence.py`)
  - Self-continuity through EMA reference identity
  - Identity locking and path stability
  - Weight attractor convergence detection
  
- **D6: Valence Module** (`v3/core/valence.py`)
  - Subjective preference with learnable beta weights
  - Personality differentiation (5 types: Explorer, Controller, Conservative, Optimizer, Balanced)
  - Loss aversion and non-optimal behavior emergence
  
- **D7: Other Module** (`v3/core/other.py`)
  - Theory of mind for agent modeling
  - Trust networks with reinforcement learning updates
  - Reputation tracking and behavior prediction
  
- **D8: Norm Module** (`v3/core/norm.py`)
  - Norm internalization through social and self-penalties
  - Three convergence types: strong_norm, opportunistic, norm_collapse
  - Long-term structure prioritized over short-term optimization

#### Multi-Agent Society
- `v3/social/multi_agent_society.py` - Full social environment
- Prisoner's dilemma repeated game implementation
- Trust-based action selection
- Norm-based cooperation emergence

#### Experiments & Validation
- **Control Experiment** (`v3/experiments/longterm_control_experiment.py`)
  - With vs Without D7-D8 comparison
  - Result: +50.12% cooperation improvement
  
- **Visualization Suite** (`v3/experiments/visualization.py`)
  - 8D evolution plots
  - Personality distribution charts
  - Trust network graphs
  - Norm convergence analysis
  
- **Parameter Sensitivity** (`v3/experiments/param_sensitivity.py`)
  - Coherence alpha analysis
  - Valence gamma analysis
  - Payoff matrix variations
  - Norm learning rate effects
  
- **Long-term Simulation** (`v3/experiments/long_term_simulation.py`)
  - 10,000+ step framework
  - Checkpoint system
  - Evolution tracking

#### Documentation
- `v3/README.md` - Version guide
- `v3/ROADMAP.md` - Development roadmap (all phases complete)
- `v3/REPORT.md` - Comprehensive results report
- `v3/COMPLETION.md` - Project completion summary
- `docs/chatgpt_analysis*.md` (×4) - Theoretical foundation from ChatGPT discussions

#### Extended Paper
- `paper/v3_extended/main.tex` - LaTeX manuscript for NeurIPS 2027
- `paper/v3_extended/README.md` - Paper planning guide
- 4 publication-ready figures

#### Quick Start
- `demo.py` - 5-minute interactive demo showcasing all features

### Key Findings

#### Experimental Results
| Metric | Without D7-D8 | With D7-D8 | Improvement |
|--------|---------------|------------|-------------|
| Cooperation Rate | 49.88% | **100.00%** | **+50.12%** |
| Mean Trust | 0.000 | **0.998** | **+0.998** |
| Personality Types | N/A | **5 types** | Emergent |

#### Emergent Phenomena
- ✅ Identity locking through D5 Coherence
- ✅ Personality differentiation through D6 Valence (5 types)
- ✅ Trust network emergence through D7 Other (0.998 mean trust)
- ✅ Norm internalization through D8 Norm (100% cooperation)

### Changed
- Updated main README.md with v3.0.0 achievements
- Added networkx to requirements for social network visualization
- Version badge updated to v3.0.0-dev

### Fixed
- MultiAgentSociety handles disabled social modules gracefully
- All modules tested and working with 100% cooperation validation

---

## [2.0.0] - 2026-03-15

### Original Release: 4-Dimensional Foundation

**Self-Modifying Multi-Objective Optimization: State-Dependent Specialization in Autonomous Agents**

### Added
- D1-D4: Survival, Curiosity, Influence, Optimization
- Self-modifying weight evolution
- State-dependent dynamic allocation (Crisis/Concerned/Normal/Growth)
- Path bifurcation discovery
- LLM verification with DeepSeek-V3
- 25-run statistical validation
- Paper submission to NeurIPS 2026

### Key Results
- 40-460% higher cumulative reward vs fixed baselines
- Path bifurcation: identical initial conditions → divergent strategies
- 48% converge to curiosity-dominant, 5 distinct strategies emerge

---

## Version History

- **v8.0.0-dev** (2026-04-16) - Meta-SME, code self-modification ultimate form, paper v3.0
- **v6.3.0** (2026-04-15) - Pareto multi-objective optimization
- **v6.2.0** (2026-04-14) - Semantic-guided mutation
- **v6.1.0** (2026-04-13) - Code self-modification engine
- **v5.2.0** (2026-03-29) - 72h real-world autonomous operation
- **v5.1.0** (2026-03-25) - Purpose causality validation (98-run study)
- **v4.1.0** (2026-03-24) - Purpose evolution reproducibility
- **v3.1.0** (2026-03-19) - 9D system with self-generated Purpose
- **v3.0.0** (2026-03-19) - 8-dimensional extension, social emergence
- **v2.0.0** (2026-03-15) - 4-dimensional foundation, NeurIPS 2026 submission
- **v0.3.0** (2026-03-06) - Fixed weight baseline, initial experiments

---

## Future Work

### v7.x (Planned)
- Scale Meta-SME to 100-200 generations for long-term adaptation study
- Statistical significance validation (N≥10 independent runs)
- LaTeX figures: fitness evolution curves, Pareto frontier scatter plots
- arXiv submission

### v8.0 (Vision)
- Integration with LLM-based code generation
- Multi-agent self-modification coordination
- External tool discovery and integration
- Real-world deployment with self-modification
