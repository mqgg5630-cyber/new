# start-gateway.ps1 —— 启动 mcp-bridge 安全网关（只监听 127.0.0.1）
# 用法: 右键 -> 使用 PowerShell 运行，或   powershell -ExecutionPolicy Bypass -File scripts\start-gateway.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

# ---- 1. 配置文件 ----
if (-not (Test-Path "bridge_config.json")) {
    Copy-Item "bridge_config.example.json" "bridge_config.json"
    Write-Host "[初始化] 已生成 bridge_config.json，请按需修改 servers 部分。" -ForegroundColor Yellow
}

# ---- 2. Token：首次生成并保存到用户环境变量 ----
if (-not $env:MCP_BRIDGE_TOKEN) {
    $saved = [Environment]::GetEnvironmentVariable("MCP_BRIDGE_TOKEN", "User")
    if ($saved) {
        $env:MCP_BRIDGE_TOKEN = $saved
    } else {
        $bytes = New-Object byte[] 32
        [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
        $token = [Convert]::ToBase64String($bytes).TrimEnd('=').Replace('+','-').Replace('/','_')
        [Environment]::SetEnvironmentVariable("MCP_BRIDGE_TOKEN", $token, "User")
        $env:MCP_BRIDGE_TOKEN = $token
        Write-Host "[初始化] 已生成新 token 并写入用户环境变量 MCP_BRIDGE_TOKEN" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "==================== 你的访问凭证 ====================" -ForegroundColor Cyan
Write-Host "MCP_BRIDGE_TOKEN = $env:MCP_BRIDGE_TOKEN"
Write-Host "（发给 Agent 时和隧道 URL 一起给；泄露了就重新生成）"
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# ---- 3. 启动 ----
$py = (Get-Command python -ErrorAction SilentlyContinue)
if (-not $py) { $py = Get-Command py -ErrorAction Stop }
& $py.Source "gateway.py" -c "bridge_config.json"
