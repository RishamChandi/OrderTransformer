# Force Render Database - Complete Fix

## Problem
The app is still connecting to SQLite instead of Render database.

## Root Cause
The database engine is created at module import time. If the app was started before the code changes, it's using the old cached connection or old environment variables.

## Complete Solution

### Step 1: Stop the App
**CRITICAL**: Stop the current app completely:
1. Press `Ctrl+C` in the terminal where Streamlit is running
2. Wait for it to stop completely
3. Close the terminal window

### Step 2: Clear All Environment Variables
Open a NEW PowerShell window and run:
```powershell
# Check if DATABASE_URL is set
$env:DATABASE_URL

# If it shows SQLite, remove it
Remove-Item Env:\DATABASE_URL -ErrorAction SilentlyContinue

# Verify it's removed
$env:DATABASE_URL
# Should be empty/null
```

### Step 3: Verify .env File
Check that `.env` file exists and contains Render database URL:
```powershell
cd C:\Users\risha\VSCODE\OrderTransformer
Get-Content .env
```

Should show:
```
DATABASE_URL=postgresql://order_transformer_db_user:npvK3aWfeS5d6nu9PCzfDL9JugjZgA70@dpg-d2436rjuibrs73a698cg-a.oregon-postgres.render.com/order_transformer_db
```

### Step 4: Clear Streamlit Cache
```powershell
streamlit cache clear
```

### Step 5: Delete local.db File (Optional)
The `local.db` file won't be used anymore:
```powershell
Remove-Item local.db -ErrorAction SilentlyContinue
```

### Step 6: Start in NEW PowerShell Window
**CRITICAL**: Start in a COMPLETELY NEW PowerShell window:

1. **Close ALL PowerShell windows**
2. **Open a NEW PowerShell window**
3. Navigate to project:
   ```powershell
   cd C:\Users\risha\VSCODE\OrderTransformer
   ```
4. Verify no DATABASE_URL is set:
   ```powershell
   $env:DATABASE_URL
   ```
   (Should be empty/null)
5. Run the app:
   ```powershell
   python -m streamlit run app.py --server.port 8502
   ```

## Expected Output

In the terminal, you should see:
```
✅ Detected Render database URL - will use production database
⚠️ NOTE: Local app will connect to Render production database
⚠️ All data changes will affect production database
🔌 Initializing database connection...
   Environment: production
   Database URL: postgresql://***:***@dpg-d2436rjuibrs73a698cg-a.oregon-postgres.render.com/...
   ✅ Using Render production database
✅ Connected to production database successfully (attempt 1)
   All order processors and mappings will use this database
```

In the app UI:
- ✅ **Connected to Render Production Database**
- Environment: production
- Database: `postgresql://***:***@dpg-d2436rjuibrs73a698cg-a.oregon-postgres.render.com/...`

## Verification

After restarting, verify the connection:
1. Check the **Database Connection** section in the sidebar
2. Should show: ✅ **Connected to Render Production Database**
3. Go to "Manage Mappings" → "UNFI East" → "Customer Mapping"
4. Should see the same **14 customer mappings** as Render app

## Code Changes Applied

1. ✅ **SQLite completely blocked**: Raises error if SQLite is detected
2. ✅ **Override=True**: .env file overrides PowerShell variables
3. ✅ **run_app.bat updated**: Removed SQLite
4. ✅ **app.py updated**: Shows error and stops if SQLite detected
5. ✅ **All modules load .env**: app.py, database/connection.py, database/env_config.py

## If You Still See SQLite

If you still see SQLite after following all steps:

1. **Check PowerShell profile:**
   ```powershell
   Test-Path $PROFILE
   Get-Content $PROFILE -ErrorAction SilentlyContinue | Select-String -Pattern "DATABASE_URL"
   ```
   If DATABASE_URL is set in PowerShell profile, remove it.

2. **Check system environment variables:**
   ```powershell
   [System.Environment]::GetEnvironmentVariable("DATABASE_URL", "User")
   [System.Environment]::GetEnvironmentVariable("DATABASE_URL", "Machine")
   ```
   If SQLite is set, remove it.

3. **Restart computer** (if needed):
   Sometimes environment variables persist in the system.

4. **Check for multiple .env files:**
   ```powershell
   Get-ChildItem -Recurse -Filter .env -ErrorAction SilentlyContinue
   ```
   Make sure only one .env file exists in the project root.

## Test Before Starting App

Test the database connection before starting the app:
```powershell
python -c "from dotenv import load_dotenv; import os; load_dotenv(override=True); from database.env_config import get_database_url; url = get_database_url(); print('SUCCESS: Render database' if 'render.com' in url.lower() else 'ERROR: Not Render database - ' + url[:50])"
```

Should output: `SUCCESS: Render database`

If it outputs `ERROR:`, check the error message and fix it before starting the app.

