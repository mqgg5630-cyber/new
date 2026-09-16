# git-sync v2.7.0 —— 解放双手（Hands-Free）

> 目标：你**不用再手动**跑 `.\sync.ps1` / `.\push.ps1`。  
> Arena 做完 → 本机值守自动拉 → 你本机改完自动推 → Agent 自动验收成功标准 → **自动收尾停下**。

## 一、链路（一次配好，之后零操作）

```
你本机（值守每 N 分钟一轮，默认 2）          Arena Agent
─────────────────────────────────          ──────────────────────────
auto_pull  = .\\sync.ps1                   agent-sync.sh "feat: ..."
auto_push  = 有脏文件就 .\\push.ps1 -NoPrompt
                                           agent-handsfree.sh --request "..."
  若 handshake=awaiting_check:               ├─ 等值守推回 check 结论
     跑 check_cmd（含 success_criteria）  ──►├─ agent-criteria.sh
     推回 passed/failed                      └─ 全过 → --accept → 停
```

## 二、本机只做一次

```powershell
cd E:\0github\git-sync\new-01a0a90b
.\sync.ps1
.\auth.ps1 -Setup -Verify          # 免点击推送（必须）
.\watch.ps1 -Unregister
.\watch.ps1 -Register              # 载入 v2.7.0 循环（hands_free 已在 config 打开）
.\watch.ps1 -Status                # 应看到 hands-free: master=True auto_pull=True auto_push=True
```

之后：

- Agent 推了新文件 → 最多 2 分钟，本机自动出现（`auto_pull`）
- 你在本机新建/改文件 → 最多 2 分钟，自动 push 回 Arena（`auto_push`，提交信息 `local: auto <时间>`）
- Agent 发起验收 → 本机自动跑检查 + 推结论；Agent 侧 `agent-handsfree.sh` 看到成功标准满足就 `--accept` 停下

## 三、配置（`skills/git-sync/sync.config.json`）

| 键 | 本仓库默认 | 含义 |
|---|---|---|
| `hands_free` | `true` | 总开关；true 时强制 auto_pull + auto_push |
| `auto_pull` | `true` | 每轮值守先 `sync.ps1` |
| `auto_push` | `true` | 工作区有非排除脏文件 → 静默 push |
| `auto_push_prefix` | `local: auto` | 自动提交信息前缀 |
| `auto_push_exclude` | `.env` / `*.pem` / `*secret*` … | 永不自动提交的路径 glob |
| `success_criteria` | `results/status/success_criteria.json` | 成功标准文件 |

关掉（回到手动）：

```json
"hands_free": false,
"auto_pull": false,
"auto_push": false
```

然后 `.\\watch.ps1 -Unregister ; .\\watch.ps1 -Register`。

## 四、成功标准（本仓库示例）

`results/status/success_criteria.json`：

- 必须存在：`deliverable/*.docx`、`deliverable/*.pptx`、`results/local-roundtrip/from-local.txt`
- `from-local.txt` 必须含 `local->arena roundtrip OK`
- 两个 Office 文件 ≥ 5 KB

Agent 判定：

```bash
bash skills/git-sync/scripts/agent-criteria.sh          # exit 0 = 过
bash skills/git-sync/scripts/agent-handsfree.sh \
     --sync "feat: ..." \
     --request "verify hands-free deliverables" \
     --timeout 600
# exit 0 = 本机检查过 + 标准过 + 已 accept，本轮结束
```

## 五、安全边界

1. **永不**自动 push 到 `main`/`master`（`push.ps1` 硬拒绝）
2. **永不**自动提交 `auto_push_exclude` 命中的路径（密钥/令牌）
3. 推送全程 `GIT_TERMINAL_PROMPT=0`；没凭据 → 快速失败写心跳，**不弹窗**
4. 成功标准不过 → Agent **不会** `--accept`，会修了再来

## 六、和旧版的关系

| 版本 | 能力 |
|---|---|
| ≤ v2.6.9 | 值守只在 `awaiting_check` 时动；平时要手跑 sync/push |
| **v2.7.0** | 值守每轮 auto_pull + auto_push；Agent 一条 `agent-handsfree.sh` 闭环到 accept |

升级后**必须重注册值守**（计划任务写死启动命令，旧循环不会加载新代码）。
