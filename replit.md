# Order Transformation Platform

## Project Overview
A robust Streamlit-based order transformation platform that converts complex multi-source sales orders into standardized Xoro CSV templates. The platform supports multiple vendor ecosystems with advanced parsing capabilities and intelligent data extraction.

## Recent Changes

### Latest Updates (October 16, 2025)

#### UNFI West Parser Enhancement
✅ **Fixed missing cost extraction** - Updated UNFI West parser to handle line items with empty Vendor P.N. fields
✅ **Robust cost detection** - Added fallback logic to detect costs with or without 'p' suffix (e.g., "13.5000p" or "13.5000")
✅ **Backward compatibility** - Maintains existing parsing logic for items with Vendor P.N. while adding secondary scan for missing fields
✅ **Validated fix** - Tested with problematic HTML files showing correct cost extraction ($13.50 instead of $0.00)

#### Database-First Item Mapping System (September 12, 2025)
✅ **Complete migration to database** - Successfully migrated 180 KEHE item mappings from CSV to PostgreSQL
✅ **Priority-based resolution** - Implemented multi-key type resolution (vendor_item, UPC, EAN, GTIN) with priority ordering
✅ **Enhanced database schema** - Added columns: key_type, priority, active, vendor, mapped_description, notes
✅ **Bulk operations** - Created efficient bulk_upsert_item_mappings for batch imports
✅ **Advanced filtering** - Built comprehensive UI with source, key_type, and active status filters
✅ **Template system** - Standardized CSV template for all processors with upload/download capabilities

### Enhanced Mapping Management System (August 29, 2025)
✅ **Complete UI Overhaul** - Rebuilt mapping management with processor-specific organization (KEHE, Whole Foods, UNFI East/West, TK Maxx)
✅ **Inline Editing & Delete** - Added click-to-edit functionality with save/cancel options and delete buttons for each mapping row
✅ **Data Editor Integration** - Implemented dual view modes: Data Editor for bulk editing and Row-by-Row for individual edits
✅ **Upload/Download System** - Complete CSV file management with upload, download, search, and pagination
✅ **Migration Tools** - Built export/import system with `migrate_mappings.py` for deployment transfers
✅ **Enhanced Debug Logging** - Added comprehensive date formatting debug for UNFI East order processing

### Previous KEHE Customer Mapping Implementation
✅ **Fixed KEHE customer mapping system** - Successfully implemented Ship To Location to Company Name mapping
✅ **Resolved leading zero preservation** - Updated CSV format and parser to preserve leading zeros in Ship To Location numbers
✅ **Added dedicated KEHE mapping UI** - Created customer mapping management interface for KEHE source
✅ **Corrected CustomerName field** - Xoro template now shows mapped company names instead of hardcoded "IDI - Richmond"
✅ **Enhanced data type handling** - Fixed pandas CSV reading to preserve string format for Ship To Location codes

### Previous Deployment Fixes
✅ **Updated cloud configuration** - Modified `cloud_config.py` to prioritize Replit environment variables over Streamlit secrets
✅ **Added Streamlit configuration** - Created `.streamlit/config.toml` with proper server settings for deployment
✅ **Enhanced environment detection** - Improved environment detection for Replit deployments in `database/env_config.py`
✅ **Added health check endpoint** - Implemented health check functionality for deployment readiness
✅ **Improved error handling** - Enhanced database initialization with deployment-specific error handling
✅ **Fixed SSL configuration** - Updated database URL handling for better Replit deployment compatibility
✅ **Resolved LSP errors** - Fixed all code issues including import errors and null reference checks

### Key Configuration Changes
- **Server Configuration**: Set to bind on `0.0.0.0:5000` with proper CORS and security settings
- **Environment Detection**: Enhanced detection for Replit vs Streamlit Cloud deployments
- **Database Connection**: Improved SSL handling with fallback strategies for different environments
- **Health Check**: Added `?health=check` endpoint for deployment readiness verification

## Architecture

### Key Technologies
- **Frontend**: Streamlit web interface with custom styling
- **Backend**: SQLAlchemy ORM with PostgreSQL database
- **File Processing**: Advanced parsing for PDF, HTML, CSV, Excel formats
- **Multi-vendor Support**: Dynamic mapping system for various vendor ecosystems
- **Data Transformation**: Pandas-based data manipulation and CSV generation

### Core Components
- **Parsers**: Vendor-specific parsers (Whole Foods, UNFI East/West, KEHE, TK Maxx)
- **Database Service**: Centralized database operations and mapping management
- **Xoro Template**: Standardized CSV output format with dynamic customer mapping
- **KEHE Customer Mapping**: Ship To Location to Company Name mapping system with leading zero preservation
- **Mapping Utils**: Customer, store, and item mapping utilities
- **Cloud Config**: Environment-aware configuration management

### Database Schema
- Orders tracking with source attribution
- Customer, store, and item mappings
- Conversion history and audit trails
- Vendor-specific configuration storage

## Deployment Configuration

### Environment Variables Required
- `DATABASE_URL` - PostgreSQL connection string
- `REPL_ID` - Replit deployment identifier (auto-set)
- `ENVIRONMENT` - Optional override (production/development/local)

### Health Check
- Endpoint: `/?health=check`
- Returns JSON status with database connectivity check
- Used for deployment readiness verification

### SSL Configuration
- **Development**: SSL disabled for local/development environments
- **Production**: SSL allow mode for Replit deployments
- **Fallback**: Multiple connection strategies with error recovery

## User Preferences
- Clean, technical communication style preferred
- Focus on comprehensive solutions over iterative updates
- Detailed error handling and troubleshooting information
- Streamlined deployment process with minimal configuration

## Known Issues & Solutions
- **Neon Database Endpoint**: If "endpoint has been disabled" error appears, reactivate endpoint via Neon dashboard (see DATABASE_REACTIVATION_GUIDE.md)
- **Database SSL**: Configured automatic SSL handling based on environment
- **Deployment Health**: Health check endpoint ensures proper initialization
- **Error Handling**: Enhanced error messages for troubleshooting deployment issues
- **KEHE Leading Zeros**: Fixed CSV format and pandas data types to preserve Ship To Location leading zeros
- **Customer Mapping**: Successfully implemented dynamic customer name mapping for KEHE orders
- **UNFI West Missing Costs**: Fixed parser to handle items with empty Vendor P.N. fields (lines 260-302 in unfi_west_parser.py)

## Future Enhancements
- Additional vendor parser support
- Real-time processing monitoring
- Enhanced mapping management UI
- Automated deployment testing