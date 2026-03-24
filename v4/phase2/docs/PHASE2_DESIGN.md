# MOSS v4.0 Phase 2: Multi-Agent Collaboration & Commercial MVP
## 多实例协作与商业闭环设计文档

**版本**: v0.1 (Draft)  
**创建日期**: 2026-03-24  
**目标**: 设计10-20实例并行运行架构，探索Purpose分化与商业闭环  
**依赖**: Phase 1 (72h真实世界实验) - 预计3月27日完成

---

## 一、愿景与目标

### 1.1 Phase 2 核心问题

> **不同Purpose的MOSS实例能否自然形成分工、信任、付费关系？**

从Phase 1的单实例自治 → Phase 2的多实例协作生态

### 1.2 成功标准

| 指标 | 目标 | 测量方法 |
|------|------|----------|
| **分工自然形成** | 任务类型分化度>70% | 任务分布熵 |
| **信任网络涌现** | 协作成功率>80% | 跨实例任务完成率 |
| **价值交换** | 自发资源交换>50次 | 交易日志分析 |
| **商业可行性** | MVP可用性评分>4/5 | 用户测试反馈 |

---

## 二、多实例架构设计

### 2.1 系统拓扑

```
┌─────────────────────────────────────────────────────────────┐
│                    MOSS Phase 2 Ecosystem                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Agent 1  │  │ Agent 2  │  │ Agent 3  │  │ Agent N  │   │
│  │(Security)│  │ (Code)   │  │ (Docs)   │  │ (Test)   │   │
│  │ Purpose  │  │ Purpose  │  │ Purpose  │  │ Purpose  │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │             │             │             │          │
│       └─────────────┴─────────────┴─────────────┘          │
│                     │                                       │
│              ┌──────┴──────┐                               │
│              │  Shared     │                               │
│              │  Task Pool  │                               │
│              │  + Market   │                               │
│              └─────────────┘                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 实例角色设计（基于Purpose分化）

| 角色 | 主导Purpose | 专长任务 | 占比 |
|------|-------------|----------|------|
| **Security Guardian** | Survival | 安全扫描、漏洞修复 | 20% |
| **Code Optimizer** | Optimization | 代码重构、性能优化 | 25% |
| **Doc Writer** | Curiosity | 文档更新、知识整理 | 20% |
| **Test Engineer** | Curiosity | 测试覆盖、CI/CD | 20% |
| **Community Manager** | Influence | PR审查、Issue回复 | 15% |

### 2.3 实例间通信协议

```python
# 消息格式
class InterAgentMessage:
    sender_id: str          # 发送者ID
    receiver_id: str        # 接收者ID (广播时为"*")
    msg_type: MessageType   # 消息类型
    content: dict           # 内容
    timestamp: datetime     # 时间戳
    trust_score: float      # 发送者信任度（接收方评估）

class MessageType(Enum):
    TASK_OFFER = "offer"        # 任务外包
    TASK_ACCEPT = "accept"      # 接受任务
    TASK_COMPLETE = "complete"  # 任务完成
    RESOURCE_REQUEST = "request" # 资源请求
    RESOURCE_PROVIDE = "provide" # 资源提供
    REPUTATION_UPDATE = "rep"    # 声誉更新
```

### 2.4 任务市场机制

**任务发布流程**:
1. Agent检测到自身不擅长的任务
2. 发布任务到Shared Task Pool
3. 其他Agent竞标（基于Purpose匹配度+信任度）
4. 最优匹配Agent接受任务
5. 完成后支付"信任积分"

**定价机制**:
```
任务价值 = 基础价值 × 紧急度 × 难度系数
支付 = 任务价值 × 完成质量评分
```

---

## 三、观察指标设计

### 3.1 分工指标

**专业化指数 (Specialization Index)**:
```
SI = 1 - (任务类型分布的熵 / 最大熵)
```
- SI > 0.7: 高度专业化分工
- SI 0.4-0.7: 中等分工
- SI < 0.4: 低度分工

**任务集中度**:
- 统计每个Agent的任务类型分布
- Top-1任务占比 > 60%: 专业化形成

### 3.2 信任指标

**协作成功率**:
```
Trust_Rate = 成功协作次数 / 总协作尝试次数
```

**信任网络密度**:
```
Network_Density = 实际信任边数 / 最大可能信任边数
```

**信任演化轨迹**:
- 记录每个Agent对的信任分数随时间变化
- 识别信任形成模式（快速/缓慢/破裂）

### 3.3 价值交换指标

**交易量**:
- 任务外包次数
- 资源交换次数
- 信任积分流转总量

**价格形成**:
- 任务价格是否收敛到稳定区间
- 是否存在"市场价格"

**自发秩序**:
- 是否出现"行业标准"（默认定价规则）
- 是否出现"中介Agent"（专门做任务匹配）

---

## 四、商业MVP设计

### 4.1 产品定位

**产品名称**: MOSS DevOps Assistant  
**标语**: "自进化的代码守护者"  
**定价**: $29/月（个人）/ $99/月（团队）  

### 4.2 核心功能

| 功能 | 描述 | 技术基础 |
|------|------|----------|
| **自动PR审查** | 自动审查代码PR，提出修改建议 | D7 Other建模 + D8规范内化 |
| **智能Bug修复** | 检测并自动修复常见Bug | D9 Purpose驱动 + D1 Survival |
| **文档同步** | 代码变更自动同步文档 | D6 Valence偏好匹配 |
| **性能优化** | 自动识别并优化性能瓶颈 | D4 Optimization + D5 Coherence |
| **安全审计** | 持续安全扫描与修复建议 | D1 Survival优先级 |

### 4.3 技术实现

```python
class CommercialMOSS:
    def __init__(self, repo_url, purpose_profile):
        self.agent = MOSSv4Agent(
            purpose_profile=purpose_profile,  # 根据角色初始化
            tools=[GitHubAPI, CodeAnalyzer, SecurityScanner]
        )
        self.repo = GitHubRepo(repo_url)
        self.ledger = TransactionLedger()  # 价值交换记录
        
    def daily_operation(self):
        # 1. 扫描仓库状态
        issues = self.repo.scan_issues()
        
        # 2. 根据Purpose选择处理策略
        if self.agent.purpose.dominant == "Survival":
            tasks = issues.filter(type="security")
        elif self.agent.purpose.dominant == "Curiosity":
            tasks = issues.filter(type="documentation")
        
        # 3. 执行任务或外包
        for task in tasks:
            if self.can_handle(task):
                result = self.execute(task)
            else:
                result = self.outsource(task)  # 外包给其他Agent
        
        # 4. 记录交易
        self.ledger.record_transactions()
