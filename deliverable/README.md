# 交付物

| 文件 | 说明 |
|---|---|
| `git-sync-local-connect.docx` | 本机打通说明（原生 Word，可编辑，无贴图） |
| `git-sync-local-connect.pptx` | 本机打通 5 页幻灯片（原生形状/文本框，可编辑，无贴图） |

## 落到本机

```powershell
cd E:\0github\git-sync\new-01a0a90b
.\sync.ps1
.\download.ps1 -Set final
# 镜像目录：E:\0github\git-sync\new-01a0a90b_out\deliverable\
```

或直接打开仓库内的 `deliverable\`。

## 回传测试（本机 → Arena）

```powershell
cd E:\0github\git-sync\new-01a0a90b
.\sync.ps1
New-Item -ItemType Directory -Force results\local-roundtrip | Out-Null
Set-Content -Encoding utf8 results\local-roundtrip\from-local.txt "local->arena roundtrip OK $env:COMPUTERNAME $(Get-Date -Format o)"
.\push.ps1 "test: local -> arena roundtrip"
Get-Content results\local-roundtrip\from-local.txt
```

推送成功后，在 Arena 会话回复「已 push」。
