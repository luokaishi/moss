# v6.0 驱动竞争机制实现文档

**日期**: 2026-04-17  
**状态**: ✅ 已完成  
**测试**: 20 个单元测试全部通过  

---

## 概述

基于 Copilot 评估报告的建议，实现了驱动力竞争机制，实现优胜劣汰的自然选择：

**核心目标**:
- 试用期机制：新驱动从低权重开始验证
- 表现评估：基于历史表现动态调整权重
- 淘汰机制：长期表现不佳的驱动被移除
- 竞争平衡：防止单一驱动垄断

---

## 实现文件

| 文件 | 路径 | 说明 |
|------|------|------|
| 核心实现 | `agi/drive_competition.py` | 竞争机制管理器 |
| 单元测试 | `tests/test_drive_competition.py` | 20 个测试用例 |

---

## 核心组件

### 1. DriveStatus (枚举)

驱动状态定义：

```python
class DriveStatus(Enum):
    PROBATION = "probation"      # 试用期
    ACTIVE = "active"            # 正式期
    AT_RISK = "at_risk"          # 风险期
    ELIMINATED = "eliminated"    # 已淘汰
```

### 2. DrivePerformance

驱动表现记录类：

```python
@dataclass
class DrivePerformance:
    drive_name: str
    age: int = 0                          # 驱动年龄
    status: DriveStatus = DriveStatus.PROBATION
    reward_history: List[float] = field(default_factory=list)
    score_history: List[float] = field(default_factory=list)
    total_rewards: float = 0.0
    avg_reward: float = 0.0
    warnings: int = 0                     # 警告次数
```

### 3. CompetitionConfig

竞争机制配置：

```python
@dataclass
class CompetitionConfig:
    probation_period: int = 500           # 试用期周期
    probation_growth_rate: float = 1.01   # 试用期增长率
    evaluation_window: int = 100          # 评估窗口
    growth_rate: float = 1.05             # 正式期增长率
    decay_rate: float = 0.95              # 衰减率
    min_weight: float = 0.02              # 最小权重
    max_weight: float = 0.35              # 最大权重
    warning_threshold: int = 3            # 警告阈值
    good_performance_threshold: float = 0.7
    poor_performance_threshold: float = 0.3
```

### 4. DriveCompetition

核心竞争逻辑：

```python
class DriveCompetition:
    def register_drive(self, name: str, is_emergent: bool = False)
    def update_performance(self, name: str, cycle: int, reward: float, score: float)
    def evaluate_drive(self, name: str, cycle: int) -> Dict:
        # 返回: {'action': 'grow'|'decay'|'eliminate'|'keep', 'factor': float, 'reason': str}
```

### 5. DriveCompetitionManager

集成到 DriveManager 的管理器：

```python
class DriveCompetitionManager:
    def update(self, cycle: int, drive_rewards: Dict[str, float])
    def evaluate_and_adjust(self, cycle: int) -> Dict[str, Dict]
    def apply_adjustments(self, adjustments: Dict, current_weights: Dict) -> Dict[str, float]
    def get_eliminated_drives(self) -> List[str]
```

---

## 使用方式

### 基础用法

```python
from agi.drive_competition import DriveCompetition, CompetitionConfig

# 创建竞争系统
config = CompetitionConfig(
    probation_period=500,
    evaluation_window=100,
    growth_rate=1.05,
    decay_rate=0.95,
)
competition = DriveCompetition(config)

# 注册驱动
competition.register_drive('survival', is_emergent=False)
competition.register_drive('new_emergent', is_emergent=True)

# 更新表现
for cycle in range(1000):
    competition.update_performance('survival', cycle, reward=0.7, score=0.6)
    
    # 每 50 周期评估一次
    if cycle > 0 and cycle % 50 == 0:
        result = competition.evaluate_drive('survival', cycle)
        print(f"Action: {result['action']}, Factor: {result['factor']}")
```

### 使用预设配置

```python
from agi.drive_competition import get_competition_preset

# 使用 v6 默认预设
config = get_competition_preset('v6_default')
competition = DriveCompetition(config)

# 可用预设
# - v6_default: 标准配置 (试用期 500)
# - v6_strict: 严格配置 (试用期 300, 警告阈值 2)
# - v6_loose: 宽松配置 (试用期 700, 警告阈值 5)
```

### 集成到 DriveManager

```python
from agi.drive_manager import DriveManager
from agi.drive_competition import DriveCompetitionManager

# 创建 DriveManager
drive_manager = DriveManager(drives_config)

# 创建竞争管理器
comp_manager = DriveCompetitionManager(drive_manager, config='v6_default')

# 在实验循环中使用
for cycle in range(10000):
    # 收集各驱动的奖励
    drive_rewards = {
        'survival': 0.7,
        'optimization': 0.6,
        'emergent': 0.8,
    }
    
    # 更新竞争系统
    comp_manager.update(cycle, drive_rewards)
    
    # 定期评估和调整
    if cycle > 0 and cycle % 50 == 0:
        adjustments = comp_manager.evaluate_and_adjust(cycle)
        
        # 应用调整
        current_weights = {name: d.weight for name, d in drive_manager.drives.items()}
        new_weights = comp_manager.apply_adjustments(adjustments, current_weights)
        
        # 更新权重
        for name, weight in new_weights.items():
            if name in drive_manager.drives:
                drive_manager.drives[name].weight = weight
        
        # 处理淘汰
        eliminated = comp_manager.get_eliminated_drives()
        for name in eliminated:
            print(f"驱动 {name} 被淘汰")
```

