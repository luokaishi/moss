# MOSS 分支同步指南

**版本**: 1.0  
**日期**: 2026-04-25  
**适用**: main ↔ mves 双向同步

---

## 快速开始

```bash
# 1. 运行同步检测
python scripts/sync_detector.py

# 2. 查看同步报告
cat SYNC_REPORT.md

# 3. 查看同步映射表
cat sync_map.json
```

---

## 同步流程

### 每周同步检查清单

- [ ] 运行 `scripts/sync_detector.py` 检测差异
- [ ] 查看生成的 `SYNC_REPORT.md`
- [ ] 处理 P0 优先级文件
- [ ] 更新 `sync_map.json` 状态
- [ ] 提交 PR 并关联此指南

---

## Main → MVES 技术回流

### P0: Token 预算控制

```bash
# 1. 切换到 mves 分支
git checkout mves-local

# 2. 创建移植分支
git checkout -b port/token-budget-from-main

# 3. 复制文件 (从 main)
git checkout main -- moss/core/llm_cost_controller.py

# 4. 调整导入路径
# 修改: from moss.core.exceptions -> from agi.exceptions

# 5. 移动到目标位置
mv moss/core/llm_cost_controller.py agi/cost_controller.py

# 6. 提交
git add agi/cost_controller.py
git commit -m "port: Token budget controller from main"

# 7. 推送并创建 PR
git push origin port/token-budget-from-main
```

### P0: 统计验证框架

```bash
git checkout mves-local
git checkout -b port/statistical-validator-from-main
git checkout main -- moss/core/statistical_validator.py
mv moss/core/statistical_validator.py experiments/
git add experiments/statistical_validator.py
git commit -m "port: Statistical validator from main"
git push origin port/statistical-validator-from-main
```

---

## MVES → Main 组件合并

### P0: 事件驱动 Purpose

```bash
# 1. 切换到 main
git checkout main

# 2. 创建合并分支
git checkout -b merge/event-driven-from-mves

# 3. 从 mves 获取文件
git checkout mves-local -- agi/event_driven_purpose.py

# 4. 移动到 main 目录结构
mv agi/event_driven_purpose.py moss/core/

# 5. 运行测试
python -m pytest tests/ -k event_driven -v

# 6. 提交
git add moss/core/event_driven_purpose.py
git commit -m "merge: Event-driven purpose from mves v8.6"
```

---

## PR 创建规范

### PR 标题格式

```
[type]: [brief description]

types:
- port: Main → MVES 技术回流
- merge: MVES → Main 组件合并  
- resolve: 冲突解决
- sync: 一般同步
```

---

## 测试验证步骤

```bash
# 导入测试
python -c "from agi.cost_controller import LLMCostController; print('OK')"

# 运行测试
python -m pytest tests/ -v
```

---

*最后更新: 2026-04-25*
