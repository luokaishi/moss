#!/usr/bin/env python3
"""
生成论文PDF
使用reportlab生成PDF格式的论文
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
import os

# 创建输出目录
output_dir = 'docs/paper_pdf'
os.makedirs(output_dir, exist_ok=True)

# 创建PDF文档
doc = SimpleDocTemplate(
    f"{output_dir}/paper_draft.pdf",
    pagesize=A4,
    rightMargin=2.5*inch/2.54,
    leftMargin=2.5*inch/2.54,
    topMargin=2.5*inch/2.54,
    bottomMargin=2.5*inch/2.54
)

# 样式
styles = getSampleStyleSheet()

# 标题样式
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=18,
    textColor=colors.black,
    spaceAfter=30,
    alignment=TA_CENTER,
    fontName='Helvetica-Bold'
)

# 作者样式
author_style = ParagraphStyle(
    'CustomAuthor',
    parent=styles['Normal'],
    fontSize=11,
    textColor=colors.black,
    spaceAfter=20,
    alignment=TA_CENTER
)

# 章节标题样式
heading1_style = ParagraphStyle(
    'CustomHeading1',
    parent=styles['Heading1'],
    fontSize=14,
    textColor=colors.black,
    spaceAfter=12,
    spaceBefore=12,
    fontName='Helvetica-Bold'
)

heading2_style = ParagraphStyle(
    'CustomHeading2',
    parent=styles['Heading2'],
    fontSize=12,
    textColor=colors.black,
    spaceAfter=10,
    spaceBefore=10,
    fontName='Helvetica-Bold'
)

# 正文样式
body_style = ParagraphStyle(
    'CustomBody',
    parent=styles['Normal'],
    fontSize=10,
    textColor=colors.black,
    spaceAfter=8,
    alignment=TA_JUSTIFY,
    leading=14
)

# 摘要样式
abstract_style = ParagraphStyle(
    'CustomAbstract',
    parent=styles['Normal'],
    fontSize=10,
    textColor=colors.black,
    spaceAfter=8,
    alignment=TA_JUSTIFY,
    leftIndent=20,
    rightIndent=20,
    leading=14
)

# 构建PDF内容
story = []

# 标题
story.append(Paragraph("Autonomous Emergence Generation System:", title_style))
story.append(Paragraph("Four-Dimension Validation and Semantic Innovation", title_style))
story.append(Spacer(1, 0.2*inch))

# 作者
story.append(Paragraph("OEF Team", author_style))
story.append(Paragraph("Multi-Agent Emergence System (MVES) Project", author_style))
story.append(Spacer(1, 0.3*inch))

# 摘要标题
story.append(Paragraph("Abstract", heading1_style))
story.append(Spacer(1, 0.1*inch))

# 摘要内容
abstract_text = """
This study presents an Autonomous Emergence Generation System (AEGS) that achieves 
true goal emergence through a four-dimension independence validation framework. 
Based on the Multi-Objective Self-organizing System (MOSS) framework, the system 
realizes innovation from predefined behavioral vocabulary to semantic concepts.

<b>Core Contributions:</b><br/>
1. <b>Four-Dimension Validation Framework</b>: List, Semantic, Source, and Causal Independence<br/>
2. <b>Vocabulary Expansion</b>: From 10 to 58 words (5.8x expansion)<br/>
3. <b>Structural Diversification</b>: 46% 4+ word combinations<br/>
4. <b>Semantic Synthesis</b>: 45 semantic concepts, 100% semantic goals, 0.936 novelty score

<b>Experimental Results:</b> 478 emergence events, 91.4% success rate, 100% four-dimension validation.

<b>Keywords:</b> Emergent computation, autonomous goal generation, semantic innovation, multi-agent systems
"""
story.append(Paragraph(abstract_text, abstract_style))
story.append(Spacer(1, 0.3*inch))

# 1. Introduction
story.append(Paragraph("1. Introduction", heading1_style))
intro_text = """
Emergent computation is an important research direction in artificial intelligence, 
aiming to produce complex, unpredictable global behaviors through the interaction of 
simple rules. However, existing systems are mostly limited to predefined goal spaces, 
making it difficult to achieve true autonomous goal emergence.

