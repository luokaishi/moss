# MOSS v5.2.0 72h Real-World Experiment Dataset

**Dataset ID**: moss-v5.2.0-72h-realworld  
**Version**: 1.0.0  
**Release Date**: 2026-03-29  
**License**: MIT  

---

## 📊 Dataset Overview

This dataset contains the complete experimental data from the 72-hour real-world autonomous operation of MOSS (Multi-Objective Self-Driven System), validating self-driven AI behavior in operational environments.

### Key Statistics

| Metric | Value |
|--------|-------|
| **Total Runtime** | 72.06 hours |
| **Total Actions** | 33,359 |
| **Success Rate** | 100% |
| **Purpose Dimensions** | 9 (D1-D8 + Purpose strength) |
| **Tools Used** | GitHub API, Shell, Filesystem |
| **Data Format** | JSONL |

---

## 📁 Files

### 1. actions.jsonl
Complete action logs with 33,359 records.

**Schema**:
```json
{
  "timestamp": "ISO 8601 timestamp",
  "step": "integer step counter",
  "task": "task description",
  "action": {
    "tool": "github|shell|filesystem",
    "task": "task name",
    "purpose_dominant": "Survival|Curiosity|Influence|Optimization",
    "purpose_statement": "generated purpose text",
    "timestamp": "action timestamp",
    "context": {}
  },
  "result": {
    "success": "boolean",
    "tool": "tool name",
    "result": {
      "executed": "boolean",
      "output": "output text"
    }
  },
  "purpose": {
    "vector": [D1, D2, D3, D4, D5, D6, D7, D8, Purpose_strength],
    "statement": "purpose text",
    "dominant": "dominant purpose"
  }
}
```

### 2. status.json
Final experiment status snapshot.

**Fields**:
- `experiment_id`: Experiment identifier
- `timestamp`: Completion timestamp
- `step`: Final step count
- `total_elapsed_hours`: Cumulative runtime
- `stats`: Aggregated statistics
  - `total_steps`: Total step count
  - `real_world_actions`: Real-world action count
  - `github_actions`: GitHub API calls
  - `shell_actions`: Shell command executions
  - `purpose_changes`: Number of purpose transitions
  - `counter_reward_behaviors`: Counter-reward actions

### 3. experiment_metadata.json
Unified metadata for all 6 experiments in the Run 4.x + 72h series.

**Contents**:
- Run 4.1 (Phase Adaptation Baseline)
- Run 4.2 (Purpose Evolution - Primary)
- Run 4.3 (Curiosity Initial Condition)
- Run 4.4 (High Exploration Rate)
- Ablation Study (v5.0 Causal)
- 72h Real World Experiment

---

## 🔬 Usage

### Loading Data (Python)

```python
import json

# Load actions
actions = []
with open('actions.jsonl', 'r') as f:
    for line in f:
        actions.append(json.loads(line))

# Load status
with open('status.json', 'r') as f:
    status = json.load(f)

# Load metadata
with open('experiment_metadata.json', 'r') as f:
    metadata = json.load(f)
```

### Basic Analysis

```python
# Purpose distribution
from collections import Counter
purpose_counts = Counter(a['purpose']['dominant'] for a in actions)

# Tool usage
tool_counts = Counter(a['action']['tool'] for a in actions)

# Success rate
success_rate = sum(1 for a in actions if a['result']['success']) / len(actions)
```

---

## 📈 Key Findings

### Purpose Distribution
| Purpose | Count | Percentage |
|---------|-------|------------|
| Curiosity | 24,582 | 73.7% |
| Optimization | 3,630 | 10.9% |
| Survival | 3,399 | 10.2% |
| Influence | 1,748 | 5.2% |

### Tool Usage
| Tool | Count | Percentage |
|------|-------|------------|
| Shell | 24,965 | 74.8% |
| GitHub | 5,561 | 16.7% |
| Filesystem | 2,833 | 8.5% |

### Purpose Stability
- Mean vector values: ~0.25 per dimension
- Standard deviation: < 0.025
- No degradation over 72 hours

---

## 🔗 Related Resources

- **Paper**: `paper/v3_extended/paper_v31_draft.tex`
- **Analysis**: `experiments/analysis_72h/`
- **Code**: https://github.com/luokaishi/moss/releases/tag/v5.2.0
- **Release Notes**: `releases/v5.2.0_RELEASE_NOTES.md`

---

## 📚 Citation

If you use this dataset, please cite:

```bibtex
@software{moss_v5.2.0,
  author = {Cash and Fuxi},
  title = {MOSS: Multi-Objective Self-Driven System},
  version = {v5.2.0},
  year = {2026},
  url = {https://github.com/luokaishi/moss}
}
```

---

## ⚠️ Notes

- **Privacy**: This dataset contains no personal information or API credentials
- **Environment**: Actions were performed in an isolated test environment
- **Reproducibility**: Full experimental code available in the repository
- **Validation**: All data has been verified for consistency

---

## 📞 Contact

- GitHub Issues: https://github.com/luokaishi/moss/issues
- Email: moss-project@github.com

---

*Dataset prepared: 2026-03-29*  
*Part of MOSS v5.2.0 Release*
