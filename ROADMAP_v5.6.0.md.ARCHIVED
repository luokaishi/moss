# MOSS v5.6.0 路线图

**版本**: 5.6.0  
**目标**: 突破涌现权重瓶颈，实现真正的涌现竞争机制  
**时间**: 2026-04-17 至 2026-05-08 (3周)  
**状态**: 🚧 规划中

---

## 背景

v5.5.2 完成了所有 P0 任务，但 P1-4 涌现效用优化未达标：
- **当前权重**: 0.168 (17%)
- **目标权重**: 0.20 (20%)
- **核心问题**: survival 驱动自适应增长过强，挤压涌现驱动空间

---

## 目标

### 主要目标
1. **突破 0.20 权重瓶颈** - 让涌现驱动占比达到 20%+
2. **实现驱动竞争机制** - 优胜劣汰，自适应调整权重
3. **提升涌现质量** - 从单终端函数到复合函数

### 次要目标
4. **长期稳定性** - 验证 50,000+ 周期涌现持续存在
5. **因果干预验证** - 证明涌现是因果的而非相关的

---

## 技术方案

### 方案一: 权重上限机制 (推荐首选)

**问题**: survival 驱动无论初始权重多低，最终都增长到 38%+

**解决方案**:
```python
# 驱动权重上限配置
DRIVE_WEIGHT_CAPS = {
    'survival': 0.30,      # 生存驱动上限 30%
    'optimization': 0.25,  # 优化驱动上限 25%
    'influence': 0.20,     # 影响驱动上限 20%
    'curiosity': 0.15,     # 好奇驱动上限 15%
    'emergent': 0.35,      # 涌现驱动上限 35% (鼓励涌现)
}

# 动态调整
if weight > cap:
    weight = cap + (weight - cap) * 0.1  # 软上限，允许轻微超出
```

**预期效果**:
- survival 被限制在 30%，释放 8% 空间
- 涌现驱动可占据 20-25%
- 实现目标: 0.20+ 权重

**工作量**: 低 (~50行)
**风险**: 低
**验证**: 5,000 周期实验

---

### 方案二: 驱动竞争机制

**问题**: 当前驱动权重固定，无竞争淘汰

**解决方案**:
```python
class DriveCompetition:
    """驱动竞争管理器"""
    
    def __init__(self):
        self.probation_period = 500  # 试用期周期
        self.performance_window = 100  # 性能评估窗口
        self.min_weight = 0.02  # 最小权重（低于则淘汰）
        self.max_weight = 0.35  # 最大权重
    
    def evaluate_drive(self, drive, performance_history):
        """评估驱动性能"""
        avg_reward = np.mean(performance_history)
        
        if drive.age < self.probation_period:
            # 试用期：权重缓慢增长
            drive.weight = min(drive.weight * 1.01, 0.10)
        else:
            # 正式期：根据表现调整
            if avg_reward < 0.3:
                drive.weight *= 0.95  # 衰减
            elif avg_reward > 0.7:
                drive.weight = min(drive.weight * 1.05, self.max_weight)  # 增长
        
        # 淘汰机制
        if drive.weight < self.min_weight:
            return 'eliminate'
        
        return 'keep'
```

**关键机制**:
1. **试用期**: 新驱动从 0.05 开始，500周期内缓慢增长
2. **表现评估**: 基于平均奖励调整权重
3. **淘汰机制**: 权重低于 0.02 的驱动被移除
4. **上限保护**: 单一驱动不超过 35%

**预期效果**:
- 劣质驱动自然淘汰
- 优质涌现驱动获得更多权重
- 系统自适应平衡

**工作量**: 中 (~150行)
**风险**: 中 (需仔细调参)
**验证**: 10,000 周期实验

---

### 方案三: GP质量强化

**问题**: 当前 GP 发现的函数过于简单（单终端）

**解决方案** (基于 `emergence_next_steps.md` Direction A):

```python
# 1. 增加种群和代数
POPULATION_SIZE = 200  # 原为100
GENERATIONS = 100      # 原为50

# 2. 惩罚单终端函数
if tree.node_count() == 1 and tree.is_terminal():
    fitness -= 0.5  # 显著惩罚

# 3. 要求最小行为增益
if behavioral_gain < 0.1:
    return None  # 拒绝

# 4. 调整适应度权重
fitness = (
    0.2 * correlation +
    0.1 * (1 - mse) +
    0.5 * behavioral_gain +  # 行为增益权重最高
    0.2 * complexity_bonus   # 奖励适度复杂
)
```

**预期效果**:
- 发现复合函数如 `sigmoid(mul(entropy, file_count))`
- 行为增益 > 0.1
- 涌现驱动质量提升，自然获得更高权重

**工作量**: 中 (~100行)
**风险**: 中 (可能增加计算开销)
**验证**: 2,000 周期实验

---

### 方案四: MLP替代GP (备选)

