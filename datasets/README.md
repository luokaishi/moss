# MOSS Datasets Repository

This directory contains curated datasets from MOSS experiments for reproducibility and research.

---

## Available Datasets

### v5.2.0 72h Real-World Experiment

**File**: `v5.2.0_72h_realworld.tar.gz`  
**Size**: ~28MB (compressed)  
**Contents**:
- `actions.jsonl`: 33,359 action records
- `status.json`: Final experiment status
- `experiment_metadata.json`: Unified metadata for 6 experiments
- `README.md`: Dataset documentation

**Download**: [v5.2.0_72h_realworld.tar.gz](./v5.2.0_72h_realworld.tar.gz)

**Citation**:
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

## Dataset Schema

### Action Record (actions.jsonl)

```json
{
  "timestamp": "ISO 8601",
  "step": "integer",
  "task": "string",
  "action": {
    "tool": "github|shell|filesystem",
    "task": "string",
    "purpose_dominant": "string",
    "purpose_statement": "string",
    "timestamp": "ISO 8601",
    "context": "object"
  },
  "result": {
    "success": "boolean",
    "tool": "string",
    "result": {
      "executed": "boolean",
      "output": "string"
    }
  },
  "purpose": {
    "vector": [9 floats],
    "statement": "string",
    "dominant": "string"
  }
}
```

---

## License

All datasets are released under the MIT License.

---

*Last updated: 2026-03-29*
