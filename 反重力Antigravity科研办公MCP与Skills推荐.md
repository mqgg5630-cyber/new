# 反重力（Google Antigravity）科研与办公：MCP / Skills 推荐 · n8n 接入 · 去AI化方案

> 生成日期：2026-08-22 ｜ 适用对象：想用 Antigravity（Google 的 Agent-first IDE）做科研和办公自动化的同学
> 本报告配套文件：`mcp/`（可直接导入的 MCP 配置）、`skills/`（可直接安装的 Agent Skills）、`反重力Antigravity科研办公MCP与Skills推荐.docx`（本报告 Word 版）

---

## 目录

1. [结论速览（TL;DR）](#1-结论速览tldr)
2. [Antigravity 的扩展机制速览（MCP / Skills 配置在哪）](#2-antigravity-的扩展机制速览)
3. [科研方向：强烈推荐的 MCP（可直接在反重力里调用）](#3-科研方向强烈推荐的-mcp)
4. [办公方向：强烈推荐的 MCP](#4-办公方向强烈推荐的-mcp)
5. [科研 + 办公：值得装的 Skills](#5-科研--办公值得装的-skills)
6. [反重力能不能调用 n8n？适合反重力的 n8n Agent 项目](#6-反重力能不能调用-n8n适合反重力的-n8n-agent-项目)
7. [去AI化：把 MCP / Skills / Agent 变成不依赖 AI 的 GUI 或独立程序](#7-去ai化把-mcp--skills--agent-变成不依赖-ai-的-gui-或独立程序)
8. [落地示例：科研办公全家桶（含可直接改用的代码）](#8-落地示例科研办公全家桶)
9. [资源清单（链接汇总）](#9-资源清单链接汇总)
10. [配套交付文件说明](#10-配套交付文件说明)

---

## 1. 结论速览（TL;DR）

| 问题 | 结论 |
|---|---|
| 反重力能不能直接用 MCP？ | 能。MCP 配置在 **Agent 面板 → ⋯ → MCP Servers → Manage MCP Servers → View raw config**，全局文件是 `~/.gemini/antigravity/mcp_config.json`（macOS/Linux 为 `~/.gemini/antigravity/mcp_config.json`，Windows 为 `%USERPROFILE%\.gemini\antigravity\mcp_config.json`），项目级也可用 `.mcp.json` |
| 科研最值得装的 MCP | **paper-search-mcp**（arXiv/PubMed/Semantic Scholar 等 20+ 源的检索+下载+阅读，2.5k★）、**arxiv-mcp-server**、**zotero-mcp**（本地文献库）、**onecite / citecheck**（引文校验+BibTeX）、**firecrawl-mcp**（网页深度抓取）、**exa-mcp-server**（语义搜索）、**duckdb / postgres MCP**（数据分析） |
| 办公最值得装的 MCP | **workspace-mcp（Google Workspace 全家桶**：Gmail/Drive/Docs/Sheets/Calendar 等 12 服务 100+ 工具）、**Notion 官方 MCP**、**Excel/Word 文档操作类 MCP**（ai-office-mcp、excel-mcp-server、Document Operations）、**Todoist/Linear/Asana**（任务管理）、**Obsidian MCP**（本地知识库） |
| 科研/办公值得装的 Skills | **deep-research**、**fact-checker**、**scientific-agent-skills**（148 个科学技能）、**web-research-agent**、**markitdown**（文档转 Markdown）、**pptx**（PPT 生成）、**office 文档系列**；集合库 **antigravity-awesome-skills（1900+）**、**Addy Osmani agent-skills** |
| 反重力能调用 n8n 吗？ | **能**，有 3 条成熟路径：① n8n 官方 **MCP Server Trigger 节点**把工作流暴露成 MCP 工具；② 社区 **czlonkowski/n8n-mcp**（官方文档专门写了 ANTIGRAVITY_SETUP.md）；③ n8n 作为 **MCP Client** 消费外部 MCP 工具。适合反重力的 n8n 项目见[第 6 节](#6-反重力能不能调用-n8n适合反重力的-n8n-agent-项目) |
| 能不能去AI化？ | **能，而且很彻底**。MCP 的"工具层"和"AI 决策层"本来就能解耦——底层 MCP Server 就是普通程序。四条路线：**A.** 用不带 LLM 的 MCP 客户端（Enola、MCPHost 等 GUI）；**B.** 把 MCP 工具转成普通 CLI/库，再用 tkinter/Streamlit 包一个 GUI（本包附模板）；**C.** 用自带 GUI、不需要 AI 的自动化平台（n8n 不用 AI 节点、Node-RED、Activepieces、Windmill、Huginn）；**D.** 最彻底：把常用流程写成普通脚本 + 计划任务。详见[第 7 节](#7-去ai化把-mcp--skills--agent-变成不依赖-ai-的-gui-或独立程序) |

---

## 2. Antigravity 的扩展机制速览

Antigravity（2026 年 5 月 I/O 发布的 2.0 版）是 Google 的 Agent-first IDE，基于 VS Code 内核，支持以下几种扩展机制，**别搞混**：

| 机制 | 存放位置 | 触发方式 |
|---|---|---|
| **MCP 服务器** | 全局：`~/.gemini/antigravity/mcp_config.json`（macOS/Linux）、`%USERPROFILE%\.gemini\antigravity\mcp_config.json`（Windows）；项目级：`.mcp.json` | 每次会话加载，Agent 自动决定何时调用 |
| **Skills** | 项目级：`.agents/skills/<技能名>/SKILL.md`（注意复数，旧版 `.agent/skills` 也兼容）；全局：官方文档说 `~/.gemini/antigravity/skills/`，但社区实测 `~/.gemini/config/skills/` 更可靠 | Agent 根据 SKILL.md 里的 `description` 自动触发，也可用 `/skills` 查看 |
| **Rules** | 全局 `~/.gemini/GEMINI.md`；项目 `.agents/rules/*.md` | always_on / glob / model_decision / @-提及，注意有 12000 字符上限 |
| **Workflows** | Markdown 文件 | 手动输入 `/工作流名` 触发 |
| **Plugins** | `agy plugin install <git-url>` | 一次装好 skills+personas+commands |

**操作入口（重要，社区踩坑总结）**：
- MCP 配置在 **Agent 侧边栏（右侧面板）顶部 ⋯ 菜单 → MCP Servers → Manage MCP Servers → View raw config**，打开的就是全局 `mcp_config.json`。**不要**照抄 VS Code 的 `mcp.json` 教程，Antigravity 里 VS Code 的 MCP 面板是坏的。
- Antigravity **不支持 `${workspaceFolder}` 占位符**，MCP 配置里要用绝对路径。
- 社区反馈：MCP 服务器的**工作目录默认是 Antigravity 程序目录**而不是项目目录，依赖相对路径的服务器（如 shadcn 的 components.json）会踩坑，建议服务器一律用绝对路径或显式传 `cwd`。
- Skills 安装命令：`npx skills add <github仓库> -y -g`（`-g` 装到全局），装完重启 Antigravity 会话。

---

## 3. 科研方向：强烈推荐的 MCP

> 全部都可以直接写进反重力的 `mcp_config.json`。`mcp/mcp_config.global.json` 已按本表配好，复制即可。

### 3.1 论文检索与下载全家桶（最推荐）

| MCP | 一句话介绍 | 安装方式 | 推荐度 |
|---|---|---|---|
| **paper-search-mcp**（openags，2.5k★） | 20+ 学术源（arXiv、PubMed、bioRxiv、medRxiv、Semantic Scholar、Crossref、OpenAlex、Europe PMC、Zenodo、HAL…）的**搜索 + 下载 + 阅读**，免费源优先 | `uvx paper-search-mcp`（可选配 Unpaywall/CORE/Semantic Scholar key） | ⭐⭐⭐⭐⭐ |
| **arxiv-mcp-server**（blazickjp） | 轻量 arXiv 检索，返回摘要/链接/PDF | `uvx arxiv-mcp-server` | ⭐⭐⭐⭐ |
| **zotero-mcp** | 桥接你**本地 Zotero 文献库**，30+ 工具管理 collection、注释、条目 | `uvx zotero-mcp`（需本地 Zotero 7+） | ⭐⭐⭐⭐ |
| **onecite / citecheck** | 引文校验 + 批量修复手稿里错误/幻觉的参考文献（PubMed/Crossref/arXiv/Semantic Scholar 多源） | `pip install onecite` / `npx` | ⭐⭐⭐⭐ |
| **Semantic Scholar MCP / Scholar Sidekick** | 语义检索、引用格式（10,000+ CSL 样式） | 各项目 README | ⭐⭐⭐ |

**paper-search-mcp 配置示例**（已含在 `mcp/mcp_config.global.json`）：

```json
{
  "mcpServers": {
    "paper-search": {
      "command": "uvx",
      "args": ["paper-search-mcp"],
      "env": {
        "PAPER_SEARCH_MCP_UNPAYWALL_EMAIL": "you@example.com",
        "PAPER_SEARCH_MCP_CORE_API_KEY": "",
        "PAPER_SEARCH_MCP_SEMANTIC_SCHOLAR_API_KEY": "",
        "PAPER_SEARCH_MCP_ZENODO_ACCESS_TOKEN": ""
      }
    }
  }
}
```

装上之后直接在反重力对话里说：
- “帮我搜 arXiv 上最近 3 个月的强化学习论文，列出 Top 10”
- “用 PubMed 查一下 CRISPR base editing 的综述，把 5 篇最重要的下载到 ./papers/”
- “把这篇手稿的参考文献校验一遍，DOI 不存在的标出来”

### 3.2 网络与深度研究

| MCP | 一句话介绍 | 安装方式 | 推荐度 |
|---|---|---|---|
| **firecrawl-mcp** | 网页抓取/爬站/结构化提取/网站地图/监控，深网研究必备 | `npx -y firecrawl-mcp`（需 FIRECRAWL_API_KEY） | ⭐⭐⭐⭐⭐ |
| **exa-mcp-server** | 神经语义搜索，按"意思"而不是关键词找资料 | `npx -y exa-mcp-server`（需 EXA_API_KEY） | ⭐⭐⭐⭐ |
| **context7-mcp** | 自动拉取项目最新文档上下文，写代码/查 API 少幻觉 | `npx -y @upstash/context7-mcp` | ⭐⭐⭐⭐ |

### 3.3 科研数据处理

| MCP | 一句话介绍 | 安装方式 |
|---|---|---|
| **duckdb-mcp** | 在本地 DuckDB 里跑 SQL，处理 CSV/Parquet 大数据集 | 见项目 README |
| **postgres-mcp** | 只读/受控 SQL 查数据库 | `npx -y @modelcontextprotocol/server-postgres "连接串"` |
| **filesystem-mcp** | 让 Agent 读写你指定目录（论文整理/批处理的基础） | `npx -y @modelcontextprotocol/server-filesystem /你的/目录` |

---

## 4. 办公方向：强烈推荐的 MCP

### 4.1 Google 全家桶（如果你们用 Google Workspace）

| MCP | 一句话介绍 | 安装方式 | 推荐度 |
|---|---|---|---|
| **workspace-mcp**（taylorwilsdon，~3000★） | Gmail、Drive、Docs、Sheets、Slides、Forms、Calendar、Chat、Tasks、Contacts、Apps Script、Search **12 个服务 100+ 工具**，OAuth 2.1 | `uvx workspace-mcp` | ⭐⭐⭐⭐⭐ |

配置示例：

```json
{
  "mcpServers": {
    "workspace-mcp": {
      "command": "uvx",
      "args": ["workspace-mcp"]
    }
  }
}
```

装上后可以说：“把上周的会议纪要从 Drive 里找出来，整理成表格发我 Gmail”，“把这份 CSV 填进新的 Google Sheets 并共享给小李”。

### 4.2 微软 Office 文档处理（如果你们用 Office/WPS）

| MCP | 一句话介绍 | 安装方式 | 推荐度 |
|---|---|---|---|
| **lingfan36/ai-office-mcp** | 三大模块：**PPT 从任意源文档生成**（原生可编辑）、**Excel 152 个注册工具**（Windows 驱动真实 Excel/WPS）、**Word 带修订痕迹编辑**（文件打开状态也能改） | pip 按模块安装，见项目 README | ⭐⭐⭐⭐⭐ |
| **excel-mcp-server**（kousunh） | Excel 双模式：workbook 模式（xlwings 操作打开的 Excel，可跑 VBA）+ path 模式（纯 Python 直接改 .xlsx，无需装 Excel） | git clone + npm/pip | ⭐⭐⭐⭐ |
| **Document Operations MCP** | 创建/编辑/转换 Word、Excel、PDF 文件 | 见项目 README | ⭐⭐⭐ |

> 提示：Antigravity 配置里的 `command`/`args` 支持任意程序，所以任何"python 启动的 MCP 服务器"都可以用 `"command": "python", "args": ["-m", "excel_mcp.main"]` 这种方式接入。

### 4.3 任务与知识管理

| MCP | 一句话介绍 | 官方/社区 | 推荐度 |
|---|---|---|---|
| **Notion MCP** | 官方，22 个工具，页面/数据库/权限管理 | 官方 | ⭐⭐⭐⭐⭐ |
| **Todoist MCP** | 官方，40+ 工具，个人任务管理天花板 | 官方 | ⭐⭐⭐⭐ |
| **Linear / Asana / ClickUp MCP** | 团队项目跟踪（23+ / 17 / 6 工具） | 官方 | ⭐⭐⭐⭐ |
| **Obsidian MCP（MCPVault 等）** | 本地优先知识库，无需 OAuth | 社区 | ⭐⭐⭐⭐ |
| **Google Calendar MCP** | 官方托管版（9 工具）或社区版 nspady（13 工具） | 官方+社区 | ⭐⭐⭐⭐ |

**选型口诀**：个人知识库用 Notion 或本地 Obsidian；任务管理个人用 Todoist、团队用 Linear；文档协作 Google 系用 workspace-mcp、微软系用 ai-office-mcp。

---

## 5. 科研 + 办公：值得装的 Skills

> Skills 是"写给 Agent 的操作说明书"（SKILL.md），不是 MCP。装法：`npx skills add <仓库> -y -g`，或者直接把文件夹拷到 `.agents/skills/`。本包 `skills/` 目录里已经写好 5 个可直接用的技能。

### 5.1 科研向

| Skill | 来源 | 用途 |
|---|---|---|
| **deep-research** | awesome-llm-apps/awesome-agent-skills（shubhamsaboo） | 给定主题做多轮检索-交叉验证-输出结构化研究报告 |
| **fact-checker** | 同上 | 逐条事实核查、给来源 |
| **web-research-agent** | skills-hub | 自主网页检索+抓取+总结+生成报告 |
| **scientific-agent-skills** | 社区（31k★） | 148 个技能：生物信息学、基因组学、科学可视化、统计分析 |
| **paper-search / literature-review** | **本包 skills/** | 论文检索整理、文献综述全流程（我写好可直接用的） |

### 5.2 办公向

| Skill | 来源 | 用途 |
|---|---|---|
| **markitdown** | 官方技能库 | 任意文档（docx/xlsx/pdf/pptx）→ Markdown，喂给 Agent 做分析 |
| **pptx / nanobanana-ppt-skills** | 技能库 | 从大纲/文档一键生成 PPT |
| **AAS Documents & Presentations** | antigravity-awesome-skills 插件包 | 9 个文档/演示技能：转换、排版、幻灯片工作流 |
| **office-docs** | **本包 skills/** | Word/Excel/PPT 批处理：合并、清洗、格式化、导出（不依赖 MCP，直接用 python-docx/openpyxl） |
| **n8n-workflow** | **本包 skills/** | 在反重力里创建/调用 n8n 工作流（AI 版）以及用 Webhook+表单去AI调用（非 AI 版） |
| **de-ai-gui** | **本包 skills/** | 把任何 MCP 工具/流程转成独立 GUI 程序的"元技能"（含模板） |

### 5.3 一站式技能库

| 仓库 | 规模 | 安装命令 |
|---|---|---|
| **antigravity-awesome-skills**（sickn33） | 1900+ 技能，反重力品牌集合，按角色打包 | `npx skills add sickn33/antigravity-awesome-skills -y -g` 或 clone 后按需装 |
| **agent-skills**（Addy Osmani） | 工程/办公通用技能，官方推荐 | `agy plugin install https://github.com/addyosmani/agent-skills.git` |
| **awesome-agent-skills**（shubhamsaboo） | 深度研究/写作/战略技能 | `npx skills add https://github.com/shubhamsaboo/awesome-llm-apps/awesome-agent-skills -y -g --skill deep-research` |
| **google/skills** | 谷歌官方技能 | `npx skills add https://github.com/google/skills -y -g` |
| **LichAmnesia/awesome-antigravity-skills** | 反重力技能导航站（按分类推荐） | 浏览器访问即可 |
| **skills-hub.ai** | 在线搜索/安装技能 | 浏览器访问即可 |

---

## 6. 反重力能不能调用 n8n？适合反重力的 n8n Agent 项目

### 6.1 结论：能，而且有官方支持的三条路径

n8n 是开源（fair-code）的可视化工作流自动化平台，自带 Web GUI、400+ 集成、可 Docker 自托管。它和反重力的关系是"**双向**"的：

**路径 A：n8n 工作流 → MCP 工具 → 反重力调用（最推荐）**
n8n 官方有 **MCP Server Trigger 节点**：把工作流里连好的任意工具节点（HTTP、Excel、数据库、邮件、Slack……）暴露成标准 MCP 工具。反重力连上这个 MCP 端点后，就能像调用本地 MCP 一样触发 n8n 工作流，**AI 只负责"决定调用哪个工具、填什么参数"，干活的是 n8n 的可视化流程**。
- 在 n8n 里新建工作流 → 拖入 MCP Server Trigger → 连接工具节点 → 激活 → 得到 MCP 端点 URL
- 在反重力 mcp_config.json 里加一条 `serverUrl`（streamable HTTP/SSE）即可

**路径 B：n8n-mcp（社区，专门为反重力适配）**
`czlonkowski/n8n-mcp` 是 n8n 官方社区推荐的 MCP 服务器，**其文档里有专门的 ANTIGRAVITY_SETUP.md**，把 n8n API 暴露成工具，让你在反重力里直接"创建、读取、执行 n8n 工作流"。配置（Windows 示例，Mac/Linux 换绝对路径）：

```json
{
  "mcpServers": {
    "n8n-mcp": {
      "command": "node",
      "args": ["C:\\Users\\<USER_NAME>\\AppData\\Roaming\\npm\\node_modules\\n8n-mcp\\dist\\mcp\\index.js"],
      "env": {
        "MCP_MODE": "stdio",
        "LOG_LEVEL": "error",
        "DISABLE_CONSOLE_OUTPUT": "true",
        "N8N_API_URL": "http://localhost:5678",
        "N8N_BASE_URL": "http://localhost:5678",
        "N8N_API_KEY": "<你的n8n API Key>"
      }
    }
  }
}
```

装完在反重力里说"把上周数据整理成 Excel 发到团队邮箱"即可，反重力会调 n8n-mcp 去执行你预先画好的 n8n 工作流。建议在项目根目录放一个 `AGENTS.md` 写清 n8n 工作流的命名规范，让 Agent 生成的流程更规范。

**路径 C：n8n 作为 MCP Client（反向）**
n8n 还有 **MCP Client Tool 节点**：n8n 里的 AI Agent 节点可以消费外部 MCP 服务器的工具（比如让 n8n 里的 agent 用 firecrawl 或你自建的 MCP）。这条路径适合"把 n8n 当调度中枢"的场景。

### 6.2 适合反重力的 n8n Agent 项目

| 项目 | 是什么 | 为什么适合反重力 |
|---|---|---|
| **czlonkowski/n8n-mcp** | 把 n8n API 变成 MCP 工具 | 官方文档写了 ANTIGRAVITY_SETUP.md，即插即用 |
| **N8N Agent Marketplace**（Super-Chain） | 把任意 n8n 工作流一键转成"AI 可调用的 MCP 服务器"，自带 Web 管理后台（Agent Marketplace）+ MCP Router | 反重力/Claude/Cursor 都能通过 MCP 直接调用你在 n8n 里画的所有流程；零服务器端凭据存储 |
| **n8n 官方模板：MCP Server with AI Agent as a tool context reducer**（工作流 #4475） | 一个专门化的 GitHub Agent，通过单一 MCP 工具提供 GitHub 全套操作，减少 LLM 上下文消耗 | 模式可复制：把复杂操作封装成"单一 MCP 工具 + 专业子 Agent"，反重力侧只看到清爽的工具列表 |
| **n8n 模板库里的 MCP Server Trigger 模板** | 现成的"工作流即 MCP 工具"示例 | 直接 import 改改就能用 |
| **n8n 自带 AI Agent 节点 + MCP Client Tool** | n8n 内部跑 agent，消费外部 MCP | 可以把反重力不想管的重复性 agent 挪到 n8n 里常驻 |

> 社区经验：**最好的分工是"反重力做决策、n8n 做执行"**。把邮件发送、Excel 处理、数据库写入、定时抓取这类"确定性流程"全部画成 n8n 工作流；反重力/AI 只负责理解需求、调用正确的工作流、填参数。这样即使哪天完全去掉 AI，这些工作流照样用（见下一节）。

### 6.3 n8n 的去AI化用法（重要）

n8n **天生就能去AI化**：
- 工作流里**不拖任何 AI/LLM 节点**，只用 webhook、schedule、HTTP、Excel、邮件等普通节点 → 它就是一个"自带 GUI 的自动化程序"，零 AI 依赖。
- 触发方式同样不需要 AI：**Webhook 节点**（任何人/程序 POST 一下就能触发）、**Schedule 节点**（定时跑）、**n8n 表单触发器**（给同事一个网页表单填参数）。
- 想保留"填参数入口"又不想要 AI？给工作流加一个 **n8n Form Trigger / Webhook + 简单 HTML 表单页**，或者用 n8n 的公共/内网 URL，就相当于你自建了一个小工具。

---

## 7. 去AI化：把 MCP / Skills / Agent 变成不依赖 AI 的 GUI 或独立程序

### 7.1 核心认知：MCP 本来就是"普通程序"，AI 只是调用方

MCP（Model Context Protocol）本质是 **JSON-RPC 2.0**：MCP Server 暴露若干工具（tool），任何程序——不一定是 LLM——都能发 `tools/call` 请求去调用。所以：

```
   MCP Server（工具层：检索论文、读写 Excel、查数据库……）
        ▲
        │ 调用（JSON-RPC，stdio 或 HTTP/SSE）
        ├── AI 客户端（Antigravity / Claude / Cursor ……）→ 需要 AI
        ├── 非AI客户端（Enola / MCPHost / 自写 Python）→ 不需要 AI  ← 去AI化路线A
        └── 被包成 GUI 按钮 / 定时任务 / 命令行  → 不需要 AI          ← 去AI化路线B
```

### 7.2 路线 A：换一个"不带 LLM 的 MCP 客户端"（最快，1 小时上手）

| 工具 | 类型 | 特点 |
|---|---|---|
| **Enola** | 桌面/CLI/TUI | 官方主打能力之一就是**直接调用任何 MCP 服务器的工具、不需要 LLM**；自带 Web UI |
| **MCPHost** | Web 应用 | 多服务器管理，GUI 连接/调用工具，配置持久化 |
| **Canvas MCP Client** | 桌面 | 画布式界面，统一管理多个 MCP server，widget 化 |
| **MCPBundle Studio** | 浏览器 | 测试/执行远程 MCP 工具的可视化客户端 |
| **mcp-cli**（chrishayuk） | CLI | 纯命令行驱动 MCP，可脚本化；自带 --dashboard 浏览器面板 |
| **官方 SDK 自写** | 代码 | Python：`pip install mcp`，几十行代码枚举+调用工具（见 8.1 模板） |

### 7.3 路线 B：把 MCP 工具"翻译"成独立 GUI 小程序（可控、可分发）

思路：**用官方 MCP 客户端库在代码里调用工具，然后包一层 GUI**。很多 MCP server 本身就是"CLI/库 + MCP"双形态（如 paper-search-mcp 自带 CLI、OneCite 是 CLI+库+MCP），直接把 CLI/库抽出来用更简单。

- 桌面 GUI：Python `tkinter`（零依赖）/ `PyQt6`
- 网页 GUI：`Streamlit` / `Gradio`（几行代码出表单和按钮）
- 本包 `skills/de-ai-gui/SKILL.md` 里写了完整步骤和模板；`8.1` 给了一个可直接运行的 Streamlit 示例

### 7.4 路线 C：用"自带 GUI、不需要 AI"的自动化平台替代 agent

如果你要的本来就是"图形化、能自己跑"的自动化，**根本不需要 AI agent**——这些平台自带拖拽画布和网页 UI：

| 平台 | 许可证 | 自托管 | 适合场景 | 和 n8n 的关系 |
|---|---|---|---|---|
| **n8n** | fair-code | ✅ | 全能；400+ 集成；**不用 AI 节点就是纯自动化工具** | 本尊 |
| **Node-RED** | Apache-2.0 | ✅ | IoT、事件流、轻量编排；极省资源 | 更轻的替代 |
| **Activepieces** | MIT（真开源） | ✅ | 最接近 n8n 的开源替代，无码+代码混合 | 替代 |
| **Windmill** | AGPL（开源核心） | ✅ | 开发者向：Python/TS 脚本→工作流→**自动生成内部工具 UI** | 代码优先替代 |
| **Huginn** | MIT | ✅ | 监控/抓取型"agent"（2013 年起），折腾党最爱 | 老牌替代 |
| **Automatisch** | AGPL | ✅ | 简单 Zapier 风格流程、隐私优先 | 替代 |
| **Flowise / Dify** | Apache-2.0 | ✅ | LLM 应用可视化（仍属 AI 系，去AI化不彻底，仅提一句） | — |

> 注意：这些平台里**目前只有 n8n 原生支持 MCP**（MCP Server Trigger / MCP Client Tool 两个节点）。Node-RED/Activepieces/Windmill 暂时没有原生 MCP 节点，但普通自动化完全够用。

### 7.5 路线 D：最彻底的"去AI"——普通脚本 + 计划任务/GUI

不碰 MCP，直接把高频任务写成 Python/shell + `cron`（Linux/macOS）或任务计划程序（Windows）：
- 每天 8:00 自动跑：arXiv API 抓新论文 → 生成摘要 md → python-docx 生成周报 → 发邮件
- 每周五：Excel 汇总报表 → 格式化成固定模板 → 存到网盘
- 需要手动入口时加一个 tkinter/Streamlit 小窗口

这条路线 **0 AI、0 联网、0 API key**，代码即文档，最可控。8.2 给了完整示例。

### 7.6 半去AI：本地小模型兜底（数据不出本机）

如果某些环节确实需要"理解自然语言"又不愿意用云端 AI：
- **Ollama + mcphost**：本地跑 qwen2.5 等模型，通过 `~/.mcp.json` 连 MCP 服务器，`mcphost -m ollama:qwen2.5:14b --config ~/.mcp.json` 即可工具调用，无需 API key、可断网
- 折中：**云端 AI 只用于"听写需求"，执行永远走 n8n/脚本**（见 6.3 的分工）

### 7.7 四条路线怎么选（决策树）

```
要不要 AI 理解自然语言？
├─ 要，但能接受本地小模型 → 路线A + Ollama/mcphost
├─ 要，必须最强模型 → 用反重力（云端 Gemini）+ MCP；去AI化不必强求
└─ 不要 / 尽量少依赖
    ├─ 是"确定性的重复流程"（抓取/汇总/发件/报表）→ 路线D（脚本+定时）或路线C（n8n/Node-RED）
    ├─ 想让同事自助使用 → 路线C（n8n Webhook+表单 / Windmill UI）或路线B（Streamlit）
    └─ 已经有现成 MCP server，只想去掉 AI → 路线A（Enola/MCPHost）或路线B（包 GUI）
```

---

## 8. 落地示例：科研办公全家桶

### 8.1 示例 1：把 paper-search-mcp 变成"不依赖 AI 的论文检索网页"

`uvx` 装好 `paper-search-mcp` 后，用 Streamlit 包一个 GUI（本包附带，见 `examples/paper_search_gui.py`）：

```python
# 只演示骨架，完整版见 examples/paper_search_gui.py
import streamlit as st
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def search_papers(query: str, max_results: int):
    params = StdioServerParameters(command="uvx", args=["paper-search-mcp"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            # 找到 search_papers 工具并调用
            result = await session.call_tool("search_papers", {"query": query, "max_results": max_results})
            return result.content

st.set_page_config(page_title="论文检索工具（无AI版）", layout="wide")
query = st.text_input("检索关键词", value="retrieval augmented generation")
n = st.slider("返回条数", 1, 20, 5)
if st.button("检索"):
    with st.spinner("检索中…"):
        rows = asyncio.run(search_papers(query, n))
        st.dataframe(rows)  # 输出表格，可直接导出 CSV
```

运行 `streamlit run examples/paper_search_gui.py`，浏览器打开就是纯 GUI，**完全不需要 AI**。同理可包 Zotero、Excel、Notion 等任何 MCP server。

### 8.2 示例 2：文献追踪流水线（纯脚本，0 AI）

```python
# examples/daily_arxiv_digest.py —— 每天定时抓 arXiv 新论文并生成周报 docx
# 用 cron: 0 8 * * * python3 /path/daily_arxiv_digest.py
import urllib.request, xml.etree.ElementTree as ET, datetime
from docx import Document

def fetch_arxiv(query: str, days: int = 1) -> list[dict]:
    url = ("http://export.arxiv.org/api/query?search_query="
           f"all:{urllib.parse.quote(query)}&sortBy=submittedDate&sortOrder=descending&max_results=20")
    root = ET.fromstring(urllib.request.urlopen(url).read())
    ns = {"a": "http://www.w3.org/2005/Atom"}
    out = []
    for e in root.findall("a:entry", ns):
        out.append({"title": e.find("a:title", ns).text.strip().replace("\n", " "),
                    "link": e.find("a:id", ns).text})
    return out

papers = fetch_arxiv("large language model")
doc = Document()
doc.add_heading(f"arXiv 日报 {datetime.date.today()}", level=1)
for p in papers:
    doc.add_paragraph(p["title"], style="List Bullet")
    doc.add_paragraph(p["link"])
doc.save(f"arxiv_daily_{datetime.date.today()}.docx")
print("saved", len(papers), "papers")
```

去掉 `docx` 部分就是纯命令行工具，加上 `cron` 就是全自动。想要图形界面就把 `input()` 换成 tkinter 输入框。

### 8.3 示例 3：n8n 工作流 → 反重力调用 + 去AI复用（同一份资产两用）

1. n8n 里画工作流：`Webhook(填参数) → Excel 节点(处理数据) → Email(发结果)`
2. **AI 版**：工作流再加 `MCP Server Trigger` 节点 → 激活后得到 MCP 端点 → 写进反重力 `mcp_config.json`（`serverUrl`）→ 反重力对话里直接说需求
3. **去AI版**：同一个 Webhook，给同事一个表单页（n8n Form Trigger），或干脆定时执行（Schedule 节点）→ 完全不需要 AI

### 8.4 示例 4：用 Enola / MCPHost 去AI调用

- 装 `enola`，配置 `~/.mcp.json` 指向你已有的 MCP server（文件系统、paper-search、workspace-mcp 都行），启动后**不连任何 LLM** 直接点工具执行。
- 或跑 `mcp-host`（Docker/本地）→ Web UI 里连接多个 server → 鼠标点击调用工具、看返回结果。

---

## 9. 资源清单（链接汇总）

**Antigravity 官方**
- 产品：https://antigravity.google/ ｜ 文档：https://docs.antigravity.google/
- MCP 配置实战教程（含全局配置目录结构）：https://devengoratela.com/2026/05/configuring-mcp-servers-and-skills-for-antigravity-cli-and-ide/ ｜ https://medium.com/google-cloud/configuring-mcp-servers-and-skills-for-antigravity-cli-and-ide-a938c7eebb78
- Agent Skills 官方规范：https://agentskills.io/ ｜ 技能安装 CLI：`npx skills add ...`

**MCP 检索与科研**
- paper-search-mcp：https://github.com/openags/paper-search-mcp
- zotero-mcp、arxiv-mcp-server、onecite、citecheck：GitHub 搜索即可（或见引文对比 https://scholar-sidekick.com/compare/citation-mcp-servers）

**MCP 办公**
- workspace-mcp：https://github.com/taylorwilsdon/google_workspace_mcp ｜ https://workspacemcp.com
- ai-office-mcp：https://github.com/lingfan36/ai-office-mcp
- excel-mcp-server：https://github.com/kousunh/excel-mcp-server

**MCP 注册表（找更多）**：https://mcp.so ｜ https://smithery.ai ｜ https://mcpservers.org ｜ https://glama.ai/mcp/servers

**Skills**
- antigravity-awesome-skills：https://github.com/sickn33/antigravity-awesome-skills
- awesome-antigravity-skills（导航）：https://github.com/LichAmnesia/awesome-antigravity-skills
- Addy Osmani agent-skills：https://github.com/addyosmani/agent-skills
- 技能在线市场：https://skills-hub.ai ｜ https://www.skills.sh

**n8n**
- n8n 官网/模板：https://n8n.io ｜ MCP 文档：https://docs.n8n.io/advanced-ai/mcp/
- n8n-mcp（含 Antigravity 配置）：https://github.com/czlonkowski/n8n-mcp
- N8N Agent Marketplace：https://mcpmarket.com/server/n8n-agent-marketplace

**去AI化**
- Enola：https://github.com/kenzlu/enola ｜ MCPHost：https://github.com/username1/mcphost ｜ Canvas MCP Client：https://github.com/ag2ai/canvas-mcp-client
- 非AI自动化平台：Node-RED（https://nodered.org）、Activepieces（https://www.activepieces.com）、Windmill（https://www.windmill.dev）、Huginn（https://github.com/huginn/huginn）、Automatisch（https://automatisch.io）
- 本地模型：Ollama（https://ollama.com）+ mcphost（https://github.com/mark3labs/mcphost）

---

## 10. 配套交付文件说明

```
.
├── README.md                                  ← 本包总览（怎么用）
├── 反重力Antigravity科研办公MCP与Skills推荐.md   ← 本报告（Markdown）
├── 反重力Antigravity科研办公MCP与Skills推荐.docx ← 本报告（Word）
├── mcp/
│   ├── README.md                              ← MCP 配置安装说明
│   ├── mcp_config.global.json                 ← 全局配置（科研+办公+n8n，可直接改名覆盖 ~/.gemini/antigravity/mcp_config.json）
│   └── mcp_config.project.json                ← 项目级 .mcp.json 精简版
├── skills/
│   ├── README.md                              ← Skills 安装说明
│   ├── paper-search/SKILL.md                  ← 科研：论文检索整理
│   ├── literature-review/SKILL.md             ← 科研：文献综述全流程
│   ├── office-docs/SKILL.md                   ← 办公：Word/Excel/PPT 批处理
│   ├── n8n-workflow/SKILL.md                  ← 办公：调用 n8n 工作流（AI版+去AI版）
│   └── de-ai-gui/SKILL.md                     ← 去AI化：把 MCP 流程包成 GUI 独立程序（含模板）
└── examples/
    ├── paper_search_gui.py                    ← 示例1：论文检索 GUI（Streamlit，无AI）
    └── daily_arxiv_digest.py                  ← 示例2：arXiv 日报脚本（纯脚本，无AI）
```

**常见问题**
- Q：配置完 MCP 不生效？A：先 `antigravity mcp list`（CLI）或在 Manage MCP Servers 里刷新；确认 Node.js 18+ / uv 已装且 `npx`、`uvx` 在 PATH；确认路径是绝对路径。
- Q：想用但不想配环境？A：优先选 HTTP 型 MCP（`serverUrl` 直接填，如高德地图 MCP `https://mcp.amap.com/mcp?key=...`），不用装任何东西。
- Q：去AI化后还能被反重力调用吗？A：能。去AI化只是"多了一个非 AI 入口"，原 MCP 端点还在，反重力照常可用——两者共存。
- Q：需要联网吗？A：路线 D 纯脚本可完全离线；路线 A/B 取决于 MCP server 本身（paper-search 需联网查 arXiv，filesystem 可离线）。

> 免责声明：文中各开源项目版本迭代很快，安装命令以各项目 README 为准；涉及 API Key（Exa/Firecrawl/Unpaywall/n8n 等）请妥善保管，勿提交到公开仓库。
