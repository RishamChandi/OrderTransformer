# Connect Local App to Render Production Database

## Problem

Your local app is currently using a SQLite database (`sqlite:///local.db`), which is **separate** from the Render production database. This is why you see different data in the local app vs the Render app.

## Solution

Set the `DATABASE_URL` environment variable to your Render database URL to connect the local app to the production database.

## Steps

### 1. Get Your Render Database URL

1. Go to your Render dashboard: https://dashboard.render.com
2. Navigate to your PostgreSQL database service
3. Copy the **External Database URL** (starts with `postgresql://`)

### 2. Set DATABASE_URL Environment Variable

#### Option A: PowerShell (Windows)

```powershell
# Set the DATABASE_URL to your Render database URL
$env:DATABASE_URL = "postgresql://user:password@hostname.render.com:5432/dbname?sslmode=require"

# Run the app
python -m streamlit run app.py --server.port 8502
```

#### Option B: Command Prompt (Windows)

```cmd
set DATABASE_URL=postgresql://user:password@hostname.render.com:5432/dbname?sslmode=require
python -m streamlit run app.py --server.port 8502
```

#### Option C: Create a `.env` file (Recommended)

1. Create a `.env` file in the project root directory
2. Add your Render database URL:

```env
DATABASE_URL=postgresql://user:password@hostname.render.com:5432/dbname?sslmode=require
ENVIRONMENT=local
```

3. The app will automatically load the `.env` file if `python-dotenv` is installed

#### Option D: Bash/Linux/Mac

```bash
export DATABASE_URL="postgresql://user:password@hostname.render.com:5432/dbname?sslmode=require"
streamlit run app.py --server.port 8502
```

### 3. Verify Connection

1. Start the app
2. Check the **Database Connection** section in the sidebar
3. You should see:
   - ✅ **Connected to Render Production Database**
   - Environment: local (or production)
   - Database: `postgresql://***:***@hostname.render.com/...`

### 4. Verify Data

1. Navigate to "Manage Mappings" → "UNFI East" → "Customer Mapping"
2. You should now see the same 14 customer mappings as in the Render app

## Important Notes

⚠️ **WARNING**: When connected to the Render database, **all data changes will affect the production database**. This includes:
- Adding new mappings
- Editing existing mappings
- Deleting mappings
- Processing orders

⚠️ **Security**: The Render database URL contains your database credentials. Do NOT commit it to Git. Use `.env` file and add `.env` to `.gitignore`.

## Troubleshooting

### Issue: Connection fails with SSL error

**Solution**: The app automatically adds `?sslmode=require` to Render database URLs. If you're still having issues, make sure your database URL doesn't already have conflicting SSL parameters.

### Issue: Still seeing SQLite database

**Solution**: 
1. Check if `DATABASE_URL` is set correctly: `echo $env:DATABASE_URL` (PowerShell) or `echo $DATABASE_URL` (Bash)
2. Make sure there's no `.env` file with `DATABASE_URL=sqlite:///local.db`
3. Restart the app after setting the environment variable

### Issue: Can't find Render database URL

**Solution**: 
1. Go to Render dashboard → Your database service
2. Look for "Connections" or "Connection String" section
3. Copy the "External Database URL"
4. The URL should look like: `postgresql://user:password@hostname.render.com:5432/dbname`

## Current Behavior

- **Render app**: Always uses Render production database
- **Local app**: 
  - If `DATABASE_URL` contains `render.com` → Uses Render production database
  - If `DATABASE_URL` contains `sqlite://` → Uses local SQLite database (separate from production)
  - If `DATABASE_URL` is not set → Error (app won't start)

## Next Steps

1. Set `DATABASE_URL` to your Render database URL
2. Restart the local app
3. Verify you see the same data as the Render app
4. All changes made locally will now affect the production database

