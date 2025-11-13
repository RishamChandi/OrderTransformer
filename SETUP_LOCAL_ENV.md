# Setup Local Environment to Use Render Database

## Quick Setup (5 minutes)

### Step 1: Install python-dotenv (if not already installed)

```powershell
pip install python-dotenv
```

Or if using requirements.txt:
```powershell
pip install -r requirements.txt
```

### Step 2: Create `.env` file

Create a file named `.env` in the project root directory (same folder as `app.py`).

**Option A: Copy from example (if .env.example exists)**
```powershell
copy .env.example .env
```

**Option B: Create manually**

Create a new file called `.env` and add the following content:

```env
# Environment Configuration
ENVIRONMENT=local

# Render Production Database URL
# This connects the local app to the same database as the Render production app
DATABASE_URL=postgresql://order_transformer_db_user:npvK3aWfeS5d6nu9PCzfDL9JugjZgA70@dpg-d2436rjuibrs73a698cg-a.oregon-postgres.render.com/order_transformer_db
```

### Step 3: Verify .env file location

Make sure the `.env` file is in the project root directory:
```
OrderTransformer/
├── .env              ← Should be here
├── app.py
├── database/
├── parsers/
└── ...
```

### Step 4: Run the app

```powershell
python -m streamlit run app.py --server.port 8502
```

### Step 5: Verify connection

1. Open the app in your browser (usually http://localhost:8502)
2. Check the **Database Connection** section in the sidebar
3. You should see:
   - ✅ **Connected to Render Production Database**
   - Environment: local
   - Database: `postgresql://***:***@dpg-d2436rjuibrs73a698cg-a.oregon-postgres.render.com/...`

4. Navigate to "Manage Mappings" → "UNFI East" → "Customer Mapping"
5. You should now see the same 14 customer mappings as in the Render app!

## Troubleshooting

### Issue: Still seeing SQLite database

**Solution:**
1. Check if `.env` file exists: `Test-Path .env` (PowerShell)
2. Check if `.env` file is in the correct location (project root)
3. Verify the DATABASE_URL in `.env` contains `render.com`
4. Restart the app after creating/modifying `.env` file
5. Check if python-dotenv is installed: `pip list | findstr dotenv`

### Issue: Connection fails

**Solution:**
1. Verify the database URL is correct (check Render dashboard)
2. Make sure the database URL doesn't have any extra spaces or quotes
3. Check if the database is accessible from your network (some databases require whitelisting)
4. The app will automatically add `?sslmode=require` for Render databases

### Issue: python-dotenv not found

**Solution:**
```powershell
pip install python-dotenv
```

Or if you prefer to use requirements.txt:
```powershell
pip install -r requirements.txt
```

## Alternative: Use PowerShell Environment Variable

If you prefer not to use a `.env` file, you can set the environment variable directly in PowerShell:

```powershell
$env:DATABASE_URL = "postgresql://order_transformer_db_user:npvK3aWfeS5d6nu9PCzfDL9JugjZgA70@dpg-d2436rjuibrs73a698cg-a.oregon-postgres.render.com/order_transformer_db"
python -m streamlit run app.py --server.port 8502
```

**Note:** This only works for the current PowerShell session. After closing PowerShell, you'll need to set it again.

## Security Notes

⚠️ **Important:**
- The `.env` file contains sensitive credentials
- It's already in `.gitignore` - DO NOT commit it to Git
- Do not share the `.env` file with anyone
- If you suspect the credentials are compromised, rotate them in Render dashboard

## What Changed?

After setting up the `.env` file:
- ✅ Local app will connect to Render production database
- ✅ You'll see the same data as the Render app
- ✅ All changes made locally will affect production database
- ⚠️ Be careful when making changes - they affect production!

## Next Steps

1. Create `.env` file with Render database URL
2. Install python-dotenv if not already installed
3. Run the app: `python -m streamlit run app.py --server.port 8502`
4. Verify you see the same data as the Render app
5. Start using the local app with production database!

