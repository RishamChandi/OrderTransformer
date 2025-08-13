# Order Transformer - Xoro CSV Converter

## Overview
This Streamlit application converts sales orders from various retail sources (Whole Foods, UNFI West, UNFI, TK Maxx, KEHE - SPS) into a standardized Xoro import CSV format. Its purpose is to streamline order processing by centralizing disparate order formats into a single, consistent output for Xoro, improving efficiency and data accuracy for businesses managing multiple retail channels. The project aims to provide a robust, extensible solution for automated sales order data transformation, reducing manual data entry and potential errors.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture
The application is built as a Streamlit web application with a modular parser architecture.

### Frontend
- **Technology**: Streamlit
- **Features**: Multi-file upload, source-specific parser selection, real-time processing feedback.

### Backend
- **Pattern**: Modular parser architecture with inheritance.
- **Core Components**:
    - **BaseParser**: Abstract class for common parsing utilities (numeric cleaning, validation, mapping).
    - **Source-Specific Parsers**: Implementations for Whole Foods (HTML), UNFI West (HTML), UNFI East (PDF), UNFI (CSV/Excel), TK Maxx (CSV/Excel), and KEHE - SPS (CSV).
    - **Utility Classes**:
        - **MappingUtils**: Handles customer/store name and item number mapping with caching and fuzzy matching.
        - **XoroTemplate**: Converts parsed data to the standardized Xoro CSV format, defining schema and handling transformations.
- **Data Processing Flow**: User upload → Source selection → Parser selection → Data extraction → Name/Item mapping → Xoro conversion → CSV output.
- **Input Formats**: HTML, PDF, CSV, Excel.
- **Output Format**: Standardized Xoro CSV.
- **Technical Implementations**:
    - Database integration (PostgreSQL) for persistent storage of processed orders, conversion history, and mappings.
    - Automatic database initialization and table creation for seamless deployment.
    - Robust date and item number extraction, including handling of various formats and special cases (e.g., discounts in KEHE, specific date fields for UNFI East/Whole Foods).
    - Dynamic product number detection and mapping to Xoro ItemNumbers.
    - Vendor-to-store mapping for UNFI East orders.
    - Comprehensive store and item mapping databases with CRUD operations via a management interface.
- **System Design Choices**:
    - Focus on extensibility to easily add new order sources.
    - Memory-efficient file processing.
    - Environment-based database switching to manage SSL connections.
    - Unified dropdown navigation for streamlined user experience.
    - Source-specific information display and filtering.

## External Dependencies
- **streamlit**: Web application framework.
- **pandas**: Data manipulation and CSV/Excel processing.
- **beautifulsoup4**: HTML parsing.
- **PyPDF2**: PDF text extraction (for UNFI East).
- **io**: File content handling.
- **PostgreSQL**: Database for persistent storage of order data and mappings.