#!/usr/bin/env python3
"""
md2docx.py —— 把主报告 Markdown 转成排版良好的 Word 文档。
用法：.venv-docx/bin/python tools/md2docx.py 反重力Antigravity科研办公MCP与Skills推荐.md
"""
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Pt, RGBColor

MONO = "Consolas"
CJK = "Microsoft YaHei"

INLINE_RE = re.compile(
    r"(\*\*.+?\*\*|\*[^*]+?\*|`[^`]+`|\[[^\]]+\]\([^\)]+\))"
)


def set_cjk(style_or_run, name=CJK):
    """同时设置西文字体和中文字体（python-docx 中文需要设置 eastAsia）。"""
    rPr = style_or_run.element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:eastAsia"), name)


def add_inline(paragraph, text, base_bold=False, base_italic=False):
    """解析 **bold**、*italic*、`code`、[text](url) 并写入段落。"""
    for token in INLINE_RE.split(text):
        if not token:
            continue
        if token.startswith("**") and token.endswith("**"):
            run = paragraph.add_run(token[2:-2])
            run.bold = True
            set_cjk(run)
        elif token.startswith("*") and token.endswith("*") and len(token) > 2:
            run = paragraph.add_run(token[1:-1])
            run.italic = True
            set_cjk(run)
        elif token.startswith("`") and token.endswith("`") and len(token) > 2:
            run = paragraph.add_run(token[1:-1])
            run.font.name = MONO
            run.font.size = Pt(9.5)
            set_cjk(run, MONO)
        elif token.startswith("[") and "](" in token:
            m = re.match(r"\[([^\]]+)\]\(([^\)]+)\)", token)
            if m:
                run = paragraph.add_run(m.group(1))
                run.font.color.rgb = RGBColor(0x0B, 0x57, 0xD0)
                run.underline = True
                set_cjk(run)
            else:
                run = paragraph.add_run(token)
                set_cjk(run)
        else:
            run = paragraph.add_run(token)
            if base_bold:
                run.bold = True
            if base_italic:
                run.italic = True
            set_cjk(run)


def add_code_block(doc, code: str):
    for line in code.splitlines():
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Pt(18)
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(line if line else " ")
        run.font.name = MONO
        run.font.size = Pt(8.5)
        set_cjk(run, MONO)
        # 浅灰底纹
        pPr = p._p.get_or_add_pPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:fill"), "F2F2F2")
        pPr.append(shd)


def add_table(doc, header, rows):
    table = doc.add_table(rows=1 + len(rows), cols=len(header))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, cell_text in enumerate(header):
        cell = table.rows[0].cells[j]
        cell.paragraphs[0].text = ""
        add_inline(cell.paragraphs[0], cell_text, base_bold=True)
    for i, row in enumerate(rows, start=1):
        for j, cell_text in enumerate(row):
            if j >= len(header):
                break
            cell = table.rows[i].cells[j]
            cell.paragraphs[0].text = ""
            add_inline(cell.paragraphs[0], cell_text)
    doc.add_paragraph()  # 表后空行


def is_separator(line: str) -> bool:
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    return all(re.fullmatch(r":?-{2,}:?", c) for c in cells) and len(cells) > 0


def convert(md_path: Path, out_path: Path) -> None:
    lines = md_path.read_text(encoding="utf-8").splitlines()

    doc = Document()
    # 全局默认字体
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10.5)
    set_cjk(style)

    i = 0
    in_code = False
    code_buf: list[str] = []
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if in_code:
            if stripped.startswith("```"):
                add_code_block(doc, "\n".join(code_buf))
                code_buf = []
                in_code = False
            else:
                code_buf.append(line)
            i += 1
            continue

        if stripped.startswith("```"):
            in_code = True
            i += 1
            continue

        if not stripped:
            i += 1
            continue

        if stripped == "---":
            p = doc.add_paragraph()
            pPr = p._p.get_or_add_pPr()
            pBdr = OxmlElement("w:pBdr")
            bottom = OxmlElement("w:bottom")
            bottom.set(qn("w:val"), "single")
            bottom.set(qn("w:sz"), "6")
            bottom.set(qn("w:color"), "BBBBBB")
            pBdr.append(bottom)
            pPr.append(pBdr)
            i += 1
            continue

        if stripped.startswith(">"):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Pt(18)
            add_inline(p, stripped.lstrip("> "), base_italic=True)
            i += 1
            continue

        if re.match(r"^#{1,6}\s", stripped):
            level = len(stripped) - len(stripped.lstrip("#"))
            text = stripped.lstrip("#").strip()
            # 去掉标题里的锚点链接尾巴，如 `（TL;DR）`
            text = re.sub(r"\s*<a[^>]*>.*?</a>", "", text)
            doc.add_heading(text, level=min(level, 6))
            i += 1
            continue

        if stripped.startswith("|") and "|" in stripped[1:]:
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                if not is_separator(lines[i]):
                    table_lines.append(lines[i])
                i += 1
            parsed = []
            for tl in table_lines:
                cells = [c.strip() for c in tl.strip().strip("|").split("|")]
                parsed.append(cells)
            if parsed:
                add_table(doc, parsed[0], parsed[1:])
            continue

        m_list = re.match(r"^(\s*)([-*])\s+(.*)$", line)
        m_num = re.match(r"^(\s*)(\d+)[.)]\s+(.*)$", line)
        if m_list:
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Pt(18)
            p.paragraph_format.space_after = Pt(2)
            p.add_run("•  ")
            add_inline(p, m_list.group(3))
            i += 1
            continue
        if m_num:
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Pt(18)
            p.paragraph_format.space_after = Pt(2)
            p.add_run(f"{m_num.group(2)}. ")
            add_inline(p, m_num.group(3))
            i += 1
            continue

        p = doc.add_paragraph()
        add_inline(p, stripped)
        i += 1

    doc.save(out_path)
    print(f"[OK] {out_path}")


if __name__ == "__main__":
    src = Path(sys.argv[1] if len(sys.argv) > 1 else "反重力Antigravity科研办公MCP与Skills推荐.md")
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".docx")
    convert(src, dst)