---

## 核心机制详解

### 1. 试用期机制

**流程**:
```
周期 0:   注册新驱动 (emergent)，状态 = PROBATION，权重 = 0.05
周期 1-500: 缓慢增长 (1% 每周期)
周期 500:   转正评估
  - 表现良好 (avg_reward >= 0.7): 转正，状态 = ACTIVE
  - 表现不佳: 警告或淘汰
```

**代码**:
```python
if perf.status == DriveStatus.PROBATION:
    if perf.age >= config.probation_period:
        # 转正评估
        if recent['avg_reward'] >= config.good_performance_threshold:
            perf.status = DriveStatus.ACTIVE
            return {'action': 'grow', 'factor': 1.05}
    else:
        # 试用期内缓慢增长
        return {'action': 'grow', 'factor': 1.01}
```

### 2. 表现评估

**评估周期**: 每 50 周期
**评估窗口**: 最近 100 周期

**评估标准**:
- **表现良好** (avg_reward >= 0.7): 增长 5%
- **表现中等** (0.3 < avg_reward < 0.7): 保持
- **表现不佳** (avg_reward <= 0.3): 衰减 5%，警告 +1

**代码**:
```python
if avg_reward >= config.good_performance_threshold:
    return {'action': 'grow', 'factor': config.growth_rate}
elif avg_reward <= config.poor_performance_threshold:
    perf.warnings += 1
    return {'action': 'decay', 'factor': config.decay_rate}
else:
    return {'action': 'keep', 'factor': 1.0}
```

### 3. 淘汰机制

**淘汰条件**:
1. 警告次数 >= 3
2. 权重 < 0.02
3. 试用期表现持续不佳

**流程**:
```
警告 1: 表现不佳，衰减权重
警告 2: 表现持续不佳，衰减权重
警告 3: 表现持续不佳，检查趋势
  - 趋势上升: 再给机会
  - 趋势下降/平稳: 淘汰
```

**代码**:
```python
if perf.warnings >= config.warning_threshold:
    if trend > 0:
        return {'action': 'decay', 'reason': '表现不佳但趋势上升'}
    else:
        perf.status = DriveStatus.ELIMINATED
        return {'action': 'eliminate', 'reason': '表现持续不佳'}
```

### 4. 趋势计算

基于最近表现计算趋势：

```python
def _calculate_trend(self, values: List[float]) -> float:
    """计算趋势 (-1 下降, 0 平稳, 1 上升)"""
    first_half = np.mean(values[:len(values)//2])
    second_half = np.mean(values[len(values)//2:])
    
    diff = second_half - first_half
    if abs(diff) < 0.05:
        return 0.0  # 平稳
    return 1.0 if diff > 0 else -1.0  # 上升或下降
```

---

## 测试覆盖

### 测试文件: `tests/test_drive_competition.py`

| 测试类 | 测试数 | 覆盖内容 |
|--------|--------|----------|
| TestCompetitionConfig | 4 | 配置默认值、预设 |
| TestDrivePerformance | 3 | 表现记录、趋势计算 |
| TestDriveCompetition | 7 | 试用期、评估、淘汰 |
| TestDriveCompetitionManager | 6 | 集成、调整、统计 |

**运行测试**:
```bash
python tests/test_drive_competition.py
```

---

## 配置预设

### v6_default (标准)

```python
probation_period=500
evaluation_window=100
growth_rate=1.05
decay_rate=0.95
warning_threshold=3
```

### v6_strict (严格)

```python
probation_period=300
evaluation_window=50
growth_rate=1.03
decay_rate=0.90
warning_threshold=2
```

### v6_loose (宽松)

```python
probation_period=700
evaluation_window=150
growth_rate=1.08
decay_rate=0.97
warning_threshold=5
```

---

## 预期效果

### 与权重上限机制配合

| 机制 | 作用 | 效果 |
|------|------|------|
| 权重上限 | 硬性限制 | survival ≤30% |
| 竞争机制 | 动态调整 | 优质驱动增长，劣质驱动衰减 |

### 预期改进

- **优质涌现驱动**: 通过试用期验证，权重持续增长至 35%
- **劣质驱动**: 及时被淘汰，释放权重空间
- **系统自适应**: 根据环境反馈自动平衡权重分布

---

## 下一步

1. **运行 10,000 周期验证实验** - 验证竞争机制效果
2. **与权重上限集成测试** - 验证两者协同工作
3. **调整参数** - 根据实验结果优化配置

---

## 参考

- Copilot 评估报告: `markDown1776415707546.md`
- v6 TODO 清单: `docs/mves/v6_todo_checklist.md`
- 权重上限实现: `docs/mves/v6