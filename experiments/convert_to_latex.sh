#!/bin/bash
# 论文格式转换脚本
# 将Markdown转换为LaTeX/PDF

echo "=== 论文格式转换 ==="
echo ""

# 检查pandoc
if ! command -v pandoc &> /dev/null; then
    echo "⚠️  pandoc未安装"
    echo "安装命令: sudo apt-get install pandoc texlive-latex-base texlive-fonts-recommended"
    exit 1
fi

# 创建输出目录
mkdir -p docs/paper_pdf

echo "📄 转换论文..."
pandoc docs/PAPER_DRAFT.md \
    -o docs/paper_pdf/paper_draft.pdf \
    --pdf-engine=xelatex \
    -V CJKmainfont="Noto Sans CJK SC" \
    -V geometry:margin=2.5cm \
    -V fontsize=11pt \
    --toc \
    --toc-depth=2 \
    -N \
    2>&1 | tail -5

if [ $? -eq 0 ]; then
    echo "✅ PDF生成成功: docs/paper_pdf/paper_draft.pdf"
else
    echo "⚠️  PDF生成失败，尝试纯文本转换..."
    pandoc docs/PAPER_DRAFT.md -o docs/paper_pdf/paper_draft.tex --standalone
    echo "✅ LaTeX生成成功: docs/paper_pdf/paper_draft.tex"
fi

echo ""
echo "📊 复制图表..."
if [ -d "docs/paper_figures" ]; then
    cp -r docs/paper_figures docs/paper_pdf/
    echo "✅ 图表已复制"
fi

echo ""
echo "🎉 格式转换完成！"
echo "输出目录: docs/paper_pdf/"
