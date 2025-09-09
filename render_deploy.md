# Render Deployment Guide

## Quick Setup for Render

1. **Upload this code to GitHub**: https://github.com/RishamChandi/OrderTransformer.git

2. **Render Service Settings**:
   - **Build Command**: `pip install -r streamlit_requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
   - **Python Version**: 3.11

3. **Environment Variables** (add in Render dashboard):
   ```
   DATABASE_URL=your_postgresql_connection_string
   ```

4. **Health Check Endpoint**: `/?health=check`

## Files Ready for Deployment

✅ **app.py** - Main Streamlit application
✅ **streamlit_requirements.txt** - All dependencies
✅ **cloud_config.py** - Environment detection
✅ **database/** - Database models and connection
✅ **parsers/** - Vendor-specific parsers (KEHE, Whole Foods, UNFI East/West, TK Maxx)
✅ **utils/** - Xoro template and mapping utilities
✅ **mappings/** - Pre-configured mapping files

## Application Features

- Multi-vendor order processing
- Advanced mapping management with click-to-edit functionality
- Database-backed storage
- Complete CSV export system
- Health check monitoring
- Environment-aware configuration

## Database Setup

The application will automatically:
- Detect the deployment environment
- Initialize database tables
- Handle SSL connections properly
- Provide comprehensive error handling

Your application is fully production-ready!