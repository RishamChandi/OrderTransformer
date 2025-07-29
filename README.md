# Order Transformer - Xoro CSV Converter

A Streamlit web application that converts sales orders from multiple retail sources into standardized Xoro import CSV format.

## Supported Sources

- **Whole Foods**: HTML order files
- **KEHE - SPS**: CSV order files  
- **UNFI West**: HTML purchase orders
- **UNFI East**: PDF purchase orders
- **TK Maxx**: CSV/Excel order exports

## Features

- Multi-file upload support
- Intelligent item mapping using authentic vendor catalogs
- Database storage for processed orders and conversion history
- Real-time processing feedback
- Download converted Xoro CSV files

## Installation

### Local Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd order-transformer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up PostgreSQL database:
```bash
# Set environment variable
export DATABASE_URL="postgresql://username:password@localhost:5432/database_name"

# Initialize database
python init_database.py
```

4. Run the application:
```bash
streamlit run app.py --server.port 8501
```

### Streamlit Cloud Deployment

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Set up secrets in Streamlit Cloud dashboard
5. Deploy!

## Configuration

### Database Setup

The application requires PostgreSQL. Set the `DATABASE_URL` environment variable:

```
DATABASE_URL=postgresql://username:password@host:port/database
```

### Mapping Files

Item and store mappings are automatically loaded from Excel files in the `mappings/` directory:

- `mappings/wholefoods/store_mapping.xlsx`
- `mappings/kehe/item_mapping.xlsx` 
- `mappings/unfi_west/item_mapping.xlsx`
- `mappings/unfi_east/item_mapping.xlsx`

## Usage

1. Select your order source from the dropdown
2. Upload one or more order files (HTML, CSV, Excel, or PDF)
3. Click "Process Orders" 
4. Download the converted Xoro CSV file

## Architecture

- **Frontend**: Streamlit web interface
- **Backend**: Python with pandas for data processing
- **Database**: PostgreSQL for persistent storage
- **Parsers**: Modular source-specific parsers
- **Mapping**: Database-backed item/store mapping system

## File Structure

```
├── app.py                 # Main Streamlit application
├── parsers/              # Source-specific parsers
│   ├── wholefoods_parser.py
│   ├── kehe_parser.py
│   ├── unfi_west_parser.py
│   ├── unfi_east_parser.py
│   └── tkmaxx_parser.py
├── utils/                # Utility classes
│   ├── mapping_utils.py
│   └── xoro_template.py
├── database/             # Database layer
│   ├── models.py
│   ├── service.py
│   └── connection.py
├── mappings/             # Mapping files
└── requirements.txt      # Dependencies
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details