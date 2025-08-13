# Order Transformer - Xoro CSV Converter

## Overview

This is a Streamlit application that converts sales orders from multiple retail sources (Whole Foods, UNFI West, UNFI, and TK Maxx) into a standardized Xoro import CSV format. The application uses a modular parser architecture with source-specific parsers that inherit from a common base parser.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Technology**: Streamlit web application
- **Purpose**: Provides a simple file upload interface with source selection
- **Key Features**: 
  - Multi-file upload support
  - Source-specific parser selection
  - Real-time processing feedback

### Backend Architecture
- **Pattern**: Modular parser architecture with inheritance
- **Core Components**:
  - Base parser class with common functionality
  - Source-specific parser implementations
  - Utility classes for mapping and template conversion
- **File Processing**: Handles HTML, CSV, and Excel file formats

## Key Components

### Parser System
- **BaseParser**: Abstract base class providing common parsing utilities
  - Numeric value cleaning
  - Field validation
  - Mapping utilities integration
- **Source-Specific Parsers**:
  - WholeFoodsParser: Handles HTML order files
  - UNFIWestParser: Processes HTML purchase orders
  - UNFIEastParser: Processes PDF purchase orders
  - UNFIParser: Handles CSV/Excel files
  - TKMaxxParser: Processes CSV/Excel files

### Utility Classes
- **MappingUtils**: Handles customer/store name mapping and normalization
  - Caching system for performance
  - Fuzzy matching capabilities
  - Source-specific mapping support
- **XoroTemplate**: Converts parsed data to standardized Xoro CSV format
  - Defines required Xoro fields schema
  - Handles data transformation and validation

### Data Processing Flow
1. User selects order source and uploads files
2. Appropriate parser is selected based on source
3. Files are parsed using source-specific logic
4. Data is normalized using mapping utilities
5. Orders are converted to Xoro format using template converter
6. Results are presented to user for download

## Data Flow

```
File Upload → Source Selection → Parser Selection → Data Extraction → 
Name Mapping → Xoro Conversion → CSV Output
```

### Input Formats
- **HTML**: Whole Foods and UNFI West order pages
- **PDF**: UNFI East purchase orders
- **CSV/Excel**: UNFI and TK Maxx order exports

### Output Format
- Standardized Xoro CSV with predefined schema including customer info, order details, and line items

## External Dependencies

### Core Libraries
- **streamlit**: Web application framework
- **pandas**: Data manipulation and CSV/Excel processing
- **beautifulsoup4**: HTML parsing for web-scraped order pages
- **io**: File content handling

### File Format Support
- HTML parsing for web order pages
- CSV/Excel processing for exported order data
- Multi-file batch processing capability

## Deployment Strategy

### Development Environment
- Streamlit application suitable for local development and testing
- Modular structure allows easy addition of new order sources
- File-based processing without persistent storage requirements

### Scalability Considerations
- Parser system designed for easy extension
- Mapping utilities support caching for performance
- Memory-efficient file processing using streaming where possible
- Database integration for persistent storage and audit trails

### Configuration Management
- Source-specific parsers can be configured independently
- Mapping files can be updated without code changes or through web interface
- Template conversion rules centralized in XoroTemplate class
- Database automatically initialized with existing Excel mapping data

## Recent Changes

### Database Integration (January 2025)
- Added PostgreSQL database for persistent storage
- Created models for processed orders, conversion history, and mappings
- Integrated database service with automatic order saving
- Added navigation pages for viewing history and managing mappings

### UNFI West Parser Enhancement
- Improved encoding support and line item extraction
- Fixed UTF-8 encoding issues with multiple fallback encodings
- Enhanced table parsing for specific UNFI West format
- Updated to use Prod# instead of Vendor P.N. for item mapping
- Added comprehensive item mapping database with 71 Prod# to ItemNumber mappings
- Hardcoded SaleStoreName and StoreName to "KL - Richmond" for UNFI West orders
- Added dual date extraction: order date from "Dated:" field and pickup date from "PICK UP" section
- Uses pickup date for DateToBeShipped and LastDateToBeShipped in Xoro template
- Fixed Prod# mapping issue by normalizing leading zeros (05885 -> 5885) for accurate item mapping
- Updated to use Cost column (removing 'p' suffix) as unit price instead of Extension column (January 28, 2025)

