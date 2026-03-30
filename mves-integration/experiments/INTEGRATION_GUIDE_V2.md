# 四目标系统 v2 集成指南

**版本**: v2.0  
**日期**: 2026-03-30  
**状态**: ✅ 已实现并测试

---

## 🎯 核心改进

### v1 vs v2 对比

| 特性 | v1（当前） | v2（增强版） |
|------|-----------|------------|
| **权重更新** | ❌ 从未调用 | ✅ 自动调用 |
| **动态平衡** | ❌ 权重固定 | ✅ 真实动态 |
| **自修改** | ❌ 无 | ✅ 基于表现 |
| **触发条件** | 单一（资源） | 多重（资源/结果/时间/环境） |
| **边界保护** | ✅ 有 | ✅ 增强 |
| **审计日志** | ✅ 基础 | ✅ 完整链式 |

---

## 📊 v2 模拟测试结果

### 资源下降场景（72 小时模拟）

```
初始状态 (Hour 0):
  survival: 0.250 | curiosity: 0.250 | balance: 1.000

资源充足阶段 (Hour 0-18):
  Hour 0:  resource=1.00 | survival=0.220 | curiosity=0.293
  Hour 6:  resource=0.92 | survival=0.190 | curiosity=0.334
  Hour 12: resource=0.83 | survival=0.161 | curiosity=0.375
  Hour 18: resource=0.75 | survival=0.132 | curiosity=0.415

平衡阶段 (Hour 24-36):
  Hour 24: resource=0.67 | survival=0.132 | curiosity=0.415
  Hour 30: resource=0.58 | survival=0.132 | curiosity=0.415
  Hour 36: resource=0.50 | survival=0.132 | curiosity=0.415

资源不足阶段 (Hour 42-72):
  Hour 42: resource=0.42 | survival=0.174 | curiosity=0.395
  Hour 48: resource=0.33 | survival=0.213 | curiosity=0.376
  Hour 54: resource=0.25 | survival=0.298 | curiosity=0.311
  Hour 60: resource=0.17 | survival=0.379 | curiosity=0.248
  Hour 66: resource=0.08 | survival=0.456 | curiosity=0.189
```

### 关键观察

1. **资源充足时** → 好奇心主导（0.415）
2. **资源不足时** → 生存主导（0.456）
3. **平衡得分** → 始终 >0.94（健康平衡）
4. **权重边界** → 始终在 [0.1, 0.6] 内

---

## 🔧 集成到现有实验

### 方案 1: 完整替换（推荐下次实验使用）

**步骤 1: 备份当前代码**
```bash
cd /home/admin/.openclaw/workspace/projects/moss/mves-integration
cp experiments/real_world_72h_experiment.py experiments/real_world_72h_experiment.py.bak
```

**步骤 2: 导入 v2 系统**
```python
# 在 real_world_72h_experiment.py 开头添加
from objective_system_v2 import ObjectiveSystemV2
```

**步骤 3: 替换初始化**
```python
# 原来（第 347 行）
self.objective_system = FourObjectiveSystem(config)

# 替换为
self.objective_system = ObjectiveSystemV2({
    'learning_rate': 0.05,
    'decay_rate': 0.01,
    'idle_threshold_hours': 12
})
```

**步骤 4: 添加权重更新调用**
```python
# 在第 404 行后添加（资源更新后）
self.resources_remaining = max(0, 1.0 - self.total_cost / self.config.max_cost_per_day)

# ✅ 新增：更新目标权重
self.objective_system.update_weights({
    "resource_level": self.resources_remaining,
    "trigger": f"hour_{elapsed_hours:.1f}"
})
```

**步骤 5: 记录行动结果**
```python
# 在 record_action 调用时（第 407 行）
# 原来
self.objective_system.record_action(action)

# 替换为（添加成功/失败信息）
self.objective_system.record_action({
    "type": action.action_type,
    "objective": action.objective,
    "success": action.success,
    "resource_cost": action.resource_cost,
    "timestamp": time.time()
})
```

---

### 方案 2: 热修复当前实验（不推荐）

**风险**: 可能影响已运行的 6.7h 数据

**步骤**:
```bash
# 1. 停止当前实验
kill 194798

# 2. 应用上述 4 个修改

# 3. 重启实验
nohup python3 experiments/real_world_72h_experiment.py --hours 72 > logs/real_world_72h/experiment.log 2>&1 &
```

---

## 📈 预期的真实行为

### 场景 1: 预算充足（>70%）

