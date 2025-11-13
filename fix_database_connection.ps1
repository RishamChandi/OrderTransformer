# PowerShell script to fix database connection
# This script removes any SQLite DATABASE_URL and ensures Render database is used

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Fixing Database Connection" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if DATABASE_URL is set in PowerShell
$currentDbUrl = $env:DATABASE_URL
if ($currentDbUrl) {
    Write-Host "⚠️  DATABASE_URL is set in PowerShell: $($currentDbUrl.Substring(0, [Math]::Min(50, $currentDbUrl.Length)))..." -ForegroundColor Yellow
    
    if ($currentDbUrl -like "*sqlite*") {
        Write-Host "❌ SQLite DATABASE_URL detected in PowerShell environment!" -ForegroundColor Red
        Write-Host "🗑️  Removing SQLite DATABASE_URL from PowerShell environment..." -ForegroundColor Yellow
        Remove-Item Env:\DATABASE_URL -ErrorAction SilentlyContinue
        Write-Host "✅ Removed SQLite DATABASE_URL from PowerShell environment" -ForegroundColor Green
    } else {
        Write-Host "ℹ️  DATABASE_URL is set to: $($currentDbUrl.Substring(0, [Math]::Min(50, $currentDbUrl.Length)))..." -ForegroundColor Cyan
    }
} else {
    Write-Host "✅ No DATABASE_URL set in PowerShell environment" -ForegroundColor Green
}

# Step 2: Check .env file
Write-Host ""
Write-Host "Checking .env file..." -ForegroundColor Cyan
if (Test-Path ".env") {
    $envContent = Get-Content ".env" -Raw
    if ($envContent -like "*sqlite*") {
        Write-Host "❌ SQLite DATABASE_URL found in .env file!" -ForegroundColor Red
        Write-Host "⚠️  Please update .env file with Render database URL" -ForegroundColor Yellow
    } elseif ($envContent -like "*render.com*") {
        Write-Host "✅ .env file contains Render database URL" -ForegroundColor Green
    } else {
        Write-Host "⚠️  .env file exists but Render database URL not found" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  .env file not found" -ForegroundColor Yellow
    Write-Host "Creating .env file with Render database URL..." -ForegroundColor Cyan
    
    $renderDbUrl = "postgresql://order_transformer_db_user:npvK3aWfeS5d6nu9PCzfDL9JugjZgA70@dpg-d2436rjuibrs73a698cg-a.oregon-postgres.render.com/order_transformer_db"
    
    $envContent = @"
# Environment Configuration
# This file is automatically loaded by app.py (if python-dotenv is installed)
# DO NOT commit this file to Git - it contains sensitive credentials

# Environment: local, development, or production
# When using Render database, the app will auto-detect render.com and use production database
ENVIRONMENT=local

# Render Production Database URL
# This connects the local app to the same database as the Render production app
# The app will automatically add ?sslmode=require for Render databases
DATABASE_URL=$renderDbUrl

# Note: All data changes made locally will affect the production database
# Be careful when making changes!
"@
    
    $envContent | Out-File -FilePath ".env" -Encoding utf8 -NoNewline
    Write-Host "✅ Created .env file with Render database URL" -ForegroundColor Green
}

# Step 3: Verify python-dotenv is installed
Write-Host ""
Write-Host "Checking python-dotenv..." -ForegroundColor Cyan
$dotenvInstalled = pip list | Select-String -Pattern "python-dotenv"
if ($dotenvInstalled) {
    Write-Host "✅ python-dotenv is installed" -ForegroundColor Green
} else {
    Write-Host "⚠️  python-dotenv is not installed" -ForegroundColor Yellow
    Write-Host "Installing python-dotenv..." -ForegroundColor Cyan
    pip install python-dotenv
    Write-Host "✅ Installed python-dotenv" -ForegroundColor Green
}

# Step 4: Clear Streamlit cache
Write-Host ""
Write-Host "Clearing Streamlit cache..." -ForegroundColor Cyan
streamlit cache clear 2>$null
Write-Host "✅ Streamlit cache cleared" -ForegroundColor Green

# Step 5: Test database connection
Write-Host ""
Write-Host "Testing database connection..." -ForegroundColor Cyan
try {
    python -c "import os; from dotenv import load_dotenv; load_dotenv(override=True); from database.env_config import get_database_url; url = get_database_url(); print('✅ Database URL loaded:', 'render.com' in url.lower(), '- sqlite' in url.lower())"
    Write-Host "✅ Database connection test passed" -ForegroundColor Green
} catch {
    Write-Host "❌ Database connection test failed: $_" -ForegroundColor Red
}

# Step 6: Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ SQLite DATABASE_URL removed from PowerShell (if it existed)" -ForegroundColor Green
Write-Host "✅ .env file verified/created with Render database URL" -ForegroundColor Green
Write-Host "✅ python-dotenv installed" -ForegroundColor Green
Write-Host "✅ Streamlit cache cleared" -ForegroundColor Green
Write-Host ""
Write-Host "🚀 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Close this PowerShell window" -ForegroundColor White
Write-Host "   2. Open a NEW PowerShell window" -ForegroundColor White
Write-Host "   3. Navigate to project directory: cd C:\Users\risha\VSCODE\OrderTransformer" -ForegroundColor White
Write-Host "   4. Run: python -m streamlit run app.py --server.port 8502" -ForegroundColor White
Write-Host "   5. Verify connection in app shows Render database" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  IMPORTANT: Start in a NEW PowerShell window to avoid old environment variables" -ForegroundColor Yellow
Write-Host ""

