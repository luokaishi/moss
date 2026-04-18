# v6.0 权重上限机制实现文档

**日期**: 2026-04-17  
**状态**: ✅ 已完成  
**测试**: 19 个单元测试全部通过  

---

## 概述

基于 Copilot 评估报告的建议，实现了驱动力权重上限机制，解决 survival 驱动过度增长、挤压涌现空间的问题。

**核心目标**:
- 限制 survival 驱动在 30% 以内
- 为涌现驱动预留 35% 空间
- 实现软上限机制，允许轻微溢出但增长放缓

---

## 实现文件

| 文件 | 路径 | 说明 |
|------|------|------|
| 核心实现 | `agi/drive_weight_cap.py` | 权重上限管理器 |
| DriveManager 集成 | `agi/drive_manager.py` | 集成权重上限到更新流程 |
| 单元测试 | `tests/test_weight_cap.py` | 19 个测试用例 |

---

## 核心组件

### 1. WeightCapConfig

配置类，定义各驱动的权重上限：

```python
@dataclass
class WeightCapConfig:
    survival: float = 0.30      # 生存驱动上限 30%
    optimization: float = 0.25  # 优化驱动上限 25%
    influence: float = 0.20     # 影响驱动上限 20%
    curiosity: float = 0.15     # 好奇驱动上限 15%
    emergent: float = 0.35      # 涌现驱动上限 35%
    soft_cap_overflow: float = 0.10  # 软上限溢出 10%
```

### 2. DriveWeightCap

核心上限逻辑：

```python
class DriveWeightCap:
    def apply_cap(self, drive_name: str, current_weight: float,
                  is_emergent: bool = False, proposed_delta: float = 0.0) -> float:
        """
        应用权重上限，返回调整后的新权重值
        
        策略：
        1. 在硬上限内：正常增长
        2. 在软硬上限之间：增长放缓（最多减缓 50%）
        3. 超过软上限：严格限制
        """
```

### 3. DriveWeightCapManager

集成到 DriveManager 的管理器：

```python
class DriveWeightCapManager:
    def apply_weight_update(self, drive_name: str, proposed_delta: float) -> float:
        """应用权重更新，强制执行上限"""
        
    def normalize_with_caps(self) -> Dict[str, float]:
        """归一化权重，同时确保不超过上限"""
```

---

## 使用方式

### 基础用法

```python
from agi.drive_manager import DriveManager

# 配置权重上限
weight_cap_config = {
    'survival': 0.30,
    'optimization': 0.25,
    'influence': 0.20,
    'curiosity': 0.15,
    'emergent': 0.35
}

# 创建 DriveManager 时启用权重上限
drive_manager = DriveManager(
    drives_config=drives_config,
    weight_cap_config=weight_cap_config
)

# 权重更新会自动应用上限
drive_manager.update_weight_from_feedback('survival', reward=0.8, lr=0.1)
```

### 使用预设配置

```python
from agi.drive_weight_cap import get_preset

# 使用 v6 默认预设
config = get_preset('v6_default')
drive_manager = DriveManager(drives_config, weight_cap_config='v6_default')

# 可用预设
# - v6_default: 标准配置 (survival=0.30)
# - v6_strict: 严格配置 (survival=0.25)
# - v6_loose: 宽松配置 (survival=0.35)
```

### 获取统计信息

```python
# 获取上限管理统计
stats = drive_manager.get_weight_cap_stats()
print(f"总更新次数: {stats['total_updates']}")
print(f"触发上限次数: {stats['caps_applied']}")
print(f"上限触发率: {stats['cap_rate']:.2%}")
```

---

## 软上限机制详解

### 工作原理

```
硬上限 (cap): 30%
软上限 (soft_cap): 30% * 1.10 = 33%

当前权重 28%，提议 +5%:
- 新权重 33% = 软上限 → 允许
- 但增长放缓: dampening = 1 - (3%/3%)*0.5 = 0.5
- 实际增长: 2.5% (减缓 50%)

当前权重 30%，提议 +5%:
- 新权重 35% > 软上限 33% → 严格限制到 33%
- 记录溢出事件
```

### 溢出警告

当某个驱动频繁触发上限时，系统会发出警告：

```python
if cap.should_warn('survival'):
    print("警告: survival 驱动频繁触及上限，建议检查系统配置")
```

---

## 测试覆盖

### 测试文件: `tests/test_weight_cap.py`

| 测试类 | 测试数 | 覆盖内容 |
|--------|--------|----------|
| TestWeightCapConfig | 4 | 配置默认值、上限获取 |
| TestDriveWeightCap | 6 | 硬上限、软上限、溢出跟踪 |
| TestDriveWeightCapManager | 5 | 权重更新、归一化、统计 |
| TestPresets | 4 | 预设配置验证 |
| TestEmergentDriveProtection | 1 | 涌现驱动保护 |

**运行测试**:
```bash
python tests/test_weight_cap.py
```

---

## 预期效果

### v5.5.2 现状

| 驱动 | 权重 | 占比 |
|------|------|------|
| survival | 0.378 | 37.8% |
| optimization | 0.214 | 21.4% |
| influence | 0.168 | 16.8% |
| emergent | 0.168 | 16.8% |
| curiosity | 0.072 | 7.2% |

### v6.0 目标 (启用权重上限后)

| 驱动 | 目标权重 | 目标占比 |
|------|----------|----------|
| survival | ≤0.30 | ≤30% |
| optimization | ≤0.25 | ≤25% |
| influence | ≤0.20 | ≤20% |
| **emergent** | **≥0.20** | **≥20%** |
| curiosity | ≤0.15 | ≤15% |

**预期改进**:
- survival 权重从 37.8% 降至 30% 以下
- 释放约 8% 权重空间给涌现驱动
- 涌现驱动有望从 16.8% 提升至 20%+

---

## 下一步

1. **运行 5,000 周期验证实验** - 验证权重上限的实际效果
2. **调整软上限参数** - 根据实验结果优化 10% 溢出比例
3. **集成到 v6 预注册实验** - 作为 H1 假设验证

---

## 参考

- Copilot 评估报告: `markDown1776415707546.md`
- v6 预注册草案: `docs/mves/v6_preregistration_draft.md`
- v6 TODO 清单: `docs/mves/v6_todo_checklist.md`

---

*实现完成: 2026-04-17*  
*测试通过: 19/19*  
*作者: OpenClaw Agent*
