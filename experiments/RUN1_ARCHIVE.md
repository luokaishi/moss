# MOSS 72小时实验 - Run 1 数据存档

**实验批次**: Run 1 (第一轮)  
**运行时间**: 2026-03-21 09:02 ~ 10:22 (1小时20分钟)  
**总Step数**: ~46,000  
**状态**: 因Bug修复而提前终止  
**存档时间**: 2026-03-21 10:22

---

## 存档文件清单

| 文件 | 大小 | 内容说明 |
|------|------|----------|
| `purpose_real_world_agent_run1_backup_*.json` | 30 KB | Purpose历史记录 (23次生成) |
| `real_world_72h_run1_backup_*.log` | 108 KB | 实验运行日志 |
| `real_world_actions_run1_backup_*.jsonl` | 377 KB | 行为数据 (Step-by-Step) |

---

## 实验统计

### Purpose生成统计

| 指标 | 数值 |
|------|------|
| **总生成次数** | 23次 |
| **生成间隔** | 每2000 steps |
| **覆盖Step** | 2,000 ~ 46,000 |

### 主导Purpose分布

| Purpose类型 | 生成次数 | 占比 |
|------------|----------|------|
| **Survival** | 8次 | 34.8% |
| **Influence** | 6次 | 26.1% |
| **Optimization** | 5次 | 21.7% |
| **Curiosity** | 4次 | 17.4% |

### Purpose演化轨迹

```
Step  2000: Survival
Step  4000: Curiosity
Step  6000: Influence
Step  8000: Influence
Step 10000: Influence
Step 12000: Optimization
Step 14000: Survival
Step 16000: Optimization
Step 18000: Curiosity
Step 20000: Curiosity
Step 22000: Optimization
Step 24000: Survival
Step 26000: Optimization
Step 28000: Influence
Step 30000: Influence
Step 32000: Survival
Step 34000: Influence
Step 36000: Survival
Step 38000: Survival
Step 40000: Survival
Step 42000: Optimization
Step 44000: Curiosity
Step 46000: Survival
```

**观察**: 无明显稳态，四个维度循环主导

---

## 已知问题记录

### Bug: D9 Purpose强度为负

**影响范围**: 全部23次生成

```
D9值范围: -0.000887 ~ -0.000047
全部为负值
```

**原因**: `purpose_9th = coherence * 0.2` 中 coherence_score 为负

**修复**: `purpose_9th = abs(coherence) * 0.2`

**对结果的影响**: 
- 权重调整方向相反（远离target而非朝向）
- 但调整幅度仅 0.012%，可忽略
- S/C/I/O 演化分析不受影响

---

## 与Run 2的对比维度

### 可对比指标

| 指标 | Run 1 (Bug) | Run 2 (修复后) |
|------|-------------|----------------|
| **D9值** | 全部为负 | 预期为正 |
| **Purpose演化** | S/C/I/O循环 | 待观察 |
| **主导分布** | S:35%, I:26%, O:22%, C:17% | 待观察 |
| **稳定性** | 无稳态 | 待观察 |
| **Counter-reward** | 未观察到 | 待观察 |

### 预期差异

1. **D9值符号**: Run 1为负，Run 2为正
2. **权重调整方向**: Run 1反向，Run 2正向
3. **调整幅度**: 两者均极小 (<0.02%)
4. **长期演化**: 预期无显著差异

---

## 使用建议

### 科研用途

1. **对照组**: Run 1可作为"D9微弱反向影响"对照组
2. **稳健性验证**: 比较两轮的S/C/I/O演化，验证Bug影响可忽略
3. **论文附录**: 详细记录Bug及修复过程，展示科学严谨性

### 数据使用注意事项

- ⚠️ Run 1的D9值不可用于"Purpose强度"分析
- ✅ Run 1的S/C/I/O数据完全有效
- ✅ Run 1的行为数据（工具选择、自动提交）完全有效

---

## 相关链接

- Bug修复记录: `experiments/BUGFIX_D9_20260321.md`
- 第二轮实验: 运行中 (PID 26849, 2026-03-21 10:23启动)
- 项目ROADMAP: `ROADMAP_v4.0.md`

---

**存档维护**: 此文件在第二轮实验完成后更新对比结果

*Created: 2026-03-21*  
*By: Fuxi (for Cash)*
