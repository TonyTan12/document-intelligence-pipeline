# Document Intelligence Pipeline - API Startup Script
# Run this script to start the FastAPI server

param(
    [string]$Host = "0.0.0.0",
    [int]$Port = 8000,
    [switch]$Dev = $false,
    [switch]$Help = $false
)

function Show-Help {
    Write-Host @"
Document Intelligence Pipeline - API Server

Usage: .\run_api.ps1 [Options]

Options:
    -Host    Bind address (default: 0.0.0.0)
    -Port    Port number (default: 8000)
    -Dev     Enable development mode with auto-reload
    -Help    Show this help message

Examples:
    .\run_api.ps1                    # Run with defaults
    .\run_api.ps1 -Port 8080         # Run on port 8080
    .\run_api.ps1 -Dev               # Development mode
    .\run_api.ps1 -Host 127.0.0.1    # Local only
"@
    exit 0
}

if ($Help) {
    Show-Help
}

# Check if virtual environment exists and activate
$venvPath = ".\venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    Write-Host "Activating virtual environment..." -ForegroundColor Green
    & $venvPath
} else {
    Write-Host "Warning: Virtual environment not found at .\venv" -ForegroundColor Yellow
    Write-Host "Make sure dependencies are installed: pip install -r requirements.txt" -ForegroundColor Yellow
}

# Check for .env file
if (-not (Test-Path ".env")) {
    Write-Host "Warning: .env file not found!" -ForegroundColor Yellow
    Write-Host "Copy .env.example to .env and configure your settings." -ForegroundColor Yellow
    
    # Check if OPENAI_API_KEY is set in environment
    if (-not $env:OPENAI_API_KEY) {
        Write-Host "ERROR: OPENAI_API_KEY not set!" -ForegroundColor Red
        Write-Host "Please set your OpenAI API key in .env file or environment variable." -ForegroundColor Red
        exit 1
    }
}

# Display startup info
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Document Intelligence Pipeline API" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Host:     $Host" -ForegroundColor White
Write-Host "Port:     $Port" -ForegroundColor White
Write-Host "Mode:     $(if ($Dev) { 'Development' } else { 'Production' })" -ForegroundColor White
Write-Host "Docs:     http://$($Host -replace '0.0.0.0', 'localhost'):$Port/docs" -ForegroundColor White
Write-Host "========================================`n" -ForegroundColor Cyan

# Run the API
try {
    if ($Dev) {
        Write-Host "Starting server in DEVELOPMENT mode (with auto-reload)..." -ForegroundColor Green
        uvicorn src.api:app --host $Host --port $Port --reload
    } else {
        Write-Host "Starting server in PRODUCTION mode..." -ForegroundColor Green
        uvicorn src.api:app --host $Host --port $Port
    }
} catch {
    Write-Host "`nERROR: Failed to start server!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    
    Write-Host "`nTroubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Ensure uvicorn is installed: pip install uvicorn[standard]" -ForegroundColor Yellow
    Write-Host "2. Check that you're in the project root directory" -ForegroundColor Yellow
    Write-Host "3. Verify all dependencies: pip install -r requirements.txt" -ForegroundColor Yellow
    
    exit 1
}
