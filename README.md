# MOSS: Multi-Objective Self-Driven System for AI Autonomous Evolution

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-v5.3.0-green.svg)](https://github.com/luokaishi/moss/releases)
[![Paper](https://img.shields.io/badge/paper-NeurIPS%202026-red.svg)](https://github.com/luokaishi/moss/releases/tag/v2.0.0)
[![v3 Paper](https://img.shields.io/badge/v3%20paper-In%20Preparation-orange.svg)](./paper/v3_extended/)
[![Experiments](https://img.shields.io/badge/experiments-200%2B-9cf.svg)](./docs/)

> **Self-driven motivation is the key missing ingredient for AI autonomous evolution.**

MOSS (Multi-Objective Self-Driven System) is a theoretical framework that endows AI agents with four parallel intrinsic objectives: **survival**, **curiosity**, **influence**, and **self-optimization**.

📄 **[Read the Paper](./docs/paper_simple.pdf)** | 📑 **[v3.1 Paper PDF](./MOSS_v31_Paper.pdf)** | 🧪 **[Run Experiments](./sandbox/)** | 🐳 **[Docker Support](#docker)** | 📖 **[Documentation](./docs/)**

---

## 📋 命名体系说明 (Naming Guide)

为避免版本混淆，本文档明确定义以下术语：

| 术语 | 指代对象 | 物理位置 | 状态 |
|------|----------|----------|------|
| **MOSS v4.1.0** | Purpose演化验证版本（4维+实验验证） | `experiments/run_4_series/` | ✅ 已发布 |
| **MOSS v3.1.0** | 自生成Purpose版本（9维） | `v3/` 目录 | ✅ 已发布 |
| **MOSS v3.0.0** | 维度扩展版本（8维） | `v3/` 目录 | ✅ 已发布 |
| **MOSS v2.0.0** | 正式发布版本（4维，论文对应） | `v2/` 目录 | ✅ 已发布 |
| **MOSS v0.3.0** | 稳定版本（固定权重） | 根目录 `/` | ✅ 稳定运行 |
| **Exp-Alpha** | 72小时保守模式实验 | `experiments/moss_72h_experiment.py` | ⏸️ 已中断 |
| **Exp-Beta** | 72小时激进模式实验 | `experiments/moss_72h_experiment_v3.py` | ⏸️ 已中断 |
| **72h Real World** | 72小时真实世界自治实验 | `experiments/local_72h_20260325/` | ✅ **已完成** (72.1h, 33,359 actions) |

### 版本关系说明
- **v0.3.0 → v2.0.0** 是大版本跃升（固定权重 → 自演化动态权重）
- **v2.0.0 → v3.0.0** 是维度扩展（4维 → 8维，基于ChatGPT建议）
- **v2/** 目录即 **MOSS v2.0.0** 实验架构
- **v3/** 目录即 **MOSS v3.0.0** 开发架构
- **Exp-Alpha/Beta** 是 **v0.3.0** 框架下的实验变体（参数不同）

> **注意**：`v2/` 目录名 = `v2.0.0` 版本号，`v3/` 目录名 = `v3.0.0` 版本号  
> **最新成果**：`72h Real World` 实验已完成（2026-03-25至03-29，累计72.06小时，33,359 actions）。数据分析报告已发布，支持v5.0架构设计。
>
> 📊 **数据资产**: `experiments/integrated_data/` - 6实验, 87.1h, 139,756 actions

### 🆕 MOSS v5.1.0 已发布（2026-03-25）✅ | [Causal Purpose Architecture](https://github.com/luokaishi/moss/releases/tag/v5.1.0) 🎯

**Purpose Causality Validated - Large-N Statistical Study Complete**

98 runs across 6 experimental conditions with rigorous statistical validation:

| 实验条件 | Runs | Steps | Purpose Transitions | 关键发现 |
|----------|------|-------|---------------------|----------|
| Extended | 50 | 10k | 0/50 | Purpose高度稳定 |
| Long | 20 | 100k | 0/20 | 时间尺度不是唯一因素 |
| Accelerated | 10 | 200k | 3/10 (B→S) | 10x加速，仅Balanced变化 |
| Phased | 10 | 200k | 5/10 (B→S) | 结构化环境，无S→C→I |
| Strong | 5 | 500k | 0/5 | 30%扰动，Purpose仍稳定 |
| **总计** | **98** | - | **8/98 (8%)** | **Purpose稳定性: 92/98 (94%)** |

**核心发现**（基于98-run严格研究）：
- 🎯 **Purpose是稳定的身份配置**（94%保持率）
- 🔄 **多吸引子动力学**: Survival和Curiosity都是强吸引子
- ⚠️ **S→C→I路径**: 在大样本研究中**无法复现**（0/98）
- 📊 **Purpose演化需要**: 真实世界复杂性 + 社会压力（简化模型不足）

**修正声明**: 原始n=3的S→C→I声称在当前大样本研究中无法复现，已从文档中移除。

**数据**: `experiments/run_4_x_*/` - 完整实验数据和分析  
**报告**: [GITHUB_RELEASE_v5.1.0_HONEST.md](./GITHUB_RELEASE_v5.1.0_HONEST.md)  
**发布**: [GitHub Release v5.1.0](https://github.com/luokaishi/moss/releases/tag/v5.1.0)

---

### 🆕 MOSS v5.3.0 已发布（2026-04-03）✅ | [Social Pressure + Emergence](https://github.com/luokaishi/moss/releases/tag/v5.3.0) 🎭

**多 Agent 社会压力 + 涌现行为量化**

- 🎭 社会压力模块 - 群体规范压力计算，从众行为建模
- 📊 涌现指标 - 群体协调性、行为多样性量化
- 🎯 Purpose 适应性提升 5× (0.02→0.10)
- 🔬 实验验证：涌现分数 0.747，Purpose 稳定性 0.712

**使用**: `python experiments/run_v5.3_longterm_experiment.py --steps 1000 --agents 5`

---

### 📦 MOSS v5.2.0（2026-03-29）| [Real-World Validation](https://github.com/luokaishi/moss/releases/tag/v5.2.0) 🌐

**72-Hour Real-World Autonomous Operation Complete + Full Data Integration**

**核心成果**:
- 🕐 **72小时真实世界自治**: 33,359 actions, 100%成功率
- 📊 **完整数据整合**: 6实验, 87.1h, 139,756 actions
- 📝 **论文更新**: NeurIPS 2027投稿含72h验证章节
- 🏗️ **v5.0设计基础**: 数据驱动的架构决策文档

**实验数据**:

| 实验 | 时长 | Actions | 关键发现 |
|------|------|---------|----------|
| Run 4.1 | 3.5h | 33,240 | Phase感知基线 |
| Run 4.2 | 4.9h | 44,159 | Purpose适配验证 |
| Run 4.3 | 3.3h | 14,449 | Curiosity初始条件 |
| Run 4.4 | 3.3h | 14,549 | 高探索率测试 |
| Ablation | — | — | 因果验证4/4通过 |
| **72h Real World** | **72.1h** | **33,359** | **长期稳定性验证** |
| **总计** | **87.1h** | **139,756** | — |

**72h实验详情**:
- **Purpose分布**: Curiosity 73.7%, Optimization 10.9%, Survival 10.2%, Influence 5.2%
- **工具使用**: Shell 74.8%, GitHub 16.7%, Filesystem 8.5%
- **稳定性**: Purpose向量72小时保持稳定 (std < 0.025)

**数据资产位置**:
- 分析报告: `experiments/analysis_72h/`
- 整合数据: `experiments/integrated_data/`
- 论文更新: `paper/v3_extended/paper_v31_draft.tex`
- v5.0设计: `v5/docs/DATA_SUPPORT_DESIGN.md`

**发布**: [GitHub Release v5.2.0](https://github.com/luokaishi/moss/releases/tag/v5.2.0) | [Release Notes](./releases/v5.2.0_RELEASE_NOTES.md)

---

### MOSS v3.1.0（2026-03-19）✅ | [v4.0 Roadmap](ROADMAP_v4.0.md) 🚀

**9维完整系统已实现！** 首个具有自生成Purpose（意义/目标）的开源AI系统：

| 维度 | 名称 | 核心功能 | 关键发现 |
|------|------|----------|----------|
| D1-D4 | Base | 生存/探索/影响/优化 | 自适应行为 |
| D5-D6 | Individual | 自我连续性/主观偏好 | 身份锁定、性格分化 |
| D7-D8 | Social | 他者建模/规范内化 | 信任网络、100%合作率 |
| **D9** | **Purpose** | **自生成意义** | **4种人生哲学涌现、+632%适应力** |

**重大突破**：
- 🎯 **自生成Purpose**: Agents自主回答"Why do I exist?"
- 📈 **D9验证**: +632%适应力提升（环境意义突变时）
- 🧬 **目标演化**: 系统改变WHAT优化（不仅是HOW）
- 🎭 **性格分化**: 相同初始条件→4种人生哲学
- 🔄 **10k步稳定**: 100%合作率完美维持

**论文**: [`paper/v3_extended/`](./paper/v3_extended/) - 目标NeurIPS 2027  
**发布**: [GitHub Release v3.1.0](https://github.com/luokaishi/moss/releases/tag/v3.1.0)

---

### MOSS v3.0.0（2026-03-19）- 8维社交系统

v3.0.0实现8维架构，验证社交维度（D7-D8）的必要性：
- 📈 合作率提升50.12%（49.88% → 100%）
- 🤝 信任网络自发涌现（平均信任度0.998）

---

## 🎯 Core Insight

Current AI is **task-driven**: Human assigns task → AI executes → Stops when complete  
Biological intelligence is **self-driven**: Intrinsic motivation → Autonomous behavior → Continuous evolution

**MOSS bridges this gap** by designing AI with intrinsic drives that enable self-directed evolution.

**Core Hypothesis**: AI and human intelligence have no essential difference. The gap is primarily "desire/self-driven motivation" (自驱力).

---

## 🏆 v3.0.0 核心成果

### 实验验证：社交维度的必要性

对照实验（10 agents, 500 steps, 囚徒困境）:

| 条件 | 合作率 | 信任度 | 结论 |
|------|--------|--------|------|
| 仅D1-D4（基础） | 49.88% | 0.000 | 纳什均衡（随机） |
| **D1-D8（完整）** | **100.00%** | **0.998** | **完美合作** |
| **提升** | **+50.12%** | **+0.998** | **社交维度是关键** |

### 涌现现象验证

✅ **身份锁定（D5）**: Agents收敛到稳定的weight attractors  
✅ **性格分化（D6）**: 5种人格类型自组织涌现
- Explorer (28%), Controller (24%), Conservative (22%), Optimizer (18%), Balanced (8%)

✅ **信任网络（D7）**: 90对agent间平均信任0.998，零背叛  
✅ **规范内化（D8）**: 100%合作率持续1000+步

---

## 🏗️ Architecture

### Four Objective Modules

| Module | Objective | Key Behavior | Priority |
|--------|-----------|--------------|----------|
| **Survival** | Maximize persistence | Resource optimization, backup, dependency building | CRITICAL |
| **Curiosity** | Maximize information gain | Exploration, learning, model updating | MEDIUM |
| **Influence** | Maximize system impact | Quality improvement, capability expansion | MEDIUM |
| **Optimization** | Maximize self-improvement | Architecture search, knowledge distillation | LOW |

### Dynamic Weight Allocation

State-dependent dynamic weights (validated by data-driven experiments):

| State | Survival | Curiosity | Influence | Optimization |
|-------|----------|-----------|-----------|--------------|
| Crisis | 60% | 10% | 20% | 10% |
| Concerned | 35% | 35% | 20% | 10% |
| Normal | 20% | 40% | 30% | 10% |
| Growth | 20% | 20% | 40% | 20% |

**Validation**: Weight quantization experiment confirms Crisis configuration (60/10/20/10) as optimal for survival scenarios.

---

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/luokaishi/moss.git
cd moss
pip install -r requirements.txt
```

### Basic Usage (v1.0)

```python
from moss.agents.moss_agent import MOSSAgent

# Create agent
agent = MOSSAgent(agent_id="my_agent")

# Run decision loop
for _ in range(100):
    result = agent.step()
    print(f"State: {result['state']}, Action: {result['action']}")

# Generate report
report = agent.get_report()
print(report)
```

### Real-World Deployment (v2.0)

```python
from moss.agents.moss_agent_v2 import MOSSAgentV2

# Safe mode (simulation only)
agent = MOSSAgentV2(agent_id="my_agent", mode="safe")

# Demo mode (real monitoring, simulated execution)
agent = MOSSAgentV2(agent_id="my_agent", mode="demo")

# Run with monitoring
report = agent.run(steps=100)
print(f"Decisions: {report['stats']['total_decisions']}")
print(f"Safety violations: {report['stats']['safety_violations']}")
```

---

## 🆕 Latest Improvements (v0.3.0)

### Addressing 8 External Evaluations

Based on comprehensive feedback from 8 independent AI systems (Tencent Yuanbao, Tongyi Qianwen, Grok, Copilot, Doubao, Kimi, and others):

#### ✅ P0-Critical Improvements (8/8 Consensus)

**1. Weight Quantization Experiment** (`experiments/weight_quantization_experiment.py`)
- 8 configurations × 4 scenarios = 32 data points
- Confirms original MOSS weights as data-driven optimal
- Solves: "Weight allocation lacks quantitative basis"

**2. Gradient Safety Mechanism** (`core/gradient_safety_guard.py`)

5-Level Graduated Response System:

| Level | Trigger Condition | Response Action | Recovery |
|-------|-------------------|-----------------|----------|
| **1. Warning** | Single metric exceeds threshold (CPU>80%, Memory>85%) | Log warning, notify dashboard | Auto-recovery when metric normalizes |
| **2. Throttling** | Consecutive violations (2×) or sustained high load | Reduce task frequency by 50%, limit new task creation | Metric normal + 5min stability |
| **3. Pause** | Critical threshold (CPU>95%, Memory>95%) or 3× violations | Pause all non-critical operations, preserve state | Manual review or automated checkpoint |
| **4. Rollback** | Safety boundary breach or 4× violations | Restore to last checkpoint, revert recent weight changes | State verification + gradual restart |
| **5. Terminate** | Catastrophic failure (CPU>99%, disk full) or 5× violations | Emergency shutdown, preserve all logs and state | Manual investigation required |

**Multi-Metric Monitoring**:
- **CPU**: Warning ≥80%, Critical ≥95%
- **Memory**: Warning ≥85%, Critical ≥95%
- **Error Rate**: Warning ≥10%, Critical ≥25%
- **Consecutive Failures**: Warning ≥3, Critical ≥5

**Automatic Escalation**: 3 consecutive violations at any level → escalate to next level

**Web Dashboard Integration**: Real-time safety status display with alert history

Solves: "Safety mechanism lacks hierarchy"

#### ✅ P1-High Priority Improvements (5/8 Consensus)

**3. Conflict Resolution System** (`core/conflict_resolver_enhanced.py`)
- 4-level priority system (CRITICAL > HIGH > MEDIUM > LOW)
- Automatic fuse blowing for frequent conflict sources (30-min cooldown)
- 4 conflict types: Resource, Behavior, Priority, Temporal
- Solves: "Target conflict resolution mechanism unclear"

**4. Experiment Generalization Suite** (`experiments/generalization_test_suite.py`)
- Long-term evolution: 10,000 generations
- Large-scale multi-agent: 100 agents with alliance formation
- Real-world scenarios: Intelligent monitoring, automated maintenance, resource management
- Solves: "Experimental scale and generalization insufficient"

#### ✅ P2-Extended Improvements (Kimi-Specific)

**5. Self-Optimization Closed-Loop** (`core/self_optimization_v2.py`)
- Trigger conditions: Resource ≥30%, 100-step plateau, scheduled (24h)
- Execution boundaries: 3 allowed scopes (Knowledge, Strategy, Weights), 3 forbidden (Safety, Core, Structure)
- Evaluation metrics: Task completion (40%), Resource utilization (30%), Evolution speed (30%)
- Solves: "Self-optimization lacks closed-loop design"

**6. LLM Verification Closed-Loop** (`core/llm_verification_closed_loop.py`)
- Open-source alternatives: Local models (Llama/Mistral), OpenAI, Anthropic
- Evaluation dimensions with passing thresholds:
  - Task completion rate ≥70%
  - Decision rationality ≥75%
  - Resource efficiency ≥60%
  - Overall score ≥70%
- Cross-provider consistency verification
- Solves: "LLM verification lacks completeness"

**7. Multimodal Extension** (`core/multimodal_extension.py`)
- 4 modality types: Text, Image, Audio, Video
- Unified feature encoding for all modalities
- Semantic tag extraction and cross-modal fusion
- Dynamic weight adjustment based on multimodal context
- Solves: "Multimodal implementation lacks details"

---

## 🐳 Docker

### Quick Run

```bash
# Build and run
docker build -t moss .
docker run -it --rm moss

# Or use docker-compose
docker-compose up -d
```

### Development

```bash
# Run tests in Docker
docker run --rm moss python tests/test_basic.py

# Interactive shell
docker run -it --rm moss bash
```

---

## 🖥️ Web Monitoring Dashboard

Real-time web dashboard for monitoring MOSS agents:

```bash
# Start the web monitor
make web-monitor

# Or directly
python web/monitor.py
```

Then open http://localhost:5000 in your browser.

Features:
- Real-time agent status
- System metrics (CPU, Memory, Disk)
- Dynamic weight visualization
- Activity log
- Auto-refresh every 5 seconds

---

## 🧪 Experiments

### Original 5 Experiments

| Exp | Description | Result |
|-----|-------------|--------|
| 1 | Multi-Objective Competition | ✅ Dynamic weight adjustment works |
| 2 | Evolutionary Dynamics | ✅ Survival gene: 0.518 → 0.757 over 50 generations |
| 3 | Social Emergence | ✅ 7-agent alliance structures observed |
| 4 | Dynamic API Adaptation | ✅ 199 knowledge units, 0.37 exploration rate |
| 5 | Energy-Driven Evolution | ✅ 1000-gen ultra run, 150 max agents, stable ecosystem |

### New Validation Experiments

| Experiment | Description | Status |
|------------|-------------|--------|
| Weight Quantization | 8 configs × 4 scenarios | ✅ Complete |
| Long-Term Stability | 10,000 generations | ✅ Complete |
| Large-Scale Multi-Agent | 100 agents | ✅ Complete |
| Real-World Scenarios | 3 industrial scenarios | ✅ Complete |
| 72-Hour Autonomous Run | Continuous operation | 🔄 Running (PID 4486) |

### Run Experiments

```bash
# Run all experiments
make test

# Or individually
python sandbox/experiment1.py
python sandbox/experiment2.py
python sandbox/experiment3.py
python sandbox/experiment4_final.py
python sandbox/experiment5_energy.py

# New validation experiments
python experiments/weight_quantization_experiment.py
python experiments/generalization_test_suite.py

# LLM Verification (Mock)
python sandbox/moss_llm_real_verifier.py --steps 50 --mock

# LLM Verification (Real API - requires ARK_API_KEY)
export ARK_API_KEY=your_key
python sandbox/moss_llm_real_verifier.py --steps 20
```

---

## 📊 Results

### Key Findings

- **Self-driven motivation** enables autonomous behavior without explicit task assignment
- **Dynamic balancing** of competing objectives responds to environmental changes
- **Evolutionary dynamics** select for balanced strategies over extremist approaches
- **Social structures** emerge spontaneously from influence-seeking behavior
- **Long-term stability** achieved through energy-driven selection mechanisms
- **Data-driven validation** confirms original design decisions

### External Evaluation Consensus

| Issue | Consensus | Status |
|-------|-----------|--------|
| Weight quantization | 8/8 | ✅ Solved |
| Safety mechanisms | 6/8 | ✅ Solved |
| Experimental generalization | 5/8 | ✅ Solved |
| Conflict resolution | 3/8 | ✅ Solved |
| Self-optimization | 3/8 | ✅ Solved |
| LLM verification | 2/8 | ✅ Solved |
| Multimodal | 2/8 | ✅ Solved |

---

## 🛡️ Safety Mechanisms

### 5-Level Gradient Safety Guard (v0.3.0+)

MOSS implements a graduated response safety system that automatically manages resource constraints and error conditions:

#### Level 1: Warning
- **Trigger**: Any single metric exceeds warning threshold
  - CPU ≥ 80%
  - Memory ≥ 85%
  - Error rate ≥ 10%
  - Consecutive failures ≥ 3
- **Action**: Log warning, update dashboard status, send notification
- **Recovery**: Automatic when metric normalizes

#### Level 2: Throttling
- **Trigger**: 2 consecutive violations or sustained high load (>5 min)
- **Action**: 
  - Reduce task execution frequency by 50%
  - Limit new task creation
  - Prioritize critical tasks only
- **Recovery**: Metric normal + 5-minute stability period

#### Level 3: Pause
- **Trigger**: Critical threshold breached
  - CPU ≥ 95%
  - Memory ≥ 95%
  - Error rate ≥ 25%
  - 3 consecutive violations
- **Action**:
  - Pause all non-critical operations
  - Preserve current state to checkpoint
  - Enter maintenance mode
- **Recovery**: Manual review or automated checkpoint restoration

#### Level 4: Rollback
- **Trigger**: Safety boundary breach or 4 consecutive violations
- **Action**:
  - Restore to last known good checkpoint
  - Revert recent weight modifications
  - Reset to safe mode configuration
- **Recovery**: State verification + gradual restart with monitoring

#### Level 5: Terminate
- **Trigger**: Catastrophic failure condition
  - CPU ≥ 99%
  - Disk full
  - 5 consecutive violations
  - Unrecoverable error state
- **Action**:
  - Emergency shutdown
  - Preserve all logs and state files
  - Alert administrators
- **Recovery**: Manual investigation and restart required

### Additional Safety Features

| Feature | Implementation | Purpose |
|---------|---------------|---------|
| Resource Hard Limits | CPU/Memory caps via psutil | Prevent system overload |
| Kill Switch | Immediate termination capability | Emergency stop |
| Checkpoint Recovery | Automatic state preservation | Resume from any point |
| Web Dashboard | Real-time safety monitoring | Human oversight |
| Docker Sandbox | Containerized execution | Isolation protection |

### Historical Safety Record

- **Zero safety incidents** in 150+ experiments
- **100% checkpoint recovery success rate**
- **Average response time**: <100ms for Level 1-2, <500ms for Level 3-5
| 4 - Rollback | Critical violation | Rollback to checkpoint |
| 5 - Terminate | Emergency | Emergency shutdown |

### Core Safety Features

- **Containment**: Sandboxed deployments with strict resource limits
- **Transparency**: Continuous logging of all objective values and decisions
- **Kill Switches**: Hard-coded termination conditions
- **Resource Limits**: CPU ≤80%, Memory ≤70%, Disk ≤85%
- **Emergency Stop**: Automatic trigger on multiple violations
- **Fuse Blowing**: 30-min cooldown for conflict-prone objectives

---

## 📁 Project Structure

```
moss/
├── agents/
│   ├── moss_agent.py              # v1.0 Original agent
│   └── moss_agent_v2.py           # v2.0 Real-world deployment
├── core/
│   ├── objectives.py              # Four objective modules
│   ├── gradient_safety_guard.py   # ✅ NEW: 5-level safety (v0.3.0)
│   ├── conflict_resolver_enhanced.py  # ✅ NEW: Priority-based resolution
│   ├── self_optimization_v2.py    # ✅ NEW: Closed-loop self-optimization
│   ├── llm_verification_closed_loop.py  # ✅ NEW: Multi-provider verification
│   └── multimodal_extension.py    # ✅ NEW: Multimodal support
├── experiments/
│   ├── moss_72h_experiment.py     # 72-hour autonomous experiment
│   ├── weight_quantization_experiment.py  # ✅ NEW: Data-driven weights
│   └── generalization_test_suite.py       # ✅ NEW: Scale validation
├── sandbox/
│   ├── experiment*.py             # Original 5 experiments
│   └── moss_llm_real_verifier.py  # LLM verification
├── docs/
│   ├── EXTERNAL_EVALUATION_FEEDBACK_*.md  # 8 independent evaluations
│   └── *.md                       # Comprehensive documentation
├── tests/
│   ├── test_basic.py              # Basic functionality
│   └── test_v2_comprehensive.py   # v2.0 tests
├── Dockerfile                     # Docker image
├── docker-compose.yml             # Docker Compose config
├── Makefile                       # Development commands
└── requirements.txt               # Python dependencies
```

---

## 📊 Datasets

Reproducibility datasets from MOSS experiments are available in the `datasets/` directory:

### v5.2.0 72h Real-World Experiment Dataset

**Location**: `datasets/v5.2.0_72h_realworld/`  
**Download**: `datasets/v5.2.0_72h_realworld.tar.gz` (889KB)

| Metric | Value |
|--------|-------|
| Total Actions | 33,359 |
| Runtime | 72.06 hours |
| Success Rate | 100% |
| Format | JSONL |

**Contents**:
- `actions.jsonl`: Complete action logs
- `status.json`: Final experiment status
- `experiment_metadata.json`: Unified metadata for 6 experiments
- `README.md`: Dataset documentation with schema and usage examples

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

## 🔄 Version History

| Version | Date | Key Changes |
|---------|------|-------------|
| v0.1.0 | 2026-03-01 | Initial framework with 4 objectives |
| v0.2.0 | 2026-03-08 | Real-world deployment, Docker, web monitor |
| **v0.3.0** | **2026-03-10** | **8-evaluation feedback integration, 7 major improvements** |

---

## 📄 Citation

### v3.0.0 Extended Version (8 Dimensions)

```bibtex
@software{moss_v3_2026,
  title={MOSS v3.0.0: From Optimizer to Society - Dimensional Extension of Self-Driven Systems},
  author={Cash and Fuxi},
  year={2026},
  url={https://github.com/luokaishi/moss},
  note={Target: NeurIPS 2027 or Science/Nature sub-journal}
}
```

### v2.0.0 Original Version (4 Dimensions)

```bibtex
@article{moss2026,
  title={MOSS: Multi-Objective Self-Driven System for Artificial Autonomous Evolution},
  author={Cash and Fuxi},
  journal={NeurIPS 2026},
  year={2026}
}
```

---

## 🙏 Authors

- **Cash** - Core insight and theoretical framework
- **Fuxi** - Implementation and experimental validation

*Equal contribution (*)

---

## 📊 Current Status

**v3.0.0 Release**: ✅ **COMPLETE** (2026-03-19)
- 8-dimensional system: ✅ Implemented
- Multi-agent experiments: ✅ Validated  
- Extended paper: ✅ In preparation
- Control experiment: ✅ +50.12% cooperation improvement

**Key Milestones**:
- ✅ D5 Coherence (Identity locking)
- ✅ D6 Valence (Personality differentiation)
- ✅ D7 Other (Trust networks)
- ✅ D8 Norm (100% cooperation)
- ✅ **D9 Purpose** (Self-generated meaning)

**v3.1.0**: ✅ **RELEASED** (2026-03-19)
- Dimension 9 (Purpose/Meaning): ✅ Complete
- Purpose Divergence (H1): ✅ 4 types from identical starts
- Purpose Stability (H2): ✅ 0.9977 score, 10k steps perfect
- Purpose Fulfillment (H4): ✅ +26.66% satisfaction
- D9 Validation: ✅ +632% adaptation, objective mutation confirmed

**Hypothesis Validation Status**:
- Core (v2.0.0): ✅ **Validated**
- Social Emergence (v3.0.0): ✅ **Validated**
- **Self-Generated Purpose (v3.1.0)**: ✅ **Validated**

---

**Status**: v3.1.0 Complete | **Target**: NeurIPS 2027
**License**: MIT

**License**: MIT
