# bootstrap.ps1 —— 一键安装到独立目录 new1（不动你原来的 new）
#
# 用法（在 E:\0mcp-agv 下运行）:
#   powershell -ExecutionPolicy Bypass -File bootstrap.ps1
#
# 如果你还没有这个文件，先手动跑这三行：
#   cd E:\0mcp-agv
#   git clone -b arena/01a02938-new https://github.com/mqgg5630-cyber/new.git new1
#   powershell -ExecutionPolicy Bypass -File new1\mcp-bridge\scripts\bootstrap.ps1

param(
    [string]$Dir = "new1",
    [string]$Branch = "arena/01a02938-new",
    [string]$Repo = "https://github.com/mqgg5630-cyber/new.git"
)

$ErrorActionPreference = "Stop"

# 如果脚本是从仓库里跑的，就直接用仓库所在位置；否则去 clone
$Bridge = $null
if ($PSScriptRoot -and (Test-Path (Join-Path (Split-Path -Parent $PSScriptRoot) "gateway.py"))) {
    $Bridge = Split-Path -Parent $PSScriptRoot
} else {
    if (Test-Path $Dir) {
        Write-Host "[跳过克隆] $Dir 已存在，执行更新" -ForegroundColor Yellow
        Push-Location $Dir
        git fetch origin $Branch
        git checkout $Branch
        git pull --ff-only origin $Branch
        Pop-Location
    } else {
        Write-Host "[克隆] $Repo ($Branch) -> $Dir" -ForegroundColor Cyan
        git clone -b $Branch $Repo $Dir
    }
    $Bridge = Join-Path (Resolve-Path $Dir) "mcp-bridge"
}

Set-Location $Bridge
Write-Host "[目录] $Bridge" -ForegroundColor Green

# 检查 Python
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }
if (-not $py) { Write-Host "[错误] 找不到 python，请先安装 Python 3.9+" -ForegroundColor Red; exit 1 }
Write-Host "[Python] $($py.Source)" -ForegroundColor Green

# 自检
Write-Host ""
Write-Host "[自检] 运行端到端测试..." -ForegroundColor Cyan
& $py.Source "smoke_test.py"
if ($LASTEXITCODE -ne 0) { Write-Host "[错误] 自检未通过" -ForegroundColor Red; exit 1 }

# 生成配置
if (-not (Test-Path "bridge_config.json")) {
    Copy-Item "bridge_config.example.json" "bridge_config.json"
    Write-Host "[配置] 已生成 bridge_config.json" -ForegroundColor Green
}

Write-Host ""
Write-Host "======================= 下一步 =======================" -ForegroundColor Cyan
Write-Host "窗口 1:  powershell -ExecutionPolicy Bypass -File scripts\start-gateway.ps1"
Write-Host "窗口 2:  powershell -ExecutionPolicy Bypass -File scripts\start-tunnel.ps1"
Write-Host "然后把 [隧道URL + TOKEN] 发给 Agent"
Write-Host "======================================================" -ForegroundColor Cyan
