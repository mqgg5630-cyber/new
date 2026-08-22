#!/usr/bin/env python3
"""
示例 2：arXiv 日报 / 周报生成（纯脚本，0 AI、0 API key）
每天定时抓取指定关键词的最新论文，生成摘要 Markdown + Word 周报。

用法：
    pip install python-docx
    python3 examples/daily_arxiv_digest.py --query "large language model" --days 1

配合 cron（Linux/macOS）每天 8 点自动跑：
    0 8 * * * cd /path/to/project && python3 examples/daily_arxiv_digest.py >> digest.log 2>&1
"""
import argparse
import datetime
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from docx import Document

ATOM_NS = {"a": "http://www.w3.org/2005/Atom"}


def fetch_arxiv(query: str, max_results: int = 20) -> list[dict]:
    """调 arXiv 公开 API（无需 key）。"""
    url = (
        "http://export.arxiv.org/api/query?"
        + urllib.parse.urlencode(
            {
                "search_query": f"all:{query}",
                "sortBy": "submittedDate",
                "sortOrder": "descending",
                "max_results": max_results,
            }
        )
    )
    with urllib.request.urlopen(url, timeout=30) as resp:
        root = ET.fromstring(resp.read())
    papers = []
    for entry in root.findall("a:entry", ATOM_NS):
        title = (entry.findtext("a:title", "", ATOM_NS) or "").strip().replace("\n", " ")
        link = entry.findtext("a:id", "", ATOM_NS)
        published = entry.findtext("a:published", "", ATOM_NS)
        papers.append({"title": title, "link": link, "published": published[:10]})
    return papers


def save_markdown(papers: list[dict], date: str, path: str) -> None:
    lines = [f"# arXiv 日报 {date}", ""]
    for i, p in enumerate(papers, 1):
        lines.append(f"{i}. {p['title']}  \n   {p['link']}（{p['published']}）")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def save_docx(papers: list[dict], date: str, path: str) -> None:
    doc = Document()
    doc.add_heading(f"arXiv 日报 {date}", level=1)
    for i, p in enumerate(papers, 1):
        doc.add_paragraph(f"{i}. {p['title']}", style="List Bullet")
        doc.add_paragraph(f"链接：{p['link']}（发布于 {p['published']}）")
    doc.save(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="arXiv 日报生成器（无 AI）")
    parser.add_argument("--query", default="large language model", help="检索关键词")
    parser.add_argument("--days", type=int, default=1, help="只看最近 N 天（默认1天）")
    parser.add_argument("--max-results", type=int, default=20)
    parser.add_argument("--out", default=".", help="输出目录")
    args = parser.parse_args()

    date = datetime.date.today()
    papers = fetch_arxiv(args.query, args.max_results)
    if args.days > 0:
        cutoff = (datetime.date.today() - datetime.timedelta(days=args.days)).isoformat()
        papers = [p for p in papers if p["published"] >= cutoff]

    md_path = f"{args.out}/arxiv_daily_{date}.md"
    docx_path = f"{args.out}/arxiv_daily_{date}.docx"
    save_markdown(papers, date, md_path)
    save_docx(papers, date, docx_path)
    print(f"[OK] {len(papers)} 篇论文 -> {md_path}, {docx_path}")


if __name__ == "__main__":
    main()
