# MOSS v6.0 - 外部锚点 Benchmark 调研报告

**调研目标**: 为 MOSS 系统寻找合适的外部验证 Benchmark，用于评估涌现行为、推理能力和泛化性能。

---

## 1. TextWorld (Microsoft)

### 1.1 核心特点

TextWorld 是微软研究院开发的文本游戏环境，用于强化学习研究。

| 属性 | 描述 |
|------|------|
| **类型** | 文本交互式环境 |
| **观察空间** | 自然语言描述 |
| **动作空间** | 文本命令 (如 "take key", "open door") |
| **任务类型** | 解谜、探索、物品收集 |
| **生成方式** | 程序化生成游戏世界 |
| **难度等级** | 可调节 (从简单房间到复杂迷宫) |

**核心机制**:
- 基于文本的观察 (房间描述、物品状态)
- 自然语言动作空间
- 部分可观察马尔可夫决策过程 (POMDP)
- 支持自定义游戏生成

### 1.2 与 MOSS 的适配性分析

| 维度 | MOSS 特性 | TextWorld 特性 | 适配度 |
|------|-----------|----------------|--------|
| **环境接口** | Shell 命令执行 | 文本命令输入 | ⭐⭐⭐⭐⭐ 高度匹配 |
| **观察类型** | 命令输出 (文本) | 房间描述 (文本) | ⭐⭐⭐⭐⭐ 高度匹配 |
| **动作空间** | Shell 命令 | 游戏命令 | ⭐⭐⭐⭐ 良好匹配 |
| **涌现验证** | 驱动涌现 | 策略涌现 | ⭐⭐⭐⭐ 良好匹配 |
| **推理需求** | 环境推理 | 谜题推理 | ⭐⭐⭐⭐⭐ 高度匹配 |

**适配优势**:
1. **接口相似性**: MOSS 的 Shell 环境与 TextWorld 的文本命令接口高度相似
2. **推理能力测试**: 解谜任务可测试 MOSS 的规划与推理能力
3. **涌现行为观察**: 复杂任务中可能观察到策略涌现
4. **可扩展性**: 支持从简单到复杂的任务梯度

### 1.3 集成方案

```python
# 概念性集成示例
from textworld import Env

class MOSS_TextWorld_Interface:
    """MOSS 与 TextWorld 的接口适配器"""
    
    def __init__(self, game_file):
        self.env = Env(game_file)
        self.observation = None
    
    def execute_action(self, command: str) -> str:
        """执行命令并返回观察"""
        # MOSS 的 shell 动作映射到 TextWorld 命令
        obs, reward, done, info = self.env.step(command)
        return obs
    
    def get_state_for_moss(self) -> dict:
        """将 TextWorld 状态转换为 MOSS 可理解的格式"""
        return {
            'observation': self.observation,
            'inventory': self.env.inventory,
            'location': self.env.location,
            'score': self.env.score,
        }
```

**集成步骤**:
1. 安装 TextWorld: `pip install textworld`
2. 创建 MOSS 适配器类，封装 TextWorld 环境
3. 将 TextWorld 观察映射为 MOSS 的 "shell 输出"
4. 将 MOSS 的动作映射为 TextWorld 命令
5. 设计奖励函数，与 MOSS 的驱动系统对接

### 1.4 实现难度评估

| 方面 | 难度 | 说明 |
|------|------|------|
| **安装配置** | 低 | pip 安装，依赖清晰 |
| **接口适配** | 低 | 文本接口天然匹配 |
| **状态映射** | 中 | 需要解析 TextWorld 输出 |
| **奖励设计** | 中 | 需要将游戏分数映射到驱动 |
| **涌现验证** | 中 | 需要设计复杂任务观察涌现 |

**总体难度**: ⭐⭐⭐ 中等偏低

---

## 2. BabyAI (Mila)

### 2.1 核心特点

BabyAI 是 Mila (Montreal Institute for Learning Algorithms) 开发的网格世界导航任务集合，专为测试 Agent 的指令跟随和探索能力设计。

| 属性 | 描述 |
|------|------|
| **类型** | 2D 网格世界 |
| **观察空间** | 部分可观察的网格视图 (7x7) |
| **动作空间** | 离散动作 (左转、右转、前进、拾取、放下) |
| **指令类型** | 自然语言指令 (如 "go to the red ball") |
| **难度等级** | 19 个预定义难度等级 (BabyAI-1 到 BabyAI-19) |
| **核心挑战** | 指令理解、导航、物体操作 |

