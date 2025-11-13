# How to Connect Local Application to Production Database

This guide shows you how to connect your local Streamlit application to the production database for testing before deploying changes.

## ⚠️ Important Warnings

1. **Be Careful**: You're connecting to the production database. Any changes you make will affect production data.
2. **Test Safely**: Only test read operations or be very careful with write operations.
3. **Don't Run Migrations**: Avoid running database migrations or schema changes from local.

## Method 1: Using PowerShell (Windows)

### Step 1: Set Environment Variables

Open PowerShell in your project directory and run:

```powershell
# Set environment to production (or leave as local - it will auto-detect production DB)
$env:ENVIRONMENT = "production"

# Set the production database URL
$env:DATABASE_URL = "postgresql://order_transformer_db_user:npvK3aWfeS5d6nu9PCzfDL9JugjZgA70@dpg-d2436rjuibrs73a698cg-a.oregon-postgres.render.com/order_transformer_db"
```

### Step 2: Run the Application

```powershell
python -m streamlit run app.py --server.port 8502
```

## Method 2: Using a .env File (Recommended)

### Step 1: Create a .env file

Create a file named `.env` in your project root directory:

```env
ENVIRONMENT=production
DATABASE_URL=postgresql://order_transformer_db_user:npvK3aWfeS5d6nu9PCzfDL9JugjZgA70@dpg-d2436rjuibrs73a698cg-a.oregon-postgres.render.com/order_transformer_db
```

### Step 2: Install python-dotenv (if not already installed)

```powershell
pip install python-dotenv
```

### Step 3: Update app.py to load .env file

Add this at the very top of `app.py` (before other imports):

```python
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
```

### Step 4: Run the Application

```powershell
python -m streamlit run app.py --server.port 8502
```

## Method 3: Using a Batch Script (Windows)

Create a file `run_with_prod_db.bat`:

```batch
@echo off
set ENVIRONMENT=production
set DATABASE_URL=postgresql://order_transformer_db_user:npvK3aWfeS5d6nu9PCzfDL9JugjZgA70@dpg-d2436rjuibrs73a698cg-a.oregon-postgres.render.com/order_transformer_db
python -m streamlit run app.py --server.port 8502
```

Then double-click the batch file to run.

## Method 4: Using Bash (Linux/Mac)

```bash
export ENVIRONMENT=production
export DATABASE_URL="postgresql://order_transformer_db_user:npvK3aWfeS5d6nu9PCzfDL9JugjZgA70@dpg-d2436rjuibrs73a698cg-a.oregon-postgres.render.com/order_transformer_db"
python -m streamlit run app.py --server.port 8502
```

## Verification

When you run the application, you should see:

```
🔌 Connecting to production database...
✅ Connected to production database successfully (attempt 1)
```

If you see connection errors, check:
1. Your internet connection
2. The database URL is correct
3. Your IP address is allowed to connect (some databases restrict by IP)

## Switching Back to Local Database

To switch back to local database:

**PowerShell:**
```powershell
$env:ENVIRONMENT = "local"
$env:DATABASE_URL = "sqlite:///local.db"
```

**Or remove/uncomment the .env file**

## Security Note

⚠️ **Never commit the .env file or database credentials to Git!**

Make sure `.env` is in your `.gitignore` file:

```
.env
*.env
```

## Troubleshooting

### Connection Timeout
- Check your firewall settings
- Verify the database URL is correct
- Try using `sslmode=allow` instead of `require` if SSL issues occur

### SSL Errors
The code automatically handles SSL for production databases. If you get SSL errors, the connection code will try fallback SSL modes.

### Authentication Errors
- Verify the username and password in the DATABASE_URL
- Check if your IP needs to be whitelisted in the database settings

