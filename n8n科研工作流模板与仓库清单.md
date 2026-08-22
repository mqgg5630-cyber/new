# n8n 科研类工作流模板与仓库清单

> 整理日期：2026-08-22
> 说明：n8n 模板有两种来源——① **n8n.io 官方模板库**（n8n 编辑器里 `☰ → Import workflow → Import from URL`，粘贴下面链接即可导入，多数免费）；② **GitHub 社区仓库**（clone 后把 `.json` 工作流文件手动导入）。

---

## 一、n8n.io 官方模板（科研相关，可直接导入）

### 📄 论文监控 / 订阅摘要

| # | 模板 | 功能 | 依赖 |
|---|---|---|---|
| 1 | [Monitor AI research papers with Gemini-powered filtering and email summaries](https://n8n.io/workflows/9859-monitor-ai-research-papers-with-gemini-powered-filtering-and-email-summaries/) | 定时抓 arXiv cs.AI 新论文 → Gemini 按你的研究兴趣过滤 → 生成摘要 → HTML 邮件订阅 | arXiv API（免费）、Gemini API、SMTP/Gmail |
| 2 | [Daily RAG research paper hub with arXiv, Gemini AI, and Notion](https://n8n.io/workflows/8847-daily-rag-research-paper-hub-with-arxiv-gemini-ai-and-notion/) | 每日 6:00 抓指定关键词的 arXiv 论文 → 清洗/翻译/摘要 → 写入 Notion 数据库 → 飞书/Gmail 通知（中文作者出品，文档详细） | arXiv API、Gemini 2.5 Flash、Notion、飞书/Gmail |
| 3 | [Build a weekly AI trend alerter with arXiv and Weaviate](https://n8n.io/workflows/5817-build-a-weekly-ai-trend-alerter-with-arxiv-and-weaviate/) | 每周抓 arXiv → LLM 打标签+嵌入到 Weaviate 向量库 → AI Agent 生成"本周 AI 趋势周报"邮件 | Weaviate、OpenRouter/OpenAI |
| 4 | [Arxiv paper trend search using AI, write article, send email](https://n8n.io/workflows/2404-arxiv-paper-trend-search-using-ai-write-article-send-email/) | arXiv 论文趋势 → AI 写通讯稿 → Gmail 发给订阅者（带 Supabase 订阅者管理） | Supabase、AI、Gmail |

### 📚 单篇论文摘要 / 阅读辅助

| # | 模板 | 功能 | 依赖 |
|---|---|---|---|
| 5 | [Arxiv paper summarization with ChatGPT](https://n8n.io/workflows/2904-arxiv-paper-summarization-with-chatgpt/) | Webhook 收 arXiv 论文 ID → 抓取正文 → 结构化摘要（Abstract/Introduction/Results/Conclusion）→ 返回结果 | Webhook、ChatGPT |
| 6 | [Generate structured scientific research PDF summaries with GPT-4o](https://n8n.io/integrations/agent/#generate-structured-scientific-research-pdf-summaries-with-gpt-4o) | PDF 论文 → 结构化科学摘要 | GPT-4o |
| 7 | [Ai research paper analysis & documentation with Decodo, GPT & Google](https://n8n.io/integrations/agent/#ai-research-paper-analysis--documentation-with-decodo-gpt--google) | 论文分析+文档化 | Decodo、GPT、Google |

### ✍️ 文献库管理（Zotero）

| # | 模板 | 功能 | 依赖 |
|---|---|---|---|
| 8 | [Import research papers from Telegram to Zotero with AI abstract summaries](https://n8n.io/workflows/7676-import-research-papers-from-telegram-to-zotero-with-ai-abstract-summaries/) | 把 DOI 链接发给 Telegram 机器人 → 自动从 Crossref/DataCite/Unpaywall 拉元数据 → 找 OA PDF → 写入 Zotero → 返回摘要 | Telegram Bot、Zotero API Key、OpenRouter |
| 9 | [Automate Zotero Bibliographic Data Extraction（第三方免费模板）](https://growwstacks.com/workflows/get-bibliographic-data-from-your-zotero-library) | 从 Zotero 指定 collection 批量提取题录元数据（标题/作者/期刊/DOI/摘要/引用键），用于文献综述、基金申请、课题组论文库 | Zotero API Key |

### 🧪 论文撰写 / 研究问答

| # | 模板 | 功能 | 依赖 |
|---|---|---|---|
| 10 | [Generate AI research papers with Claude, arXiv, Google Scholar and DOCX export](https://n8n.io/workflows/13713-generate-ai-research-papers-with-claude-arxiv-google-scholar-and-docx-export/) | 多 Agent 架构：Research Agent 检索参考文献 → Orchestration Agent 协调 6 个写作 Agent（Introduction/Related Work/Methodology/Results/Discussion/Conclusion）→ 自动生成参考文献 → 导出格式化 DOCX | Claude API、Google Scholar、Google Docs Script |
| 11 | [Draft and manage academic research papers with GPT-4 and Pinecone](https://n8n.io/integrations/agent/#draft-and-manage-academic-research-papers-with-gpt-4-and-pinecone) | 论文草稿撰写与管理（带向量库） | GPT-4、Pinecone |
| 12 | [Answer research questions using OpenAI GPT-4.1 and arXiv papers](https://n8n.io/integrations/agent/#answer-research-questions-using-openai-gpt-4.1-and-arxiv-papers) | 基于 arXiv 论文回答问题 | OpenAI GPT-4.1、arXiv |

> 更多科研/数据分析模板可刷 n8n 官方集成页：https://n8n.io/integrations/agent/ （搜索 research / arxiv / scholar）

---

## 二、GitHub 社区仓库（工作流大合集，含科研类可直接挖）

| 仓库 | 规模/特点 | 怎么用 |
|---|---|---|
| [Danitilahun/n8n-workflow-templates](https://github.com/Danitilahun/n8n-workflow-templates) | **2053 个工作流**、365 个集成、自带本地搜索文档站（Python 启动 localhost:8000 即可搜索/浏览） | `git clone` → `python run.py` → 搜索 "arxiv/research" → 复制对应 `.json` 导入 n8n |
| [pxw3504k-web/awesome-n8n-workflows](https://github.com/pxw3504k-web/awesome-n8n-workflows) | 最大的非官方合集，**6000+ 工作流**，配套网站 https://n8nworkflows.world | 网站按分类浏览 + 复制 JSON |
| [enescingoz/awesome-n8n-templates](https://github.com/enescingoz/awesome-n8n-templates) | **280+ 模板、19k★**，18 个分类；其中 **AI research/RAG/数据分析类 39 个**（Hugging Face 论文摘要、RAG 问答、深度研究 agent 等） | clone 后找 research 相关 `.json` 导入 |
| [felipfr/awesome-n8n-workflows](https://github.com/felipfr/awesome-n8n-workflows) | 2000+ 工作流，按 Analytics/Monitoring/DevOps 等分类 | 同上 |
| [scholarpeak/n8n-workflows](https://github.com/scholarpeak/n8n-workflows) | 社区模板合集，含 **"Analyse papers from Hugging Face with AI and store them in Notion"**、Exa.ai 竞品调研等 | 同上 |
| [AIXerum/AWESOME-n8n-Examples](https://github.com/AIXerum/AWESOME-n8n-Examples) | 社区模板合集（中文文档，含 Notion 论文分析类） | 同上 |
| [lqshow/awesome-n8n-workflows](https://github.com/lqshow/awesome-n8n-workflows) | 中文作者精选，含 **RAG 知识助手（n8n + Ollama + Qwen3 本地化、不依赖云端 AI）**、GitHub→飞书收集 | 同上 |
| [Marvomatic/n8n-templates](https://github.com/Marvomatic/n8n-templates) | SEO/内容/数据分析模板（对科研文献计量/文本分析有参考价值） | 同上 |

---

## 三、结合上一轮的"去AI化"思路怎么选

| 你的需求 | 推荐模板/仓库 | 去AI化程度 |
|---|---|---|
| 每天盯 arXiv 新论文 | #9859、#8847（最贴近中文用户，文档最全） | 可去掉 Gemini 节点 → 纯抓取+存 Notion/发邮件，零 AI |
| 文献库自动化（Zotero 题录/PDF 入库） | #7676、growwstacks Zotero 模板 | 摘要节点可去掉，元数据部分纯 API |
| 写综述/论文初稿 | #13713（多 Agent 撰写） | 强依赖 AI，适合保留 AI；想省成本可换本地 Ollama |
| 团队论文共享/监控大而全 | Danitilahun 2053 合集 / n8nworkflows.world | 按需挑，可完全去掉 AI 节点 |
| 完全不要 AI 的科研自动化 | lqshow RAG（Ollama 本地）或把任意模板删掉 LLM 节点 | ✅ 100% 去AI |

**导入方法**：n8n 编辑器 → `☰` → **Import workflow → Import from URL** → 粘贴上面 n8n.io 模板链接（或本地 `.json` 文件路径）→ 按提示填 API Key/凭据 → 激活。
