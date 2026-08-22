---
name: de-ai-gui
description: >
  De-AI-ify MCP tools and AI-dependent workflows into standalone GUI programs
  that run without any LLM: wrap MCP tools in Streamlit/Gradio/tkinter UIs,
  convert them to plain CLI scripts, or port them to GUI automation platforms
  (n8n without AI nodes, Node-RED, Activepieces). Use when the user asks to
  去AI化, 去掉AI, 改成GUI, 独立程序, 不依赖AI, run without AI, standalone app,
  or make an MCP/skill/agent usable without an LLM.
---

# De-AI GUI（把 MCP/Agent 流程去AI化，包成独立 GUI）

**核心理念：MCP 的工具层和 AI 决策层可以解耦。MCP Server 本身就是普通程序，
AI 只是调用方。去掉 AI 后，工具照常可用，只需要换一个"驱动者"。**

## 第 1 步：分析目标流程，分类处理

| 流程类型 | 推荐去AI化路线 |
|---|---|
| 已有 MCP server，想保留协议层 | 路线 A：非 AI 的 MCP 客户端（Enola / MCPHost / 官方 SDK） |
| 想要自己控制的图形界面 | 路线 B：SDK 调用 + Streamlit/tkinter 包 GUI（本技能模板） |
| 多步确定性流程（抓取→处理→通知） | 路线 C：n8n（去掉 AI 节点）/ Node-RED / Activepieces |
| 高频小任务，要最轻量 | 路线 D：纯脚本 + cron/计划任务 + 可选 tkinter 输入框 |

## 第 2 步：路线 B 标准做法（包 GUI）

1. **找到 MCP 工具的命令**（如 paper-search-mcp → `uvx paper-search-mcp`）
2. **用官方 Python SDK 调用**：

```python
# gui_skel.py —— 骨架
import asyncio, streamlit as st
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def call_tool(tool_name: str, args: dict):
    params = StdioServerParameters(command="uvx", args=["<你的mcp包>"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await session.call_tool(tool_name, args)

st.title("工具名（无AI版）")
q = st.text_input("输入")
if st.button("执行"):
    st.json(asyncio.run(call_tool("tool_name", {"query": q})))
```

3. **运行**：`streamlit run gui.py` → 浏览器打开即是纯 GUI
4. 可换 `tkinter` 做桌面版（离线、无需浏览器）；或 `gradio` 更快出原型

## 第 3 步：路线 C 标准做法（n8n 去 AI 节点）

- 删除工作流里的所有 AI/LLM 节点，保留：Webhook/Schedule + 工具节点 + 输出节点
- 触发入口：Webhook URL + 表单页（见 `n8n-workflow` 技能）
- 可选：给流程加 n8n 的 Error Workflow 做失败通知

## 第 4 步：交付清单

- [ ] 目标流程里没有对 LLM API 的调用（grep 一遍代码/工作流）
- [ ] 有 GUI 入口（网页/桌面/表单）或定时入口
- [ ] 断网/无 key 环境下能跑通核心功能（本地库类工具如 office-docs 应完全离线可用）
- [ ] 给用户一行启动命令（如 `streamlit run gui.py` 或 `python app.py`）

## 注意

- 半去AI方案（本地 Ollama 小模型）不违反"不依赖云端 AI"，可作兜底
- 去AI化后原 MCP/AI 入口依然保留，两条路径共存
- 模板与更多示例见本包 `examples/paper_search_gui.py`