**核心机制**:
- 基于网格的确定性环境
- 自然语言指令生成
- 组合任务 (需要多步推理)
- 稀疏奖励
- 可复现的基准测试

### 2.2 与 MOSS 的适配性分析

| 维度 | MOSS 特性 | BabyAI 特性 | 适配度 |
|------|-----------|-------------|--------|
| **环境接口** | Shell 文本 | 网格视觉 | ⭐⭐ 需要适配 |
| **动作空间** | 自由命令 | 离散动作 | ⭐⭐⭐ 需要映射 |
| **指令理解** | 自然语言理解 | 自然语言指令 | ⭐⭐⭐⭐⭐ 高度匹配 |
| **涌现验证** | 驱动涌现 | 策略涌现 | ⭐⭐⭐⭐ 良好匹配 |
| **探索能力** | 环境探索 | 网格探索 | ⭐⭐⭐⭐ 良好匹配 |

**适配优势**:
1. **指令跟随**: BabyAI 的自然语言指令与 MOSS 的语言理解能力匹配
2. **涌现行为**: 复杂任务中可能观察到策略涌现 (如子目标分解)
3. **难度梯度**: 19 个难度等级提供系统的测试路径
4. **社区支持**: 活跃的研究社区，丰富的基线结果

**适配挑战**:
1. **观察空间差异**: MOSS 使用文本，BabyAI 使用网格视觉
2. **动作空间差异**: 需要将 BabyAI 的离散动作映射到 MOSS 的命令

### 2.3 集成方案

```python
# 概念性集成示例
import babyai
from babyai import Bot

class MOSS_BabyAI_Interface:
    """MOSS 与 BabyAI 的接口适配器"""
    
    def __init__(self, level='BabyAI-GoToLocal-v0'):
        self.env = gym.make(level)
        self.current_mission = None
    
    def get_text_observation(self):
        """将网格观察转换为文本描述"""
        obs = self.env.gen_obs()
        # 转换为文本描述供 MOSS 理解
        return self._grid_to_text(obs)
    
    def execute_moss_action(self, action_text: str):
        """将 MOSS 的文本动作转换为 BabyAI 动作"""
        action_map = {
            'turn left': self.env.actions.left,
            'turn right': self.env.actions.right,
            'move forward': self.env.actions.forward,
            'pick up': self.env.actions.pickup,
            'drop': self.env.actions.drop,
        }
        action = action_map.get(action_text.lower())
        if action:
            return self.env.step(action)
        return None
    
    def _grid_to_text(self, obs) -> str:
        """将网格观察转换为自然语言描述"""
        # 生成类似 "You see a red ball to your left" 的描述
        pass
```

**集成步骤**:
1. 安装 BabyAI: `pip install babyai`
2. 创建观察转换器 (网格 → 文本)
3. 创建动作映射器 (MOSS 命令 → BabyAI 动作)
4. 实现奖励转换 (环境奖励 → 驱动信号)
5. 从 BabyAI-1 开始逐步测试

### 2.4 实现难度评估

| 方面 | 难度 | 说明 |
|------|------|------|
| **安装配置** | 低 | pip 安装 |
| **观察转换** | 中 | 网格到文本需要额外工作 |
| **动作映射** | 低 | 动作空间小，映射简单 |
| **涌现验证** | 高 | 需要复杂任务才可能涌现 |
| **难度等级** | 低 | 19 个预定义等级 |

**总体难度**: ⭐⭐⭐⭐ 中等偏高

---

## 3. Procgen (OpenAI)

### 3.1 核心特点

Procgen 是 OpenAI 开发的程序化生成环境集合，包含 16 种不同的游戏，专门用于测试强化学习 Agent 的泛化能力。

| 属性 | 描述 |
|------|------|
| **游戏数量** | 16 种不同游戏 |
| **观察空间** | 64x64 RGB 图像 |
| **动作空间** | 离散动作 (通常 15 个) |
| **生成方式** | 程序化生成关卡 |
| **核心挑战** | 泛化能力 (训练集 vs 测试集) |
| **难度模式** | 简单 (easy) / 困难 (hard) |

**游戏列表**:
1. **CoinRun** - 跑酷收集金币
2. **StarPilot** - 太空射击
3. **CaveFlyer** - 洞穴飞行
4. **Dodgeball** - 躲避球
5. **FruitBot** - 水果收集
6. **Chaser** - 追逐
7. **Miner** - 采矿
8. **Jumper** - 跳跃
9. **Leaper** - 飞跃
10. **Maze** - 迷宫
11. **Heist** - 盗窃
12. **Climber** - 攀爬
13. **Plunder** - 掠夺
14. **CoinRun-Old** - 旧版跑酷
15. **BigFish** - 大鱼吃小鱼
16. **BossFight** - Boss 战

