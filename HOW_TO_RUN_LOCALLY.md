# How to Run the Application Locally

This guide shows you how to run the Order Transformer application on your local machine.

## Prerequisites

1. **Python 3.8+** installed on your system
2. **All dependencies** installed from `requirements.txt`

## Step 1: Install Dependencies

Open PowerShell (or Terminal) in your project directory and run:

```powershell
pip install -r requirements.txt
```

If you encounter issues, try:
```powershell
python -m pip install -r requirements.txt
```

## Step 2: Connect to Production Database

⚠️ **Warning**: This connects to the production database. Be careful with any changes!

**PowerShell:**
```powershell
$env:ENVIRONMENT = "production"
$env:DATABASE_URL = "postgresql://order_transformer_db_user:npvK3aWfeS5d6nu9PCzfDL9JugjZgA70@dpg-d2436rjuibrs73a698cg-a.oregon-postgres.render.com/order_transformer_db"
python -m streamlit run app.py --server.port 8502
```

**Or create a `.env` file:**
```env
ENVIRONMENT=production
DATABASE_URL=postgresql://order_transformer_db_user:npvK3aWfeS5d6nu9PCzfDL9JugjZgA70@dpg-d2436rjuibrs73a698cg-a.oregon-postgres.render.com/order_transformer_db
```

Then run:
```powershell
python -m streamlit run app.py --server.port 8502
```

### Alternative: Use Local Database (SQLite) - Only if you want to test without affecting production

If you want to use a local SQLite database instead (for safe testing without affecting production):

**PowerShell:**
```powershell
$env:DATABASE_URL = "sqlite:///local.db"
python -m streamlit run app.py --server.port 8502
```

**Or create a `.env` file:**
```env
DATABASE_URL=sqlite:///local.db
ENVIRONMENT=local
```

Then run:
```powershell
python -m streamlit run app.py --server.port 8502
```

## Step 3: Access the Application

Once the app starts, you should see:

```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8502
Network URL: http://192.168.x.x:8502
```

Open your browser and go to: **http://localhost:8502**

## Quick Reference Commands

### Start with Production Database (Recommended for Testing)
```powershell
$env:ENVIRONMENT = "production"
$env:DATABASE_URL = "postgresql://order_transformer_db_user:npvK3aWfeS5d6nu9PCzfDL9JugjZgA70@dpg-d2436rjuibrs73a698cg-a.oregon-postgres.render.com/order_transformer_db"
python -m streamlit run app.py --server.port 8502
```

### Start with Local Database (Only if you want to avoid affecting production)
```powershell
$env:DATABASE_URL = "sqlite:///local.db"
python -m streamlit run app.py --server.port 8502
```

### Start on Different Port
```powershell
python -m streamlit run app.py --server.port 8503
```

## Troubleshooting

### Issue: "Port 8502 is already in use"

**Solution:** Use a different port:
```powershell
python -m streamlit run app.py --server.port 8503
```

### Issue: "DATABASE_URL environment variable not found"

**Solution:** Set the DATABASE_URL before running:
```powershell
$env:DATABASE_URL = "sqlite:///local.db"
python -m streamlit run app.py --server.port 8502
```

### Issue: "ModuleNotFoundError: No module named 'X'"

**Solution:** Install missing dependencies:
```powershell
pip install -r requirements.txt
```

### Issue: Connection errors when using production database

**Solutions:**
1. Check your internet connection
2. Verify the database URL is correct
3. Check if your IP needs to be whitelisted in Render database settings
4. Try using `sslmode=allow` instead of `require` (the code handles this automatically)

### Issue: "streamlit: command not found"

**Solution:** Use Python module syntax:
```powershell
python -m streamlit run app.py --server.port 8502
```

## Using .env File (Recommended)

For easier setup, create a `.env` file in your project root:

**For production database testing (Recommended):**
```env
ENVIRONMENT=production
DATABASE_URL=postgresql://order_transformer_db_user:npvK3aWfeS5d6nu9PCzfDL9JugjZgA70@dpg-d2436rjuibrs73a698cg-a.oregon-postgres.render.com/order_transformer_db
```

**For local database (Only if you want to avoid affecting production):**
```env
DATABASE_URL=sqlite:///local.db
ENVIRONMENT=local
```

Then install python-dotenv:
```powershell
pip install python-dotenv
```

The app will automatically load the `.env` file when it starts.

## Stopping the Application

Press `Ctrl+C` in the terminal/PowerShell window to stop the application.

## Next Steps

1. **Initialize Database** (if using local database):
   - Go to the app → System → Initialize Database
   - This creates the necessary tables

2. **Test with Sample Files**:
   - Upload test order files
   - Process them to verify everything works

3. **Manage Mappings**:
   - Set up customer, store, and item mappings
   - Test the mapping functionality

## Development Tips

- **Hot Reload**: Streamlit automatically reloads when you save code changes
- **Debug Mode**: Check the terminal for debug messages and errors
- **Clear Cache**: Use `Ctrl+C` to stop, then restart if you encounter caching issues
- **View Logs**: All debug output appears in the terminal where you ran the command

