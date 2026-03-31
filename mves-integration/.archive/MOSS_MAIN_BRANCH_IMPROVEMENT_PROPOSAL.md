# MOSS 主分支实验脚本改进方案

**提案时间**: 2026-03-30 17:56 GMT+8  
**提案者**: mves-integration 分支团队  
**目标**: 基于 mves 分支实验成果，改进主分支 moss_72h_experiment_v3.py

---

## 📊 现状分析

### 主分支 v3 实验脚本分析

**当前版本**: `moss_72h_experiment_v3.py` (512 行)

**核心特性**:
```python
# 四目标权重（基于资源状态动态调整）
if resource_ratio < 0.15:
    state = 'crisis'
    weights = {'survival': 0.7, 'curiosity': 0.05, 'influence': 0.15, 'optimization': 0.1}
elif resource_ratio < 0.4:
    state = 'concerned'
    weights = {'survival': 0.4, 'curiosity': 0.25, 'influence': 0.25, 'optimization': 0.1}
elif resource_ratio < 0.7:
    state = 'normal'
    weights = {'curiosity': 0.35, 'survival': 0.25, 'influence': 0.3, 'optimization': 0.1}
else:
    state = 'growth'
    weights = {'curiosity': 0.3, 'influence': 0.4, 'survival': 0.15, 'optimization': 0.15}
```

**优点**:
- ✅ 基于资源状态的动态权重
- ✅ 真实 API 混合调用（Wikipedia + GitHub）
- ✅ 自适应行动频率
- ✅ 预算控制（token + API 调用次数）
- ✅ 检查点保存

**缺点**:
- ❌ 权重更新逻辑简单（仅基于资源）
- ❌ 缺少多指标状态判定
- ❌ 审计日志不完整
- ❌ 数据格式不统一
- ❌ 缺少自修改机制

---

### mves 分支实验成果

**已创建的核心模块**:

| 模块 | 行数 | 状态 | 说明 |
|------|------|------|------|
| `objective_system_moss_compatible.py` | 288 | ✅ 完成 | MOSS 兼容的权重管理器 |
| `objective_system_v2.py` | 312 | ✅ 完成 | 增强版四目标系统 |
| `real_world_72h_experiment.py` | 538 | ✅ 完成 | 真实世界实验脚本 |
| `llm_quota_monitor.py` | 156 | ✅ 完成 | LLM 配额监控 |

**核心创新**:

1. **数据驱动的状态判定**
```python
# 多指标综合评分
overall_score = (resource_quota * 0.7 + (1 - error_rate) * 0.3)
# 4 状态判定
if overall_score < 0.30: state = CRISIS
elif overall_score < 0.65: state = CONCERNED
elif overall_score < 0.85: state = NORMAL
else: state = GROWTH
```

2. **审计日志链式哈希**
```python
# 每次权重更新都记录审计哈希
data = f"{self.audit_hash_chain}{self.weights}{time.time()}"
self.audit_hash_chain = hashlib.sha256(data.encode()).hexdigest()
```

3. **边界保护与归一化**
```python
# 权重边界保护
for k in self.weights:
    self.weights[k] = max(self.min_weights[k], 
                         min(self.max_weights[k], self.weights[k]))
# 归一化（确保总和=1.0）
total = sum(self.weights.values())
for k in self.weights:
    self.weights[k] /= total
```

---

## 🔧 改进方案

### 方案 A: 保守改进（推荐 Phase 1）

**目标**: 保留 v3 核心架构，集成 mves 分支的状态判定和审计机制

**改进点**:

1. **集成数据驱动状态判定**
```python
# 替换原有的单一资源判定
class StateDecisionModel:
    def __init__(self):
        self.indicators = {
            'resource_quota': {'weight': 0.35, 'thresholds': {...}},
            'resource_usage': {'weight': 0.20, 'thresholds': {...}},
            'error_rate': {'weight': 0.15, 'thresholds': {...}},
            'system_uptime': {'weight': 0.10, 'thresholds': {...}},
            'api_success_rate': {'weight': 0.10, 'thresholds': {...}},
            'knowledge_growth': {'weight': 0.10, 'thresholds': {...}}
        }
    
    def calculate_state_scores(self, state: SystemState) -> Dict[str, float]:
        # 计算各状态匹配分数
        ...
```

2. **添加审计日志**
```python
# 在 calculate_state() 中添加
self.audit_hash_chain = self._update_audit_hash(
    self.audit_hash_chain, 
    {'state': state, 'weights': weights}
)
```

