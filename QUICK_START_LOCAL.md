# Quick Start: Connect Local App to Render Database

## The Problem
Your local app is using SQLite (`sqlite:///local.db`) which is **separate** from the Render production database. That's why you see different data locally vs on Render.

## The Solution (3 Steps)

### Step 1: Install python-dotenv
```powershell
pip install python-dotenv
```

### Step 2: Create `.env` file
Create a file named `.env` in the project root (same folder as `app.py`) with this content:

```env
ENVIRONMENT=local
DATABASE_URL=postgresql://order_transformer_db_user:npvK3aWfeS5d6nu9PCzfDL9JugjZgA70@dpg-d2436rjuibrs73a698cg-a.oregon-postgres.render.com/order_transformer_db
```

**Where to create it:**
```
OrderTransformer/          ← Project root
├── .env                  ← Create here
├── app.py
├── database/
└── ...
```

### Step 3: Run the app
```powershell
python -m streamlit run app.py --server.port 8502
```

## Verify It's Working

1. Open http://localhost:8502
2. Check the **Database Connection** section in sidebar (should be expanded)
3. You should see: ✅ **Connected to Render Production Database**
4. Go to "Manage Mappings" → "UNFI East" → "Customer Mapping"
5. You should now see the same 14 customer mappings as Render! 🎉

## Alternative: Use PowerShell Environment Variable

If you prefer not to use `.env` file:

```powershell
$env:DATABASE_URL = "postgresql://order_transformer_db_user:npvK3aWfeS5d6nu9PCzfDL9JugjZgA70@dpg-d2436rjuibrs73a698cg-a.oregon-postgres.render.com/order_transformer_db"
python -m streamlit run app.py --server.port 8502
```

**Note:** This only works for the current PowerShell session.

## Important Warnings

⚠️ **When connected to Render database:**
- All data changes will affect production
- Be careful when adding/editing/deleting mappings
- All changes are permanent

⚠️ **Security:**
- The `.env` file contains your database password
- It's already in `.gitignore` - DO NOT commit it to Git
- Do not share the `.env` file

## Troubleshooting

### Still seeing SQLite?
1. Make sure `.env` file exists in project root
2. Check if python-dotenv is installed: `pip list | findstr dotenv`
3. Restart the app after creating `.env`
4. Verify DATABASE_URL in `.env` contains `render.com`

### Connection fails?
1. Verify the database URL is correct
2. Check if database is accessible (some require network whitelisting)
3. Make sure no extra spaces/quotes in DATABASE_URL

### Need help?
See `SETUP_LOCAL_ENV.md` for detailed instructions.

