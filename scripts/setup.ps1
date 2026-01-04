# ============================================================================
# PDFKit 本地部署脚本 (Windows PowerShell)
# ============================================================================
# 用法: 在项目目录中运行 .\scripts\setup.ps1
# ============================================================================

#Requires -Version 5.1

$ErrorActionPreference = "Stop"

# 配置
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$VenvName = "pdfkit-env"
$BinDir = "$env:USERPROFILE\.local\bin"

# ============================================================================
# 工具函数
# ============================================================================

function Write-Info($message) {
    Write-Host "ℹ " -NoNewline -ForegroundColor Blue
    Write-Host $message
}

function Write-Success($message) {
    Write-Host "✓ " -NoNewline -ForegroundColor Green
    Write-Host $message
}

function Write-Warning($message) {
    Write-Host "⚠ " -NoNewline -ForegroundColor Yellow
    Write-Host $message
}

function Write-Error($message) {
    Write-Host "✗ " -NoNewline -ForegroundColor Red
    Write-Host $message
}

function Write-Step($step, $total, $message) {
    Write-Host ""
    Write-Host "[$step/$total] " -NoNewline -ForegroundColor Cyan
    Write-Host $message -ForegroundColor Yellow
}

function Test-Command($command) {
    $null = Get-Command $command -ErrorAction SilentlyContinue
    return $?
}

# ============================================================================
# 安装步骤
# ============================================================================

$TotalSteps = 4

function Test-Python {
    Write-Step 1 $TotalSteps "检查 Python..."
    
    if (-not (Test-Command "python")) {
        Write-Error "未找到 Python，请先安装 Python 3.10+"
        exit 1
    }
    
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$Matches[1]
        $minor = [int]$Matches[2]
        
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
            Write-Error "Python 版本过低 ($pythonVersion)，需要 3.10+"
            exit 1
        }
        
        Write-Success "Python $major.$minor"
    }
}

function New-Venv {
    Write-Step 2 $TotalSteps "创建虚拟环境..."
    
    $venvPath = Join-Path $ProjectDir $VenvName
    
    if (Test-Path $venvPath) {
        Write-Warning "虚拟环境已存在: $VenvName"
    } else {
        Push-Location $ProjectDir
        python -m venv $VenvName
        Pop-Location
        Write-Success "虚拟环境已创建: $VenvName"
    }
}

function Install-Dependencies {
    Write-Step 3 $TotalSteps "安装依赖..."
    
    $activateScript = Join-Path $ProjectDir "$VenvName\Scripts\Activate.ps1"
    . $activateScript
    
    Push-Location $ProjectDir
    
    Write-Info "升级 pip..."
    python -m pip install --upgrade pip -q
    
    Write-Info "安装 PDFKit..."
    pip install -e . -q
    
    Pop-Location
    
    Write-Success "依赖安装完成"
}

function Set-Command {
    Write-Step 4 $TotalSteps "配置系统命令..."
    
    # 创建 bin 目录
    if (-not (Test-Path $BinDir)) {
        New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
    }
    
    # 创建 wrapper 脚本
    $wrapperPath = Join-Path $BinDir "pdfkit.cmd"
    $wrapperContent = @"
@echo off
call "$ProjectDir\$VenvName\Scripts\activate.bat"
python -m pdfkit %*
"@
    
    Set-Content -Path $wrapperPath -Value $wrapperContent -Encoding ASCII
    Write-Success "命令脚本已创建: $wrapperPath"
    
    # 添加到 PATH
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notlike "*$BinDir*") {
        Write-Info "添加 $BinDir 到用户 PATH..."
        [Environment]::SetEnvironmentVariable("Path", "$BinDir;$userPath", "User")
        $env:Path = "$BinDir;$env:Path"
        Write-Success "PATH 已更新"
    } else {
        Write-Warning "$BinDir 已在 PATH 中"
    }
    
    Write-Success "系统命令已配置"
}

function Write-SuccessBanner {
    Write-Host ""
    Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "              ✓ PDFKit 部署成功！" -ForegroundColor Green
    Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host ""
    Write-Host "  项目目录: " -NoNewline -ForegroundColor Cyan
    Write-Host $ProjectDir
    Write-Host "  虚拟环境: " -NoNewline -ForegroundColor Cyan
    Write-Host "$ProjectDir\$VenvName"
    Write-Host ""
    Write-Host "  激活虚拟环境:" -ForegroundColor Yellow
    Write-Host "    . $ProjectDir\$VenvName\Scripts\Activate.ps1" -ForegroundColor Green
    Write-Host ""
    Write-Host "  使用命令:" -ForegroundColor Yellow
    Write-Host "    pdfkit --help" -ForegroundColor Green
    Write-Host "    pdfkit info system" -ForegroundColor Green
    Write-Host ""
    Write-Host "  刷新 PATH (如需要):" -ForegroundColor Yellow
    Write-Host '    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")' -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Green
}

# ============================================================================
# 主程序
# ============================================================================

function Main {
    Write-Host "PDFKit 本地部署脚本" -ForegroundColor Cyan
    Write-Host "项目目录: $ProjectDir" -ForegroundColor Yellow
    Write-Host ""
    
    try {
        Test-Python
        New-Venv
        Install-Dependencies
        Set-Command
        Write-SuccessBanner
    }
    catch {
        Write-Error "部署失败: $_"
        exit 1
    }
}

Main
