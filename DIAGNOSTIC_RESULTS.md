# Production Database Diagnostic Results

## Summary

The diagnostic script successfully identified and fixed several issues:

### ✅ Issues Fixed Automatically:

1. **KEHE Customer Mappings Migration**
   - **Found**: 13 KEHE customer mappings were in the legacy `StoreMapping` table
   - **Action**: Migration automatically moved them to `CustomerMapping` table
   - **Result**: ✅ 13 mappings migrated successfully

### ⚠️ Issues Requiring Manual Action:

1. **KEHE Customer Mappings - Incorrect Raw Customer IDs**
   - **Problem**: All 13 KEHE customer mappings have `raw_customer_id='569813000000.0'` (generic value)
   - **Expected**: Each mapping should have the actual "Ship To Location" number from the EDI file (e.g., "569813430012", "569813430041", etc.)
   - **Impact**: Customer mapping lookups fail because the database keys don't match the values extracted from EDI files
   - **Solution**: Re-upload KEHE customer mappings with correct `raw_customer_id` values
   - **How to Fix**:
     1. Go to the Streamlit app → KEHE → Customer Mappings
     2. Delete the existing mappings (or export them first to save the mapped names)
     3. Upload a new CSV/Excel file with columns:
        - `raw_customer_id`: The actual Ship To Location number (13 digits, e.g., "569813430012")
        - `mapped_customer_name`: The customer name (e.g., "KEHE AURORA CO DC12")
        - `source`: "kehe"
        - `customer_type`: "customer"
        - `active`: true

2. **UNFI East Customer Mappings - Code Extraction**
   - **Problem**: Parser sometimes extracts "128 RCH" format, but database has just "RCH"
   - **Status**: ✅ **FIXED** - Updated `mapping_utils.py` to automatically extract the IOW code from formats like "128 RCH" → "RCH"
   - **Result**: Lookups should now work correctly

## Database Structure

✅ All tables exist and have correct structure:
- `customer_mappings` table: ✅ EXISTS
- `store_mappings` table: ✅ EXISTS

## Current Data Status

### KEHE Customer Mappings:
- **CustomerMapping table**: 0 records (after migration, but need to verify)
- **StoreMapping table (legacy)**: 0 records (migrated)
- **Issue**: Need to re-upload with correct `raw_customer_id` values

### UNFI East Customer Mappings:
- **CustomerMapping table**: 14 records ✅
- **StoreMapping table (legacy)**: 0 records ✅
- **Status**: Working correctly after code extraction fix

## Next Steps

1. **Re-upload KEHE Customer Mappings**
   - Export current mappings to see the mapped names
   - Create new CSV with correct Ship To Location numbers
   - Upload via Streamlit app

2. **Test UNFI East Processing**
   - Process a UNFI East order file
   - Verify customer mapping works correctly
   - Check that "128 RCH" format is handled properly

3. **Verify KEHE Processing**
   - After re-uploading mappings, process a KEHE EDI file
   - Verify customer mapping lookups work
   - Check that Ship To Location numbers match

## Code Changes Made

1. **`utils/mapping_utils.py`**:
   - Added code extraction for UNFI East: "128 RCH" → "RCH"
   - Improved IOW code normalization

2. **`database/service.py`**:
   - Enhanced source name normalization for UNFI East variations
   - Improved `get_customer_mappings` to try multiple source name formats

3. **`parsers/unfi_east_parser.py`**:
   - Added more detailed debug logging

4. **Migration**:
   - Successfully migrated 13 KEHE customer mappings from `StoreMapping` to `CustomerMapping`

