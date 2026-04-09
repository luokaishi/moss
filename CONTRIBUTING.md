# Contributing to MOSS

Thank you for your interest in contributing to MOSS (Multi-Objective Self-Driven System)! This document provides guidelines for contributing to the project.

---

## 🚀 Quick Start for Contributors

### Reproducing the 72h Real-World Experiment

The 72-hour real-world experiment is our flagship validation. Here's how to reproduce it:

#### Prerequisites

```bash
# System requirements
- Python 3.8+
- 4GB+ RAM
- 10GB free disk space
- Git

# Optional but recommended
- Docker
- GitHub API access (for full real-world interaction)
```

#### Step 1: Clone and Setup

```bash
git clone https://github.com/luokaishi/moss.git
cd moss

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import moss; print('MOSS installed successfully')"
```

#### Step 2: Run the 72h Experiment (Shortened Version)

For quick validation (30 minutes instead of 72 hours):

```bash
# Run 30-minute version
cd experiments/local_72h_20260325
python3 local_72h_resume.py --resume-step 0 --remaining-hours 0.5

# Monitor progress
tail -f resume_nohup_*.log
```

#### Step 3: Analyze Results

```bash
# View analysis report
cat experiments/analysis_72h/72h_experiment_analysis_report.md

# Check generated data
ls -lh actions.jsonl
wc -l actions.jsonl  # Should have ~200+ actions for 30-min run
```

---

## 🧪 Experiment Reproduction Guide

### Run 4.x Series

```bash
# Run 4.2 (4-5 hours)
cd experiments
python3 run_4_2.py

# Check results
tail -f run_4_2.out
```

### Ablation Study

```bash
cd experiments
python3 ablation_purpose.py

# View results
cat ablation_results.json
```

---

## 📊 Data Contribution

### Sharing Your Experimental Results

If you run MOSS experiments, we encourage you to share your results:

1. **Fork the repository**
2. **Add your experiment data** to `experiments/community/`
3. **Document your setup** in a README.md
4. **Submit a Pull Request**

### Data Format

```json
{
  "experiment_id": "your_experiment_name",
  "timestamp": "ISO8601",
  "duration_hours": 24,
  "total_actions": 10000,
  "purpose_distribution": {
    "Curiosity": 0.7,
    "Survival": 0.1,
    "Influence": 0.1,
    "Optimization": 0.1
  },
  "key_findings": "Brief description"
}
```

---

## 🐛 Reporting Issues

### Bug Reports

When reporting bugs, please include:

1. **MOSS version**: `git describe --tags`
2. **Python version**: `python --version`
3. **OS**: `uname -a`
4. **Error message**: Full traceback
5. **Steps to reproduce**: Minimal example

### Example Bug Report

```markdown
**Version**: v5.2.0
**Python**: 3.9.7
**OS**: Ubuntu 20.04

**Error**:
```
Traceback (most recent call last):
  File "experiments/local_72h_resume.py", line 45
    agent.step()
Exception: Purpose vector mismatch
```

**Reproduce**:
1. Clone repo
2. Run `python3 experiments/local_72h_resume.py`
3. Error occurs at step ~1000
```

---

## 💡 Feature Requests

### Suggesting Enhancements

1. **Check existing issues** first
2. **Describe the use case**: What problem does it solve?
3. **Proposed solution**: How should it work?
4. **Alternatives**: Other approaches considered

### Example Feature Request

```markdown
**Feature**: Add support for multi-modal observations

**Use Case**: Enable MOSS agents to process image inputs for visual tasks

**Proposed Solution**: 
- Add Vision Transformer (ViT) encoder
- Extend D3 (Curiosity) to support visual prediction error

**Alternatives**:
- Use pre-trained CLIP features
- Raw pixel inputs (computationally expensive)
```

---

## 🔬 Research Contributions

### Paper Improvements

To contribute to the NeurIPS 2027 submission:

1. **Review the paper**: `paper/v3_extended/paper_v31_draft.tex`
2. **Suggest edits** via Pull Request
3. **Cite additional relevant work** in related work section
4. **Propose new experiments** to strengthen validation

### New Experiments

When proposing new experiments:

1. **Hypothesis**: What are you testing?
2. **Design**: How will you test it?
3. **Expected outcomes**: What would validate/invalidate the hypothesis?
4. **Resources needed**: Compute time, storage, etc.

---

## 📝 Code Style

### Python

```python
# Follow PEP 8
# Use type hints
def calculate_purpose_vector(
    history: List[Action],
    preferences: Dict[str, float]
) -> np.ndarray:
    """
    Calculate purpose vector from history and preferences.
    
    Args:
        history: List of past actions
        preferences: Agent's preference weights
        
    Returns:
        9-dimensional purpose vector
    """
    # Implementation
    pass
```

### Documentation

- All public functions must have docstrings
- Complex algorithms need inline comments
- Update README.md if adding new features

---

## 🔄 Pull Request Process

1. **Fork** the repository
2. **Create a branch**: `git checkout -b feature/your-feature-name`
3. **Make changes** with clear commit messages
4. **Test** your changes
5. **Update documentation** if needed
6. **Submit PR** with detailed description

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Experiment data

## Testing
How was this tested?

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
```

---

## 🛡️ Safety Guidelines

When running MOSS experiments:

1. **Use isolated environments** (Docker/container)
2. **Set resource limits** (CPU < 80%, Memory < 70%)
3. **Enable safety guards** (gradient_safety_guard)
4. **Monitor continuously** for anomalous behavior
5. **Keep kill switch accessible**

See `docs/SAFETY.md` for full safety protocols.

---

## 📞 Getting Help

- **GitHub Issues**: https://github.com/luokaishi/moss/issues
- **Discussions**: https://github.com/luokaishi/moss/discussions
- **Email**: moss-project@github.com

---

## 🙏 Acknowledgments

Contributors will be acknowledged in:
- README.md Contributors section
- Release notes
- Paper acknowledgments (for significant contributions)

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

*Last updated: 2026-03-29*  
*Part of MOSS v5.2.0*