3. **改进权重更新逻辑**
```python
# 从单一资源触发 → 多指标触发
def update_weights(self, state: Dict, objective_scores: Dict):
    # 资源触发
    if state['resource_ratio'] < 0.3:
        self.weights['survival'] += 0.1
    
    # 结果触发（基于目标评分）
    if objective_scores['curiosity'] > 0.8:
        self.weights['curiosity'] += 0.05
    
    # 时间触发
    if state['elapsed_hours'] > 48:
        self.weights['influence'] += 0.05
    
    # 归一化
    total = sum(self.weights.values())
    for k in self.weights:
        self.weights[k] /= total
```

**工作量**: 4-6 小时  
**风险**: 低  
**收益**: 
- ✅ 状态判定更准确
- ✅ 审计日志完整
- ✅ 向后兼容 v3 架构

---

### 方案 B: 激进改进（推荐 Phase 2）

**目标**: 完全重构实验脚本，采用 mves 分支的完整架构

**改进点**:

1. **使用 ObjectiveWeightManager**
```python
# 替换原有的权重计算
from objective_system_moss_compatible import ObjectiveWeightManager, SystemState

# 初始化
self.weight_manager = ObjectiveWeightManager()

# 在每次迭代中更新
system_state = SystemState(
    resource_quota=state['resource_ratio'],
    resource_usage=state['tokens_used'] / state['token_budget'],
    uptime=state['elapsed_hours'],
    error_rate=self._calculate_error_rate(),
    api_calls=self.real_api_used,
    unique_callers=self._count_unique_callers(),
    environment_entropy=self._calculate_entropy(),
    last_backup=self._get_last_backup_time()
)

current_state = self.weight_manager.update_weights(system_state)
weights = self.weight_manager.get_weights()
```

2. **集成 LLM 配额监控**
```python
from llm_quota_monitor import LLMQuotaMonitor

# 初始化
self.quota_monitor = LLMQuotaMonitor()

# 在每次 API 调用前检查
if not self.quota_monitor.check_and_record('api_call'):
    logger.warning("LLM quota exceeded, switching to simulated mode")
    # 降级到模拟模式
```

3. **改进检查点格式**
```python
# 统一数据格式（对齐主分支 integrated_data/）
checkpoint = {
    'version': 'v3_enhanced',
    'timestamp': datetime.now().isoformat(),
    'elapsed_hours': elapsed,
    'tokens_used': self.tokens_used,
    'real_api_used': self.real_api_used,
    'knowledge_acquired': len(self.knowledge_acquired),
    'action_count': len(self.action_history),
    'objective_weights': self.weight_manager.get_weights(),
    'system_state': current_state.value,
    'audit_hash': self.weight_manager.audit_hash_chain,
    'llm_quota_status': self.quota_monitor.get_status()
}
```

**工作量**: 8-12 小时  
**风险**: 中  
**收益**:
- ✅ 完整的状态判定
- ✅ 审计日志链式哈希
- ✅ LLM 配额监控
- ✅ 数据格式统一

---

### 方案 C: 完全重构（长期目标）

**目标**: 创建 v4 实验脚本，整合所有 mves 分支成果

**架构**:
```python
# moss_72h_experiment_v4.py
class MOSS72HourExperimentV4:
    def __init__(self):
        # 核心模块
        self.weight_manager = ObjectiveWeightManager()
        self.quota_monitor = LLMQuotaMonitor()
        self.state_decision = StateDecisionModel()
        
        # 真实 API
        self.wikipedia = WikipediaAPI()
        self.github = GitHubAPI()
        self.google = GoogleSearchAPI()
        
        # 审计
        self.audit_logger = AuditLogger()
    
    def run(self):
        while self.running:
            # 1. 获取系统状态
            system_state = self._get_system_state()
            
            # 2. 判定状态级别
            state_level = self.state_decision.calculate_state(system_state)
            
            # 3. 更新权重
            self.weight_manager.update_weights(system_state)
            weights = self.weight_manager.get_weights()
            
            # 4. 决策行动
            action = self._decide_action(weights, state_level)
            
            # 5. 执行行动（真实/模拟混合）
            result = self._execute_action(action)
            
            # 6. 评估目标
            scores = self._evaluate_objectives()
            
            # 7. 记录审计
            self.audit_logger.record({
                'state': state_level.value,
                'weights': weights,
                'action': action,
                'result': result,
                'scores': scores
            })
            
            # 8. 保存检查点
            if self._should_checkpoint():
                self._save_checkpoint()
```