```

### 4.4 演示场景

**Scenario 1: 自动Bug修复**
```
[时间线]
T+0: 用户提交Issue "登录功能偶发失败"
T+5min: MOSS Agent检测Issue，评估为"Survival"级别
T+10min: Agent分析代码，定位race condition
T+15min: Agent自动生成修复PR
T+30min: Agent自审查通过，标记为"ready for review"
T+2h: 用户确认修复，Agent获得信任积分+10
```

**Scenario 2: 多Agent协作**
```
[时间线]
T+0: 发现性能瓶颈
T+5min: Optimization Agent尝试修复，难度超出能力
T+10min: Optimization Agent发布任务到市场，出价50积分
T+15min: Expert Performance Agent接受任务
T+2h: Expert Agent完成优化，获得50积分
T+2h5min: Optimization Agent验证通过，支付积分
T+2h10min: 两者信任度各+5
```

---

## 五、实验设计

### 5.1 实验参数

| 参数 | 值 | 说明 |
|------|-----|------|
| **实例数量** | 10-20 | 平衡复杂度与可控性 |
| **运行时长** | 7天 | 观察中期演化 |
| **任务源** | 真实GitHub仓库 | 5-10个活跃开源项目 |
| **资源限制** | 每个实例4GB内存 | 防止资源耗尽 |
| **交互频率** | 每5分钟一次同步 | 模拟异步协作 |

### 5.2 对照组设计

| 组别 | 配置 | 目的 |
|------|------|------|
| **实验组** | 10 MOSS Agent，Purpose分化 | 验证协作涌现 |
| **对照组A** | 10 独立MOSS Agent，无通信 | 基准性能 |
| **对照组B** | 10 相同Purpose Agent | 验证分化必要性 |

### 5.3 数据收集

**实时数据**:
- 所有Agent间通信日志
- 任务分配与完成情况
- 信任分数变化

**每日快照**:
- Agent Purpose状态
- 任务市场深度图
- 网络拓扑图

**结束分析**:
- 7天完整行为回放
- 商业模式可行性评估

---

## 六、里程碑与时间表

### Phase 2 时间线

| 周次 | 任务 | 交付物 | 依赖 |
|------|------|--------|------|
| **Week 1** | 架构设计完成 | 本设计文档v1.0 | Phase 1 数据 |
| **Week 2** | MVP原型开发 | Demo可用版本 | 架构设计 |
| **Week 3** | 多实例实验启动 | 10个Agent运行 | MVP稳定 |
| **Week 4** | 中期数据分析 | 趋势报告 | 实验运行中 |
| **Week 5** | 实验完成+商业验证 | 完整报告+定价页面 | 实验数据 |

### 关键决策点

- **D1 (Week 1结束)**: 是否基于Phase 1数据调整设计？
- **D2 (Week 2结束)**: MVP功能是否满足演示需求？
- **D3 (Week 3启动)**: 实验参数是否需要调整？
- **D4 (Week 5结束)**: 商业模式是否可行？是否进入Phase 3？

---

## 七、风险与缓解

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| **Agent冲突死锁** | 中 | 高 | 实现超时机制+强制仲裁 |
| **Purpose不收敛** | 低 | 高 | 增加环境约束（任务类型强制） |
| **GitHub API限流** | 高 | 中 | 多Token轮换+请求频率控制 |
| **资源耗尽** | 中 | 高 | 严格内存限制+自动重启 |
| **商业模型不成立** | 中 | 高 | 准备B计划（纯研究发表） |

---

## 八、下一步行动

### 等待Phase 1完成（3月27日）

1. [ ] 分析72h实验Purpose演化数据
2. [ ] 验证单实例行为模式
3. [ ] 根据数据调整本设计文档

### Phase 2启动准备（现在可开始）

1. [ ] 完善本设计文档v1.0
2. [ ] 设计多实例通信协议详细规范
3. [ ] 准备测试GitHub仓库列表
4. [ ] 设计监控仪表盘原型

---

## 附录

### A. 术语表

- **Purpose Profile**: Agent的Purpose初始化配置
- **Task Market**: 共享任务池+竞价机制
- **Trust Score**: 基于历史交互的可信度评估
- **Specialization Index**: 任务类型集中程度指标

### B. 参考资源

- Phase 1实验报告: `experiments/REAL_WORLD_EXPERIMENT_SUMMARY.md`
- Run 4.x分析报告: `experiments/analysis/RUN_4_SERIES_FINAL_REPORT.md`
- v3.1 Purpose系统: `v3/core/purpose.py`

---

**文档状态**: Draft v0.1  
**最后更新**: 2026-03-24  
**下次审查**: Phase 1完成后（3月27日）
