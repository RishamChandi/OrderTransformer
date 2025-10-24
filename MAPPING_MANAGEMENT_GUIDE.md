# Enhanced Mapping Management Guide

## Overview

The Order Transformer platform now includes comprehensive mapping management features for all clients and mapping types (Customer, Store, Item). This guide provides detailed instructions on how to use each feature.

## Available Features

### 1. 📥 Download Template
### 2. 📊 Download Current  
### 3. 📤 Upload Mapping
### 4. 🗑️ Delete Mapping
### 5. ➕ Add New Mapping
### 6. 📝 Bulk Editor
### 7. 📋 Row by Row

## Supported Clients

- **KEHE - SPS**
- **Whole Foods**
- **UNFI East**
- **UNFI West**
- **TK Maxx**

## Supported Mapping Types

- **Customer Mapping**: Maps raw customer identifiers to Xoro customer names
- **Store Mapping**: Maps raw store identifiers to Xoro store names  
- **Item Mapping**: Maps raw item identifiers to Xoro item numbers and descriptions

---

## Feature Details

### 1. 📥 Download Template

**Purpose**: Download a CSV template with the correct format for the mapping type.

**How to Use**:
1. Navigate to any mapping section (Customer, Store, or Item)
2. Click the "📥 Download Template" button
3. A CSV file will be downloaded with example data and proper column headers
4. Use this template to create your mapping data

**Template Formats**:

**Customer Mapping Template**:
```csv
Source,Raw Customer ID,Mapped Customer Name,Customer Type,Priority,Active,Notes
kehe,CUST001,Example Customer,distributor,100,True,Example mapping
```

**Store Mapping Template**:
```csv
Source,Raw Store ID,Mapped Store Name,Store Type,Priority,Active,Notes
kehe,STORE001,Example Store,distributor,100,True,Example store mapping
```

**Item Mapping Template**:
```csv
Source,Raw Item,Mapped Item,Item Description,Priority,Active,Notes
kehe,ITEM001,MAPPED001,Example item,100,True,Example item mapping
```

### 2. 📊 Download Current

**Purpose**: Export all current mappings from the database to a CSV file.

**How to Use**:
1. Navigate to any mapping section
2. Click the "📊 Download Current" button
3. A CSV file with all current mappings will be downloaded
4. The filename includes the processor, mapping type, and timestamp

**Features**:
- Includes all mapping data (ID, Raw Name, Mapped Name, Type, Priority, Active, Notes)
- Timestamped filename for easy identification
- Ready for backup or migration purposes

### 3. 📤 Upload Mapping

**Purpose**: Import mapping data from a CSV file into the database.

**How to Use**:
1. Click the "📤 Upload Mapping" button
2. The upload form will expand
3. Review the required CSV format shown
4. Click "Choose CSV file" and select your file
5. Preview the data to ensure it's correct
6. Click "✅ Upload Mappings" to import
7. Click "❌ Cancel" to abort the upload

**CSV Requirements**:
- Must include required columns (Source, Raw ID, Mapped Name, etc.)
- Data will be validated before import
- Existing mappings will be updated, new ones will be added
- Invalid rows will be skipped with error reporting

**Upload Process**:
1. **File Validation**: Checks for required columns and data types
2. **Data Preview**: Shows first few rows of your data
3. **Import**: Bulk uploads to database with transaction safety
4. **Results**: Shows success/error counts and details

### 4. 🗑️ Delete Mapping

**Purpose**: Delete existing mappings from the database.

**How to Use**:
1. Click the "🗑️ Delete Mapping" button
2. The delete interface will show all current mappings
3. Review the mappings to be deleted
4. Click "🗑️ Delete Selected" to confirm deletion
5. Click "❌ Cancel" to abort

**Safety Features**:
- Shows all mappings before deletion
- Requires explicit confirmation
- Transaction-safe deletion
- Error handling for failed deletions

### 5. ➕ Add New Mapping

**Purpose**: Add a single new mapping through a form interface.

**How to Use**:
1. Click the "➕ Add New" button
2. Fill out the form with mapping details:
   - **Raw ID**: Original identifier from the source system
   - **Mapped Name**: Target name in Xoro system
   - **Type**: Customer/Store type (distributor, retailer, wholesaler)
   - **Priority**: Priority level (0-1000, default: 100)
   - **Active**: Whether the mapping is active
   - **Notes**: Additional notes or comments
3. Click "✅ Add Mapping" to save
4. Click "❌ Cancel" to abort

**Form Fields by Mapping Type**:

**Customer Mapping**:
- Raw Customer ID
- Mapped Customer Name
- Customer Type (dropdown)
- Priority, Active, Notes

**Store Mapping**:
- Raw Store ID
- Mapped Store Name
- Store Type (dropdown)
- Priority, Active, Notes

**Item Mapping**:
- Raw Item
- Mapped Item
- Item Description
- Priority, Active, Notes

### 6. 📝 Bulk Editor

**Purpose**: Edit multiple mappings at once using a spreadsheet-like interface.

