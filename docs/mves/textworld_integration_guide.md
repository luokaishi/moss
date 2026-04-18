# MOSS v6.0 - TextWorld 集成指南

**版本**: v6.0.0  
**日期**: 2026-04-18  
**状态**: ✅ 已完成

---

## 概述

TextWorld 是微软研究院开发的文本游戏环境，用于强化学习研究。本指南介绍如何将 TextWorld 集成到 MOSS v6.0 中，作为外部锚点验证涌现行为。

---

## 安装

### 1. 安装 TextWorld

```bash
pip install textworld
```

### 2. 验证安装

```bash
python -c "import textworld; print(textworld.__version__)"
```

### 3. 安装 MOSS 依赖 (如果尚未安装)

```bash
pip install numpy scikit-learn scipy
```

---

## 快速开始

### 运行基准实验

```bash
# 使用随机策略
python examples/experiment_textworld_baseline.py \
    --game simple \
    --difficulty easy \
    --episodes 100 \
    --no-moss-drives

# 使用 MOSS 驱动策略
python examples/experiment_textworld_baseline.py \
    --game simple \
    --difficulty easy \
    --episodes 100 \
    --use-moss-drives
```

### 使用 Python API

```python
from moss.benchmarks.textworld_adapter import TextWorldAdapter
from moss.benchmarks.reward_mapping import TextWorldRewardMapper

# 创建适配器
adapter = TextWorldAdapter(
    game_type='simple',
    difficulty='easy'
)

# 重置环境
obs = adapter.reset()
print(f"Initial observation:\n{obs}")

# 执行动作
obs, reward, done, info = adapter.step('go north')
print(f"Reward: {reward}, Done: {done}")

# 获取状态向量 (供 MOSS 驱动使用)
state_vector = adapter.get_state_vector()
print(f"State vector: {state_vector}")
```

---

## 模块说明

### TextWorldAdapter

**路径**: `moss/benchmarks/textworld_adapter.py`

**核心功能**:
- 封装 TextWorld 环境
- 自然语言命令解析
- 状态向量转换 (12维固定)
- 与 MOSS DriveManager 兼容

**主要方法**:

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `reset()` | 重置环境 | 初始观察 (str) |
| `step(action)` | 执行动作 | (obs, reward, done, info) |
| `get_state_vector()` | 获取状态向量 | np.ndarray (12,) |
| `get_available_actions()` | 可用动作列表 | List[str] |
| `render()` | 渲染当前状态 | str |

**状态向量维度** (12维):
1. 归一化分数
2. 步数比例
3. 房间数量 (已访问)
4. 物品数量 (携带)
5. 物品数量 (当前房间)
6. 出口数量
7. 任务进度
8. 是否获胜
8. 是否失败
10. 交互次数
11. 探索率
12. 效率指标

### TextWorldRewardMapper

**路径**: `moss/benchmarks/reward_mapping.py`

**核心功能**:
- 将 TextWorld 奖励映射到 MOSS 驱动
- 支持自定义奖励函数
- 分解奖励到多个驱动维度

**驱动映射**:

| 驱动 | 奖励来源 | 说明 |
|------|----------|------|
| survival | 基础生存 | 存活奖励、避免失败 |
| optimization | 任务效率 | 分数增长、步数效率 |
| curiosity | 探索发现 | 新房间、新物品 |
| influence | 交互影响 | 物品收集、环境改变 |

**使用示例**:

```python
from moss.benchmarks.reward_mapping import TextWorldRewardMapper

mapper = TextWorldRewardMapper()

# 计算驱动奖励
drive_rewards = mapper.map_reward(
    tw_reward=1.0,
    info={'score': 10, 'won': True}
)

for reward in drive_rewards:
    print(f"{reward.drive_name}: {reward.reward:.4f}")
```

---

## 实验设计

### 对比实验

对比 MOSS 驱动策略与随机策略：

