# Order Transformation Platform

## Project Overview
A robust Streamlit-based order transformation platform that converts complex multi-source sales orders into standardized Xoro CSV templates. The platform supports multiple vendor ecosystems with advanced parsing capabilities and intelligent data extraction.

## Enhanced Features (Version 2.0)

### Complete Mapping Management
- **Per-Processor Management**: Dedicated UI for each order processor (KEHE, Whole Foods, UNFI East/West, TK Maxx)
- **Three Mapping Types**: Customer, Store (Xoro), and Item mappings for each processor
- **Upload/Download**: CSV file upload and download for easy migration
- **Search & Pagination**: Handle large mapping files efficiently
- **Real-time Editing**: Add, edit, and delete mappings through the UI

### Migration Tools
- **Export Mappings**: Create portable mapping packages for deployment migration
- **Import Mappings**: Seamlessly import mappings to new deployments  
- **Validation**: Built-in mapping file validation and integrity checking
- **Backup**: Automated backup creation before major changes

### Order Processing
- **Multi-vendor Support**: KEHE, UNFI East/West, Whole Foods, TK Maxx order processing
- **Real-time Conversion**: Live order transformation with comprehensive error handling
- **Debug Logging**: Detailed logging for troubleshooting and monitoring
- **Error Recovery**: Robust error handling with clear user feedback

## Setup Instructions

### 1. Environment Setup
```bash
# Install Python 3.11 or higher
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup
Set up PostgreSQL and configure the DATABASE_URL environment variable:
```bash
export DATABASE_URL="postgresql://username:password@host:port/database"
```

### 3. Initialize Database
```bash
python init_database.py
```

### 4. Run the Application
```bash
streamlit run app.py --server.port 5000
```

## Mapping Management

### UI-Based Management
1. Navigate to "Manage Mappings" in the application
2. Select an order processor (KEHE, Whole Foods, etc.)
3. Manage three mapping types:
   - **Customer Mapping**: Raw customer IDs → Xoro customer names
   - **Store Mapping**: Raw store IDs → Xoro store names  
   - **Item Mapping**: Raw item numbers → Xoro item numbers

### Migration Between Deployments
```bash
# Export mappings from source deployment
python migrate_mappings.py export

# Import mappings to target deployment  
python migrate_mappings.py import --import-dir mapping_export_YYYYMMDD_HHMMSS

# Validate all mappings
python migrate_mappings.py validate
```

## Configuration
- Main configuration: `.streamlit/config.toml`
- Environment variables: DATABASE_URL
- Mapping files: `mappings/` directory (organized by processor)

## Vendor Support
- **KEHE**: Customer mapping, store mapping, 101 item mappings (complete)
- **UNFI East/West**: Full parsing and mapping support with CSV management
- **Whole Foods**: HTML order parsing with comprehensive mappings
- **TK Maxx**: Order processing support with mapping management

## Project Structure
- `app.py` - Main Streamlit application with enhanced mapping UI
- `migrate_mappings.py` - Mapping migration and validation tools
- `database/` - Database models and services
- `parsers/` - Vendor-specific parsers (unchanged logic)
- `utils/` - Utility functions and templates
- `mappings/` - CSV mapping files organized by processor

## Key Improvements
- **User-Friendly UI**: Simplified mapping management by processor
- **Migration Ready**: Easy deployment migration with export/import tools
- **Complete Coverage**: All three mapping types for every order processor
- **CSV Based**: All mappings in CSV format for easy editing and version control
- **Search & Filter**: Find mappings quickly in large files
- **Upload/Download**: Direct file management through the UI

## Migration from Previous Version
Existing deployments can migrate to the new version:
1. Export current mappings using the migration tool
2. Deploy new version 
3. Import mappings to new deployment
4. Validate all mappings through UI

The enhanced platform maintains backward compatibility while providing significant improvements in mapping management and deployment flexibility.