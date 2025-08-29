# Mapping Migration Guide

## Overview
This guide helps you migrate mappings between different deployments of the Order Transformation Platform.

## Migration Tools

### 1. Backup Current Mappings
```bash
python migrate_mappings.py backup
```
Creates a timestamped backup directory with all current mapping files.

### 2. Export Mappings for Migration
```bash
python migrate_mappings.py export
```
Creates a portable export with all mappings organized by processor:
- `kehe/customer_mapping.csv`
- `kehe/xoro_store_mapping.csv` 
- `kehe/item_mapping.csv`
- `wholefoods/customer_mapping.csv`
- `wholefoods/xoro_store_mapping.csv`
- `wholefoods/item_mapping.csv`
- And so on for all processors...

### 3. Import Mappings to New Deployment
```bash
python migrate_mappings.py import --import-dir mapping_export_20250815_143022
```
Imports all mappings from an export directory to the current deployment.

### 4. Validate Mappings
```bash
python migrate_mappings.py validate
```
Checks all mapping files for integrity and reports any issues.

## UI-Based Mapping Management

### Complete Mapping Management by Processor
The new UI provides comprehensive management for each order processor:

#### For Each Processor (KEHE, Whole Foods, UNFI East/West, TK Maxx):

**1. Customer Mapping**
- Maps raw customer identifiers to Xoro customer names
- Upload/download CSV files
- Search and pagination
- Add new mappings through UI

**2. Store (Xoro) Mapping** 
- Maps raw store identifiers to Xoro store names
- Used for SaleStoreName and StoreName fields
- Upload/download CSV files
- Search and pagination

**3. Item Mapping**
- Maps raw item numbers to Xoro item numbers
- Upload/download CSV files
- Search and pagination
- Special handling for KEHE (preserves existing 101 mappings)

### Key Features:
- **Upload**: Drag and drop CSV files for any mapping type
- **Download**: Export current mappings as CSV
- **Search**: Find specific mappings quickly
- **Pagination**: Handle large mapping files efficiently
- **Add New**: Create mappings directly in the UI
- **Validation**: Automatic file format validation

## Mapping File Structure

### Customer Mapping Format:
```csv
Raw Customer ID,Mapped Customer Name
CUST001,Customer Name 1
CUST002,Customer Name 2
```

### Store Mapping Format:
```csv
Raw Store ID,Xoro Store Name
STORE001,Store Location 1
STORE002,Store Location 2
```

### Item Mapping Format:
```csv
Raw Item Number,Mapped Item Number
ITEM001,XORO-001
ITEM002,XORO-002
```

### KEHE Special Format:
```csv
KeHE Number,ItemNumber,Description,UPC
00110368,17-041-1,BRUSCHETTA ARTICHOKE,728119098687
02313478,12-006-2,DATES MLK CHOC ALMD STFD,728119515061
```

## Deployment Migration Steps

1. **On Source System:**
   ```bash
   python migrate_mappings.py export
   # Downloads: mapping_export_YYYYMMDD_HHMMSS.zip
   ```

2. **Transfer export to new system**

3. **On Target System:**
   ```bash
   python migrate_mappings.py import --import-dir mapping_export_YYYYMMDD_HHMMSS
   python migrate_mappings.py validate
   ```

4. **Verify in UI:**
   - Go to "Manage Mappings" in the application
   - Check each processor's mappings
   - Test with sample order files

## Best Practices

- **Always backup before importing** new mappings
- **Validate mappings** after import or manual changes
- **Use descriptive names** for custom mappings
- **Test thoroughly** with sample orders after migration
- **Keep exports** for rollback purposes

## Troubleshooting

### Missing Mapping Files
Use the UI to create new mapping files:
1. Select processor in Manage Mappings
2. Click "Create [Type] Mapping File" 
3. Add entries through the UI

### Invalid CSV Format
- Ensure proper column headers
- Check for special characters
- Verify file encoding (UTF-8)

### Large Files
- Use search functionality to navigate
- Consider splitting very large files
- Pagination handles up to thousands of entries

## Migration Support
For complex migrations or issues, the mapping management UI provides:
- Real-time validation
- Error reporting
- File format guidance
- Sample templates