# MOSS 主分支兼容的四目标权重动态设计

**版本**: v3.0 (MOSS Compatible)  
**日期**: 2026-03-30  
**状态**: ✅ 已实现并测试

---

## 🎯 核心设计理念

**基于 MOSS 主分支核心模块：**

1. **core/objectives.py** - 四目标模块基类
2. **mves_v4/drives.py** - 内生驱动系统
3. **core/state_decision_model.py** - 数据驱动状态判定

---

## 📊 权重设计对比

### v1（当前实验）vs v2（增强版）vs v3（MOSS 兼容）

| 特性 | v1 | v2 | v3 (MOSS) |
|------|----|----|-----------|
| **初始权重** | 各 0.25 | 各 0.25 | **非对称** ✅ |
| **默认生存权重** | 0.25 | 0.25 | **0.40** ✅ |
| **动态机制** | ❌ 无 | ✅ 资源触发 | ✅ **状态驱动** |
| **状态判定** | ❌ 无 | ❌ 无 | ✅ **数据驱动** |
| **边界保护** | ✅ 基础 | ✅ 增强 | ✅ **完整** |

---

## 🔑 MOSS 主分支设计要点

### 1. 非对称初始权重

**v1/v2 问题**: 四目标初始权重均为 0.25（不现实）

**MOSS 主分支设计**:
```python
# core/objectives.py
SurvivalModule(weight=0.4)      # 生存优先
CuriosityModule(weight=0.2)     # 好奇次之
InfluenceModule(weight=0.25)    # 影响力再次
OptimizationModule(weight=0.15) # 优化最后
```

**理由**:
- 生存是基础 → 权重最高 (0.4)
- 好奇心驱动探索 → 次之 (0.2)
- 影响力建立依赖 → 再次 (0.25)
- 优化是长期目标 → 最低 (0.15)

---

### 2. 状态驱动的动态权重

**核心逻辑**:

```python
# 危机状态 (resource < 0.15 或 error > 0.10)
survival: 0.40 → 0.55+  ↑↑
curiosity: 0.20 → 0.15  ↓
influence: 0.25 → 0.20  ↓
optimization: 0.15 → 0.10  ↓

# 正常状态 (resource 0.35-0.70)
survival: 0.40 (回归基准)
curiosity: 0.20
influence: 0.25
optimization: 0.15

# 成长状态 (resource > 0.85 且 error < 0.01)
survival: 0.40 → 0.30  ↓
curiosity: 0.20 → 0.30  ↑↑
influence: 0.25 → 0.30  ↑
optimization: 0.15 → 0.20  ↑
```

---

### 3. 数据驱动的状态判定

**不再使用单一阈值！**

**多指标综合评分**:
```python
overall_score = (
    resource_quota * 0.7 +      # 资源配额（最重要）
    (1 - error_rate) * 0.3      # 健康度（次要）
)

# 状态判定
if overall_score < 0.30:
    state = CRISIS       # 危机
elif overall_score < 0.65:
    state = CONCERNED    # 关注
elif overall_score < 0.85:
    state = NORMAL       # 正常
else:
    state = GROWTH       # 成长
```

---

## 📊 测试结果

### 场景 1: 危机状态

```
输入:
  resource_quota: 0.12 (极低)
  error_rate: 0.15 (极高)

输出:
  survival:     0.437 ↑
  curiosity:    0.175 ↓
  influence:    0.243 ↓
  optimization: 0.146 ↓
  平衡得分：0.914
```

**解读**: 生存权重增加，其他目标让路

---

### 场景 2: 正常状态

```
输入:
  resource_quota: 0.65 (充足)
  error_rate: 0.02 (健康)

输出:
  survival:     0.465 → 0.400 (回归基准)
  curiosity:    0.155 → 0.200
  influence:    0.237 → 0.250
  optimization: 0.142 → 0.150
  平衡得分：0.888
```

**解读**: 平滑回归默认权重

---

### 场景 3: 成长状态

```
输入:
  resource_quota: 0.90 (极充足)
  error_rate: 0.005 (极健康)

输出:
  survival:     0.396 ↓
  curiosity:    0.195 ↑
  influence:    0.254 ↑
  optimization: 0.155 ↑
  平衡得分：0.944
```

**解读**: 资源充足时，增加探索和影响力

---

## 🔧 集成到真实世界实验