**问题**: GP 表达能力有限，难以发现复杂模式

**解决方案** (基于 `proposal_gp_emergence.md` Direction D):

```python
import numpy as np

class MLPDriveGenerator:
    """使用MLP替代GP生成涌现驱动"""
    
    def __init__(self, input_dim=8, hidden_dim=16):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        
    def evolve(self, states, labels):
        """训练小型MLP"""
        # 初始化权重
        W1 = np.random.randn(self.input_dim, self.hidden_dim) * 0.1
        b1 = np.zeros(self.hidden_dim)
        W2 = np.random.randn(self.hidden_dim, 1) * 0.1
        b2 = np.zeros(1)
        
        # 简单梯度下降
        for epoch in range(1000):
            # 前向传播
            h = np.tanh(states @ W1 + b1)
            pred = sigmoid(h @ W2 + b2)
            
            # 损失：行为增益
            loss = -behavioral_gain(pred, labels)
            
            # 反向传播
            # ... (简化)
        
        return MLPFunction(W1, b1, W2, b2)
```

**优势**:
- 更强的函数逼近能力
- 可学习非线性模式
- 可能发现GP无法表达的函数

**劣势**:
- 可解释性降低
- 计算开销增加
- 难以验证科学假设

**工作量**: 高 (~300行)
**风险**: 高
**验证**: 5,000 周期实验
**决策**: 仅当前三个方案无效时考虑

---

## 实施计划

### 第1周 (4/17 - 4/23): 方案一 + 方案二

**Day 1-2: 权重上限机制**
- [ ] 实现 `DRIVE_WEIGHT_CAPS` 配置
- [ ] 修改权重更新逻辑
- [ ] 快速测试 (1,000周期)

**Day 3-4: 驱动竞争机制**
- [ ] 实现 `DriveCompetition` 类
- [ ] 集成试用期、淘汰机制
- [ ] 快速测试 (1,000周期)

**Day 5-7: 组合验证**
- [ ] 5,000周期实验
- [ ] 分析涌现权重变化
- [ ] 调参优化

**里程碑**: 涌现权重达到 0.18+

---

### 第2周 (4/24 - 4/30): 方案三 + 验证

**Day 8-10: GP质量强化**
- [ ] 增加种群/代数
- [ ] 实现单终端惩罚
- [ ] 调整适应度权重
- [ ] 快速测试 (500周期)

**Day 11-14: 长周期验证**
- [ ] 10,000周期实验
- [ ] 跟踪涌现事件数量
- [ ] 分析涌现驱动生存率

**里程碑**: 涌现权重达到 0.20+

---

### 第3周 (5/1 - 5/8): 优化 + 文档

**Day 15-17: 因果干预实验**
- [ ] 驱动消融实验
- [ ] 行为限制实验
- [ ] 证明因果性

**Day 18-21: 文档与发布**
- [ ] 撰写 v5.6.0 报告
- [ ] 更新 MOSS_Final_Report.md
- [ ] 创建 GitHub Release

**里程碑**: v5.6.0 正式发布

---

## 验证标准

### 成功标准

| 指标 | 目标 | 验证方式 |
|------|------|---------|
| 涌现权重 | ≥ 0.20 | 10,000周期实验 |
| 涌现稳定性 | 持续5,000+周期 | 检查点分析 |
| 驱动竞争 | 至少1次淘汰事件 | 日志分析 |
| 复合函数 | ≥ 50% 复合函数 | GP结构分析 |
| 因果验证 | p < 0.05 | 统计检验 |

### 失败回退

如果方案一+二+三组合后仍未达标:
1. **分析原因**: 是survival太强还是涌现太弱？
2. **尝试方案四**: MLP替代GP
3. **调整目标**: 将0.20目标调整为0.18

---

## 风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 权重上限导致系统不稳定 | 低 | 高 | 软上限机制，允许轻微超出 |
| 竞争机制过度淘汰 | 中 | 中 | 保守参数，最小权重0.02 |
| GP强化后计算过慢 | 中 | 低 | 异步进化，不阻塞主循环 |
| 三周无法完成 | 低 | 中 | 优先方案一+二，方案三可选 |

---

## 文件清单

### 新建文件
- `agi/drive_competition.py` - 驱动竞争管理器
- `ROADMAP_v5.6.0.md` - 本路线图
- `RELEASE_v5.6.0.md` - 发布说明

### 修改文件
- `agi/agent.py` - 集成权重上限
- `agi/drive_manager.py` - 集成竞争机制
- `agi/genetic_programmer.py` - GP质量强化

---

## 总结

v5.6.0 核心策略:
1. **限制强者** (survival上限)
2. **扶持弱者** (涌现驱动保护)
3. **优胜劣汰** (竞争机制)
4. **质量提升** (GP强化)

**预期结果**: 涌现权重突破 0.20，实现真正的涌现竞争！

---

**创建日期**: 2026-04-17  
**维护者**: MOSS Team
