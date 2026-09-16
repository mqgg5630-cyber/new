# 用户一句话 —— 助手必须自动跑完全套

用户以后在任何新 Arena 会话里**只发这一句**（有无 markdown 链接都算）：

```text
安装 arena/01a0a821-git-pull-arena skills, 与本地打通
```

等价说法（都触发同一套动作）：

- `安装 https://github.com/mqgg5630-cyber/git-pull-arena/tree/arena/01a0a821-git-pull-arena 的 skills，与本地打通`
- `安装 [arena/01a0a821-git-pull-arena](https://github.com/mqgg5630-cyber/git-pull-arena/tree/arena%2F01a0a821-git-pull-arena) skills, 与本地打通`

助手**不要再向用户要长提示词**。立刻按下面做完，然后只回本机那一段 PowerShell。

## 助手必须执行（不要问、不要改命令）

当前仓库根目录：

```bash
git clone --quiet --depth 1 -b arena/01a0a821-git-pull-arena \
  https://github.com/mqgg5630-cyber/git-pull-arena.git /tmp/git-sync-src \
  && bash /tmp/git-sync-src/skills/git-sync/scripts/agent-install.sh

bash skills/git-sync/scripts/agent-sync.sh "feat: install git-sync skill"
```

然后读：

```bash
git remote get-url origin
git rev-parse --abbrev-ref HEAD
```

HEAD 若是 `main` / `master`：**停**，先切到本会话工作分支再装。

## 助手必须回复用户的本机代码（填好，可直接粘）

禁止文件夹名：`git-pull-arena`、`git-pull-arena-v268`、`git-pull-arena-s2`（已占用，覆盖即破坏旧克隆）。

新文件夹建议：`<仓库名>-<工作分支短号>`，例如 `image-to-editable-pptx-01a04caf`。

```powershell
cd E:\0github\git-sync
git clone -b <BRANCH> <ORIGIN_URL> <NEW_FOLDER>
cd <NEW_FOLDER>
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\bootstrap.ps1 -Auto
.\doctor.ps1
.\watch.ps1 -Status
```

把 `<BRANCH>` / `<ORIGIN_URL>` / `<NEW_FOLDER>` 换成刚才读到的真值。不要留占位符。

成功标志：`doctor.ps1` 的 branch 是工作分支、ahead/behind = 0/0、末尾 watcher / heartbeat / auth 三行正常。

`bootstrap.ps1 -Auto`（内部 `.\watch.ps1 -Register`）会**暂停其他会话**的 `git-sync-watch-*`：Stop + Disable + 杀掉循环进程，**不删除**计划任务。台账在 `%LOCALAPPDATA%\git-sync\parked.json`。不想动别人就 `-Register -KeepOthers`。

回到本会话 HQ（恢复本克隆、暂停其他会话）：

```powershell
cd E:\0github\git-sync\git-pull-arena-s2
.\watch.ps1 -Focus
```

一次恢复所有被暂停的值守：`.\watch.ps1 -RestoreParked`
