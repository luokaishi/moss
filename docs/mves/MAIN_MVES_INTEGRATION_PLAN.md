# main ↔ mves 分支整合计划

**日期**: 2026-04-22  
**状态**: 草案  
**目标**: 整合 main 分支 LLM 引导变异与 mves 分支 AGI 架构

---

## 1. 分支现状对比

| 特性 | main (v8.1.1) | mves (v8.0.0) |
|------|---------------|---------------|
| **核心焦点** | LLM 引导代码自我修改 | 全面 AGI 架构 |
| **统计验证** | N=5 (30 代) | N=45 (50K cycles) |
| **LLM 集成** | ✅ 深度集成 (token 优化) | ❌ 未明确 |
| **驱动机制** | 间接 (fitness) | ✅ drive_competition.py |
| **实验报告** | ✅ 详细 (V81_EXPERIMENT_ANALYSIS.md) | ⚠️ 待完善 |

---

## 2. 整合优先级

### P0: 立即整合 (1-2 周)

1. **Meta-SME N=45 报告同步到 main**
   - 将 `docs/mves/PHASE2_FINAL_REPORT.md` 同步至 main
   - 补充统计分析脚本

2. **LLM Token 优化同步到 mves**
   - 将 main 的 token budget 管理集成到 mves
   - 优化 AGI 组件 LLM 调用

3. **精英保留机制双向同步**
   - main 的 elite protection → mves
   - mves 的 drive competition → main

### P1: 架构整合 (2-4 周)

4. **统一 AGI 接口**
   - 对齐 `agi/` 目录结构
   - 统一组件 API

5. **联合验证实验**
   - 设计 N=10+ 重复实验
   - multi_eval 验证

### P2: 发布准备 (4-6 周)

6. **v9.0 统一版本**
   - 合并分支或明确分工
   - 发布联合论文

---

## 3. 立即行动项

- [ ] 创建 `main-mves-sync` 分支
- [ ] 同步 N=45 统计报告到 main
- [ ] 同步 LLM token 优化到 mves
- [ ] 安排技术交流会议

---

## 4. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| 代码冲突 | 高 | 小步合并，频繁测试 |
| 实验不一致 | 中 | 统一随机种子和参数 |
| 文档滞后 | 中 | 每次合并同步更新文档 |

---

**下一步**: 待用户确认后执行 P0 任务
