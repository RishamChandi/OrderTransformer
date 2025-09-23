# Whole Foods Mappings Migration Guide

This guide explains how to migrate the new Whole Foods mappings to your local database and deploy them to production.

## Overview

The new Whole Foods mappings include:
- **Customer Mappings**: 51 store mappings (e.g., 10005 → WHOLE FOODS #10005 PALO ALTO)
- **Item Mappings**: 29 item mappings (e.g., 12-046-2 → 12-046-2)
- **Store Mappings**: 51 store mappings (e.g., 10005 → IDI - Richmond)

## Files Added

### New Mapping Files
- `mappings/wholefoods/Xoro Whole Foods Customer Mapping 9-17-25.csv`
- `mappings/wholefoods/Xoro Whole Foods Item Mapping 9-17-25.csv`
- `mappings/wholefoods/Xoro Whole Foods Store Mapping 9-17-25.csv`

### Scripts Created
- `setup_local_database.py` - Sets up local database and imports mappings
- `import_mappings.py` - Imports mappings to local database
- `test_wholefoods_processor.py` - Tests the order processor with new mappings
- `migrate_wholefoods_mappings.py` - Migration script for production
- `deploy_wholefoods_mappings.py` - Deployment script for Render

## Local Development Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Local Database
```bash
python setup_local_database.py
```

This will:
- Create a local SQLite database
- Set up all required tables
- Import the new Whole Foods mappings
- Verify the import was successful

### 3. Test the Processor
```bash
python test_wholefoods_processor.py
```

This will:
- Test the Whole Foods parser with sample files
- Verify mappings are working correctly
- Save test orders to the database

## Production Deployment

### Option 1: Manual Migration
```bash
# Set production environment
export ENVIRONMENT=production
export DATABASE_URL=your_production_database_url

# Run migration
python migrate_wholefoods_mappings.py
```

### Option 2: Render Deployment
The `deploy_wholefoods_mappings.py` script is designed to be run during Render deployment. Add it to your deployment process:

```bash
python deploy_wholefoods_mappings.py
```

## Verification

After migration, verify the mappings are working:

### Check Customer Mappings
```python
from database.service import DatabaseService
db = DatabaseService()
mappings = db.get_customer_mappings_advanced(source='wholefoods', active_only=True)
print(f"Customer mappings: {len(mappings)}")
```

### Check Item Mappings
```python
mappings = db.get_item_mappings_advanced(source='wholefoods', active_only=True)
print(f"Item mappings: {len(mappings)}")
```

### Check Store Mappings
```python
mappings = db.get_store_mappings_advanced(source='wholefoods', active_only=True)
print(f"Store mappings: {len(mappings)}")
```

## Expected Results

After successful migration, you should see:
- **51 customer mappings** active
- **29 item mappings** active  
- **51 store mappings** active

## Testing the Order Processor

The order processor will now:
1. **Map store numbers** to customer names (e.g., 10447 → WHOLE FOODS #10447 FOLSOM)
2. **Map item numbers** to standardized item codes (e.g., 12-046-2 → 12-046-2)
3. **Map stores** to distribution centers (e.g., 10005 → IDI - Richmond)

### Example Output
```
Order Item 1:
  Order Number: 154533670
  Customer: WHOLE FOODS #10447 FOLSOM
  Raw Customer: WHOLE FOODS #10447
  Item Number: 13-025-1
  Raw Item: 130251
  Description: BONNE MAMAN CHERRY PRESERVE
  Quantity: 1
  Unit Price: $14.94
  Total Price: $14.94
```

## Troubleshooting

### Common Issues

1. **"Invalid Item" in output**
   - This means the item number from the order file is not in the mapping file
   - Check if the item number exists in `Xoro Whole Foods Item Mapping 9-17-25.csv`
   - Add the missing mapping if needed

2. **Database connection errors**
   - Ensure DATABASE_URL is set correctly
   - Check database permissions
   - Verify network connectivity

3. **Import errors**
   - Check CSV file format
   - Ensure all required columns are present
   - Verify data types match expected format

### Logs and Debugging

Enable debug logging by setting:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Rollback

If you need to rollback the migration:

1. **Restore from backup** (if created during migration)
2. **Deactivate mappings**:
   ```python
   from database.service import DatabaseService
   db = DatabaseService()
   
   # Deactivate all Whole Foods mappings
   customer_mappings = db.get_customer_mappings_advanced(source='wholefoods', active_only=False)
   for mapping in customer_mappings:
       mapping['active'] = False
   
   # Repeat for item and store mappings
   ```

## Support

If you encounter issues:
1. Check the logs for error messages
2. Verify the mapping files are correct
3. Test with a small subset of mappings first
4. Contact the development team for assistance

## Next Steps

After successful migration:
1. **Test thoroughly** with real Whole Foods order files
2. **Monitor performance** and error rates
3. **Update documentation** if needed
4. **Train users** on any new features or changes
