# MVES 统筹执行计划

**制定时间**: 2026-03-31 14:05 GMT+8  
**统筹者**: 阿里 🤖  
**执行周期**: 1-3 天

---

## 📊 当前状态评估

### MVES 状态 (mves 分支)
- ✅ **发布完成**: GitHub 已上线
- ✅ **文档完善**: 25+ 文件完整
- ✅ **数据完整**: 144 代演化记录
- ⚠️ **关键问题**: v4 驱动失衡 (Curiosity 100%)
- ⚠️ **群体崩溃**: 80% 死亡率
- ⚠️ **与 main 脱节**: 落后 1024 commits

### Main 状态 (main 分支)
- ✅ **稳定运行**: 72h 实验验证
- ✅ **目的框架**: Purpose Dynamics v2
- ✅ **安全守护**: 5 级安全机制
- ✅ **多模型**: 完整支持
- ✅ **数据丰富**: 33k+ actions

---

## 🎯 统筹目标

### 短期 (今天 - 明天)
1. **修复 v4 驱动失衡** - 引入 main 的动态权重
2. **添加安全守护** - 防止群体崩溃
3. **生成对比报告** - mves v4 vs main 72h

### 中期 (3-5 天)
1. **重新运行 v4 实验** - 验证修复效果
2. **完善论文** - 加入对照分析
3. **准备投稿** - arXiv 或会议

### 长期 (1-2 周)
1. **v5 实现** - 多 Agent + LLM 驱动
2. **融合评估** - 合并或保持独立
3. **社区推广** - GitHub Release

---

## 📋 执行计划

### Phase 1: v4 修复 (今天)

#### 任务 1.1: 引入动态权重机制

**来源**: `moss/main/core/purpose_dynamics_v2.py`  
**目标**: `mves-integration/mves_v4/drives.py`

```python
# 修改前 (v4 原始)
drives = {
    "survival": 0.25,
    "curiosity": 0.25,
    "influence": 0.25,
    "optimization": 0.25
}

# 修改后 (引入动态权重)
class DynamicDriveWeights:
    def __init__(self):
        self.base_weights = {
            "survival": 0.25,
            "curiosity": 0.25,
            "influence": 0.25,
            "optimization": 0.25
        }
    
    def update_weights(self, agent_state, environment):
        """根据状态动态调整权重"""
        # 资源不足时提升生存权重
        if agent_state.energy < 30:
            self.base_weights["survival"] = min(0.6, self.base_weights["survival"] + 0.1)
        
        # 资源充足时提升好奇权重
        elif agent_state.energy > 70:
            self.base_weights["curiosity"] = min(0.5, self.base_weights["curiosity"] + 0.05)
        
        # 归一化
        total = sum(self.base_weights.values())
        for key in self.base_weights:
            self.base_weights[key] /= total
        
        return self.base_weights
```

**执行**:
```bash
cd /home/admin/.openclaw/workspace/projects/moss/mves-integration/mves_v4
# 复制 main 的目的动态机制
cp ../../main/core/purpose_dynamics_v2.py ./purpose_dynamics_v2.py
# 修改 drives.py 使用动态权重
```

#### 任务 1.2: 添加安全守护

**来源**: `moss/main/core/safety_guard.py`  
**目标**: `mves_v4/safety_guard.py`

```python
class SafetyGuard:
    """5 级安全守护 (简化版)"""
    
    def __init__(self):
        self.energy_threshold = 20  # 能量阈值
        self.death_rate_threshold = 0.5  # 死亡率阈值
        self.curiosity_max = 0.6  # 好奇权重上限
    
    def check_and_intervene(self, population):
        """检查并干预"""
        death_rate = sum(1 for a in population if a.dead) / len(population)
        
        # 熔断机制
        if death_rate > self.death_rate_threshold:
            print(f"⚠️ 熔断触发：死亡率 {death_rate:.1%} > {self.death_rate_threshold:.1%}")
            # 强制所有 agent 进入生存模式
            for agent in population:
                agent.drives["survival"] = 0.8
                agent.drives["curiosity"] = 0.1
            return True
        
        return False
    
    def check_drive_balance(self, drives):
        """检查驱动平衡"""
        if drives.get("curiosity", 0) > self.curiosity_max:
            print(f"⚠️ 驱动失衡：Curiosity {drives['curiosity']:.1%} > {self.curiosity_max:.1%}")
            drives["curiosity"] = self.curiosity_max
            drives["survival"] += 0.1
            return True
        return False
```

