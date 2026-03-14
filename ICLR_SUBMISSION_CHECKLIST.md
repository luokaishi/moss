# ICLR Workshop 投稿材料清单

## 主论文
- **文件**: `paper/main.tex`
- **格式**: LaTeX (article class)
- **页数**: 7 页（正文）+ 参考文献
- **最新 commit**: 9fa390f

## 生成 PDF 命令
```bash
cd /workspace/projects/moss/paper
pdflatex main.tex
bibtex main  # 如果有 .bib 文件
pdflatex main.tex
pdflatex main.tex  # 需要编译两次确保交叉引用正确
```

## 补充材料 (Supplementary Material)

### 1. 实验数据文件
- ✅ `experiments/data/longterm_6h_0311_2108_agent_current.json`
- ✅ `experiments/data/longterm_24h_0311_2108_agent_current.json`
- ✅ `experiments/weight_quantization_results_20260310_190638.json`
- ✅ `experiments/safety_test_report_20260310_220807.json`
- ✅ `v2/experiments/statistical_validation/` (15次运行结果)

### 2. 代码仓库
- **GitHub**: https://github.com/luokaishi/moss
- **Branch**: main
- **最新 commit**: 9fa390f

### 3. 图表文件
- `paper/figures/fig2_performance.png`
- `paper/figures/fig3_path_bifurcation.png`
- `paper/figures/fig4_trajectories.png`

### 4. README 文档
- 根目录 `README.md`
- `v2/README.md` (v2.0.0 详细文档)

## ICLR Workshop 投稿要求

### 格式要求
- 8 页正文（不含参考文献）
- 无限页补充材料
- LaTeX 格式
- 使用官方模板（如有）

### 当前状态检查
- [x] 8 页以内：✅ 满足（正文约 7 页）
- [x] 可复现性：✅ 所有数据文件已上传
- [x] 开源代码：✅ GitHub 仓库公开
- [x] 图表清晰：✅ 高分辨率 PNG

### 需要准备的额外材料
1. **Cover Letter**（可选，但推荐）
2. **Response to Reviewers**（如为修订版）
3. **Supplementary PDF**（补充材料汇总）

## 建议的投稿策略

### 会议选择
1. **ICLR 2027 Workshop**（如果 deadline 允许）
2. **NeurIPS 2026 Workshop**（备选）
3. **AAAI 2027**（主会，更长篇幅）

### 突出亮点
1. **Path Bifurcation**: 相同初始条件→不同策略（新颖发现）
2. **5级安全机制**: 工程实践价值
3. **统计验证**: N=15 验证稳健性
4. **完整开源**: 100% 可复现

## 投稿前最终检查清单

- [ ] PDF 生成成功
- [ ] 页数符合要求
- [ ] 图表清晰可读
- [ ] 参考文献完整
- [ ] GitHub 链接有效
- [ ] 补充材料已打包

## 生成补充材料 PDF

```bash
cd /workspace/projects/moss

# 创建补充材料目录
mkdir -p supplementary

# 复制关键文件
cp experiments/data/*.json supplementary/
cp v2/experiments/statistical_validation/summary.json supplementary/
cp paper/figures/*.png supplementary/

# 创建 README
cat > supplementary/README.md << 'EOF'
# MOSS Supplementary Materials

## Experiment Data
- `longterm_6h_0311_2108_agent_current.json`: 6h experiment raw data
- `longterm_24h_0311_2108_agent_current.json`: 24h experiment raw data
- `weight_quantization_results_20260310_190638.json`: Weight quantization results
- `safety_test_report_20260310_220807.json`: Safety mechanism test results
- `summary.json`: Statistical validation (N=15) summary

## Figures
- `fig2_performance.png`: Performance comparison
- `fig3_path_bifurcation.png`: Path bifurcation visualization
- `fig4_trajectories.png`: Weight evolution trajectories

## Code
Full code available at: https://github.com/luokaishi/moss
Commit: 9fa390f
EOF

# 打包
tar -czf moss_supplementary_materials.tar.gz supplementary/
```

## 联系信息
- **作者**: Cash, Fuxi
- **邮箱**: moss-project@github.com
- **机构**: MOSS Project Team
