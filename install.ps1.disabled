# ============================================================================
# PDFKit 一键安装脚本 (Windows PowerShell)
# ============================================================================
# 用法: 
#   irm https://raw.githubusercontent.com/linzhiqin2003/pdfkit/main/scripts/install.ps1 | iex
# 或者:
#   .\install.ps1
# ============================================================================

#Requires -Version 5.1

$ErrorActionPreference = "Stop"

# 配置
$RepoUrl = "https://github.com/linzhiqin2003/pdfkit.git"
$InstallDir = "$env:USERPROFILE\.pdfkit-cli"
$VenvName = "venv"
$BinDir = "$env:USERPROFILE\.local\bin"

# ============================================================================
# 工具函数
# ============================================================================

function Write-Banner {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║                                                               ║" -ForegroundColor Cyan
    Write-Host "║   ██████╗ ██████╗ ███████╗██╗  ██╗██╗████████╗               ║" -ForegroundColor Cyan
    Write-Host "║   ██╔══██╗██╔══██╗██╔════╝██║ ██╔╝██║╚══██╔══╝               ║" -ForegroundColor Cyan
    Write-Host "║   ██████╔╝██║  ██║█████╗  █████╔╝ ██║   ██║                  ║" -ForegroundColor Cyan
    Write-Host "║   ██╔═══╝ ██║  ██║██╔══╝  ██╔═██╗ ██║   ██║                  ║" -ForegroundColor Cyan
    Write-Host "║   ██║     ██████╔╝██║     ██║  ██╗██║   ██║                  ║" -ForegroundColor Cyan
    Write-Host "║   ╚═╝     ╚═════╝ ╚═╝     ╚═╝  ╚═╝╚═╝   ╚═╝                  ║" -ForegroundColor Cyan
    Write-Host "║                                                               ║" -ForegroundColor Cyan
    Write-Host "║              Windows 一键安装脚本 v1.0.0                      ║" -ForegroundColor Cyan
    Write-Host "║                                                               ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

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

$TotalSteps = 5

function Install-Python {
    Write-Step 1 $TotalSteps "检查 Python..."
    
    if (Test-Command "python") {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python (\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            
            if ($major -ge 3 -and $minor -ge 10) {
                Write-Success "Python 已安装: $pythonVersion"
                return
            }
        }
    }
    
    # 尝试使用 winget 安装
    if (Test-Command "winget") {
        Write-Info "正在通过 winget 安装 Python 3.12..."
        winget install Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
        
        # 刷新 PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        
        Write-Success "Python 3.12 安装完成"
    } else {
        Write-Error "未找到 Python 3.10+，请手动安装: https://www.python.org/downloads/"
        Write-Info "安装时请勾选 'Add Python to PATH'"
        exit 1
    }
}

function Install-Git {
    Write-Step 2 $TotalSteps "检查 Git..."
    
    if (Test-Command "git") {
        $gitVersion = git --version
        Write-Success "Git 已安装: $gitVersion"
        return
    }
    
    # 尝试使用 winget 安装
    if (Test-Command "winget") {
        Write-Info "正在通过 winget 安装 Git..."
        winget install Git.Git --silent --accept-package-agreements --accept-source-agreements
        
        # 刷新 PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        
        Write-Success "Git 安装完成"
    } else {
        Write-Error "未找到 Git，请手动安装: https://git-scm.com/download/win"
        exit 1
    }
}

function Clone-Repository {
    Write-Step 3 $TotalSteps "克隆代码仓库..."
    
    if (Test-Path $InstallDir) {
        Write-Warning "安装目录已存在: $InstallDir"
        Write-Info "正在更新代码..."
        Push-Location $InstallDir
        git pull origin main 2>$null
        if (-not $?) {
            git pull origin master
        }
        Pop-Location
        Write-Success "代码更新完成"
    } else {
        Write-Info "正在克隆仓库..."
        git clone $RepoUrl $InstallDir
        Write-Success "代码克隆完成: $InstallDir"
    }
}

function Install-Dependencies {
    Write-Step 4 $TotalSteps "安装 Python 依赖..."
    
    Push-Location $InstallDir
    
    # 创建虚拟环境
    $venvPath = Join-Path $InstallDir $VenvName
    if (-not (Test-Path $venvPath)) {
        Write-Info "创建虚拟环境..."
        python -m venv $VenvName
    }
    
    # 激活虚拟环境并安装
    $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
    . $activateScript
    
    Write-Info "升级 pip..."
    python -m pip install --upgrade pip -q
    
    Write-Info "安装 PDFKit..."
    pip install -e . -q
    
    Pop-Location
    
    Write-Success "依赖安装完成"
}

function Configure-Command {
    Write-Step 5 $TotalSteps "配置系统命令..."
    
    # 创建 bin 目录
    if (-not (Test-Path $BinDir)) {
        Write-Info "创建目录 $BinDir..."
        New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
    }
    
    # 创建 wrapper 脚本 (批处理文件)
    $wrapperPath = Join-Path $BinDir "pdfkit.cmd"
    $wrapperContent = @"
@echo off
call "$InstallDir\$VenvName\Scripts\activate.bat"
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
    Write-Host "              ✓ PDFKit 安装成功！" -ForegroundColor Green
    Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host ""
    Write-Host "  安装位置: " -NoNewline -ForegroundColor Cyan
    Write-Host $InstallDir
    Write-Host "  虚拟环境: " -NoNewline -ForegroundColor Cyan
    Write-Host "$InstallDir\$VenvName"
    Write-Host ""
    Write-Host "  开始使用:" -ForegroundColor Yellow
    Write-Host "    pdfkit --help" -ForegroundColor Green
    Write-Host "    pdfkit info system" -ForegroundColor Green
    Write-Host "    pdfkit info doc.pdf" -ForegroundColor Green
    Write-Host ""
    Write-Host "  常用命令:" -ForegroundColor Yellow
    Write-Host "    pdfkit merge a.pdf b.pdf -o combined.pdf" -ForegroundColor Green
    Write-Host "    pdfkit split doc.pdf --single" -ForegroundColor Green
    Write-Host "    pdfkit compress large.pdf -o small.pdf" -ForegroundColor Green
    Write-Host "    pdfkit ocr scan.pdf" -ForegroundColor Green
    Write-Host ""
    Write-Host "  配置 API Key (OCR/AI 功能):" -ForegroundColor Yellow
    Write-Host '    $env:DASHSCOPE_API_KEY = "your-api-key"' -ForegroundColor Green
    Write-Host "    或永久设置:" -ForegroundColor DarkGray
    Write-Host '    [Environment]::SetEnvironmentVariable("DASHSCOPE_API_KEY", "your-key", "User")' -ForegroundColor Green
    Write-Host ""
    Write-Host "  重要: 请重启终端或运行以下命令刷新 PATH:" -ForegroundColor Yellow
    Write-Host '    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")' -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Green
}

# ============================================================================
# 主程序
# ============================================================================

function Main {
    Write-Banner
    
    Write-Host "即将安装 PDFKit CLI 到: $InstallDir" -ForegroundColor Yellow
    Write-Host ""
    
    $confirm = Read-Host "是否继续安装? [Y/n]"
    if ($confirm -eq "n" -or $confirm -eq "N") {
        Write-Host "安装已取消"
        exit 0
    }
    
    try {
        Install-Python
        Install-Git
        Clone-Repository
        Install-Dependencies
        Configure-Command
        Write-SuccessBanner
    }
    catch {
        Write-Error "安装失败: $_"
        exit 1
    }
}

# 运行主程序
Main
