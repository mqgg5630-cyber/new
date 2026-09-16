# 交付物

| 文件 | 说明 |
|---|---|
| `git-sync-local-connect.docx` | 本机打通说明（原生 Word，可编辑） |
| `git-sync-local-connect.pptx` | 本机打通 5 页幻灯片（原生形状，可编辑） |
| `HANDS_FREE_v2.7.0.md` | **解放双手**功能说明（v2.7.0 新） |

## 落到本机

```powershell
cd E:\0github\git-sync\new-01a0a90b
.\sync.ps1
.\download.ps1 -Set final
# → E:\0github\git-sync\new-01a0a90b_out\deliverable\
```

## Hands-free 一次升级

```powershell
.\sync.ps1
.\watch.ps1 -Unregister ; .\watch.ps1 -Register
.\watch.ps1 -Status
# 应看到 hands-free: master=True auto_pull=True auto_push=True
```
