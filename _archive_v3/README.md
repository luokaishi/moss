# MOSS v3.0.0

**从4维到8维：自驱力系统的维度扩展**

---

## 版本说明

| 版本 | 维度 | 状态 | 用途 |
|------|------|------|------|
| v2.0.0 | 4维 [S,C,I,O] | ✅ 已发布 | NeurIPS 2026投稿 |
| **v3.0.0** | **8维 [S,C,I,O,V,V,Oth,N]** | 🚧 开发中 | 理论探索 |

---

## 新增维度（基于ChatGPT建议）

### 第5维：Coherence（自我连续性）
- **功能**: 让系统"在改变自己时，仍然保持是同一个自己"
- **数学**: `V = -||w - w_ref||²`，EMA更新参考身份
- **效应**: 身份锁定、路径稳定、抑制漂移

### 第6维：Valence（主观偏好）
- **功能**: 让系统开始有"我在意什么"
- **数学**: `V = β·ΔM`，偏好权重β可进化
- **效应**: 性格分化、损失厌恶、非最优行为

### 第7维：Other（他者建模）
- **功能**: 区分"自己 vs 他者"
- **状态**: 🚧 开发中
- **效应**: 多主体博弈、社会互动

### 第8维：Norm（规范内化）
- **功能**: 稳定的行为约束系统
- **状态**: 🚧 开发中
- **效应**: 信任结构、声誉机制、制度萌芽

---

## 快速开始

```python
from moss.v3 import MOSSv3Agent

# 创建8维agent
agent = MOSSv3Agent(
    agent_id="test_agent",
    enable_coherence=True,  # 启用第5维
    enable_valence=True     # 启用第6维
)

# 运行决策循环
for step in range(100):
    result = agent.step()
    print(f"Step {step}: State={result['state']}, Coherence={result['coherence']}")
```

---

## 开发路线图

见 [ROADMAP.md](./ROADMAP.md)

---

## 理论背景

基于与ChatGPT的深入讨论，实现从"优化器"到"主体"到"社会系统"的完整跃迁。

详细分析见：
- `docs/chatgpt_analysis.md` - 人类角色转换
- `docs/chatgpt_analysis_part2.md` - 第5维设计
- `docs/chatgpt_analysis_part3.md` - 第6维设计
- `docs/chatgpt_analysis_part4.md` - 第8维设计

---

## 实验预测

| 预测 | 验证维度 | 预期现象 |
|------|----------|----------|
| 身份锁定 | 第5维 | 长期运行后weight稳定 |
| 性格分化 | 第6维 | 相同初始条件产生不同行为模式 |
| 非最优行为 | 第6维 | 系统选择"更喜欢"但非最优路径 |
| 信任结构 | 第8维 | 多agent环境出现稳定合作 |

---

## 引用

如果使用MOSS v3.0.0，请引用：

```bibtex
@software{moss_v3_2026,
  author = {Cash},
  title = {MOSS v3.0.0: From 4 to 8 Dimensions},
  year = {2026},
  url = {https://github.com/luokaishi/moss}
}
```

---

**状态**: 开发中 | **目标**: NeurIPS 2027 / Science子刊
