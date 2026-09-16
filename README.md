# new

本仓库已接入 **git-sync v2.7.0**（来源：`arena/01a0a821-git-pull-arena`），与 Windows 本机双向同步。

| 项 | 值 |
|---|---|
| 工作分支 | `arena/01a0a90b-new` |
| 技能 | `skills/git-sync` v2.7.0 |
| 本机克隆建议目录 | `E:\0github\git-sync\new-01a0a90b`（勿覆盖已有 HQ 目录） |

## 本机首次打通

```powershell
cd E:\0github\git-sync
git clone -b arena/01a0a90b-new https://github.com/mqgg5630-cyber/new.git new-01a0a90b
cd new-01a0a90b
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\bootstrap.ps1 -Auto
.\doctor.ps1
.\watch.ps1 -Status
```

## 日常

```powershell
.\sync.ps1                 # 拉 Arena 最新
.\push.ps1 "msg"           # 本机改动推回
.\download.ps1 -Set final  # 交付物落地
```

助手侧每轮：`bash skills/git-sync/scripts/agent-sync.sh "feat: ..."`


## Hands-Free（解放双手，v2.7.0）

本仓库已打开 `hands_free`：本机值守自动 pull / 自动 push；Agent 用 `agent-handsfree.sh` 按成功标准自动收尾。

```powershell
# 本机一次（升级值守到 v2.7.0）
cd E:\0github\git-sync\new-01a0a90b
.\sync.ps1
.\watch.ps1 -Unregister ; .\watch.ps1 -Register
.\watch.ps1 -Status   # hands-free: master=True ...
```

说明：`deliverable/HANDS_FREE_v2.7.0.md`
