# mcp-bridge · 让云端 Agent 安全调用你本地的 MCP

> 目标：Arena 沙箱里的我（Agent）能调用 `E:\0mcp-agv` 下你自己的 MCP 服务，
> 同时保证 **除了拿到 token 的我，别人谁都进不来**。

---

## 一、先把几个问题说清楚

| 你的问题 | 答案 |
|---|---|
| 你（沙箱）能直连我本地 MCP 吗？ | **不能。** 沙箱在云端，和你的 `E:\0mcp-agv` 不在同一网络，只能主动访问公网 HTTPS。必须有一层公网入口。 |
| 是不是必须内网穿透？ | 是，必须有"从公网能到达你本机"的通道。区别只是用什么通道、安不安全。 |
| 一定要用 Docker 吗？ | **不用。** Windows 上跑一个 `cloudflared.exe` 就行，比 Docker 轻得多。Docker 版本作为方案 B 也给了（`docker-compose.yml`）。 |
| 方案二（Docker）稳定吗？ | 隧道本身一样稳，但如果 MCP 要读你 Windows 本机文件/串口/AGV 硬件，容器里挂载和设备透传很折腾。**你这个场景推荐方案 A（原生 PowerShell）。** |
| Arena 沙箱能连吗？ | 能。沙箱可以出网访问 HTTPS，我已在沙箱验证过整套网关逻辑（12/12 自检通过）。 |
| 直接穿透安全吗？ | **不安全。** 裸暴露 = 谁知道 URL 谁就能调你本机工具，甚至读写文件。所以本方案不暴露 MCP，只暴露一个带鉴权的网关。 |
| 能帮我干更多科研/办公活吗？ | 能。我通过 HTTP 调你的 MCP 工具（检索、批量处理文档、跑数据）。**限制**：不是原生 MCP 长连接；每个会话沙箱是新的，URL + token 要重新给我一次。 |

---

## 二、架构（安全的关键在这张图）

```
 你的电脑 E:\0mcp-agv                          公网                Arena 沙箱
┌──────────────────────────────────────┐                        ┌──────────────┐
│  你的 MCP 进程 (stdio 子进程)          │                        │              │
│  ❗不监听任何端口，只能被网关唤起        │                        │   Agent(我)  │
│            ▲                          │                        │      │       │
│            │ stdin/stdout             │                        │      │       │
│  ┌─────────┴──────────┐               │   Cloudflare Tunnel    │      ▼       │
│  │  gateway.py        │◄──出站长连接───┼───►  https://xxx  ◄────┼── client.py  │
│  │  127.0.0.1:8787    │  （不开放端口） │      (TLS 加密)         │              │
│  │  ✔ Bearer Token    │               │                        │              │
│  │  ✔ 工具白名单       │               │                        │              │
│  │  ✔ 只读模式         │               │                        │              │
│  │  ✔ 限速 + 审计日志  │               │                        │              │
│  └────────────────────┘               │                        │              │
└──────────────────────────────────────┘                        └──────────────┘
```

**为什么这样就安全：**

1. **路由器上不开任何端口**。cloudflared 是你的电脑**主动往外**建连接，不需要公网 IP、不需要端口映射，扫描器扫不到你。
2. **MCP 本体永不联网**。它只是网关的一个 stdio 子进程，网关不转发就没人碰得到。
3. **五层防线**：Bearer Token（常数时间比对，防时序攻击）→ 可选 IP 白名单 → method 白名单 → 工具白名单 / 只读拦截 → 限速。
4. **全量审计**。谁在什么时候调了哪个工具、耗时多久，都写进 `logs/audit.jsonl`。
5. **随时切断**。关掉 cloudflared 窗口，公网入口立刻消失。

---

## 三、方案 A（推荐）：Windows 原生，5 分钟跑通

在 `E:\0mcp-agv` 下：

```powershell
# 0. 克隆仓库（如果还没有）
git clone https://github.com/mqgg5630-cyber/new.git
cd new\mcp-bridge

# 1. 启动网关（首次会自动生成配置和 token）
powershell -ExecutionPolicy Bypass -File scripts\start-gateway.ps1
```

屏幕会打印：

```
==================== 你的访问凭证 ====================
MCP_BRIDGE_TOKEN = xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
======================================================
mcp-bridge 1.0.0 已启动 → http://127.0.0.1:8787
```

**另开一个 PowerShell 窗口**：

```powershell
cd E:\0mcp-agv\new\mcp-bridge
powershell -ExecutionPolicy Bypass -File scripts\start-tunnel.ps1
```

会打印一个地址，例如：

```
https://calm-river-1234.trycloudflare.com
```

**然后把这两样东西发给我：**

