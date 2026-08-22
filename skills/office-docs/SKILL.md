---
name: office-docs
description: >
  Batch-process office files (Word .docx, Excel .xlsx/.csv, PowerPoint .pptx)
  without any MCP server: merge, clean, format, convert, and export documents,
  spreadsheets and slides using python-docx / openpyxl / python-pptx / markitdown.
  Use when the user asks to 合并文档, 处理Excel, 清洗数据, 批量改格式, 转换格式,
  生成表格, 汇总报表, or manipulate Office files in bulk.
---

# Office Docs（办公文档批处理）

**零 MCP、零 AI 依赖**：全部用本地 Python 库完成。先检查依赖：

```bash
pip install python-docx openpyxl python-pptx markitdown
```

## 常见任务模板

### 1. 合并多个 Word 文档（append 段落）

```python
from docx import Document
merged = Document()
for path in ["a.docx", "b.docx"]:
    src = Document(path)
    for para in src.paragraphs:
        merged.add_paragraph(para.text)
    # 每篇之间加分页符
    merged.add_page_break()
merged.save("merged.docx")
```

### 2. Excel 清洗 + 汇总（openpyxl）

```python
import glob
from openpyxl import load_workbook
from openpyxl import Workbook

wb_out = Workbook(); ws_out = wb_out.active
for f in glob.glob("data/*.xlsx"):
    wb = load_workbook(f, data_only=True)
    for row in wb.active.iter_rows(values_only=True):
        if row and any(v is not None for v in row):   # 跳过空行
            ws_out.append(row)
wb_out.save("all_merged.xlsx")
```

常用增强：去重（集合）、按列排序（`ws_out.append` 前排序）、
日期列统一格式（`datetime.strptime` → 固定格式字符串）。

### 3. 任意文档 → Markdown（喂给后续分析/存档）

```bash
markitdown input.docx > output.md
markitdown input.xlsx > output.md
markitdown input.pdf  > output.md
```

### 4. 批量改格式（示例：给 docx 里所有一级标题加编号）

```python
from docx import Document
doc = Document("report.docx")
for i, p in enumerate(doc.paragraphs):
    if p.style.name.startswith("Heading 1"):
        p.text = f"{i+1}. {p.text}"
doc.save("report_numbered.docx")
```

## 执行流程

1. **先列目录**：用 `ls`/`glob` 看清要处理的文件，向用户确认范围（避免误伤）
2. **写脚本 → 先跑一遍**：小批量验证输出
3. **展示结果**：报告输出文件路径 + 关键统计（处理了几行/几个文件、去重多少）
4. 用户确认后再覆盖原文件（默认输出到新文件，不覆盖）

## 注意

- 默认**只读不覆盖**：输出一律写新文件（如 `*_merged.xlsx`）
- 大 Excel 用 `read_only=True` 模式省内存
- 编码问题（中文 CSV 乱码）时指定 `encoding="utf-8-sig"` 或 `gbk`
- 这些脚本都可以独立跑（cron/双击/命令行），完全不需要 AI
