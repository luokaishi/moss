# MOSS 分支合并策略

**版本**: 1.0  
**日期**: 2026-04-25  
**目标**: 将 MVES v8.6 合并到 Main，构建统一的 v9.0 架构

---

## 战略概述

### 合并原则

1. **统一命名空间**: 最终使用 `moss/core/` 作为唯一核心命名空间
2. **功能优先**: 保留两个分支的最佳功能，不丢弃任何有用代码
3. **向后兼容**: 提供 `agi/` 兼容层，确保现有脚本可运行
4. **分阶段执行**: 按优先级分阶段合并，降低风险

### 合并目标

```
当前状态:
  main (v9.5): moss/core/ (50个文件) + agi/ (部分)
  mves (v8.6): agi/ (45个文件)

目标状态:
  unified (v9.0): moss/core/ (75个文件，合并后)
                   agi/ (兼容层，软链接或导入别名)
```

---

## 阶段规划

### Phase 1: P0 核心组件合并 (Day 1-2)

**目标**: 合并最核心的 GP 和驱动力系统

```bash
# 创建合并分支
git checkout main
git checkout -b merge/mves-p0-core

# 1. GP 系统 (MVES 更完整)
cp agi/genetic_programmer.py moss/core/
cp agi/genetic_programmer_v2.py moss/core/
cp agi/genetic_programmer_v3.py moss/core/
git add moss/core/genetic_programmer*.py
git commit -m "merge: GP system from mves v8.6

- genetic_programmer.py: Base GP implementation
- genetic_programmer_v2.py: Enhanced version
- genetic_programmer_v3.py: Latest improvements
- Source: agi/ (mves branch)"

# 2. 驱动力系统 (MVES 更完整)
cp agi/drive_manager.py moss/core/
cp agi/drive_competition.py moss/core/
cp agi/drive_weight_cap.py moss/core/
git add moss/core/drive_*.py
git commit -m "merge: Drive system from mves v8.6

- drive_manager.py: Drive management
- drive_competition.py: Drive competition mechanism
- drive_weight_cap.py: Weight capping
- Source: agi/ (mves branch)"

# 3. 环境系统 (MVES 更完整)
cp agi/environment.py moss/core/
cp agi/environment_v2.py moss/core/
git add moss/core/environment*.py
git commit -m "merge: Environment system from mves v8.6

- environment.py: Base environment
- environment_v2.py: Enhanced environment
- Source: agi/ (mves branch)"

# 4. Agent 基类 (需要整合)
cp agi/agent.py moss/core/agi_agent.py  # 重命名避免冲突
git add moss/core/agi_agent.py
git commit -m "merge: AGI Agent base from mves v8.6

- agi_agent.py: Base AGI Agent implementation
- Note: Will be integrated with agent_bridge.py in Phase 2
- Source: agi/agent.py (mves branch)"

# 运行测试
python -c "from moss.core.genetic_programmer import GeneticProgrammer; print('GP OK')"
python -c "from moss.core.drive_manager import DriveManager; print('Drive OK')"
python -c "from moss.core.environment import RealEnvironment; print('Env OK')"
```

**产出**:
- 4 个 commit
- 9 个新文件
- 核心功能测试通过

---

### Phase 2: P1 重要组件合并 (Day 3-5)

**目标**: 合并 Agent 系统、多 Agent、任务感知等

```bash
# 创建 Phase 2 分支
git checkout -b merge/mves-p1-agent

# 1. 多 Agent 系统
cp agi/multi_agent_coordinator.py moss/core/
cp -r agi/multi_agent/ moss/core/
git add moss/core/multi_agent_coordinator.py moss/core/multi_agent/
git commit -m "merge: Multi-Agent system from mves v8.6

- multi_agent_coordinator.py: Agent coordination
- multi_agent/: Multi-agent components
- Source: agi/ (mves branch)"

# 2. 任务感知 Agent
cp agi/task_aware_agent.py moss/core/
cp agi/task_discovery.py moss/core/
cp agi/task_scenarios.py moss/core/
git add moss/core/task_*.py
git commit -m "merge: Task-Aware Agent from mves v8.6

- task_aware_agent.py: Task-aware agent implementation
- task_discovery.py: Task discovery mechanism
- task_scenarios.py: Task scenario definitions
- Source: agi/ (mves branch)"

# 3. LLM 集成 (补充功能)
cp agi/llm_integration.py moss/core/llm_integration_mves.py
git add moss/core/llm_integration_mves.py
git commit -m "merge: LLM integration from mves v8.6

- llm_integration_mves.py: Additional LLM integration features
- Note: Complements existing llm_backend.py
- Source: agi/llm_integration.py (mves branch)"

# 4. 记忆引擎
cp agi/memory_engine.py moss/core/
git add moss/core/memory_engine.py
git commit -m "merge: Memory engine from mves v8.6

- memory_engine.py: Agent memory management
- Source: agi/ (mves branch)"

# 5. 自适应动作选择
cp agi/adaptive_action_selector.py moss/core/
git add moss/core/adaptive_action_selector.py
git commit -m "merge: Adaptive action selector from mves v8.6

- adaptive_action_selector.py: 9-dim action selection
- Source: agi/ (mves branch)"

# 运行集成测试
python -m pytest tests/test_multi_agent.py -v || echo "Tests may need updates"
```

