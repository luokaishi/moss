# MOSS v8.1.1 Release Notes

**Release Date**: 2026-04-21  
**Codename**: "Enhanced Elite"  
**Previous**: v8.1.0-dev

---

## 🎯 Release Highlights

v8.1.1 introduces **enhanced elite protection** with forced rollback mechanism, addressing fitness instability observed in v5 statistical validation. This release also includes complete statistical validation reports and token optimization verification.

---

## ✨ New Features

### Enhanced Elite Protection (v8.1.1)

```python
SMEConfig(
    enable_forced_rollback=True,        # NEW: Auto-rollback when fitness drops
    elite_rollback_threshold=0.93,      # Rollback if fitness < 93% of elite
    elite_archive_size=3,               # Keep N recent elite versions
    elite_min_generations=5,            # Delay rollback for early exploration
)
```

**Why**: v5 validation showed LLM group final fitness σ=0.012 vs AST σ=0.005. Enhanced elite protection prevents catastrophic regression after peak fitness.

**How**: After each generation, if `fitness < elite_rollback_threshold × best_fitness`, automatically rollback to the best elite version from archive.

---

## 📊 Statistical Validation Results

### v5 Experiment (N=5 per group, 30 generations)

| Metric | AST-only | LLM Hybrid | Δ | p-value | Effect Size |
|--------|---------|-----------|---|---------|-------------|
| Improvement | +0.0164 ± 0.0072 | +0.0184 ± 0.0150 | +0.0020 | 0.80 | d=0.17 (small) |
| **Peak Fitness** | 0.6920 ± 0.0012 | **0.6971 ± 0.0059** | **+0.0051** | **0.12** | **d=1.20 (large)** |
| Final Fitness | **0.6885 ± 0.0053** | 0.6834 ± 0.0120 | -0.0051 | 0.42 | d=-0.55 (medium) |

**Key Finding**: Peak Fitness shows large effect size (Cohen's d=1.20) but underpowered at N=5. Bootstrap 95% CI: [+0.0006, +0.0100] excludes 0. **N≥7 recommended for significance**.

### Token Optimization Verified

| Mode | Input Tokens | Output Tokens | Cost |
|------|-------------|--------------|------|
| v4 (full source) | 268,482 | 238,028 | $0.55 |
| v5 (function-level) | 101,908 | 15,569 | $0.08 |
| **Reduction** | **-62.0%** | **-93.5%** | **-85.5%** |

Function-level extraction (sending only target functions to LLM) dramatically reduces token usage.

---

## 🔧 Technical Changes

### Core Improvements

1. **Forced Rollback Mechanism** (`_check_and_rollback_to_elite()`)
   - Post-generation fitness check
   - Automatic rollback to elite archive
   - Rollback history logging

2. **Elite Archive** (`_elite_archive`)
   - Multi-version elite storage
   - Sorted by fitness for efficient retrieval
   - Configurable size limit

3. **Function-Level LLM Prompt** (`llm_mutator.py`)
   - Send only target functions vs full source
   - ~60% input token reduction
   - ~93% output token reduction

### API Changes

**New Config Options**:
- `enable_forced_rollback: bool = False`
- `elite_rollback_threshold: float = 0.93`
- `elite_archive_size: int = 3`
- `elite_min_generations: int = 5`

**No Breaking Changes**: All v8.1.0 configs remain compatible.

---

## 🧪 Validation

### Test Coverage

- ✅ Unit tests: `tests/test_sme.py` (68 tests)
- ✅ Integration: 5-gen elite protection comparison
- ✅ Statistical: N=5 validation with Welch's t-test
- ✅ Token optimization: Verified 85.5% cost reduction

### Known Limitations

1. **API Rate Limits**: Bailian Coding Plan has hourly quotas (429 errors observed)
2. **Small Sample**: N=5 insufficient for full statistical significance
3. **Short-term Elite Archive**: 5-gen test didn't trigger archive activation

---

## 📈 Performance

### Evolution Performance (30 gen)

| Configuration | Time | Cost | Peak Fitness |
|--------------|------|------|-------------|
| AST-only | ~2.5 min | $0 | 0.6920 |
| LLM Hybrid v8.1 | ~43 min | $0.55 | 0.6910 |
| LLM Hybrid v8.1.1 | ~45 min | $0.08* | TBD |

*With function-level optimization

---

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/luokaishi/moss.git
cd moss
pip install -r requirements.txt

# Set API key for LLM experiments
export DASHSCOPE_API_KEY="your-key"

# Run v8.1.1 with enhanced elite protection
python experiment_coding_plan_v4.py
```

### Example Configuration

```python
from moss.core.self_modification_engine import SMEConfig
from moss.core.hybrid_mutation import HybridStrategyConfig

config = SMEConfig(
    enable_llm_mutation=True,
    llm_provider='bailian',
    llm_model='qwen3-coder-plus',
    llm_daily_token_budget=500000,
    # v8.1 features
    enable_elitism=True,
    elitism_threshold=0.95,
    enable_adaptive_threshold=True,
    # v8.1.1 features
    enable_forced_rollback=True,
    elite_rollback_threshold=0.93,
    elite_archive_size=3,
)

hybrid = HybridStrategyConfig(
    mode="scheduled",
    schedule_pattern=["ast", "ast", "llm"],
    llm_budget_fraction=0.5,
)
```

---

## 📚 Documentation

- [V81_EXPERIMENT_ANALYSIS.md](V81_EXPERIMENT_ANALYSIS.md) - v8.1 experiment comparison
- [V5_STATISTICAL_REPORT.md](V5_STATISTICAL_REPORT.md) - N=5 statistical validation
- [CHANGELOG.md](CHANGELOG.md) - Full version history

---

## 🔮 Roadmap

### Next Steps

1. **N=10 Statistical Validation** - Complete N=10 for Peak Fitness significance
2. **Multi-Eval Verification** - Enable 3-run averaging to reduce fitness noise
3. **v9.0 Planning** - Multi-agent self-modification coordination

### Long-term

- Integration with mves branch N=45 validation methodology
- Cross-branch LLM mutation module sharing
- Real-world deployment with self-modification

---

## 🙏 Acknowledgments

- **Cash** - Core insight and theoretical framework
- **Fuxi** - Implementation and experimental validation
- **Manus** - External evaluation and methodology suggestions
- **Aliyun Bailian** - Coding Plan API support

---

## 📜 License

MIT License - See [LICENSE](LICENSE) for details.

---

**Full Changelog**: [CHANGELOG.md](CHANGELOG.md)
