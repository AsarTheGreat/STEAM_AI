# STEAM AI - Docker Setup Script for Windows
# This script builds the Docker image, creates the volume, and runs the container
# Prerequisites: Docker Desktop must be installed and running

Write-Host "================================" -ForegroundColor Cyan
Write-Host "STEAM AI - Docker Setup Script" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

# Step 1: Check if Docker is installed and running
Write-Host "[1/4] Checking Docker installation..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    Write-Host "[OK] Found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Docker Desktop from https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

try {
    docker ps > $null 2>&1
    Write-Host "[OK] Docker daemon is running`n" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker daemon is not running" -ForegroundColor Red
    Write-Host "Please start Docker Desktop" -ForegroundColor Yellow
    exit 1
}

# Step 2: Build Docker image
Write-Host "[2/4] Checking Docker image..." -ForegroundColor Yellow
$imageExists = docker images --filter "reference=steam_ai" --quiet
if ($imageExists) {
    Write-Host "[OK] Image 'steam_ai' already exists" -ForegroundColor Green
    Write-Host "Do you want to rebuild the image? (y/n)" -ForegroundColor Cyan
    $rebuild = Read-Host "Enter your choice"
    
    if ($rebuild -eq "y" -or $rebuild -eq "yes") {
        Write-Host "`nRebuilding Docker image...`n" -ForegroundColor Yellow
        docker build -t steam_ai .
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n[OK] Docker image rebuilt successfully`n" -ForegroundColor Green
        } else {
            Write-Host "`n[ERROR] Failed to rebuild Docker image" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "[OK] Skipping rebuild, using existing image`n" -ForegroundColor Green
    }
} else {
    Write-Host "[OK] Building Docker image for the first time..." -ForegroundColor Green
    Write-Host "This may take a few minutes...`n" -ForegroundColor Cyan
    docker build -t steam_ai .
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n[OK] Docker image built successfully`n" -ForegroundColor Green
    } else {
        Write-Host "`n[ERROR] Failed to build Docker image" -ForegroundColor Red
        exit 1
    }
}

# Step 3: Create Docker volume (if it doesn't exist)
Write-Host "[3/4] Setting up Docker volume for Ollama models..." -ForegroundColor Yellow
$volumeExists = docker volume ls --filter name=ollama_data --quiet
if ($volumeExists) {
    Write-Host "[OK] Volume 'ollama_data' already exists`n" -ForegroundColor Green
} else {
    docker volume create ollama_data | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Volume 'ollama_data' created`n" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Failed to create volume" -ForegroundColor Red
        exit 1
    }
}

# Step 4: Ask user for run mode
Write-Host "[4/4] Starting Docker container..." -ForegroundColor Yellow
Write-Host "Choose run mode:" -ForegroundColor Cyan
Write-Host "  1) Interactive mode (foreground, see output)" -ForegroundColor White
Write-Host "  2) Detached mode (background, container runs silently)" -ForegroundColor White
Write-Host ""
$choice = Read-Host "Enter your choice (1 or 2)"

if ($choice -eq "2") {
    Write-Host "`nStarting container in detached mode..." -ForegroundColor Yellow
    docker run -d --name steam_ai -p 11434:11434 -v ollama_data:/root/.ollama steam_ai
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n[OK] Container started successfully!" -ForegroundColor Green
        Write-Host "Container is running in the background as 'steam_ai'" -ForegroundColor Cyan
        Write-Host "Access the application at: http://localhost:11434" -ForegroundColor Cyan
        Write-Host "`nUseful commands:" -ForegroundColor Yellow
        Write-Host "  docker logs steam_ai        - View container output" -ForegroundColor White
        Write-Host "  docker attach steam_ai      - Attach to running container" -ForegroundColor White
        Write-Host "  docker stop steam_ai        - Stop the container" -ForegroundColor White
        Write-Host "  docker rm steam_ai          - Remove the container" -ForegroundColor White
    } else {
        Write-Host "`n[ERROR] Failed to start container" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "`nStarting container in interactive mode..." -ForegroundColor Yellow
    Write-Host "First run will download the llama3 model (~4.7 GB). Please be patient...`n" -ForegroundColor Cyan
    docker run --rm -it -p 11434:11434 -v ollama_data:/root/.ollama steam_ai
}
