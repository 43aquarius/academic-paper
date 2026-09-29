#!/usr/bin/env python3
"""合并封面与正文，写入元数据，输出最终 Novelty Audit 报告。"""
from pypdf import PdfReader, PdfWriter

A4_W, A4_H = 595.28, 841.89

def normalize_page_to_a4(page):
    box = page.mediabox
    w, h = float(box.width), float(box.height)
    if abs(w - A4_W) > 0.3 or abs(h - A4_H) > 0.3:
        page.scale_to(A4_W, A4_H)
    return page

writer = PdfWriter()
cover_page = normalize_page_to_a4(PdfReader('cover.pdf').pages[0])
writer.add_page(cover_page)
for page in PdfReader('main.pdf').pages:
    writer.add_page(page)

writer.add_metadata({
    '/Title': 'Sieve 拒稿后重构·第一阶段：Novelty 审计报告',
    '/Author': 'Z.ai',
    '/Creator': 'Z.ai PDF Workbench (Tectonic + Playwright)',
    '/Subject': 'IP&M 拒稿后的文献新颖性审计：2023-2026 上下文选择与压缩方法七维对比，Sieve 增量分析与论文 v2 重构方案',
})

with open('Novelty_Audit_Report.pdf', 'wb') as f:
    writer.write(f)

r = PdfReader('Novelty_Audit_Report.pdf')
print(f'final pages: {len(r.pages)}')
import os
print(f'size: {os.path.getsize("Novelty_Audit_Report.pdf")/1024:.1f} KiB')
