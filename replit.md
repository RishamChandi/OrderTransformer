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
- Store No. 10447 now correctly maps to "IDI - Richmond" customer using store mapping database
- Item numbers 130357 and 130356 correctly map to Xoro items "1" and "2" respectively
- Parser now extracts exactly 2 line items with proper quantities, descriptions, and prices
- Implemented robust metadata extraction and single-pass line item processing

## Database Schema

### Tables
- **processed_orders**: Stores order headers with customer and date information
- **order_line_items**: Stores individual line items linked to orders
- **conversion_history**: Tracks all conversion attempts with success/error status
- **store_mappings**: Customer/store name mappings by source
- **item_mappings**: Item number mappings by source