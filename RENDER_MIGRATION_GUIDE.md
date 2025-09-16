# 🚀 Render Database Migration Guide

## Problem
Your deployed application at `https://ordertransformer.onrender.com` shows this error:
```
column `item_mappings.key_type` does not exist
```

This happens because the database schema on Render is missing the enhanced `item_mappings` table structure.

## Solution
Run the database migration script to fix the schema and import your CSV mappings.

## Step 1: Access Render Console

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Find your `order-transformer` service
3. Click on it to open the service details

## Step 2: Run Migration Script

### Option A: Using Render Shell (Recommended)

1. In your service dashboard, click **"Shell"** tab
2. Run these commands:

```bash
# Navigate to your app directory
cd /opt/render/project/src

# Run the migration script
python render_migrate_database.py
```

### Option B: Using Render Console

1. In your service dashboard, click **"Console"** tab
2. Run the migration command:

```bash
python render_migrate_database.py
```

## Step 3: Verify Migration

After running the migration, check the logs for success messages:

```
✅ Migration completed. Added columns: key_type, priority, active, vendor, mapped_description, notes
✅ Imported 180+ item mappings
🎉 Database migration completed successfully!
```

## Step 4: Test Your Application

1. Go to `https://ordertransformer.onrender.com`
2. Try loading item mappings for any vendor
3. The error should be resolved

## What the Migration Does

1. **Creates missing columns** in `item_mappings` table:
   - `key_type` (VARCHAR(50)) - Type of item identifier
   - `priority` (INTEGER) - Priority for resolution
   - `active` (BOOLEAN) - Whether mapping is active
   - `vendor` (VARCHAR(100)) - Vendor information
   - `mapped_description` (TEXT) - Item description
   - `notes` (TEXT) - Additional notes

2. **Imports CSV mappings** to database:
   - KEHE mappings from `kehe_item_mapping.csv`
   - Whole Foods mappings from `mappings/wholefoods/item_mapping.csv`
   - UNFI East/West mappings from respective CSV files
   - TK Maxx mappings from CSV files

3. **Creates performance indexes** for faster lookups

4. **Creates other required tables** if missing

## Troubleshooting

### If Migration Fails

1. **Check DATABASE_URL**: Ensure it's set in Render environment variables
2. **Check file permissions**: Make sure the script can read CSV files
3. **Check database connection**: Verify PostgreSQL is accessible

### If You Get Permission Errors

```bash
# Make script executable
chmod +x render_migrate_database.py

# Run with explicit Python
python3 render_migrate_database.py
```

### If CSV Files Are Missing

The migration will skip sources that don't have CSV files and continue with available ones.

## Expected Results

After successful migration:
- ✅ All parsers will work with database mappings
- ✅ 180+ KEHE mappings will be available
- ✅ Other vendor mappings will be imported
- ✅ Application will load without errors
- ✅ Order processing will work correctly

## Support

If you encounter issues:
1. Check the Render service logs
2. Verify environment variables are set
3. Ensure all CSV mapping files are present
4. Contact support with the error logs

---

**🎉 Once migration is complete, your Order Transformation Platform will be fully functional on Render!**
