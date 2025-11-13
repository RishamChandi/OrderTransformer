# How IOW Code Mapping Works for UNFI East

## ✅ YES - The Three-Letter Code (CHE) is Used to Map Customer to Xoro Template

### Overview

The parser extracts the **three-letter IOW code** (like `CHE`, `RCH`, `HOW`) from the UNFI East PDF and uses it to look up the customer name in the database, which is then used in the Xoro Template.

### Complete Flow

```
PDF File
  ↓
Extract IOW Code (CHE)
  ↓
Look up in Database (customer_mappings table)
  ↓
Get Mapped Customer Name ("UNFI EAST CHESTERFIELD")
  ↓
Use in Xoro Template (CustomerName field)
```

## 📋 Step-by-Step Process

### 1. Extract IOW Code from PDF

The parser tries **multiple strategies** to extract the IOW code:

#### **Strategy 1: Header Pattern**
- Looks for: `*** Howell * Howell * Howell ***` at the top of PDF
- Extracts: `Howell` → Maps to `HOW`

#### **Strategy 2: Warehouse Field**
- Looks for: `Warehouse: ... Howell Warehouse` or `Warehouse: Chesterfield Warehouse`
- Extracts: `Howell` or `Chesterfield` → Maps to `HOW` or `CHE`

#### **Strategy 3: Ship To Section**
- Looks for: `Ship To: Chesterfield Warehouse` or `Ship To: Richburg Warehouse`
- Extracts: `Chesterfield` or `Richburg` → Maps to `CHE` or `RCH`

#### **Strategy 4: Int Ref# Prefix Code**
- Looks for: `Int Ref#: CC-85948-105` or `Int Ref#: JJ-85948-J10`
- Extracts: `CC` or `JJ` → Maps to `CHE` or `HOW`
- **Mapping table:**
  - `CC` → `CHE` (Chesterfield)
  - `JJ` → `HOW` (Howell)
  - `MM` → `YOR` (York)
  - `SS` → `SAR` (Sarasota)
  - `HH` → `HOW` (Howell)
  - `GG` → `GRW` (Greenwood)
  - `UU` → `HOW` (Howell)
  - `RR` → `RCH` (Richburg)
  - `YY` → `YOR` (York)

#### **Strategy 5: IOW Code on Separate Line**
- Looks for: `CHE` or `RCH` or `HOW` on lines near `Int Ref#`
- Example: `Int Ref#: CC-85948-105` on one line, then `CHE` on the next line
- Extracts: `CHE` directly

#### **Strategy 6: Document-Wide Search**
- Searches entire PDF for IOW codes: `RCH`, `HOW`, `CHE`, `YOR`, `IOW`, `GRW`, `MAN`, `ATL`, `SAR`, `SRQ`, `DAY`, `HVA`, `RAC`, `TWC`
- Maps the first valid code found

### 2. Look Up IOW Code in Database

```python
# Query database
mapping_dict = db_service.get_customer_mappings('unfi_east')
# Result: {'CHE': 'UNFI EAST CHESTERFIELD', 'RCH': 'UNFI EAST - RICHBURG', ...}

# Look up IOW code
customer_name = mapping_dict.get('CHE')  # Returns: 'UNFI EAST CHESTERFIELD'
```

### 3. Use in Xoro Template

```python
# In XoroTemplate._convert_single_order()
final_customer_name = order.get('customer_name')  # 'UNFI EAST CHESTERFIELD'

# Set in Xoro CSV
xoro_order = {
    'CustomerName': final_customer_name,  # 'UNFI EAST CHESTERFIELD'
    'CustomerFirstName': first_name,      # Split from customer name
    'CustomerLastName': last_name,        # Split from customer name
    ...
}
```

## 🎯 Example: PO4480501 (Chesterfield)

Based on the screenshot you provided:

### PDF Content:
- **Int Ref#:** `CC-85948-105`
- **IOW Code:** `CHE` (shown below Int Ref#)
- **Ship To:** `Chesterfield Warehouse`

### Extraction Process:

1. **Strategy 4 (Int Ref# Prefix):**
   - Finds: `CC-85948-105`
   - Extracts: `CC`
   - Maps: `CC` → `CHE`

2. **Strategy 5 (IOW Code on Separate Line):**
   - Finds: `CHE` on line below `Int Ref#`
   - Extracts: `CHE` directly

3. **Strategy 3 (Ship To Section):**
   - Finds: `Chesterfield Warehouse`
   - Extracts: `Chesterfield`
   - Maps: `Chesterfield` → `CHE`

### Database Lookup:

```python
mapping_dict = db_service.get_customer_mappings('unfi_east')
customer_name = mapping_dict['CHE']  # Returns: 'UNFI EAST CHESTERFIELD'
```

### Xoro Template:

```python
xoro_order = {
    'CustomerName': 'UNFI EAST CHESTERFIELD',
    'SaleStoreName': 'PSS-NJ',  # From store mapping (Order To: 85948)
    'StoreName': 'PSS-NJ',      # From store mapping (Order To: 85948)
    ...
}
```

## 📊 Database Mappings

All 14 IOW codes in the database:

| IOW Code | Customer Name | Example Int Ref# |
|----------|---------------|------------------|
| `CHE` | UNFI EAST CHESTERFIELD | CC-85948-105 |
| `HOW` | UNFI EAST - HOWELL | JJ-85948-J10 |
| `RCH` | UNFI EAST - RICHBURG | (various) |
| `YOR` | UNFI EAST YORK PA | MM-... |
| `GRW` | UNFI EAST GREENWOOD IN | GG-... |
| `MAN` | UNFI EAST MANCHESTER | (various) |
| `ATL` | UNFI EAST ATLANTA GA | (various) |
| `SAR` | UNFI EAST SARASOTA FL | SS-... |
| `SRQ` | UNFI EAST SARASOTA FL | (various) |
| `DAY` | UNFI EAST DAYVILLE CT | (various) |
| `HVA` | UNFI EAST - HUDSON VALLEY WSHE | (various) |
| `RAC` | UNFI EAST - RACINE WAREHOUSE | (various) |
| `TWC` | UNFI EAST PRESCOTT WI | (various) |
| `IOW` | UNFI EAST IOWA CITY | (various) |

## 🔍 Why Extraction Might Fail

If you see "Raw customer ID extracted: ''", it means:

1. **PDF text extraction failed** - PDF might be image-based or corrupted
2. **IOW code not found** - Code might be in a different format or location
3. **Pattern matching failed** - PDF format might be different than expected

### Solutions:

1. **Check console output** - Look for DEBUG messages showing what was extracted
2. **Verify PDF format** - Ensure PDF contains readable text (not just images)
3. **Check database** - Verify IOW code exists in `customer_mappings` table
4. **Add mapping** - If code is missing, add it via "Manage Mappings" → "UNFI East" → "Customer Mapping"

## ✅ Summary

**YES** - The parser **does use** the three-letter IOW code (like `CHE`) from the PDF to:
1. Look up the customer name in the database
2. Map it to the Xoro Template's `CustomerName` field
3. Generate the final Xoro CSV with the correct customer name

The IOW code is the **key** that links the PDF to the database mapping, which then provides the customer name for the Xoro Template.

