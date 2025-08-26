# Order Transformation Platform

## Project Overview
A robust Streamlit-based order transformation platform that converts complex multi-source sales orders into standardized Xoro CSV templates. The platform supports multiple vendor ecosystems with advanced parsing capabilities and intelligent data extraction.

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

## Features
- Multi-vendor order parsing (KEHE, UNFI East/West, Whole Foods, TK Maxx)
- Dynamic customer, store, and item mapping
- Real-time order processing and conversion
- Comprehensive mapping management interface
- PostgreSQL database integration
- Advanced error handling and debugging

## Configuration
- Main configuration: `.streamlit/config.toml`
- Environment variables: DATABASE_URL
- Mapping files: `mappings/` directory

## Vendor Support
- **KEHE**: Customer mapping, store mapping, item mapping
- **UNFI East/West**: Full parsing and mapping support
- **Whole Foods**: HTML order parsing
- **TK Maxx**: Order processing support

## Project Structure
- `app.py` - Main Streamlit application
- `database/` - Database models and services
- `parsers/` - Vendor-specific parsers
- `utils/` - Utility functions and templates
- `mappings/` - CSV mapping files