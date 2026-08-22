# MCP 配置安装说明（Antigravity）

本目录提供两份可直接使用的 MCP 配置：

| 文件 | 作用 | 安装位置 |
|---|---|---|
| `mcp_config.global.json` | 科研 + 办公 + n8n 全家桶（推荐） | `~/.gemini/antigravity/mcp_config.json`（macOS/Linux）或 `%USERPROFILE%\.gemini\antigravity\mcp_config.json`（Windows） |
| `mcp_config.project.json` | 精简版（只留常用，放项目里） | 项目根目录 `.mcp.json` |

## 安装步骤

1. 打开 Antigravity → 右侧 **Agent 面板** → 顶部 **⋯** 菜单 → **MCP Servers** → **Manage MCP Servers** → **View raw config**（会打开全局 `mcp_config.json`）
2. 把本目录里 `mcp_config.global.json` 的 `mcpServers` 内容合并进去（**先备份原文件**）
3. 回到 Manage MCP Servers 页面点 **刷新/Refresh**
4. 在 `antigravity mcp list`（CLI）或面板里确认各服务器状态为已启用

> ⚠️ 不要照抄 VS Code 的 `mcp.json` 教程：Antigravity 里真正的配置入口是上面第 1 步的路径。

## 配置项说明

- 需要 API Key 的服务器默认 `"disabled": true`（避免启动报错），拿到 key 后填进 `env` 并把 `disabled` 删掉/改为 `false` 即可
- Antigravity **不支持 `${workspaceFolder}`**，所有路径写绝对路径
- 依赖相对路径的服务器建议显式传 `cwd`（社区已知问题：MCP 工作目录默认是 Antigravity 程序目录）
- HTTP 型服务器（填 `serverUrl` 的）无需安装任何东西，最快

## 各条目速查

| key | 是什么 | 需要什么 | 开箱即用 |
|---|---|---|---|
| `paper-search` | 论文检索/下载/阅读（20+ 学术源） | uvx + Python 3.10+ | ✅（可选 Unpaywall/CORE key） |
| `arxiv` | arXiv 轻量检索 | uvx | ✅ |
| `zotero` | 本地 Zotero 文献库 | 本地 Zotero 7+ 已运行 | ✅ |
| `filesystem` | 读写本地目录 | 绝对路径参数 | ✅ |
| `workspace-mcp` | Google Workspace 全家桶（Gmail/Drive/Docs/Sheets/Calendar…） | 首次 OAuth 登录 | ✅（浏览器授权） |
| `notion` | Notion 页面/数据库 | Notion Integration Token | ❌ 需 key |
| `exa` | 语义搜索 | EXA_API_KEY | ❌ 需 key |
| `firecrawl` | 网页抓取/深网研究 | FIRECRAWL_API_KEY | ❌ 需 key |
| `n8n-mcp` | 驱动 n8n（创建/执行工作流） | 本地 n8n + N8N_API_KEY | ✅（改路径+key） |

## 自建 HTTP 型 MCP（零安装）

在 `mcpServers` 里加一行即可，例如高德地图：

```json
{
  "mcpServers": {
    "amap-maps-http": {
      "serverUrl": "https://mcp.amap.com/mcp?key=你的高德Web服务key"
    }
  }
}
```

## 常见问题

- **服务器不加载**：确认 Node.js 18+ / Python 3.10+ / `uvx`、`npx` 在 PATH；看服务器日志；重启会话
- **启动慢**：`disabled: true` 的服务器不会启动，只开要用的
- **安全**：`env` 里的 key 会明文存本地，别把 `mcp_config.json` 提交到公开仓库