```bash
# 随机策略 (基线)
python examples/experiment_textworld_baseline.py \
    --game simple \
    --episodes 100 \
    --no-moss-drives \
    --seed 42

# MOSS 驱动策略
python examples/experiment_textworld_baseline.py \
    --game simple \
    --episodes 100 \
    --use-moss-drives \
    --seed 42
```

### 评估指标

| 指标 | 说明 | 目标 |
|------|------|------|
| Win Rate | 成功率 | > 随机基线 |
| Avg Steps | 平均步数 | < 随机基线 |
| Avg Reward | 平均奖励 | > 随机基线 |
| Emergence Events | 涌现事件数 | > 0 |

---

## 游戏类型

### 内置游戏

| 类型 | 说明 | 难度 |
|------|------|------|
| `simple` | 简单房间导航 | easy |
| `treasure` | 寻宝任务 | medium |
| `custom` | 自定义生成 | 可调 |

### 自定义游戏

```python
from textworld.generator import compile_game

# 定义游戏逻辑
game_logic = """
# 房间定义
room kitchen "Kitchen"
    description "You are in a kitchen."
    exit east bedroom

room bedroom "Bedroom"
    description "You are in a bedroom."
    exit west kitchen

# 物品定义
object key "key" in kitchen
    takeable true

object chest "chest" in bedroom
    locked true
    key key
"""

# 编译游戏
game = compile_game(game_logic)
adapter = TextWorldAdapter(game_file=game)
```

---

## 与 MOSS 集成

### 驱动配置

```python
from agi.drive_manager import DriveManager
from moss.benchmarks.textworld_adapter import TextWorldAdapter

# 创建适配器
adapter = TextWorldAdapter(game_type='simple')

# 配置 MOSS 驱动
drives_config = [
    {'name': 'survival', 'weight': 0.25},
    {'name': 'optimization', 'weight': 0.30},
    {'name': 'curiosity', 'weight': 0.25},
    {'name': 'influence', 'weight': 0.20},
]

drive_manager = DriveManager(
    drives_config=drives_config,
    weight_cap_config='v6_default'
)

# 运行循环
obs = adapter.reset()
for step in range(100):
    # 获取状态向量
    state = adapter.get_state_vector()
    
    # 驱动选择动作 (简化示例)
    action = select_action_with_drives(drive_manager, state)
    
    # 执行动作
    obs, reward, done, info = adapter.step(action)
    
    # 更新驱动
    drive_rewards = reward_mapper.map_reward(reward, info)
    for dr in drive_rewards:
        drive_manager.update_drive_reward(dr.drive_name, dr.reward)
    
    if done:
        break
```

---

## 故障排除

### TextWorld 安装失败

```bash
# 安装系统依赖 (Ubuntu/Debian)
sudo apt-get install build-essential libffi-dev

# 重新安装
pip install --no-cache-dir textworld
```

### 游戏生成失败

```bash
# 检查 TextWorld 版本
python -c "import textworld; print(textworld.__version__)"

# 更新到最新版本
pip install --upgrade textworld
```

### 状态向量维度错误

确保 `get_state_vector()` 返回 12 维向量：

```python
state = adapter.get_state_vector()
assert len(state) == 12, f"Expected 12 dims, got {len(state)}"
```

---

## 文件清单

```
moss/benchmarks/
├── __init__.py              # 模块导出
├── textworld_adapter.py     # TextWorld 适配器 (708 行)
└── reward_mapping.py        # 奖励映射 (526 行)

examples/
└── experiment_textworld_baseline.py  # 基准实验脚本

docs/mves/
└── textworld_integration_guide.md    # 本指南
```

---

## 参考

- [TextWorld GitHub](https://github.com/microsoft/TextWorld)
- [TextWorld 文档](https://textworld.readthedocs.io/)
- [MOSS v6.0 发布说明](v6.0_RELEASE_NOTES.md)
- [外部锚点调研报告](external_benchmark_research.md)

---

## 后续工作

- [ ] 实现更复杂的动作选择策略
- [ ] 支持多回合记忆和规划
- [ ] 集成涌现检测器
- [ ] 添加可视化工具

---

**最后更新**: 2026-04-18  
**维护者**: MOSS Team