```
URL:   https://calm-river-1234.trycloudflare.com
TOKEN: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

我就能开始调你的 MCP 了。

### 自测一下（可选）

```powershell
$env:MCP_BRIDGE_URL="https://calm-river-1234.trycloudflare.com"
python client.py health
python client.py tools demo
python client.py call demo echo '{\"text\":\"通了\"}'
```

---

## 四、把 demo 换成你自己的 MCP

编辑 `bridge_config.json` 的 `servers` 段：

```json
"agv": {
  "enabled": true,
  "command": ["python", "-m", "your_agv_mcp"],
  "cwd": "E:\\0mcp-agv",
  "env": { "AGV_PROFILE": "readonly" },
  "read_only": true,
  "allow_tools": ["query_status", "search_papers", "read_report"],
  "deny_tools": ["move_robot", "shutdown", "reset"],
  "timeout_seconds": 180
}
```

字段含义：

| 字段 | 作用 |
|---|---|
| `command` | 启动 MCP 的命令行数组。和你在 Antigravity `mcp_config.json` 里写的一样。 |
| `read_only` | `true` 时，工具名里含 `write/delete/exec/shell/...` 等特征词的一律 403。**建议先保持 true。** |
| `allow_tools` | 白名单。**非空时只有列表里的工具能调**，其他一律隐藏 + 403。最强的一道锁。 |
| `deny_tools` | 黑名单，优先级最高，白名单也拦不住它。 |
| `timeout_seconds` | 单次调用超时，防止长任务卡死网关。 |

> **建议起步姿势**：`read_only: true` + `allow_tools` 只写你真正需要我用的 3~5 个工具。
> 等验证顺手了，再逐个放开写操作。

---

## 五、想要更强的安全（长期使用推荐）

临时隧道 URL 虽然随机、不可枚举，但本质上是"知道 URL + token 就能用"。
长期跑建议升级成**命名隧道 + Cloudflare Access**，多一道身份验证：

```powershell
bin\cloudflared.exe tunnel login
bin\cloudflared.exe tunnel create mcp-agv
bin\cloudflared.exe tunnel route dns mcp-agv mcp.你的域名.com
.\scripts\start-tunnel.ps1 -Named mcp-agv
```

然后在 Cloudflare Zero Trust 控制台给 `mcp.你的域名.com` 加一条 Access 策略
（Service Auth → Service Token），这样请求需要同时带 Access 的
`CF-Access-Client-Id/Secret` **和** 我们自己的 Bearer token 才放行。

安全强度排序：

```
裸端口映射(❌千万别)  <  临时隧道+Token(✅够用)  <  命名隧道+Access+Token(✅✅长期推荐)
```

### 日常安全习惯

- **用完就关**：不干活时关掉 cloudflared 窗口，公网入口消失。
- **定期换 token**：`[Environment]::SetEnvironmentVariable("MCP_BRIDGE_TOKEN", "新token", "User")` 后重启网关。
- **看审计**：`Get-Content logs\audit.jsonl -Tail 20`，出现 `deny_auth` 说明有人在试探。
- **别提交私密文件**：`bridge_config.json` / `.env` / `logs/` 已在 `.gitignore` 里。

---

## 六、方案 B：Docker

见 `docker-compose.yml`。适合 MCP 本身能容器化的情况；
如果 MCP 要摸 Windows 本机文件或 AGV 硬件，请用方案 A。

```bash
cp .env.example .env      # 填 MCP_BRIDGE_TOKEN
docker compose up -d
docker compose logs -f tunnel
```

注意 compose 里 gateway **故意不做 ports 映射** —— 只有同一 docker 网络里的
tunnel 容器能访问它，宿主机端口都不开。

---

## 七、API 速查

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/healthz` | 健康检查，**免鉴权**（只返回服务器名和存活状态，不泄露工具信息） |
| GET | `/v1/servers` | 列出已加载的 MCP 服务器及其策略 |
| GET | `/v1/servers/{name}/tools` | 列工具（已按策略过滤） |
| POST | `/v1/servers/{name}/tools/{tool}/call` | 便捷调用，body: `{"arguments": {...}}` |
| POST | `/v1/servers/{name}/rpc` | 原生 JSON-RPC 透传，body: `{"method":"...","params":{...}}` |

除 `/healthz` 外全部要求 `Authorization: Bearer <token>`。

---

## 八、文件清单

| 文件 | 说明 |
|---|---|
| `gateway.py` | 安全网关本体，**零第三方依赖**，Python 3.9+ |
| `bridge_config.example.json` | 配置模板，复制成 `bridge_config.json` 用 |
| `demo_mcp_server.py` | 最小 MCP 服务器，用来先跑通链路 |
| `client.py` | 客户端 / 命令行工具（我在沙箱里也用它） |
| `smoke_test.py` | 端到端自检，12 项断言 |
| `scripts/start-gateway.ps1` | Windows 一键启网关（自动生成 token） |
| `scripts/start-tunnel.ps1` | Windows 一键起隧道（自动下载 cloudflared） |
| `docker-compose.yml` / `.env.example` | 方案 B |

---

## 九、自检结果

在 Arena 沙箱实测：

```
== mcp-bridge 端到端自检 ==
  ✅ 网关健康检查 /healthz          ✅ Bearer token 鉴权通过
  ✅ 错误 token 被拒绝 (401)        ✅ 无 token 被拒绝 (401)
  ✅ tools/list 可用                ✅ 危险工具 danger_write 已被策略隐藏
  ✅ 调用 echo 成功                 ✅ 调用 sum 成功
  ✅ 只读策略拦截写操作 (403)        ✅ 原生 JSON-RPC 透传可用
  ✅ 非白名单 method 被拒 (403)      ✅ 审计日志已写入
结果: 12 通过 / 0 失败
```

---

## 十、常见问题

**Q: 隧道 URL 每次重启都变，很烦？**
A: 用命名隧道（第五节），域名固定。

**Q: 我关电脑了会怎样？**
A: 隧道断开，我这边调用返回连接错误。重开脚本即可，token 不变。

**Q: 会不会有人猜到我的 trycloudflare 地址？**
A: 子域名是随机的，且即使猜到，没有 token 也是 401，还会被限速和记录。

**Q: 我怎么知道有没有被人偷用？**
A: `logs/audit.jsonl` 里每一次调用都有 IP、工具名、耗时。

**Q: Antigravity 里已经配好的 MCP，怎么搬过来？**
A: 把 `mcp_config.json` 里那个 server 的 `command` + `args` 拼成一个数组，
   填进 `bridge_config.json` 的 `command` 字段，`env` 原样抄过来。
