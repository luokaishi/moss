# arXiv 提交流指南

## 快速提交步骤

### 1. 注册账号（2分钟）

访问: https://arxiv.org/user/register

需要：
- 邮箱（建议使用学术邮箱）
- 用户名
- 密码
- 机构信息（可选填 "Independent Researcher"）

### 2. 准备提交文件

```
submission/
├── moss_arxiv.tex      # 主文件（已准备）
├── moss_arxiv.pdf      # 编译后的PDF
└── (无需其他文件，此版本为简洁版)
```

**编译PDF**:
```bash
cd /workspace/projects/moss/docs
pdflatex moss_arxiv.tex
```

### 3. 提交表单填写

**Start New Submission**: https://arxiv.org/submit

#### Metadata

| 字段 | 填写内容 |
|------|----------|
| **Title** | MOSS: Multi-Objective Self-Driven System for Artificial Autonomous Evolution |
| **Authors** | Cash, Fuxi |
| **Abstract** | (从moss_arxiv.tex复制) |
| **Comments** | 5 pages, Position paper. Code available at https://github.com/cash-ai/moss |
| **Report Number** | (留空) |
| **ACM Class** | I.2.0, I.2.6, I.2.11 |
| **MSC Class** | (留空) |

#### Categories (最多5个)

**Primary**: `cs.AI` (Artificial Intelligence)

**Secondary**: 
- `cs.LG` (Machine Learning)
- `cs.MA` (Multiagent Systems)
- `cs.RO` (Robotics - 可选)
- `cs.CY` (Computers and Society - 可选)

#### 文件上传

1. 点击 "Choose File"
2. 选择 `moss_arxiv.tex` 和 `moss_arxiv.pdf`
3. 点击 "Add Files"
4. 点击 "Process Files"

### 4. 预览和提交

- 检查PDF预览是否正常
- 确认metadata正确
- 点击 "Submit Article"

### 5. 提交后

- **获取arXiv ID**: 格式如 `arXiv:2603.12345`
- **等待时间**: 通常24-48小时审核
- **状态查询**: https://arxiv.org/user/

---

## 时间线

| 时间 | 事件 |
|------|------|
| **今天** | 提交arXiv |
| **明天** | 获取arXiv ID，更新论文和GitHub |
| **后天** | arXiv公开，建立优先权 |

---

## 注意事项

### 重要提示

1. **License选择**: 建议选择 "arXiv.org perpetual, non-exclusive license"
   - 允许后续投稿会议/期刊
   - 保留版权

2. **版本控制**: 
   - 首次提交为 v1
   - 后续更新为 v2, v3...
   - 旧版本仍然可见

3. **与ICLR投稿的关系**:
   - arXiv不冲突ICLR投稿
   - ICLR接受arXiv预印本
   - 投稿时引用arXiv ID

### 常见问题

**Q: 需要机构邮箱吗？**  
A: 不需要，个人邮箱也可以。

**Q: 没有ORCID怎么办？**  
A: 可以留空，或现场注册（免费）。

**Q: 可以后续修改吗？**  
A: 可以，通过 "Replace" 功能上传新版本。

**Q: 多久后公开？**  
A: 通常提交后24-48小时，选择 "Announce immediately" 最快。

---

## 提交后行动

### 立即执行

1. **更新论文PDF**: 在封面添加 "arXiv:2603.XXXXX"
2. **更新GitHub README**: 添加arXiv链接
3. **社交媒体发布**: Twitter/LinkedIn宣布

### 本周内

4. **提交ICLR Workshop**: 使用arXiv ID
5. **通知相关研究者**: 邮件发送给潜在合作者
6. **申请Google Scholar索引**: 自动，但需时间

---

## 联系arXiv

如有问题：
- 帮助: https://arxiv.org/help
- 联系: https://arxiv.org/help/contact
- 状态: https://status.arxiv.org/

---

**状态**: 准备就绪，等待执行  
**优先级**: 🔴 最高（建立优先权）
