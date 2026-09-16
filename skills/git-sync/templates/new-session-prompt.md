# 新会话：用户一句话，助手自动装技能并与本机打通

> 用户**只发一句话**。完整动作清单在 `one-sentence.md`。
> 本文件给已经打开技能目录的人看；助手看到用户那句话就按 `one-sentence.md` 执行。

---

## 用户发的（只要这一句）

```text
安装 arena/01a0a821-git-pull-arena skills, 与本地打通
```

## 助手自动做的

1. 从 `arena/01a0a821-git-pull-arena` 把 `skills/git-sync` 装进**本仓库当前工作分支**（`agent-install.sh`）。
2. `agent-sync.sh` 提交推送。
3. 回复一段**已经填好仓库 / 分支 / 新文件夹名**的本机 PowerShell。
4. 本机克隆必须用新文件夹，禁止覆盖 `git-pull-arena` / `git-pull-arena-v268` / `git-pull-arena-s2`。

命令与回复模板见 [`one-sentence.md`](one-sentence.md)。

## 本机日常（打通之后）

```powershell
.\sync.ps1                 # 取
.\push.ps1 "说明"           # 传（静默，不弹窗）
.\watch.ps1 -Status        # 值守
.\doctor.ps1               # 不对劲先跑
```

双向验收：助手 `agent-sync.sh` 推一个小改动 → 本机 `.\sync.ps1` 看得到；本机 `.\push.ps1` 推一句 → 助手回执里能看到该提交。
