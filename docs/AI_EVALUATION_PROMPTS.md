# MOSS项目AI评估提示词集合
## 用于外部AI（ChatGPT/Claude/Gemini）评估MOSS项目

---

## 提示词1：架构设计评估

```
你是一位资深AI系统架构师， specializing in multi-agent systems and autonomous AI.

请审查以下MOSS项目架构设计：

【项目背景】
MOSS (Multi-Objective Self-Driven System) 是一个赋予AI代理自驱力的理论框架，通过内在目标（生存、好奇心、影响力、自我优化）实现自主进化。

【核心创新】
1. 9维Purpose系统：D1-D4（基础目标）+ D5-D6（个体维度）+ D7-D8（社交维度）+ D9（自生成意义）
2. 自生成Purpose：Agent自主回答"Why do I exist?"
3. 动态权重演化：Purpose向量实时调整行为优先级

【代码位置】
https://github.com/luokaishi/moss/blob/main/v4/phase2/src/communication.py
https://github.com/luokaishi/moss/blob/main/v4/phase2/src/orchestrator.py

【评估请求】
请分析：
1. 架构设计的合理性和可扩展性
2. 潜在的技术风险或瓶颈
3. 与现有RL/MAS方案相比的独特价值
4. 改进建议（3-5条具体建议）

请给出详细的技术评估报告。
```

---

## 提示词2：实验结果分析

```
你是一位AI研究科学家，specializing in emergent behavior and complex systems.

请分析以下实验结果：

【实验设计】
Run 4.x Series: 三个独立实验验证Purpose演化可重复性
- Run 4.2: 4,320,000 steps, 初始Purpose=Survival, 终点=Influence
- Run 4.3: 2,880,000 steps, 初始Purpose=Curiosity, 终点=Influence  
- Run 4.4: 2,880,000 steps, 探索率=20%, 终点=Influence

【关键发现】
1. 所有实验最终都收敛到Influence（3/3验证）
2. 初始Purpose影响路径但不影响终点
3. 高探索率(20%)延迟但不阻止收敛

【报告位置】
https://github.com/luokaishi/moss/blob/main/experiments/analysis/RUN_4_SERIES_FINAL_REPORT.md

【分析请求】
1. 这个结果在复杂系统领域的意义
2. 可能的理论解释（吸引子动力学？）
3. 实验设计的局限性
4. 下一步应该验证什么假设

请给出学术视角的深度分析。
```

---

## 提示词3：商业潜力评估

```
你是一位AI产品策略专家，有丰富商业化经验。

请评估以下产品的商业潜力：

【产品概念】
MOSS DevOps Assistant - "自进化的代码守护者"
- 自动PR审查（基于Purpose选择审查重点）
- 智能Bug修复（主动发现+自动修复）
- 文档同步（代码变更自动更新文档）
- 7×24自主运行（不依赖人工指令）

【定价策略】
- Free: 1个仓库，基础功能
- Pro: $29/月，自动修复，24h监控
- Team: $99/月，多Agent协作，SLA保障

【MVP设计文档】
https://github.com/luokaishi/moss/blob/main/v4/phase2/docs/MVP_DESIGN.md

【评估请求】
1. 目标市场（TAM/SAM/SOM估算）
2. 与GitHub Copilot等竞品的差异化
3. 可能的商业模式（授权/SaaS/开源捐赠）
4. 风险与挑战（3个主要风险）
5. go-to-market策略建议

请给出务实的商业评估。
```

---

## 提示词4：论文写作辅助

```
你是一位NeurIPS/ICLR审稿人，熟悉AI论文写作。

请帮我完善以下论文段落（关于MOSS项目）：

【段落主题】
"Purpose Evolution Reproducibility" - 解释为什么三个独立实验都收敛到Influence

【实验数据】
- 实验1: 初始Survival → 路径S→C→I → 终点Influence
- 实验2: 初始Curiosity → 路径C→S→I → 终点Influence
- 实验3: 高探索率 → 延迟收敛 → 终点Influence

【写作目标】
1. 用学术语言阐述"终点决定论"
2. 引用复杂系统/动力学相关文献
3. 讨论与纳什均衡的关系
4. 指出对AI安全的影响（可预测性）

【要求】
- 约500字
- 适合放在Discussion部分
- 包含2-3个引用占位符[1][2]

请生成可直接使用的论文段落。
```

---

## 提示词5：代码审查请求

```
你是一位Python代码审查专家，注重代码质量和可维护性。

请审查以下代码文件：

【文件】v4/phase2/src/communication.py
【代码URL】https://raw.githubusercontent.com/luokaishi/moss/main/v4/phase2/src/communication.py

【审查重点】
1. 代码结构和组织（是否符合Python最佳实践）
2. 类型提示和文档字符串
3. 潜在的性能问题
4. 错误处理是否完善
5. 安全性考虑（反序列化、信任验证）

【输出格式】
- 严重问题（Critical）: 
- 建议改进（Suggestions）:
- 优点（Strengths）:

请给出具体的代码审查报告，包含行号引用。
```

---

## 使用建议

### 如何获取最佳效果

1. **给ChatGPT Plus (GPT-4)**
   - 直接粘贴完整提示词
   - 可以上传代码文件截图
   - 支持长对话追问

2. **给Claude (Claude 3)**
   - 特别适合提示词2和4（学术分析）
   - 擅长长文本和深度推理
   - 可以处理整个报告文件

3. **给Gemini (Gemini Pro)**
   - 适合提示词3（商业评估）
   - 可以联网获取最新市场信息
   - 多模态（可分析图表）

4. **对比策略**
   - 同一个问题问多个AI
   - 整合不同AI的建议
   - 找出共识点和分歧点

### 追问策略

获得初步回答后，可以继续问：
- "请详细解释第3点"
- "能否提供具体的代码示例？"
- "这个建议的实施难度如何？"
- "有哪些相关文献支持这个观点？"

---

## 预期输出示例

每个提示词预期获得：
- 深度分析（不仅是表面评价）
- 具体建议（可执行的行动）
- 潜在风险（提前预警）
- 改进方向（下一步优化）

---

*提示词版本：v1.0*
*适用：ChatGPT-4, Claude 3, Gemini Pro*
