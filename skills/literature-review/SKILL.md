---
name: literature-review
description: >
  Conduct a structured deep literature review: scoping search, screening,
  reading & note-taking, synthesis outline, and exporting a review report as
  Markdown or docx. Use when the user asks for a literature review, research
  survey, 文献综述, 研究现状, 相关工作总结, or a "state of the art" report on a topic.
---

# Literature Review（文献综述全流程）

把"写综述"拆成可复现的 6 步。整个过程不强制依赖 AI——检索和整理都是确定性操作；
AI 只负责读摘要、归纳和排版。输出物：`review.md`（+ 可选 `review.docx`）。

## 第 1 步：明确范围（先问清 3 件事）

1. 主题一句话（如 "RAG 在生物医学领域的应用"）
2. 时间范围（默认近 3 年）
3. 文献数量（默认 20~50 篇）与深度（速览 / 精读）

## 第 2 步：系统检索

- 用 `paper-search` 技能（或 paper-search-mcp / arXiv API）在 **arXiv + Semantic Scholar + Crossref + PubMed（生物医学时）** 各检一轮
- 每轮记录：检索式、来源、命中数 → 保证可复现（可写进综述方法学部分）

## 第 3 步：筛选（PRISMA 风格）

- 初筛：按标题+摘要，排除不相关 → 得到候选集
- 复筛：按"是否支撑综述论点"打标签：`核心 / 支撑 / 背景 / 排除`
- 输出 `papers/screening.md`：编号 | 标题 | 筛选结果 | 理由

## 第 4 步：精读与笔记

每篇核心文献做一条结构化笔记（`papers/notes.md`）：

```markdown
## [编号] 作者 (年份). 标题
- 问题：……
- 方法：……
- 关键发现：……
- 局限：……
- 与综述论点的关系：……
```

## 第 5 步：合成大纲

按主题聚类（不是按文献罗列），常用结构：

```markdown
# 标题：XX研究综述
1. 引言（背景 + 问题 + 综述范围/方法学）
2. 方法分类
   2.1 类别A
   2.2 类别B
3. 各方法对比（表格：方法 | 代表工作 | 数据集 | 指标 | 优劣）
4. 挑战与开放问题
5. 结论与展望
6. 参考文献（BibTeX/编号列表）
```

对比表格是综述的"正文"，务必用表格呈现。

## 第 6 步：导出

- Markdown：直接写 `review.md`
- Word：用 python-docx（无 python-docx 时先 `pip install python-docx`），标题用 Heading 样式、
  表格用 `doc.add_table`，参考文献用编号列表
- 生成后向用户报告文件路径和统计（共检索 X 篇、精读 Y 篇、引用 Z 篇）

## 注意

- 引用必须真实：每个引用都能追溯到 DOI/arXiv 链接，禁止编造
- 数据/图片有来源时标注出处
- 本流程的每一步都是确定性的，可以在完全没有 AI 的环境下手动/脚本执行
