# 反重力（Antigravity）科研办公 MCP / Skills 推荐 · n8n 接入 · 去AI化方案

一套面向 Google Antigravity 的"科研 + 办公"扩展包：帮你选好能直接用的 MCP 和 Skills，
教你接 n8n，并把整套东西**去AI化**（改成不依赖 AI 的 GUI / 独立程序）。

## 📦 包里有什么

| 路径 | 内容 |
|---|---|
| `反重力Antigravity科研办公MCP与Skills推荐.md` | 主报告（Markdown） |
| `反重力Antigravity科研办公MCP与Skills推荐.docx` | 主报告（Word 版，可直接分享） |
| `mcp/` | MCP 配置文件（科研 + 办公 + n8n，导入即用） |
| `skills/` | 5 个可直接安装的 Agent Skills（论文检索、文献综述、办公批处理、n8n 工作流、去AI化） |
| `examples/` | 2 个"去AI化"可运行示例（Streamlit 论文检索 GUI、arXiv 日报脚本） |
| `tools/md2docx.py` | Markdown → Word 转换脚本（改完报告重新生成 docx 用） |

## 🚀 快速开始

```bash
# 1. 装 MCP：把 mcp/mcp_config.global.json 的内容合并进
#    ~/.gemini/antigravity/mcp_config.json（Antigravity Agent面板 → ⋯ → MCP Servers → View raw config）
# 2. 装 Skills：把 skills/* 拷到项目 .agents/skills/ 或全局 ~/.gemini/config/skills/
cp -R skills/* .agents/skills/
# 3. （可选）跑去AI化示例
pip install streamlit mcp && streamlit run examples/paper_search_gui.py
```

详细说明见主报告，尤其是：

- [科研/办公 MCP 推荐清单](反重力Antigravity科研办公MCP与Skills推荐.md#3-科研方向强烈推荐的-mcp)
- [Antigravity 调用 n8n 的三条路径](反重力Antigravity科研办公MCP与Skills推荐.md#6-反重力能不能调用-n8n适合反重力的-n8n-agent-项目)
- [去AI化四条路线](反重力Antigravity科研办公MCP与Skills推荐.md#7-去ai化把-mcp--skills--agent-变成不依赖-ai-的-gui-或独立程序)

## ⚠️ 提示

- 开源项目版本迭代快，安装命令以各项目 README 为准
- API Key 请妥善保管，不要把 `mcp_config.json` 提交到公开仓库