**产出**:
- 5 个 commit
- ~10 个新文件
- Agent 系统功能增强

---

### Phase 3: Agent 系统整合 (Day 6-7)

**目标**: 整合 moss/core/agent_bridge.py 和 moss/core/agi_agent.py

```python
# moss/core/unified_agent.py
"""
统一 Agent 抽象层

整合:
- agent_bridge.py (v9 架构)
- agi_agent.py (v8.6 实现)
"""

from typing import Optional, Dict, Any
from .agent_bridge import AgentBridge  # v9
from .agi_agent import AGIAgent  # v8.6


class UnifiedAgent:
    """
    统一 Agent 类

    结合 v9 的架构抽象和 v8.6 的具体实现
    """

    def __init__(self, agent_id: str, config: Optional[Dict] = None):
        self.agent_id = agent_id
        self.config = config or {}

        # v9 架构组件
        self.bridge = AgentBridge(agent_id)

        # v8.6 实现组件
        self.agi = AGIAgent(agent_id, config)

    def act(self, observation: Any) -> Any:
        """统一动作接口"""
        # 使用 v8.6 的实现
        return self.agi.act(observation)

    def learn(self, experience: Any) -> None:
        """统一学习接口"""
        # 使用 v8.6 的实现
        self.agi.learn(experience)

    def get_status(self) -> Dict[str, Any]:
        """统一状态接口"""
        return {
            'agent_id': self.agent_id,
            'bridge_status': self.bridge.get_status(),
            'agi_status': self.agi.get_status(),
        }
```

```bash
git add moss/core/unified_agent.py
git commit -m "feat: Unified Agent abstraction (v9.0)

- Integrates agent_bridge.py (v9) and agi_agent.py (v8.6)
- Provides backward-compatible interface
- Enables gradual migration"
```

---

### Phase 4: P2 辅助组件合并 (Week 2)

**目标**: 合并元学习、监控、优化等辅助组件

```bash
# 元学习系统
cp agi/meta_learner.py moss/core/
cp agi/meta_sme.py moss/core/
cp agi/meta_sme_v2.py moss/core/
cp agi/meta_sme_integration.py moss/core/
cp agi/meta_sme_optimizer.py moss/core/

# 其他组件
cp agi/behavior_tracker.py moss/core/
cp agi/emergence_detector.py moss/core/
cp agi/intervention_validator.py moss/core/
cp agi/performance_optimizer.py moss/core/
# ... etc
```

---

### Phase 5: 清理与重构 (Week 3)

**目标**: 统一导入路径，删除重复代码

```bash
# 1. 创建 agi/ 兼容层
cat > agi/__init__.py << 'EOF'
"""
AGI 兼容层

重定向到 moss.core
"""
import warnings
warnings.warn(
    "agi module is deprecated, use moss.core instead",
    DeprecationWarning,
    stacklevel=2
)

# 重定向所有导入
from moss.core import *
EOF

# 2. 批量更新导入语句 (示例)
find . -name "*.py" -type f -exec sed -i 's/from agi import/from moss.core import/g' {} \;
find . -name "*.py" -type f -exec sed -i 's/from agi\./from moss.core./g' {} \;

# 3. 测试所有导入
python -c "
import moss.core
from moss.core import unified_agent
from moss.core import genetic_programmer
from moss.core import drive_manager
print('All imports OK')
"

# 4. 删除 agi/ 目录 (可选，保留兼容层)
# rm -rf agi/
```

---

## 合并检查清单

### 每个 Phase 的检查项

- [ ] 文件复制完成
- [ ] 导入测试通过
- [ ] 功能测试通过
- [ ] 文档更新
- [ ] Commit message 规范
- [ ] 代码审查

### 最终检查项

- [ ] 所有 P0/P1 组件已合并
- [ ] 统一 Agent 抽象可用
- [ ] 向后兼容层工作正常
- [ ] 所有测试通过
- [ ] 文档已更新
- [ ] CHANGELOG 已更新

---

## 风险缓解

| 风险 | 缓解措施 |
|------|----------|
| 导入循环 | 使用延迟导入 (lazy import) |
| 命名冲突 | 重命名冲突文件 (如 xxx_mves.py) |
| 功能重复 | 保留两者，标记弃用，逐步迁移 |
| 测试失败 | 每个 Phase 后运行测试，及时修复 |

---

## 时间线

| 阶段 | 时间 | 产出 |
|------|------|------|
| Phase 1 | Day 1-2 | P0 核心组件 (9个文件) |
| Phase 2 | Day 3-5 | P1 重要组件 (~10个文件) |
| Phase 3 | Day 6-7 | Agent 系统整合 |
| Phase 4 | Week 2 | P2 辅助组件 |
| Phase 5 | Week 3 | 清理重构 |

---

## 立即执行

```bash
# 开始 Phase 1
cd /workspace/moss
git checkout main
git checkout -b merge/mves-p0-core-$(date +%Y%m%d)

# 执行 Phase 1 脚本...
```

---

*策略版本: 1.0*  
*基于: CONFLICT_LIST.md + ARCHITECTURE_DIFFERENCE_REPORT.md*
