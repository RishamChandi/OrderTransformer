# UNFI East Customer Mappings - Summary

## ✅ Mappings Are Used From Database

**YES** - The application uses customer mappings from the **Render PostgreSQL database** (production database).

### How It Works:

1. **Parser extracts IOW code from PDF**: The UNFI East parser extracts IOW codes (like RCH, HOW, CHE, etc.) from the PDF order files
2. **MappingUtils looks up in database**: The `MappingUtils.get_customer_mapping()` method queries the database
3. **DatabaseService retrieves mappings**: The `DatabaseService.get_customer_mappings('unfi_east')` method retrieves all active mappings from the `customer_mappings` table
4. **Mapping applied**: The extracted IOW code is matched to the database key (`raw_customer_id`) and the mapped customer name is returned

## 📊 What's Currently in the Database

### Total Mappings: **14 active customer mappings**

| Raw Customer ID (IOW Code) | Mapped Customer Name | Database ID |
|---------------------------|---------------------|-------------|
| **ATL** | UNFI EAST ATLANTA GA | 127 |
| **CHE** | UNFI EAST CHESTERFIELD | 122 |
| **DAY** | UNFI EAST DAYVILLE CT | 125 |
| **GRW** | UNFI EAST GREENWOOD IN | 126 |
| **HOW** | UNFI EAST - HOWELL | 121 |
| **HVA** | UNFI EAST - HUDSON VALLEY WSHE | 129 |
| **IOW** | UNFI EAST IOWA CITY | 124 |
| **MAN** | UNFI EAST MANCHESTER | 132 |
| **RAC** | UNFI EAST - RACINE WAREHOUSE | 130 |
| **RCH** | UNFI EAST - RICHBURG | 120 |
| **SAR** | UNFI EAST SARASOTA FL | 128 |
| **SRQ** | UNFI EAST SARASOTA FL | 133 |
| **TWC** | UNFI EAST PRESCOTT WI | 131 |
| **YOR** | UNFI EAST YORK PA | 123 |

### Database Table: `customer_mappings`
- **Source**: `unfi_east`
- **Active**: All mappings are active (`active = True`)
- **Priority**: All mappings have priority 100
- **Customer Type**: `customer`

## 📁 How Mappings Were Uploaded

### Migration Script: `migrate_unfi_east_customer_mappings.py`

The migration script was designed to:
1. **Read Excel file**: `attached_assets/UNFI EAST STORE TO CUSTOMER MAPPING_1753461773530.xlsx`
2. **Extract mappings**: Read IOW codes from "UNFI East " column and company names from "CompanyName" column
3. **Add additional mappings**: Add codes like SS, HH, GG, JJ, MM that were discovered from PDFs
4. **Insert into database**: Use `bulk_upsert_store_mappings()` method

### ⚠️ Issue with Migration Script

The migration script uses `bulk_upsert_store_mappings()` which inserts into the **StoreMapping** table, not the **CustomerMapping** table. However, the current database has mappings in the **CustomerMapping** table, which suggests they were uploaded differently or migrated later.

### ✅ Current Status

The database currently has **14 mappings in the CustomerMapping table**, which is the correct table for customer mappings. These mappings are working correctly and are being used by the application.

## 🔍 Potential Missing Mappings

Based on the migration script and historical data, these codes were mentioned but are **NOT currently in the database**:

| Code | Suggested Mapping | Status |
|------|------------------|--------|
| **SS** | UNFI EAST SARASOTA FL | ❌ NOT IN DATABASE |
| **HH** | UNFI EAST HOWELL NJ | ❌ NOT IN DATABASE |
| **GG** | UNFI EAST GREENWOOD IN | ❌ NOT IN DATABASE (but GRW is) |
| **JJ** | UNFI EAST HOWELL NJ | ❌ NOT IN DATABASE |
| **MM** | UNFI EAST YORK PA | ❌ NOT IN DATABASE |

### Note About 'GG' vs 'GRW':

- The migration script tried to add 'GG' for Greenwood
- But the database has 'GRW' for Greenwood (which is correct)
- The parser was updated to use 'GRW' instead of 'GG'

## 🎯 How Mappings Are Used

### 1. Parser Extraction:
- Parser extracts warehouse location from PDF (e.g., "Richburg", "Howell")
- Maps warehouse name to IOW code (e.g., "Richburg" → "RCH")
- Looks up IOW code in database

### 2. Database Lookup:
```python
mapping_utils.get_customer_mapping('RCH', 'unfi_east')
# Returns: 'UNFI EAST - RICHBURG'
```

### 3. Xoro Template:
- Uses mapped customer name in Xoro CSV output
- Customer name goes in `CustomerName` field
- Store name (from store mapping) goes in `SaleStoreName` and `StoreName` fields

## ✅ Verification

All 14 mappings in the database are working correctly:
- ✅ RCH → UNFI EAST - RICHBURG
- ✅ HOW → UNFI EAST - HOWELL
- ✅ CHE → UNFI EAST CHESTERFIELD
- ✅ YOR → UNFI EAST YORK PA
- ✅ IOW → UNFI EAST IOWA CITY
- ✅ GRW → UNFI EAST GREENWOOD IN
- ✅ MAN → UNFI EAST MANCHESTER
- ✅ ATL → UNFI EAST ATLANTA GA
- ✅ SAR → UNFI EAST SARASOTA FL
- ✅ SRQ → UNFI EAST SARASOTA FL
- ✅ DAY → UNFI EAST DAYVILLE CT
- ✅ HVA → UNFI EAST - HUDSON VALLEY WSHE
- ✅ RAC → UNFI EAST - RACINE WAREHOUSE
- ✅ TWC → UNFI EAST PRESCOTT WI

## 🔧 If Orders Fail

If you see errors like "No customer mapping found for UNFI East order", it means:

1. **Parser couldn't extract IOW code from PDF**: The PDF might not contain readable IOW codes
2. **Extracted code doesn't match database**: The extracted code might be one of the missing codes (SS, HH, JJ, MM) or a code that's not in the database
3. **Solution**: Check the console output to see what was extracted, then add the mapping to the database if needed

## 📝 Summary

- ✅ **Mappings are loaded from database**: YES
- ✅ **Database**: Render PostgreSQL (production)
- ✅ **Table**: `customer_mappings`
- ✅ **Total mappings**: 14 active mappings
- ✅ **All valid IOW codes work**: RCH, HOW, CHE, YOR, IOW, GRW, MAN, ATL, SAR, SRQ, DAY, HVA, RAC, TWC
- ⚠️ **Some codes not in database**: SS, HH, JJ, MM (may need to be added if PDFs contain these codes)

