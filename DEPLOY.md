# MOSS Server Deployment Guide

**Status**: Local deployment only (cloud server deployment suspended)
**Last Updated**: 2026-03-06

---

## Local Deployment (推荐)

MOSS currently runs in local environment only. Cloud server deployment is suspended.

### Quick Start

```bash
cd /workspace/projects/moss
python sandbox/experiment1.py  # Run experiments locally
```

### Run Long-term Experiments

```bash
cd /workspace/projects/moss
bash start_longterm_experiment.sh
```

Monitor with:
```bash
bash check_experiment.sh
```

---

## Manual Local Setup

### 1. Install Dependencies

```bash
pip install numpy flask requests psutil
```

### 2. Run Experiments

```python
# Run any experiment
python sandbox/experiment1.py  # Multi-objective competition
python sandbox/experiment2.py  # Evolutionary dynamics
python sandbox/experiment3.py  # Social emergence
python sandbox/experiment4_final.py  # Dynamic API adaptation
python sandbox/experiment5_energy.py  # Energy-driven evolution
```

---

## Historical: Cloud Deployment (Suspended)

Previous cloud deployment instructions have been archived. If you need to deploy to a new server in the future:

1. Update the IP address in deployment scripts
2. Ensure SSH access is configured
3. Follow standard Python deployment practices

---

## Configuration

### Environment Variables

```bash
export MOSS_AGENT_ID="moss_local_001"
export MOSS_LOG_LEVEL="INFO"
export MOSS_RESOURCE_LIMIT="0.8"
```

---

## Monitoring

### Local Logs

```bash
# View experiment logs
tail -f /workspace/projects/moss/logs/longterm_*.log

# Check experiment status
bash check_experiment.sh
```

---

## Current Status

- **Cloud Deployment**: ❌ Suspended
- **Local Experiments**: ✅ Active
- **Long-term Evolution**: ✅ Available locally

---

**Note**: Server deployment guides are archived. Current focus is on local experimentation and research validation.