### 3.2 与 MOSS 的适配性分析

| 维度 | MOSS 特性 | Procgen 特性 | 适配度 |
|------|-----------|--------------|--------|
| **环境接口** | Shell 文本 | 图像输入 | ⭐ 需要大量适配 |
| **动作空间** | 自由命令 | 离散动作 | ⭐⭐⭐ 需要映射 |
| **观察类型** | 文本 | 图像 | ⭐ 需要视觉模块 |
| **泛化测试** | 环境适应 | 关卡泛化 | ⭐⭐⭐⭐ 概念匹配 |
| **涌现验证** | 驱动涌现 | 策略涌现 | ⭐⭐⭐ 可能匹配 |

**适配优势**:
1. **泛化能力测试**: Procgen 的核心目标是测试泛化，与 MOSS 的环境适应能力测试目标一致
2. **多样化任务**: 16 种游戏提供丰富的测试场景
3. **程序化生成**: 无限关卡生成，避免过拟合

**适配挑战**:
1. **视觉输入**: MOSS 当前为文本环境，需要添加视觉处理模块
2. **动作映射**: 离散动作空间与 MOSS 的自由命令差异大
3. **计算资源**: Procgen 需要 GPU 加速

### 3.3 集成方案

```python
# 概念性集成示例 (需要视觉模块)
import gym
import procgen

class MOSS_Procgen_Interface:
    """MOSS 与 Procgen 的接口适配器"""
    
    def __init__(self, game_name='coinrun', distribution_mode='easy'):
        self.env = gym.make(
            f'procgen:procgen-{game_name}-v0',
            distribution_mode=distribution_mode
        )
        self.vision_module = VisionModule()  # 需要实现
    
    def get_text_observation(self, obs_image):
        """将图像观察转换为文本描述"""
        # 使用 VLM 或传统 CV 方法描述图像
        return self.vision_module.describe(obs_image)
    
    def execute_moss_action(self, action_text: str):
        """将 MOSS 的意图转换为 Procgen 动作"""
        # 使用策略网络或规则映射
        action = self._text_to_action(action_text)
        return self.env.step(action)
    
    def _text_to_action(self, text: str) -> int:
        """将文本命令映射到离散动作"""
        # 例如: "move left" → 0, "jump" → 1
        pass
```

**集成步骤**:
1. 安装 Procgen: `pip install procgen`
2. 实现视觉模块 (图像 → 文本描述)
3. 实现动作策略 (MOSS 意图 → 离散动作)
4. 选择适合的游戏 (推荐: Maze, CoinRun, Heist)
5. 在 easy 模式下开始测试

### 3.4 实现难度评估

| 方面 | 难度 | 说明 |
|------|------|------|
| **安装配置** | 中 | 需要 GPU 支持 |
| **视觉模块** | 高 | 需要图像理解能力 |
| **动作映射** | 中 | 需要策略网络 |
| **计算资源** | 高 | 需要 GPU 训练 |
| **涌现验证** | 中 | 部分游戏可能涌现 |

**总体难度**: ⭐⭐⭐⭐⭐ 高

---

## 4. MiniGrid (Farama Foundation)

### 4.1 核心特点

MiniGrid 是 Farama Foundation (Gymnasium 维护者) 开发的轻量级网格世界环境，专为快速原型设计和教育用途设计。

| 属性 | 描述 |
|------|------|
| **类型** | 2D 网格世界 |
| **观察空间** | 网格编码 (7x7x3) 或 RGB 图像 |
| **动作空间** | 7 个离散动作 |
| **任务类型** | 可自定义 (导航、开门、拾取等) |
| **环境大小** | 轻量级，运行快速 |
| **依赖** | 仅需 Gymnasium + NumPy |

**核心特性**:
- 极简设计，易于理解
- 完全可自定义任务
- 支持部分可观察性
- 丰富的预定义环境
- 活跃维护，文档完善

### 4.2 与 MOSS 的适配性分析

| 维度 | MOSS 特性 | MiniGrid 特性 | 适配度 |
|------|-----------|---------------|--------|
| **环境接口** | Shell 文本 | 网格编码 | ⭐⭐⭐ 需要适配 |
| **动作空间** | 自由命令 | 7 个离散动作 | ⭐⭐⭐ 需要映射 |
| **自定义性** | 高 | 极高 | ⭐⭐⭐⭐⭐ 高度匹配 |
