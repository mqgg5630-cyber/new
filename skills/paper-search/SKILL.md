---
name: paper-search
description: >
  Search, download, and organize academic papers from arXiv, PubMed, bioRxiv,
  Semantic Scholar, Crossref, OpenAlex and other sources. Use when the user asks
  to find / search / retrieve / download / cite academic papers, preprints,
  references or bibliographies, or to build a BibTeX list from a research topic.
  用于论文检索、下载、整理成文献清单或 BibTeX（中英文场景均适用）。
---

# Paper Search（论文检索与整理）

帮助用户检索、下载、整理学术论文。优先使用 **paper-search-mcp**（如果已配置）；
MCP 不可用时，用 arXiv/PubMed 的公开 API 兜底（不需要任何 AI 能力也能执行）。

## 第 1 步：确认可用的检索通道

按顺序探测，用第一个可用的：

1. **paper-search-mcp**（已配置时）：工具 `search_papers` / `download_papers` / `read_paper`
2. **arXiv API 兜底**（无需 key）：`http://export.arxiv.org/api/query?search_query=...`
3. **PubMed E-utilities 兜底**：`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=...`

不要向用户索要 API key 就能完成的检索，先用免费通道完成。

## 第 2 步：检索

- 关键词拆解：把用户的中文/英文需求拆成 2~4 个英文检索词，用 AND/OR/引号组合
- 常用限定：`all:` 全文 / `ti:` 标题 / `au:` 作者 / `cat:cs.AI` 分类；时间用 `submittedDate:[YYYYMMDD TO YYYYMMDD]`
- 默认返回 5~20 条；先给"摘要级"结果，用户确认后再下载 PDF

## 第 3 步：整理输出

按下面的模板输出（Markdown 表格），并按用户要求提供 BibTeX：

| # | 标题 | 第一作者 | 年份 | 期刊/预印本 | DOI/链接 | 摘要要点 |
|---|------|---------|------|------------|---------|---------|

BibTeX 模板：

```bibtex
@article{key2026,
  title  = {论文标题},
  author = {作者A and 作者B},
  journal = {arXiv preprint arXiv:xxxx.xxxxx},
  year   = {2026},
  url    = {https://arxiv.org/abs/xxxx.xxxxx}
}
```

## 第 4 步：下载与保存（用户要求时）

- 建目录 `papers/`，文件名规范：`年份-第一作者-简短标题.pdf`（如 `2026-smith-agent-memory.pdf`）
- 下载后用 `paper-search-mcp` 的 `read_paper` 或本地工具验证 PDF 可读
- 最后把 BibTeX 汇总写入 `papers/references.bib`，并生成 `papers/README.md` 清单

## 注意

- 尊重版权：优先下载 OA（开放获取）全文；付费墙论文只给 DOI 链接，不鼓励绕行
- Google Scholar 有反爬，结果不稳定时提示用户可配 `PAPER_SEARCH_MCP_GOOGLE_SCHOLAR_PROXY_URL`
- 所有命令可在终端手跑，不依赖 AI；反重力里由 Agent 代为执行即可
