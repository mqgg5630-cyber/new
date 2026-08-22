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

> **装到独立目录 `new1`，不动你原来的 `E:\0mcp-agv\new`。**
> 如果你之前克隆过 `new`，那是旧副本、没有本分支，所以 `git checkout` 会报
> `did not match any file(s) known to git`。重新克隆到 `new1` 即可。

```powershell
cd E:\0mcp-agv

# 1. 克隆到 new1（-b 直接切到本分支，不会碰原来的 new 目录）
git clone -b arena/01a02938-new https://github.com/mqgg5630-cyber/new.git new1

# 2. 一键初始化 + 自检
powershell -ExecutionPolicy Bypass -File new1\mcp-bridge\scripts\bootstrap.ps1

# 3. 进目录
cd new1\mcp-bridge
```

然后开两个窗口：

```powershell
# 窗口 1 —— 启动网关（首次会自动生成配置和 token）
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
cd E:\0mcp-agv\new1\mcp-bridge
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

## 四、穿透通了之后，还需要依赖 MCP 吗？

**不需要。MCP 只是"怎么描述一个能力"的一种标准格式，不是能力本身。**

要分清三件事：

| 层 | 作用 | 能不能换掉 |
|---|---|---|
| **隧道**（cloudflared） | 只负责把字节从公网搬到你本机，**它不提供任何能力** | 可换（frp/ngrok），但 cloudflared 最省事最安全 |
| **网关**（gateway.py） | 鉴权、白名单、只读、限速、审计 | 建议保留，这是安全的核心 |
| **能力层** | 真正干活的代码 | **MCP 只是选项之一** |

所以能力层有两条路，本仓库两条都给你实现了：

### 路线 1：挂现成的 MCP（复用生态）

社区已经写好的 MCP（filesystem、arxiv、zotero、Excel、浏览器…）直接填进
`bridge_config.json` 的 `command` 就能用。好处是不用自己写。

### 路线 2：不用 MCP，直接写普通 Python 函数 ⭐

打开 `my_tools.py`，写一个普通函数就行：

```python
def csv_summary(path: str, rows: int = 5) -> dict:
    """读取 CSV，返回列名、总行数和前几行样例。"""
    ...
```

`local_tools_server.py` 会自动把它变成一个标准工具：
函数名 → 工具名，docstring → 工具描述，类型注解 → 参数 schema。
**你完全不用懂 MCP 协议，也不用装任何 MCP SDK。**

仓库里已内置 5 个示例函数，实测输出：

```
machine_info   -> {"type":"object","properties":{}}
find_files     -> {... "pattern":{"type":"string","default":"*"}, "limit":{"type":"integer","default":100}}
read_text      -> {... "required":["path"]}
csv_summary    -> {... "required":["path"]}
run_agv_script -> {... "required":["script"]}
被策略隐藏: ['write_note']       ← 只读模式自动拦截了写操作
```

其中 `run_agv_script` 特别有用：它能运行你工作目录里**任何已有的 .py 脚本**并返回输出。
也就是说你以前写的所有科研脚本，不用改一行，立刻变成我能调用的能力。

### 那"什么能力都有了"吗？

诚实地说 —— **能力上限 = 你在 `my_tools.py` 里暴露了什么 + 你允许了什么**，不是无限的。

- ✅ 能做：读写你本机文件、跑你的本地脚本、查你的本地数据库、操作 Excel/Word、
  调你内网的服务、控制 AGV（如果你写了对应函数并放行）
- ❌ 做不到：我"自动"知道你电脑上有什么。每一项能力都必须你先写成函数 / 挂上 MCP，
  并在 `allow_tools` 里放行 —— **这个限制是特性不是缺陷**，它正是安全的来源。
- ⚠️ 别做：写一个 `run_any_command(cmd)` 把整个 shell 暴露出来。那等于把你电脑的
  完全控制权放到公网上，一旦 token 泄露后果不可控。要放开也请用白名单式的具体函数。

---

## 五、把 demo 换成你自己的 MCP


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

## 六、想要更强的安全（长期使用推荐）

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

## 七、方案 B：Docker

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

## 八、API 速查

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/healthz` | 健康检查，**免鉴权**（只返回服务器名和存活状态，不泄露工具信息） |
| GET | `/v1/servers` | 列出已加载的 MCP 服务器及其策略 |
| GET | `/v1/servers/{name}/tools` | 列工具（已按策略过滤） |
| POST | `/v1/servers/{name}/tools/{tool}/call` | 便捷调用，body: `{"arguments": {...}}` |
| POST | `/v1/servers/{name}/rpc` | 原生 JSON-RPC 透传，body: `{"method":"...","params":{...}}` |

除 `/healthz` 外全部要求 `Authorization: Bearer <token>`。

---

## 九、文件清单

| 文件 | 说明 |
|---|---|
| `gateway.py` | 安全网关本体，**零第三方依赖**，Python 3.9+ |
| `bridge_config.example.json` | 配置模板，复制成 `bridge_config.json` 用 |
| `demo_mcp_server.py` | 最小 MCP 服务器，用来先跑通链路 |
| `local_tools_server.py` | **不用懂 MCP** 的适配器：把普通 Python 函数自动变成工具 |
| `my_tools.py` | **你写自己能力的地方**，普通函数即可，内置 5 个示例 |
| `client.py` | 客户端 / 命令行工具（我在沙箱里也用它） |
| `smoke_test.py` | 端到端自检，12 项断言 |
| `scripts/start-gateway.ps1` | Windows 一键启网关（自动生成 token） |
| `scripts/start-tunnel.ps1` | Windows 一键起隧道（自动下载 cloudflared） |
| `scripts/bootstrap.ps1` | 一键克隆/更新到 `new1` + 自检 |
| `docker-compose.yml` / `.env.example` | 方案 B |

---

## 十、自检结果

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

## 十一、常见问题

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
