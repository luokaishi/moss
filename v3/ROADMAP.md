# MOSS v3.0.0 开发规划

**版本定位**: 从4维到8维的维度扩展  
**基础**: 保留v2.0.0论文成果，开启新理论探索  
**核心思想**: ChatGPT维度扩展框架  
**创建日期**: 2026-03-19

---

## 版本关系

```
MOSS v2.0.0 (论文版本)
    │
    ├── 核心：4维目标 [S, C, I, O]
    ├── 状态：已发布，NeurIPS投稿
    └── 保留：所有实验结果和验证

    ↓

MOSS v3.0.0 (扩展版本)
    │
    ├── 核心：8维目标 [S, C, I, O, V_coh, V_val, Oth, Norm]
    ├── 状态：开发中
    └── 目标：探索"最小可演化主体"到"最小社会系统"
```

---

## 维度架构（v3.0.0）

| 维度 | 符号 | 名称 | 核心功能 | 数学形式 |
|------|------|------|----------|----------|
| 1 | S | Survival | 生存 | 原有 |
| 2 | C | Curiosity | 探索 | 原有 |
| 3 | I | Influence | 影响 | 原有 |
| 4 | O | Optimization | 优化 | 原有 |
| **5** | **V_coh** | **Coherence** | **自我连续性** | **V = -||w - w_ref||²** |
| **6** | **V_val** | **Valence** | **主观偏好** | **V = β·ΔM** |
| **7** | **Oth** | **Other** | **他者建模** | **待设计** |
| **8** | **Norm** | **Norm** | **规范内化** | **V = -N(a,s)** |

---

## 开发阶段

### Phase 1: 第5维 Coherence（✅ 已完成 2026-03-19）

**目标**: 实现自我连续性机制

**核心代码**:
```python
class CoherenceModule:
    def __init__(self, alpha=0.9):
        self.w_ref = None  # 参考权重
        self.alpha = alpha  # EMA系数
    
    def update_reference(self, w_current):
        """更新参考身份"""
        if self.w_ref is None:
            self.w_ref = w_current.copy()
        else:
            self.w_ref = self.alpha * w_current + (1 - self.alpha) * self.w_ref
    
    def compute_coherence(self, w_current):
        """计算一致性reward"""
        return -np.sum((w_current - self.w_ref) ** 2)
```

**实现文件**: `v3/core/coherence.py`

**实验目标**:
- [x] 验证路径稳定性提升
- [x] 测量weight attractor收敛
- [x] 观察"身份锁定"现象

**测试结果**: ✅ 通过
- EMA更新正常
- 距离计算正确
- IdentityAttractor可检测收敛

---

### Phase 2: 第6维 Valence（✅ 已完成 2026-03-19）

**目标**: 实现主观偏好机制

**核心代码**:
```python
class ValenceModule:
    def __init__(self, gamma=0.01):
        self.beta = np.ones(4) / 4  # 偏好权重，初始均匀
        self.gamma = gamma  # 学习率
        self.M_prev = None  # 上一步M值
    
    def compute_valence(self, M_current):
        """计算内部体验"""
        if self.M_prev is None:
            self.M_prev = M_current.copy()
            return 0
        
        delta_M = M_current - self.M_prev
        E = np.dot(self.beta, delta_M)
        
        # 更新偏好
        self.beta += self.gamma * delta_M
        self.beta = normalize(self.beta)
        
        return E
```

**实现文件**: `v3/core/valence.py`

**实验目标**:
- [x] 验证性格分化涌现
- [x] 观察损失厌恶行为
- [x] 测试非最优选择现象

**测试结果**: ✅ 通过
- PersonalityClassifier可识别5种人格类型
- 偏好权重可进化
- 损失厌恶系数可计算
        E = np.dot(self.beta, delta_M)
        
        # 更新偏好
        self.beta += self.gamma * delta_M
        self.beta = np.maximum(self.beta, 0)  # 非负
        self.beta /= np.sum(self.beta)  # 归一化
        
        self.M_prev = M_current.copy()
        return E
```

**实验目标**:
- [ ] 验证性格分化涌现
- [ ] 观察损失厌恶行为
- [ ] 测试非最优选择现象

**成功标准**:
- 相同初始条件产生不同行为模式
- 系统避免负变化（即使正变化reward更高）
- 出现"偏好某种成长路径"现象

---

### Phase 3: 第7-8维 Other + Norm（✅ 已完成 2026-03-19）

**目标**: 实现多主体社会系统

**实现文件**:
- `v3/core/other.py` - 第7维：他者建模、信任、声誉
- `v3/core/norm.py` - 第8维：规范内化、社会约束
- `v3/social/multi_agent_society.py` - 多agent社会环境

**核心代码**:
```python
class OtherModule:
    def observe_agent(self, agent_id, behavior, step):
        # 更新他者模型
        # 计算信任分数
        # 预测行为

class NormModule:
    def compute_norm_cost(self, action, state):
        # N(a,s) = social_penalty + self_penalty
        # V_norm = -N(a,s)
