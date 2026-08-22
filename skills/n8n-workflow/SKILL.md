---
name: n8n-workflow
description: >
  Create, inspect, trigger, and de-AI-ify n8n workflows from Antigravity.
  Covers three modes: (1) drive n8n via the n8n-mcp MCP server or the n8n REST
  API; (2) call n8n workflows exposed as MCP tools (MCP Server Trigger node);
  (3) non-AI usage of the same workflows through webhooks + simple HTML forms.
  Use when the user mentions n8n, 工作流, 自动化流程, workflow automation, webhook,
  or wants an AI-independent automation endpoint.
---

# n8n Workflow（在反重力里调用 n8n 工作流）

n8n 是可自托管（Docker）、带 Web GUI 的可视化自动化平台。本技能覆盖三种用法。
**核心原则：把"确定性执行"交给 n8n 工作流，AI 只负责理解需求、填参数。**

## 用法 A：通过 n8n-mcp 直接操作 n8n（已配置 MCP 时）

前提：反重力里已配置 `n8n-mcp`（见 `mcp/mcp_config.global.json` 中的 `n8n-mcp` 条目）。

- 列出工作流：调用 `listWorkflows` 工具
- 激活/停用：`activateWorkflow(id)` / `deactivateWorkflow(id)`
- 执行：`executeWorkflow(id, data)` —— 传参走工作流的 Webhook/参数
- 创建：用 `createWorkflow` 提交 n8n JSON 定义（建议先让用户在 n8n GUI 里画好再导入）

示例对话：
> 用户："把 n8n 里‘销售周报’工作流激活，然后立刻跑一次"
> 步骤：`listWorkflows` 找到 id → `activateWorkflow` → `executeWorkflow`

## 用法 B：把 n8n 工作流当 MCP 工具调用（工作流已暴露成 MCP）

n8n 里用 **MCP Server Trigger** 节点把工作流暴露成 MCP 工具后，反重力把该端点配成
`serverUrl` 的 MCP server。此时：
- 用 `tools/list` 看可用工作流工具
- 调用时严格按工具参数 schema 填参；参数不确定时**问用户**，不要瞎编

## 用法 C：去AI化——同一工作流的非 AI 入口（重点）

同一份 n8n 工作流可以有完全不需要 AI 的用法：

1. **Webhook 触发（最常用，零 AI）**：工作流首节点用 Webhook 节点，任何程序/脚本/同事都能调，不需要 AI：
   - Windows PowerShell：`curl.exe -X POST "http://localhost:5678/webhook/<Path>" -H "Content-Type: application/json" -d '{\"query\":\"关键词\"}'`
   - 注意：Webhook 的 Path 在节点设置里（如 `crossref-bibtex`），URL = `http://localhost:5678/webhook/<Path>`
2. **定时触发（全自动）**：加 Schedule Trigger 节点，Cron 表达式如 `0 9 * * *`（每天 9:00）或 `0 17 * * 5`（每周五 17:00）
3. **表单触发（给同事自助）**：加 n8n Form Trigger 节点，生成网页表单 URL，同事填参数自动跑流程
4. **GUI 按钮触发**：用 Streamlit/tkinter 包一个按钮，点击即 POST webhook（模板见本包 `examples/n8n_crossref_gui.py`）
5. **n8n 内建 Webhook 测试**：n8n 编辑界面直接点 "Execute workflow" 手测

给用户的交付物：**一个 webhook URL + 一个参数 JSON 示例 + 一个 GUI/表单入口**。
去AI化的判断标准：工作流里没有任何 LLM 节点 + 触发方式不依赖 AI 对话（webhook/定时/表单/按钮均可）。

## 检查清单（任何用法都过一遍）

- [ ] n8n 在跑吗？`http://localhost:5678` 能否打开
- [ ] API Key 配好了吗？（n8n 设置 → API）环境变量 `N8N_API_KEY`
- [ ] 工作流已 **Active**（激活）状态，测试执行过一次成功
- [ ] 参数命名与 n8n 节点里的字段一致

## 注意

- n8n 是 fair-code 许可：自用免费，商用托管有限制，部署前看许可
- 敏感凭据（数据库密码、API key）放 n8n Credentials 里，不要写进工作流 JSON 明文
- 去AI化不等于移除 AI 入口：工作流可以同时有 MCP 入口和 Webhook 入口，互不影响
