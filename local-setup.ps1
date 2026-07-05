# STEAM AI - Local Setup Script for Windows
# This script sets up and runs the STEAM AI application locally on Windows
# Prerequisites: Python 3.12+ must be installed

Write-Host "================================" -ForegroundColor Cyan
Write-Host "STEAM AI - Local Setup Script" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

# Ensure we're in the script's directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir
Write-Host "Working directory: $(Get-Location)`n" -ForegroundColor Cyan

# Step 1: Check if Python is installed
Write-Host "[1/5] Checking for Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Found: $pythonVersion`n" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.12+ from https://www.python.org/" -ForegroundColor Yellow
    exit 1
}

# Step 2: Set Execution Policy
Write-Host "[2/5] Setting PowerShell execution policy..." -ForegroundColor Yellow
try {
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force | Out-Null
    Write-Host "[OK] Execution policy set`n" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Could not set execution policy" -ForegroundColor Red
    Write-Host "Try running PowerShell as Administrator" -ForegroundColor Yellow
    exit 1
}

# Step 3: Create virtual environment
Write-Host "[3/5] Creating Python virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "[OK] Virtual environment already exists" -ForegroundColor Green
} else {
    try {
        python -m venv venv
        # Give it a moment and verify it was created
        Start-Sleep -Milliseconds 500
        if (Test-Path "venv") {
            Write-Host "[OK] Virtual environment created`n" -ForegroundColor Green
        } else {
            Write-Host "[ERROR] Virtual environment was not created" -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "[ERROR] Failed to create virtual environment" -ForegroundColor Red
        Write-Host "Error details: $_" -ForegroundColor Yellow
        exit 1
    }
}

# Step 4: Activate virtual environment and install dependencies
Write-Host "[4/5] Activating virtual environment and installing dependencies..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to activate virtual environment" -ForegroundColor Red
    exit 1
}

pip install --upgrade pip | Out-Null
pip install -r requirements.txt | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Dependencies installed`n" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Step 5: Run the application
Write-Host "[5/5] Starting STEAM AI application..." -ForegroundColor Yellow
Write-Host "Note: Study Mode requires Ollama running locally on http://localhost:11434" -ForegroundColor Cyan
Write-Host "Download Ollama from https://ollama.ai`n" -ForegroundColor Cyan

python main.py

# Deactivate on exit
deactivate
