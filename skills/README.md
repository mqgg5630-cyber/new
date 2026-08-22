# Skills 安装说明（Antigravity）

本目录包含 5 个可直接安装到 Google Antigravity 的 Agent Skills（Agent Skills 开放规范：`SKILL.md` + YAML frontmatter）。

## 技能一览

| 技能 | 分类 | 用途 |
|---|---|---|
| `paper-search` | 科研 | 论文检索、下载、整理成 BibTeX/清单（优先走 paper-search-mcp，无 MCP 时用 arXiv API 兜底） |
| `literature-review` | 科研 | 深度文献综述全流程：检索→筛选→笔记→大纲→导出 md/docx |
| `office-docs` | 办公 | Word/Excel/PPT 批处理（合并、清洗、格式化、导出），不依赖任何 MCP |
| `n8n-workflow` | 办公 | 在反重力里创建/调用 n8n 工作流（AI 版）；以及用 Webhook+表单去AI调用（非 AI 版） |
| `de-ai-gui` | 去AI化 | 把任意 MCP 工具/流程改造成不依赖 AI 的独立 GUI 程序（tkinter / Streamlit），附模板 |

## 安装方法（任选其一）

### 方法 1：复制到项目（推荐，随仓库走）

```bash
mkdir -p .agents/skills
cp -R skills/* .agents/skills/
```

然后重启 Antigravity 会话（或重开窗口），在对话里输入 `/skills` 确认已加载。

### 方法 2：安装到全局（所有项目可用）

官方文档路径是 `~/.gemini/antigravity/skills/`，社区实测 `~/.gemini/config/skills/` 更可靠（两处都放也行，幂等）：

```bash
mkdir -p ~/.gemini/config/skills
cp -R skills/* ~/.gemini/config/skills/
```

### 方法 3：推到 GitHub 后用 CLI 安装

```bash
# 把 skills/ 推到你自己的仓库后：
npx skills add <你的github仓库> -y -g --skill paper-search
npx skills add <你的github仓库> -y -g --skill literature-review
npx skills add <你的github仓库> -y -g --skill office-docs
npx skills add <你的github仓库> -y -g --skill n8n-workflow
npx skills add <你的github仓库> -y -g --skill de-ai-gui
```

## 结构规范

```
<技能名>/
└── SKILL.md        # 技能本体：frontmatter(name/description) + 步骤指令
```

- `name`：技能名（小写连字符）
- `description`：Agent 何时该触发这个技能的描述（要写清触发场景）
- 正文：给 Agent 的分步指令，可含代码块、shell 命令、模板

## 使用示例

装好后直接在反重力对话里说：

- “用 paper-search 技能帮我找 5 篇 2025 年关于 agent memory 的 arXiv 论文，整理成 BibTeX”
- “用 literature-review 做一份 RAG 领域的文献综述，输出 docx”
- “用 office-docs 把这个文件夹里的 10 个 xlsx 合并成一张总表，按日期排序”
- “用 n8n-workflow 在 n8n 里创建一个‘每周五发销售周报’的工作流并激活”
- “用 de-ai-gui 把 paper-search-mcp 的检索功能包成一个 Streamlit 网页，不要 AI”
