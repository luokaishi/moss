# MOSS Migration Guide: agi/ → moss.core

> 从 MVES v8.6 命名空间 `agi/` 迁移到统一命名空间 `moss.core`

## 概述

MOSS v9.6.0 将 MVES v8.6 分支的所有组件合并到 `moss.core` 命名空间。
`agi/` 目录保留为**向后兼容层**，但所有导入会发出 `DeprecationWarning`。

## 迁移映射

### 核心组件

| 旧导入 (agi/) | 新导入 (moss.core) |
|---|---|
| `from agi.agent import AGIAgent` | `from moss.core import AGIAgent` |
| `from agi.genetic_programmer import GeneticProgrammer` | `from moss.core import GeneticProgrammer` |
| `from agi.genetic_programmer_v2 import GeneticProgrammerV2` | `from moss.core import GeneticProgrammerV2` |
| `from agi.genetic_programmer_v3 import GeneticProgrammerV3` | `from moss.core import GeneticProgrammerV3` |
| `from agi.drive_manager import DriveManager` | `from moss.core import DriveManager` |
| `from agi.drive_competition import DriveCompetition` | `from moss.core import DriveCompetition` |
| `from agi.drive_weight_cap import DriveWeightCap` | `from moss.core import DriveWeightCap` |
| `from agi.environment import RealEnvironment` | `from moss.core import RealEnvironment` |
| `from agi.environment_v2 import EnvState` | `from moss.core.environment_v2 import EnvState` |

### Agent 系统

| 旧导入 | 新导入 |
|---|---|
| `from agi.multi_agent_coordinator import ...` | `from moss.core import MultiAgentCoordinator` |
| `from agi.task_aware_agent import TaskAwareAgent` | `from moss.core import TaskAwareAgent` |
| `from agi.task_discovery import TaskDiscovery` | `from moss.core import TaskDiscovery` |
| `from agi.llm_integration import AGILLMIntegrator` | `from moss.core import AGILLMIntegrator` |
| `from agi.adaptive_action_selector import ...` | `from moss.core import AdaptiveActionSelector` |
| `from agi.memory_engine import MemoryEngine` | `from moss.core import MemoryEngine` |
| `from agi.behavior_tracker import BehaviorTracker` | `from moss.core import BehaviorTracker` |
| `from agi.emergence_detector import EmergenceDetector` | `from moss.core import EmergenceDetector` |

### 统一 Agent (v9.6 新增)

```python
# 新的统一 Agent 接口
from moss.core import UnifiedMOSSAgentV2, AgentMode

# v9 模式 (9-dimension integrated)
agent = UnifiedMOSSAgentV2.v9_mode(agent_id="test")

# v8.6 模式 (drive emergence)
agent = UnifiedMOSSAgentV2.v86_mode(agent_id="test")

# 统一模式 (both)
agent = UnifiedMOSSAgentV2(agent_id="test", mode=AgentMode.UNIFIED)
```

### 子包

| 旧路径 | 新路径 |
|---|---|
| `from agi.causal.engine import ...` | `from moss.core.causal.engine import ...` |
| `from agi.concept.concept_system import ...` | `from moss.core.concept.concept_system import ...` |
| `from agi.goal.goal_system import ...` | `from moss.core.goal.goal_system import ...` |
| `from agi.meta_cognition import MetaCognition` | `from moss.core.meta_cognition import MetaCognition` |
| `from agi.safety.alignment import ...` | `from moss.core.safety.alignment import ...` |
| `from agi.analysis.effect_size import ...` | `from moss.core.analysis.effect_size import ...` |
| `from agi.ecology.world import ...` | `from moss.core.ecology.world import ...` |
| `from agi.learning.lifelong import ...` | `from moss.core.learning.lifelong import ...` |
| `from agi.representation.autoencoder import ...` | `from moss.core.representation.autoencoder import ...` |

## 批量替换

```bash
# 一次性替换所有导入
find . -name "*.py" -type f -exec sed -i 's/from agi\./from moss.core./g' {} \;
find . -name "*.py" -type f -exec sed -i 's/import agi\./import moss.core./g' {} \;
```

## 兼容层行为

现有的 `from agi import X` 仍然有效，但会触发：

```
DeprecationWarning: Importing 'X' from 'agi' is deprecated.
Use 'from moss.core import X' instead.
This compatibility layer will be removed in v10.0.
```

## 时间线

- **v9.6.0**: `agi/` 兼容层可用，发出 DeprecationWarning
- **v10.0**: 计划移除 `agi/` 兼容层（至少保留 2 个版本周期）
