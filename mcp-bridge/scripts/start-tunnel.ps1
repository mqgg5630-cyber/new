# start-tunnel.ps1 —— 用 Cloudflare Tunnel 把 127.0.0.1:8787 安全地暴露到公网
#
# 两种模式:
#   .\start-tunnel.ps1                  快速模式：临时 trycloudflare.com 域名，随开随用
#   .\start-tunnel.ps1 -Named mcp-agv   命名模式：固定域名 + 可加 Cloudflare Access（推荐长期用）
#
# 首次会自动下载 cloudflared.exe 到 bin\ 目录。

param(
    [int]$Port = 8787,
    [string]$Named = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$BinDir = Join-Path $Root "bin"
$Exe    = Join-Path $BinDir "cloudflared.exe"

if (-not (Test-Path $Exe)) {
    New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
    $url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    Write-Host "[下载] cloudflared ..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $url -OutFile $Exe -UseBasicParsing
    Write-Host "[下载] 完成 -> $Exe" -ForegroundColor Green
}

# 先确认网关活着，避免开了隧道却指向空端口
try {
    $h = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/healthz" -TimeoutSec 5
    Write-Host "[检查] 网关在线: $($h.service) $($h.version)" -ForegroundColor Green
} catch {
    Write-Host "[错误] http://127.0.0.1:$Port 没有响应，请先运行 scripts\start-gateway.ps1" -ForegroundColor Red
    exit 1
}

if ($Named) {
    Write-Host "[命名隧道] 运行 $Named" -ForegroundColor Cyan
    Write-Host "  未创建过请先执行:" -ForegroundColor DarkGray
    Write-Host "    bin\cloudflared.exe tunnel login" -ForegroundColor DarkGray
    Write-Host "    bin\cloudflared.exe tunnel create $Named" -ForegroundColor DarkGray
    Write-Host "    bin\cloudflared.exe tunnel route dns $Named mcp.你的域名.com" -ForegroundColor DarkGray
    & $Exe tunnel run --url "http://127.0.0.1:$Port" $Named
} else {
    Write-Host "[快速隧道] 启动中，下面会打印一个 https://xxx.trycloudflare.com 地址" -ForegroundColor Cyan
    Write-Host "把【该地址 + token】一起发给 Agent 即可。关闭窗口隧道即失效。" -ForegroundColor Cyan
    & $Exe tunnel --url "http://127.0.0.1:$Port" --no-autoupdate
}