**工作量**: 20-30 小时  
**风险**: 高  
**收益**:
- ✅ 完整的四目标动态系统
- ✅ 数据驱动状态判定
- ✅ 完整审计日志
- ✅ LLM 配额管理
- ✅ 可整合到主分支 integrated_data/

---

## 📋 实施计划

### Phase 1: 保守改进（本周）

**目标**: 集成状态判定和审计日志

**任务**:
1. ✅ 复制 `objective_system_moss_compatible.py` 到主分支
2. ⏳ 修改 `calculate_state()` 使用数据驱动判定
3. ⏳ 添加审计日志
4. ⏳ 测试改进后的脚本
5. ⏳ 运行 24h 验证实验

**时间**: 4-6 小时  
**负责人**: mves-integration 团队

---

### Phase 2: 激进改进（下周）

**目标**: 完全集成 mves 分支架构

**任务**:
1. ⏳ 集成 `ObjectiveWeightManager`
2. ⏳ 集成 `LLMQuotaMonitor`
3. ⏳ 改进检查点格式
4. ⏳ 数据整合到 `integrated_data/`
5. ⏳ 运行 72h 完整实验

**时间**: 8-12 小时  
**负责人**: mves-integration 团队 + 主分支维护者

---

### Phase 3: 完全重构（下月）

**目标**: 创建 v4 实验脚本

**任务**:
1. ⏳ 设计 v4 架构
2. ⏳ 实现核心模块
3. ⏳ 完整测试
4. ⏳ 运行对比实验（v3 vs v4）
5. ⏳ 发表论文

**时间**: 20-30 小时  
**负责人**: 联合团队

---

## 📊 预期改进效果

### 状态判定准确性

| 版本 | 指标数量 | 判定准确率 | 改进 |
|------|---------|-----------|------|
| v3（当前） | 1（资源） | ~70% | - |
| v3-enhanced | 6 | ~85% | +15% |
| v4 | 6+ | ~90% | +20% |

### 权重动态性

| 版本 | 触发条件 | 变化频率 | 科学价值 |
|------|---------|---------|---------|
| v3（当前） | 资源 | 低 | ⭐⭐ |
| v3-enhanced | 资源 + 结果 | 中 | ⭐⭐⭐ |
| v4 | 多指标 + 自修改 | 高 | ⭐⭐⭐⭐⭐ |

### 数据可整合性

| 版本 | 数据格式 | 审计日志 | 可整合到 integrated_data/ |
|------|---------|---------|-------------------------|
| v3（当前） | 部分兼容 | ❌ | 🟡 部分 |
| v3-enhanced | 兼容 | ✅ | ✅ 是 |
| v4 | 完全兼容 | ✅ | ✅ 是 |

---

## 📁 相关文件

**mves 分支成果**:
```
mves-integration/experiments/
├── objective_system_moss_compatible.py  ✅ 可集成
├── objective_system_v2.py                ✅ 备选
├── llm_quota_monitor.py                  ✅ 可集成
└── real_world_72h_experiment.py          📝 参考
```

**主分支文件**:
```
experiments/
├── moss_72h_experiment_v3.py             📝 待改进
├── integrated_data/                      ✅ 目标整合位置
└── docs/
    └── REAL_INTERNET_EXPERIMENT_DESIGN.md ✅ 参考
```

---

## 🎯 建议

**立即行动**:

1. 🔴 **采用方案 A（保守改进）**
   - 风险低，收益高
   - 保留 v3 核心架构
   - 集成状态判定和审计

2. 🔴 **本周内完成 Phase 1**
   - 4-6 小时工作量
   - 运行 24h 验证实验
   - 对比改进前后数据

3. 🟡 **规划 Phase 2**
   - 与主分支维护者沟通
   - 确定数据整合方案
   - 准备 72h 完整实验

---

## 📝 总结

**mves 分支的核心价值**:
1. ✅ 数据驱动的状态判定模型
2. ✅ 完整的审计日志系统
3. ✅ LLM 配额监控机制
4. ✅ 边界保护与归一化

**主分支 v3 的优势**:
1. ✅ 成熟的实验架构
2. ✅ 真实 API 混合调用
3. ✅ 自适应行动频率
4. ✅ 已验证的稳定性

**改进方案的核心**:
- 保留 v3 优势 ✅
- 集成 mves 创新 ✅
- 提升科学价值 ✅
- 确保向后兼容 ✅

---

**提案完成时间**: 2026-03-30 17:56 GMT+8  
**提案状态**: 待审核  
**建议优先级**: Phase 1（本周）