**How to Use**:
1. Click the "📝 Bulk Editor" button
2. All current mappings will be displayed in an editable table
3. Make changes directly in the table:
   - Edit any cell by clicking and typing
   - Use checkboxes for Active status
   - Modify Priority, Notes, etc.
4. Click "💾 Save Changes" to save all modifications
5. Click "❌ Cancel" to discard changes

**Bulk Editor Features**:
- **Inline Editing**: Click any cell to edit
- **Data Validation**: Ensures data integrity
- **Bulk Operations**: Edit multiple rows simultaneously
- **Transaction Safety**: All changes saved together or rolled back
- **Real-time Preview**: See changes before saving

**Column Descriptions**:
- **ID**: Database ID (read-only)
- **Raw Name/Item**: Original identifier
- **Mapped Name/Item**: Target identifier
- **Type**: Mapping type
- **Priority**: Priority level (0-1000)
- **Active**: Checkbox for active status
- **Notes**: Additional information

### 7. 📋 Row by Row

**Purpose**: Edit mappings one at a time with detailed forms and pagination.

**How to Use**:
1. Click the "📋 Row by Row" button
2. Mappings are displayed with pagination (10 per page)
3. Each mapping has its own form with:
   - All mapping fields
   - Individual Save/Delete/Cancel buttons
4. Use pagination to navigate through all mappings
5. For each mapping:
   - Edit the fields as needed
   - Click "💾 Save" to save changes
   - Click "🗑️ Delete" to remove the mapping
   - Click "❌ Cancel" to discard changes

**Row by Row Features**:
- **Pagination**: Navigate through large datasets
- **Individual Control**: Each mapping has its own form
- **Detailed Editing**: Full form interface for each mapping
- **Individual Actions**: Save, delete, or cancel per mapping
- **Progress Tracking**: See which mapping you're editing

---

## Navigation and Interface

### Accessing Mapping Management

1. **Select Client**: Choose from the sidebar dropdown
2. **Select Action**: Choose "Manage Mappings"
3. **Choose Mapping Type**: Click on Customer, Store, or Item tabs

### Interface Layout

```
┌─────────────────────────────────────────────────────────┐
│ [📥 Download Template] [📊 Download Current] [📤 Upload] │
│ [🗑️ Delete] [➕ Add New] [📝 Bulk Editor] [📋 Row by Row] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [Selected Interface Content]                           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Button Functions

| Button | Function | Description |
|--------|----------|-------------|
| 📥 Download Template | Template | Downloads CSV template with correct format |
| 📊 Download Current | Export | Exports all current mappings to CSV |
| 📤 Upload Mapping | Import | Uploads CSV file with mapping data |
| 🗑️ Delete Mapping | Delete | Removes mappings from database |
| ➕ Add New | Create | Adds single new mapping via form |
| 📝 Bulk Editor | Edit | Edits multiple mappings in table |
| 📋 Row by Row | Edit | Edits mappings one by one with forms |

---

## Best Practices

### Data Management

1. **Backup Before Changes**: Use "Download Current" to backup before major changes
2. **Test with Templates**: Use "Download Template" to understand the format
3. **Bulk Operations**: Use "Bulk Editor" for multiple changes
4. **Individual Control**: Use "Row by Row" for detailed editing

### CSV File Management

1. **Use Templates**: Always start with downloaded templates
2. **Validate Data**: Check data types and required fields
3. **Test Uploads**: Start with small files to test the process
4. **Keep Backups**: Download current data before uploading changes

### Error Handling

1. **Validation Errors**: Check required columns and data types
2. **Upload Errors**: Review error messages for specific issues
3. **Database Errors**: Contact support for persistent issues
4. **Data Conflicts**: Resolve duplicate entries before uploading

---

## Troubleshooting

### Common Issues

**Upload Failures**:
- Check CSV format matches template
- Ensure required columns are present
- Verify data types (Priority must be numeric)
- Check for duplicate entries

**Bulk Editor Issues**:
- Save changes before navigating away
- Check for validation errors
- Ensure all required fields are filled

**Row by Row Problems**:
- Use pagination to navigate large datasets
- Save individual changes before moving to next row
- Check for form validation errors

### Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "Missing required columns" | CSV format incorrect | Use template format |
| "Invalid data type" | Wrong data in cells | Check Priority is numeric |
| "Duplicate entry" | Same mapping exists | Update existing or remove duplicate |
| "Database error" | System issue | Contact support |

---

## Support and Contact

For technical support or questions about mapping management:

1. **Check Documentation**: Review this guide for common solutions
2. **Test with Templates**: Use provided templates for correct format
3. **Contact Support**: For persistent issues or system problems
4. **Feature Requests**: Suggest improvements for future versions

---

## Version History

- **v2.0**: Enhanced mapping management with 7 comprehensive features
- **v1.0**: Basic mapping functionality

---

*This guide covers all mapping management features available in the Order Transformer platform. For additional support or feature requests, please contact the development team.*