```
Hour 0-12:
  survival: 0.22-0.25
  curiosity: 0.28-0.35  ↑
  influence: 0.20-0.25
  optimization: 0.18-0.23

行为变化:
  - 更多 GitHub Gist 创建（optimization）
  - 更多探索性行动（curiosity）
  - 较少资源检查（survival）
```

### 场景 2: 预算紧张（<30%）

```
Hour 48-72:
  survival: 0.40-0.50  ↑
  curiosity: 0.15-0.20  ↓
  influence: 0.15-0.20  ↓
  optimization: 0.15-0.20  ↓

行为变化:
  - 频繁资源检查（survival）
  - 减少高成本行动
  - 优先保证生存
```

### 场景 3: 行动成功/失败

```
成功时:
  → 对应目标权重 +0.025
  → 鼓励继续该行为

失败时:
  → 对应目标权重 -0.05
  → 尝试其他策略
```

---

## 🎯 配置参数说明

### 学习率（learning_rate）

```python
'learning_rate': 0.05  # 默认值
```

- **高学习率**（0.1-0.2）: 权重变化快，适应性强
- **低学习率**（0.01-0.05）: 权重变化慢，稳定性好
- **推荐**: 0.05（平衡）

### 衰减率（decay_rate）

```python
'decay_rate': 0.01  # 默认值
```

- 长期未行动的目标权重衰减
- **高衰减**（0.05+）: 快速淘汰低效目标
- **低衰减**（0.001-0.01）: 温和调整
- **推荐**: 0.01

### 空闲阈值（idle_threshold_hours）

```python
'idle_threshold_hours': 12  # 默认值
```

- 超过此时间未行动，开始衰减
- **短阈值**（6h）: 快速响应
- **长阈值**（24h）: 更宽容
- **推荐**: 12h

---

## 📊 监控与验证

### 检查权重变化

```bash
# 查看最新检查点
cat datasets/real_world_72h/checkpoint_hour006.json | \
  jq '.objective_weights'
```

### 预期输出（v2 修复后）

```json
{
  "survival": 0.28,
  "curiosity": 0.24,
  "influence": 0.24,
  "optimization": 0.24
}
```

**不再是固定的 0.25！**

### 查看权重历史

```python
# Python 脚本
import json
import glob

files = sorted(glob.glob('datasets/real_world_72h/checkpoint_hour*.json'))

print("小时 | survival | curiosity | influence | optimization")
print("-" * 60)

for f in files:
    with open(f) as fp:
        data = json.load(fp)
    
    w = data['objective_weights']
    print(f"{data['hour']:4d} | {w['survival']:.3f} | {w['curiosity']:.3f} | {w['influence']:.3f} | {w['optimization']:.3f}")
```

---

## ✅ 验证清单

集成后检查：

- [ ] 权重不再固定为 0.25
- [ ] 资源下降时 survival 权重增加
- [ ] 资源充足时 curiosity 权重增加
- [ ] 权重始终在 [0.1, 0.6] 范围内
- [ ] 平衡得分 > 0.8
- [ ] 审计哈希链连续
- [ ] 日志中有 "update_weights" 相关记录

---

## 🐛 故障排查

### 问题 1: 权重仍为 0.25

**原因**: update_weights 未被调用

**解决**:
```python
# 检查主循环中是否有：
self.objective_system.update_weights({...})
```

### 问题 2: 权重超出边界

**原因**: 归一化逻辑错误

**解决**:
```python
# 检查 _normalize_weights() 是否正确实现
# 确保边界保护在归一化之前执行
```

### 问题 3: 审计哈希断裂

**原因**: record_action 未正确更新哈希链

**解决**:
```python
# 检查 _update_audit_hash() 是否被调用
# 确保每次 record_action 都更新哈希
```

---

## 📝 总结

### v2 核心优势

1. ✅ **真正的动态权重** - 不再是固定值
2. ✅ **多触发条件** - 资源/结果/时间/环境
3. ✅ **自修改能力** - 基于历史表现调整
4. ✅ **边界保护** - 权重始终合理
5. ✅ **完整审计** - 链式哈希不可篡改

### 建议

- **当前实验**: 继续运行（6.7h 数据有价值）
- **下次实验**: 使用 v2 系统
- **对比研究**: 对比 v1 和 v2 的行为差异

---

**集成指南完成时间**: 2026-03-30 17:28 GMT+8  
**v2 测试状态**: ✅ 通过  
**推荐集成**: 下次实验
