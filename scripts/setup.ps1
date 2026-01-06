# ============================================================================
# PDFKit Local Deployment Script (Windows PowerShell)
# ============================================================================
# Usage: Run .\scripts\setup.ps1 in the project directory
# ============================================================================

#Requires -Version 5.1

$ErrorActionPreference = "Stop"

# Configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$VenvName = "pdfkit-env"
$BinDir = "$env:USERPROFILE\.local\bin"

# ============================================================================
# Utility Functions
# ============================================================================

function Write-Info($message) {
    Write-Host "[INFO] " -NoNewline -ForegroundColor Blue
    Write-Host $message
}

function Write-Success($message) {
    Write-Host "[OK] " -NoNewline -ForegroundColor Green
    Write-Host $message
}

function Write-Warn($message) {
    Write-Host "[WARN] " -NoNewline -ForegroundColor Yellow
    Write-Host $message
}

function Write-Err($message) {
    Write-Host "[ERROR] " -NoNewline -ForegroundColor Red
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
# Installation Steps
# ============================================================================

$TotalSteps = 4

function Test-Python {
    Write-Step 1 $TotalSteps "Checking Python..."
    
    if (-not (Test-Command "python")) {
        Write-Err "Python not found. Please install Python 3.10+"
        exit 1
    }
    
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$Matches[1]
        $minor = [int]$Matches[2]
        
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
            Write-Err "Python version too old ($pythonVersion). Requires 3.10+"
            exit 1
        }
        
        Write-Success "Python $major.$minor"
    }
}

function New-Venv {
    Write-Step 2 $TotalSteps "Creating virtual environment..."
    
    $venvPath = Join-Path $ProjectDir $VenvName
    
    if (Test-Path $venvPath) {
        Write-Warn "Virtual environment already exists: $VenvName"
    }
    else {
        Push-Location $ProjectDir
        python -m venv $VenvName
        Pop-Location
        Write-Success "Virtual environment created: $VenvName"
    }
}

function Install-Dependencies {
    Write-Step 3 $TotalSteps "Installing dependencies..."
    
    $activateScript = Join-Path $ProjectDir "$VenvName\Scripts\Activate.ps1"
    . $activateScript
    
    Push-Location $ProjectDir
    
    Write-Info "Upgrading pip..."
    python -m pip install --upgrade pip -q
    
    Write-Info "Installing PDFKit..."
    pip install -e . -q
    
    Pop-Location
    
    Write-Success "Dependencies installed"
}

function Set-Command {
    Write-Step 4 $TotalSteps "Configuring system command..."
    
    # Create bin directory
    if (-not (Test-Path $BinDir)) {
        New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
    }
    
    # Create wrapper script
    $wrapperPath = Join-Path $BinDir "pdfkit.cmd"
    $wrapperContent = @"
@echo off
call "$ProjectDir\$VenvName\Scripts\activate.bat"
python -m pdfkit %*
"@
    
    Set-Content -Path $wrapperPath -Value $wrapperContent -Encoding ASCII
    Write-Success "Command script created: $wrapperPath"
    
    # Add to PATH
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notlike "*$BinDir*") {
        Write-Info "Adding $BinDir to user PATH..."
        [Environment]::SetEnvironmentVariable("Path", "$BinDir;$userPath", "User")
        $env:Path = "$BinDir;$env:Path"
        Write-Success "PATH updated"
    }
    else {
        Write-Warn "$BinDir is already in PATH"
    }
    
    Write-Success "System command configured"
}

function Write-SuccessBanner {
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Green
    Write-Host "              PDFKit Deployment Successful!" -ForegroundColor Green
    Write-Host "================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Project Directory: " -NoNewline -ForegroundColor Cyan
    Write-Host $ProjectDir
    Write-Host "  Virtual Environment: " -NoNewline -ForegroundColor Cyan
    Write-Host "$ProjectDir\$VenvName"
    Write-Host ""
    Write-Host "  Activate virtual environment:" -ForegroundColor Yellow
    Write-Host "    . $ProjectDir\$VenvName\Scripts\Activate.ps1" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Usage:" -ForegroundColor Yellow
    Write-Host "    pdfkit --help" -ForegroundColor Green
    Write-Host "    pdfkit info system" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Refresh PATH (if needed):" -ForegroundColor Yellow
    Write-Host '    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")' -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Green
}

# ============================================================================
# Main Program
# ============================================================================

function Main {
    Write-Host "PDFKit Local Deployment Script" -ForegroundColor Cyan
    Write-Host "Project Directory: $ProjectDir" -ForegroundColor Yellow
    Write-Host ""
    
    try {
        Test-Python
        New-Venv
        Install-Dependencies
        Set-Command
        Write-SuccessBanner
    }
    catch {
        Write-Err "Deployment failed: $_"
        exit 1
    }
}

Main