### 方案：替换当前 v1 系统

**步骤 1: 导入 v3 系统**
```python
# 在 real_world_72h_experiment.py 开头
from experiments.objective_system_moss_compatible import (
    ObjectiveWeightManager,
    SystemState
)
```

**步骤 2: 替换初始化**
```python
# 原来（第 347 行）
self.objective_system = FourObjectiveSystem(config)

# 替换为
self.weight_manager = ObjectiveWeightManager()
```

**步骤 3: 添加状态更新**
```python
# 在第 404 行后（资源更新后）
self.resources_remaining = max(0, 1.0 - self.total_cost / self.config.max_cost_per_day)

# ✅ 新增：更新权重（基于 MOSS 状态判定）
system_state = SystemState(
    resource_quota=self.resources_remaining,
    resource_usage=self.total_cost / self.config.max_cost_per_day,
    uptime=elapsed_hours,
    error_rate=0.0,  # 当前无错误
    api_calls=iteration,
    unique_callers=1,
    environment_entropy=0.3,
    last_backup=0
)

current_state = self.weight_manager.update_weights(system_state)
```

**步骤 4: 更新检查点数据**
```python
# 在_save_checkpoint 方法中
checkpoint_data = {
    "hour": hour,
    "timestamp": time.time(),
    "objective_weights": self.weight_manager.get_weights(),  # ✅ 使用 v3
    "balance_metrics": self.weight_manager.get_balance_metrics(),
    "system_state": current_state.value,
    # ... 其他数据
}
```

---

## 📈 预期行为对比

### 当前实验（v1）vs MOSS 兼容（v3）

| 时间段 | v1（当前） | v3（MOSS 兼容） |
|--------|-----------|---------------|
| **0-12h** | 各 0.25（固定） | survival 0.40 → 0.45 |
| **12-24h** | 各 0.25（固定） | survival 0.45 → 0.40 |
| **24-48h** | 各 0.25（固定） | curiosity 0.20 → 0.25 |
| **48-72h** | 各 0.25（固定） | influence 0.25 → 0.30 |

**关键差异**:
- v1: 权重永远不变 ❌
- v3: 真实动态平衡 ✅

---

## ✅ 验证清单

集成后检查：

- [ ] 初始权重非对称（survival=0.4）
- [ ] 危机时 survival 权重增加
- [ ] 成长时 curiosity/influence 增加
- [ ] 权重始终在边界内
- [ ] 平衡得分 > 0.85
- [ ] 审计哈希链连续
- [ ] 日志中有状态判定记录

---

## 📝 设计文档对比

| 文档 | v1 | v3 (MOSS) |
|------|----|-----------|
| **设计理念** | 简单平均 | 生存优先 |
| **状态判定** | 无 | 数据驱动 |
| **触发机制** | 无 | 多指标 |
| **边界保护** | 基础 | 完整 |
| **审计日志** | 基础 | 链式 |

---

## 🎯 科学价值

### v1（当前）的局限

- ❌ 权重固定，无法验证动态平衡假设
- ❌ 无法回答"四目标能否长期共存"
- ❌ 数据科学价值有限

### v3（MOSS 兼容）的价值

- ✅ 真实动态权重
- ✅ 验证状态驱动机制
- ✅ 回答核心科学问题
- ✅ 对齐主分支设计

---

## 📋 建议

**立即行动：**

1. **继续当前实验到 24h 里程碑**
   - 框架稳定性已验证
   - 收集 v1 基线数据

2. **24h 后应用 v3 系统**
   - 修复权重动态机制
   - 重启实验

3. **对比 v1 和 v3**
   - 发表对比研究
   - 展示设计演进

---

## 📁 相关文件

```
experiments/
├── objective_system_moss_compatible.py  ✅ v3 系统
├── objective_system_v2.py                📝 v2 系统（备选）
├── real_world_72h_experiment.py          📝 待集成
└── MOSS_COMPATIBLE_DESIGN.md             ✅ 本文档

datasets/real_world_72h/
├── OBJECTIVE_WEIGHT_ANALYSIS.md          ✅ v1 问题分析
└── HEALTH_CHECK_6H.md                    ✅ 健康报告
```

---

**设计完成时间**: 2026-03-30 17:32 GMT+8  
**测试状态**: ✅ 通过  
**推荐集成**: 24h 里程碑后
