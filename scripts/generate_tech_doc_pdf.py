#!/usr/bin/env python3
"""
Convert technical-documentation.md into a professional PDF using ReportLab.
"""
import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)

def md_to_pdf(md_path, pdf_path):
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1e1b4b'),
        spaceAfter=8
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#4f46e5'),
        spaceAfter=14
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=5
    )

    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor('#0f172a'),
        backColor=colors.HexColor('#f1f5f9'),
        borderColor=colors.HexColor('#cbd5e1'),
        borderWidth=0.5,
        borderPadding=4,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#1e293b'),
        leftIndent=12,
        spaceAfter=3
    )

    story = []
    
    lines = md_text.split("\n")
    in_code_block = False
    code_lines = []

    for line in lines:
        # Code blocks
        if line.strip().startswith("```"):
            if in_code_block:
                code_text = "<br/>".join(
                    line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") 
                    for line in code_lines
                )
                story.append(Paragraph(code_text, code_style))
                code_lines = []
                in_code_block = False
            else:
                in_code_block = True
                code_lines = []
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        stripped = line.strip()
        if not stripped:
            continue

        # Document Header
        if stripped.startswith("# 🏛️ Process Intelligence Engine"):
            story.append(Paragraph("Process Intelligence Engine (PIE)", title_style))
            story.append(Paragraph("Stage 2 Technical Architecture & Implementation Documentation | MODUS Challenge", subtitle_style))
            story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#4f46e5'), spaceBefore=2, spaceAfter=10))
            continue
        elif stripped.startswith("# "):
            clean = stripped[2:].strip()
            story.append(Paragraph(clean, h1_style))
            continue
        elif stripped.startswith("## "):
            clean = stripped[3:].strip()
            story.append(Paragraph(clean, h1_style))
            continue
        elif stripped.startswith("### "):
            clean = stripped[4:].strip()
            story.append(Paragraph(clean, h2_style))
            continue
        elif stripped.startswith("---"):
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e1'), spaceBefore=6, spaceAfter=8))
            continue
        elif stripped.startswith("- ") or stripped.startswith("* "):
            clean = stripped[2:].strip()
            # Basic bold conversion
            clean = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', clean)
            clean = re.sub(r'`(.*?)`', r'<font face="Courier">\1</font>', clean)
            story.append(Paragraph(f"• {clean}", bullet_style))
            continue
        elif re.match(r'^\d+\.\s', stripped):
            clean = re.sub(r'^\d+\.\s', '', stripped).strip()
            clean = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', clean)
            clean = re.sub(r'`(.*?)`', r'<font face="Courier">\1</font>', clean)
            story.append(Paragraph(f"• {clean}", bullet_style))
            continue
        elif stripped.startswith("> "):
            clean = stripped[2:].strip()
            clean = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', clean)
            quote_style = ParagraphStyle(
                'Quote_Custom', parent=body_style,
                fontName='Helvetica-Oblique', textColor=colors.HexColor('#4338ca'),
                leftIndent=15, spaceBefore=4, spaceAfter=6
            )
            story.append(Paragraph(clean, quote_style))
            continue
        elif stripped.startswith("|"):
            # Table line (skip complex parsing for now, format as text or paragraph)
            if "---" in stripped:
                continue
            cols = [c.strip() for c in stripped.split("|")[1:-1]]
            if cols:
                formatted_cols = " | ".join(cols)
                formatted_cols = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', formatted_cols)
                formatted_cols = re.sub(r'`(.*?)`', r'<font face="Courier">\1</font>', formatted_cols)
                story.append(Paragraph(f"<font color='#64748b'>[TABLE ROW]</font> {formatted_cols}", body_style))
            continue
        else:
            clean = stripped
            clean = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', clean)
            clean = re.sub(r'`(.*?)`', r'<font face="Courier">\1</font>', clean)
            clean = clean.replace("&", "&amp;")
            story.append(Paragraph(clean, body_style))

    doc.build(story)
    print(f"✓ Generated PDF: {pdf_path}")

if __name__ == "__main__":
    md_to_pdf(
        "submission/documentation/technical-documentation.md",
        "submission/documentation/technical-documentation.pdf"
    )
