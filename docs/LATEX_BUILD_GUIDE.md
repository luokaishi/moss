# ICLR投稿论文编译指南

## 论文文件

- **LaTeX源文件**: `docs/paper_simple.tex`
- **Markdown版本**: `docs/paper_with_llm_verification.md` (供参考)
- **最终检查清单**: `docs/ICLR_FINAL_CHECKLIST.md`

## 本地编译步骤

### 方法1: 使用pdflatex (推荐)

```bash
cd docs
pdflatex paper_simple.tex
pdflatex paper_simple.tex  # 运行两次以解决引用
```

### 方法2: 使用latexmk (自动处理依赖)

```bash
cd docs
latexmk -pdf paper_simple.tex
```

### 方法3: 使用Overleaf (在线)

1. 访问 https://www.overleaf.com
2. 创建新项目 → 上传 `.tex` 文件
3. 自动编译生成PDF

## 依赖包

论文使用的LaTeX包：
- `amsmath, amssymb, amsfonts` - 数学公式
- `graphicx` - 图片支持
- `hyperref` - 超链接
- `booktabs` - 专业表格
- `geometry` - 页面边距
- `lipsum` - 占位文本（可删除）

## 匿名化处理 (双盲审稿)

提交前需要删除/匿名化以下内容：

1. **作者信息** (第8-11行):
```latex
\author{
  Cash$^{1*}$ \and Fuxi$^{2*}$\\[0.5em]
  \small $^1$Independent Researcher\\
  \small $^2$AI Research Assistant\\[0.3em]
  \small $^*$Equal contribution
}
```
改为:
```latex
\author{Anonymous}
```

2. **GitHub链接**: 使用匿名版本或临时隐藏

3. **致谢**: 如有致谢部分需删除

4. **自引**: 使用第三人称描述

## 提交前检查清单

- [ ] PDF页数 ≤ 8页 (正文+参考文献)
- [ ] 字体大小: 10pt
- [ ] 边距: 1英寸
- [ ] 作者已匿名化
- [ ] 所有图表清晰可见
- [ ] 参考文献格式统一

## 生成最终提交文件

```bash
# 1. 编译匿名版本
pdflatex paper_simple_anonymous.tex

# 2. 重命名为ICLR提交格式
mv paper_simple_anonymous.pdf moss_iclr_2027_submission.pdf

# 3. 准备补充材料ZIP
cd ..
zip -r supplementary_materials.zip \
  core/ agents/ sandbox/ integration/ tests/ \
  README.md requirements.txt Dockerfile
```

## OpenReview提交流程

1. 访问 https://openreview.net/group?id=ICLR.cc/2027/Workshop
2. 选择 **AI Safety and Alignment** Workshop
3. 填写元数据:
   - Title: MOSS: Multi-Objective Self-Driven System for Artificial Autonomous Evolution
   - Abstract: (复制自论文)
   - Keywords: Self-driven AI, Multi-objective optimization, Autonomous evolution, Intrinsic motivation, AI safety
4. 上传PDF文件
5. 上传补充材料ZIP (可选)
6. 确认提交

## 联系方式

如有问题，请联系: 64480094@qq.com

---

**最后更新**: 2026-03-10
