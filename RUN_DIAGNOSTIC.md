# How to Run the Production Database Diagnostic Script

## Option 1: Run on Render (Production Server)

### Method A: Using Render Shell (Recommended)

1. **Open Render Dashboard**
   - Go to https://dashboard.render.com
   - Navigate to your service (Order Transformer)

2. **Open Shell**
   - Click on your service
   - Look for "Shell" button or tab (usually in the top menu)
   - Click "Open Shell" or "Connect to Shell"
   - This opens a web-based terminal

3. **Run the Script**
   ```bash
   # Navigate to your app directory (usually already there)
   cd /opt/render/project/src  # or check with: pwd
   
   # Run the diagnostic script
   python check_production_db.py
   ```

   **Note:** The `DATABASE_URL` environment variable should already be set in Render, so the script will automatically connect to production.

### Method B: Using Render CLI (Alternative)

If you have Render CLI installed:
```bash
render shell
python check_production_db.py
```

### Method C: Add as One-Off Command in Render

1. In Render dashboard, go to your service
2. Look for "One-off Commands" or "Run Command" option
3. Enter: `python check_production_db.py`
4. Click "Run" or "Execute"

## Option 2: Run Locally (Connecting to Production DB)

### Prerequisites
- You need the production `DATABASE_URL` environment variable

### Steps

1. **Set Environment Variables**
   ```powershell
   # PowerShell (Windows)
   $env:ENVIRONMENT = "production"
   $env:DATABASE_URL = "postgresql://user:password@host:port/database"
   ```

   ```bash
   # Bash/Linux/Mac
   export ENVIRONMENT=production
   export DATABASE_URL="postgresql://user:password@host:port/database"
   ```

2. **Run the Script**
   ```bash
   python check_production_db.py
   ```

## Option 3: Run via Streamlit App (Temporary Page)

You can also add a temporary diagnostic page to your Streamlit app:

1. Add this to `app.py`:
   ```python
   if st.sidebar.button("🔍 Run Database Diagnostic"):
       import subprocess
       result = subprocess.run(['python', 'check_production_db.py'], 
                              capture_output=True, text=True)
       st.code(result.stdout)
       if result.stderr:
           st.error(result.stderr)
   ```

## What the Script Checks

1. **Database Structure**
   - Verifies `customer_mappings` table exists
   - Checks table columns and structure
   - Verifies `store_mappings` table structure

2. **KEHE Customer Mappings**
   - Checks CustomerMapping table for KEHE mappings
   - Checks StoreMapping table for legacy KEHE customer data
   - Lists all source name variations found
   - Tests mapping lookup function

3. **UNFI East Customer Mappings**
   - Checks CustomerMapping table for UNFI East mappings
   - Checks StoreMapping table for legacy UNFI East customer data
   - Lists all source name variations found
   - Tests mapping lookup with common IOW codes (RCH, HOW, CHE, etc.)

4. **Migration Test**
   - Tests if legacy data migration would work
   - Shows how many mappings would be migrated

## Expected Output

The script will show:
- ✅ Which tables exist
- 📊 How many mappings are in each table
- 🔍 Sample records with their source names
- ⚠️ Any issues found (missing mappings, wrong source names, etc.)
- 🧪 Test results of the mapping lookup function

## Troubleshooting

If you get connection errors:
- Verify `DATABASE_URL` is set correctly
- Check that the database allows connections from your IP (for local runs)
- Ensure SSL settings are correct (production requires SSL)

If you get import errors:
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Verify you're in the correct directory