### UNFI East Parser Implementation (January 2025)
- Created new parser for UNFI East PDF purchase orders
- Integrated PyPDF2 for PDF text extraction
- Added 71 item mappings and 14 store mappings for UNFI East
- Supports triple date extraction: order date (Ord Date), pickup date (Pck Date), and ETA date from PDF structure
- Uses Ord Date for OrderDate and Pck Date for DateToBeShipped/LastDateToBeShipped in Xoro template
- Maps warehouse locations (Sarasota, Atlanta, etc.) to proper customer names
- Extracts line items with Prod# mapping to Xoro ItemNumbers using normalized Prod# values
- Maps line item fields: Prod#→ItemNumber, Description→ItemDescription, Qty→Qty, Unit Cost→UnitPrice
- Creates separate Xoro records for each line item with header information merged
- Implements Order To number-based store mapping: 85948→PSS-NJ, 85950→IDI-Richmond
- Enhanced with robust manual extraction fallback for complex PDF text formats (January 28, 2025)
- Successfully extracts all line items including problematic cases with concatenated text structure
- Improved dynamic product number detection to handle various UNFI East PDF formats automatically
- Smart extraction now works for any UNFI East PDF with proper item mapping and data extraction

### Mapping System Enhancement
- Database-backed mapping with Excel file fallback
- Store and item mappings now stored in database
- Added management interface for mappings
- Maintained backward compatibility with Excel files

### Whole Foods Parser Enhancement (January 2025)
- Complete Whole Foods parser implementation with HTML support
- Added comprehensive store mapping with 51 Whole Foods locations
- Includes all major California stores plus Boise, Reno, and Vancouver locations
- Fixed date handling issues for robust parsing
- Added item mapping support for Whole Foods products with 29 authentic item mappings
- Maps various WF item number formats (spaces, dashes, compressed) to standardized Xoro format
- Unit price values copied to CustomFieldD1 field like other parsers
- Enhanced table parsing to correctly extract line items from HTML structure (January 28, 2025)
- Fixed order number extraction using regex patterns for "Purchase Order #" format
- Improved line item extraction to handle 6-column table structure: Line, Item No., Qty, Description, Size, Cost, UPC
- Always uses "IDI - Richmond" for SaleStoreName and StoreName as specified
- ThirdPartyRefNo and CustomerPO now correctly populated with order number from HTML content
- Complete parser rewrite following reference code pattern to eliminate duplicate entries (January 29, 2025)
- Fixed critical issue where parser created 7 duplicate "UNKNOWN" entries instead of parsing actual line items
- Corrected store mapping logic: Store No. 10447 maps to "WHOLE FOODS #10447 FOLSOM" for CustomerName
- Separated logic: CustomerName uses store mapping (varies by store), SaleStoreName/StoreName hardcoded to "IDI - Richmond"
- Updated database with complete 51-store mapping from StoreNo to proper company names
- Item numbers 130357 and 130356 correctly map to Xoro items "1" and "2" respectively
- Parser now extracts exactly 2 line items with proper quantities, descriptions, and prices
- Implemented robust metadata extraction and single-pass line item processing
- Added Expected Delivery Date extraction from HTML for DateToBeShipped and LastDateToBeShipped (January 29, 2025)
- DateToBeShipped now uses actual Expected Delivery Date from HTML instead of calculated date
- Example: Order Date 2025-07-27 → Expected Delivery Date 2025-07-29 used for shipping dates
- Supports multiple delivery date patterns and works across different Whole Foods HTML formats
- Updated item mapping database with complete 31-item authentic Whole Foods mapping data (January 29, 2025)
- Item numbers now properly extracted from HTML Item No. field and mapped to Xoro format
- Example: 130357 → 13-035-7, 130356 → 13-035-6 using authentic WF_ItemNo to Xoro_ItemNo mapping
- Replaced previous test mapping (1, 2) with proper Whole Foods item number conversion system
- Updated unmapped items to use "Invalid Item" as fallback instead of raw item numbers (January 29, 2025)

