# Meta-SME 稳定性修复方案

## 问题分析

E3 N=5 实验显示 Meta-SME 高度不稳定：
- 仅 20% (1/5) 的 trial 产生正向 meta-fitness 提升
- 平均 meta-fitness Δ = -5.2% (p=0.079, 不显著)

### 根本原因

1. **Meta-fitness 评估方差过大**
   - `_evaluate_sme_fitness()` 运行 10 代 SME 实验
   - 每次评估本身就有随机性（不同的种子、变异选择）
   - 导致 meta-fitness 信号被噪声淹没

2. **评估成本过高**
   - 每代 Meta 需要评估 4 个候选 × 10 代 SME = 40 次 SME 运行
   - 30 代 Meta = 1200 次 SME 运行
   - 评估时间过长，累积误差

3. **接受阈值过于严格**
   - `acceptance_threshold=-0.001` 要求几乎立即正向提升
   - Meta 进化是长期的，短期波动正常

4. **变异空间仍过大**
   - `META_TARGET_FUNCTIONS` 包含 6 个函数
   - 每个函数可能有数十个可变异常量
   - 搜索空间太大，随机变异效率低

## 修复方案

### 1. 改进 Meta-fitness 评估 (高优先级)

**当前**: 单次 10 代 SME 运行  
**改进**: 多次运行取平均 + 评估历史趋势

```python
def _evaluate_sme_fitness_robust(self, sme_source: str, n_runs: int = 3) -> float:
    """鲁棒的 meta-fitness 评估（多次运行平均）"""
    fitness_values = []
    for seed in range(n_runs):
        f = self._evaluate_sme_fitness_single(sme_source, seed=seed)
        fitness_values.append(f)
    
    # 使用中位数而非均值（对异常值更鲁棒）
    return float(np.median(fitness_values))
```

### 2. 降低单次评估成本

**当前**: 10 代 SME  
**改进**: 5 代 SME + 快速适应度估算

```python
# 快速评估模式
quick_config = SMEConfig(
    max_generations=5,  # 从 10 降到 5
    population_size=2,  # 从 3 降到 2
)
```

### 3. 放宽接受策略

**当前**: 每代必须 Δ > -0.001  
**改进**: 滑动窗口接受 + 累积提升

```python
# 允许短期波动，看长期趋势
if best_meta["delta"] > -0.01:  # 放宽到 -0.01
    # 接受，但记录到历史
    self.meta_fitness_history.append(best_meta["meta_fitness"])
    
    # 只有历史趋势向上才真正接受
    if len(self.meta_fitness_history) >= 5:
        recent_trend = np.polyfit(range(5), self.meta_fitness_history[-5:], 1)[0]
        if recent_trend > 0:
            # 真正接受
```

### 4. 约束变异空间

**当前**: 6 个目标函数  
**改进**: 仅允许 fitness 权重参数变异

```python
# 更严格的变异白名单
META_SAFE_MUTATIONS_V2 = [
    "fitness_weight_tweak",  # 只允许调整 α/β/γ/δ
]

META_TARGET_CONSTANTS = [
    "EmergenceGuidedFitness.alpha",
    "EmergenceGuidedFitness.beta", 
    "EmergenceGuidedFitness.gamma",
    "EmergenceGuidedFitness.delta",
]
```

### 5. 添加 Meta-level 早停

```python
# 如果连续 10 代无改进，早停
if self.generations_without_improvement >= 10:
    logger.info("[MetaSME] Early stopping: no improvement for 10 generations")
    break
```

## 实施计划

1. **Phase 3A**: 实现改进的 meta-fitness 评估（多次运行 + 中位数）
2. **Phase 3B**: 实现滑动窗口接受策略
3. **Phase 3C**: 约束变异空间到 fitness 权重
4. **Phase 3D**: 重新运行 E3 N=10 验证

## 预期结果

- Meta-fitness 评估方差降低 50%
- 接受率从 13% 提升到 30%+
- 正向 trial 比例从 20% 提升到 60%+