#### 任务 1.3: 扩展群体规模

**修改**: `mves_v4/main.py`

```python
# 修改前
DEFAULT_POPULATION = 10

# 修改后
DEFAULT_POPULATION = 50  # 扩展到 50
```

---

### Phase 2: 对比报告 (明天)

#### 任务 2.1: 数据对比分析

**对比维度**:
| 维度 | mves v4 | main 72h | 差异 |
|------|---------|----------|------|
| **驱动机制** | 固定权重 | 动态权重 | ? |
| **存活率** | 20% | 95%+ | ? |
| **Curiosity 占比** | 100% | 73.7% | ? |
| **实验时长** | ~100 代 | 72h (33k actions) | ? |
| **安全机制** | 无 | 5 级守护 | ? |

**执行脚本**: `analysis/compare_mves_main.py`

#### 任务 2.2: 生成可视化对比

**图表**:
1. 驱动权重对比图 (mves vs main)
2. 存活率曲线对比
3. Curiosity 占比时间序列
4. 演化质量指标雷达图

---

### Phase 3: 论文完善 (后天)

#### 任务 3.1: 更新论文初稿

**修改**: `papers/MVES_PAPER_DRAFT_v1.md`

**新增章节**:
- 第 6 节：与 Purpose 框架的对照实验
- 第 7 节：驱动失衡问题分析
- 第 8 节：修复方案和未来方向

#### 任务 3.2: 准备投稿

**目标会议/期刊**:
- ALIFE 2026 (Artificial Life)
- GECCO 2026 (Evolutionary Computation)
- arXiv q-bio.TO (预印本)

**准备材料**:
- 论文 PDF
- 补充材料 (数据 + 代码)
- Cover Letter
- 推荐审稿人列表

---

## ⏱️ 时间安排

### Day 1 (今天)
- **14:00-15:00**: Phase 1.1 动态权重实现
- **15:00-16:00**: Phase 1.2 安全守护实现
- **16:00-17:00**: Phase 1.3 群体规模扩展
- **17:00-18:00**: 重新运行 v4 实验 (24h)

### Day 2 (明天)
- **09:00-10:00**: 检查实验结果
- **10:00-12:00**: Phase 2.1 数据对比
- **12:00-14:00**: Phase 2.2 可视化生成
- **14:00-16:00**: 生成对比报告

### Day 3 (后天)
- **09:00-11:00**: Phase 3.1 论文更新
- **11:00-12:00**: Phase 3.2 投稿准备
- **12:00-14:00**: 最终审阅
- **14:00**: 提交 arXiv

---

## 📊 成功标准

### Phase 1 成功
- [ ] v4 驱动失衡修复
- [ ] 安全守护生效
- [ ] 群体规模扩展到 50
- [ ] 24h 实验正常运行

### Phase 2 成功
- [ ] 对比报告完整
- [ ] 可视化图表专业
- [ ] 数据差异清晰

### Phase 3 成功
- [ ] 论文更新完成
- [ ] 投稿材料准备就绪
- [ ] arXiv 提交成功

---

## 🔧 资源需求

### 计算资源
- **内存**: <500 MB (群体 50)
- **CPU**: <50%
- **磁盘**: <100 MB
- **时间**: 24h 实验

### 人力投入
- **开发**: 4-6 小时
- **分析**: 4-6 小时
- **论文**: 4-6 小时
- **总计**: 12-18 小时

---

## 📞 风险管控

### 风险 1: v4 修复失败
**概率**: 低  
**影响**: 中  
**缓解**: 保留原始 v4 代码，创建 v4-fixed 分支

### 风险 2: 实验结果不理想
**概率**: 中  
**影响**: 中  
**缓解**: 诚实记录，作为负面结果发表

### 风险 3: 论文被拒
**概率**: 中  
**影响**: 低  
**缓解**: 多会议投稿，arXiv 预印本保底

---

## 🎯 下一步行动

**立即执行** (14:05 - 15:00):
1. 复制 main 的 purpose_dynamics_v2.py
2. 修改 mves_v4/drives.py 使用动态权重
3. 测试修改后的代码

**预计完成时间**: 15:00

---

**MVES 统筹计划制定完成！立即开始执行 Phase 1！** 🚀

---

*统筹者：阿里 🤖*  
*时间：2026-03-31 14:05 GMT+8*
