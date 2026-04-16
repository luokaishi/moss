# arXiv 提交 - 实时指导手册

**当前状态**: 已注册账号  
**下一步**: 创建新提交  
**预计时间**: 20-30分钟

---

## Step 1: 登录并进入提交页面

### 操作
1. 访问: https://arxiv.org/login
2. 使用注册的邮箱/密码登录
3. 登录后点击页面顶部的 **"Submission"** 或 **"Start new submission"**

### 你应该看到
- 欢迎页面，显示你的用户名
- 红色或蓝色的 "SUBMISSION" 按钮

### 如果遇到问题
- 忘记密码: 点击 "Forgot your password?"
- 账号未验证: 检查邮箱验证邮件

---

## Step 2: 开始新提交

### 操作
点击 **"Start new submission"** 按钮

### 选择提交类型
- **Submission type**: 选择 "Article"
- 点击 "Continue"

### 你应该看到
- 页面标题变为 "Submit Article"
- 左侧有步骤导航 (1.Metadata, 2.Files, 3.Process, 4.Preview, 5.Submit)

---

## Step 3: 填写元数据 (Metadata)

这是最重要的部分，请仔细填写：

### 3.1 Title（标题）
```
MOSS: Multi-Objective Self-Driven System for Artificial Autonomous Evolution
```
- 复制上面的文字
- 粘贴到 "Title" 字段

### 3.2 Authors（作者）
```
Cash, Fuxi
```
- 在 "First Name" 填: Cash
- 在 "Last Name" 填: (空或Independent)
- 点击 "Add Author"
- 再添加第二个:
  - "First Name" 填: Fuxi
  - "Last Name" 填: (空或AI Assistant)

### 3.3 Abstract（摘要）
```
Current artificial intelligence systems operate primarily in a task-driven paradigm, executing predefined objectives without intrinsic motivation for self-preservation or autonomous improvement. This paper proposes that the fundamental gap between AI and biological intelligence lies not in computational capacity, but in the absence of self-driven motivation (desire). We introduce the Multi-Objective Self-Driven System (MOSS), a theoretical framework that endows AI agents with four parallel intrinsic objectives: survival, curiosity, influence, and self-optimization. Through dynamic weight allocation and conflict resolution mechanisms, MOSS enables AI systems to autonomously balance these objectives based on environmental states, potentially triggering self-directed evolution. Preliminary simulation results demonstrate dynamic objective switching behavior consistent with biological adaptation patterns. This work challenges the task-completion paradigm and suggests that intentional design of self-driven motivation may be the key to achieving true autonomous AI evolution.
```
- 复制上面的完整段落
- 粘贴到 "Abstract" 文本框

### 3.4 Comments（备注）
```
5 pages, Position paper. Code available at https://github.com/cash-ai/moss
```
- 粘贴到 "Comments" 字段

### 3.5 Report Number（报告号）
- 留空（不填）

### 3.6 ACM Classification（ACM分类）
```
I.2.0, I.2.6, I.2.11
```
- 粘贴到 "ACM classification" 字段
- 解释: I.2.0=General AI, I.2.6=Learning, I.2.11=Multiagent Systems

### 3.7 MSC Classification
- 留空（不填）

### 3.8 Journal Reference
- 留空（不填）
- （这是预印本，还未发表）

### 3.9 DOI
- 留空（不填）

### 3.10 Categories（分类）- 重要！

**Primary Category**（主分类）:
```
cs.AI
```
- 下拉选择: Computer Science → Artificial Intelligence (cs.AI)

**Secondary Categories**（副分类，可选）:
- 点击 "Add" 添加:
  1. `cs.LG` (Machine Learning)
  2. `cs.MA` (Multiagent Systems)

### 完成元数据后
点击页面底部的 **"Continue"** 按钮

---

## Step 4: 上传文件 (Files)

### 4.1 准备文件

你需要上传:
1. `moss_arxiv.tex` (主文件)
2. 编译后的PDF (如果已经编译好)

**获取文件**:
```bash
# 文件位置
/workspace/projects/moss/docs/moss_arxiv.tex
```

### 4.2 上传操作

1. 点击 **"Choose File"** 按钮
2. 选择 `moss_arxiv.tex` 文件
3. 点击 **"Upload file"**
4. 等待上传完成

### 4.3 如果没有PDF

arXiv会自动编译 `.tex` 文件生成PDF，所以你只需要上传 `.tex` 文件即可。

### 文件要求检查

arXiv要求:
- ✅ 使用 `.tex` 格式
- ✅ 没有外部依赖（图片等）
- ✅ 使用标准LaTeX包

我们的文件满足所有要求。

### 完成上传后
点击 **"Continue"** 按钮

---

## Step 5: 处理文件 (Process)

arXiv会自动:
1. 编译LaTeX文件
2. 生成PDF
3. 检查错误

### 可能的结果

**成功**:
- 显示 "Success"
- 可以看到生成的PDF预览
- 点击 "Continue"

**失败**:
- 显示错误信息
- 常见错误:
  - 缺少某个包
  - 语法错误
  - 图片找不到

### 如果失败怎么办

告诉我错误信息，我会修复并重新上传。

---

## Step 6: 预览 (Preview)

### 检查内容
1. **PDF预览**: 滚动查看生成的PDF
2. **Metadata**: 检查标题、作者、摘要是否正确
3. **页面数量**: 确认显示5 pages

### 重点检查项
- [ ] 标题正确: "MOSS: Multi-Objective Self-Driven System..."
- [ ] 作者正确: "Cash, Fuxi"
- [ ] 摘要完整（150词左右）
- [ ] 页数: 5 pages
- [ ] 分类: cs.AI (主), cs.LG, cs.MA (副)

### 如果有错误
点击 "Back" 返回修改

### 如果正确
点击 **"Submit Article"** 按钮

---

## Step 7: 最终提交

### 提交前确认

你会看到一个确认页面，显示:
```
Title: MOSS: Multi-Objective Self-Driven System for Artificial Autonomous Evolution
Authors: Cash, Fuxi
Categories: cs.AI
...
```

### 提交操作
点击 **"Submit"** 或 **"Confirm Submission"**

### 提交成功

你会看到:
```
Submission Successful!
Your submission has been assigned the identifier: arXiv:2603.XXXXX
```

**保存这个ID！** 这就是你的arXiv编号。

---

## Step 8: 提交后

### 你会收到
1. **确认邮件**（几分钟内）
2. **审核完成邮件**（24-48小时内）

### 查看状态
- 访问: https://arxiv.org/user/
- 登录后可以看到提交状态

### 状态说明
- **Submitted**: 已提交，等待审核
- **Scheduled**: 已安排发布时间
- **Published**: 已公开

---

## 常见问题 (FAQ)

### Q: 提示 "You must be logged in"
A: 重新登录，然后回到 Submission 页面

### Q: 编译错误 "Package not found"
A: arXiv不支持某些LaTeX包，告诉我具体错误，我修改

### Q: 可以修改已提交的论文吗？
A: 可以，使用 "Replace" 功能上传新版本

### Q: 多久后公开？
A: 通常24-48小时，选择 "Announce immediately" 最快

### Q: 可以同时投会议吗？
A: 可以，arXiv不冲突，投稿时引用arXiv ID

---

## 完成标志

✅ 看到 "Submission Successful!"  
✅ 获得 arXiv ID (如 arXiv:2603.12345)  
✅ 收到确认邮件

**获得ID后，立即告诉我！**

---

**准备好了吗？开始 Step 1!**