### KEHE - SPS Parser Implementation (January 2025)
- Created new KEHE - SPS parser to replace UNFI in dropdown menu
- Handles CSV format with header (H) and line item (D) record types
- Added 88 authentic KEHE item mappings from Buyer's Catalog/Stock Keeping # to Xoro ItemNumber
- Maps KEHE numbers like 334790 → 17-041-7, 308376 → 8-400-1, 2207887 → 8-501
- Extracts order metadata from header records (PO Number, PO Date, Requested Delivery Date)
- Processes line items with quantity, unit price, and product descriptions
- Uses "IDI - Richmond" as CustomerName consistent with other parsers
- Successfully tested with provided KEHE CSV files and verified accurate mapping conversion
- Successfully deployed to Streamlit Cloud with enhanced auto-initialization and updated dependencies (January 29, 2025)
- Added automatic database table creation on first run for seamless cloud deployment
- Enhanced with updated package versions for improved stability and security
- Enhanced KEHE parser to handle discount records (January 29, 2025)
- Added support for discount lines (Record Type 'I') that apply to previous product lines (Record Type 'D')
- Supports both percentage discounts (column BG) and flat discounts (column BH)
- Calculates optimal discount (chooses better option when both types present)
- Stores original total, discount amount, and final total for complete audit trail
- Enhanced UNFI East parser to use IOW location-based customer mapping (January 29, 2025)
- Added Excel-based IOW customer mapping system using provided mapping file
- Extracts IOW location codes from Internal Ref Number (e.g., "II-85948-H01" -> "II")
- Maps IOW codes to proper Xoro customer names: IOW -> "UNFI EAST IOWA CITY", RCH -> "UNFI EAST - RICHBURG", etc.
- Maintains fallback logic for warehouse location detection and mapping
- Added vendor-to-store mapping for UNFI East orders (January 29, 2025)
- Extracts vendor number from Order To field (e.g., "Order To: 85948 KITLVE" -> "85948")
- Maps vendor numbers to store names: 85948 -> "PSS-NJ", 85950 -> "K&L Richmond"
- Updated Xoro template to use vendor-based store mapping for SaleStoreName and StoreName fields
- Enhanced mapping UI to show vendor-to-store mapping explanation for UNFI East
- Fixed UNFI East IOW customer mapping to include missing codes GG, JJ, mm (January 29, 2025)
- Added proper mapping for warehouse-specific IOW codes: GG->Greenwood IN, JJ->Howell NJ, mm->York PA
- Updated regex patterns to handle lowercase IOW codes (mm) alongside uppercase codes (GG, JJ)
- Complete IOW customer mapping now covers all discovered warehouse location codes from PDFs
- Implemented source-based navigation system with global source selector (January 29, 2025)
- Added source-specific information display with supported formats and key features
- Updated all pages to accept source filtering parameter for focused client experience
- Enhanced process orders page to pre-select source and show relevant file types only
- Added source-specific page titles and navigation options for better user experience
- Redesigned architecture with single unified dropdown navigation (January 29, 2025)
- Eliminated redundant source selection dropdowns for cleaner user experience
- Smart navigation combines client selection and action in one dropdown
- Streamlined interface with direct routing to specific client/action combinations
- Cleaned up UNFI East store mappings to show only vendor-to-store mappings (January 29, 2025)
- Removed unnecessary IOW customer mappings from store mapping interface
- Store mappings now only show vendor numbers (85948, 85950) and their corresponding stores
- IOW customer mappings remain available in the Customer Mapping tab as intended
- Implemented environment-based database switching to resolve SSL connection issues (January 29, 2025)
- Automatic detection: Replit (development/no SSL) vs Streamlit Cloud (production/SSL required)
- Smart fallback handling for SSL connection errors in development environments
- Enhanced Manage Mappings interface with editable functionality (January 29, 2025)
- Added three-tab layout: Store Mapping, Customer Mapping, and Item Mapping
- Full CRUD operations: Add, edit, delete mappings with real-time updates
- Search and pagination for large item mapping datasets
- Source-specific filtering for better organization
- Fixed SSL connection handling with multiple fallback strategies for production database in development
- Successfully connected using SSL allow mode with enhanced error handling and troubleshooting

## Database Schema

### Tables
- **processed_orders**: Stores order headers with customer and date information
- **order_line_items**: Stores individual line items linked to orders
- **conversion_history**: Tracks all conversion attempts with success/error status
- **store_mappings**: Customer/store name mappings by source
- **item_mappings**: Item number mappings by source