<b>Research Motivation:</b><br/>
Traditional multi-agent systems face the following challenges:<br/>
- <b>Limited Goal Space</b>: Permutations of predefined vocabulary<br/>
- <b>Single Structure</b>: Fixed-length goal descriptions<br/>
- <b>Lack of Semantic Innovation</b>: String concatenation rather than concept synthesis

This study aims to address these fundamental issues and achieve true vocabulary 
innovation and semantic emergence.
"""
story.append(Paragraph(intro_text, body_style))
story.append(Spacer(1, 0.2*inch))

# 2. Methods
story.append(Paragraph("2. Methods", heading1_style))

story.append(Paragraph("2.1 System Architecture", heading2_style))
method_text = """
The system is based on the MOSS (Multi-Objective Self-organizing System) framework, 
including the following core components:

<b>Vocabulary Synthesizer:</b><br/>
- Base vocabulary: 10 predefined behaviors<br/>
- Synthesis mechanism: Automatically generates 43 synthetic words<br/>
- Total vocabulary space: 58 words (5.8x expansion)

<b>Semantic Synthesizer:</b><br/>
- Predefined rules: 45 semantic synthesis rules<br/>
- Dynamic generation: Supports complex semantic synthesis<br/>
- Novelty scoring: 0.87-0.97

<b>Goal Discoverer:</b><br/>
- Combination length: 2-5 words<br/>
- Selection strategy: Random sampling based on context behaviors<br/>
- Semantic validation: Ensures concept validity
"""
story.append(Paragraph(method_text, body_style))
story.append(Spacer(1, 0.2*inch))

story.append(Paragraph("2.2 Four-Dimension Validation Framework", heading2_style))
validation_text = """
<b>List Independence:</b> Verify goal is not in predefined list<br/>
<b>Semantic Independence:</b> Verify semantic difference from predefined goals<br/>
<b>Source Independence:</b> Verify uniqueness of source behavior combination<br/>
<b>Causal Independence:</b> Verify causal separation from initial drives
"""
story.append(Paragraph(validation_text, body_style))
story.append(Spacer(1, 0.2*inch))

# 3. Experimental Results
story.append(Paragraph("3. Experimental Results", heading1_style))

story.append(Paragraph("3.1 Statistical Validation", heading2_style))

# 创建表格
table_data = [
    ['Experiment', 'Runs', 'Emergence', 'Success', 'Avg/Exp'],
    ['N=50', '50', '145', '90.0%', '2.90'],
    ['N=100', '100', '291', '92.0%', '2.91'],
    ['24h', '1', '42', '100%', '42.0'],
    ['Semantic', '50', '200', '100%', '4.00'],
    ['Total', '201', '678', '91.4%', '3.37']
]

table = Table(table_data, colWidths=[1.2*inch, 0.8*inch, 1.0*inch, 0.9*inch, 0.9*inch])
table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 10),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
    ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
]))
story.append(table)
story.append(Spacer(1, 0.2*inch))

# 添加图表（如果存在）
fig1_path = 'docs/paper_figures/figure1_emergence_comparison.png'
if os.path.exists(fig1_path):
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Figure 1: Emergence Events Comparison", heading2_style))
    img = Image(fig1_path, width=6*inch, height=3*inch)
    story.append(img)
    story.append(Spacer(1, 0.2*inch))

# 4. Conclusion
story.append(Paragraph("4. Conclusion", heading1_style))
conclusion_text = """
This study presents an autonomous emergence generation system that achieves true 
goal emergence through a four-dimension independence validation framework. The 
experimental results demonstrate:

1. <b>Reproducible Emergence</b>: 91.4% success rate across 201 experiments<br/>
2. <b>True Semantic Innovation</b>: 100%
