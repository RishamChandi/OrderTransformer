# PowerShell script to help set up .env file for local development
# This script will create a .env file with the Render database URL

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setting up .env file for Local Development" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env file already exists
if (Test-Path ".env") {
    Write-Host "⚠️  .env file already exists!" -ForegroundColor Yellow
    $overwrite = Read-Host "Do you want to overwrite it? (y/n)"
    if ($overwrite -ne "y" -and $overwrite -ne "Y") {
        Write-Host "❌ Cancelled. .env file not modified." -ForegroundColor Red
        exit
    }
}

# Render database URL (from run_with_prod_db.bat)
$databaseUrl = "postgresql://order_transformer_db_user:npvK3aWfeS5d6nu9PCzfDL9JugjZgA70@dpg-d2436rjuibrs73a698cg-a.oregon-postgres.render.com/order_transformer_db"

# Create .env file content
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
DATABASE_URL=$databaseUrl

# Note: All data changes made locally will affect the production database
# Be careful when making changes!
"@

# Write .env file
try {
    $envContent | Out-File -FilePath ".env" -Encoding utf8 -NoNewline
    Write-Host "✅ .env file created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📝 File location: $((Get-Location).Path)\.env" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "⚠️  IMPORTANT:" -ForegroundColor Yellow
    Write-Host "   - This file contains your database password" -ForegroundColor Yellow
    Write-Host "   - It's already in .gitignore - DO NOT commit it to Git" -ForegroundColor Yellow
    Write-Host "   - All data changes made locally will affect the production database" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "🚀 Next steps:" -ForegroundColor Cyan
    Write-Host "   1. Install python-dotenv: pip install python-dotenv" -ForegroundColor White
    Write-Host "   2. Run the app: python -m streamlit run app.py --server.port 8502" -ForegroundColor White
    Write-Host "   3. Verify connection in the app's Database Connection section" -ForegroundColor White
    Write-Host ""
} catch {
    Write-Host "❌ Error creating .env file: $_" -ForegroundColor Red
    exit 1
}

