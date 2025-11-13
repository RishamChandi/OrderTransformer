# Quick fix script to ensure Render database is used
Write-Host "Checking database configuration..." -ForegroundColor Cyan

# Remove SQLite DATABASE_URL if it exists
if ($env:DATABASE_URL -like "*sqlite*") {
    Write-Host "Removing SQLite DATABASE_URL from PowerShell..." -ForegroundColor Yellow
    Remove-Item Env:\DATABASE_URL
    Write-Host "Removed SQLite DATABASE_URL" -ForegroundColor Green
}

# Check .env file
if (Test-Path ".env") {
    $envContent = Get-Content ".env" -Raw
    if ($envContent -like "*render.com*") {
        Write-Host ".env file contains Render database URL" -ForegroundColor Green
    } else {
        Write-Host ".env file does not contain Render database URL" -ForegroundColor Red
    }
} else {
    Write-Host ".env file not found" -ForegroundColor Red
}

# Test connection
Write-Host "Testing database connection..." -ForegroundColor Cyan
python -c "from dotenv import load_dotenv; import os; load_dotenv(override=True); from database.env_config import get_database_url; url = get_database_url(); print('SUCCESS: Render database' if 'render.com' in url.lower() else 'ERROR: Not Render database')"

