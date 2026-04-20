# MOSS v8.0.0 Release Notes

**Release Date**: 2026-04-21  
**Codename**: "Genesis"  
**Status**: Pre-release (v8.0.0-dev)

---

## 🚀 Major Features

### 1. LLM-Guided Self-Modification

MOSS v8.0 introduces **LLM-guided mutation**, enabling AI agents to leverage Large Language Models for intelligent code evolution.

**Supported Providers**:
- ✅ OpenAI GPT-4
- ✅ Anthropic Claude
- ✅ Aliyun Bailian (Coding Plan)
- ✅ Local models (Qwen2.5-Coder)

**Key Innovation**: LLMs understand code semantics, generating meaningful mutations beyond random AST changes.

### 2. Hybrid Mutation Strategy

Combines the best of both worlds:
- **AST mutations**: Fast, low-cost, good for fine-tuning
- **LLM mutations**: Intelligent, semantic-aware, good for breakthroughs

**Modes**:
- `scheduled`: Fixed pattern (e.g., 2 AST + 1 LLM)
- `adaptive`: Dynamic switching based on fitness plateau
- `ast_only`: v6.x compatible fallback

### 3. v8.1 Stability Mechanisms

Three new features ensure reliable evolution:

**Elite Protection** 🛡️
- Prevents fitness degradation below 95% of historical best
- Solves the "Gen 22 crash" problem

**Adaptive Threshold** 📈
- Early: Permissive (-0.01) for exploration
- Late: Strict (-0.005) for fine-tuning

**Multi-Evaluation** 🎯
- Reduces fitness evaluation variance
- Optional 3-run averaging

---

## 📊 Experimental Results

### A/B Comparison (30 generations)

| Variant | Initial | Final | Best | Improvement | Time | Cost |
|---------|---------|-------|------|-------------|------|------|
| AST-Only | 0.6926 | 0.6818 | 0.6926 | -1.08% | 2.5min | $0 |
| LLM-v2 | 0.6670 | 0.6732 | 0.6844 | +0.62% | 10.9min | $0.11 |
| **LLM-v3** | 0.6651 | **0.6737** | **0.6954** | **+0.86%** | 43.7min | $0.54 |

**Key Findings**:
- LLM achieves positive improvement while AST degrades
- Peak performance: +4.56% at Gen 14
- 59 LLM calls over 30 generations

### Cost-Benefit Analysis

```
Cost per 1% improvement: $0.63
Time per generation: 1.46 min (vs 0.08 min for AST)
Break-even point: ~15 generations
```

---

## 🔧 Installation

```bash
# Clone repository
git clone https://github.com/luokaishi/moss.git
cd moss

# Install dependencies
pip install -r requirements.txt

# Set API key (for LLM experiments)
export DASHSCOPE_API_KEY='your-key-here'

# Run quick test
python experiment_coding_plan_v4.py
```

---

## 📖 Quick Start

### Basic Usage

```python
from moss.core.self_modification_engine import SelfModificationEngine, SMEConfig
from moss.core.hybrid_mutation import HybridStrategyConfig

# Configure hybrid strategy
hybrid_config = HybridStrategyConfig(
    mode="scheduled",
    schedule_pattern=["ast", "ast", "llm"],
    llm_budget_fraction=0.50,
)

# Configure SME with v8.1 features
config = SMEConfig(
    enable_llm_mutation=True,
    llm_provider='bailian',
    llm_model='qwen3-coder-plus',
    llm_budget_fraction=0.50,
    # Stability features
    enable_elitism=True,
    enable_adaptive_threshold=True,
)

# Run evolution
sme = SelfModificationEngine(config=config, hybrid_config=hybrid_config)
report = sme.run(max_generations=30)
```

---

## 🆕 What's New

### Added
- LLM Backend abstraction layer
- Bailian Coding Plan integration
- LLM Mutator with pre-validation
- Hybrid Mutation Strategy (scheduled/adaptive)
- Elite protection mechanism
- Adaptive acceptance threshold
- Multi-run evaluation
- 10 experiment scripts

### Changed
- Version unified to v8.0.0-dev
- README updated with LLM features
- Experiments archived (157.6 MB)

### Fixed
- Scheduled mode cooldown issue
- LLM output parsing
- Fitness evaluation stability

---

## 📁 File Structure

```
moss/
├── moss/
│   ├── core/
│   │   ├── llm_backend.py          # NEW: LLM abstraction
│   │   ├── llm_mutator.py          # NEW: LLM-guided mutation
│   │   ├── hybrid_mutation.py      # NEW: Hybrid strategy
│   │   └── self_modification_engine.py  # UPDATED: v8.1 features
│   └── ...
├── experiments/
│   ├── e9_ast_only/                # AST baseline
│   ├── e10_coding_plan_v2/         # v2 experiments
│   └── _archived/                  # Old experiments (157.6 MB)
├── experiment_coding_plan_v4.py    # RECOMMENDED: Latest script
├── BLOG_POST.md                    # Technical blog
├── PAPER_OUTLINE.md                # Academic paper outline
└── FINAL_SUMMARY.md                # Project summary
```

---

## 🎯 Use Cases

1. **AutoML**: Evolve neural network architectures
2. **Agent Optimization**: Improve decision-making policies
3. **Code Repair**: Automatically fix bugs
4. **Research**: Study emergent behavior in self-modifying systems

---

## ⚠️ Known Limitations

1. **Cost**: LLM experiments cost ~$0.50 per 30 generations
2. **Time**: 17x slower than AST-only (43.7 min vs 2.5 min)
3. **Token Limits**: Large functions may exceed LLM context
4. **Stability**: Requires elite protection for reliable results

---

## 🔮 Future Roadmap

### v8.1.x (Short-term)
- [ ] Multi-agent social evolution
- [ ] Complex environment support
- [ ] Additional LLM providers

### v8.2 (Mid-term)
- [ ] Meta-learning for evolution strategies
- [ ] Theoretical convergence analysis
- [ ] Distributed evolution

### v9.0 (Long-term)
- [ ] Real-world API integration
- [ ] Safety guarantees
- [ ] AGI readiness assessment

---

## 🤝 Contributing

We welcome contributions! Areas of interest:
- Additional LLM backends
- New mutation types
- Stability improvements
- Documentation

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📄 Citation

```bibtex
@software{moss_v8_2026,
  author = {MOSS Team},
  title = {MOSS: Multi-Objective Self-Driven System},
  version = {8.0.0},
  year = {2026},
  url = {https://github.com/luokaishi/moss}
}
```

---

## 🙏 Acknowledgments

- **阿里云百炼** - Coding Plan API support
- **开源社区** - Feedback and contributions
- **Manus** - External evaluation and suggestions

---

## 📞 Contact

- **Issues**: https://github.com/luokaishi/moss/issues
- **Discussions**: https://github.com/luokaishi/moss/discussions
- **Email**: moss-team@example.com

---

**Full Changelog**: https://github.com/luokaishi/moss/compare/v7.0.0...v8.0.0-dev