```

**实验目标**:
- [x] 验证信任结构涌现
- [x] 观察声誉机制
- [x] 测试三种收敛形态

**实验结果**: ✅ 通过（2026-03-19）
```
实验设置: 8 agents, 100 steps
结果: 100% cooperation rate
Mean trust: 0.869
所有agent识别其他agent
```

**对照实验**: ✅ 已完成（2026-03-19）
```
设置: 10 agents, 500 steps
有D7-D8: 100.00% cooperation, trust=0.998
无D7-D8: 49.88% cooperation (random)
提升: +50.12 percentage points
```

**关键发现**:
- 社交维度(D7-D8)使合作率提升50%+
- 信任网络成功涌现
- 规范内化导致稳定合作
- 对照组呈现囚徒困境均衡(~50%)

---

## 理论贡献目标

### v3.0.0论文（目标：NeurIPS 2027 或 Science/ Nature子刊）

**核心命题**:
> 从4维到8维：自驱力系统的维度扩展与主体性涌现

**关键贡献**:
1. **理论**: 提供"最小可演化主体"到"最小社会系统"的完整框架
2. **实验**: 验证每个维度的独立贡献和组合效应
3. **预测**: 性格分化、非最优行为、规范涌现的可验证预测

**与v2.0.0的关系**:
- v2.0.0: 证明4维MOSS可产生自适应行为
- v3.0.0: 证明5-8维可产生主体性和社会结构

---

## 代码结构（✅ 已实现）

```
moss/
├── v2/                      # v2.0.0（论文版本，冻结）
│   └── ...
├── v3/                      # v3.0.0（✅ 已实现）
│   ├── core/
│   │   ├── coherence.py     # ✅ 第5维
│   │   ├── valence.py       # ✅ 第6维
│   │   ├── other.py         # ✅ 第7维
│   │   ├── norm.py          # ✅ 第8维
│   │   ├── agent.py         # ✅ D1-D6 Agent
│   │   └── agent_8d.py      # ✅ D1-D8 Agent
│   ├── social/
│   │   └── multi_agent_society.py  # ✅ 多agent社会
│   └── experiments/
│       └── longterm_control_experiment.py  # ✅ 对照实验
└── docs/
    ├── chatgpt_analysis.md      # ChatGPT分析Part 1
    ├── chatgpt_analysis_part2.md # Part 2: D5设计
    ├── chatgpt_analysis_part3.md # Part 3: D6设计
    └── chatgpt_analysis_part4.md # Part 4: D8设计
```

---

## 风险评估

### 技术风险

| 风险 | 概率 | 影响 | 应对 |
|------|------|------|------|
| 维度爆炸导致不稳定 | 中 | 高 | 逐个添加，充分测试 |
| 超参数调优困难 | 高 | 中 | 自动化参数搜索 |
| 计算成本过高 | 中 | 中 | 优化实现，使用缓存 |

### 理论风险

| 风险 | 概率 | 影响 | 应对 |
|------|------|------|------|
| 涌现行为不明显 | 中 | 高 | 设计更敏感的测量指标 |
| 与现有理论重复 | 低 | 中 | 充分文献调研 |
| 审稿人不接受"意识"相关讨论 | 中 | 高 | 使用功能主义语言，避免"意识"术语 |

---

## 里程碑

| 日期 | 里程碑 | 交付物 |
|------|--------|--------|
| 2026-03-27 | Phase 1完成 | Coherence模块+实验报告 |
| 2026-04-10 | Phase 2完成 | Valence模块+性格分化实验 |
| 2026-05-10 | Phase 3完成 | Other+Norm模块+社会实验 |
| 2026-05-31 | v3.0.0 alpha | 完整8维系统+基础测试 |
| 2026-06-30 | v3.0.0 beta | 完整实验套件+论文草稿 |
| 2026-09-15 | v3.0.0 release | 投稿NeurIPS 2027 |

---

## 与ChatGPT分析的关联

| ChatGPT建议 | v3.0.0实现 |
|-------------|------------|
| Value Coherence（第5维） | Phase 1核心目标 |
| Valence（第6维） | Phase 2核心目标 |
| Other（第7维） | Phase 3目标 |
| Norm（第8维） | Phase 3目标 |
| 性格分化预测 | Phase 2实验验证 |
| 非最优行为预测 | Phase 2实验验证 |
| 三种收敛形态 | Phase 3实验验证 |

---

## 下一步行动

### 今天
- [ ] 创建v3/目录结构
- [ ] 迁移v2核心代码到v3
- [ ] 开始Coherence模块实现

### 本周
- [ ] 完成Coherence模块编码
- [ ] 设计身份锁定实验
- [ ] 开始实验运行

### 文档
- [ ] 创建v3_design.md详细设计
- [ ] 更新README说明版本关系
- [ ] 创建CHANGELOG记录v2→v3演进

---

**创建时间**: 2026-03-19  
**创建者**: Cash  
**状态**: 规划阶段，准备启动开发
