# Hosting Guide for Order Transformation Platform

## 📦 Complete Project Package

This package contains everything you need to host the Order Transformation Platform on any platform:

### 🗂️ What's Included
- **Core Application**: `app.py` - Main Streamlit application
- **Database Layer**: `database/` - PostgreSQL models and services  
- **Parsers**: `parsers/` - Vendor-specific order parsers (KEHE, UNFI, Whole Foods, TK Maxx)
- **Utilities**: `utils/` - Data transformation and mapping utilities
- **Mappings**: `mappings/` - CSV mapping files for all vendors
- **Configuration**: `.streamlit/config.toml`, `requirements.txt`
- **Deployment Files**: `Dockerfile`, `docker-compose.yml`, `deploy.sh`

### 🚀 Quick Deployment Options

#### Option 1: Docker (Recommended)
```bash
# Extract files
tar -xzf order_transformation_platform.tar.gz
cd order_transformation_platform

# Deploy with one command
./deploy.sh
```
Access at: http://localhost:5000

#### Option 2: Streamlit Cloud
1. Upload files to GitHub repository
2. Connect to Streamlit Cloud
3. Add `DATABASE_URL` to secrets
4. Deploy automatically

#### Option 3: Manual Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variable
export DATABASE_URL="your_postgresql_url"

# Initialize database
python init_database.py

# Run application
streamlit run app.py --server.port 5000
```

### 🔧 Environment Requirements
- **Python**: 3.11+
- **Database**: PostgreSQL 12+
- **Memory**: 1GB+ RAM recommended
- **Storage**: 500MB for application + database storage

### 📋 Pre-configured Features
- ✅ KEHE order processing with customer/store/item mappings
- ✅ UNFI East/West order parsing
- ✅ Whole Foods HTML order processing
- ✅ TK Maxx order support
- ✅ PostgreSQL database integration
- ✅ Comprehensive error handling
- ✅ Debug logging and monitoring

### 🌐 Hosting Platforms Tested
- **Docker**: Full containerization included
- **Streamlit Cloud**: Ready for direct deployment
- **Heroku**: Procfile and configuration included
- **AWS/GCP/DigitalOcean**: Dockerfile ready for cloud deployment
- **Local Development**: Complete setup instructions

### 🔑 Required Environment Variables
```bash
DATABASE_URL=postgresql://user:pass@host:port/dbname
```

### 📊 Database Schema
Auto-creates these tables:
- `customers` - Customer mappings
- `stores` - Store mappings  
- `items` - Item mappings
- `mappings` - Cross-reference data
- `orders` - Processing history

### 🔍 Health Check
Built-in health endpoint: `/?health=check`

### 📞 Support
All code is production-ready with comprehensive error handling and logging. The platform processes real order files and generates accurate Xoro CSV templates.

---

**Ready to deploy? Start with `./deploy.sh` for the fastest setup!**